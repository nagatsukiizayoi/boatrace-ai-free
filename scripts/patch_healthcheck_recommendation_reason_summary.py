#!/usr/bin/env python3
from pathlib import Path

HEALTHCHECK_PATH = Path("docs/healthcheck.html")

STYLE_MARKER = "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_STYLE"
HTML_MARKER = "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_HTML"
SCRIPT_MARKER = "STEP96_RECOMMENDATION_REASON_HEALTHCHECK_SCRIPT"


STYLE_BLOCK = """
<style>
/* STEP96_RECOMMENDATION_REASON_HEALTHCHECK_STYLE */
.step96-reason-health-panel {
  margin: 16px 0;
  padding: 16px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.step96-reason-health-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.step96-reason-health-title {
  font-weight: 800;
  font-size: 1.05rem;
  color: #0f172a;
}

.step96-reason-health-status {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.85rem;
  background: #f1f5f9;
  color: #475569;
}

.step96-reason-health-status.ok {
  background: #dcfce7;
  color: #166534;
}

.step96-reason-health-status.warn {
  background: #fef3c7;
  color: #92400e;
}

.step96-reason-health-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.step96-reason-health-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.step96-reason-health-card {
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.step96-reason-health-label {
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 5px;
}

.step96-reason-health-value {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}

.step96-reason-health-sub {
  margin-top: 4px;
  font-size: 0.76rem;
  color: #64748b;
}

.step96-reason-health-preview {
  margin-top: 12px;
  padding: 10px;
  border-radius: 12px;
  background: #f8fafc;
  color: #334155;
  font-size: 0.86rem;
  line-height: 1.6;
}

.step96-reason-health-preview code {
  color: #92400e;
  background: #fef3c7;
  padding: 2px 5px;
  border-radius: 6px;
}

@media (max-width: 860px) {
  .step96-reason-health-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .step96-reason-health-grid {
    grid-template-columns: 1fr;
  }

  .step96-reason-health-panel {
    padding: 12px;
  }
}
</style>
"""


HTML_BLOCK = """
<!-- STEP96_RECOMMENDATION_REASON_HEALTHCHECK_HTML -->
<section id="step96RecommendationReasonHealthPanel" class="step96-reason-health-panel">
  <div class="step96-reason-health-header">
    <div class="step96-reason-health-title">推奨理由 Health Check</div>
    <div id="step96RecommendationReasonHealthStatus" class="step96-reason-health-status">読み込み中...</div>
  </div>

  <div class="step96-reason-health-grid">
    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">recommendations</div>
      <div id="step96ReasonTotal" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">総買い目数</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">推奨理由つき</div>
      <div id="step96ReasonWithReason" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">recommendation_reason</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">理由ポイントつき</div>
      <div id="step96ReasonWithPoints" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">reason_points</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">高EV推奨理由</div>
      <div id="step96ReasonHighEv" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">EV >= 1.2</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">risk_note</div>
      <div id="step96ReasonRiskNote" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">注意文つき</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">Grade S/A/B/C</div>
      <div id="step96ReasonGrades" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">value_grade</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">reason version</div>
      <div id="step96ReasonVersion" class="step96-reason-health-value">-</div>
      <div class="step96-reason-health-sub">recommendation_reasoning.version</div>
    </div>

    <div class="step96-reason-health-card">
      <div class="step96-reason-health-label">対象レース数</div>
      <div id="step96ReasonRaceCount" class="step96-reason-health-value">-</div>
      <div id="step96ReasonUpdatedAt" class="step96-reason-health-sub">-</div>
    </div>
  </div>

  <div id="step96RecommendationReasonHealthPreview" class="step96-reason-health-preview">
    prediction.json を読み込み中です。
  </div>
</section>
"""


