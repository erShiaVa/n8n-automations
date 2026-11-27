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
