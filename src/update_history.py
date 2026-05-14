import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


EVALUATION_PATH = Path("docs/evaluation.json")
HISTORY_PATH = Path("docs/evaluation_history.json")
HISTORY_HTML_PATH = Path("docs/history.html")


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


def get_race_value(evaluation, key, default=""):
    """
    evaluation.json の race 情報から値を取り出す。
    result_race を優先し、なければ prediction_race を見る。
    """

    race_block = evaluation.get("race", {})
    result_race = race_block.get("result_race", {})
    prediction_race = race_block.get("prediction_race", {})

    return (
        result_race.get(key)
        or prediction_race.get(key)
        or prediction_race.get("stadium") if key == "place" else ""
        or default
    )


def get_place(evaluation):
    race_block = evaluation.get("race", {})
    result_race = race_block.get("result_race", {})
    prediction_race = race_block.get("prediction_race", {})

    return (
        result_race.get("place")
        or result_race.get("stadium")
        or prediction_race.get("place")
        or prediction_race.get("stadium")
        or "不明"
    )


def get_date(evaluation):
    race_block = evaluation.get("race", {})
    result_race = race_block.get("result_race", {})
    prediction_race = race_block.get("prediction_race", {})

    return (
        result_race.get("date")
        or prediction_race.get("date")
        or "不明"
    )


def get_race_no(evaluation):
    race_block = evaluation.get("race", {})
    result_race = race_block.get("result_race", {})
    prediction_race = race_block.get("prediction_race", {})

    return (
        result_race.get("race_no")
        or prediction_race.get("race_no")
        or "不明"
    )


def make_race_id(evaluation):
    date = get_date(evaluation)
    place = get_place(evaluation)
    race_no = get_race_no(evaluation)

    return f"{date}_{place}_{race_no}"


def evaluation_to_record(evaluation):
    summary = evaluation.get("summary", {})
    result = evaluation.get("result", {})

    date = get_date(evaluation)
    place = get_place(evaluation)
    race_no = get_race_no(evaluation)

    record = {
        "race_id": make_race_id(evaluation),
        "date": date,
        "place": place,
        "race_no": race_no,
        "evaluated_at": evaluation.get("evaluated_at", ""),
        "trifecta": result.get("trifecta", ""),
        "payout_per_100yen": result.get("payout_per_100yen", 0),
        "ticket_count": summary.get("ticket_count", 0),
        "hit_count": summary.get("hit_count", 0),
        "hit_rate": summary.get("hit_rate", 0),
        "total_stake": summary.get("total_stake", 0),
        "total_return": summary.get("total_return", 0),
        "profit": summary.get("profit", 0),
        "roi": summary.get("roi", 0),
        "tickets": evaluation.get("tickets", [])
    }

    return record


def upsert_record(history, new_record):
    """
    同じ race_id のデータがあれば上書きする。
    なければ追加する。
    """

    records = history.get("records", [])
    race_id = new_record["race_id"]

    replaced = False
    new_records = []

    for record in records:
        if record.get("race_id") == race_id:
            new_records.append(new_record)
            replaced = True
        else:
            new_records.append(record)

    if not replaced:
        new_records.append(new_record)

    new_records.sort(key=lambda x: (x.get("date", ""), x.get("place", ""), x.get("race_no", "")))

    history["records"] = new_records
    return history


def calculate_summary(records):
    race_count = len(records)

    total_stake = sum(int(r.get("total_stake", 0)) for r in records)
    total_return = sum(int(r.get("total_return", 0)) for r in records)
    total_profit = total_return - total_stake

    hit_race_count = sum(1 for r in records if int(r.get("hit_count", 0)) > 0)

    if total_stake > 0:
        roi = round((total_return / total_stake) * 100, 2)
    else:
        roi = 0

    if race_count > 0:
        hit_race_rate = round((hit_race_count / race_count) * 100, 2)
    else:
        hit_race_rate = 0

    return {
        "race_count": race_count,
        "hit_race_count": hit_race_count,
        "hit_race_rate": hit_race_rate,
        "total_stake": total_stake,
        "total_return": total_return,
        "total_profit": total_profit,
        "roi": roi
    }


