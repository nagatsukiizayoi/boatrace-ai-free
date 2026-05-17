from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "/* STEP82_EXPECTED_VALUE_ALERT_STYLE */"
HTML_MARKER = "<!-- STEP82_EXPECTED_VALUE_ALERT_HTML -->"
SCRIPT_MARKER = "// STEP82_EXPECTED_VALUE_ALERT_SCRIPT"

STYLE_BLOCK = f"""
<style>
{STYLE_MARKER}
.ev-alert-panel {{
  max-width: 1100px;
  margin: 24px auto;
  padding: 16px;
  border-radius: 16px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  box-shadow: 0 4px 18px rgba(234, 88, 12, 0.12);
  color: #111827;
}}

.ev-alert-panel h2 {{
  margin: 0 0 8px;
  font-size: 22px;
  color: #9a3412;
}}

.ev-alert-panel__note {{
  color: #7c2d12;
  font-size: 13px;
  margin-bottom: 14px;
  line-height: 1.6;
}}

.ev-alert-panel__status {{
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 800;
  background: #ffedd5;
  color: #9a3412;
}}

.ev-alert-panel__status.ok {{
  background: #ecfdf5;
  color: #166534;
}}

.ev-alert-panel__status.ng {{
  background: #fef2f2;
  color: #991b1b;
}}

.ev-alert-panel__toolbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}}

.ev-alert-panel__toolbar button {{
  border: 0;
  border-radius: 9px;
  padding: 8px 11px;
  font-size: 12px;
  font-weight: 800;
  background: #ea580c;
  color: #fff;
  cursor: pointer;
}}

.ev-alert-panel__toolbar button.secondary {{
  background: #475569;
}}

.ev-alert-summary {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}}

.ev-alert-summary__item {{
  background: #ffffff;
  border: 1px solid #fed7aa;
  border-radius: 12px;
  padding: 10px;
}}

.ev-alert-summary__label {{
  font-size: 12px;
  color: #9a3412;
  font-weight: 800;
  margin-bottom: 4px;
}}

.ev-alert-summary__value {{
  font-size: 22px;
  font-weight: 900;
  color: #c2410c;
}}

.ev-alert-card {{
  background: #ffffff;
  border: 1px solid #fdba74;
  border-left: 6px solid #ea580c;
  border-radius: 14px;
  padding: 14px;
  margin: 12px 0;
}}

.ev-alert-card__header {{
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}}

.ev-alert-card__title {{
  font-size: 16px;
  font-weight: 900;
  color: #9a3412;
}}

.ev-alert-card__badge {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 10px;
  background: #ea580c;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}}

.ev-alert-card__message {{
  font-size: 13px;
  line-height: 1.6;
  color: #111827;
  margin-bottom: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}}

.ev-alert-card__grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 8px;
}}

.ev-alert-card__metric {{
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 10px;
  padding: 8px;
}}

.ev-alert-card__metric-label {{
  color: #9a3412;
  font-size: 11px;
  font-weight: 800;
  margin-bottom: 3px;
}}

.ev-alert-card__metric-value {{
  color: #111827;
  font-size: 14px;
  font-weight: 900;
  word-break: break-all;
}}

.ev-alert-empty {{
  padding: 14px;
  background: #ffffff;
  color: #92400e;
  border: 1px dashed #fdba74;
  border-radius: 12px;
  font-weight: 800;
}}

@media (max-width: 640px) {{
  .ev-alert-panel {{
    margin: 16px 10px;
    padding: 12px;
  }}

  .ev-alert-card {{
    padding: 12px;
  }}
}}
</style>
"""

