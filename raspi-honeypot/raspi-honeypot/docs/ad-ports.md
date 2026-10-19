# Vorgetäuschte Active Directory Ports

Damit der Pi für Scanner wie ein Windows Domänencontroller aussieht, lauscht das Skript [scripts/portfake.py](../scripts/portfake.py) auf den typischen AD Ports. Jede Verbindung wird mit Zeit, Quell‑IP, Port und den ersten empfangenen Bytes in eine JSON Datei geschrieben.

## Ports

| Port | Dienst | Verhalten im Skript |
|---|---|---|
| 88 | Kerberos | nimmt Verbindung an, protokolliert, schließt |
| 135 | MS RPC Endpoint Mapper | nimmt Verbindung an, protokolliert, schließt |
| 389 | LDAP | nimmt Verbindung an, liest Anfrage, protokolliert |
| 445 | SMB | antwortet auf SMBv1 Negotiate minimal, protokolliert |
| 3389 | RDP | sendet eine X.224 Connection Confirm Antwort, protokolliert |

Es wird kein echter Dienst betrieben, es gibt nichts, was ein Angreifer tatsächlich ausnutzen könnte. Das Skript liest nur die ersten Bytes und schließt die Verbindung dann.

## Installation

```bash
sudo mkdir -p /opt/portfake /var/log/portfake
sudo cp scripts/portfake.py /opt/portfake/
sudo cp config/systemd/portfake.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now portfake
```

Ports unter 1024 brauchen Root Rechte bzw. die Capability `CAP_NET_BIND_SERVICE`. Der systemd Dienst gibt dem Skript genau diese eine Berechtigung und lässt es sonst als unprivilegierter Benutzer laufen.

## Kontrolle

```bash
sudo ss -tlnp | grep -E ':(88|135|389|445|3389)\s'
tail -f /var/log/portfake/portfake.json | jq .
```

## Test von außen

```bash
nmap -Pn -p 88,135,389,445,3389 <VPS_IP>
```

Alle fünf Ports sollten als `open` erscheinen.
