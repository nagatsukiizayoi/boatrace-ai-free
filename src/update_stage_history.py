import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


STAGE_EVALUATION_PATH = Path("docs/stage_evaluation.json")
STAGE_HISTORY_PATH = Path("docs/stage_evaluation_history.json")
STAGE_HISTORY_HTML_PATH = Path("docs/stage_history.html")


STAGE_ORDER = [
    "PRE_NIGHT",
    "MORNING",
    "PRE_EXHIBITION",
    "POST_EXHIBITION",
    "FINAL"
]


STAGE_LABELS = {
    "PRE_NIGHT": "前日夜予想",
    "MORNING": "当日朝予想",
    "PRE_EXHIBITION": "展示前予想",
    "POST_EXHIBITION": "展示後予想",
    "FINAL": "最終予想"
}


def now_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo"))


def load_json(path: Path, default=None):
    if default is None:
        default = {}

    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def yen(value):
    return f"{int(value):,}円"


def profit_class(value):
    value = int(value)

    if value > 0:
        return "plus"
    elif value < 0:
        return "minus"
    else:
        return "zero"


def profit_text(value):
    value = int(value)

    if value > 0:
        return f"+{yen(value)}"
    elif value < 0:
        return f"-{yen(abs(value))}"
    else:
        return yen(0)


def get_race_id(stage_evaluation):
    race = stage_evaluation.get("race", {})

    date = race.get("date", "不明")
    place = race.get("place") or race.get("stadium") or "不明"
    race_no = race.get("race_no", "不明")

    return f"{date}_{place}_{race_no}"


def evaluation_to_record(stage_evaluation):
    race = stage_evaluation.get("race", {})
    result = stage_evaluation.get("result", {})

    stages = []

    for stage in stage_evaluation.get("stages", []):
        stages.append({
            "stage": stage.get("stage", ""),
            "label": stage.get("label", ""),
            "exists": stage.get("exists", False),
            "updated_at": stage.get("updated_at", ""),
            "summary": stage.get("summary", {}),
            "top_boats": stage.get("top_boats", []),
            "tickets": stage.get("tickets", [])
        })

    record = {
        "race_id": get_race_id(stage_evaluation),
        "date": race.get("date", "不明"),
        "place": race.get("place") or race.get("stadium") or "不明",
        "race_no": race.get("race_no", "不明"),
        "evaluated_at": stage_evaluation.get("evaluated_at", ""),
        "result": {
            "trifecta": result.get("trifecta", ""),
            "payout": result.get("payout", 0)
        },
        "best_stage": stage_evaluation.get("best_stage"),
        "stages": stages
    }

    return record


def upsert_record(history, new_record):
    records = history.get("records", [])
    race_id = new_record.get("race_id")

    new_records = []
    replaced = False

    for record in records:
        if record.get("race_id") == race_id:
            new_records.append(new_record)
            replaced = True
        else:
            new_records.append(record)

    if not replaced:
        new_records.append(new_record)

    new_records.sort(
        key=lambda r: (
            str(r.get("date", "")),
            str(r.get("place", "")),
            str(r.get("race_no", ""))
        )
    )

    history["records"] = new_records
    return history


def empty_stage_summary(stage):
    return {
        "stage": stage,
        "label": STAGE_LABELS.get(stage, stage),
        "race_count": 0,
        "hit_race_count": 0,
        "ticket_count": 0,
        "hit_count": 0,
        "total_stake": 0,
        "total_return": 0,
        "profit": 0,
        "roi": 0,
        "hit_race_rate": 0,
        "ticket_hit_rate": 0
    }


def calculate_stage_summary(records):
    """
    ステージごとの通算成績を計算する。
    """

    summaries = {}

    for stage in STAGE_ORDER:
        summaries[stage] = empty_stage_summary(stage)

    for record in records:
        for stage_record in record.get("stages", []):
            if not stage_record.get("exists"):
                continue

            stage = stage_record.get("stage", "")
            summary = stage_record.get("summary", {})

            if stage not in summaries:
                summaries[stage] = empty_stage_summary(stage)

            s = summaries[stage]

            ticket_count = int(summary.get("ticket_count", 0))
            hit_count = int(summary.get("hit_count", 0))
            stake = int(summary.get("total_stake", 0))
            ret = int(summary.get("total_return", 0))

            s["race_count"] += 1
            s["ticket_count"] += ticket_count
            s["hit_count"] += hit_count
            s["total_stake"] += stake
            s["total_return"] += ret

            if hit_count > 0:
                s["hit_race_count"] += 1

    for s in summaries.values():
        s["profit"] = s["total_return"] - s["total_stake"]

        if s["total_stake"] > 0:
            s["roi"] = round((s["total_return"] / s["total_stake"]) * 100, 2)
        else:
            s["roi"] = 0

        if s["race_count"] > 0:
            s["hit_race_rate"] = round((s["hit_race_count"] / s["race_count"]) * 100, 2)
        else:
            s["hit_race_rate"] = 0

        if s["ticket_count"] > 0:
            s["ticket_hit_rate"] = round((s["hit_count"] / s["ticket_count"]) * 100, 2)
        else:
            s["ticket_hit_rate"] = 0

    return [summaries[stage] for stage in STAGE_ORDER if stage in summaries]


