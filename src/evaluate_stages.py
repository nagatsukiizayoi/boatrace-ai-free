import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


RESULT_PATH = Path("docs/result.json")

STAGE_FILES = [
    {
        "stage": "PRE_NIGHT",
        "label": "前日夜予想",
        "path": Path("docs/prediction_pre_night.json")
    },
    {
        "stage": "MORNING",
        "label": "当日朝予想",
        "path": Path("docs/prediction_morning.json")
    },
    {
        "stage": "PRE_EXHIBITION",
        "label": "展示前予想",
        "path": Path("docs/prediction_pre_exhibition.json")
    },
    {
        "stage": "POST_EXHIBITION",
        "label": "展示後予想",
        "path": Path("docs/prediction_post_exhibition.json")
    },
    {
        "stage": "FINAL",
        "label": "最終予想",
        "path": Path("docs/prediction_final.json")
    }
]

OUTPUT_JSON_PATH = Path("docs/stage_evaluation.json")
OUTPUT_HTML_PATH = Path("docs/stage_evaluation.html")


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


def normalize_ticket(ticket):
    """
    表記ゆれを 1-2-3 にそろえる。
    """

    if ticket is None:
        return ""

    text = str(ticket)
    text = text.replace(" ", "")
    text = text.replace("　", "")
    text = text.replace("－", "-")
    text = text.replace("ー", "-")
    text = text.replace("―", "-")
    return text


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


def collect_tickets(prediction_data):
    """
    prediction json から買い目を取り出す。

    対応形式：
    1. ticket_groups がある形式
    2. tickets だけがある古い形式
    """

    tickets = []

    ticket_groups = prediction_data.get("ticket_groups", [])

    if ticket_groups:
        for group in ticket_groups:
            group_name = group.get("name", "未分類")
            risk = group.get("risk", "不明")

            for item in group.get("tickets", []):
                ticket = normalize_ticket(item.get("ticket"))
                amount = int(item.get("amount", 100))
                reason = item.get("reason", "")
                probability = item.get("probability", None)

                if not ticket:
                    continue

                tickets.append({
                    "ticket": ticket,
                    "amount": amount,
                    "group": group_name,
                    "risk": risk,
                    "reason": reason,
                    "probability": probability
                })

    elif prediction_data.get("tickets"):
        for ticket in prediction_data.get("tickets", []):
            tickets.append({
                "ticket": normalize_ticket(ticket),
                "amount": 100,
                "group": "通常",
                "risk": "不明",
                "reason": "旧形式の買い目",
                "probability": None
            })

    return tickets


def get_top_boats(prediction_data):
    """
    上位3艇を取り出す。
    """

    result = []

    for item in prediction_data.get("predictions", []):
        result.append({
            "rank": item.get("rank"),
            "mark": item.get("mark"),
            "boat": item.get("boat"),
            "driver": item.get("driver"),
            "score": item.get("score")
        })

    return result


def evaluate_one_stage(stage_info, result_data):
    path = stage_info["path"]

    if not path.exists():
        return {
            "stage": stage_info["stage"],
            "label": stage_info["label"],
            "file": str(path),
            "exists": False,
            "message": "予想ファイルがありません。",
            "summary": {
                "ticket_count": 0,
                "hit_count": 0,
                "hit_rate": 0,
                "total_stake": 0,
                "total_return": 0,
                "profit": 0,
                "roi": 0
            },
            "tickets": [],
            "top_boats": []
        }

    prediction_data = load_json(path)

    result = result_data.get("result", {})
    actual_trifecta = normalize_ticket(result.get("trifecta"))
    payout_per_100yen = int(result.get("payout", 0))

    tickets = collect_tickets(prediction_data)

    total_stake = 0
    total_return = 0
    hit_count = 0
    evaluated_tickets = []

    for item in tickets:
        ticket = item["ticket"]
        amount = int(item.get("amount", 100))

        total_stake += amount

        is_hit = ticket == actual_trifecta

        if is_hit:
            hit_count += 1
            returned = int(payout_per_100yen * (amount / 100))
        else:
            returned = 0

        total_return += returned

        evaluated_tickets.append({
            "ticket": ticket,
            "amount": amount,
            "group": item.get("group", ""),
            "risk": item.get("risk", ""),
            "reason": item.get("reason", ""),
            "probability": item.get("probability"),
            "hit": is_hit,
            "return": returned,
            "profit": returned - amount
        })

    profit = total_return - total_stake

    if total_stake > 0:
        roi = round((total_return / total_stake) * 100, 2)
    else:
        roi = 0

    if tickets:
        hit_rate = round((hit_count / len(tickets)) * 100, 2)
    else:
        hit_rate = 0

    return {
        "stage": stage_info["stage"],
        "label": stage_info["label"],
        "file": str(path),
        "exists": True,
        "prediction_run_id": prediction_data.get("prediction_run_id", ""),
        "updated_at": prediction_data.get("updated_at", ""),
        "race": prediction_data.get("race", {}),
        "actual_result": {
            "trifecta": actual_trifecta,
            "payout_per_100yen": payout_per_100yen
        },
        "summary": {
            "ticket_count": len(tickets),
            "hit_count": hit_count,
            "hit_rate": hit_rate,
            "total_stake": total_stake,
            "total_return": total_return,
            "profit": profit,
            "roi": roi
        },
        "tickets": evaluated_tickets,
        "top_boats": get_top_boats(prediction_data)
    }


