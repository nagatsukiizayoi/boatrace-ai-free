import json
from pathlib import Path


HISTORY_PATH = Path("docs/evaluation_history.json")
CHARTS_HTML_PATH = Path("docs/charts.html")


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} が見つかりません。先に Evaluate Result を実行してください。")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def sort_records(records):
    return sorted(
        records,
        key=lambda r: (
            str(r.get("date", "")),
            str(r.get("place", "")),
            str(r.get("race_no", ""))
        )
    )


def make_cumulative_data(records):
    """
    レースごとの累計利益・累計回収率を作る。
    """

    cumulative_profit = 0
    cumulative_stake = 0
    cumulative_return = 0

    points = []

    for index, record in enumerate(records, start=1):
        stake = int(record.get("total_stake", 0))
        ret = int(record.get("total_return", 0))
        profit = int(record.get("profit", ret - stake))

        cumulative_profit += profit
        cumulative_stake += stake
        cumulative_return += ret

        if cumulative_stake > 0:
            cumulative_roi = round((cumulative_return / cumulative_stake) * 100, 2)
        else:
            cumulative_roi = 0

        label = f'{record.get("date", "")} {record.get("place", "")} {record.get("race_no", "")}'

        points.append({
            "index": index,
            "label": label,
            "profit": profit,
            "cumulative_profit": cumulative_profit,
            "cumulative_roi": cumulative_roi,
            "stake": stake,
            "return": ret,
            "hit": int(record.get("hit_count", 0)) > 0
        })

    return points


def make_svg_line_chart(points, value_key, title, unit="", color="#2563eb", baseline_zero=True):
    """
    SVGで簡単な折れ線グラフを作る。
    外部ライブラリを使わないので、無料でそのまま動きます。
    """

    width = 760
    height = 300
    padding_left = 60
    padding_right = 30
    padding_top = 35
    padding_bottom = 45

    if not points:
        return f"""
        <div class="empty-chart">
          {title}：データがありません。
        </div>
        """

    values = [float(p.get(value_key, 0)) for p in points]

    min_value = min(values)
    max_value = max(values)

    if baseline_zero:
        min_value = min(min_value, 0)
        max_value = max(max_value, 0)

    if min_value == max_value:
        min_value -= 1
        max_value += 1

    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom

    def x_pos(i):
        if len(points) == 1:
            return padding_left + plot_width / 2

        return padding_left + (i / (len(points) - 1)) * plot_width

    def y_pos(value):
        return padding_top + ((max_value - value) / (max_value - min_value)) * plot_height

    polyline_points = []

    circles = ""

    for i, p in enumerate(points):
        value = float(p.get(value_key, 0))
        x = x_pos(i)
        y = y_pos(value)
        polyline_points.append(f"{x:.2f},{y:.2f}")

        hit_class = "hit-dot" if p.get("hit") else "miss-dot"

        circles += f"""
        <circle class="{hit_class}" cx="{x:.2f}" cy="{y:.2f}" r="5">
          <title>{p.get("label", "")}：{value}{unit}</title>
        </circle>
        """

    # 0ライン
    zero_line = ""
    if min_value <= 0 <= max_value:
        y0 = y_pos(0)
        zero_line = f"""
        <line x1="{padding_left}" y1="{y0:.2f}" x2="{width - padding_right}" y2="{y0:.2f}" class="zero-line" />
        <text x="10" y="{y0 + 4:.2f}" class="axis-label">0{unit}</text>
        """

    # 最大・最小ラベル
    y_max = y_pos(max_value)
    y_min = y_pos(min_value)

    # X軸ラベルは最初と最後だけ表示
    first_label = points[0].get("label", "")
    last_label = points[-1].get("label", "")

    svg = f"""
    <div class="chart-title">{title}</div>
    <div class="chart-scroll">
      <svg viewBox="0 0 {width} {height}" class="line-chart" role="img" aria-label="{title}">
        <rect x="0" y="0" width="{width}" height="{height}" class="chart-bg" />

        <text x="10" y="{y_max + 4:.2f}" class="axis-label">{round(max_value, 2)}{unit}</text>
        <text x="10" y="{y_min + 4:.2f}" class="axis-label">{round(min_value, 2)}{unit}</text>

        {zero_line}

        <line x1="{padding_left}" y1="{padding_top}" x2="{padding_left}" y2="{height - padding_bottom}" class="axis-line" />
        <line x1="{padding_left}" y1="{height - padding_bottom}" x2="{width - padding_right}" y2="{height - padding_bottom}" class="axis-line" />

        <polyline
          fill="none"
          stroke="{color}"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
          points="{' '.join(polyline_points)}"
        />

        {circles}

        <text x="{padding_left}" y="{height - 15}" class="x-label">{first_label}</text>
        <text x="{width - padding_right}" y="{height - 15}" text-anchor="end" class="x-label">{last_label}</text>
      </svg>
    </div>
    """

    return svg