def get_stage_summary_from_record(record, stage_name):
    for stage in record.get("stages", []):
        if stage.get("stage") == stage_name and stage.get("exists"):
            return stage.get("summary", {})

    return None


def calculate_transition_summary(records):
    """
    前日夜予想から、展示後・最終予想で改善したかを見る。
    """

    transitions = [
        {
            "from_stage": "PRE_NIGHT",
            "to_stage": "POST_EXHIBITION",
            "label": "前日夜 → 展示後"
        },
        {
            "from_stage": "PRE_NIGHT",
            "to_stage": "FINAL",
            "label": "前日夜 → 最終"
        },
        {
            "from_stage": "POST_EXHIBITION",
            "to_stage": "FINAL",
            "label": "展示後 → 最終"
        }
    ]

    results = []

    for transition in transitions:
        compared_count = 0
        improved_count = 0
        worsened_count = 0
        same_count = 0

        total_profit_diff = 0
        total_roi_diff = 0

        for record in records:
            before = get_stage_summary_from_record(record, transition["from_stage"])
            after = get_stage_summary_from_record(record, transition["to_stage"])

            if before is None or after is None:
                continue

            compared_count += 1

            before_profit = int(before.get("profit", 0))
            after_profit = int(after.get("profit", 0))
            profit_diff = after_profit - before_profit

            before_roi = float(before.get("roi", 0))
            after_roi = float(after.get("roi", 0))
            roi_diff = after_roi - before_roi

            total_profit_diff += profit_diff
            total_roi_diff += roi_diff

            if profit_diff > 0:
                improved_count += 1
            elif profit_diff < 0:
                worsened_count += 1
            else:
                same_count += 1

        if compared_count > 0:
            improved_rate = round((improved_count / compared_count) * 100, 2)
            average_profit_diff = round(total_profit_diff / compared_count, 2)
            average_roi_diff = round(total_roi_diff / compared_count, 2)
        else:
            improved_rate = 0
            average_profit_diff = 0
            average_roi_diff = 0

        results.append({
            "from_stage": transition["from_stage"],
            "to_stage": transition["to_stage"],
            "label": transition["label"],
            "compared_count": compared_count,
            "improved_count": improved_count,
            "worsened_count": worsened_count,
            "same_count": same_count,
            "improved_rate": improved_rate,
            "total_profit_diff": total_profit_diff,
            "average_profit_diff": average_profit_diff,
            "average_roi_diff": average_roi_diff
        })

    return results


def calculate_overall_summary(records, stage_summary, transition_summary):
    race_count = len(records)

    best_stage = None

    existing_stages = [s for s in stage_summary if s.get("race_count", 0) > 0]

    if existing_stages:
        existing_stages.sort(
            key=lambda s: (
                int(s.get("profit", 0)),
                float(s.get("roi", 0))
            ),
            reverse=True
        )

        best_stage = existing_stages[0]

    return {
        "race_count": race_count,
        "best_stage": best_stage,
        "stage_summary_count": len(existing_stages),
        "transition_summary_count": len(transition_summary)
    }


