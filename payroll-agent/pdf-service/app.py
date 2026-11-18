# pdf-service v2 – lokaler Helfer für den Payroll Agent
# Arbeitet NUR im Ordner /data (= ein Ordner auf dem Rechner, z. B. ~/Payroll).
#
#   POST /scan           Eingangsordner prüfen, PDFs auslesen, Abrechnungen je Person finden
#   POST /split-encrypt  Seiten einer Person herausschneiden und mit Passwort verschlüsseln
#   POST /archive        verarbeitete Dateien nach archiv/JJJJ-MM/ verschieben
#   POST /cleanup        alles löschen, was älter als X Tage ist

import io
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_file
from pypdf import PdfReader

DATA = "/data"
EINGANG = os.path.join(DATA, "eingang")
ARCHIV = os.path.join(DATA, "archiv")
MIN_ALTER_SEK = int(os.environ.get("MIN_ALTER_SEK", 120))  # Datei muss 2 Minuten unverändert sein (Download fertig)
TEMP_ENDUNGEN = (".crdownload", ".download", ".part", ".tmp")

MONATE = "Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"

app = Flask(__name__)


# ---------- Hilfsfunktionen ----------

def quelle_pfad(quelle):
    """Nur direkte Einträge in eingang/ erlauben (kein ../ usw.)."""
    if not quelle or "/" in quelle or quelle.startswith("."):
        raise ValueError(f"Ungültige Quelle: {quelle}")
    pfad = os.path.join(EINGANG, quelle)
    if not os.path.exists(pfad):
        raise FileNotFoundError(f"Quelle nicht gefunden: {quelle}")
    return pfad


def ist_muell(name):
    teile = name.split("/")
    return any(t.startswith(".") or t == "__MACOSX" for t in teile)


def letzte_aenderung(pfad):
    if os.path.isfile(pfad):
        st = os.stat(pfad)
        return max(st.st_mtime, st.st_ctime)
    zeiten = [os.stat(pfad).st_mtime]
    for wurzel, _, dateien in os.walk(pfad):
        for d in dateien:
            st = os.stat(os.path.join(wurzel, d))
            zeiten.append(max(st.st_mtime, st.st_ctime))
    return max(zeiten)


def pdfs_der_quelle(pfad):
    """Liefert [(pdf_name, bytes)] für eine PDF, ZIP oder einen Ordner."""
    ergebnis = []
    if os.path.isdir(pfad):
        for wurzel, _, dateien in os.walk(pfad):
            for d in sorted(dateien):
                voll = os.path.join(wurzel, d)
                rel = os.path.relpath(voll, pfad)
                if ist_muell(rel):
                    continue
                if d.lower().endswith(".pdf"):
                    with open(voll, "rb") as f:
                        ergebnis.append((rel, f.read()))
                elif d.lower().endswith(".zip"):
                    ergebnis += [(f"{rel}/{n}", b) for n, b in pdfs_aus_zip(voll)]
    elif pfad.lower().endswith(".zip"):
        ergebnis = pdfs_aus_zip(pfad)
    elif pfad.lower().endswith(".pdf"):
        with open(pfad, "rb") as f:
            ergebnis = [(os.path.basename(pfad), f.read())]
    return ergebnis


def pdfs_aus_zip(pfad):
    with zipfile.ZipFile(pfad) as z:
        return [
            (n, z.read(n))
            for n in sorted(z.namelist())
            if n.lower().endswith(".pdf") and not ist_muell(n)
        ]


def pdf_bytes(quelle, pdf_name):
    for name, daten in pdfs_der_quelle(quelle_pfad(quelle)):
        if name == pdf_name:
            return daten
    raise FileNotFoundError(f"PDF {pdf_name} nicht in {quelle}")


def seite_auslesen(text):
    pn = re.search(r"Personal-Nr\.\s*(\d+)", text)
    mj = re.search(rf"({MONATE})\s+(\d{{4}})", text)
    seite = re.search(r"Seite\s*(\d+)\s*von\s*(\d+)", text)
    name = ""
    zeilen = [z.strip() for z in text.splitlines()]
    for i, z in enumerate(zeilen[:20]):
        if z in ("Herrn", "Herr", "Frau") and i + 1 < len(zeilen):
            name = zeilen[i + 1]
            break
    return {
        "personalnummer": int(pn.group(1)) if pn else None,
        "monat": mj.group(1) if mj else None,
        "jahr": mj.group(2) if mj else None,
        "seite_nr": int(seite.group(1)) if seite else None,
        "seiten_gesamt": int(seite.group(2)) if seite else None,
        "name_pdf": name,
    }


