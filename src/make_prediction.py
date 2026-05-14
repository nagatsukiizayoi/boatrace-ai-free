import json
import os
from datetime import datetime, timezone


def mark_for_rank(rank):
    """
    順位に応じて予想印を返します。
    """
    marks = {
        1: ("◎", "本命"),
        2: ("○", "対抗"),
        3: ("▲", "単穴"),
        4: ("△", "連下"),
        5: ("☆", "穴"),
        6: ("×", "押さえ"),
    }

    return marks.get(rank, ("", ""))


def to_float(value, default=0.0):
    """
    数値に変換できない値が来てもエラーにならないようにします。
    """
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_boats():
    """
    出走データを読み込みます。

    data/race.json や docs/race.json がある場合はそれを使います。
    ない場合はサンプルデータで prediction.json を作ります。
    """

    possible_files = [
        "data/race.json",
        "data/boats.json",
        "docs/race.json",
    ]

    for path in possible_files:
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            if "boats" in data:
                return normalize_boats(data["boats"])
            if "racers" in data:
                return normalize_boats(data["racers"])
            if "entries" in data:
                return normalize_boats(data["entries"])

        if isinstance(data, list):
            return normalize_boats(data)

    return sample_boats()


def normalize_boats(items):
    """
    読み込んだデータのキー名が多少違っても使えるように整えます。
    """
    boats = []

    for index, item in enumerate(items, start=1):
        boat_no = item.get("boat", item.get("boat_no", item.get("number", index)))
        course = item.get("course", item.get("course_no", boat_no))
        driver = item.get("driver", item.get("name", item.get("racer", f"選手{index}")))

        win_rate = item.get("win_rate", item.get("rate", item.get("racer_rate", 5.0)))
        motor_rate = item.get("motor_rate", item.get("motor", item.get("motor_win_rate", 30.0)))
        avg_st = item.get("avg_st", item.get("st", item.get("start_timing", 0.16)))

        boats.append({
            "boat": int(to_float(boat_no, index)),
            "course": int(to_float(course, boat_no)),
            "driver": str(driver),
            "win_rate": to_float(win_rate, 5.0),
            "motor_rate": to_float(motor_rate, 30.0),
            "avg_st": to_float(avg_st, 0.16),
        })

    return boats


def sample_boats():
    """
    データファイルがない場合に使うサンプルデータです。
    """
    return [
        {
            "boat": 1,
            "course": 1,
            "driver": "選手A",
            "win_rate": 7.20,
            "motor_rate": 45.0,
            "avg_st": 0.13,
        },
        {
            "boat": 2,
            "course": 2,
            "driver": "選手B",
            "win_rate": 6.10,
            "motor_rate": 38.0,
            "avg_st": 0.15,
        },
        {
            "boat": 3,
            "course": 3,
            "driver": "選手C",
            "win_rate": 6.60,
            "motor_rate": 41.5,
            "avg_st": 0.14,
        },
        {
            "boat": 4,
            "course": 4,
            "driver": "選手D",
            "win_rate": 5.80,
            "motor_rate": 35.0,
            "avg_st": 0.16,
        },
        {
            "boat": 5,
            "course": 5,
            "driver": "選手E",
            "win_rate": 5.20,
            "motor_rate": 33.0,
            "avg_st": 0.17,
        },
        {
            "boat": 6,
            "course": 6,
            "driver": "選手F",
            "win_rate": 4.90,
            "motor_rate": 29.0,
            "avg_st": 0.18,
        },
    ]


def calculate_score(boat):
    """
    各艇のスコアを計算します。

    点数の考え方：
    - 勝率が高いほどプラス
    - モーター率が高いほどプラス
    - 平均STが早いほどプラス
    - 内側コースを少し有利にする
    """

    win_rate = boat["win_rate"]
    motor_rate = boat["motor_rate"]
    avg_st = boat["avg_st"]
    course = boat["course"]

    course_bonus_map = {
        1: 18,
        2: 10,
        3: 7,
        4: 4,
        5: 1,
        6: 0,
    }

    course_bonus = course_bonus_map.get(course, 0)

    # 平均STは小さいほど良いので、0.25との差を点数化します
    start_score = max(0, (0.25 - avg_st) * 100)

    score = (
        win_rate * 10
        + motor_rate * 1.2
        + start_score
        + course_bonus
    )

    return round(score, 2)


def make_confidence_scores(boats):
    """
    順位に応じて信頼度を付けます。
    """
    confidence_map = {
        1: 95,
        2: 88,
        3: 80,
        4: 70,
        5: 60,
        6: 50,
    }

    for boat in boats:
        rank = boat.get("rank", 6)
        boat["confidence"] = confidence_map.get(rank, 50)

    return boats


def make_predictions(boats):
    """
    予想順位のデータを作ります。
    """

    labels = {
        1: "1着候補",
        2: "2着候補",
        3: "3着候補",
        4: "4着候補",
        5: "5着候補",
        6: "6着候補",
    }

    predictions = []

    for boat in boats:
        predictions.append({
            "rank": boat["rank"],
            "mark": boat["mark"],
            "mark_name": boat["mark_name"],
            "boat": boat["boat"],
            "course": boat["course"],
            "driver": boat["driver"],
            "label": labels.get(boat["rank"], f"{boat['rank']}着候補"),
            "win_rate": boat["win_rate"],
            "motor_rate": boat["motor_rate"],
            "avg_st": boat["avg_st"],
            "score": boat["score"],
            "confidence": boat["confidence"],
        })

    return predictions


def make_tickets(boats):
    """
    買い目候補を作ります。
    STEP 8ではシンプルな買い目にしています。
    STEP 9で本線・押さえ・穴狙いに分けて強化します。
    """

    if len(boats) < 3:
        return []

    first = boats[0]["boat"]
    second = boats[1]["boat"]
    third = boats[2]["boat"]

    fourth = boats[3]["boat"] if len(boats) >= 4 else third

    tickets = [
        f"{first}-{second}-{third}",
        f"{first}-{third}-{second}",
        f"{second}-{first}-{third}",
        f"{first}-{second}-{fourth}",
        f"{third}-{first}-{second}",
    ]

    return tickets


def build_prediction_json():
    """
    prediction.json に出力する全体データを作ります。
    """

    boats = load_boats()

    # スコア計算
    for boat in boats:
        boat["score"] = calculate_score(boat)

    # スコアが高い順に並べ替え
    boats.sort(key=lambda x: x["score"], reverse=True)

    # 順位と予想印を付ける
    for index, boat in enumerate(boats, start=1):
        boat["rank"] = index

        mark, mark_name = mark_for_rank(index)
        boat["mark"] = mark
        boat["mark_name"] = mark_name

    # 信頼度を付ける
    boats = make_confidence_scores(boats)

    predictions = make_predictions(boats)
    tickets = make_tickets(boats)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "race": {
            "place": "サンプル競艇場",
            "race_no": "12R",
            "title": "AI予想",
        },
        "predictions": predictions,
        "all_boats": boats,
        "tickets": tickets,
    }

    return result


def save_prediction_json(data):
    """
    docs/prediction.json に保存します。
    """

    os.makedirs("docs", exist_ok=True)

    output_path = "docs/prediction.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"{output_path} を作成しました。")


def main():
    data = build_prediction_json()
    save_prediction_json(data)


if __name__ == "__main__":
    main()
