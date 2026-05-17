#!/usr/bin/env python3
from pathlib import Path

INDEX_PATH = Path("docs/index.html")

STYLE_MARKER = "STEP88_EV_SUMMARY_CARDS_STYLE"
HTML_MARKER = "STEP88_EV_SUMMARY_CARDS_HTML"
SCRIPT_MARKER = "STEP88_EV_SUMMARY_CARDS_SCRIPT"


STYLE_BLOCK = """
<style>
/* STEP88_EV_SUMMARY_CARDS_STYLE */
.step88-ev-summary-panel {
  margin: 16px auto;
  padding: 16px;
  max-width: 1100px;
  border-radius: 14px;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  color: #f8fafc;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.step88-ev-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.step88-ev-summary-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.step88-ev-summary-status {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
}

.step88-ev-summary-status.ok {
  background: rgba(34, 197, 94, 0.18);
  color: #bbf7d0;
}

.step88-ev-summary-status.warn {
  background: rgba(245, 158, 11, 0.18);
  color: #fde68a;
}

.step88-ev-summary-status.error {
  background: rgba(239, 68, 68, 0.18);
  color: #fecaca;
}

.step88-ev-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.step88-ev-summary-card {
  border-radius: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.16);
}

.step88-ev-summary-label {
  font-size: 0.78rem;
  color: #cbd5e1;
  margin-bottom: 6px;
}

.step88-ev-summary-value {
  font-size: 1.35rem;
  font-weight: 800;
  color: #ffffff;
}

.step88-ev-summary-sub {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #94a3b8;
}

.step88-ev-summary-highlight {
  color: #facc15;
}

.step88-ev-summary-preview {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #e2e8f0;
  line-height: 1.6;
}

.step88-ev-summary-preview code {
  color: #fde68a;
}

@media (max-width: 860px) {
  .step88-ev-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .step88-ev-summary-panel {
    margin: 12px 8px;
    padding: 12px;
  }

  .step88-ev-summary-grid {
    grid-template-columns: 1fr;
  }

  .step88-ev-summary-value {
    font-size: 1.2rem;
  }
}
</style>
"""


HTML_BLOCK = """
<!-- STEP88_EV_SUMMARY_CARDS_HTML -->
<section id="step88EvSummaryPanel" class="step88-ev-summary-panel">
  <div class="step88-ev-summary-header">
    <div class="step88-ev-summary-title">EVサマリー</div>
    <div id="step88EvSummaryStatus" class="step88-ev-summary-status">読み込み中...</div>
  </div>

  <div class="step88-ev-summary-grid">
    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">おすすめ買い目数</div>
      <div id="step88TotalRecommendations" class="step88-ev-summary-value">-</div>
      <div class="step88-ev-summary-sub">prediction.json recommendations</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">高EV買い目</div>
      <div id="step88HighEvCount" class="step88-ev-summary-value step88-ev-summary-highlight">-</div>
      <div class="step88-ev-summary-sub">expected_value >= 1.2</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">最大EV</div>
      <div id="step88MaxEv" class="step88-ev-summary-value">-</div>
      <div id="step88MaxEvTicket" class="step88-ev-summary-sub">-</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">最大オッズ</div>
      <div id="step88MaxOdds" class="step88-ev-summary-value">-</div>
      <div id="step88MaxOddsTicket" class="step88-ev-summary-sub">-</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">オッズ反映済み</div>
      <div id="step88OddsCount" class="step88-ev-summary-value">-</div>
      <div class="step88-ev-summary-sub">odds > 0</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">EV反映済み</div>
      <div id="step88EvCount" class="step88-ev-summary-value">-</div>
      <div class="step88-ev-summary-sub">expected_value > 0</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">期待値アラート</div>
      <div id="step88ExpectedValueAlerts" class="step88-ev-summary-value">-</div>
      <div class="step88-ev-summary-sub">alerts</div>
    </div>

    <div class="step88-ev-summary-card">
      <div class="step88-ev-summary-label">対象レース数</div>
      <div id="step88RaceCount" class="step88-ev-summary-value">-</div>
      <div id="step88UpdatedAt" class="step88-ev-summary-sub">-</div>
    </div>
  </div>

  <div id="step88EvSummaryPreview" class="step88-ev-summary-preview"></div>
</section>
"""


