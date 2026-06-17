#!/usr/bin/env python3
"""
run_pipeline.py — Phase 5 driver for the SAP master-data reconciliation project.

Builds the SQLite database from the numbered SQL scripts, runs the
reconciliation and data-quality scorecard, prints a console summary, and
writes a standalone interactive dashboard to dashboard/index.html
(no Power BI / Tableau install required — opens in any browser).

Usage:
    python3 run_pipeline.py
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SQL = os.path.join(HERE, "sql")
DB = os.path.join(HERE, "recon.db")
OUT_DIR = os.path.join(HERE, "dashboard")

BUILD_SCRIPTS = [
    "01_create_tables.sql",
    "02_insert_data.sql",
    "03_source_tables.sql",
    "04_source_data.sql",
    "06_data_quality_scorecard.sql",  # creates the DQ_SCORECARD view
]


def build_db():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    for name in BUILD_SCRIPTS:
        with open(os.path.join(SQL, name), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    return con


def fetch(con, sql):
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    return cols, [dict(zip(cols, row)) for row in cur.fetchall()]


def gather(con):
    _, missing = fetch(con, """
        SELECT s.MATNR, s.MTART
        FROM SRC_MARA s LEFT JOIN MARA t ON s.MATNR = t.MATNR
        WHERE t.MATNR IS NULL;
    """)
    _, mism = fetch(con, """
        SELECT s.MATNR, s.NTGEW AS source_weight, t.NTGEW AS target_weight
        FROM SRC_MARA s JOIN MARA t ON s.MATNR = t.MATNR
        WHERE CAST(s.NTGEW AS REAL) <> t.NTGEW;
    """)
    _, checks = fetch(con, """
        SELECT dimension, check_name, table_name, total_records, failed_records,
               ROUND(100.0*(total_records-failed_records)/NULLIF(total_records,0),1) AS pass_rate_pct
        FROM DQ_SCORECARD ORDER BY dimension, check_name;
    """)
    _, dims = fetch(con, """
        SELECT dimension,
               SUM(total_records) AS total_records,
               SUM(failed_records) AS failed_records,
               ROUND(100.0*(SUM(total_records)-SUM(failed_records))/NULLIF(SUM(total_records),0),1) AS pass_rate_pct
        FROM DQ_SCORECARD GROUP BY dimension ORDER BY pass_rate_pct ASC;
    """)
    overall = con.execute("""
        SELECT ROUND(100.0*(SUM(total_records)-SUM(failed_records))/NULLIF(SUM(total_records),0),1)
        FROM DQ_SCORECARD;
    """).fetchone()[0]
    _, rowcounts = fetch(con, """
        SELECT 'MARA' AS table_name, (SELECT COUNT(*) FROM SRC_MARA) AS source_count, (SELECT COUNT(*) FROM MARA) AS target_count
        UNION ALL SELECT 'MAKT', (SELECT COUNT(*) FROM SRC_MAKT), (SELECT COUNT(*) FROM MAKT)
        UNION ALL SELECT 'KNA1', (SELECT COUNT(*) FROM SRC_KNA1), (SELECT COUNT(*) FROM KNA1);
    """)
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "overall": overall,
        "dimensions": dims,
        "checks": checks,
        "missing": missing,
        "mismatches": mism,
        "rowcounts": rowcounts,
    }


def console_report(d):
    print(f"\nSAP Master-Data Reconciliation — {d['generated_at']}")
    print(f"Overall data-quality score: {d['overall']}%\n")
    print("By dimension:")
    for r in d["dimensions"]:
        print(f"  {r['dimension']:<22} {r['pass_rate_pct']:>5}%  "
              f"({r['failed_records']} failed / {r['total_records']})")
    print(f"\nMissing in target: {len(d['missing'])}   "
          f"Value mismatches: {len(d['mismatches'])}")


def write_dashboard(d):
    os.makedirs(OUT_DIR, exist_ok=True)
    html = DASHBOARD_TEMPLATE.replace("__DATA__", json.dumps(d))
    path = os.path.join(OUT_DIR, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"\nDashboard written to {path}")


DASHBOARD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAP Master-Data Reconciliation — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{--bg:#0f1419;--card:#1a212b;--line:#2a3441;--txt:#e6edf3;--mut:#8b98a5;
        --ok:#3fb950;--warn:#d29922;--bad:#f85149;--accent:#58a6ff;}
  *{box-sizing:border-box}
  body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
       background:var(--bg);color:var(--txt);padding:32px;}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:var(--mut);font-size:13px;margin-bottom:24px}
  .grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-bottom:24px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px}
  .kpi{font-size:40px;font-weight:700;line-height:1}
  .kpi.ok{color:var(--ok)} .kpi.warn{color:var(--warn)} .kpi.bad{color:var(--bad)}
  .label{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
  .charts{display:grid;gap:16px;grid-template-columns:1fr 1fr;margin-bottom:24px}
  @media(max-width:820px){.charts{grid-template-columns:1fr}}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
  .pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:600}
  .p-ok{background:rgba(63,185,80,.15);color:var(--ok)}
  .p-bad{background:rgba(248,81,73,.15);color:var(--bad)}
  h2{font-size:15px;margin:0 0 14px}
  .canvas-wrap{position:relative;height:240px}
  a{color:var(--accent)}
</style>
</head>
<body>
  <h1>SAP Master-Data Reconciliation</h1>
  <div class="sub">Source vs. migrated target · MARA / MAKT / MARC / KNA1 · generated <span id="ts"></span></div>

  <div class="grid" id="kpis"></div>

  <div class="charts">
    <div class="card"><h2>Quality score by dimension</h2><div class="canvas-wrap"><canvas id="dimChart"></canvas></div></div>
    <div class="card"><h2>Row counts: source vs target</h2><div class="canvas-wrap"><canvas id="rowChart"></canvas></div></div>
  </div>

  <div class="card" style="margin-bottom:16px">
    <h2>Data-quality checks</h2>
    <table><thead><tr><th>Dimension</th><th>Check</th><th>Table</th><th>Failed / Total</th><th>Pass rate</th></tr></thead>
    <tbody id="checks"></tbody></table>
  </div>

  <div class="charts">
    <div class="card"><h2>Missing in target</h2>
      <table><thead><tr><th>MATNR</th><th>Material type</th></tr></thead><tbody id="missing"></tbody></table></div>
    <div class="card"><h2>Value mismatches (net weight)</h2>
      <table><thead><tr><th>MATNR</th><th>Source</th><th>Target</th></tr></thead><tbody id="mismatch"></tbody></table></div>
  </div>

<script>
const D = __DATA__;
document.getElementById('ts').textContent = D.generated_at;

function cls(v){return v>=99?'ok':v>=90?'warn':'bad';}
const kpis = [
  {label:'Overall quality', val:D.overall+'%', c:cls(D.overall)},
  {label:'Missing in target', val:D.missing.length, c:D.missing.length?'bad':'ok'},
  {label:'Value mismatches', val:D.mismatches.length, c:D.mismatches.length?'bad':'ok'},
  {label:'Checks run', val:D.checks.length, c:'ok'},
];
document.getElementById('kpis').innerHTML = kpis.map(k=>
  `<div class="card"><div class="label">${k.label}</div><div class="kpi ${k.c}">${k.val}</div></div>`).join('');

document.getElementById('checks').innerHTML = D.checks.map(c=>{
  const ok = c.failed_records===0;
  return `<tr><td>${c.dimension}</td><td>${c.check_name}</td><td>${c.table_name}</td>
    <td>${c.failed_records} / ${c.total_records}</td>
    <td><span class="pill ${ok?'p-ok':'p-bad'}">${c.pass_rate_pct}%</span></td></tr>`;
}).join('');

document.getElementById('missing').innerHTML = D.missing.length
  ? D.missing.map(m=>`<tr><td>${m.MATNR}</td><td>${m.MTART}</td></tr>`).join('')
  : '<tr><td colspan="2" style="color:var(--mut)">None — all source rows migrated</td></tr>';

document.getElementById('mismatch').innerHTML = D.mismatches.length
  ? D.mismatches.map(m=>`<tr><td>${m.MATNR}</td><td>${m.source_weight}</td><td>${m.target_weight}</td></tr>`).join('')
  : '<tr><td colspan="3" style="color:var(--mut)">None — all values match</td></tr>';

const grid = {color:'#2a3441'}, tick = {color:'#8b98a5'};
new Chart(document.getElementById('dimChart'),{
  type:'bar',
  data:{labels:D.dimensions.map(d=>d.dimension),
    datasets:[{data:D.dimensions.map(d=>d.pass_rate_pct),
      backgroundColor:D.dimensions.map(d=>d.pass_rate_pct>=99?'#3fb950':d.pass_rate_pct>=90?'#d29922':'#f85149')}]},
  options:{indexAxis:'y',plugins:{legend:{display:false}},
    scales:{x:{min:0,max:100,grid,ticks:tick},y:{grid:{display:false},ticks:tick}}}
});
new Chart(document.getElementById('rowChart'),{
  type:'bar',
  data:{labels:D.rowcounts.map(r=>r.table_name),
    datasets:[
      {label:'Source',backgroundColor:'#58a6ff',data:D.rowcounts.map(r=>r.source_count)},
      {label:'Target',backgroundColor:'#3fb950',data:D.rowcounts.map(r=>r.target_count)}]},
  options:{plugins:{legend:{labels:{color:'#e6edf3'}}},
    scales:{x:{grid:{display:false},ticks:tick},y:{beginAtZero:true,grid,ticks:tick}}}
});
</script>
</body>
</html>
"""


def main():
    con = build_db()
    data = gather(con)
    con.close()
    console_report(data)
    write_dashboard(data)


if __name__ == "__main__":
    main()
