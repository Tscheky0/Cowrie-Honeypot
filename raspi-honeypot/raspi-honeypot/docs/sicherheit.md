# Sicherheit

Ein Honeypot lädt Angreifer absichtlich ein. Deshalb muss klar getrennt sein, was gefangen werden darf und was nicht.

## Schutzschichten

| Schicht | Maßnahme | Schützt vor |
|---|---|---|
| Heimnetz | CGNAT, keine Portfreigabe am Router | Direkten Angriffen auf das Zuhause |
| Gateway | Nur Honeypot Ports werden weitergeleitet, Verwaltung nur mit Schlüssel auf hohem Port | Übernahme des VPS |
| Tunnel | WireGuard, nur bekannte Schlüssel | Fremden Teilnehmern im Netz |
| Cowrie | Läuft in Docker, simulierte Shell, keine echte Befehlsausführung | Codeausführung am Pi |
| portfake.py | Liest nur Bytes, nur eine Capability, kein Root | Ausnutzung des Skripts |
| LAN‑Sperre | iptables blockt Pi und Docker Richtung Heimnetz | Seitlicher Bewegung ins LAN |
| Verwaltung | Echtes SSH nur über Tunnel, nur Schlüssel, eigener Benutzer | Zugriff auf den echten Pi |
| Updates | unattended‑upgrades am Pi und VPS | Bekannten Lücken |

## Zugangsdaten

Echte Zugangsdaten, IPs und Schlüssel stehen nie im Repo. Für die Präsentation eine eigene Übersicht offline führen. Die `.gitignore` schließt private Schlüssel, `*.conf` ohne `.example`, Logs und Downloads aus.

Vor jedem Commit kurz prüfen:

```bash
git diff --cached | grep -iE "privatekey|PrivateKey|password|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
```

## Host Key Wechsel am VPS

Wird der VPS neu installiert, ändert sich sein Host Key und SSH warnt. Vorher immer über die Web Konsole des Anbieters den Fingerprint prüfen:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Stimmt er, alten Eintrag am Laptop entfernen:

```bash
ssh-keygen -R "[<VPS_IP>]:<ADMIN_SSH_PORT>"
```

Nach einer Neuinstallation fehlen auch WireGuard Konfiguration und iptables Regeln, der Tunnel ist dann tot, bis alles wieder eingespielt ist.

## Datenschutz und Ethik

Angreifer‑IPs sind personenbezogene Daten im weiteren Sinn. Deshalb werden Rohlogs nicht veröffentlicht, in der Präsentation werden IPs teilweise geschwärzt. Bei Vorführungen in der Klasse wird vorher gesagt, dass alle Eingaben aufgezeichnet werden.

## Notfall

Wenn etwas komisch wirkt, zuerst den Honeypot vom Internet trennen, dann in Ruhe nachsehen:

```bash
# am VPS: Weiterleitung sofort stoppen
iptables -t nat -F PREROUTING

# am Pi: Cowrie stoppen
docker compose -f ~/honeypot/docker-compose.yml down
```
