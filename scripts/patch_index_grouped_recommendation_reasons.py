#!/usr/bin/env python3
from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "STEP94_GROUPED_RECOMMENDATION_REASONS_STYLE"
HTML_MARKER = "STEP94_GROUPED_RECOMMENDATION_REASONS_HTML"
SCRIPT_MARKER = "STEP94_GROUPED_RECOMMENDATION_REASONS_SCRIPT"


STYLE_BLOCK = """
<style>
/* STEP94_GROUPED_RECOMMENDATION_REASONS_STYLE */
.step94-grouped-reason-panel {
  max-width: 1100px;
  margin: 16px auto;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.step94-grouped-reason-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.step94-grouped-reason-title {
  font-size: 1.15rem;
  font-weight: 800;
}

.step94-grouped-reason-status {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #475569;
}

.step94-grouped-reason-status.ok {
  background: #dcfce7;
  color: #166534;
}

.step94-grouped-reason-status.warn {
  background: #fef3c7;
  color: #92400e;
}

.step94-grouped-reason-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.step94-grouped-race-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.step94-race-card {
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 14px;
  padding: 14px;
}

.step94-race-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.step94-race-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #0f172a;
}

.step94-race-subtitle {
  margin-top: 3px;
  font-size: 0.82rem;
  color: #64748b;
}

.step94-race-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.step94-race-badge {
  font-size: 0.78rem;
  padding: 5px 8px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
}

.step94-race-badge.high {
  background: #fee2e2;
  color: #991b1b;
}

.step94-race-badge.ev {
  background: #fef3c7;
  color: #92400e;
}

.step94-race-badge.grade {
  background: #dbeafe;
  color: #1d4ed8;
}

.step94-ticket-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.step94-ticket-card {
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 12px;
}

.step94-ticket-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.step94-ticket-title {
  font-weight: 800;
  color: #0f172a;
}

.step94-ticket-grade {
  min-width: 32px;
  text-align: center;
  border-radius: 999px;
  padding: 4px 9px;
  font-weight: 800;
  font-size: 0.8rem;
  color: #fff;
  background: #64748b;
}

.step94-grade-S {
  background: #dc2626;
}

.step94-grade-A {
  background: #ea580c;
}

.step94-grade-B {
  background: #ca8a04;
}

.step94-grade-C {
  background: #2563eb;
}

.step94-grade-UNKNOWN {
  background: #64748b;
}

.step94-ticket-metrics {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 6px 0;
}

.step94-ticket-metric {
  font-size: 0.76rem;
  padding: 4px 7px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
}

.step94-ticket-reason {
  margin-top: 7px;
  font-size: 0.9rem;
  line-height: 1.55;
  color: #334155;
}

.step94-ticket-points {
  margin: 8px 0 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.5;
  font-size: 0.86rem;
}

.step94-ticket-risk {
  margin-top: 8px;
  padding: 8px 9px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 0.82rem;
  line-height: 1.45;
}

.step94-empty {
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

@media (max-width: 640px) {
  .step94-grouped-reason-panel {
    margin: 12px 8px;
    padding: 12px;
  }

  .step94-race-card {
    padding: 12px;
  }

  .step94-grouped-reason-title {
    font-size: 1rem;
  }
}
</style>
"""


HTML_BLOCK = """
<!-- STEP94_GROUPED_RECOMMENDATION_REASONS_HTML -->
<section id="step94GroupedRecommendationReasonsPanel" class="step94-grouped-reason-panel">
  <div class="step94-grouped-reason-header">
    <div class="step94-grouped-reason-title">レース別 推奨理由サマリー</div>
    <div id="step94GroupedRecommendationReasonsStatus" class="step94-grouped-reason-status">読み込み中...</div>
  </div>

  <div id="step94GroupedRecommendationReasonsList" class="step94-grouped-race-list">
    <div class="step94-empty">prediction.json を読み込み中です。</div>
  </div>
</section>
"""


