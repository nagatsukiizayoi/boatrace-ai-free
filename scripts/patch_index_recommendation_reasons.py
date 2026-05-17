#!/usr/bin/env python3
from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "STEP92_RECOMMENDATION_REASONS_STYLE"
HTML_MARKER = "STEP92_RECOMMENDATION_REASONS_HTML"
SCRIPT_MARKER = "STEP92_RECOMMENDATION_REASONS_SCRIPT"


STYLE_BLOCK = """
<style>
/* STEP92_RECOMMENDATION_REASONS_STYLE */
.step92-reason-panel {
  max-width: 1100px;
  margin: 16px auto;
  padding: 16px;
  border-radius: 14px;
  background: #ffffff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.step92-reason-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.step92-reason-title {
  font-size: 1.15rem;
  font-weight: 800;
}

.step92-reason-status {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
}

.step92-reason-status.ok {
  background: #dcfce7;
  color: #166534;
}

.step92-reason-status.warn {
  background: #fef3c7;
  color: #92400e;
}

.step92-reason-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.step92-reason-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.step92-reason-filter {
  padding: 7px 10px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  font-size: 0.9rem;
}

.step92-reason-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.step92-reason-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 14px;
}

.step92-reason-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.step92-reason-ticket {
  font-weight: 800;
  color: #0f172a;
}

.step92-reason-grade {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  height: 26px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 800;
  color: #ffffff;
  background: #64748b;
}

.step92-reason-grade-S {
  background: #dc2626;
}

.step92-reason-grade-A {
  background: #ea580c;
}

.step92-reason-grade-B {
  background: #ca8a04;
}

.step92-reason-grade-C {
  background: #2563eb;
}

.step92-reason-grade-UNKNOWN {
  background: #64748b;
}

.step92-reason-main {
  margin: 8px 0;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #334155;
}

.step92-reason-metrics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0;
}

.step92-reason-metric {
  font-size: 0.78rem;
  padding: 4px 8px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
}

.step92-reason-points {
  margin: 8px 0 0;
  padding-left: 20px;
  color: #334155;
  line-height: 1.55;
  font-size: 0.9rem;
}

.step92-reason-risk {
  margin-top: 10px;
  padding: 9px 10px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 0.86rem;
  line-height: 1.5;
}

.step92-reason-empty {
  color: #64748b;
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
}

@media (max-width: 640px) {
  .step92-reason-panel {
    margin: 12px 8px;
    padding: 12px;
  }

  .step92-reason-card {
    padding: 12px;
  }

  .step92-reason-title {
    font-size: 1rem;
  }
}
</style>
"""


HTML_BLOCK = """
<!-- STEP92_RECOMMENDATION_REASONS_HTML -->
<section id="step92RecommendationReasonsPanel" class="step92-reason-panel">
  <div class="step92-reason-header">
    <div class="step92-reason-title">買い目別 推奨理由</div>
    <div id="step92RecommendationReasonsStatus" class="step92-reason-status">読み込み中...</div>
  </div>

  <div class="step92-reason-controls">
    <select id="step92ReasonGradeFilter" class="step92-reason-filter">
      <option value="ALL">全グレード</option>
      <option value="S">Sのみ</option>
      <option value="A">Aのみ</option>
      <option value="B">Bのみ</option>
      <option value="C">Cのみ</option>
      <option value="UNKNOWN">UNKNOWNのみ</option>
    </select>

    <select id="step92ReasonEvFilter" class="step92-reason-filter">
      <option value="ALL">全EV</option>
      <option value="HIGH">高EVのみ EV>=1.2</option>
    </select>
  </div>

  <div id="step92RecommendationReasonsList" class="step92-reason-list">
    <div class="step92-reason-empty">prediction.json を読み込み中です。</div>
  </div>
</section>
"""


