import json
from pathlib import Path


HISTORY_PATH = Path("docs/stage_evaluation_history.json")
OUTPUT_HTML_PATH = Path("docs/stage_charts.html")


STAGE_ORDER = [
    "PRE_NIGHT",
    "MORNING",
    "PRE_EXHIBITION",
    "POST_EXHIBITION",
    "FINAL"
]


STAGE_LABELS = {
    "PRE_NIGHT": "前日夜",
    "MORNING": "当日朝",
    "PRE_EXHIBITION": "展示前",
    "POST_EXHIBITION": "展示後",
    "FINAL": "最終"
}


STAGE_COLORS = {
    "PRE_NIGHT": "#475569",
    "MORNING": "#2563eb",
    "PRE_EXHIBITION": "#0f766e",
    "POST_EXHIBITION": "#ea580c",
    "FINAL": "#be123c"
}


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            "docs/stage_evaluation_history.json が見つかりません。先に Evaluate Result を実行してください。"
        )

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


def profit_text(value):
    value = int(value)

    if value > 0:
        return f"+{yen(value)}"
    elif value < 0:
        return f"-{yen(abs(value))}"
    else:
        return yen(0)


def sort_records(records):
    return sorted(
        records,
        key=lambda r: (
            str(r.get("date", "")),
            str(r.get("place", "")),
            str(r.get("race_no", ""))
        )
    )


def get_stage_record(record, stage_name):
    for stage in record.get("stages", []):
        if stage.get("stage") == stage_name and stage.get("exists"):
            return stage

    return None


def get_stage_summary(record, stage_name):
    stage = get_stage_record(record, stage_name)

    if stage is None:
        return None

    return stage.get("summary", {})


def build_cumulative_points(records):
    """
    ステージごとの累計利益・累計回収率を作る。
    """

    stage_states = {}

    for stage in STAGE_ORDER:
        stage_states[stage] = {
            "stake": 0,
            "return": 0,
            "profit": 0,
            "points": []
        }

    for index, record in enumerate(records, start=1):
        label = f'{record.get("date", "")} {record.get("place", "")} {record.get("race_no", "")}'

        for stage in STAGE_ORDER:
            summary = get_stage_summary(record, stage)

            state = stage_states[stage]

            if summary is not None:
                stake = int(summary.get("total_stake", 0))
                ret = int(summary.get("total_return", 0))
                profit = int(summary.get("profit", ret - stake))

                state["stake"] += stake
                state["return"] += ret
                state["profit"] += profit

            if state["stake"] > 0:
                roi = round((state["return"] / state["stake"]) * 100, 2)
            else:
                roi = 0

            state["points"].append({
                "index": index,
                "label": label,
                "stage": stage,
                "stage_label": STAGE_LABELS.get(stage, stage),
                "cumulative_profit": state["profit"],
                "cumulative_roi": roi,
                "stake": state["stake"],
                "return": state["return"]
            })

    return stage_states


