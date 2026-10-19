#!/usr/bin/env python3
"""
cowrie_auswertung.py
Liest cowrie.json (und optional portfake.json) und erzeugt ein einzelnes
HTML Dashboard ohne externe Abhaengigkeiten.

Optional: Laender ueber GeoLite2 (pip install geoip2, Datei GeoLite2-Country.mmdb).
"""

import argparse
import html
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

DEFAULT_LOG = os.path.expanduser("~/honeypot/cowrie/log/cowrie.json")
DEFAULT_PF = "/var/log/portfake/portfake.json"
DEFAULT_OUT = os.path.expanduser("~/honeypot/dashboard.html")
DEFAULT_GEO = os.path.expanduser("~/honeypot/GeoLite2-Country.mmdb")


def read_jsonl(path):
    if not path or not os.path.exists(path):
        return []
    events = []
    # auch rotierte Dateien cowrie.json.2026-10-01 usw. einlesen
    folder, base = os.path.split(path)
    files = sorted(f for f in os.listdir(folder or ".") if f.startswith(base))
    for name in files:
        with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def geo_lookup(path):
    try:
        import geoip2.database  # type: ignore
        reader = geoip2.database.Reader(path)
    except Exception:  # noqa: BLE001
        return None

    cache = {}

    def lookup(ip):
        if ip not in cache:
            try:
                cache[ip] = reader.country(ip).country.name or "Unbekannt"
            except Exception:  # noqa: BLE001
                cache[ip] = "Unbekannt"
        return cache[ip]

    return lookup


def analyse(events, pf_events, geo):
    s = {
        "connects": 0, "ips": set(), "login_ok": 0, "login_fail": 0,
        "users": Counter(), "passwords": Counter(), "combos": Counter(),
        "commands": Counter(), "clients": Counter(), "src": Counter(),
        "countries": Counter(), "hours": Counter(), "downloads": [],
        "success": [], "pf_ports": Counter(), "pf_ips": Counter(),
        "first": None, "last": None,
    }
    for e in events:
        eid = e.get("eventid", "")
        ip = e.get("src_ip")
        ts = e.get("timestamp", "")
        if ts:
            s["first"] = min(s["first"] or ts, ts)
            s["last"] = max(s["last"] or ts, ts)
        if eid == "cowrie.session.connect":
            s["connects"] += 1
            s["ips"].add(ip)
            s["src"][ip] += 1
            s["hours"][ts[:13]] += 1
            if geo:
                s["countries"][geo(ip)] += 1
        elif eid in ("cowrie.login.success", "cowrie.login.failed"):
            u, p = e.get("username", ""), e.get("password", "")
            s["users"][u] += 1
            s["passwords"][p] += 1
            s["combos"][f"{u} / {p}"] += 1
            if eid == "cowrie.login.success":
                s["login_ok"] += 1
                s["success"].append((ts, ip, u, p))
            else:
                s["login_fail"] += 1
        elif eid == "cowrie.command.input":
            s["commands"][e.get("input", "").strip()] += 1
        elif eid == "cowrie.client.version":
            s["clients"][e.get("version", "")] += 1
        elif eid == "cowrie.session.file_download":
            s["downloads"].append((ts, ip, e.get("url", ""), e.get("shasum", "")))
    for e in pf_events:
        s["pf_ports"][f'{e.get("dst_port")} {e.get("service", "")}'] += 1
        s["pf_ips"][e.get("src_ip")] += 1
    return s


def esc(x):
    return html.escape(str(x))


def table(title, rows, headers, limit=15):
    body = "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
        for r in rows[:limit]
    ) or f'<tr><td colspan="{len(headers)}" class="empty">keine Daten</td></tr>'
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    return f'<section class="card"><h2>{esc(title)}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></section>'


def top(counter, n=15):
    return [(k, v) for k, v in counter.most_common(n)]


def bars(hours):
    if not hours:
        return '<p class="empty">keine Daten</p>'
    keys = sorted(hours)[-72:]
    peak = max(hours[k] for k in keys) or 1
    cols = "".join(
        f'<div class="bar" style="height:{max(2, int(hours[k] / peak * 100))}%" '
        f'title="{esc(k)}:00  {hours[k]} Verbindungen"></div>'
        for k in keys
    )
    return f'<div class="bars">{cols}</div><p class="hint">letzte {len(keys)} Stunden, Spitze {peak}</p>'


