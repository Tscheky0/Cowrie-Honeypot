#!/bin/bash
# Weiterleitung der Honeypot Ports vom VPS in den WireGuard Tunnel.
# Aufruf: honeypot-nat.sh up | down
# Kein MASQUERADE, damit die Sensoren die echten Angreifer-IPs sehen.

WAN=eth0
WG=wg0
PI=10.8.0.2
TPOT=10.8.0.3

# Port am VPS -> Ziel
PI_MAP=("22:2222" "23:2223" "88:88" "135:135" "389:389" "445:445" "3389:3389")
TPOT_PORTS=(21 25 80 443 1433 3306 5900)

[ "$1" = "down" ] && A="-D" || A="-A"

for m in "${PI_MAP[@]}"; do
  ext=${m%%:*}; int=${m##*:}
  iptables -t nat $A PREROUTING -i $WAN -p tcp --dport $ext -j DNAT --to-destination $PI:$int
done

for p in "${TPOT_PORTS[@]}"; do
  iptables -t nat $A PREROUTING -i $WAN -p tcp --dport $p -j DNAT --to-destination $TPOT:$p
done

iptables $A FORWARD -i $WAN -o $WG -j ACCEPT
iptables $A FORWARD -i $WG -o $WAN -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
# Sensoren duerfen nicht neu ins Internet verbinden (keine Malware-Downloads ueber den VPS)
iptables $A FORWARD -i $WG -o $WAN -m conntrack --ctstate NEW -j DROP