SCRIPT_BLOCK = """
<script>
// STEP96_RECOMMENDATION_REASON_HEALTHCHECK_SCRIPT
(function () {
  const STEP96_HIGH_EV_THRESHOLD = 1.2;

  function toNumber(value) {
    const n = Number(value || 0);
    return Number.isFinite(n) ? n : 0;
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  function setStatus(message, type) {
    const el = document.getElementById("step96RecommendationReasonHealthStatus");
    if (!el) return;

    el.textContent = message;
    el.classList.remove("ok", "warn", "error");

    if (type) {
      el.classList.add(type);
    }
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function hasText(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  async function loadStep96RecommendationReasonHealth() {
    const panel = document.getElementById("step96RecommendationReasonHealthPanel");
    if (!panel) return;

    try {
      setStatus("読み込み中...", "");

      const response = await fetch("./prediction.json?v=96-" + Date.now(), {
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error("prediction.json fetch failed: HTTP " + response.status);
      }

      const data = await response.json();
      const races = Array.isArray(data.races) ? data.races : [];
      const reasoning = data.recommendation_reasoning || {};

      let total = 0;
      let withReason = 0;
      let withPoints = 0;
      let withRiskNote = 0;
      let highEvReason = 0;
      const gradeCounts = {};
      const previewItems = [];

      races.forEach(function (race) {
        const recs = Array.isArray(race.recommendations) ? race.recommendations : [];

        recs.forEach(function (rec) {
          total += 1;

          const ev = toNumber(rec.expected_value);
          const grade = rec.value_grade || "UNKNOWN";

          gradeCounts[grade] = (gradeCounts[grade] || 0) + 1;

          if (hasText(rec.recommendation_reason)) {
            withReason += 1;
          }

          if (Array.isArray(rec.reason_points) && rec.reason_points.length >= 2) {
            withPoints += 1;
          }

          if (hasText(rec.risk_note)) {
            withRiskNote += 1;
          }

          if (ev >= STEP96_HIGH_EV_THRESHOLD && hasText(rec.recommendation_reason)) {
            highEvReason += 1;
            previewItems.push({
              race_no: race.race_no || race.race_number || "",
              bet_type: rec.bet_type || "",
              combination: rec.combination || "",
              expected_value: ev,
              value_grade: grade
            });
          }
        });
      });

      const gradeText = ["S", "A", "B", "C", "UNKNOWN"].map(function (g) {
        return g + ":" + (gradeCounts[g] || 0);
      }).join(" ");

      setText("step96ReasonTotal", String(total));
      setText("step96ReasonWithReason", String(withReason));
      setText("step96ReasonWithPoints", String(withPoints));
      setText("step96ReasonHighEv", String(highEvReason));
      setText("step96ReasonRiskNote", String(withRiskNote));
      setText("step96ReasonGrades", gradeText);
      setText("step96ReasonVersion", reasoning.version || "-");
      setText("step96ReasonRaceCount", String(races.length));
      setText("step96ReasonUpdatedAt", data.updated_at ? "updated: " + data.updated_at : "-");

      const preview = document.getElementById("step96RecommendationReasonHealthPreview");
      if (preview) {
        const top = previewItems
          .sort(function (a, b) { return b.expected_value - a.expected_value; })
          .slice(0, 6)
          .map(function (item) {
            return "<code>" +
              escapeHtml((item.race_no || "?") + "R " + item.bet_type + " " + item.combination + " Grade=" + item.value_grade + " EV=" + item.expected_value.toFixed(2)) +
              "</code>";
          });

        preview.innerHTML = top.length
          ? "高EV推奨理由プレビュー: " + top.join(" / ")
          : "高EV推奨理由はありません。";
      }

      if (total === 0) {
        setStatus("ERROR: recommendations がありません", "error");
      } else if (withReason !== total || withPoints !== total || withRiskNote !== total) {
        setStatus("WARN: 一部の推奨理由フィールドが不足しています", "warn");
      } else if (highEvReason === 0) {
        setStatus("WARN: 高EV推奨理由がありません", "warn");
      } else {
        setStatus("OK: 推奨理由サマリーを表示しました", "ok");
      }
    } catch (error) {
      console.error("STEP96 recommendation reason health error:", error);
      setStatus("ERROR: " + error.message, "error");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStep96RecommendationReasonHealth);
  } else {
    loadStep96RecommendationReasonHealth();
  }

  window.step96LoadRecommendationReasonHealth = loadStep96RecommendationReasonHealth;
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
    if not HEALTHCHECK_PATH.exists():
        raise SystemExit("docs/healthcheck.html does not exist")

    text = HEALTHCHECK_PATH.read_text(encoding="utf-8")
    original = text

    text = insert_before(text, STYLE_MARKER, STYLE_BLOCK, "</head>")
    text = insert_before(text, HTML_MARKER, HTML_BLOCK, "</body>")
    text = insert_before(text, SCRIPT_MARKER, SCRIPT_BLOCK, "</body>")

    if text != original:
        HEALTHCHECK_PATH.write_text(text, encoding="utf-8")
        print("Updated docs/healthcheck.html")
    else:
        print("No changes needed")

    final = HEALTHCHECK_PATH.read_text(encoding="utf-8")

    required_tokens = [
        STYLE_MARKER,
        HTML_MARKER,
        SCRIPT_MARKER,
        "step96RecommendationReasonHealthPanel",
        "step96RecommendationReasonHealthStatus",
        "step96LoadRecommendationReasonHealth",
        "recommendation_reasoning",
        "recommendation_reason",
        "reason_points",
        "value_grade",
        "risk_note",
        "推奨理由 Health Check",
    ]

    missing = [token for token in required_tokens if token not in final]
    if missing:
        raise SystemExit(f"Missing inserted tokens: {missing}")

    print("Added STEP 96 recommendation reason healthcheck summary")
    print("STEP 96 CHECK: OK")


if __name__ == "__main__":
    main()
