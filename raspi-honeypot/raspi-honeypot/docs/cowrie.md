# Cowrie

Cowrie ist ein Medium Interaction SSH und Telnet Honeypot. Er nimmt Logins an, zeigt eine täuschend echte Linux Shell mit falschem Dateisystem und protokolliert jeden Tastendruck. Heruntergeladene Dateien werden gespeichert, aber nie ausgeführt.

## Docker installieren

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker <ADMIN_USER>
```

Danach einmal ab‑ und wieder anmelden.

## Ordner anlegen

```bash
mkdir -p ~/honeypot/cowrie/{etc,log,downloads,tty}
cd ~/honeypot
```

In diesen Ordner kommen aus dem Repo:

| Datei aus dem Repo | Ziel am Pi |
|---|---|
| `config/cowrie/docker-compose.yml` | `~/honeypot/docker-compose.yml` |
| `config/cowrie/cowrie.cfg.example` | `~/honeypot/cowrie/etc/cowrie.cfg` |
| `config/cowrie/userdb.txt.example` | `~/honeypot/cowrie/etc/userdb.txt` |

Rechte setzen, der Container läuft als Benutzer mit der ID 999:

```bash
sudo chown -R 999:999 ~/honeypot/cowrie
```

## Starten

```bash
docker compose up -d
docker compose logs -f
```

## Wichtige Einstellungen

| Einstellung | Wert | Grund |
|---|---|---|
| `hostname` | `dc01` | Passt zur Tarnung als Windows Domänen‑Umgebung im Netz |
| `listen_endpoints` | `tcp:2222` | Port 22 ist am Host frei, Weiterleitung kommt vom VPS |
| `download_limit_size` | 10 MB | Speicher am Pi schonen |
| `userdb.txt` | großzügig | Angreifer sollen hereinkommen, sonst sieht man keine Befehle |

## userdb.txt

Steuert, welche Logins angenommen werden. Für maximale Ausbeute akzeptiert Cowrie fast alles, ein paar typische Passwörter werden abgelehnt, damit es realistischer wirkt. Für die Klassenvorführung kann `root:x:*` gesetzt werden, dann kommt jeder mit jedem Passwort rein.

## Wo die Logs liegen

| Datei | Inhalt |
|---|---|
| `~/honeypot/cowrie/log/cowrie.json` | Alle Ereignisse im JSON Format, Grundlage der Auswertung |
| `~/honeypot/cowrie/log/cowrie.log` | Lesbares Textlog |
| `~/honeypot/cowrie/tty/` | Aufzeichnungen ganzer Sitzungen |
| `~/honeypot/cowrie/downloads/` | Von Angreifern geladene Dateien, benannt nach SHA256 |

Sitzung wie ein Video abspielen:

```bash
docker exec -it cowrie bin/playlog /cowrie/cowrie-git/var/lib/cowrie/tty/<DATEI>
```

## Wichtige Event IDs

| eventid | Bedeutung |
|---|---|
| `cowrie.session.connect` | Neue Verbindung |
| `cowrie.login.success` | Login angenommen |
| `cowrie.login.failed` | Login abgelehnt |
| `cowrie.command.input` | Eingegebener Befehl |
| `cowrie.session.file_download` | Datei heruntergeladen |
| `cowrie.client.version` | SSH Client des Angreifers |
| `cowrie.session.closed` | Sitzung beendet, mit Dauer |

## Achtung beim Testen

Beim eigenen Test unbedingt auf den richtigen Port achten. Wer sich versehentlich auf Port 22 statt auf den Admin Port verbindet, landet im Honeypot und das echte Passwort steht im Log. In dem Fall Passwort sofort mit `passwd` ändern.
