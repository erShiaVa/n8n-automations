# n8n Automations

Hier zeige ich Automatisierungen, die ich mit [n8n](https://n8n.io) für ein Berliner Gastro-Unternehmen gebaut habe. Jede davon nimmt im Backoffice eine Aufgabe ab, die vorher von Hand erledigt wurde, und läuft im echten Betrieb.

Alle Workflows sind **bereinigt**: Namen, E-Mail-Adressen, Links und Preise sind durch Platzhalter oder Beispielwerte ersetzt. Logik und Aufbau entsprechen der Version, die tatsächlich im Einsatz ist.

## Projekte

| Projekt | Was es macht | Werkzeuge |
|---|---|---|
| [Payroll Agent](payroll-agent/) | Verteilt die monatlichen Lohnabrechnungen vom Steuerbüro automatisch an die Mitarbeitenden: teilt die Sammel-PDF auf, ordnet jede Abrechnung zu, schützt sie mit einem persönlichen Passwort und verschickt sie per Mail. | n8n, Google Sheets, Gmail, Docker, Python (qpdf) |
| [Event Order Automation](event-order-automation/) | Macht aus einer Eventanfrage über das Website-Formular automatisch einen fertig berechneten Angebotsentwurf in der Buchhaltungssoftware sevDesk. | n8n, Gmail, sevDesk-API |

## So arbeite ich

- **Erst klären, dann bauen:** Vor jedem Projekt schreibe ich die Anforderungen genau auf: Was soll passieren, was darf auf keinen Fall passieren, wer bekommt welche Nachricht?
- **Sicher testen:** Neue Workflows laufen zuerst im Testmodus, bei dem alle Mails an mich gehen. Erst nach einem erfolgreichen Test mit echten Daten gehen sie live.
- **Fehler sichtbar machen:** Jeder Workflow meldet sich, wenn etwas schiefgeht, statt still abzubrechen.
- **Sparsam mit Anfragen:** Externe Dienste werden nur dann angefragt, wenn es wirklich etwas zu tun gibt.
- **Dokumentieren:** Zu jedem Projekt halte ich den Stand, die Tests und die Learnings fest.

## Workflows ausprobieren

1. In n8n einen neuen Workflow öffnen.
2. Oben rechts auf **„…“ → „Import from File…“** klicken und die `workflow.json` des Projekts auswählen.
3. Die eigenen Zugänge (Credentials) in den markierten Bausteinen auswählen und die Platzhalter ersetzen.
4. Unter **„…“ → „Settings“** die Zeitzone prüfen. Beim Import übernimmt n8n die Workflow-Einstellungen nicht.