def make_group_bar_chart(group_summary):
    """
    本線・押さえ・穴狙いなどの分類別成績を横棒グラフにする。
    """

    if not group_summary:
        return """
        <div class="empty-chart">
          分類別データがありません。
        </div>
        """

    max_abs_profit = max(abs(int(g.get("profit", 0))) for g in group_summary)

    if max_abs_profit == 0:
        max_abs_profit = 1

    rows = ""

    for g in group_summary:
        group = g.get("group", "未分類")
        stake = int(g.get("stake", 0))
        ret = int(g.get("return", 0))
        profit = int(g.get("profit", 0))
        roi = g.get("roi", 0)
        hit_count = int(g.get("hit_count", 0))
        ticket_count = int(g.get("ticket_count", 0))

        width = min(100, round(abs(profit) / max_abs_profit * 100, 1))
        p_class = profit_class(profit)

        if profit > 0:
            profit_text = f"+{yen(profit)}"
        elif profit < 0:
            profit_text = f"-{yen(abs(profit))}"
        else:
            profit_text = yen(0)

        rows += f"""
        <div class="group-row">
          <div class="group-info">
            <div class="group-name">{group}</div>
            <div class="group-detail">
              買い目 {ticket_count}点 / 的中 {hit_count}点 / 投資 {yen(stake)} / 払戻 {yen(ret)} / 回収率 {roi}%
            </div>
          </div>
          <div class="bar-area">
            <div class="bar {p_class}" style="width: {width}%;">
              <span>{profit_text}</span>
            </div>
          </div>
        </div>
        """

    return f"""
    <div class="chart-title">分類別 利益比較</div>
    <div class="group-chart">
      {rows}
    </div>
    """