def make_multi_line_chart(stage_states, value_key, title, unit="", baseline_zero=True):
    """
    複数ステージを1つのSVG折れ線グラフで表示する。
    外部ライブラリなしで動く。
    """

    width = 860
    height = 360
    padding_left = 70
    padding_right = 40
    padding_top = 40
    padding_bottom = 60

    all_points = []

    for stage in STAGE_ORDER:
        all_points.extend(stage_states.get(stage, {}).get("points", []))

    if not all_points:
        return f"""
        <div class="empty-chart">
          {title}：データがありません。
        </div>
        """

    values = [float(p.get(value_key, 0)) for p in all_points]

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

    max_len = max(
        len(stage_states.get(stage, {}).get("points", []))
        for stage in STAGE_ORDER
    )

    def x_pos(i):
        if max_len <= 1:
            return padding_left + plot_width / 2

        return padding_left + (i / (max_len - 1)) * plot_width

    def y_pos(value):
        return padding_top + ((max_value - value) / (max_value - min_value)) * plot_height

    lines_html = ""
    dots_html = ""

    for stage in STAGE_ORDER:
        points = stage_states.get(stage, {}).get("points", [])

        if not points:
            continue

        color = STAGE_COLORS.get(stage, "#111827")
        polyline_points = []

        for i, p in enumerate(points):
            value = float(p.get(value_key, 0))
            x = x_pos(i)
            y = y_pos(value)

            polyline_points.append(f"{x:.2f},{y:.2f}")

            dots_html += f"""
            <circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" stroke="white" stroke-width="2">
              <title>{p.get("stage_label", "")} / {p.get("label", "")}：{value}{unit}</title>
            </circle>
            """

        lines_html += f"""
        <polyline
          fill="none"
          stroke="{color}"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
          points="{' '.join(polyline_points)}"
        />
        """

    zero_line = ""

    if min_value <= 0 <= max_value:
        y0 = y_pos(0)
        zero_line = f"""
        <line x1="{padding_left}" y1="{y0:.2f}" x2="{width - padding_right}" y2="{y0:.2f}" class="zero-line" />
        <text x="10" y="{y0 + 4:.2f}" class="axis-label">0{unit}</text>
        """

    y_max = y_pos(max_value)
    y_min = y_pos(min_value)

    first_label = ""
    last_label = ""

    for stage in STAGE_ORDER:
        points = stage_states.get(stage, {}).get("points", [])
        if points:
            first_label = points[0].get("label", "")
            last_label = points[-1].get("label", "")
            break

    legend = ""

    for stage in STAGE_ORDER:
        color = STAGE_COLORS.get(stage, "#111827")
        label = STAGE_LABELS.get(stage, stage)

        legend += f"""
        <span class="legend-item">
          <span class="legend-color" style="background:{color};"></span>
          {label}
        </span>
        """

    svg = f"""
    <div class="chart-title">{title}</div>

    <div class="legend">
      {legend}
    </div>

    <div class="chart-scroll">
      <svg viewBox="0 0 {width} {height}" class="line-chart" role="img" aria-label="{title}">
        <rect x="0" y="0" width="{width}" height="{height}" class="chart-bg" />

        <text x="10" y="{y_max + 4:.2f}" class="axis-label">{round(max_value, 2)}{unit}</text>
        <text x="10" y="{y_min + 4:.2f}" class="axis-label">{round(min_value, 2)}{unit}</text>

        {zero_line}

        <line x1="{padding_left}" y1="{padding_top}" x2="{padding_left}" y2="{height - padding_bottom}" class="axis-line" />
        <line x1="{padding_left}" y1="{height - padding_bottom}" x2="{width - padding_right}" y2="{height - padding_bottom}" class="axis-line" />

        {lines_html}
        {dots_html}

        <text x="{padding_left}" y="{height - 20}" class="x-label">{first_label}</text>
        <text x="{width - padding_right}" y="{height - 20}" text-anchor="end" class="x-label">{last_label}</text>
      </svg>
    </div>
    """

    return svg


def make_stage_roi_bar_chart(stage_summary):
    """
    ステージ別回収率を横棒グラフにする。
    """

    if not stage_summary:
        return """
        <div class="empty-chart">
          ステージ別成績データがありません。
        </div>
        """

    max_roi = max(float(s.get("roi", 0)) for s in stage_summary)

    if max_roi <= 0:
        max_roi = 100

    rows = ""

    for s in stage_summary:
        stage = s.get("stage", "")
        label = s.get("label", STAGE_LABELS.get(stage, stage))
        roi = float(s.get("roi", 0))
        race_count = int(s.get("race_count", 0))
        profit = int(s.get("profit", 0))
        stake = int(s.get("total_stake", 0))
        ret = int(s.get("total_return", 0))

        width = min(100, round((roi / max_roi) * 100, 1)) if max_roi > 0 else 0
        color = STAGE_COLORS.get(stage, "#111827")

        rows += f"""
        <div class="bar-row">
          <div class="bar-label">
            <strong>{label}</strong><br>
            <span>{race_count}R / 投資 {yen(stake)} / 払戻 {yen(ret)} / 利益 <span class="{profit_class(profit)}">{profit_text(profit)}</span></span>
          </div>

          <div class="bar-area">
            <div class="bar" style="width:{width}%; background:{color};">
              {roi}%
            </div>
          </div>
        </div>
        """

    return f"""
    <div class="chart-title">ステージ別 回収率比較</div>
    <div class="bar-chart">
      {rows}
    </div>
    """


