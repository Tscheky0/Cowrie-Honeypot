#!/bin/bash
# Schickt bei jedem erfolgreichen Cowrie Login eine Push-Nachricht ueber ntfy.
# Benoetigt: jq, curl
# Variablen: NTFY_TOPIC, NTFY_SERVER (Standard https://ntfy.sh), LOGFILE

: "${NTFY_SERVER:=https://ntfy.sh}"
: "${LOGFILE:=$HOME/honeypot/cowrie/log/cowrie.json}"

if [ -z "$NTFY_TOPIC" ] || [ "$NTFY_TOPIC" = "<NTFY_TOPIC>" ]; then
  echo "NTFY_TOPIC ist nicht gesetzt" >&2
  exit 1
fi

tail -n0 -F "$LOGFILE" 2>/dev/null \
| jq --unbuffered -r 'select(.eventid=="cowrie.login.success")
    | "\(.src_ip)\t\(.username)\t\(.password)\t\(.timestamp)"' \
| while IFS=$'\t' read -r ip user pass ts; do
    curl -s \
      -H "Title: Honeypot Login von $ip" \
      -H "Priority: high" \
      -H "Tags: rotating_light" \
      -H "Click: https://www.abuseipdb.com/check/$ip" \
      -d "Benutzer: $user
Passwort: $pass
Zeit: $ts" \
      "$NTFY_SERVER/$NTFY_TOPIC" >/dev/null
  done
