# Monitoring und Alarm

## Push‑Benachrichtigung mit ntfy

Bei jedem erfolgreichen Login im Honeypot kommt eine Nachricht aufs Handy mit Angreifer‑IP, Benutzername und Passwort. Dafür wird [ntfy.sh](https://ntfy.sh) verwendet, kostenlos und ohne Konto.

### Kanal wählen

Der Kanalname (Topic) ist gleichzeitig das Passwort. Jeder, der ihn kennt, kann mitlesen. Deshalb einen langen, zufälligen Namen wählen und nie veröffentlichen:

```bash
echo "hp-$(openssl rand -hex 6)"
```

### Handy einrichten

ntfy App aus dem App Store bzw. Play Store installieren, auf das Plus tippen, als Server `ntfy.sh` lassen, den eigenen Topic Namen eintragen und abonnieren.

### Dienst am Pi

Das Skript [scripts/hp-alarm.sh](../scripts/hp-alarm.sh) liest `cowrie.json` live mit und schickt bei `cowrie.login.success` eine Nachricht. Gestartet wird es über [config/systemd/hp-alarm.service](../config/systemd/hp-alarm.service).

```bash
sudo cp scripts/hp-alarm.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/hp-alarm.sh
sudo cp config/systemd/hp-alarm.service /etc/systemd/system/
sudo systemctl edit hp-alarm     # NTFY_TOPIC und LOGFILE setzen
sudo systemctl enable --now hp-alarm
```

Testnachricht:

```bash
curl -d "Testalarm vom Honeypot" ntfy.sh/<NTFY_TOPIC>
```

## Fernzugriff mit Termius

Termius am Handy hat zwei Einträge:

| Eintrag | Host | Port | Besonderheit |
|---|---|---|---|
| Gateway | `<VPS_IP>` | `<ADMIN_SSH_PORT>` | Schlüssel‑Login |
| Honeypot Pi | `10.8.0.2` | `<ADMIN_SSH_PORT>` | Gateway als Jump Host eintragen |

So kann man nach einem Alarm sofort nachsehen, was der Angreifer gerade tippt:

```bash
tail -f ~/honeypot/cowrie/log/cowrie.json | jq -c 'select(.eventid=="cowrie.command.input") | {src_ip, input}'
```

## LAN‑Sperre

Falls ein Angreifer jemals aus dem Container ausbricht, darf er nicht ins Heimnetz. Das Skript [scripts/lansperre.sh](../scripts/lansperre.sh) sperrt mit iptables jeglichen Verkehr vom Pi und aus Docker in Richtung `<HEIMNETZ>`. Ausnahme ist nur der Router als Gateway ins Internet.

```bash
sudo cp scripts/lansperre.sh /usr/local/sbin/
sudo chmod +x /usr/local/sbin/lansperre.sh
sudo cp config/systemd/cowrie-lansperre.service /etc/systemd/system/
sudo systemctl enable --now cowrie-lansperre
```

Kontrolle:

```bash
sudo iptables -L DOCKER-USER -n -v
sudo iptables -L OUTPUT -n -v
```

## Regelmäßige Kontrollen

| Was | Befehl |
|---|---|
| Tunnel steht | `sudo wg show` |
| Cowrie läuft | `docker ps` |
| Alarm läuft | `systemctl status hp-alarm` |
| Platz auf der Karte | `df -h` |
| Logs wachsen | `ls -lh ~/honeypot/cowrie/log/` |
