#!/usr/bin/env python3
from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "STEP98_QUALITY_SCORE_CARDS_STYLE"
HTML_MARKER = "STEP98_QUALITY_SCORE_CARDS_HTML"
SCRIPT_MARKER = "STEP98_QUALITY_SCORE_CARDS_SCRIPT"


STYLE_BLOCK = """
<style>
/* STEP98_QUALITY_SCORE_CARDS_STYLE */
.step98-quality-panel {
  max-width: 1100px;
  margin: 16px auto;
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #111827, #1e293b);
  color: #f8fafc;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.step98-quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.step98-quality-title {
  font-size: 1.15rem;
  font-weight: 800;
}

.step98-quality-status {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
}

.step98-quality-status.ok {
  background: rgba(34, 197, 94, 0.18);
  color: #bbf7d0;
}

.step98-quality-status.warn {
  background: rgba(245, 158, 11, 0.18);
  color: #fde68a;
}

.step98-quality-status.error {
  background: rgba(239, 68, 68, 0.18);
  color: #fecaca;
}

.step98-quality-main {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  align-items: stretch;
}

.step98-score-card {
  border-radius: 14px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.16);
  text-align: center;
}

.step98-score-label {
  font-size: 0.82rem;
  color: #cbd5e1;
  margin-bottom: 6px;
}

.step98-score-value {
  font-size: 2.2rem;
  font-weight: 900;
  line-height: 1;
}

.step98-score-max {
  margin-top: 4px;
  font-size: 0.85rem;
  color: #94a3b8;
}

.step98-score-grade {
  display: inline-block;
  margin-top: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.86rem;
}

.step98-score-grade.excellent {
  background: #dcfce7;
  color: #166534;
}

.step98-score-grade.good {
  background: #dbeafe;
  color: #1d4ed8;
}

.step98-score-grade.warn {
  background: #fef3c7;
  color: #92400e;
}

.step98-score-grade.bad {
  background: #fee2e2;
  color: #991b1b;
}

.step98-quality-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.step98-quality-metric {
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.16);
}

.step98-quality-metric-label {
  font-size: 0.76rem;
  color: #cbd5e1;
  margin-bottom: 5px;
}

.step98-quality-metric-value {
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffffff;
}

.step98-quality-metric-sub {
  margin-top: 3px;
  font-size: 0.72rem;
  color: #94a3b8;
}

.step98-quality-preview {
  margin-top: 14px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.07);
  color: #e2e8f0;
  font-size: 0.86rem;
  line-height: 1.6;
}

.step98-quality-preview code {
  color: #fde68a;
}

@media (max-width: 900px) {
  .step98-quality-main {
    grid-template-columns: 1fr;
  }

  .step98-quality-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .step98-quality-panel {
    margin: 12px 8px;
    padding: 12px;
  }

  .step98-quality-grid {
    grid-template-columns: 1fr;
  }

  .step98-score-value {
    font-size: 1.9rem;
  }
}
</style>
"""


HTML_BLOCK = """
<!-- STEP98_QUALITY_SCORE_CARDS_HTML -->
<section id="step98QualityScorePanel" class="step98-quality-panel">
  <div class="step98-quality-header">
    <div class="step98-quality-title">予想データ品質スコア</div>
    <div id="step98QualityStatus" class="step98-quality-status">読み込み中...</div>
  </div>

  <div class="step98-quality-main">
    <div class="step98-score-card">
      <div class="step98-score-label">Quality Score</div>
      <div id="step98QualityScore" class="step98-score-value">-</div>
      <div class="step98-score-max">/ 100</div>
      <div id="step98QualityGrade" class="step98-score-grade warn">判定待ち</div>
    </div>

    <div class="step98-quality-grid">
      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">recommendations</div>
        <div id="step98TotalRecommendations" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">総買い目数</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">odds反映</div>
        <div id="step98OddsCount" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">odds &gt; 0</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">EV反映</div>
        <div id="step98EvCount" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">expected_value &gt; 0</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">高EV買い目</div>
        <div id="step98HighEvCount" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">EV &gt;= 1.2</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">推奨理由つき</div>
        <div id="step98ReasonCount" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">recommendation_reason</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">理由ポイント</div>
        <div id="step98ReasonPointsCount" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">reason_points</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">期待値アラート</div>
        <div id="step98ExpectedValueAlerts" class="step98-quality-metric-value">-</div>
        <div class="step98-quality-metric-sub">alerts</div>
      </div>

      <div class="step98-quality-metric">
        <div class="step98-quality-metric-label">対象レース</div>
        <div id="step98RaceCount" class="step98-quality-metric-value">-</div>
        <div id="step98UpdatedAt" class="step98-quality-metric-sub">-</div>
      </div>
    </div>
  </div>

  <div id="step98QualityPreview" class="step98-quality-preview">
    prediction.json を読み込み中です。
  </div>
</section>
"""


