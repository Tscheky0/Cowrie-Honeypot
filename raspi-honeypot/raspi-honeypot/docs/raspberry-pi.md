# Raspberry Pi vorbereiten

## Hardware

| Teil | Wert |
|---|---|
| Board | Raspberry Pi 5, 8 GB RAM |
| Speicher | microSD oder besser NVMe SSD |
| Netz | LAN Kabel ins Heimnetz (eigenes WLAN, kein Gäste‑VLAN) |
| Netzteil | offizielles 27 W USB‑C |

## System

Raspberry Pi OS Lite (64 bit) mit dem Raspberry Pi Imager flashen. Im Imager gleich Benutzer, SSH mit Public Key und Hostname setzen.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y wireguard iptables jq python3 curl unattended-upgrades
```

## Echten SSH Dienst verlegen

Port 22 bleibt für Cowrie frei. In `/etc/ssh/sshd_config`:

```text
Port <ADMIN_SSH_PORT>
PasswordAuthentication no
AllowUsers <ADMIN_USER>
```

```bash
sudo systemctl restart ssh
```

## WireGuard Client

Vorlage: [config/pi/wg0.conf.example](../config/pi/wg0.conf.example).

Zwei Punkte sind dabei entscheidend:

`PersistentKeepalive = 25` hält den Tunnel durch das CGNAT offen. Ohne diese Zeile schläft die Verbindung ein und der VPS erreicht den Pi nicht mehr.

`Table = off` zusammen mit den PostUp Regeln sorgt dafür, dass nur Antworten auf Tunnel‑Verbindungen in den Tunnel gehen. Der restliche Verkehr des Pi (Updates, Push‑Nachrichten) läuft normal über das Heimnetz.

```bash
sudo cp wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable --now wg-quick@wg0
ping 10.8.0.1
```

## Wie die Rückroute funktioniert

Ein Angriff kommt mit der echten Angreifer‑IP über wg0 herein. Ohne Zusatzregel würde der Pi die Antwort über die normale Standardroute ins Heimnetz schicken, der Angreifer bekäme eine Antwort von einer fremden IP und die Verbindung käme nie zustande.

Deshalb:

| Regel | Wirkung |
|---|---|
| `CONNMARK --set-mark 0x1` für neue Verbindungen auf wg0 | Jede Verbindung, die über den Tunnel kommt, bekommt eine Markierung |
| `CONNMARK --restore-mark` in PREROUTING und OUTPUT | Antwortpakete (auch aus dem Docker Container) erben die Markierung |
| `ip rule add fwmark 0x1 table 51820` | Markierte Pakete nutzen eine eigene Routingtabelle |
| `ip route add default dev wg0 table 51820` | In dieser Tabelle geht alles in den Tunnel |
| `rp_filter = 2` | Lockerer Reverse Path Filter, sonst verwirft der Kernel die Pakete |

## Fernzugriff

Der Pi steht nicht zu Hause, sondern rund 70 km entfernt. Zugriff erfolgt immer über den Tunnel:

```bash
# Laptop ohne WireGuard: VPS als Sprungserver
ssh -J root@<VPS_IP>:<ADMIN_SSH_PORT> -p <ADMIN_SSH_PORT> <ADMIN_USER>@10.8.0.2
```

Am Handy mit Termius: Host 10.8.0.2 eintragen und den VPS als Jump Host hinterlegen.

## Automatische Updates

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```
