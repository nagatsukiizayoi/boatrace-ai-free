from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "/* STEP84_EV_TICKET_BADGE_STYLE */"
HTML_MARKER = "<!-- STEP84_EV_TICKET_BADGE_HTML -->"
SCRIPT_MARKER = "// STEP84_EV_TICKET_BADGE_SCRIPT"

STYLE_BLOCK = f"""
<style>
{STYLE_MARKER}
.ev-ticket-badge-panel {{
  max-width: 1100px;
  margin: 24px auto;
  padding: 16px;
  border-radius: 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  box-shadow: 0 4px 18px rgba(22, 163, 74, 0.12);
  color: #111827;
}}

.ev-ticket-badge-panel h2 {{
  margin: 0 0 8px;
  font-size: 22px;
  color: #166534;
}}

.ev-ticket-badge-panel__note {{
  color: #166534;
  font-size: 13px;
  margin-bottom: 14px;
  line-height: 1.6;
}}

.ev-ticket-badge-panel__status {{
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 800;
  background: #dcfce7;
  color: #166534;
}}

.ev-ticket-badge-panel__status.ok {{
  background: #ecfdf5;
  color: #166534;
}}

.ev-ticket-badge-panel__status.ng {{
  background: #fef2f2;
  color: #991b1b;
}}

.ev-ticket-badge-panel__toolbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}}

.ev-ticket-badge-panel__toolbar button {{
  border: 0;
  border-radius: 9px;
  padding: 8px 11px;
  font-size: 12px;
  font-weight: 800;
  background: #16a34a;
  color: #fff;
  cursor: pointer;
}}

.ev-ticket-badge-panel__toolbar button.secondary {{
  background: #475569;
}}

.ev-ticket-badge-summary {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}}

.ev-ticket-badge-summary__item {{
  background: #ffffff;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 10px;
}}

.ev-ticket-badge-summary__label {{
  font-size: 12px;
  color: #166534;
  font-weight: 800;
  margin-bottom: 4px;
}}

.ev-ticket-badge-summary__value {{
  font-size: 22px;
  font-weight: 900;
  color: #15803d;
}}

.ev-race-card {{
  background: #ffffff;
  border: 1px solid #bbf7d0;
  border-radius: 14px;
  padding: 14px;
  margin: 12px 0;
}}

.ev-race-card__header {{
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}}

.ev-race-card__title {{
  font-size: 16px;
  font-weight: 900;
  color: #14532d;
}}

.ev-race-card__badge {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 10px;
  background: #16a34a;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}}

.ev-ticket-list {{
  display: grid;
  gap: 8px;
}}

.ev-ticket-item {{
  border: 1px solid #bbf7d0;
  border-left: 6px solid #16a34a;
  border-radius: 12px;
  padding: 10px;
  background: #f0fdf4;
}}

.ev-ticket-item__top {{
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}}

.ev-ticket-item__name {{
  font-size: 14px;
  font-weight: 900;
  color: #14532d;
}}

.ev-ticket-item__ev {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  background: #15803d;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}}

.ev-ticket-item__metrics {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 8px;
}}

.ev-ticket-item__metric {{
  background: #ffffff;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 8px;
}}

.ev-ticket-item__metric-label {{
  color: #166534;
  font-size: 11px;
  font-weight: 800;
  margin-bottom: 3px;
}}

.ev-ticket-item__metric-value {{
  color: #111827;
  font-size: 14px;
  font-weight: 900;
  word-break: break-all;
}}

.ev-ticket-empty {{
  padding: 14px;
  background: #ffffff;
  color: #166534;
  border: 1px dashed #86efac;
  border-radius: 12px;
  font-weight: 800;
}}

@media (max-width: 640px) {{
  .ev-ticket-badge-panel {{
    margin: 16px 10px;
    padding: 12px;
  }}

  .ev-race-card {{
    padding: 12px;
  }}
}}
</style>
"""

HTML_BLOCK = f"""
{HTML_MARKER}
<section id="step84EvTicketBadgePanel" class="ev-ticket-badge-panel">
  <h2>レース別 EV高 買い目</h2>
  <div class="ev-ticket-badge-panel__note">
    prediction.json の <code>recommendations</code> から、
    <code>expected_value >= 1.2</code> の買い目をレース別に表示します。
    期待値が高い買い目を素早く確認するためのパネルです。
  </div>

  <div id="step84EvTicketBadgeStatus" class="ev-ticket-badge-panel__status">
    EV高買い目を読み込み中です。
  </div>

  <div class="ev-ticket-badge-panel__toolbar">
    <button type="button" onclick="step84LoadEvTicketBadges()">再読み込み</button>
    <button type="button" class="secondary" onclick="step84ToggleEvTicketBadges()">表示/非表示</button>
    <button type="button" class="secondary" onclick="window.open('./prediction.json?v=' + Date.now(), '_blank')">JSONを開く</button>
  </div>

  <div id="step84EvTicketBadgeContent"></div>
</section>
"""

