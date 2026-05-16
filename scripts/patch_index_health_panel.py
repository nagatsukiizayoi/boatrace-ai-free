from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "/* STEP67_DATA_STATUS_PANEL_STYLE */"
HTML_MARKER = "<!-- STEP67_DATA_STATUS_PANEL_HTML -->"
SCRIPT_MARKER = "// STEP67_DATA_STATUS_PANEL_SCRIPT"

STYLE_BLOCK = f"""
<style>
{STYLE_MARKER}
.data-status-panel {{
  position: fixed;
  right: 14px;
  bottom: 14px;
  z-index: 9999;
  width: min(360px, calc(100vw - 28px));
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #d9dee8;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2937;
  overflow: hidden;
}}

.data-status-panel__header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #111827;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}}

.data-status-panel__badge {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 800;
  background: #facc15;
  color: #422006;
}}

.data-status-panel__badge.ok {{
  background: #22c55e;
  color: #052e16;
}}

.data-status-panel__badge.ng {{
  background: #ef4444;
  color: #fff;
}}

.data-status-panel__body {{
  padding: 10px 12px 12px;
  font-size: 12px;
}}

.data-status-panel__grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}}

.data-status-panel__item {{
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
}}

.data-status-panel__label {{
  color: #64748b;
  font-size: 11px;
  margin-bottom: 2px;
}}

.data-status-panel__value {{
  color: #0f172a;
  font-size: 14px;
  font-weight: 800;
  word-break: break-all;
}}

.data-status-panel__message {{
  margin-top: 8px;
  padding: 8px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #334155;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}}

.data-status-panel__message.ok {{
  background: #ecfdf5;
  color: #166534;
}}

.data-status-panel__message.ng {{
  background: #fef2f2;
  color: #991b1b;
}}

.data-status-panel__actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}}

.data-status-panel__actions button,
.data-status-panel__actions a {{
  appearance: none;
  border: 0;
  border-radius: 8px;
  padding: 7px 9px;
  font-size: 11px;
  font-weight: 800;
  text-decoration: none;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}}

.data-status-panel__actions button.secondary,
.data-status-panel__actions a.secondary {{
  background: #475569;
}}

.data-status-panel.is-collapsed .data-status-panel__body {{
  display: none;
}}

@media (max-width: 640px) {{
  .data-status-panel {{
    left: 10px;
    right: 10px;
    bottom: 10px;
    width: auto;
  }}
}}
</style>
"""

HTML_BLOCK = f"""
{HTML_MARKER}
<div id="step67DataStatusPanel" class="data-status-panel" aria-live="polite">
  <div class="data-status-panel__header">
    <div>Prediction JSON Status</div>
    <div id="step67StatusBadge" class="data-status-panel__badge">CHECKING</div>
  </div>
  <div class="data-status-panel__body">
    <div class="data-status-panel__grid">
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">updated_at</div>
        <div id="step67UpdatedAt" class="data-status-panel__value">-</div>
      </div>
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">run_key</div>
        <div id="step67RunKey" class="data-status-panel__value">-</div>
      </div>
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">races</div>
        <div id="step67RaceCount" class="data-status-panel__value">-</div>
      </div>
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">tickets</div>
        <div id="step67TicketCount" class="data-status-panel__value">-</div>
      </div>
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">alerts</div>
        <div id="step67AlertCount" class="data-status-panel__value">-</div>
      </div>
      <div class="data-status-panel__item">
        <div class="data-status-panel__label">target_date</div>
        <div id="step67TargetDate" class="data-status-panel__value">-</div>
      </div>
    </div>
    <div id="step67StatusMessage" class="data-status-panel__message">
      prediction.json を確認中です。
    </div>
    <div class="data-status-panel__actions">
      <button type="button" onclick="step67ReloadPredictionStatus()">再確認</button>
      <button type="button" class="secondary" onclick="step67TogglePredictionStatus()">折りたたみ</button>
      <a class="secondary" href="./prediction.json" target="_blank" rel="noopener">JSON</a>
      <a class="secondary" href="./healthcheck.html" target="_blank" rel="noopener">HealthCheck</a>
    </div>
  </div>
</div>
"""

