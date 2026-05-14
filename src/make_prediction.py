import csv
import json
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


DATA_PATH = Path("data/race.csv")
OUTPUT_PATH = Path("docs/prediction.json")


def to_float(value, default=0.0):
    """
    CSVの文字列をfloatに変換するための関数。
    空欄や変換できない値が来てもエラーで止まらないようにする。
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):
    """
    CSVの文字列をintに変換するための関数。
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_race_rows():
    """
    data/race.csv を読み込む。
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} が見つかりません")

    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("race.csv にデータがありません")

    return rows


def calculate_score(row):
    """
    1艇ごとのスコアを計算する。

    今回は学習用として、以下を使います。
    - 勝率
    - モーター率
    - 平均スタート
    - コース補正
    - 少しだけランダム補正
    """

    boat = to_int(row.get("boat"))
    course = to_int(row.get("course"), boat)

    win_rate = to_float(row.get("win_rate"))
    motor_rate = to_float(row.get("motor_rate"))
    avg_st = to_float(row.get("avg_st"), 0.18)

    # 勝率が高いほど加点
    win_score = win_rate * 8

    # モーター率が高いほど加点
    motor_score = motor_rate * 0.6

    # 平均STは小さいほど良い、という仮ルール
    # 0.10なら高評価、0.20なら低め評価
    start_score = max(0, (0.25 - avg_st) * 100)

    # 内側コースを少し有利にする仮ルール
    course_bonus = max(0, (7 - course) * 3)

    # 完全に同じ結果になりすぎないように小さな補正
    random_bonus = random.uniform(-2.0, 2.0)

    score = win_score + motor_score + start_score + course_bonus + random_bonus

    return round(score, 2)


def make_prediction():
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    today_text = now.strftime("%Y-%m-%d")

    rows = load_race_rows()

    first_row = rows[0]

    race_date = first_row.get("date") or today_text
    stadium = first_row.get("stadium") or "未設定"
    race_no = first_row.get("race_no") or "未設定"

    race = {
        "date": race_date,
        "stadium": stadium,
        "race_no": race_no
    }

    # 同じ日・同じレースなら大きく結果が変わりすぎないようにする
    seed_text = f"{race_date}-{stadium}-{race_no}"
    random.seed(seed_text)

    boats = []

    for row in rows:
        boat_no = to_int(row.get("boat"))
        course = to_int(row.get("course"), boat_no)
        driver = row.get("driver") or f"{boat_no}号艇"

        score = calculate_score(row)

        boats.append({
            "boat": boat_no,
            "course": course,
            "driver": driver,
            "score": score,
            "win_rate": to_float(row.get("win_rate")),
            "motor_rate": to_float(row.get("motor_rate")),
            "avg_st": to_float(row.get("avg_st"))
        })

    # スコアが高い順に並べる
    boats.sort(key=lambda x: x["score"], reverse=True)

    # 上位3艇を予想として使う
    top3 = boats[:3]

    predictions = []

    for index, item in enumerate(top3):
        rank = index + 1

        # confidenceは見やすいように50〜95くらいに丸める
        confidence = int(min(95, max(50, item["score"])))

        predictions.append({
            "rank": rank,
            "boat": item["boat"],
            "course": item["course"],
            "driver": item["driver"],
            "label": f"{rank}着候補",
            "confidence": confidence,
            "score": item["score"]
        })

    first = top3[0]["boat"]
    second = top3[1]["boat"]
    third = top3[2]["boat"]

    tickets = [
        f"{first}-{second}-{third}",
        f"{first}-{third}-{second}",
        f"{second}-{first}-{third}"
    ]

    data = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M"),
        "race": race,
        "predictions": predictions,
        "tickets": tickets,
        "source": {
            "type": "csv",
            "path": str(DATA_PATH)
        },
        "notice": "このページは学習用のサンプルです。表示されている予想は仮のデータです。実際の的中や利益を保証するものではありません。"
    }

    return data


def main():
    data = make_prediction()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("prediction.json を作成しました")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
