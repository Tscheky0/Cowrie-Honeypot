# Fehlersuche

## Tunnel

| Symptom | Ursache | Lösung |
|---|---|---|
| `wg show` zeigt keinen Handshake | Schlüssel vertauscht oder Endpoint falsch | Public Keys auf beiden Seiten vergleichen, Endpoint `<VPS_IP>:51820` prüfen |
| Handshake ist Minuten alt | Keepalive fehlt, CGNAT hat die Verbindung vergessen | `PersistentKeepalive = 25` am Pi setzen |
| Ping 10.8.0.1 geht, SSH zum Pi läuft in Timeout | Falscher Port, Cowrie belegt 22 | Admin Port verwenden |
| Tunnel war plötzlich weg | VPS wurde neu installiert | Host Key prüfen, WireGuard und iptables neu einspielen |
| UDP 51820 blockiert | Firewall beim Anbieter | Port in der Cloud Firewall freigeben |

## Weiterleitung

| Symptom | Ursache | Lösung |
|---|---|---|
| Port 22 von außen geschlossen | IP Forwarding aus | `sysctl net.ipv4.ip_forward` muss 1 sein |
| Zähler in `iptables -t nat -L -v` steigen, aber keine Antwort | Rückroute am Pi fehlt | PostUp Regeln mit Connmark prüfen, `ip rule` und `ip route show table 51820` |
| Cowrie zeigt nur 10.8.0.1 als Absender | MASQUERADE auf wg0 am VPS | Diese Regel entfernen |
| Pakete kommen an, werden verworfen | Strenger Reverse Path Filter | `rp_filter = 2` auf wg0 und all |

## Cowrie

| Symptom | Ursache | Lösung |
|---|---|---|
| Container startet neu im Kreis | Rechte am Volume | `sudo chown -R 999:999 ~/honeypot/cowrie` |
| `cowrie.json` leer | Falscher Pfad gesucht | Log liegt unter `~/honeypot/cowrie/log/`, nicht unter `var/log` |
| Login immer abgelehnt | userdb zu streng | `userdb.txt` anpassen, Container neu starten |

## portfake.py

| Symptom | Ursache | Lösung |
|---|---|---|
| `Permission denied` beim Binden | Fehlende Capability | `AmbientCapabilities=CAP_NET_BIND_SERVICE` im Dienst |
| `Address already in use` | Samba oder anderer Dienst läuft | `sudo ss -tlnp` und störenden Dienst stoppen |

## Alarm

| Symptom | Ursache | Lösung |
|---|---|---|
| Keine Push Nachricht | Topic falsch abonniert | Name exakt vergleichen, Testnachricht per curl |
| Nachricht kommt mehrfach | Dienst doppelt gestartet | `systemctl status hp-alarm`, alte Prozesse beenden |
| Nach Logrotation Funktion weg | tail folgt alter Datei | Skript nutzt `tail -F`, das folgt dem Dateinamen |

## Nützliche Befehle

```bash
sudo wg show
ip rule
ip route show table 51820
sudo iptables -t mangle -L -n -v
sudo tcpdump -ni wg0
docker logs --tail 50 cowrie
journalctl -u hp-alarm -f
```
