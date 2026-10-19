# VPS Gateway

## VPS mieten

Verwendet wurde ein kleiner Cloud Server bei Hetzner (Standort Deutschland, kleinste Größe reicht völlig). Betriebssystem Debian 12. Backups und zusätzliche Volumes sind nicht nötig und kosten nur extra.

## Grundabsicherung

Pakete aktualisieren und Werkzeuge installieren:

```bash
apt update && apt full-upgrade -y
apt install -y wireguard iptables iptables-persistent fail2ban
```

Den echten SSH Dienst auf einen hohen Port verlegen, damit Port 22 frei für den Honeypot ist. In `/etc/ssh/sshd_config`:

```text
Port <ADMIN_SSH_PORT>
PasswordAuthentication no
PermitRootLogin prohibit-password
```

Wichtig: Vorher den eigenen Public Key hinterlegen und eine zweite SSH Sitzung offen lassen, bis der neue Port getestet ist.

```bash
systemctl restart ssh
ssh -p <ADMIN_SSH_PORT> root@<VPS_IP>
```

## IP Forwarding aktivieren

```bash
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-forward.conf
sysctl --system
```

## WireGuard Schlüssel erzeugen

Für jedes Gerät einmal, jeweils auf dem Gerät selbst:

```bash
umask 077
wg genkey | tee privatekey | wg pubkey > publickey
```

## WireGuard Server

Datei `/etc/wireguard/wg0.conf`, Vorlage in [config/vps/wg0.conf.example](../config/vps/wg0.conf.example).

```bash
systemctl enable --now wg-quick@wg0
wg show
```

## Weiterleitung der Honeypot Ports

Die Regeln stehen im Skript [config/vps/honeypot-nat.sh](../config/vps/honeypot-nat.sh). Kern davon:

```bash
# SSH Port 22 auf Cowrie am Pi
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 22 -j DNAT --to-destination 10.8.0.2:2222

# Fake AD Ports
for p in 88 135 389 445 3389; do
  iptables -t nat -A PREROUTING -i eth0 -p tcp --dport $p -j DNAT --to-destination 10.8.0.2:$p
done

# Weiterleiten erlauben
iptables -A FORWARD -i eth0 -o wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -o eth0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

Installieren, WireGuard ruft das Skript beim Starten und Stoppen des Tunnels automatisch auf:

```bash
cp config/vps/honeypot-nat.sh /usr/local/sbin/
chmod +x /usr/local/sbin/honeypot-nat.sh
systemctl restart wg-quick@wg0
```

Die letzte Regel im Skript verbietet den Sensoren, über den VPS neue Verbindungen ins Internet aufzubauen. Malware Downloads aus dem Honeypot laufen damit nie über die öffentliche IP des Gateways.

Es gibt bewusst keine MASQUERADE Regel für eingehenden Verkehr, damit Cowrie die echten Angreifer‑IPs sieht.

## Firewall am VPS selbst

| Port | Erlaubt von | Zweck |
|---|---|---|
| `<ADMIN_SSH_PORT>`/tcp | überall, nur Schlüssel | Verwaltung |
| 51820/udp | überall | WireGuard |
| Honeypot Ports | überall | werden per DNAT weitergereicht |
| alles andere | niemand | gesperrt |

## Kontrolle

```bash
wg show                                  # Handshake mit Pi und T-Pot sichtbar?
iptables -t nat -L PREROUTING -n -v      # Zähler steigen bei Angriffen
tcpdump -ni wg0 port 2222                # Pakete gehen durch den Tunnel
```
