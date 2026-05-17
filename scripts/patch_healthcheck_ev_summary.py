from pathlib import Path

HEALTHCHECK_PATH = Path("docs/healthcheck.html")

STYLE_MARKER = "/* STEP86_EV_HEALTHCHECK_STYLE */"
HTML_MARKER = "<!-- STEP86_EV_HEALTHCHECK_HTML -->"
SCRIPT_MARKER = "// STEP86_EV_HEALTHCHECK_SCRIPT"

STYLE_BLOCK = f"""
<style>
{STYLE_MARKER}
.ev-health-section {{
  margin-top: 18px;
}}

.ev-health-section h2 {{
  font-size: 20px;
  margin: 0 0 10px;
}}

.ev-health-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}}

.ev-health-card {{
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e3e5ec;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}}

.ev-health-label {{
  color: #777;
  font-size: 13px;
  margin-bottom: 4px;
}}

.ev-health-value {{
  font-size: 22px;
  font-weight: 800;
  color: #14532d;
  word-break: break-all;
}}

.ev-health-warning {{
  color: #9a3412;
}}

.ev-health-ok {{
  color: #166534;
}}

.ev-health-list {{
  background: #fff;
  border: 1px solid #e3e5ec;
  border-radius: 12px;
  padding: 12px;
  margin-top: 8px;
}}

.ev-health-list-item {{
  padding: 8px 0;
  border-bottom: 1px solid #eef2f7;
  font-size: 13px;
  line-height: 1.5;
}}

.ev-health-list-item:last-child {{
  border-bottom: 0;
}}

.ev-health-badge {{
  display: inline-block;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: #16a34a;
  margin-right: 6px;
}}
</style>
"""

HTML_BLOCK = f"""
{HTML_MARKER}
<div class="ev-health-section">
  <h2>EV / 期待値アラート確認</h2>

  <div class="ev-health-grid">
    <div class="ev-health-card">
      <div class="ev-health-label">recommendations</div>
      <div id="step86RecommendationCount" class="ev-health-value">-</div>
    </div>
    <div class="ev-health-card">
      <div class="ev-health-label">EV高買い目</div>
      <div id="step86HighEvTicketCount" class="ev-health-value">-</div>
    </div>
    <div class="ev-health-card">
      <div class="ev-health-label">期待値アラート</div>
      <div id="step86ExpectedValueAlertCount" class="ev-health-value">-</div>
    </div>
    <div class="ev-health-card">
      <div class="ev-health-label">最大EV</div>
      <div id="step86MaxEv" class="ev-health-value">-</div>
    </div>
    <div class="ev-health-card">
      <div class="ev-health-label">最大オッズ</div>
      <div id="step86MaxOdds" class="ev-health-value">-</div>
    </div>
    <div class="ev-health-card">
      <div class="ev-health-label">オッズ付き買い目</div>
      <div id="step86TicketsWithOdds" class="ev-health-value">-</div>
    </div>
  </div>

  <div class="ev-health-list">
    <strong>EV高買い目プレビュー</strong>
    <div id="step86HighEvPreview">-</div>
  </div>
</div>
"""