SCRIPT_BLOCK = """
<script>
// STEP94_GROUPED_RECOMMENDATION_REASONS_SCRIPT
(function () {
  const STEP94_EV_THRESHOLD = 1.2;

  function toNumber(value) {
    const n = Number(value || 0);
    return Number.isFinite(n) ? n : 0;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function setStatus(message, type) {
    const el = document.getElementById("step94GroupedRecommendationReasonsStatus");
    if (!el) return;

    el.textContent = message;
    el.classList.remove("ok", "warn", "error");

    if (type) {
      el.classList.add(type);
    }
  }

  function gradeRank(grade) {
    const ranks = { "S": 5, "A": 4, "B": 3, "C": 2, "UNKNOWN": 1 };
    return ranks[grade || "UNKNOWN"] || 1;
  }

  function bestGrade(items) {
    let best = "UNKNOWN";
    items.forEach(function (item) {
      if (gradeRank(item.value_grade) > gradeRank(best)) {
        best = item.value_grade;
      }
    });
    return best;
  }

  function gradeClass(grade) {
    const g = grade || "UNKNOWN";
    if (["S", "A", "B", "C"].includes(g)) {
      return "step94-grade-" + g;
    }
    return "step94-grade-UNKNOWN";
  }

  function ticketTitle(item) {
    return [
      item.bet_type || "-",
      item.combination || "-"
    ].join(" ");
  }

  function renderRaceCard(group) {
    const items = group.items.slice().sort(function (a, b) {
      return b.expected_value - a.expected_value;
    });

    const recommendationCount = items.length;
    const highEvCount = items.filter(function (item) {
      return item.expected_value >= STEP94_EV_THRESHOLD;
    }).length;

    const maxEv = items.reduce(function (m, item) {
      return Math.max(m, item.expected_value);
    }, 0);

    const maxOdds = items.reduce(function (m, item) {
      return Math.max(m, item.odds);
    }, 0);

    const topGrade = bestGrade(items);

    const ticketsHtml = items.map(function (item) {
      const points = Array.isArray(item.reason_points) ? item.reason_points : [];
      const pointsHtml = points.length
        ? '<ul class="step94-ticket-points">' + points.map(function (p) {
            return '<li>' + escapeHtml(p) + '</li>';
          }).join("") + '</ul>'
        : "";

      return [
        '<article class="step94-ticket-card">',
          '<div class="step94-ticket-head">',
            '<div class="step94-ticket-title">' + escapeHtml(ticketTitle(item)) + '</div>',
            '<div class="step94-ticket-grade ' + gradeClass(item.value_grade) + '">' + escapeHtml(item.value_grade || "UNKNOWN") + '</div>',
          '</div>',
          '<div class="step94-ticket-metrics">',
            '<span class="step94-ticket-metric">EV ' + item.expected_value.toFixed(2) + '</span>',
            '<span class="step94-ticket-metric">odds ' + item.odds.toFixed(2) + '</span>',
            '<span class="step94-ticket-metric">amount ' + item.amount + '</span>',
            item.probability > 0 ? '<span class="step94-ticket-metric">prob ' + item.probability.toFixed(3) + '</span>' : '',
          '</div>',
          '<div class="step94-ticket-reason">' + escapeHtml(item.recommendation_reason || "推奨理由なし") + '</div>',
          pointsHtml,
          item.risk_note ? '<div class="step94-ticket-risk">注意: ' + escapeHtml(item.risk_note) + '</div>' : '',
        '</article>'
      ].join("");
    }).join("");

    return [
      '<section class="step94-race-card">',
        '<div class="step94-race-card-header">',
          '<div>',
            '<div class="step94-race-title">' + escapeHtml(group.race_no ? group.race_no + "R" : "?R") + '</div>',
            '<div class="step94-race-subtitle">' + escapeHtml(group.venue_name || "") + '</div>',
          '</div>',
          '<div class="step94-race-badges">',
            '<span class="step94-race-badge">買い目 ' + recommendationCount + '件</span>',
            '<span class="step94-race-badge high">高EV ' + highEvCount + '件</span>',
            '<span class="step94-race-badge ev">最大EV ' + maxEv.toFixed(2) + '</span>',
            '<span class="step94-race-badge">最大odds ' + maxOdds.toFixed(2) + '</span>',
            '<span class="step94-race-badge grade">最高Grade ' + escapeHtml(topGrade) + '</span>',
          '</div>',
        '</div>',
        '<div class="step94-ticket-list">',
          ticketsHtml,
        '</div>',
      '</section>'
    ].join("");
  }

  async function loadGroupedRecommendationReasons() {
    const panel = document.getElementById("step94GroupedRecommendationReasonsPanel");
    if (!panel) return;

    const list = document.getElementById("step94GroupedRecommendationReasonsList");

    try {
      setStatus("読み込み中...", "");

      const response = await fetch("./prediction.json?v=94-" + Date.now(), {
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error("prediction.json fetch failed: HTTP " + response.status);
      }

      const data = await response.json();
      const races = Array.isArray(data.races) ? data.races : [];

      const groups = [];

      races.forEach(function (race) {
        const recs = Array.isArray(race.recommendations) ? race.recommendations : [];
        const items = [];

        recs.forEach(function (rec) {
          items.push({
            race_no: race.race_no || race.race_number || "",
            venue_name: race.venue_name || race.venue || "",
            bet_type: rec.bet_type || "",
            combination: rec.combination || "",
            odds: toNumber(rec.odds),
            expected_value: toNumber(rec.expected_value),
            amount: toNumber(rec.amount),
            probability: toNumber(rec.probability),
            recommendation_reason: rec.recommendation_reason || "",
            reason_points: Array.isArray(rec.reason_points) ? rec.reason_points : [],
            value_grade: rec.value_grade || "UNKNOWN",
            risk_note: rec.risk_note || "",
            reason_version: rec.reason_version || ""
          });
        });

        if (items.length > 0) {
          groups.push({
            race_no: race.race_no || race.race_number || "",
            venue_name: race.venue_name || race.venue || "",
            items: items
          });
        }
      });

      if (!list) return;

      if (groups.length === 0) {
        list.innerHTML = '<div class="step94-empty">推奨理由つきのレースがありません。</div>';
        setStatus("WARN: 表示対象がありません", "warn");
        return;
      }

      groups.sort(function (a, b) {
        return toNumber(a.race_no) - toNumber(b.race_no);
      });

      list.innerHTML = groups.map(renderRaceCard).join("");

      const totalItems = groups.reduce(function (sum, g) {
        return sum + g.items.length;
      }, 0);

      const highEvItems = groups.reduce(function (sum, g) {
        return sum + g.items.filter(function (item) {
          return item.expected_value >= STEP94_EV_THRESHOLD;
        }).length;
      }, 0);

      setStatus("OK: " + groups.length + "レース / " + totalItems + "件の推奨理由を表示しました", "ok");

      if (highEvItems === 0) {
        setStatus("WARN: 高EV推奨理由がありません", "warn");
      }
    } catch (error) {
      console.error("STEP94 grouped recommendation reasons error:", error);
      setStatus("ERROR: " + error.message, "error");

      if (list) {
        list.innerHTML = '<div class="step94-empty">レース別 推奨理由サマリーの読み込みに失敗しました。</div>';
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadGroupedRecommendationReasons);
  } else {
    loadGroupedRecommendationReasons();
  }

  window.step94LoadGroupedRecommendationReasons = loadGroupedRecommendationReasons;
})();
</script>
"""


