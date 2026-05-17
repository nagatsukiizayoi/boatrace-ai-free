from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "/* STEP74_SCORE_EXPLANATION_STYLE */"
HTML_MARKER = "<!-- STEP74_SCORE_EXPLANATION_HTML -->"
SCRIPT_MARKER = "// STEP74_SCORE_EXPLANATION_SCRIPT"

STYLE_BLOCK = f"""
<style>
{STYLE_MARKER}
.score-explanation-panel {{
  max-width: 1100px;
  margin: 24px auto;
  padding: 16px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
  color: #111827;
}}

.score-explanation-panel h2 {{
  margin: 0 0 8px;
  font-size: 22px;
}}

.score-explanation-panel__note {{
  color: #64748b;
  font-size: 13px;
  margin-bottom: 14px;
  line-height: 1.6;
}}

.score-explanation-panel__status {{
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 700;
  background: #fef3c7;
  color: #92400e;
}}

.score-explanation-panel__status.ok {{
  background: #ecfdf5;
  color: #166534;
}}

.score-explanation-panel__status.ng {{
  background: #fef2f2;
  color: #991b1b;
}}

.score-explanation-panel__toolbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}}

.score-explanation-panel__toolbar button {{
  border: 0;
  border-radius: 9px;
  padding: 8px 11px;
  font-size: 12px;
  font-weight: 800;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}}

.score-explanation-panel__toolbar button.secondary {{
  background: #475569;
}}

.score-race-card {{
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px;
  margin: 12px 0;
  background: #f8fafc;
}}

.score-race-card__header {{
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 10px;
}}

.score-race-card__title {{
  font-size: 17px;
  font-weight: 900;
  color: #0f172a;
}}

.score-race-card__meta {{
  color: #64748b;
  font-size: 12px;
  margin-top: 3px;
}}

.score-race-card__badge {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 9px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 900;
}}

.score-summary {{
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
  margin: 10px 0;
  line-height: 1.6;
  font-size: 13px;
}}

.score-top-list {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
  margin: 10px 0;
}}

.score-top-item {{
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
}}

.score-top-item__label {{
  font-size: 12px;
  font-weight: 900;
  color: #2563eb;
  margin-bottom: 4px;
}}

.score-top-item__text {{
  font-size: 13px;
  color: #0f172a;
  line-height: 1.5;
}}

.score-detail-table-wrap {{
  overflow-x: auto;
  margin-top: 10px;
}}

.score-detail-table {{
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  font-size: 12px;
}}

.score-detail-table th,
.score-detail-table td {{
  border-bottom: 1px solid #e5e7eb;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}}

.score-detail-table th {{
  background: #111827;
  color: #fff;
  white-space: nowrap;
}}

.score-detail-table td.score-rank {{
  font-weight: 900;
  color: #1d4ed8;
  white-space: nowrap;
}}

.score-detail-table td.score-number {{
  font-weight: 800;
  white-space: nowrap;
}}

.score-reason {{
  min-width: 220px;
  line-height: 1.5;
}}

.score-method {{
  margin-top: 10px;
  padding: 10px;
  background: #eef2ff;
  color: #3730a3;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.6;
}}

.score-empty {{
  padding: 14px;
  background: #fff7ed;
  color: #9a3412;
  border-radius: 12px;
  font-weight: 700;
}}

@media (max-width: 640px) {{
  .score-explanation-panel {{
    margin: 16px 10px;
    padding: 12px;
  }}

  .score-race-card {{
    padding: 12px;
  }}

  .score-detail-table {{
    font-size: 11px;
  }}

  .score-detail-table th,
  .score-detail-table td {{
    padding: 7px;
  }}
}}
</style>
"""

