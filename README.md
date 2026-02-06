# copy_mac_to_Pi

Lokales Web-UI auf dem Mac, das Dateien per `rsync` via SSH auf den Pi5 kopiert.

## Start

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Browser: `http://localhost:5055`

## Konfiguration
Im UI unter **Einstellungen**:
- `SSH Host`: `pi5` oder Tailscale-IP (z.B. `100.66.12.52`)
- `SSH Port`: `22`
- `Remote Basis`: z.B. `/mnt/meineplatte`

Hinweis: `config.json` wird lokal erzeugt und nicht ins Git eingecheckt.

## Nutzung
1. Links Dateien/Ordner auswählen.
2. Rechts Zielpfad eintragen oder in der Liste navigieren.
3. `Aktualisieren` lädt den Inhalt des Zielpfads.
4. `Kopieren` überträgt die Auswahl per `rsync`.

## Voraussetzungen
- SSH ohne Passwort (`ssh pi5`) eingerichtet.
- `rsync` auf Mac und Pi5 vorhanden.
- Tailscale aktiv, wenn du remote zugreifst.

## Troubleshooting
- Wenn die Liste nicht passt: Pfad prüfen und `Aktualisieren` drücken.
- Typischer Pfad für die Platte: `/mnt/meineplatte`.