SCRIPT_BLOCK = f"""
<script>
{SCRIPT_MARKER}
(function () {{
  var STEP86_EV_THRESHOLD = 1.2;

  function setStep86Text(id, value) {{
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = value === undefined || value === null || value === "" ? "-" : String(value);
  }}

  function toNumber(value) {{
    var n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }}

  function getTicketCombination(ticket) {{
    return ticket.combination || ticket.ticket || ticket.buy || ticket.bet || "";
  }}

  function getTicketBetType(ticket) {{
    return ticket.bet_type || ticket.type || ticket.ticket_type || "";
  }}

  function getRaceLabel(race, index) {{
    var venue = "";
    if (typeof race.venue === "string") {{
      venue = race.venue;
    }} else if (race.venue && typeof race.venue === "object") {{
      venue = race.venue.name || race.venue.venue_name || race.venue.code || "";
    }} else {{
      venue = race.venue_name || "";
    }}

    var raceNo = race.race_no || race.raceNo || race.race_number || index + 1;
    return (venue ? venue + " " : "") + raceNo + "R";
  }}

  function isExpectedValueAlert(alert) {{
    var text = [
      alert && alert.message,
      alert && alert.type,
      alert && alert.alert_type,
      alert && alert.details,
      alert && alert.details_json
    ].join(" ");

    return (
      text.includes("期待値") ||
      text.includes("expected_value") ||
      text.includes("high_expected_value") ||
      text.includes("value_bet")
    );
  }}

  function updateStep86EvHealth(data) {{
    var races = Array.isArray(data.races) ? data.races : [];
    var alerts = Array.isArray(data.alerts) ? data.alerts : [];

    var recommendationCount = 0;
    var highEvTicketCount = 0;
    var ticketsWithOdds = 0;
    var maxEv = 0;
    var maxOdds = 0;
    var previewItems = [];

    races.forEach(function (race, raceIndex) {{
      var recommendations = Array.isArray(race.recommendations) ? race.recommendations : [];
      recommendationCount += recommendations.length;

      recommendations.forEach(function (ticket) {{
        var ev = toNumber(ticket.expected_value);
        var odds = toNumber(ticket.odds);

        if (odds > 0) {{
          ticketsWithOdds += 1;
        }}

        if (ev > maxEv) {{
          maxEv = ev;
        }}

        if (odds > maxOdds) {{
          maxOdds = odds;
        }}

        if (ev >= STEP86_EV_THRESHOLD) {{
          highEvTicketCount += 1;

          previewItems.push({{
            race: getRaceLabel(race, raceIndex),
            betType: getTicketBetType(ticket),
            combination: getTicketCombination(ticket),
            odds: odds,
            ev: ev,
            amount: ticket.amount
          }});
        }}
      }});
    }});

    var expectedValueAlertCount = alerts.filter(isExpectedValueAlert).length;

    setStep86Text("step86RecommendationCount", recommendationCount);
    setStep86Text("step86HighEvTicketCount", highEvTicketCount);
    setStep86Text("step86ExpectedValueAlertCount", expectedValueAlertCount);
    setStep86Text("step86MaxEv", maxEv ? maxEv.toFixed(3) : "-");
    setStep86Text("step86MaxOdds", maxOdds ? maxOdds.toFixed(2) : "-");
    setStep86Text("step86TicketsWithOdds", ticketsWithOdds);

    var preview = document.getElementById("step86HighEvPreview");
    if (!preview) return;

    if (previewItems.length === 0) {{
      preview.innerHTML = '<div class="ev-health-list-item ev-health-warning">EV高買い目はありません。</div>';
      return;
    }}

    preview.innerHTML = previewItems.slice(0, 10).map(function (item) {{
      return [
        '<div class="ev-health-list-item">',
        '<span class="ev-health-badge">EV高</span>',
        item.race,
        ' / ',
        item.betType,
        ' ',
        item.combination,
        ' / odds=',
        item.odds ? item.odds.toFixed(2) : "-",
        ' / EV=',
        item.ev ? item.ev.toFixed(3) : "-",
        ' / amount=',
        item.amount || "-",
        '</div>'
      ].join("");
    }}).join("");
  }}

  window.step86UpdateEvHealth = updateStep86EvHealth;

  // healthcheck.html 既存の loadJson() が data を画面反映した後に呼べるよう、
  // fetchを横取りせず、少し遅延して prediction.json を別途読み込む。
  async function loadStep86EvHealth() {{
    try {{
      var response = await fetch("./prediction.json?v=" + Date.now(), {{ cache: "no-store" }});
      if (!response.ok) throw new Error("HTTP " + response.status);
      var data = await response.json();
      updateStep86EvHealth(data);
    }} catch (error) {{
      setStep86Text("step86HighEvPreview", "読み込み失敗: " + String(error && (error.message || error)));
    }}
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", loadStep86EvHealth);
  }} else {{
    loadStep86EvHealth();
  }}
}})();
</script>
"""

def main():
    if not HEALTHCHECK_PATH.exists():
        raise SystemExit(f"{HEALTHCHECK_PATH} が見つかりません")

    html = HEALTHCHECK_PATH.read_text(encoding="utf-8")

    if STYLE_MARKER in html or HTML_MARKER in html or SCRIPT_MARKER in html:
        print("STEP 86 patch already exists. No changes made.")
        print("STEP 86 CHECK: OK")
        return

    if "</head>" not in html:
        raise SystemExit("</head> が見つかりません。docs/healthcheck.html を確認してください。")

    if "</body>" not in html:
        raise SystemExit("</body> が見つかりません。docs/healthcheck.html を確認してください。")

    html = html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)

    # preview の直前に挿入できればそこへ。無ければ body末尾へ。
    if '<h2>JSON Preview</h2>' in html:
        html = html.replace('<h2>JSON Preview</h2>', HTML_BLOCK + "\n<h2>JSON Preview</h2>", 1)
    else:
        html = html.replace("</body>", HTML_BLOCK + "\n" + SCRIPT_BLOCK + "\n</body>", 1)
        HEALTHCHECK_PATH.write_text(html, encoding="utf-8")
        print("Updated docs/healthcheck.html")
        print("Added STEP 86 EV healthcheck summary")
        print("STEP 86 CHECK: OK")
        return

    html = html.replace("</body>", SCRIPT_BLOCK + "\n</body>", 1)

    HEALTHCHECK_PATH.write_text(html, encoding="utf-8")

    print("Updated docs/healthcheck.html")
    print("Added STEP 86 EV healthcheck summary")
    print("STEP 86 CHECK: OK")


if __name__ == "__main__":
    main()
