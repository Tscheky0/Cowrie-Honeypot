# T‑Pot als zweiter Sensor

T‑Pot von der Deutschen Telekom bündelt rund 20 Honeypots und eine fertige Auswertung mit Elastic und Kibana. Für den Pi ist das zu schwer, deshalb läuft T‑Pot als VM am Laptop und hängt als dritter Teilnehmer im WireGuard Netz.

## VM anlegen (Hyper‑V)

| Einstellung | Wert | Grund |
|---|---|---|
| Generation | 1 | Vermeidet Probleme mit Secure Boot und Grafik |
| RAM | mindestens 8 GB, besser 16 GB | Elastic braucht viel Speicher |
| Festplatte | 128 GB dynamisch | Logs und Indizes wachsen schnell |
| Netzwerk | Default Switch | NAT über den Laptop, reicht für ausgehenden Tunnel |
| System | Debian 12 netinst, ohne Desktop, mit SSH Server |

## Vorbereitung in der VM

```bash
su -
apt install -y sudo openssh-server curl wireguard
usermod -aG sudo <ADMIN_USER>
exit
```

Danach neu anmelden, damit die sudo Gruppe greift.

## Installation

Als normaler Benutzer, nicht als root:

```bash
env bash -c "$(curl -sL https://github.com/telekom-security/tpotce/raw/master/install.sh)"
```

Im Installer Typ `h` für Hive wählen. Nach dem Neustart ist SSH auf Port 64295 und die Weboberfläche auf Port 64297 erreichbar.

## WireGuard

Vorlage: [config/tpot/wg0.conf.example](../config/tpot/wg0.conf.example). Auch hier mit Rückroute über Connection Marking, damit T‑Pot echte Angreifer‑IPs sieht.

```bash
sudo systemctl enable --now wg-quick@wg0
```

## Zugriff

| Dienst | Adresse |
|---|---|
| SSH | `ssh -p 64295 <ADMIN_USER>@10.8.0.3` |
| Kibana und Weboberfläche | `https://10.8.0.3:64297` |

Beide nur über den Tunnel, niemals öffentlich weiterleiten.

## Ports am VPS auf T‑Pot leiten

Welche Ports T‑Pot bekommt, ist frei wählbar, solange sie sich nicht mit dem Pi überschneiden. Beispiel in [config/vps/honeypot-nat.sh](../config/vps/honeypot-nat.sh): FTP, Telnet, HTTP, HTTPS, MySQL, MSSQL und VNC.

## Typische Stolpersteine

| Problem | Lösung |
|---|---|
| `BECOME password` Fehler im Installer | Benutzer ist nicht in der sudo Gruppe oder Passwort falsch eingegeben |
| Ordner `~/tpotce` fehlt nach Abbruch | Installer einfach erneut ausführen |
| Kibana lädt ewig | VM hat zu wenig RAM, auf 16 GB erhöhen |
| Nach Neustart keine Verbindung | Default Switch vergibt neue IP, Tunnel baut aber von selbst wieder auf |