SCRIPT_BLOCK = """
<script>
// STEP98_QUALITY_SCORE_CARDS_SCRIPT
(function () {
  const STEP98_HIGH_EV_THRESHOLD = 1.2;

  function toNumber(value) {
    const n = Number(value || 0);
    return Number.isFinite(n) ? n : 0;
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function setStatus(message, type) {
    const el = document.getElementById("step98QualityStatus");
    if (!el) return;

    el.textContent = message;
    el.classList.remove("ok", "warn", "error");

    if (type) el.classList.add(type);
  }

  function hasText(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function expectedValueAlert(alert) {
    const text = JSON.stringify(alert || {});
    return text.includes("期待値") || text.includes("expected_value") || text.includes("EV");
  }

  function scoreGrade(score) {
    if (score >= 90) return { text: "EXCELLENT", cls: "excellent" };
    if (score >= 75) return { text: "GOOD", cls: "good" };
    if (score >= 60) return { text: "WARN", cls: "warn" };
    return { text: "BAD", cls: "bad" };
  }

  function ratioScore(count, total, weight) {
    if (total <= 0) return 0;
    return Math.round((count / total) * weight);
  }

  async function loadStep98QualityScore() {
    const panel = document.getElementById("step98QualityScorePanel");
    if (!panel) return;

    try {
      setStatus("読み込み中...", "");

      const response = await fetch("./prediction.json?v=98-" + Date.now(), {
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error("prediction.json fetch failed: HTTP " + response.status);
      }

      const data = await response.json();
      const races = Array.isArray(data.races) ? data.races : [];
      const alerts = Array.isArray(data.alerts) ? data.alerts : [];
      const reasoning = data.recommendation_reasoning || {};

      const recommendations = [];

      races.forEach(function (race) {
        const recs = Array.isArray(race.recommendations) ? race.recommendations : [];
        recs.forEach(function (rec) {
          recommendations.push({
            race_no: race.race_no || race.race_number || "",
            bet_type: rec.bet_type || "",
            combination: rec.combination || "",
            odds: toNumber(rec.odds),
            expected_value: toNumber(rec.expected_value),
            recommendation_reason: rec.recommendation_reason || "",
            reason_points: Array.isArray(rec.reason_points) ? rec.reason_points : [],
            risk_note: rec.risk_note || "",
            value_grade: rec.value_grade || "UNKNOWN"
          });
        });
      });

      const total = recommendations.length;
      const oddsCount = recommendations.filter(function (r) { return r.odds > 0; }).length;
      const evCount = recommendations.filter(function (r) { return r.expected_value > 0; }).length;
      const highEvCount = recommendations.filter(function (r) { return r.expected_value >= STEP98_HIGH_EV_THRESHOLD; }).length;
      const reasonCount = recommendations.filter(function (r) { return hasText(r.recommendation_reason); }).length;
      const pointsCount = recommendations.filter(function (r) { return r.reason_points.length >= 2; }).length;
      const riskCount = recommendations.filter(function (r) { return hasText(r.risk_note); }).length;
      const expectedValueAlerts = alerts.filter(expectedValueAlert).length;

      let score = 0;

      score += races.length > 0 ? 10 : 0;
      score += total > 0 ? 10 : 0;
      score += ratioScore(oddsCount, total, 15);
      score += ratioScore(evCount, total, 15);
      score += highEvCount > 0 ? 10 : 0;
      score += expectedValueAlerts > 0 ? 10 : 0;
      score += ratioScore(reasonCount, total, 15);
      score += ratioScore(pointsCount, total, 10);
      score += ratioScore(riskCount, total, 5);
      score += reasoning.enabled === true ? 10 : 0;

      if (score > 100) score = 100;

      const grade = scoreGrade(score);

      setText("step98QualityScore", String(score));
      setText("step98QualityGrade", grade.text);
      setText("step98TotalRecommendations", String(total));
      setText("step98OddsCount", String(oddsCount));
      setText("step98EvCount", String(evCount));
      setText("step98HighEvCount", String(highEvCount));
      setText("step98ReasonCount", String(reasonCount));
      setText("step98ReasonPointsCount", String(pointsCount));
      setText("step98ExpectedValueAlerts", String(expectedValueAlerts));
      setText("step98RaceCount", String(races.length));
      setText("step98UpdatedAt", data.updated_at ? "updated: " + data.updated_at : "-");

      const gradeEl = document.getElementById("step98QualityGrade");
      if (gradeEl) {
        gradeEl.classList.remove("excellent", "good", "warn", "bad");
        gradeEl.classList.add(grade.cls);
      }

      const preview = document.getElementById("step98QualityPreview");
      if (preview) {
        const top = recommendations
          .slice()
          .sort(function (a, b) { return b.expected_value - a.expected_value; })
          .slice(0, 5)
          .map(function (item) {
            return "<code>" +
              (item.race_no || "?") + "R " +
              item.bet_type + " " +
              item.combination +
              " EV=" + item.expected_value.toFixed(2) +
              " Grade=" + item.value_grade +
              "</code>";
          });

        preview.innerHTML = [
          "reasoning version: <code>" + (reasoning.version || "-") + "</code>",
          "高EV上位: " + (top.length ? top.join(" / ") : "なし")
        ].join("<br>");
      }

      if (score >= 90) {
        setStatus("OK: 品質スコアは良好です", "ok");
      } else if (score >= 75) {
        setStatus("OK: 品質スコアは許容範囲です", "ok");
      } else if (score >= 60) {
        setStatus("WARN: 一部の品質項目が不足しています", "warn");
      } else {
        setStatus("ERROR: 品質スコアが低いです", "error");
      }
    } catch (error) {
      console.error("STEP98 quality score error:", error);
      setStatus("ERROR: " + error.message, "error");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStep98QualityScore);
  } else {
    loadStep98QualityScore();
  }

  window.step98LoadQualityScore = loadStep98QualityScore;
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
        "step98QualityScorePanel",
        "step98QualityStatus",
        "step98QualityScore",
        "step98QualityGrade",
        "step98LoadQualityScore",
        "recommendation_reason",
        "expected_value",
        "odds",
        "予想データ品質スコア",
    ]

    missing = [token for token in required_tokens if token not in final]
    if missing:
        raise SystemExit(f"Missing inserted tokens: {missing}")

    print("Added STEP 98 quality score cards")
    print("STEP 98 CHECK: OK")


if __name__ == "__main__":
    main()