HTML_BLOCK = f"""
{HTML_MARKER}
<section id="step82ExpectedValueAlertPanel" class="ev-alert-panel">
  <h2>期待値アラート</h2>
  <div class="ev-alert-panel__note">
    prediction.json の <code>alerts</code> から、期待値が高い買い目を抽出して表示します。
    <code>expected_value</code> が高い買い目は、オッズ妙味のある候補として確認できます。
  </div>

  <div id="step82EvAlertStatus" class="ev-alert-panel__status">
    期待値アラートを読み込み中です。
  </div>

  <div class="ev-alert-panel__toolbar">
    <button type="button" onclick="step82LoadExpectedValueAlerts()">再読み込み</button>
    <button type="button" class="secondary" onclick="step82ToggleExpectedValueAlerts()">表示/非表示</button>
    <button type="button" class="secondary" onclick="window.open('./prediction.json?v=' + Date.now(), '_blank')">JSONを開く</button>
  </div>

  <div id="step82EvAlertContent"></div>
</section>
"""

SCRIPT_BLOCK = f"""
<script>
{SCRIPT_MARKER}
(function () {{
  function escapeHtml(value) {{
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }}

  function setStatus(type, message) {{
    var el = document.getElementById("step82EvAlertStatus");
    if (!el) return;
    el.className = "ev-alert-panel__status " + (type || "");
    el.textContent = message;
  }}

  function safeParseDetails(alert) {{
    var details = alert.details || alert.details_json || alert.detail || null;

    if (!details) return {{}};

    if (typeof details === "object") return details;

    try {{
      return JSON.parse(String(details));
    }} catch (e) {{
      return {{}};
    }}
  }}

  function isExpectedValueAlert(alert) {{
    var details = safeParseDetails(alert);

    var text = [
      alert.message,
      alert.type,
      alert.alert_type,
      alert.level,
      JSON.stringify(details)
    ].join(" ");

    return (
      text.includes("期待値") ||
      text.includes("expected_value") ||
      text.includes("high_expected_value") ||
      text.includes("value_bet")
    );
  }}

  function numberText(value, digits) {{
    if (value == null || value === "") return "-";
    var n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    return n.toFixed(digits);
  }}

  function renderSummary(alerts) {{
    var maxEv = 0;
    var maxOdds = 0;

    alerts.forEach(function (alert) {{
      var d = safeParseDetails(alert);
      var ev = Number(d.expected_value || alert.expected_value || 0);
      var odds = Number(d.odds || alert.odds || 0);

      if (Number.isFinite(ev) && ev > maxEv) maxEv = ev;
      if (Number.isFinite(odds) && odds > maxOdds) maxOdds = odds;
    }});

    return [
      '<div class="ev-alert-summary">',
      '<div class="ev-alert-summary__item">',
      '<div class="ev-alert-summary__label">期待値アラート件数</div>',
      '<div class="ev-alert-summary__value">' + escapeHtml(alerts.length) + '</div>',
      '</div>',
      '<div class="ev-alert-summary__item">',
      '<div class="ev-alert-summary__label">最大EV</div>',
      '<div class="ev-alert-summary__value">' + escapeHtml(maxEv ? maxEv.toFixed(3) : "-") + '</div>',
      '</div>',
      '<div class="ev-alert-summary__item">',
      '<div class="ev-alert-summary__label">最大オッズ</div>',
      '<div class="ev-alert-summary__value">' + escapeHtml(maxOdds ? maxOdds.toFixed(2) : "-") + '</div>',
      '</div>',
      '</div>'
    ].join("");
  }}

  function renderAlertCard(alert, index) {{
    var details = safeParseDetails(alert);

    var venueName = details.venue_name || details.venue || "";
    var raceNo = details.race_no || alert.race_no || "";
    var betType = details.bet_type || alert.bet_type || alert.type || alert.alert_type || "";
    var combination = details.combination || alert.combination || "";
    var ev = details.expected_value || alert.expected_value || "";
    var odds = details.odds || alert.odds || "";
    var probability = details.probability || alert.probability || "";
    var amount = details.amount || alert.amount || "";

    var title = "期待値アラート";
    if (venueName || raceNo) {{
      title += " - " + [venueName, raceNo ? raceNo + "R" : ""].filter(Boolean).join(" ");
    }}

    return [
      '<article class="ev-alert-card">',
      '<div class="ev-alert-card__header">',
      '<div class="ev-alert-card__title">' + escapeHtml(title) + '</div>',
      '<div class="ev-alert-card__badge">EV ' + escapeHtml(numberText(ev, 3)) + '</div>',
      '</div>',

      '<div class="ev-alert-card__message">',
      escapeHtml(alert.message || "期待値が高い買い目です。"),
      '</div>',

      '<div class="ev-alert-card__grid">',
      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">券種</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(betType || "-") + '</div>',
      '</div>',

      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">買い目</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(combination || "-") + '</div>',
      '</div>',

      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">オッズ</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(numberText(odds, 2)) + '</div>',
      '</div>',

      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">期待値</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(numberText(ev, 3)) + '</div>',
      '</div>',

      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">確率</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(numberText(probability, 3)) + '</div>',
      '</div>',

      '<div class="ev-alert-card__metric">',
      '<div class="ev-alert-card__metric-label">金額</div>',
      '<div class="ev-alert-card__metric-value">' + escapeHtml(amount || "-") + '</div>',
      '</div>',

      '</div>',
      '</article>'
    ].join("");
  }}

  window.step82LoadExpectedValueAlerts = async function () {{
    var content = document.getElementById("step82EvAlertContent");
    if (!content) return;

    setStatus("", "期待値アラートを読み込み中です。");
    content.innerHTML = "";

    try {{
      var response = await fetch("./prediction.json?v=" + Date.now(), {{ cache: "no-store" }});

      if (!response.ok) {{
        throw new Error("HTTP " + response.status + " " + response.statusText);
      }}

      var data = await response.json();
      var alerts = Array.isArray(data.alerts) ? data.alerts : [];
      var evAlerts = alerts.filter(isExpectedValueAlert);

      if (evAlerts.length === 0) {{
        setStatus("ng", "期待値アラートは見つかりませんでした。create_expected_value_alerts.py の実行を確認してください。");
        content.innerHTML = '<div class="ev-alert-empty">期待値アラートはありません。</div>';
        return;
      }}

      content.innerHTML =
        renderSummary(evAlerts) +
        evAlerts.map(renderAlertCard).join("");

      setStatus("ok", "OK: " + evAlerts.length + "件の期待値アラートを表示しました。");
    }} catch (error) {{
      setStatus("ng", "NG: 期待値アラートの読み込みに失敗しました。 " + String(error && (error.message || error)));
      content.innerHTML = '<div class="ev-alert-empty">' + escapeHtml(String(error && (error.stack || error.message) || error)) + '</div>';
    }}
  }};

  window.step82ToggleExpectedValueAlerts = function () {{
    var content = document.getElementById("step82EvAlertContent");
    if (!content) return;
    content.style.display = content.style.display === "none" ? "" : "none";
  }};

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", window.step82LoadExpectedValueAlerts);
  }} else {{
    window.step82LoadExpectedValueAlerts();
  }}
}})();
</script>
"""

def main():
    if not INDEX_PATH.exists():
        raise SystemExit(f"{INDEX_PATH} が見つかりません")

    html = INDEX_PATH.read_text(encoding="utf-8")

    if STYLE_MARKER in html or HTML_MARKER in html or SCRIPT_MARKER in html:
        print("STEP 82 patch already exists. No changes made.")
        print("STEP 82 CHECK: OK")
        return

    if "</head>" not in html:
        raise SystemExit("</head> が見つかりません。docs/index.html を確認してください。")

    if "</body>" not in html:
        raise SystemExit("</body> が見つかりません。docs/index.html を確認してください。")

    html = html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)
    html = html.replace("</body>", HTML_BLOCK + "\n" + SCRIPT_BLOCK + "\n</body>", 1)

    INDEX_PATH.write_text(html, encoding="utf-8")

    print("Updated docs/index.html")
    print("Added STEP 82 expected value alert panel")
    print("STEP 82 CHECK: OK")


if __name__ == "__main__":
    main()
