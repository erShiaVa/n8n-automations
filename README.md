# n8n Automations

Event Order-Automation

👉🏼 Ziel:
Aus jeder Event-Anfrage automatisch einen geprüften Angebotsentwurfmachen

👉🏼 Technik:
n8n, Gmail, sevDesk

👉🏼 Status:
im Einsatz, läuft täglich um 13:00 und 14:00 Uhr

⚠️ Ausgangslage
Kunden fragen Events über ein Formular auf der Website an. Jede Anfrage musste vonHand bearbeitet werden:
- Anfrage lesen
- Preis ausrechnen
- Kunden in sevDesk suchen oder neu anlegen
- Angebot schreiben
Das kostete bei jeder Anfrage Zeit und war fehleranfällig, z. B. durch Tippfehler.

✅ Lösung
Ein n8n-Workflow übernimmt die Vorarbeit:

1.Anfrage auslesen:
Name, Datum, Gästezahl, Dauer und Ort aus der Gmail-Nachricht

2.Preis berechnen:
nach festen Regeln für Becher, Personal, Transport sowieWochenend- und Feiertagszuschlag

3.Kunden abgleichen:
in sevDesk finden oder neu anlegen

4.Angebot vorbereiten:
als Entwurf in sevDesk

5.Zur Prüfung melden:
Ich bekomme eine Mail mit Link zum Entwurf. Fehler werden mit einem Gmail-Label markiert und per Mail gemeldet.

📍 Wichtige Entscheidungen
1. Mensch entscheidet:
Der Workflow bereitet nur vor. Nichts geht automatisch an denKunden.
2. Regeln statt KI:
Die Preisberechnung folgt festen Regeln. Das Ergebnis ist jedes Malgleich und nachvollziehbar.
3. Sparsame Schnittstellen:
sevDesk wird nur bei einer neuen Anfrage abgefragt. Dasspart API-Anfragen.

Payroll Agent

👉🏼 Ziel:
Lohnabrechnungen jeden Monat sicher und automatisch an die richtigenPersonen verschicken

👉🏼Technik:
n8n, Google Sheets, Gmail, eigener Docker-Dienst (qpdf) zum Teilen undVerschlüsseln

👉🏼Status:
im Einsatz, mit Testdaten erfolgreich getestet

⚠️ Ausgangslage
Der Steuerberater schickt alle Lohnabrechnungen als eine große PDF in einer ZIP-Datei.
Jede Person soll nur ihre eigene Abrechnung bekommen, und zwar geschützt, dennLohndaten sind sensibel. 
Von Hand hieß das jeden Monat, für jede Person:
1. PDF aufteilen
2. Dateien umbenennen
3. mit Passwort versehen
4. Mail schreiben und verschicken

✅ Lösung
Ich lege die ZIP-Datei in einen Ordner, den Rest erledigt der Workflow:
1.Entpacken:
direkt im Arbeitsspeicher

2.Auslesen:
Personalnummer, Name und Monat aus jeder Seite

3.Zuordnen:
über eine Google-Tabelle zu den Mitarbeitenden

4.Verschlüsseln:
jede Abrechnung mit dem persönlichen Passwort

5.Versenden:
per Mail an die jeweilige Person

6.Zusammenfassen:
Bericht mit versendet, ignoriert und Fehlern

7.Aufräumen:
alte Dateien werden nach 5 Tagen automatisch gelöscht

✨ Wichtige Entscheidungen
1. Datenschutz zuerst:
Es liegt nie eine unverschlüsselte Einzel-PDF auf der Festplatte.
Das Passwort steht nie in der Mail. Teilen und Verschlüsseln laufen lokal in einemeigenen Docker-Dienst.
Kein externer PDF- oder KI-Dienst sieht die Abrechnungen,und Gmail verschickt nur verschlüsselte Dateien.

2. Nur freigegebene Empfänger:
Wer nicht in der Liste steht, bekommt nichts. Sosteuere ich selbst, wer Mails erhält.
Kein Doppelversand.