SCRIPT_BLOCK = f"""
<script>
{SCRIPT_MARKER}
(function () {{
  var STEP84_EV_THRESHOLD = 1.2;

  function escapeHtml(value) {{
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }}

  function setStatus(type, message) {{
    var el = document.getElementById("step84EvTicketBadgeStatus");
    if (!el) return;
    el.className = "ev-ticket-badge-panel__status " + (type || "");
    el.textContent = message;
  }}

  function toNumber(value, fallback) {{
    var n = Number(value);
    if (!Number.isFinite(n)) return fallback || 0;
    return n;
  }}

  function numberText(value, digits) {{
    var n = Number(value);
    if (!Number.isFinite(n)) return "-";
    return n.toFixed(digits);
  }}

  function getRaceTitle(race) {{
    var venue = "";

    if (typeof race.venue === "string") {{
      venue = race.venue;
    }} else if (race.venue && typeof race.venue === "object") {{
      venue = race.venue.name || race.venue.venue_name || race.venue.code || "";
    }} else {{
      venue = race.venue_name || "";
    }}

    var raceNo = race.race_no || race.raceNo || race.race_number || "";
    var raceName = race.race_name || race.name || "";

    var parts = [];
    if (venue) parts.push(venue);
    if (raceNo) parts.push(raceNo + "R");
    if (raceName) parts.push(raceName);

    return parts.join(" ") || "Race";
  }}

  function getTicketCombination(ticket) {{
    return (
      ticket.combination ||
      ticket.ticket ||
      ticket.buy ||
      ticket.bet ||
      ""
    );
  }}

  function getTicketBetType(ticket) {{
    return (
      ticket.bet_type ||
      ticket.type ||
      ticket.ticket_type ||
      ""
    );
  }}

  function getEvTicketsByRace(races) {{
    var result = [];

    races.forEach(function (race) {{
      var recommendations = Array.isArray(race.recommendations) ? race.recommendations : [];
      var evTickets = recommendations.filter(function (ticket) {{
        var ev = toNumber(ticket.expected_value, 0);
        return ev >= STEP84_EV_THRESHOLD;
      }});

      if (evTickets.length > 0) {{
        evTickets.sort(function (a, b) {{
          return toNumber(b.expected_value, 0) - toNumber(a.expected_value, 0);
        }});

        result.push({{
          race: race,
          tickets: evTickets
        }});
      }}
    }});

    return result;
  }}

  function renderSummary(groups) {{
    var raceCount = groups.length;
    var ticketCount = 0;
    var maxEv = 0;
    var maxOdds = 0;

    groups.forEach(function (group) {{
      ticketCount += group.tickets.length;

      group.tickets.forEach(function (ticket) {{
        var ev = toNumber(ticket.expected_value, 0);
        var odds = toNumber(ticket.odds, 0);

        if (ev > maxEv) maxEv = ev;
        if (odds > maxOdds) maxOdds = odds;
      }});
    }});

    return [
      '<div class="ev-ticket-badge-summary">',
      '<div class="ev-ticket-badge-summary__item">',
      '<div class="ev-ticket-badge-summary__label">対象レース</div>',
      '<div class="ev-ticket-badge-summary__value">' + escapeHtml(raceCount) + '</div>',
      '</div>',
      '<div class="ev-ticket-badge-summary__item">',
      '<div class="ev-ticket-badge-summary__label">EV高買い目</div>',
      '<div class="ev-ticket-badge-summary__value">' + escapeHtml(ticketCount) + '</div>',
      '</div>',
      '<div class="ev-ticket-badge-summary__item">',
      '<div class="ev-ticket-badge-summary__label">最大EV</div>',
      '<div class="ev-ticket-badge-summary__value">' + escapeHtml(maxEv ? maxEv.toFixed(3) : "-") + '</div>',
      '</div>',
      '<div class="ev-ticket-badge-summary__item">',
      '<div class="ev-ticket-badge-summary__label">最大オッズ</div>',
      '<div class="ev-ticket-badge-summary__value">' + escapeHtml(maxOdds ? maxOdds.toFixed(2) : "-") + '</div>',
      '</div>',
      '</div>'
    ].join("");
  }}

  function renderTicket(ticket) {{
    var betType = getTicketBetType(ticket);
    var combination = getTicketCombination(ticket);
    var odds = ticket.odds;
    var ev = ticket.expected_value;
    var amount = ticket.amount;
    var confidence = ticket.confidence;
    var memo = ticket.memo || ticket.reason || "";

    return [
      '<div class="ev-ticket-item">',
      '<div class="ev-ticket-item__top">',
      '<div class="ev-ticket-item__name">',
      escapeHtml(betType || "-") + ' ' + escapeHtml(combination || "-"),
      '</div>',
      '<div class="ev-ticket-item__ev">EV高 ' + escapeHtml(numberText(ev, 3)) + '</div>',
      '</div>',

      '<div class="ev-ticket-item__metrics">',
      '<div class="ev-ticket-item__metric">',
      '<div class="ev-ticket-item__metric-label">オッズ</div>',
      '<div class="ev-ticket-item__metric-value">' + escapeHtml(numberText(odds, 2)) + '</div>',
      '</div>',

      '<div class="ev-ticket-item__metric">',
      '<div class="ev-ticket-item__metric-label">期待値</div>',
      '<div class="ev-ticket-item__metric-value">' + escapeHtml(numberText(ev, 3)) + '</div>',
      '</div>',

      '<div class="ev-ticket-item__metric">',
      '<div class="ev-ticket-item__metric-label">金額</div>',
      '<div class="ev-ticket-item__metric-value">' + escapeHtml(amount || "-") + '</div>',
      '</div>',

      '<div class="ev-ticket-item__metric">',
      '<div class="ev-ticket-item__metric-label">信頼度</div>',
      '<div class="ev-ticket-item__metric-value">' + escapeHtml(confidence == null ? "-" : confidence) + '</div>',
      '</div>',

      '</div>',

      memo ? '<div style="margin-top:8px;font-size:12px;line-height:1.5;color:#166534;">' + escapeHtml(memo) + '</div>' : '',
      '</div>'
    ].join("");
  }}

  function renderRaceGroup(group) {{
    var race = group.race;
    var tickets = group.tickets;

    return [
      '<article class="ev-race-card">',
      '<div class="ev-race-card__header">',
      '<div class="ev-race-card__title">' + escapeHtml(getRaceTitle(race)) + '</div>',
      '<div class="ev-race-card__badge">' + escapeHtml(tickets.length) + '件</div>',
      '</div>',
      '<div class="ev-ticket-list">',
      tickets.map(renderTicket).join(""),
      '</div>',
      '</article>'
    ].join("");
  }}

  window.step84LoadEvTicketBadges = async function () {{
    var content = document.getElementById("step84EvTicketBadgeContent");
    if (!content) return;

    setStatus("", "EV高買い目を読み込み中です。");
    content.innerHTML = "";

    try {{
      var response = await fetch("./prediction.json?v=" + Date.now(), {{ cache: "no-store" }});

      if (!response.ok) {{
        throw new Error("HTTP " + response.status + " " + response.statusText);
      }}

      var data = await response.json();
      var races = Array.isArray(data.races) ? data.races : [];
      var groups = getEvTicketsByRace(races);

      if (groups.length === 0) {{
        setStatus("ng", "EV高買い目は見つかりませんでした。expected_value の値を確認してください。");
        content.innerHTML = '<div class="ev-ticket-empty">expected_value >= ' + STEP84_EV_THRESHOLD + ' の買い目はありません。</div>';
        return;
      }}

      content.innerHTML =
        renderSummary(groups) +
        groups.map(renderRaceGroup).join("");

      var totalTickets = groups.reduce(function (sum, group) {{
        return sum + group.tickets.length;
      }}, 0);

      setStatus(
        "ok",
        "OK: " + groups.length + "レース / " + totalTickets + "件のEV高買い目を表示しました。"
      );
    }} catch (error) {{
      setStatus("ng", "NG: EV高買い目の読み込みに失敗しました。 " + String(error && (error.message || error)));
      content.innerHTML = '<div class="ev-ticket-empty">' + escapeHtml(String(error && (error.stack || error.message) || error)) + '</div>';
    }}
  }};

  window.step84ToggleEvTicketBadges = function () {{
    var content = document.getElementById("step84EvTicketBadgeContent");
    if (!content) return;
    content.style.display = content.style.display === "none" ? "" : "none";
  }};

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", window.step84LoadEvTicketBadges);
  }} else {{
    window.step84LoadEvTicketBadges();
  }}
}})();
</script>
"""

def main():
    if not INDEX_PATH.exists():
        raise SystemExit(f"{INDEX_PATH} が見つかりません")

    html = INDEX_PATH.read_text(encoding="utf-8")

    if STYLE_MARKER in html or HTML_MARKER in html or SCRIPT_MARKER in html:
        print("STEP 84 patch already exists. No changes made.")
        print("STEP 84 CHECK: OK")
        return

    if "</head>" not in html:
        raise SystemExit("</head> が見つかりません。docs/index.html を確認してください。")

    if "</body>" not in html:
        raise SystemExit("</body> が見つかりません。docs/index.html を確認してください。")

    html = html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)
    html = html.replace("</body>", HTML_BLOCK + "\n" + SCRIPT_BLOCK + "\n</body>", 1)

    INDEX_PATH.write_text(html, encoding="utf-8")

    print("Updated docs/index.html")
    print("Added STEP 84 EV ticket badge panel")
    print("STEP 84 CHECK: OK")


if __name__ == "__main__":
    main()