SCRIPT_BLOCK = """
<script>
// STEP92_RECOMMENDATION_REASONS_SCRIPT
(function () {
  const STEP92_EV_THRESHOLD = 1.2;
  let step92ReasonItems = [];

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
    const el = document.getElementById("step92RecommendationReasonsStatus");
    if (!el) return;

    el.textContent = message;
    el.classList.remove("ok", "warn", "error");

    if (type) {
      el.classList.add(type);
    }
  }

  function ticketLabel(item) {
    const raceNo = item.race_no ? item.race_no + "R" : "?R";
    const betType = item.bet_type || "-";
    const combination = item.combination || "-";
    return raceNo + " " + betType + " " + combination;
  }

  function gradeClass(grade) {
    const g = grade || "UNKNOWN";
    if (["S", "A", "B", "C"].includes(g)) {
      return "step92-reason-grade-" + g;
    }
    return "step92-reason-grade-UNKNOWN";
  }

  function renderReasons() {
    const list = document.getElementById("step92RecommendationReasonsList");
    if (!list) return;

    const gradeFilter = document.getElementById("step92ReasonGradeFilter");
    const evFilter = document.getElementById("step92ReasonEvFilter");

    const gradeValue = gradeFilter ? gradeFilter.value : "ALL";
    const evValue = evFilter ? evFilter.value : "ALL";

    let items = step92ReasonItems.slice();

    if (gradeValue !== "ALL") {
      items = items.filter(function (item) {
        return (item.value_grade || "UNKNOWN") === gradeValue;
      });
    }

    if (evValue === "HIGH") {
      items = items.filter(function (item) {
        return item.expected_value >= STEP92_EV_THRESHOLD;
      });
    }

    items.sort(function (a, b) {
      return b.expected_value - a.expected_value;
    });

    if (items.length === 0) {
      list.innerHTML = '<div class="step92-reason-empty">表示対象の推奨理由がありません。</div>';
      setStatus("WARN: 表示対象がありません", "warn");
      return;
    }

    list.innerHTML = items.map(function (item) {
      const points = Array.isArray(item.reason_points) ? item.reason_points : [];
      const pointsHtml = points.length
        ? "<ul class=\\"step92-reason-points\\">" + points.map(function (p) {
            return "<li>" + escapeHtml(p) + "</li>";
          }).join("") + "</ul>"
        : "";

      return [
        '<article class="step92-reason-card">',
          '<div class="step92-reason-card-head">',
            '<div class="step92-reason-ticket">' + escapeHtml(ticketLabel(item)) + '</div>',
            '<div class="step92-reason-grade ' + gradeClass(item.value_grade) + '">' + escapeHtml(item.value_grade || "UNKNOWN") + '</div>',
          '</div>',
          '<div class="step92-reason-metrics">',
            '<span class="step92-reason-metric">EV ' + item.expected_value.toFixed(2) + '</span>',
            '<span class="step92-reason-metric">odds ' + item.odds.toFixed(2) + '</span>',
            '<span class="step92-reason-metric">amount ' + item.amount + '</span>',
            item.probability > 0 ? '<span class="step92-reason-metric">prob ' + item.probability.toFixed(3) + '</span>' : '',
          '</div>',
          '<div class="step92-reason-main">' + escapeHtml(item.recommendation_reason || "推奨理由なし") + '</div>',
          pointsHtml,
          item.risk_note ? '<div class="step92-reason-risk">注意: ' + escapeHtml(item.risk_note) + '</div>' : '',
        '</article>'
      ].join("");
    }).join("");

    setStatus("OK: " + items.length + "件の推奨理由を表示しました", "ok");
  }

  async function loadRecommendationReasons() {
    const panel = document.getElementById("step92RecommendationReasonsPanel");
    if (!panel) return;

    try {
      setStatus("読み込み中...", "");

      const response = await fetch("./prediction.json?v=92-" + Date.now(), {
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error("prediction.json fetch failed: HTTP " + response.status);
      }

      const data = await response.json();
      const races = Array.isArray(data.races) ? data.races : [];

      const items = [];

      races.forEach(function (race) {
        const recs = Array.isArray(race.recommendations) ? race.recommendations : [];

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
      });

      step92ReasonItems = items;

      const withReason = items.filter(function (item) {
        return item.recommendation_reason && item.reason_points.length > 0;
      }).length;

      if (items.length === 0) {
        setStatus("WARN: recommendations がありません", "warn");
      } else if (withReason === 0) {
        setStatus("WARN: 推奨理由がありません", "warn");
      } else {
        setStatus("OK: " + withReason + "件の推奨理由を読み込みました", "ok");
      }

      renderReasons();
    } catch (error) {
      console.error("STEP92 recommendation reasons error:", error);
      setStatus("ERROR: " + error.message, "error");

      const list = document.getElementById("step92RecommendationReasonsList");
      if (list) {
        list.innerHTML = '<div class="step92-reason-empty">推奨理由の読み込みに失敗しました。</div>';
      }
    }
  }

  function setupFilters() {
    const gradeFilter = document.getElementById("step92ReasonGradeFilter");
    const evFilter = document.getElementById("step92ReasonEvFilter");

    if (gradeFilter) {
      gradeFilter.addEventListener("change", renderReasons);
    }

    if (evFilter) {
      evFilter.addEventListener("change", renderReasons);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setupFilters();
      loadRecommendationReasons();
    });
  } else {
    setupFilters();
    loadRecommendationReasons();
  }

  window.step92LoadRecommendationReasons = loadRecommendationReasons;
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
        "step92RecommendationReasonsPanel",
        "step92RecommendationReasonsStatus",
        "step92RecommendationReasonsList",
        "step92LoadRecommendationReasons",
        "recommendation_reason",
        "reason_points",
        "value_grade",
        "risk_note",
        "買い目別 推奨理由",
    ]

    missing = [token for token in required_tokens if token not in final]
    if missing:
        raise SystemExit(f"Missing inserted tokens: {missing}")

    print("Added STEP 92 recommendation reasons panel")
    print("STEP 92 CHECK: OK")


if __name__ == "__main__":
    main()