def abrechnungen_finden(quelle, pdf_name, daten):
    """Seiten zu Abrechnungen je Person gruppieren."""
    abrechnungen, ignoriert = [], []
    reader = PdfReader(io.BytesIO(daten))
    aktuell = None
    for idx, page in enumerate(reader.pages):
        info = seite_auslesen(page.extract_text() or "")
        folgeseite = (
            aktuell is not None
            and (info["personalnummer"] in (None, aktuell["personalnummer"]))
            and info["seite_nr"] not in (None, 1)
        )
        if folgeseite:
            aktuell["seiten"].append(idx)
            continue
        if aktuell:
            abrechnungen.append(aktuell)
            aktuell = None
        if info["personalnummer"] is None:
            ignoriert.append({
                "quelle": quelle, "pdf": pdf_name, "seiten": [idx],
                "grund": "Keine Personalnummer auf der Seite gefunden",
            })
            continue
        aktuell = {"quelle": quelle, "pdf": pdf_name, "seiten": [idx], **info}
    if aktuell:
        abrechnungen.append(aktuell)

    for a in abrechnungen:
        a["seitenzahl_ok"] = a["seiten_gesamt"] in (None, len(a["seiten"]))
        a.pop("seite_nr", None)
    return abrechnungen, ignoriert


# ---------- Endpunkte ----------

@app.route("/")
def home():
    return "PDF Service v2 läuft"


@app.route("/scan", methods=["POST"])
def scan():
    os.makedirs(EINGANG, exist_ok=True)
    jetzt = time.time()
    quellen, abrechnungen, ignoriert, wartend = [], [], [], []
    for eintrag in sorted(os.listdir(EINGANG)):
        pfad = os.path.join(EINGANG, eintrag)
        if eintrag.startswith(".") or eintrag.lower().endswith(TEMP_ENDUNGEN):
            continue
        if jetzt - letzte_aenderung(pfad) < MIN_ALTER_SEK:
            wartend.append(eintrag)
            continue
        quellen.append(eintrag)
        try:
            pdfs = pdfs_der_quelle(pfad)
            if not pdfs:
                ignoriert.append({"quelle": eintrag, "grund": "Keine PDF gefunden"})
            for pdf_name, daten in pdfs:
                a, i = abrechnungen_finden(eintrag, pdf_name, daten)
                abrechnungen += a
                ignoriert += i
        except Exception as e:  # kaputte Datei → melden, nicht abbrechen
            ignoriert.append({"quelle": eintrag, "grund": f"Datei nicht lesbar: {e}"})
    return jsonify({
        "quellen": quellen,
        "wartend": wartend,
        "abrechnungen": abrechnungen,
        "ignoriert": ignoriert,
    })


@app.route("/split-encrypt", methods=["POST"])
def split_encrypt():
    body = request.get_json(force=True)
    passwort = str(body.get("password") or "")
    seiten = [int(s) for s in body.get("seiten", [])]
    if not passwort or not seiten:
        return jsonify({"fehler": "password und seiten sind Pflicht"}), 400
    daten = pdf_bytes(body["quelle"], body["pdf"])

    with tempfile.TemporaryDirectory() as tmp:
        ein = os.path.join(tmp, "ein.pdf")
        aus = os.path.join(tmp, "aus.pdf")
        with open(ein, "wb") as f:
            f.write(daten)
        bereich = ",".join(str(s + 1) for s in seiten)
        cmd = [
            "qpdf", "--empty",
            "--pages", ein, bereich, "--",
            "--encrypt",
            f"--user-password={passwort}",
            f"--owner-password={secrets.token_urlsafe(32)}",
            "--bits=256", "--",
            aus,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode not in (0, 3):
            return jsonify({"fehler": f"qpdf Fehler {r.returncode}: {r.stderr[-300:]}"}), 500
        with open(aus, "rb") as f:
            ergebnis = f.read()

    return send_file(
        io.BytesIO(ergebnis),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="lohnabrechnung.pdf",
    )


@app.route("/archive", methods=["POST"])
def archive():
    body = request.get_json(force=True)
    monat = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m")
    ziel_ordner = os.path.join(ARCHIV, monat)
    os.makedirs(ziel_ordner, exist_ok=True)
    verschoben = []
    for quelle in body.get("quellen", []):
        pfad = quelle_pfad(quelle)
        ziel = os.path.join(ziel_ordner, quelle)
        if os.path.exists(ziel):
            ziel = os.path.join(ziel_ordner, f"{int(time.time())}_{quelle}")
        shutil.move(pfad, ziel)
        os.utime(ziel)  # Zeitstempel = Archivierung (für das Löschen nach X Tagen)
        verschoben.append(os.path.relpath(ziel, DATA))
    return jsonify({"verschoben": verschoben})


@app.route("/cleanup", methods=["POST"])
def cleanup():
    tage = float((request.get_json(silent=True) or {}).get("tage", 5))
    grenze = time.time() - tage * 86400
    geloescht = []
    for basis in (EINGANG, ARCHIV):
        if not os.path.isdir(basis):
            continue
        for wurzel, ordner, dateien in os.walk(basis, topdown=False):
            for d in dateien:
                p = os.path.join(wurzel, d)
                st = os.stat(p)
                if max(st.st_mtime, st.st_ctime) < grenze:
                    os.remove(p)
                    geloescht.append(os.path.relpath(p, DATA))
            for o in ordner:
                p = os.path.join(wurzel, o)
                if not os.listdir(p):
                    os.rmdir(p)
    return jsonify({"geloescht": geloescht, "anzahl": len(geloescht)})


@app.errorhandler(Exception)
def fehler(e):
    return jsonify({"fehler": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
