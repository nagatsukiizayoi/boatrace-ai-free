import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HISTORY_PATH = Path("docs/stage_evaluation_history.json")
OUTPUT_JSON_PATH = Path("docs/stage_insights.json")
OUTPUT_HTML_PATH = Path("docs/stage_insights.html")

STAGE_LABELS = {
    "PRE_NIGHT": "前日夜予想",
    "MORNING": "当日朝予想",
    "PRE_EXHIBITION": "展示前予想",
    "POST_EXHIBITION": "展示後予想",
    "FINAL": "最終予想",
}

STAGE_ORDER = [
    "PRE_NIGHT",
    "MORNING",
    "PRE_EXHIBITION",
    "POST_EXHIBITION",
    "FINAL",
]


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} が見つかりません。先に STEP 22〜24 を実行してください。")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def yen(value):
    try:
        return f"{int(round(float(value))):,}円"
    except Exception:
        return "0円"


def pct(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "0.00%"


def num(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def extract_records(history):
    """
    stage_evaluation_history.json の構造差異に対応するため、
    records / races / history のいずれかからレース別データを取り出す。
    """
    if isinstance(history, list):
        return history

    for key in ["records", "races", "history", "items"]:
        if isinstance(history.get(key), list):
            return history[key]

    return []


def extract_stage_results(record):
    """
    1レース内のステージ別評価を取り出す。
    想定キー:
    - stage_results
    - stages
    - evaluations
    """
    for key in ["stage_results", "stages", "evaluations"]:
        value = record.get(key)
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            result = {}
            for item in value:
                stage = item.get("stage") or item.get("stage_key")
                if stage:
                    result[stage] = item
            return result

    return {}


def normalize_stage_result(stage, data):
    total_stake = num(data.get("total_stake", data.get("stake", data.get("investment", 0))))
    total_return = num(data.get("total_return", data.get("return", data.get("payout_total", 0))))
    profit = data.get("profit")

    if profit is None:
        profit = total_return - total_stake
    else:
        profit = num(profit)

    roi = data.get("roi")
    if roi is None:
        roi = (total_return / total_stake * 100) if total_stake > 0 else 0
    else:
        roi = num(roi)

    hit_count = num(data.get("hit_count", data.get("hits", 0)))
    ticket_count = num(data.get("ticket_count", data.get("tickets_count", 0)))
    is_hit = bool(data.get("is_hit", False)) or hit_count > 0

    return {
        "stage": stage,
        "label": STAGE_LABELS.get(stage, stage),
        "total_stake": total_stake,
        "total_return": total_return,
        "profit": profit,
        "roi": roi,
        "hit_count": hit_count,
        "ticket_count": ticket_count,
        "is_hit": is_hit,
    }


def aggregate_by_stage(records):
    summary = {}

    for stage in STAGE_ORDER:
        summary[stage] = {
            "stage": stage,
            "label": STAGE_LABELS.get(stage, stage),
            "race_count": 0,
            "hit_race_count": 0,
            "total_stake": 0,
            "total_return": 0,
            "total_profit": 0,
            "roi": 0,
            "hit_rate": 0,
        }

    for record in records:
        stage_results = extract_stage_results(record)

        for stage, raw in stage_results.items():
            if stage not in summary:
                summary[stage] = {
                    "stage": stage,
                    "label": STAGE_LABELS.get(stage, stage),
                    "race_count": 0,
                    "hit_race_count": 0,
                    "total_stake": 0,
                    "total_return": 0,
                    "total_profit": 0,
                    "roi": 0,
                    "hit_rate": 0,
                }

            normalized = normalize_stage_result(stage, raw)
            item = summary[stage]

            item["race_count"] += 1
            item["hit_race_count"] += 1 if normalized["is_hit"] else 0
            item["total_stake"] += normalized["total_stake"]
            item["total_return"] += normalized["total_return"]
            item["total_profit"] += normalized["profit"]

    for item in summary.values():
        if item["total_stake"] > 0:
            item["roi"] = item["total_return"] / item["total_stake"] * 100
        else:
            item["roi"] = 0

        if item["race_count"] > 0:
            item["hit_rate"] = item["hit_race_count"] / item["race_count"] * 100
        else:
            item["hit_rate"] = 0

    return summary


def pick_best(summary, metric):
    candidates = [
        item for item in summary.values()
        if item.get("race_count", 0) > 0
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda x: num(x.get(metric, 0)))


def compare_stages(summary, before, after):
    b = summary.get(before)
    a = summary.get(after)

    if not b or not a:
        return None

    if b["race_count"] == 0 or a["race_count"] == 0:
        return None

    roi_diff = a["roi"] - b["roi"]
    profit_diff = a["total_profit"] - b["total_profit"]
    hit_rate_diff = a["hit_rate"] - b["hit_rate"]

    return {
        "before": before,
        "before_label": b["label"],
        "after": after,
        "after_label": a["label"],
        "roi_diff": roi_diff,
        "profit_diff": profit_diff,
        "hit_rate_diff": hit_rate_diff,
        "improved_roi": roi_diff > 0,
        "improved_profit": profit_diff > 0,
        "improved_hit_rate": hit_rate_diff > 0,
    }


def make_comment(summary, best_roi, best_profit, best_hit_rate, comparisons):
    comments = []

    if not best_roi:
        comments.append("まだ分析できるステージ別データがありません。まずは数レース分の評価を蓄積してください。")
        return comments

    comments.append(
        f"現時点で回収率が最も高いのは「{best_roi['label']}」で、回収率は {pct(best_roi['roi'])} です。"
    )

    if best_profit:
        comments.append(
            f"利益が最も大きいのは「{best_profit['label']}」で、累計利益は {yen(best_profit['total_profit'])} です。"
        )

    if best_hit_rate:
        comments.append(
            f"的中率が最も高いのは「{best_hit_rate['label']}」で、的中率は {pct(best_hit_rate['hit_rate'])} です。"
        )

    for comp in comparisons:
        if not comp:
            continue

        if comp["improved_roi"]:
            comments.append(
                f"「{comp['before_label']}」から「{comp['after_label']}」では、回収率が {pct(comp['roi_diff'])} 改善しています。"
            )
        else:
            comments.append(
                f"「{comp['before_label']}」から「{comp['after_label']}」では、回収率が {pct(comp['roi_diff'])} 低下しています。"
            )

    race_counts = [item["race_count"] for item in summary.values() if item["race_count"] > 0]
    max_race_count = max(race_counts) if race_counts else 0

    if max_race_count < 5:
        comments.append("まだレース数が少ないため、現時点の傾向は参考程度です。まずは5レース以上の蓄積を目指してください。")
    elif max_race_count < 30:
        comments.append("ある程度の傾向は見え始めていますが、まだブレがあります。30レース以上で判断精度が上がります。")
    else:
        comments.append("レース数が増えてきているため、ステージごとの傾向を比較しやすくなっています。")

    return comments


def make_html(insights):
    summary = insights["stage_summary"]
    comments = insights["comments"]
    comparisons = insights["comparisons"]

    stage_rows = ""

    for stage in STAGE_ORDER:
        item = summary.get(stage)

        if not item:
            continue

        if item["race_count"] == 0:
            continue

        profit_class = "plus" if item["total_profit"] > 0 else "minus" if item["total_profit"] < 0 else "zero"
        roi_class = "plus" if item["roi"] >= 100 else "minus"

        stage_rows += f"""
          <tr>
            <td>{item["label"]}</td>
            <td>{item["race_count"]}</td>
            <td>{item["hit_race_count"]}</td>
            <td>{pct(item["hit_rate"])}</td>
            <td>{yen(item["total_stake"])}</td>
            <td>{yen(item["total_return"])}</td>
            <td class="{profit_class}">{yen(item["total_profit"])}</td>
            <td class="{roi_class}">{pct(item["roi"])}</td>
          </tr>
        """

    comparison_cards = ""

    for comp in comparisons:
        if not comp:
            continue

        roi_class = "plus" if comp["roi_diff"] > 0 else "minus" if comp["roi_diff"] < 0 else "zero"
        profit_class = "plus" if comp["profit_diff"] > 0 else "minus" if comp["profit_diff"] < 0 else "zero"
        hit_class = "plus" if comp["hit_rate_diff"] > 0 else "minus" if comp["hit_rate_diff"] < 0 else "zero"

        comparison_cards += f"""
          <div class="compare-card">
            <h3>{comp["before_label"]} → {comp["after_label"]}</h3>
            <div class="metric-grid">
              <div class="metric">
                <div class="metric-label">回収率変化</div>
                <div class="metric-value {roi_class}">{pct(comp["roi_diff"])}</div>
              </div>
              <div class="metric">
                <div class="metric-label">利益変化</div>
                <div class="metric-value {profit_class}">{yen(comp["profit_diff"])}</div>
              </div>
              <div class="metric">
                <div class="metric-label">的中率変化</div>
                <div class="metric-value {hit_class}">{pct(comp["hit_rate_diff"])}</div>
              </div>
            </div>
          </div>
        """

    comment_items = "\n".join([f"<li>{comment}</li>" for comment in comments])

    generated_at = insights.get("generated_at", "")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>ステージ別自動分析</title>

  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #0891b2, #0f766e);
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
      opacity: 0.92;
    }}

    main {{
      max-width: 1100px;
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

    h2 {{
      margin-top: 0;
      font-size: 20px;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }}

    .summary-box {{
      border-radius: 14px;
      padding: 14px;
      color: white;
    }}

    .box-roi {{
      background: linear-gradient(135deg, #dc2626, #fb7185);
    }}

    .box-profit {{
      background: linear-gradient(135deg, #16a34a, #4ade80);
    }}

    .box-hit {{
      background: linear-gradient(135deg, #2563eb, #60a5fa);
    }}

    .summary-label {{
      font-size: 13px;
      opacity: 0.9;
    }}

    .summary-value {{
      font-size: 22px;
      font-weight: 900;
      margin-top: 6px;
    }}

    .summary-sub {{
      font-size: 13px;
      margin-top: 4px;
      opacity: 0.9;
    }}

    ul {{
      padding-left: 20px;
      line-height: 1.8;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 850px;
      font-size: 13px;
    }}

    th,
    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px 8px;
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
      color: #6b7280;
      font-weight: 900;
    }}

    .compare-card {{
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 14px;
      margin-bottom: 12px;
      background: #ffffff;
    }}

    .compare-card h3 {{
      margin: 0 0 12px;
      font-size: 17px;
    }}

    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }}

    .metric {{
      background: #f9fafb;
      border-radius: 12px;
      padding: 12px;
      text-align: center;
    }}

    .metric-label {{
      font-size: 12px;
      color: #6b7280;
    }}

    .metric-value {{
      font-size: 18px;
      margin-top: 4px;
    }}

    .menu {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .menu a {{
      display: block;
      text-decoration: none;
      color: white;
      border-radius: 14px;
      padding: 14px;
      font-weight: 800;
      text-align: center;
    }}

    .menu-home {{
      background: linear-gradient(135deg, #0f766e, #14b8a6);
    }}

    .menu-stage {{
      background: linear-gradient(135deg, #9333ea, #d946ef);
    }}

    .menu-chart {{
      background: linear-gradient(135deg, #0891b2, #22d3ee);
    }}

    .menu-json {{
      background: linear-gradient(135deg, #475569, #94a3b8);
    }}

    footer {{
      text-align: center;
      color: #6b7280;
      font-size: 12px;
      padding: 24px 16px;
    }}

    @media (max-width: 700px) {{
      .summary-grid,
      .metric-grid,
      .menu {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>

<body>
  <header>
    <h1>ステージ別自動分析</h1>
    <p>前日夜・展示後・最終予想のどこで改善しているかを確認します</p>
  </header>

  <main>
    <section class="card">
      <h2>おすすめステージ</h2>

      <div class="summary-grid">
        <div class="summary-box box-roi">
          <div class="summary-label">回収率トップ</div>
          <div class="summary-value">{insights["best_roi"]["label"] if insights["best_roi"] else "-"}</div>
          <div class="summary-sub">{pct(insights["best_roi"]["roi"]) if insights["best_roi"] else "-"}</div>
        </div>

        <div class="summary-box box-profit">
          <div class="summary-label">利益トップ</div>
          <div class="summary-value">{insights["best_profit"]["label"] if insights["best_profit"] else "-"}</div>
          <div class="summary-sub">{yen(insights["best_profit"]["total_profit"]) if insights["best_profit"] else "-"}</div>
        </div>

        <div class="summary-box box-hit">
          <div class="summary-label">的中率トップ</div>
          <div class="summary-value">{insights["best_hit_rate"]["label"] if insights["best_hit_rate"] else "-"}</div>
          <div class="summary-sub">{pct(insights["best_hit_rate"]["hit_rate"]) if insights["best_hit_rate"] else "-"}</div>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>自動コメント</h2>
      <ul>
        {comment_items}
      </ul>
    </section>

    <section class="card">
      <h2>ステージ間の改善</h2>
      {comparison_cards if comparison_cards else "<p>比較できるステージデータがまだありません。</p>"}
    </section>

    <section class="card">
      <h2>ステージ別通算成績</h2>
      <table>
        <thead>
          <tr>
            <th>ステージ</th>
            <th>レース数</th>
            <th>的中レース数</th>
            <th>的中率</th>
            <th>総投資</th>
            <th>総払戻</th>
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
      <h2>ページ移動</h2>
      <div class="menu">
        <a class="menu-home" href="./index.html">トップページ</a>
        <a class="menu-stage" href="./stage_history.html">ステージ別過去成績</a>
        <a class="menu-chart" href="./stage_charts.html">ステージ別グラフ</a>
        <a class="menu-json" href="./stage_insights.json">分析JSON</a>
      </div>
    </section>

    <section class="card">
      <h2>更新情報</h2>
      <p>生成日時：{generated_at}</p>
    </section>
  </main>

  <footer>
    boatrace-ai-free / stage insights
  </footer>
</body>
</html>
"""

    return html


def main():
    history = load_json(HISTORY_PATH)
    records = extract_records(history)
    summary = aggregate_by_stage(records)

    best_roi = pick_best(summary, "roi")
    best_profit = pick_best(summary, "total_profit")
    best_hit_rate = pick_best(summary, "hit_rate")

    comparisons = [
        compare_stages(summary, "PRE_NIGHT", "POST_EXHIBITION"),
        compare_stages(summary, "POST_EXHIBITION", "FINAL"),
        compare_stages(summary, "PRE_NIGHT", "FINAL"),
    ]

    comments = make_comment(
        summary=summary,
        best_roi=best_roi,
        best_profit=best_profit,
        best_hit_rate=best_hit_rate,
        comparisons=comparisons,
    )

    insights = {
        "generated_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "best_roi": best_roi,
        "best_profit": best_profit,
        "best_hit_rate": best_hit_rate,
        "comparisons": comparisons,
        "comments": comments,
        "stage_summary": summary,
        "record_count": len(records),
    }

    save_json(OUTPUT_JSON_PATH, insights)

    html = make_html(insights)
    OUTPUT_HTML_PATH.write_text(html, encoding="utf-8")

    print(f"created: {OUTPUT_JSON_PATH}")
    print(f"created: {OUTPUT_HTML_PATH}")


if __name__ == "__main__":
    main()