def make_recent_table(records, limit=10):
    recent_records = list(reversed(records))[:limit]

    if not recent_records:
        return """
        <p>まだレース履歴がありません。</p>
        """

    rows = ""

    for r in recent_records:
        profit = int(r.get("profit", 0))
        p_class = profit_class(profit)

        if profit > 0:
            profit_text = f"+{yen(profit)}"
        elif profit < 0:
            profit_text = f"-{yen(abs(profit))}"
        else:
            profit_text = yen(0)

        hit_text = "的中" if int(r.get("hit_count", 0)) > 0 else "不的中"
        hit_class = "hit-text" if int(r.get("hit_count", 0)) > 0 else "miss-text"

        rows += f"""
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

    return f"""
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
        {rows}
      </tbody>
    </table>
    """


def make_html(history):
    records = sort_records(history.get("records", []))
    summary = history.get("summary", {})
    group_summary = history.get("group_summary", [])

    cumulative_points = make_cumulative_data(records)

    profit_chart = make_svg_line_chart(
        cumulative_points,
        value_key="cumulative_profit",
        title="累計利益の推移",
        unit="円",
        color="#dc2626",
        baseline_zero=True
    )

    roi_chart = make_svg_line_chart(
        cumulative_points,
        value_key="cumulative_roi",
        title="累計回収率の推移",
        unit="%",
        color="#2563eb",
        baseline_zero=False
    )

    group_chart = make_group_bar_chart(group_summary)
    recent_table = make_recent_table(records)

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
  <title>成績グラフ</title>
  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #7c3aed, #4c1d95);
      color: white;
      padding: 20px;
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
      margin-top: 4px;
      font-size: 22px;
      font-weight: 800;
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

    .chart-title {{
      font-size: 18px;
      font-weight: 800;
      margin-bottom: 12px;
    }}

    .chart-scroll {{
      overflow-x: auto;
    }}

    .line-chart {{
      width: 100%;
      min-width: 720px;
      height: auto;
      display: block;
    }}

    .chart-bg {{
      fill: #ffffff;
    }}

    .axis-line {{
      stroke: #9ca3af;
      stroke-width: 1.5;
    }}

    .zero-line {{
      stroke: #6b7280;
      stroke-width: 1.5;
      stroke-dasharray: 6 6;
    }}

    .axis-label {{
      fill: #6b7280;
      font-size: 12px;
    }}

    .x-label {{
      fill: #6b7280;
      font-size: 11px;
    }}

    .hit-dot {{
      fill: #dc2626;
      stroke: white;
      stroke-width: 2;
    }}

    .miss-dot {{
      fill: #6b7280;
      stroke: white;
      stroke-width: 2;
    }}

    .empty-chart {{
      padding: 20px;
      background: #f9fafb;
      border-radius: 12px;
      color: #6b7280;
    }}

    .group-chart {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .group-row {{
      display: grid;
      grid-template-columns: 260px 1fr;
      gap: 12px;
      align-items: center;
    }}

    .group-name {{
      font-weight: 800;
      font-size: 16px;
    }}

    .group-detail {{
      margin-top: 4px;
      color: #6b7280;
      font-size: 12px;
      line-height: 1.5;
    }}

    .bar-area {{
      background: #f3f4f6;
      border-radius: 999px;
      overflow: hidden;
      min-height: 30px;
      position: relative;
    }}

    .bar {{
      min-width: 60px;
      height: 30px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding: 0 10px;
      box-sizing: border-box;
      color: white;
      font-size: 13px;
      font-weight: bold;
    }}

    .bar.plus {{
      background: #dc2626;
    }}

    .bar.minus {{
      background: #2563eb;
    }}

    .bar.zero {{
      background: #6b7280;
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

    .hit-text {{
      color: #dc2626;
      font-weight: bold;
    }}

    .miss-text {{
      color: #6b7280;
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
      background: #7c3aed;
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

      .group-row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>成績グラフ</h1>
    <p>過去の予想成績をグラフで確認します</p>
  </header>

  <main>
    <section class="card">
      <h2>全体サマリー</h2>
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
      {profit_chart}
    </section>

    <section class="card">
      {roi_chart}
    </section>

    <section class="card">
      {group_chart}
    </section>

    <section class="card">
      <h2>直近レース</h2>
      {recent_table}
    </section>

    <section class="card">
      <h2>ページ移動</h2>
      <div class="links">
        <a class="link-button" href="./index.html">予想ページへ</a>
        <a class="link-button" href="./evaluation.html">直近評価へ</a>
        <a class="link-button" href="./history.html">過去成績へ</a>
        <a class="link-button" href="./evaluation_history.json">履歴JSONを見る</a>
      </div>
    </section>

    <section class="card notice">
      このページは学習用・分析練習用です。実際の購入や利益を保証するものではありません。
      グラフは過去の仮想評価を見やすくしたもので、将来の的中や利益を保証するものではありません。
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    history = load_json(HISTORY_PATH)
    html = make_html(history)

    CHARTS_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CHARTS_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("成績グラフページを作成しました。")
    print(f"HTML: {CHARTS_HTML_PATH}")


if __name__ == "__main__":
    main()