def make_transition_bar_chart(transition_summary):
    """
    前日夜→展示後などの改善率を棒グラフにする。
    """

    if not transition_summary:
        return """
        <div class="empty-chart">
          改善比較データがありません。
        </div>
        """

    rows = ""

    for t in transition_summary:
        label = t.get("label", "")
        compared_count = int(t.get("compared_count", 0))
        improved_count = int(t.get("improved_count", 0))
        worsened_count = int(t.get("worsened_count", 0))
        same_count = int(t.get("same_count", 0))
        improved_rate = float(t.get("improved_rate", 0))
        total_profit_diff = int(round(float(t.get("total_profit_diff", 0))))

        rows += f"""
        <div class="bar-row">
          <div class="bar-label">
            <strong>{label}</strong><br>
            <span>
              比較 {compared_count}R /
              改善 {improved_count}R /
              悪化 {worsened_count}R /
              変化なし {same_count}R /
              利益差 <span class="{profit_class(total_profit_diff)}">{profit_text(total_profit_diff)}</span>
            </span>
          </div>

          <div class="bar-area">
            <div class="bar improve-bar" style="width:{min(100, improved_rate)}%;">
              {improved_rate}%
            </div>
          </div>
        </div>
        """

    return f"""
    <div class="chart-title">ステージ間 改善率</div>
    <div class="bar-chart">
      {rows}
    </div>
    """


def make_recent_table(records, limit=10):
    recent_records = list(reversed(records))[:limit]

    if not recent_records:
        return "<p class='notice'>まだ履歴がありません。</p>"

    rows = ""

    for r in recent_records:
        def stage_profit_cell(stage_name):
            summary = get_stage_summary(r, stage_name)

            if summary is None:
                return "<td>-</td>"

            profit = int(summary.get("profit", 0))

            return f'<td class="{profit_class(profit)}">{profit_text(profit)}</td>'

        best_stage = r.get("best_stage") or {}
        best_label = best_stage.get("label", "-")

        rows += f"""
        <tr>
          <td>{r.get("date", "")}</td>
          <td>{r.get("place", "")}</td>
          <td>{r.get("race_no", "")}</td>
          <td>{r.get("result", {}).get("trifecta", "")}</td>
          {stage_profit_cell("PRE_NIGHT")}
          {stage_profit_cell("POST_EXHIBITION")}
          {stage_profit_cell("FINAL")}
          <td>{best_label}</td>
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
          <th>前日夜利益</th>
          <th>展示後利益</th>
          <th>最終利益</th>
          <th>最良ステージ</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """


