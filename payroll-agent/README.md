# Payroll Agent

Verteilt die monatlichen Lohnabrechnungen automatisch und passwortgeschützt an die Mitarbeitenden.

## Problem

Das Steuerbüro stellt die Lohnabrechnungen jeden Monat als **eine** ZIP-Datei bereit. Darin liegt eine gemeinsame PDF mit den Abrechnungen aller Mitarbeitenden hintereinander. Bisher musste jemand die PDF von Hand aufteilen, jede Seite der richtigen Person zuordnen, die Dateien benennen und einzeln verschicken. Das kostet Zeit, und gerade bei Gehaltsdaten ist jeder Fehler unangenehm, etwa eine Abrechnung an die falsche Person oder eine ungeschützte PDF im Postfach.

## Lösung

1. Die ZIP-Datei vom Steuerbüro wird in einen festen Ordner gelegt. Mehr ist von Hand nicht zu tun.
2. n8n prüft den Ordner einmal täglich. Dateien, die gerade erst ankommen, werden noch nicht verarbeitet, damit kein halb fertiger Download erwischt wird.
3. Ein kleiner, selbst gebauter Dienst (`pdf-service`) entpackt die ZIP im Arbeitsspeicher und liest jede Seite aus: Personalnummer, Name, Monat und Jahr. Mehrseitige Abrechnungen erkennt er an „Seite x von y“ und hält sie zusammen.
4. n8n gleicht die Personalnummer mit der Mitarbeiterliste in Google Sheets ab und prüft zusätzlich den Nachnamen. Wer nicht in der Liste steht oder nicht aktiv ist, wird übersprungen.
5. Der Dienst schneidet die Seiten der Person heraus und verschlüsselt sie **im selben Schritt** mit ihrem persönlichen Passwort (AES-256). Eine unverschlüsselte Einzel-PDF wird nie gespeichert. Das Passwort steht nie in der Mail.
6. Die Mail geht raus, mit einem sauberen Dateinamen wie `Max_Mustermann_September_2026_Lohnabrechnung.pdf`.
7. Jeder Versand wird in einem Versandprotokoll (Google Sheets) eingetragen. Wird dieselbe Datei versehentlich noch einmal abgelegt, bekommt niemand seine Abrechnung doppelt.
8. Zum Schluss kommt eine Zusammenfassung: wie viele versendet, wie viele übersprungen (mit Grund) und ob es Fehler gab. Die ZIP wird archiviert. Alle 5 Tage löscht der Workflow nachts automatisch alle Dateien, die älter als 5 Tage sind.

## Ergebnis

- Lohnabrechnungen verschicken heißt jetzt: eine Datei in einen Ordner ziehen.
- Jede Abrechnung ist passwortgeschützt, und Fehlversand oder Doppelversand ist ausgeschlossen.
- Seit November 2026 im echten Einsatz.

## Aufbau

| Teil | Aufgabe |
|---|---|
| `workflow.json` | n8n-Workflow mit 23 Bausteinen: Ablauf, Zuordnung, Versand, Protokoll, Zusammenfassung, Fehlermeldungen und nächtliches Aufräumen |
| `pdf-service/` | Kleiner Python-Dienst (Flask + qpdf) im Docker-Container. Er darf nur auf den Payroll-Ordner zugreifen. Funktionen: `/scan`, `/split-encrypt`, `/archive`, `/cleanup` |
| Google Sheets | Blatt „MA_Liste“ (`personalnummer`, `name`, `email`, `passwort`, `status`) und Blatt „Versandprotokoll“ |

**Warum ein eigener Dienst?** n8n kann Dateien lesen und schreiben, aber keine PDFs aufteilen oder verschlüsseln und keine Dateien verschieben oder löschen. Dafür bräuchte man den Baustein „Execute Command“, mit dem n8n beliebige Befehle auf dem Rechner ausführen könnte. Der eigene Dienst kann genau vier Dinge, und das nur in einem Ordner. Das ist sicherer.

## Sicherheit

- **Testmodus:** Ein Schalter im Baustein „⚙️ Einstellungen“ schickt alle Mails an die eigene Adresse. Im Betreff steht dann, an wen sie eigentlich gehen würden.
- **Abgleich doppelt:** Erst die Personalnummer, dann zusätzlich der Nachname.
- **Keine Daten in n8n:** Erfolgreiche Läufe werden nicht gespeichert, so landen weder Passwörter noch PDFs in der n8n-Datenbank.
- **Fehlermails gedrosselt:** Bei grundsätzlichen Fehlern (z. B. Dienst nicht erreichbar) wird nichts verschickt. Die Fehlermail kommt höchstens einmal pro Stunde.

## Einrichten

```bash
docker network create payroll
docker build -t pdf-service ./pdf-service
docker run -d --name pdf-service --restart unless-stopped --network payroll -v ~/Payroll:/data pdf-service
docker network connect payroll n8n
```

Danach `workflow.json` in n8n importieren, die Platzhalter `DEINE_GOOGLE_SHEET_ID` und `deine.adresse@example.com` ersetzen, die Zugänge für Gmail und Google Sheets auswählen und zuerst im Testmodus starten.

## Learnings

- Erst eine echte Beispieldatei ansehen, dann bauen. Die Annahme „eine PDF pro Person“ war falsch, es war eine Sammel-PDF.
- Aufteilen und Verschlüsseln in einem Schritt, damit nie eine ungeschützte Datei entsteht.
- Polling so oft wie nötig, nicht so oft wie möglich: Für eine monatliche Aufgabe reicht eine Prüfung pro Tag statt alle 5 Minuten.
- Im Finder kopierte Dateien behalten ihr altes Änderungsdatum. Um zu erkennen, ob ein Download fertig ist, braucht man zusätzlich den Zeitpunkt der letzten Statusänderung.
