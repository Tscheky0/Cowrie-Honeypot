# Cowrie SSH-Honeypot

Ein absichtlich verwundbarer SSH-Server, der Angreifer anlockt, ihre Login-Versuche und eingegebenen Befehle mitschneidet und anschließend auswertet. Entstanden als Projektarbeit in der IT-Ausbildung (Netzwerktechnik) am Schulungszentrum Fohnsdorf.

## Idee

Ein Honeypot ist ein Köder-System, das außer einem keinen Zweck hat: jeden Zugriff darauf aufzuzeichnen. Niemand hat dort legitim etwas zu suchen, also ist jede Verbindung verdächtig. Cowrie simuliert eine echte Linux-Shell, sodass Angreifer glauben, auf einem echten Server gelandet zu sein, während im Hintergrund jeder Tastendruck protokolliert wird.

## Aufbau

Der Honeypot läuft auf einem Raspberry Pi 5 als dediziertem Sensor, Cowrie selbst in Docker. Weil der Heimanschluss hinter CGNAT liegt und keine direkt erreichbare öffentliche IP hat, hängt der Pi nicht am Router. Stattdessen nimmt ein gemieteter VPS mit öffentlicher IP die Angriffe aus dem Internet entgegen und ist über einen verschlüsselten WireGuard-Tunnel mit dem Pi verbunden. Der Pi bleibt reiner Sensor und täuscht zusätzlich typische Active-Directory-Ports vor, um gezieltere Angriffe anzulocken.

## Auswertung

Die Auswertung läuft über T-Pot (die Honeypot-Plattform der Telekom), das als virtuelle Maschine betrieben wird und ein fertiges Web-Dashboard mit Kibana liefert: eine Live-Angriffskarte, Auswertungen nach Herkunftsland, Angreifer-IPs und verwendeten Zugangsdaten.

## Monitoring

Sobald sich jemand am Honeypot einloggt, kommt eine Push-Benachrichtigung aufs Handy. Der Fernzugriff auf den Sensor läuft per SSH über eine Mobil-App.

## Technik

Raspberry Pi 5, Docker, Cowrie, WireGuard, Python, HTML-Dashboard.