def make_html(history):
    records = sort_records(history.get("records", []))
    stage_summary = history.get("stage_summary", [])
    transition_summary = history.get("transition_summary", [])
    overall = history.get("overall_summary", {})

    stage_states = build_cumulative_points(records)

    profit_chart = make_multi_line_chart(
        stage_states,
        value_key="cumulative_profit",
        title="ステージ別 累計利益の推移",
        unit="円",
        baseline_zero=True
    )

    roi_chart = make_multi_line_chart(
        stage_states,
        value_key="cumulative_roi",
        title="ステージ別 累計回収率の推移",
        unit="%",
        baseline_zero=False
    )

    roi_bar_chart = make_stage_roi_bar_chart(stage_summary)
    transition_chart = make_transition_bar_chart(transition_summary)
    recent_table = make_recent_table(records)

    best_stage = overall.get("best_stage")

    if best_stage:
        best_profit = int(best_stage.get("profit", 0))

        best_html = f"""
        <div class="best-box">
          通算で最も成績が良いステージ：
          <strong>{best_stage.get("label", "")}</strong><br>
          利益：
          <strong class="{profit_class(best_profit)}">{profit_text(best_profit)}</strong>
          / 回収率：
          <strong>{best_stage.get("roi", 0)}%</strong>
          / 評価R数：
          <strong>{best_stage.get("race_count", 0)}R</strong>
        </div>
        """
    else:
        best_html = """
        <div class="best-box">
          まだ通算成績を計算できるステージがありません。
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>ステージ別成績グラフ</title>

  <style>
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}

    header {{
      background: linear-gradient(135deg, #9333ea, #d946ef);
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

    .best-box {{
      background: #faf5ff;
      border: 1px solid #d946ef;
      color: #581c87;
      border-radius: 14px;
      padding: 14px;
      line-height: 1.8;
      font-size: 15px;
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

    .chart-title {{
      font-size: 18px;
      font-weight: 900;
      margin-bottom: 12px;
    }}

    .chart-scroll {{
      overflow-x: auto;
    }}

    .line-chart {{
      width: 100%;
      min-width: 820px;
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

    .legend {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}

    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 800;
      color: #374151;
    }}

    .legend-color {{
      width: 14px;
      height: 14px;
      border-radius: 999px;
      display: inline-block;
    }}

    .bar-chart {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .bar-row {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 12px;
      align-items: center;
    }}

    .bar-label {{
      font-size: 13px;
      line-height: 1.6;
      color: #374151;
    }}

    .bar-area {{
      background: #f3f4f6;
      border-radius: 999px;
      min-height: 32px;
      overflow: hidden;
    }}

    .bar {{
      min-width: 55px;
      height: 32px;
      color: white;
      font-weight: 900;
      font-size: 13px;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      padding: 0 10px;
      border-radius: 999px;
      box-sizing: border-box;
    }}

    .improve-bar {{
      background: linear-gradient(135deg, #16a34a, #4ade80);
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
      background: #9333ea;
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

    .empty-chart {{
      padding: 20px;
      background: #f9fafb;
      border-radius: 12px;
      color: #6b7280;
    }}

    @media (max-width: 700px) {{
      .summary-grid {{
        grid-template-columns: 1fr;
      }}

      .bar-row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>

<body>
  <header>
    <h1>ステージ別成績グラフ</h1>
    <p>前日夜・展示後・最終予想の推移をグラフで確認します</p>
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

      {best_html}
    </section>

    <section class="card">
      {profit_chart}
    </section>

    <section class="card">
      {roi_chart}
    </section>

    <section class="card">
      {roi_bar_chart}
    </section>

    <section class="card">
      {transition_chart}
    </section>

    <section class="card">
      <h2>直近レースのステージ別利益</h2>
      {recent_table}
    </section>

    <section class="card">
      <h2>ページ移動</h2>

      <div class="links">
        <a class="link-button" href="./index.html">予想ページへ</a>
        <a class="link-button" href="./stage_history.html">ステージ別過去成績へ</a>
        <a class="link-button" href="./stage_evaluation.html">直近ステージ評価へ</a>
        <a class="link-button" href="./compare.html">予想比較へ</a>
        <a class="link-button" href="./stage_evaluation_history.json">履歴JSON</a>
      </div>
    </section>

    <section class="card notice">
      このページは学習用・分析練習用です。実際の購入や利益を保証するものではありません。
      グラフを見ることで、前日夜予想・展示後予想・最終予想のどの段階が有効かを検証できます。
    </section>
  </main>
</body>
</html>
"""

    return html


def main():
    history = load_json(HISTORY_PATH)
    html = make_html(history)

    OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_HTML_PATH.open("w", encoding="utf-8") as f:
        f.write(html)

    print("ステージ別成績グラフを作成しました。")
    print(f"HTML: {OUTPUT_HTML_PATH}")


if __name__ == "__main__":
    main()