def calculate_group_summary(records):
    """
    本線・押さえ・穴狙いなど、分類ごとの成績を計算する。
    """

    groups = {}

    for record in records:
        for ticket in record.get("tickets", []):
            group = ticket.get("group", "未分類")
            amount = int(ticket.get("amount", 0))
            ret = int(ticket.get("return", 0))

            if group not in groups:
                groups[group] = {
                    "group": group,
                    "ticket_count": 0,
                    "hit_count": 0,
                    "stake": 0,
                    "return": 0,
                    "profit": 0,
                    "roi": 0
                }

            groups[group]["ticket_count"] += 1
            groups[group]["stake"] += amount
            groups[group]["return"] += ret

            if ticket.get("hit"):
                groups[group]["hit_count"] += 1

    for group in groups.values():
        group["profit"] = group["return"] - group["stake"]

        if group["stake"] > 0:
            group["roi"] = round((group["return"] / group["stake"]) * 100, 2)
        else:
            group["roi"] = 0

    return list(groups.values())


def profit_class(value):
    if value > 0:
        return "plus"
    elif value < 0:
        return "minus"
    else:
        return "zero"


def make_history_html(history):
    records = history.get("records", [])
    summary = history.get("summary", {})
    group_summary = history.get("group_summary", [])

    record_rows = ""

    for r in reversed(records):
        p_class = profit_class(int(r.get("profit", 0)))

        if int(r.get("profit", 0)) > 0:
            profit_text = f"+{yen(r.get('profit', 0))}"
        elif int(r.get("profit", 0)) < 0:
            profit_text = f"-{yen(abs(int(r.get('profit', 0))))}"
        else:
            profit_text = yen(0)

        hit_text = "的中" if int(r.get("hit_count", 0)) > 0 else "不的中"
        hit_class = "hit" if int(r.get("hit_count", 0)) > 0 else "miss"

        record_rows += f"""
        <tr>
          <td>{r.get("date", "")}</td>
          <td>{r.get("place", "")}</td>
          <td>{r.get("race_no", "")}</td>
          <td>{r.get("trifecta", "")}</td>
          <td class="{hit_class}">{hit_text}</td>
          <td>{yen(r.get("total_stake", 0))}</td>
          <td>{yen(r.get("total_return", 0))}</td>
          <td class="{p_class}">{profit_text}</td>
          <td>{r.get("roi", 0)}%</td>
        </tr>
        """

    group_rows = ""

    for g in group_summary:
        p_class = profit_class(int(g.get("profit", 0)))

        if int(g.get("profit", 0)) > 0:
            profit_text = f"+{yen(g.get('profit', 0))}"
        elif int(g.get("profit", 0)) < 0:
            profit_text = f"-{yen(abs(int(g.get('profit', 0))))}"
        else:
            profit_text = yen(0)

        group_rows += f"""
        <tr>
          <td>{g.get("group", "")}</td>
          <td>{g.get("ticket_count", 0)}点</td>
          <td>{g.get("hit_count", 0)}点</td>
          <td>{yen(g.get("stake", 0))}</td>
          <td>{yen(g.get("return", 0))}</td>
          <td class="{p_class}">{profit_text}</td>
          <td>{g.get("roi", 0)}%</td>
        </tr>
        """

    total_profit = int(summary.get("total_profit", 0))
    total_profit_class = profit_class(total_profit)

    if total_profit > 0:
        total_profit_text = f"+{yen(total_profit)}"
    elif total_profit < 0:
        total_profit_text = f"-{yen(abs(total_profit))}"
    else:
        total_profit_text = yen(0)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>過去成績</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #16a34a, #166534);
      color: white;
      padding: 20px;
      text-align: center;
    }}

    header h1 {{
      margin: 0;
      font-size: 24px;
    }}

    main {{
      max-width: 1000px;
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
      font-weight: bold;
    }}

    .minus {{
      color: #2563eb;
      font-weight: bold;
    }}

    .zero {{
      color: #111827;
      font-weight: bold;
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
      min-width: 760px;
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

    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .link-button {{
      display: inline-block;
      padding: 10px 14px;
      border-radius: 999px;
      background: #16a34a;
      color: white;
      text-decoration: none;
      font-weight: bold;
      font-size: 14px;
    }}

    .notice {{
      font-size: 13px;
      color: #6b7280;
      line-height: 1.6;
    }}

    @media (max-width: 600px) {{
      .summary-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>過去成績</h1>
    <p>予想の成績を毎回ためて確認するページ</p>
  </header>

  <main>
    <section class="card">
      <h2>全体成績</h2>
      <div class="summary-grid">
        <div class="summary-box">
          <div class="label">評価レース数</div>
          <div class="value">{summary.get("race_count", 0)}R</div>
        </div>
        <div class="summary-box">
          <div class="label">的中レース数</div>
          <div class="value">{summary.get("hit_race_count", 0)}R</div>
        </div>
        <div class="summary-box">
          <div class="label">的中レース率</div>
          <div class="value">{summary.get("hit_race_rate", 0)}%</div>
        </div>
        <div class="summary-box">
          <div class="label">総投資額</div>
          <div class="value">{yen(summary.get("total_stake", 0))}</div>
        </div>
        <div class="summary-box">
          <div class="label">総払戻額</div>
          <div class="value">{yen(summary.get("total_return", 0))}</div>
        </div>
        <div class="summary-box">
          <div class="label">総利益</div>
          <div class="value {total_profit_class}">{total_profit_text}</div>
        </div>
        <div class="summary-box">
          <div class="label">全体回収率</div>
          <div class="value">{summary.get("roi", 0)}%</div>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>分類別成績</h2>
      <table>
        <thead>
          <tr>
            <th>分類</th>
            <th>買い目数</th>
            <th>的中数</th>
            <th>投資額</th>
            <th>払戻額</th>
            <th>利益</th>
            <th>回収率</th>
          </tr>
        </thead>
        <tbody>
          {group_rows}
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>レースごとの履歴</h2>
      <table>
        <thead>
          <tr>
            <th>日付</th>
            <th>場</th>
            <th>R</th>
            <th>結果</th>
            <th>的中</th>
            <th>投資</th>
            <th>払戻</th>
            <th>利益</th>
            <th>回収率</th>
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
        <a class="link-button" href="./evaluation.html">直近評価へ</a>
        <a class="link-button" href="./evaluation_history.json">履歴JSONを見る</a>
      </div>
    </section>

    <section class="card notice">
      このページは学習用・分析練習用です。実際の購入や利益を保証するものではありません。
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    evaluation = load_json(EVALUATION_PATH)

    if not evaluation:
        raise FileNotFoundError("docs/evaluation.json が見つかりません。先に STEP 11 の評価を実行してください。")

    history = load_json(HISTORY_PATH, default={
        "updated_at": "",
        "summary": {},
        "group_summary": [],
        "records": []
    })

    new_record = evaluation_to_record(evaluation)
    history = upsert_record(history, new_record)

    records = history.get("records", [])
    history["updated_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    history["summary"] = calculate_summary(records)
    history["group_summary"] = calculate_group_summary(records)

    save_json(HISTORY_PATH, history)

    html = make_history_html(history)

    with HISTORY_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("過去成績を更新しました。")
    print(f"JSON: {HISTORY_PATH}")
    print(f"HTML: {HISTORY_HTML_PATH}")


if __name__ == "__main__":
    main()

