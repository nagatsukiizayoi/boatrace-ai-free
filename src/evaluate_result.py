import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


PREDICTION_PATH = Path("docs/prediction.json")
RESULT_PATH = Path("docs/result.json")
EVALUATION_JSON_PATH = Path("docs/evaluation.json")
EVALUATION_HTML_PATH = Path("docs/evaluation.html")


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} が見つかりません。")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_ticket(ticket: str) -> str:
    """
    1 - 2 - 3
    1-2-3
    １－２－３
    のような表記ゆれを 1-2-3 にそろえる。
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


def collect_tickets(prediction_data):
    """
    prediction.json から買い目を取り出す。

    STEP9以降の ticket_groups がある場合：
      ticket_groups から ticket と amount を読む。

    古い形式の tickets だけがある場合：
      1点100円として読む。
    """

    tickets = []

    # 新しい形式：ticket_groups
    ticket_groups = prediction_data.get("ticket_groups", [])

    if ticket_groups:
        for group in ticket_groups:
            group_name = group.get("name", "未分類")
            risk = group.get("risk", "不明")

            for item in group.get("tickets", []):
                ticket = normalize_ticket(item.get("ticket"))
                amount = int(item.get("amount", 100))
                reason = item.get("reason", "")

                tickets.append({
                    "ticket": ticket,
                    "amount": amount,
                    "group": group_name,
                    "risk": risk,
                    "reason": reason
                })

    # 古い形式：tickets
    elif prediction_data.get("tickets"):
        for ticket in prediction_data.get("tickets", []):
            tickets.append({
                "ticket": normalize_ticket(ticket),
                "amount": 100,
                "group": "通常",
                "risk": "不明",
                "reason": "旧形式の買い目"
            })

    return tickets


def evaluate():
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    prediction_data = load_json(PREDICTION_PATH)
    result_data = load_json(RESULT_PATH)

    result = result_data.get("result", {})
    actual_trifecta = normalize_ticket(result.get("trifecta"))
    payout_per_100yen = int(result.get("payout", 0))

    tickets = collect_tickets(prediction_data)

    if not tickets:
        raise ValueError("prediction.json から買い目を読み取れませんでした。")

    evaluated_tickets = []
    total_stake = 0
    total_return = 0
    hit_count = 0

    for item in tickets:
        ticket = item["ticket"]
        amount = int(item["amount"])
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
            "hit": is_hit,
            "return": returned,
            "profit": returned - amount
        })

    profit = total_return - total_stake

    if total_stake > 0:
        roi = round((total_return / total_stake) * 100, 2)
    else:
        roi = 0

    hit_rate = round((hit_count / len(tickets)) * 100, 2)

    evaluation = {
        "evaluated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "race": {
            "prediction_race": prediction_data.get("race", {}),
            "result_race": result_data.get("race", {})
        },
        "result": {
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
        "notice": "これは学習用の仮想評価です。実際の購入や利益を保証するものではありません。"
    }

    return evaluation


def yen(value):
    return f"{value:,}円"


def make_html(evaluation):
    summary = evaluation["summary"]
    result = evaluation["result"]

    if summary["profit"] > 0:
        profit_class = "plus"
        profit_text = f"+{yen(summary['profit'])}"
    elif summary["profit"] < 0:
        profit_class = "minus"
        profit_text = f"-{yen(abs(summary['profit']))}"
    else:
        profit_class = "zero"
        profit_text = yen(0)

    rows = ""

    for item in evaluation["tickets"]:
        hit_label = "的中" if item["hit"] else "不的中"
        hit_class = "hit" if item["hit"] else "miss"

        rows += f"""
        <tr>
          <td>{item["group"]}</td>
          <td class="ticket">{item["ticket"]}</td>
          <td>{yen(item["amount"])}</td>
          <td class="{hit_class}">{hit_label}</td>
          <td>{yen(item["return"])}</td>
          <td>{yen(item["profit"])}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>予想評価結果</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #2563eb, #1e40af);
      color: white;
      padding: 20px;
      text-align: center;
    }}

    header h1 {{
      margin: 0;
      font-size: 24px;
    }}

    main {{
      max-width: 900px;
      margin: 0 auto;
      padding: 16px;
    }}

    .card {{
      background: white;
      border-radius: 16px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    .summary-box {{
      background: #f9fafb;
      border-radius: 12px;
      padding: 12px;
      text-align: center;
    }}

    .label {{
      font-size: 13px;
      color: #6b7280;
    }}

    .value {{
      font-size: 22px;
      font-weight: 700;
      margin-top: 4px;
    }}

    .plus {{
      color: #dc2626;
    }}

    .minus {{
      color: #2563eb;
    }}

    .zero {{
      color: #111827;
    }}

    .hit {{
      color: #dc2626;
      font-weight: bold;
    }}

    .miss {{
      color: #6b7280;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}

    th, td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px 6px;
      text-align: center;
    }}

    th {{
      background: #f9fafb;
      color: #374151;
    }}

    .ticket {{
      font-weight: bold;
      font-size: 16px;
    }}

    .notice {{
      font-size: 13px;
      color: #6b7280;
      line-height: 1.6;
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
      background: #2563eb;
      color: white;
      text-decoration: none;
      font-weight: bold;
      font-size: 14px;
    }}

    @media (max-width: 600px) {{
      .summary-grid {{
        grid-template-columns: 1fr;
      }}

      table {{
        font-size: 12px;
      }}

      th, td {{
        padding: 8px 4px;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>予想評価結果</h1>
    <p>的中・回収率・利益を自動計算</p>
  </header>

  <main>
    <section class="card">
      <h2>レース結果</h2>
      <p>3連単結果：<strong>{result["trifecta"]}</strong></p>
      <p>払戻金：<strong>{yen(result["payout_per_100yen"])}</strong> / 100円</p>
      <p>評価日時：{evaluation["evaluated_at"]}</p>
    </section>

    <section class="card">
      <h2>集計結果</h2>
      <div class="summary-grid">
        <div class="summary-box">
          <div class="label">買い目数</div>
          <div class="value">{summary["ticket_count"]}点</div>
        </div>
        <div class="summary-box">
          <div class="label">的中数</div>
          <div class="value">{summary["hit_count"]}点</div>
        </div>
        <div class="summary-box">
          <div class="label">投資額</div>
          <div class="value">{yen(summary["total_stake"])}</div>
        </div>
        <div class="summary-box">
          <div class="label">払戻額</div>
          <div class="value">{yen(summary["total_return"])}</div>
        </div>
        <div class="summary-box">
          <div class="label">利益</div>
          <div class="value {profit_class}">{profit_text}</div>
        </div>
        <div class="summary-box">
          <div class="label">回収率</div>
          <div class="value">{summary["roi"]}%</div>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>買い目ごとの結果</h2>
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
    </section>

    <section class="card">
      <h2>ページ移動</h2>
      <div class="links">
        <a class="link-button" href="./index.html">予想ページへ戻る</a>
        <a class="link-button" href="./evaluation.json">評価JSONを見る</a>
      </div>
    </section>

    <section class="card notice">
      {evaluation["notice"]}
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    evaluation = evaluate()

    EVALUATION_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    with EVALUATION_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=2)

    html = make_html(evaluation)

    with EVALUATION_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("評価が完了しました。")
    print(f"JSON: {EVALUATION_JSON_PATH}")
    print(f"HTML: {EVALUATION_HTML_PATH}")


if __name__ == "__main__":
    main()