SCRIPT_BLOCK = f"""
<script>
{SCRIPT_MARKER}
(function () {{
  function setText(id, value) {{
    var el = document.getElementById(id);
    if (!el) return;
    if (value === undefined || value === null || value === "") {{
      el.textContent = "-";
    }} else {{
      el.textContent = String(value);
    }}
  }}

  function setBadge(type, text) {{
    var badge = document.getElementById("step67StatusBadge");
    if (!badge) return;
    badge.className = "data-status-panel__badge " + type;
    badge.textContent = text;
  }}

  function setMessage(type, text) {{
    var msg = document.getElementById("step67StatusMessage");
    if (!msg) return;
    msg.className = "data-status-panel__message " + type;
    msg.textContent = text;
  }}

  function countTickets(races) {{
    if (!Array.isArray(races)) return 0;
    return races.reduce(function (sum, race) {{
      var recs = Array.isArray(race.recommendations) ? race.recommendations : [];
      return sum + recs.length;
    }}, 0);
  }}

  function validatePredictionJson(data) {{
    var required = [
      "updated_at",
      "run_key",
      "model_name",
      "model_version",
      "target_date",
      "summary",
      "races",
      "alerts"
    ];

    var missing = required.filter(function (key) {{
      return !(key in data);
    }});

    if (missing.length > 0) {{
      throw new Error("Missing keys: " + missing.join(", "));
    }}

    if (!Array.isArray(data.races)) {{
      throw new Error("races must be an array");
    }}

    if (!Array.isArray(data.alerts)) {{
      throw new Error("alerts must be an array");
    }}

    if (data.races.length === 0) {{
      throw new Error("races is empty");
    }}

    var tickets = countTickets(data.races);
    if (tickets === 0) {{
      throw new Error("recommendations are empty");
    }}

    return tickets;
  }}

  window.step67ReloadPredictionStatus = async function () {{
    setBadge("", "CHECKING");
    setMessage("", "prediction.json を確認中です。");

    try {{
      var url = "./prediction.json?v=" + Date.now();
      var response = await fetch(url, {{ cache: "no-store" }});

      if (!response.ok) {{
        throw new Error("HTTP " + response.status + " " + response.statusText);
      }}

      var data = await response.json();
      var ticketCount = validatePredictionJson(data);
      var races = Array.isArray(data.races) ? data.races : [];
      var alerts = Array.isArray(data.alerts) ? data.alerts : [];

      setText("step67UpdatedAt", data.updated_at);
      setText("step67RunKey", data.run_key);
      setText("step67RaceCount", races.length);
      setText("step67TicketCount", ticketCount);
      setText("step67AlertCount", alerts.length);
      setText("step67TargetDate", data.target_date);

      setBadge("ok", "JSON OK");
      setMessage(
        "ok",
        "prediction.json を正常に読み込みました。\\n" +
        "model: " + data.model_name + " / " + data.model_version
      );
    }} catch (error) {{
      setBadge("ng", "JSON NG");
      setMessage(
        "ng",
        "prediction.json の読み込みまたは検証に失敗しました。\\n" +
        String(error && (error.stack || error.message) || error)
      );
    }}
  }};

  window.step67TogglePredictionStatus = function () {{
    var panel = document.getElementById("step67DataStatusPanel");
    if (!panel) return;
    panel.classList.toggle("is-collapsed");
  }};

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", window.step67ReloadPredictionStatus);
  }} else {{
    window.step67ReloadPredictionStatus();
  }}
}})();
</script>
"""

def main():
    if not INDEX_PATH.exists():
        raise SystemExit(f"{INDEX_PATH} が見つかりません")

    html = INDEX_PATH.read_text(encoding="utf-8")

    if STYLE_MARKER in html or HTML_MARKER in html or SCRIPT_MARKER in html:
        print("STEP 67 patch already exists. No changes made.")
        print("STEP 67 CHECK: OK")
        return

    if "</head>" not in html:
        raise SystemExit("</head> が見つかりません。index.html の構造を確認してください。")

    if "</body>" not in html:
        raise SystemExit("</body> が見つかりません。index.html の構造を確認してください。")

    html = html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)
    html = html.replace("</body>", HTML_BLOCK + "\n" + SCRIPT_BLOCK + "\n</body>", 1)

    INDEX_PATH.write_text(html, encoding="utf-8")

    print("Updated docs/index.html")
    print("Added STEP 67 data status panel")
    print("STEP 67 CHECK: OK")

if __name__ == "__main__":
    main()