def render(s):
    kpis = [
        ("Verbindungen", s["connects"]),
        ("Eindeutige IPs", len(s["ips"])),
        ("Logins erfolgreich", s["login_ok"]),
        ("Logins abgelehnt", s["login_fail"]),
        ("Befehle", sum(s["commands"].values())),
        ("Downloads", len(s["downloads"])),
        ("AD Port Treffer", sum(s["pf_ports"].values())),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><span>{esc(v)}</span><small>{esc(k)}</small></div>' for k, v in kpis
    )
    dl_rows = [
        (ts[:19].replace("T", " "), ip, url,
         sha[:16] + "…" if sha else "") for ts, ip, url, sha in reversed(s["downloads"])
    ]
    succ_rows = [(ts[:19].replace("T", " "), ip, u, p) for ts, ip, u, p in reversed(s["success"])]

    sections = [
        f'<section class="card wide"><h2>Verbindungen pro Stunde</h2>{bars(s["hours"])}</section>',
        table("Top Angreifer IPs", top(s["src"]), ["IP", "Verbindungen"]),
    ]
    if s["countries"]:
        sections.append(table("Top Länder", top(s["countries"]), ["Land", "Verbindungen"]))
    sections += [
        table("Top Benutzernamen", top(s["users"]), ["Benutzer", "Versuche"]),
        table("Top Passwörter", top(s["passwords"]), ["Passwort", "Versuche"]),
        table("Top Kombinationen", top(s["combos"]), ["Benutzer / Passwort", "Versuche"]),
        table("Top Befehle", top(s["commands"], 20), ["Befehl", "Anzahl"], 20),
        table("SSH Clients", top(s["clients"]), ["Version", "Anzahl"]),
        table("AD Ports", top(s["pf_ports"]), ["Port", "Treffer"]),
        table("Letzte erfolgreiche Logins", succ_rows, ["Zeit", "IP", "Benutzer", "Passwort"], 20),
        table("Downloads", dl_rows, ["Zeit", "IP", "URL", "SHA256"], 20),
    ]

    zeitraum = ""
    if s["first"]:
        zeitraum = f'{s["first"][:16].replace("T", " ")} bis {s["last"][:16].replace("T", " ")}'
    erstellt = datetime.now().strftime("%d.%m.%Y %H:%M")

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Honeypot Dashboard</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--line:#30363d;--txt:#e6edf3;--mut:#8b949e;--acc:#f0883e}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--txt);font:15px/1.5 Calibri,Segoe UI,system-ui,sans-serif;padding:24px}}
h1{{margin:0 0 4px;font-size:26px}}
.sub{{color:var(--mut);margin-bottom:24px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
.kpi span{{display:block;font-size:30px;font-weight:700;color:var(--acc)}}
.kpi small{{color:var(--mut)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;overflow:auto}}
.wide{{grid-column:1/-1}}
h2{{font-size:17px;margin:0 0 10px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);word-break:break-all}}
th{{color:var(--mut);font-weight:600}}
td:last-child,th:last-child{{text-align:right}}
.bars{{display:flex;align-items:flex-end;gap:2px;height:160px}}
.bar{{flex:1;background:var(--acc);border-radius:2px 2px 0 0;min-width:2px}}
.hint,.empty{{color:var(--mut);font-size:13px}}
</style></head><body>
<h1>Honeypot Dashboard</h1>
<div class="sub">Zeitraum {esc(zeitraum)} · erstellt {esc(erstellt)}</div>
<div class="kpis">{kpi_html}</div>
<div class="grid">{''.join(sections)}</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Cowrie HTML Dashboard")
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--portfake", default=DEFAULT_PF)
    ap.add_argument("--geo", default=DEFAULT_GEO)
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args()

    events = read_jsonl(a.log)
    pf = read_jsonl(a.portfake)
    geo = geo_lookup(a.geo) if os.path.exists(a.geo) else None
    stats = analyse(events, pf, geo)

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(render(stats))
    print(f"{len(events)} Cowrie Ereignisse, {len(pf)} AD Port Ereignisse -> {a.out}")


if __name__ == "__main__":
    main()