def find_best_stage(stage_results):
    """
    回収率と利益を見て、一番成績が良かったステージを選ぶ。
    """

    existing = [r for r in stage_results if r.get("exists")]

    if not existing:
        return None

    existing.sort(
        key=lambda r: (
            int(r["summary"].get("profit", 0)),
            float(r["summary"].get("roi", 0))
        ),
        reverse=True
    )

    return existing[0]


def make_stage_evaluation():
    now = now_jst()

    result_data = load_json(RESULT_PATH)

    if not result_data:
        raise FileNotFoundError("docs/result.json が見つかりません。先に結果を入力してください。")

    stage_results = []

    for stage_info in STAGE_FILES:
        stage_results.append(evaluate_one_stage(stage_info, result_data))

    best_stage = find_best_stage(stage_results)

    evaluation = {
        "evaluated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "result": result_data.get("result", {}),
        "race": result_data.get("race", {}),
        "best_stage": {
            "stage": best_stage.get("stage"),
            "label": best_stage.get("label"),
            "profit": best_stage.get("summary", {}).get("profit"),
            "roi": best_stage.get("summary", {}).get("roi")
        } if best_stage else None,
        "stages": stage_results,
        "notice": "これは学習用のステージ別評価です。実際の購入や利益を保証するものではありません。"
    }

    return evaluation


def make_top_boats_html(top_boats):
    if not top_boats:
        return "<span class='small'>上位艇データなし</span>"

    parts = []

    for item in top_boats:
        parts.append(
            f"{item.get('mark', '')}{item.get('boat', '')}号艇 "
            f"{item.get('driver', '')} "
            f"({item.get('score', '-')})"
        )

    return "<br>".join(parts)


def make_ticket_detail_html(tickets):
    if not tickets:
        return "<p class='small'>買い目がありません。</p>"

    rows = ""

    for t in tickets:
        hit_class = "hit" if t.get("hit") else "miss"
        hit_text = "的中" if t.get("hit") else "不的中"

        rows += f"""
        <tr>
          <td>{t.get("group", "")}</td>
          <td class="ticket">{t.get("ticket", "")}</td>
          <td>{yen(t.get("amount", 0))}</td>
          <td class="{hit_class}">{hit_text}</td>
          <td>{yen(t.get("return", 0))}</td>
          <td class="{profit_class(t.get("profit", 0))}">{profit_text(t.get("profit", 0))}</td>
        </tr>
        """

    return f"""
    <table>
      <thead>
        <tr>
          <th>分類</th>
          <th>買い目</th>
          <th>金額</th>
          <th>結果</th>
          <th>払戻</th>
          <th>損益</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """


def make_html(evaluation):
    result = evaluation.get("result", {})
    stages = evaluation.get("stages", [])
    best_stage = evaluation.get("best_stage")

    summary_rows = ""

    for stage in stages:
        summary = stage.get("summary", {})
        exists = stage.get("exists", False)

        if not exists:
            summary_rows += f"""
            <tr>
              <td>{stage.get("label", "")}</td>
              <td colspan="8" class="missing">予想ファイルなし</td>
            </tr>
            """
            continue

        profit = int(summary.get("profit", 0))
        p_class = profit_class(profit)

        hit_text = "的中" if int(summary.get("hit_count", 0)) > 0 else "不的中"
        hit_class = "hit" if int(summary.get("hit_count", 0)) > 0 else "miss"

        summary_rows += f"""
        <tr>
          <td>{stage.get("label", "")}</td>
          <td>{stage.get("updated_at", "")}</td>
          <td class="{hit_class}">{hit_text}</td>
          <td>{summary.get("ticket_count", 0)}点</td>
          <td>{summary.get("hit_count", 0)}点</td>
          <td>{yen(summary.get("total_stake", 0))}</td>
          <td>{yen(summary.get("total_return", 0))}</td>
          <td class="{p_class}">{profit_text(profit)}</td>
          <td>{summary.get("roi", 0)}%</td>
        </tr>
        """

    detail_blocks = ""

    for stage in stages:
        if not stage.get("exists"):
            continue

        summary = stage.get("summary", {})
        profit = int(summary.get("profit", 0))

        detail_blocks += f"""
        <section class="card">
          <h2>{stage.get("label", "")}</h2>

          <div class="summary-grid">
            <div class="info-box">
              <div class="info-label">的中数</div>
              <div class="info-value">{summary.get("hit_count", 0)}点</div>
            </div>

            <div class="info-box">
              <div class="info-label">投資額</div>
              <div class="info-value">{yen(summary.get("total_stake", 0))}</div>
            </div>

            <div class="info-box">
              <div class="info-label">払戻額</div>
              <div class="info-value">{yen(summary.get("total_return", 0))}</div>
            </div>

            <div class="info-box">
              <div class="info-label">利益</div>
              <div class="info-value {profit_class(profit)}">{profit_text(profit)}</div>
            </div>

            <div class="info-box">
              <div class="info-label">回収率</div>
              <div class="info-value">{summary.get("roi", 0)}%</div>
            </div>

            <div class="info-box">
              <div class="info-label">上位艇</div>
              <div class="info-value small">{make_top_boats_html(stage.get("top_boats", []))}</div>
            </div>
          </div>

          <h3>買い目ごとの結果</h3>
          {make_ticket_detail_html(stage.get("tickets", []))}
        </section>
        """

    if best_stage:
        best_html = f"""
        <div class="best-box">
          今回もっとも成績が良かったステージ：
          <strong>{best_stage.get("label")}</strong>
          / 利益 <strong>{profit_text(best_stage.get("profit", 0))}</strong>
          / 回収率 <strong>{best_stage.get("roi", 0)}%</strong>
        </div>
        """
    else:
        best_html = """
        <div class="best-box">
          比較できるステージ予想がありません。
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>ステージ別評価</title>

  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #be123c, #881337);
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
      margin-bottom: 14px;
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
      font-size: 17px;
      font-weight: 800;
      line-height: 1.5;
    }}

    .small {{
      font-size: 13px;
      line-height: 1.7;
    }}

    .best-box {{
      background: #fff7ed;
      border: 1px solid #fdba74;
      color: #9a3412;
      border-radius: 14px;
      padding: 14px;
      font-size: 15px;
      line-height: 1.7;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      min-width: 850px;
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

    .ticket {{
      font-weight: 900;
      font-size: 15px;
    }}

    .hit {{
      color: #dc2626;
      font-weight: 900;
    }}

    .miss {{
      color: #6b7280;
      font-weight: 800;
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

    .missing {{
      color: #991b1b;
      background: #fee2e2;
      font-weight: 800;
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
    <h1>ステージ別評価</h1>
    <p>前日夜予想・展示後予想・最終予想を同じ結果で比較します</p>
  </header>

  <main>
    <section class="card">
      <h2>レース結果</h2>

      <div class="summary-grid">
        <div class="info-box">
          <div class="info-label">3連単結果</div>
          <div class="info-value">{result.get("trifecta", "")}</div>
        </div>

        <div class="info-box">
          <div class="info-label">払戻金 / 100円</div>
          <div class="info-value">{yen(result.get("payout", 0))}</div>
        </div>

        <div class="info-box">
          <div class="info-label">評価日時</div>
          <div class="info-value">{evaluation.get("evaluated_at", "")}</div>
        </div>
      </div>

      {best_html}
    </section>

    <section class="card">
      <h2>ステージ別 成績一覧</h2>
      <p class="notice">スマホの場合は表を左右にスクロールできます。</p>

      <table>
        <thead>
          <tr>
            <th>ステージ</th>
            <th>予想更新日時</th>
            <th>的中</th>
            <th>買い目数</th>
            <th>的中数</th>
            <th>投資額</th>
            <th>払戻額</th>
            <th>利益</th>
            <th>回収率</th>
          </tr>
        </thead>
        <tbody>
          {summary_rows}
        </tbody>
      </table>
    </section>

    {detail_blocks}

    <section class="card">
      <h2>ページ移動</h2>

      <div class="links">
        <a class="link-button" href="./index.html">予想ページへ</a>
        <a class="link-button" href="./compare.html">予想比較へ</a>
        <a class="link-button" href="./evaluation.html">直近評価へ</a>
        <a class="link-button" href="./history.html">過去成績へ</a>
        <a class="link-button" href="./charts.html">成績グラフへ</a>
        <a class="link-button" href="./stage_evaluation.json">ステージ評価JSON</a>
      </div>
    </section>

    <section class="card notice">
      {evaluation.get("notice", "")}
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    evaluation = make_stage_evaluation()

    save_json(OUTPUT_JSON_PATH, evaluation)

    html = make_html(evaluation)

    OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("ステージ別評価を作成しました。")
    print(f"JSON: {OUTPUT_JSON_PATH}")
    print(f"HTML: {OUTPUT_HTML_PATH}")


if __name__ == "__main__":
    main()