HTML_BLOCK = f"""
{HTML_MARKER}
<section id="step74ScoreExplanationPanel" class="score-explanation-panel">
  <h2>予想スコア説明</h2>
  <div class="score-explanation-panel__note">
    prediction.json に含まれる <code>score_explanation</code> と <code>score_details</code> を表示します。
    本命・対抗・三番手の根拠、各艇のスコア、勝率、ST、評価理由を確認できます。
  </div>

  <div id="step74ScoreStatus" class="score-explanation-panel__status">
    score explanation を読み込み中です。
  </div>

  <div class="score-explanation-panel__toolbar">
    <button type="button" onclick="step74LoadScoreExplanations()">再読み込み</button>
    <button type="button" class="secondary" onclick="step74ToggleScorePanel()">表示/非表示</button>
    <button type="button" class="secondary" onclick="window.open('./prediction.json?v=' + Date.now(), '_blank')">JSONを開く</button>
  </div>

  <div id="step74ScoreContent"></div>
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
    var el = document.getElementById("step74ScoreStatus");
    if (!el) return;
    el.className = "score-explanation-panel__status " + (type || "");
    el.textContent = message;
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
    var title = "";

    if (venue) title += venue + " ";
    if (raceNo) title += raceNo + "R";
    if (raceName) title += " " + raceName;

    return title || "Race";
  }}

  function renderTopSummary(items) {{
    if (!Array.isArray(items) || items.length === 0) {{
      return "";
    }}

    return [
      '<div class="score-top-list">',
      items.map(function (text, index) {{
        var label = ["本命", "対抗", "三番手"][index] || ("候補" + (index + 1));
        return [
          '<div class="score-top-item">',
          '<div class="score-top-item__label">' + escapeHtml(label) + '</div>',
          '<div class="score-top-item__text">' + escapeHtml(text) + '</div>',
          '</div>'
        ].join("");
      }}).join(""),
      '</div>'
    ].join("");
  }}

  function renderScoreDetails(details) {{
    if (!Array.isArray(details) || details.length === 0) {{
      return '<div class="score-empty">score_details がありません。</div>';
    }}

    var rows = details.map(function (item) {{
      return [
        "<tr>",
        '<td class="score-rank">' + escapeHtml(item.rank) + '</td>',
        '<td class="score-number">' + escapeHtml(item.boat_no) + '号艇</td>',
        '<td>' + escapeHtml(item.racer_name || "") + '</td>',
        '<td class="score-number">' + escapeHtml(item.score) + '</td>',
        '<td class="score-number">' + escapeHtml(item.national_win_rate) + '</td>',
        '<td class="score-number">' + escapeHtml(item.local_win_rate) + '</td>',
        '<td class="score-number">' + escapeHtml(item.st_timing) + '</td>',
        '<td class="score-reason">' + escapeHtml(item.reason || "") + '</td>',
        "</tr>"
      ].join("");
    }}).join("");

    return [
      '<div class="score-detail-table-wrap">',
      '<table class="score-detail-table">',
      '<thead>',
      '<tr>',
      '<th>順位</th>',
      '<th>艇</th>',
      '<th>選手</th>',
      '<th>スコア</th>',
      '<th>全国勝率</th>',
      '<th>当地勝率</th>',
      '<th>ST</th>',
      '<th>理由</th>',
      '</tr>',
      '</thead>',
      '<tbody>',
      rows,
      '</tbody>',
      '</table>',
      '</div>'
    ].join("");
  }}

  function renderRaceCard(race, index) {{
    var explanation = race.score_explanation || {{}};
    var details = race.score_details || explanation.score_details || [];
    var method = race.score_method || explanation.score_method || {{}};
    var topSummary = explanation.top_summary || [];

    var favorite = explanation.favorite_boat_no || "-";
    var rival = explanation.rival_boat_no || "-";
    var darkhorse = explanation.darkhorse_boat_no || "-";

    var confidence = explanation.confidence;
    if (confidence == null || confidence === "") {{
      confidence = race.confidence || "-";
    }}

    var summary = explanation.summary || race.prediction_summary || "説明文がありません。";

    return [
      '<article class="score-race-card">',
      '<div class="score-race-card__header">',
      '<div>',
      '<div class="score-race-card__title">' + escapeHtml(getRaceTitle(race)) + '</div>',
      '<div class="score-race-card__meta">',
      '本命 ' + escapeHtml(favorite) + '号艇 / ',
      '対抗 ' + escapeHtml(rival) + '号艇 / ',
      '三番手 ' + escapeHtml(darkhorse) + '号艇',
      '</div>',
      '</div>',
      '<div class="score-race-card__badge">confidence: ' + escapeHtml(confidence) + '</div>',
      '</div>',

      '<div class="score-summary">' + escapeHtml(summary) + '</div>',
      renderTopSummary(topSummary),
      renderScoreDetails(details),

      '<div class="score-method">',
      '<strong>score method:</strong> ',
      escapeHtml(method.name || "simple_rule_score_v1"),
      '<br>',
      escapeHtml(method.description || "全国勝率、当地勝率、ST、枠番補正を組み合わせた簡易スコアです。"),
      '</div>',
      '</article>'
    ].join("");
  }}

  window.step74LoadScoreExplanations = async function () {{
    var content = document.getElementById("step74ScoreContent");
    if (!content) return;

    setStatus("", "score explanation を読み込み中です。");
    content.innerHTML = "";

    try {{
      var response = await fetch("./prediction.json?v=" + Date.now(), {{ cache: "no-store" }});
      if (!response.ok) {{
        throw new Error("HTTP " + response.status + " " + response.statusText);
      }}

      var data = await response.json();
      var races = Array.isArray(data.races) ? data.races : [];

      var explainability = data.explainability || {{}};
      var explained = races.filter(function (race) {{
        return race && (race.score_explanation || race.score_details);
      }});

      if (explained.length === 0) {{
        setStatus("ng", "score_explanation が見つかりません。enrich_prediction_json.py の実行を確認してください。");
        content.innerHTML = '<div class="score-empty">説明付きレースがありません。</div>';
        return;
      }}

      content.innerHTML = explained.map(renderRaceCard).join("");

      setStatus(
        "ok",
        "OK: " + explained.length + "件のレース説明を表示しました。 method=" + (explainability.method || "-")
      );
    }} catch (error) {{
      setStatus("ng", "NG: スコア説明の読み込みに失敗しました。 " + String(error && (error.message || error)));
      content.innerHTML = '<div class="score-empty">' + escapeHtml(String(error && (error.stack || error.message) || error)) + '</div>';
    }}
  }};

  window.step74ToggleScorePanel = function () {{
    var content = document.getElementById("step74ScoreContent");
    if (!content) return;
    content.style.display = content.style.display === "none" ? "" : "none";
  }};

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", window.step74LoadScoreExplanations);
  }} else {{
    window.step74LoadScoreExplanations();
  }}
}})();
</script>
"""

def main():
    if not INDEX_PATH.exists():
        raise SystemExit(f"{INDEX_PATH} が見つかりません")

    html = INDEX_PATH.read_text(encoding="utf-8")

    if STYLE_MARKER in html or HTML_MARKER in html or SCRIPT_MARKER in html:
        print("STEP 74 patch already exists. No changes made.")
        print("STEP 74 CHECK: OK")
        return

    if "</head>" not in html:
        raise SystemExit("</head> が見つかりません。docs/index.html を確認してください。")

    if "</body>" not in html:
        raise SystemExit("</body> が見つかりません。docs/index.html を確認してください。")

    html = html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)

    # できるだけページ本文の最後に説明パネルを追加
    html = html.replace("</body>", HTML_BLOCK + "\n" + SCRIPT_BLOCK + "\n</body>", 1)

    INDEX_PATH.write_text(html, encoding="utf-8")

    print("Updated docs/index.html")
    print("Added STEP 74 score explanation panel")
    print("STEP 74 CHECK: OK")


if __name__ == "__main__":
    main()