def insert_before(text: str, marker: str, block: str, closing_tag: str) -> str:
    if marker in text:
        print(f"Already exists: {marker}")
        return text

    index = text.lower().rfind(closing_tag.lower())
    if index == -1:
        raise SystemExit(f"Could not find closing tag: {closing_tag}")

    return text[:index] + block + "\n" + text[index:]


def main() -> None:
    if not INDEX_PATH.exists():
        raise SystemExit("docs/index.html does not exist")

    text = INDEX_PATH.read_text(encoding="utf-8")
    original = text

    text = insert_before(text, STYLE_MARKER, STYLE_BLOCK, "</head>")
    text = insert_before(text, HTML_MARKER, HTML_BLOCK, "</body>")
    text = insert_before(text, SCRIPT_MARKER, SCRIPT_BLOCK, "</body>")

    if text != original:
        INDEX_PATH.write_text(text, encoding="utf-8")
        print("Updated docs/index.html")
    else:
        print("No changes needed")

    final = INDEX_PATH.read_text(encoding="utf-8")

    required_tokens = [
        STYLE_MARKER,
        HTML_MARKER,
        SCRIPT_MARKER,
        "step94GroupedRecommendationReasonsPanel",
        "step94GroupedRecommendationReasonsStatus",
        "step94GroupedRecommendationReasonsList",
        "step94LoadGroupedRecommendationReasons",
        "recommendation_reason",
        "reason_points",
        "value_grade",
        "risk_note",
        "レース別 推奨理由サマリー",
    ]

    missing = [token for token in required_tokens if token not in final]
    if missing:
        raise SystemExit(f"Missing inserted tokens: {missing}")

    print("Added STEP 94 grouped recommendation reasons panel")
    print("STEP 94 CHECK: OK")


if __name__ == "__main__":
    main()
