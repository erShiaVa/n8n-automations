# Event Order Automation

Macht aus einer Eventanfrage über das Website-Formular automatisch einen fertig berechneten Angebotsentwurf in sevDesk.

## Problem

Eventanfragen kommen über ein Formular auf der Website per Mail an. Für jede Anfrage musste bisher von Hand ein Angebot erstellt werden: den Kunden in der Buchhaltungssoftware sevDesk suchen oder anlegen, Personal, Transport und Zuschläge ausrechnen, Positionen eintragen. Das dauert pro Anfrage einige Minuten, und Rechenfehler passieren leicht.

## Lösung

1. n8n sucht zweimal täglich in Gmail nach neuen Formular-Anfragen (Label „Events“). Gibt es keine, endet der Lauf sofort, **ohne** sevDesk anzufragen.
2. Ein Code-Baustein liest die Anfrage aus: Name, E-Mail, Datum, Gästezahl, Dauer und Ort. Die Dauer versteht er als Zahl oder als Zeitspanne wie „18–22 Uhr“.
3. Der Preis wird berechnet: Produkt pro Gast, Personal (Dauer plus Auf- und Abbau × Mitarbeitende × Stundensatz), Transport nach Entfernung und ein Wochenendzuschlag für Fr/Sa/So und Berliner Feiertage.
4. Der Kunde wird in sevDesk gesucht, erst per E-Mail, dann per Name. Gibt es ihn nicht, wird er neu angelegt, mit der nächsten freien Kundennummer.
5. In sevDesk entsteht ein **Angebotsentwurf** (wird nicht versendet) mit zwei Positionen und fortlaufender Angebotsnummer.
6. Die Mail bekommt das Label „Angebot erstellt“, und es kommt eine Benachrichtigung mit Link zum Entwurf, Kunde, Hinweisen und der Nachricht des Kunden.
7. Kann eine Anfrage nicht verarbeitet werden, bekommt sie das Label „Angebot fehlgeschlagen“, und es kommt eine Fehler-Mail mit dem Grund.

## Ergebnis

- Für jede Anfrage liegt ein fertig berechneter Angebotsentwurf bereit. Er muss nur noch geprüft und verschickt werden.
- Durch die Labels wird keine Anfrage doppelt verarbeitet.
- sevDesk wird nur angefragt, wenn es wirklich neue Anfragen gibt.

## Aufbau

- `workflow.json`: n8n-Workflow mit 28 Bausteinen (Gmail, Code, HTTP-Anfragen an die sevDesk-API).
- Alle Preise und Einstellungen stehen gesammelt im Baustein „Konfiguration“. **Die Preise in dieser Datei sind Beispielwerte.**
- Der sevDesk-Zugang läuft über eine Header-Authentifizierung (`Authorization` = API-Token).

## Learnings

- `Order/Factory/saveOrder` in sevDesk **verlangt eine Angebotsnummer**. Wird sie per API gesetzt, zählt sevDesk seinen Nummernkreis nicht weiter. Lösung: Die Nummer selbst bestimmen, als größere von „nächste Nummer laut sevDesk“ und „höchste vorhandene Nummer + 1“.
- Angebote in sevDesk haben kein Lieferdatum. Das Feld wird über die API stillschweigend ignoriert.
- Formular-Mails enthalten am Ende eine automatische Zeile („Sent via form submission …“), die beim Auslesen abgeschnitten werden muss.
- Code-Bausteine in n8n können keine gespeicherten Zugänge nutzen. API-Anfragen laufen deshalb über HTTP-Request-Bausteine.
- Ein Zeitplan nützt nichts, wenn der Rechner zu dieser Zeit schläft. Deshalb läuft der Workflow mittags, wenn der Rechner sicher an ist.
