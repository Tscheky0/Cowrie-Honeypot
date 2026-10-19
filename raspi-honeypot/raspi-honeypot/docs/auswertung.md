# Auswertung

## Schnelle Abfragen mit jq

Alle Befehle beziehen sich auf `~/honeypot/cowrie/log/cowrie.json`. Zur Abkürzung:

```bash
LOG=~/honeypot/cowrie/log/cowrie.json
```

| Frage | Befehl |
|---|---|
| Wie viele Verbindungen? | `jq -r 'select(.eventid=="cowrie.session.connect")' $LOG \| jq -s length` |
| Top 10 Angreifer‑IPs | `jq -r 'select(.eventid=="cowrie.session.connect").src_ip' $LOG \| sort \| uniq -c \| sort -rn \| head` |
| Top 10 Passwörter | `jq -r 'select(.eventid \| startswith("cowrie.login")).password' $LOG \| sort \| uniq -c \| sort -rn \| head` |
| Top 10 Benutzernamen | `jq -r 'select(.eventid \| startswith("cowrie.login")).username' $LOG \| sort \| uniq -c \| sort -rn \| head` |
| Erfolgreiche Logins | `jq -c 'select(.eventid=="cowrie.login.success") \| {timestamp, src_ip, username, password}' $LOG` |
| Alle Befehle | `jq -r 'select(.eventid=="cowrie.command.input").input' $LOG \| sort \| uniq -c \| sort -rn` |
| Downloads | `jq -c 'select(.eventid=="cowrie.session.file_download") \| {src_ip, url, shasum}' $LOG` |
| SSH Clients | `jq -r 'select(.eventid=="cowrie.client.version").version' $LOG \| sort \| uniq -c \| sort -rn` |
| Verlauf einer IP | `jq -c 'select(.src_ip=="1.2.3.4")' $LOG` |

## Dashboard

Das Skript [scripts/cowrie_auswertung.py](../scripts/cowrie_auswertung.py) liest die Logs von Cowrie und portfake.py und baut daraus eine einzelne HTML Datei. Die Seite braucht keinen Webserver und lässt sich direkt im Browser öffnen oder in der Präsentation zeigen.

Inhalt des Dashboards:

| Bereich | Inhalt |
|---|---|
| Kennzahlen | Verbindungen, eindeutige IPs, Login‑Versuche, erfolgreiche Logins, Befehle, Downloads |
| Zeitverlauf | Verbindungen pro Stunde als Balkendiagramm |
| Top Listen | IPs, Länder, Benutzernamen, Passwörter, Befehle, SSH Clients |
| Downloads | URL und SHA256 jeder geladenen Datei mit Link zu VirusTotal |
| AD Ports | Treffer pro Port aus portfake.py |
| Letzte Logins | Tabelle der letzten erfolgreichen Logins |

Länder werden optional über die kostenlose GeoLite2 Datenbank ermittelt (Python Paket `geoip2` plus Datei `GeoLite2-Country.mmdb`). Fehlt sie, wird die Spalte einfach ausgelassen.

### Aufruf

```bash
python3 scripts/cowrie_auswertung.py \
  --log ~/honeypot/cowrie/log/cowrie.json \
  --portfake /var/log/portfake/portfake.json \
  --out ~/honeypot/dashboard.html
```

Auf den Laptop holen:

```bash
scp -J root@<VPS_IP>:<ADMIN_SSH_PORT> -P <ADMIN_SSH_PORT> <ADMIN_USER>@10.8.0.2:~/honeypot/dashboard.html .
```

### Automatisch jede Stunde

```bash
crontab -e
```

```text
0 * * * * /usr/bin/python3 /home/<ADMIN_USER>/raspi-honeypot/scripts/cowrie_auswertung.py --out /home/<ADMIN_USER>/honeypot/dashboard.html
```

## Kibana in T‑Pot

T‑Pot bringt fertige Dashboards mit. Unter `https://10.8.0.3:64297` den Punkt Kibana öffnen, dann das Dashboard `T-Pot` oder pro Honeypot das passende auswählen. Besonders hilfreich für die Präsentation ist die Attack Map.

## Malware Proben

Heruntergeladene Dateien liegen unter `~/honeypot/cowrie/downloads/`. Sie werden niemals ausgeführt. Zur Einordnung reicht der Hash:

```bash
sha256sum ~/honeypot/cowrie/downloads/*
file ~/honeypot/cowrie/downloads/*
```

Den Hash auf virustotal.com suchen, nicht die Datei hochladen.