def build_history():
    now = now_jst()

    stage_evaluation = load_json(STAGE_EVALUATION_PATH)

    if not stage_evaluation:
        raise FileNotFoundError("docs/stage_evaluation.json が見つかりません。先に Evaluate Result を実行してください。")

    history = load_json(STAGE_HISTORY_PATH, default={
        "updated_at": "",
        "overall_summary": {},
        "stage_summary": [],
        "transition_summary": [],
        "records": []
    })

    new_record = evaluation_to_record(stage_evaluation)
    history = upsert_record(history, new_record)

    records = history.get("records", [])

    stage_summary = calculate_stage_summary(records)
    transition_summary = calculate_transition_summary(records)
    overall_summary = calculate_overall_summary(records, stage_summary, transition_summary)

    history["updated_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    history["overall_summary"] = overall_summary
    history["stage_summary"] = stage_summary
    history["transition_summary"] = transition_summary

    return history


def make_stage_summary_rows(stage_summary):
    rows = ""

    for s in stage_summary:
        profit = int(s.get("profit", 0))

        rows += f"""
        <tr>
          <td>{s.get("label", "")}</td>
          <td>{s.get("race_count", 0)}R</td>
          <td>{s.get("hit_race_count", 0)}R</td>
          <td>{s.get("hit_race_rate", 0)}%</td>
          <td>{s.get("ticket_count", 0)}点</td>
          <td>{s.get("hit_count", 0)}点</td>
          <td>{s.get("ticket_hit_rate", 0)}%</td>
          <td>{yen(s.get("total_stake", 0))}</td>
          <td>{yen(s.get("total_return", 0))}</td>
          <td class="{profit_class(profit)}">{profit_text(profit)}</td>
          <td>{s.get("roi", 0)}%</td>
        </tr>
        """

    return rows


def make_transition_rows(transition_summary):
    rows = ""

    for t in transition_summary:
        diff = int(round(float(t.get("total_profit_diff", 0))))

        rows += f"""
        <tr>
          <td>{t.get("label", "")}</td>
          <td>{t.get("compared_count", 0)}R</td>
          <td class="plus">{t.get("improved_count", 0)}R</td>
          <td class="minus">{t.get("worsened_count", 0)}R</td>
          <td>{t.get("same_count", 0)}R</td>
          <td>{t.get("improved_rate", 0)}%</td>
          <td class="{profit_class(diff)}">{profit_text(diff)}</td>
          <td>{t.get("average_profit_diff", 0)}円</td>
          <td>{t.get("average_roi_diff", 0)}%</td>
        </tr>
        """

    return rows


def get_stage_profit(record, stage_name):
    summary = get_stage_summary_from_record(record, stage_name)

    if summary is None:
        return None

    return int(summary.get("profit", 0))


def get_stage_roi(record, stage_name):
    summary = get_stage_summary_from_record(record, stage_name)

    if summary is None:
        return None

    return float(summary.get("roi", 0))


def make_record_rows(records):
    rows = ""

    for record in reversed(records):
        pre_profit = get_stage_profit(record, "PRE_NIGHT")
        post_profit = get_stage_profit(record, "POST_EXHIBITION")
        final_profit = get_stage_profit(record, "FINAL")

        def cell_profit(value):
            if value is None:
                return "<td>-</td>"
            return f'<td class="{profit_class(value)}">{profit_text(value)}</td>'

        best_stage = record.get("best_stage") or {}
        best_label = best_stage.get("label", "-")

        rows += f"""
        <tr>
          <td>{record.get("date", "")}</td>
          <td>{record.get("place", "")}</td>
          <td>{record.get("race_no", "")}</td>
          <td>{record.get("result", {}).get("trifecta", "")}</td>
          {cell_profit(pre_profit)}
          {cell_profit(post_profit)}
          {cell_profit(final_profit)}
          <td>{best_label}</td>
        </tr>
        """

    return rows


def make_html(history):
    overall = history.get("overall_summary", {})
    stage_summary = history.get("stage_summary", [])
    transition_summary = history.get("transition_summary", [])
    records = history.get("records", [])

    best_stage = overall.get("best_stage")

    if best_stage:
        best_stage_html = f"""
        <div class="best-box">
          通算で最も成績が良いステージ：
          <strong>{best_stage.get("label", "")}</strong><br>
          利益：<strong class="{profit_class(best_stage.get("profit", 0))}">{profit_text(best_stage.get("profit", 0))}</strong>
          / 回収率：<strong>{best_stage.get("roi", 0)}%</strong>
          / 評価レース数：<strong>{best_stage.get("race_count", 0)}R</strong>
        </div>
        """
    else:
        best_stage_html = """
        <div class="best-box">
          まだ通算成績を計算できるステージがありません。
        </div>
        """

    stage_rows = make_stage_summary_rows(stage_summary)
    transition_rows = make_transition_rows(transition_summary)
    record_rows = make_record_rows(records)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>ステージ別 過去成績</title>

  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #be123c, #fb7185);
      color: white;
      padding: 20px 16px;
      text-align: center;
    }}

    header h1 {{
      margin: 0;
      font-size: 24px;
    }}

    header p {{
      margin: 8px 0 0;
      font-size: 14px;
      opacity: 0.9;
    }}

    main {{
      max-width: 1150px;
      margin: 0 auto;
      padding: 16px;
    }}

    .card {{
      background: white;
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      overflow-x: auto;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .info-box {{
      background: #f9fafb;
      border-radius: 12px;
      padding: 12px;
    }}

    .info-label {{
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 4px;
    }}

    .info-value {{
      font-size: 20px;
      font-weight: 900;
    }}

    .best-box {{
      background: #fff1f2;
      border: 1px solid #fb7185;
      color: #881337;
      border-radius: 14px;
      padding: 14px;
      line-height: 1.8;
      font-size: 15px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      min-width: 950px;
    }}

    th, td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px 6px;
      text-align: center;
      white-space: nowrap;
    }}

    th {{
      background: #f9fafb;
      color: #374151;
    }}

    .plus {{
      color: #dc2626;
      font-weight: 900;
    }}

    .minus {{
      color: #2563eb;
      font-weight: 900;
    }}

    .zero {{
      color: #111827;
      font-weight: 900;
    }}

    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .link-button {{
      display: inline-block;
      padding: 10px 14px;
      border-radius: 999px;
      background: #be123c;
      color: white;
      text-decoration: none;
      font-weight: bold;
      font-size: 14px;
    }}

    .notice {{
      color: #6b7280;
      font-size: 13px;
      line-height: 1.7;
    }}

    @media (max-width: 700px) {{
      .summary-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>

<body>
  <header>
    <h1>ステージ別 過去成績</h1>
    <p>前日夜・展示後・最終予想の通算成績を確認します</p>
  </header>

  <main>
    <section class="card">
      <h2>全体サマリー</h2>

      <div class="summary-grid">
        <div class="info-box">
          <div class="info-label">評価レース数</div>
          <div class="info-value">{overall.get("race_count", 0)}R</div>
        </div>

        <div class="info-box">
          <div class="info-label">最終更新</div>
          <div class="info-value">{history.get("updated_at", "")}</div>
        </div>
      </div>

      <br>

      {best_stage_html}
    </section>

    <section class="card">
      <h2>ステージ別 通算成績</h2>
      <p class="notice">スマホの場合は表を左右にスクロールできます。</p>

      <table>
        <thead>
          <tr>
            <th>ステージ</th>
            <th>評価R数</th>
            <th>的中R数</th>
            <th>的中R率</th>
            <th>買い目数</th>
            <th>的中点数</th>
            <th>点数的中率</th>
            <th>投資額</th>
            <th>払戻額</th>
            <th>利益</th>
            <th>回収率</th>
          </tr>
        </thead>
        <tbody>
          {stage_rows}
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>ステージ間 改善比較</h2>
      <p class="notice">
        例：「前日夜 → 展示後」で利益が増えたレース数を改善として数えます。
      </p>

      <table>
        <thead>
          <tr>
            <th>比較</th>
            <th>比較R数</th>
            <th>改善</th>
            <th>悪化</th>
            <th>変化なし</th>
            <th>改善率</th>
            <th>合計利益差</th>
            <th>平均利益差</th>
            <th>平均ROI差</th>
          </tr>
        </thead>
        <tbody>
          {transition_rows}
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>レース別 ステージ成績</h2>
      <p class="notice">各レースで、前日夜・展示後・最終の利益を比較します。</p>

      <table>
        <thead>
          <tr>
            <th>日付</th>
            <th>場</th>
            <th>R</th>
            <th>結果</th>
            <th>前日夜利益</th>
            <th>展示後利益</th>
            <th>最終利益</th>
            <th>最良ステージ</th>
          </tr>
        </thead>
        <tbody>
          {record_rows}
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>ページ移動</h2>

      <div class="links">
        <a class="link-button" href="./index.html">予想ページへ</a>
        <a class="link-button" href="./stage_evaluation.html">直近ステージ評価へ</a>
        <a class="link-button" href="./compare.html">予想比較へ</a>
        <a class="link-button" href="./history.html">過去成績へ</a>
        <a class="link-button" href="./charts.html">成績グラフへ</a>
        <a class="link-button" href="./stage_evaluation_history.json">履歴JSON</a>
      </div>
    </section>

    <section class="card notice">
      このページは学習用・分析練習用です。実際の購入や利益を保証するものではありません。
      ステージ別の通算成績を見ることで、前日予想・展示後予想・最終予想のどこが有効かを検証できます。
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    history = build_history()

    save_json(STAGE_HISTORY_PATH, history)

    html = make_html(history)

    STAGE_HISTORY_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)

    with STAGE_HISTORY_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("ステージ別過去成績を更新しました。")
    print(f"JSON: {STAGE_HISTORY_PATH}")
    print(f"HTML: {STAGE_HISTORY_HTML_PATH}")


if __name__ == "__main__":
    main()