SCRIPT_BLOCK = """
<script>
// STEP88_EV_SUMMARY_CARDS_SCRIPT
(function () {
  const STEP88_EV_THRESHOLD = 1.2;

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
    const el = document.getElementById("step88EvSummaryStatus");
    if (!el) return;
    el.textContent = message;
    el.classList.remove("ok", "warn", "error");
    if (type) {
      el.classList.add(type);
    }
  }

  function formatNumber(value, digits) {
    const n = toNumber(value);
    return n.toFixed(digits);
  }

  function ticketLabel(item) {
    if (!item) return "-";
    const raceNo = item.race_no ? item.race_no + "R" : "?R";
    const betType = item.bet_type || "-";
    const combination = item.combination || "-";
    return raceNo + " " + betType + " " + combination;
  }

  function isExpectedValueAlert(alert) {
    const text = JSON.stringify(alert || {});
    return text.includes("期待値") || text.includes("expected_value") || text.includes("EV");
  }

  async function loadStep88EvSummary() {
    const panel = document.getElementById("step88EvSummaryPanel");
    if (!panel) return;

    try {
      setStatus("読み込み中...", "");

      const url = "./prediction.json?v=88-" + Date.now();
      const response = await fetch(url, { cache: "no-store" });

      if (!response.ok) {
        throw new Error("prediction.json fetch failed: HTTP " + response.status);
      }

      const data = await response.json();
      const races = Array.isArray(data.races) ? data.races : [];
      const alerts = Array.isArray(data.alerts) ? data.alerts : [];

      const recommendations = [];

      races.forEach(function (race) {
        const recs = Array.isArray(race.recommendations) ? race.recommendations : [];
        recs.forEach(function (rec) {
          const odds = toNumber(rec.odds);
          const ev = toNumber(rec.expected_value);
          recommendations.push({
            race_no: race.race_no || race.race_number || "",
            venue_name: race.venue_name || race.venue || "",
            bet_type: rec.bet_type || "",
            combination: rec.combination || "",
            odds: odds,
            expected_value: ev,
            amount: toNumber(rec.amount),
            probability: toNumber(rec.probability)
          });
        });
      });

      const totalRecommendations = recommendations.length;
      const oddsItems = recommendations.filter(function (item) { return item.odds > 0; });
      const evItems = recommendations.filter(function (item) { return item.expected_value > 0; });
      const highEvItems = recommendations.filter(function (item) { return item.expected_value >= STEP88_EV_THRESHOLD; });
      const expectedValueAlerts = alerts.filter(isExpectedValueAlert);

      let maxEvItem = null;
      let maxOddsItem = null;

      recommendations.forEach(function (item) {
        if (!maxEvItem || item.expected_value > maxEvItem.expected_value) {
          maxEvItem = item;
        }
        if (!maxOddsItem || item.odds > maxOddsItem.odds) {
          maxOddsItem = item;
        }
      });

      setText("step88TotalRecommendations", String(totalRecommendations));
      setText("step88HighEvCount", String(highEvItems.length));
      setText("step88MaxEv", maxEvItem ? formatNumber(maxEvItem.expected_value, 2) : "-");
      setText("step88MaxOdds", maxOddsItem ? formatNumber(maxOddsItem.odds, 2) : "-");
      setText("step88OddsCount", String(oddsItems.length));
      setText("step88EvCount", String(evItems.length));
      setText("step88ExpectedValueAlerts", String(expectedValueAlerts.length));
      setText("step88RaceCount", String(races.length));
      setText("step88UpdatedAt", data.updated_at ? "updated: " + data.updated_at : "-");
      setText("step88MaxEvTicket", ticketLabel(maxEvItem));
      setText("step88MaxOddsTicket", ticketLabel(maxOddsItem));

      const preview = document.getElementById("step88EvSummaryPreview");
      if (preview) {
        const top = highEvItems
          .slice()
          .sort(function (a, b) { return b.expected_value - a.expected_value; })
          .slice(0, 5)
          .map(function (item) {
            return "<code>" + ticketLabel(item) + " EV=" + formatNumber(item.expected_value, 2) + " odds=" + formatNumber(item.odds, 2) + "</code>";
          });

        preview.innerHTML = top.length
          ? "高EV上位: " + top.join(" / ")
          : "高EV買い目はありません。";
      }

      if (totalRecommendations === 0) {
        setStatus("WARN: recommendations がありません", "warn");
      } else if (highEvItems.length === 0) {
        setStatus("WARN: 高EV買い目がありません", "warn");
      } else {
        setStatus("OK: EVサマリーを表示しました", "ok");
      }
    } catch (error) {
      console.error("STEP88 EV summary error:", error);
      setStatus("ERROR: " + error.message, "error");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStep88EvSummary);
  } else {
    loadStep88EvSummary();
  }

  window.step88LoadEvSummary = loadStep88EvSummary;
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

    required = [
        STYLE_MARKER,
        HTML_MARKER,
        SCRIPT_MARKER,
        "step88EvSummaryPanel",
        "step88HighEvCount",
        "step88MaxEv",
        "step88ExpectedValueAlerts",
        "STEP 87",
    ]

    # STEP 87 は index.html に必須ではないので、ここでは除外して実チェック
    required = [
        STYLE_MARKER,
        HTML_MARKER,
        SCRIPT_MARKER,
        "step88EvSummaryPanel",
        "step88HighEvCount",
        "step88MaxEv",
        "step88ExpectedValueAlerts",
        "expected_value",
        "odds",
        "EVサマリー",
    ]

    missing = [token for token in required if token not in final]
    if missing:
        raise SystemExit(f"Missing inserted tokens: {missing}")

    print("Added STEP 88 EV summary cards")
    print("STEP 88 CHECK: OK")


if __name__ == "__main__":
    main()
