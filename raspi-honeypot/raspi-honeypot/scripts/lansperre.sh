#!/bin/bash
# Verhindert, dass der Honeypot (Host und Docker Container) Geraete im Heimnetz erreicht.
# Erlaubt bleibt nur der Router als Gateway ins Internet.
# Aufruf: lansperre.sh up | down
# Variablen: HEIMNETZ (z.B. 192.168.1.0/24), ROUTER_IP (z.B. 192.168.1.1)

set -e
: "${HEIMNETZ:?HEIMNETZ fehlt}"
: "${ROUTER_IP:?ROUTER_IP fehlt}"

up() {
  iptables -N DOCKER-USER 2>/dev/null || true
  # Docker Container: DNS am Router erlauben, sonst nichts ins LAN
  iptables -I DOCKER-USER 1 -d "$ROUTER_IP" -p udp --dport 53 -j RETURN
  iptables -I DOCKER-USER 2 -d "$HEIMNETZ" -m conntrack --ctstate NEW -j DROP
  # Pi selbst: Router erlaubt, Antworten erlaubt, neue Verbindungen ins LAN verboten
  iptables -I OUTPUT 1 -d "$ROUTER_IP" -j ACCEPT
  iptables -I OUTPUT 2 -d "$HEIMNETZ" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -I OUTPUT 3 -d "$HEIMNETZ" -m conntrack --ctstate NEW -j DROP
}

down() {
  iptables -D DOCKER-USER -d "$ROUTER_IP" -p udp --dport 53 -j RETURN || true
  iptables -D DOCKER-USER -d "$HEIMNETZ" -m conntrack --ctstate NEW -j DROP || true
  iptables -D OUTPUT -d "$ROUTER_IP" -j ACCEPT || true
  iptables -D OUTPUT -d "$HEIMNETZ" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT || true
  iptables -D OUTPUT -d "$HEIMNETZ" -m conntrack --ctstate NEW -j DROP || true
}

case "$1" in
  up)   up ;;
  down) down ;;
  *)    echo "Aufruf: $0 up|down"; exit 1 ;;
esac
