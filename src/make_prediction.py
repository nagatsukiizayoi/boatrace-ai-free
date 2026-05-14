import csv
import json
from pathlib import Path
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


INPUT_CSV = Path("data/race.csv")
OUTPUT_JSON = Path("docs/prediction.json")


def now_jst_string():
    if ZoneInfo:
        return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_value(row, *names, default=""):
    """
    CSVの列名が多少違っても読めるようにする関数です。
    例:
    boat / 艇番
    driver / 選手名
    """
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return default


def to_float(value, default=0.0):
    """
    文字列を小数に変換します。
    例:
    "45.0%" -> 45.0
    "0.15"  -> 0.15
    """
    try:
        text = str(value).replace("%", "").strip()
        if text == "":
            return default
        return float(text)
    except ValueError:
        return default


def to_int(value, default=0):
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


def course_bonus(course):
    """
    コース補正です。
    ボートレースは一般的に内側コースが有利なので、
    1コースに高めの点数を付けています。
    """
    bonuses = {
        1: 12.0,
        2: 8.0,
        3: 5.0,
        4: 3.0,
        5: 1.0,
        6: 0.0,
    }
    return bonuses.get(course, 0.0)


def calculate_score(win_rate, motor_rate, avg_st, course):
    """
    簡易スコア計算です。

    win_rate   : 選手勝率。高いほど良い
    motor_rate : モーター率。高いほど良い
    avg_st     : 平均ST。小さいほど良い
    course     : コース。内側ほど少し有利

    注意:
    これは学習用の簡易式です。
    実際の舟券的中を保証するものではありません。
    """

    # 選手勝率の影響
    win_score = win_rate * 12.0

    # モーター率の影響
    motor_score = motor_rate * 0.7

    # 平均STの影響
    # 0.20より早いほど加点、遅いほど減点
    st_score = (0.20 - avg_st) * 120.0

    # コース補正
    c_bonus = course_bonus(course)

    score = win_score + motor_score + st_score + c_bonus

    return round(score, 2)


def make_confidence_scores(boats):
    """
    スコアをもとに信頼度を作ります。
    最高スコアを95%、最低付近を50%くらいにします。
    """
    if not boats:
        return boats

    scores = [boat["score"] for boat in boats]
    max_score = max(scores)
    min_score = min(scores)

    for boat in boats:
        if max_score == min_score:
            confidence = 70
        else:
            ratio = (boat["score"] - min_score) / (max_score - min_score)
            confidence = 50 + ratio * 45

        boat["confidence"] = round(confidence)

    return boats


def make_tickets(sorted_boats):
    """
    上位艇から3連単の買い目候補を作ります。
    """
    if len(sorted_boats) < 3:
        return []

    b1 = sorted_boats[0]["boat"]
    b2 = sorted_boats[1]["boat"]
    b3 = sorted_boats[2]["boat"]

    tickets = [
        f"{b1}-{b2}-{b3}",
        f"{b1}-{b3}-{b2}",
        f"{b2}-{b1}-{b3}",
    ]

    if len(sorted_boats) >= 4:
        b4 = sorted_boats[3]["boat"]
        tickets.append(f"{b1}-{b2}-{b4}")
        tickets.append(f"{b1}-{b4}-{b2}")

    return tickets


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"{INPUT_CSV} が見つかりません")

    rows = []

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("race.csv にデータがありません")

    boats = []

    for row in rows:
        date = get_value(row, "date", "日付")
        stadium = get_value(row, "stadium", "場", "レース場")
        race_no = get_value(row, "race_no", "race", "レース番号", "R")

        boat = to_int(get_value(row, "boat", "艇番"))
        course = to_int(get_value(row, "course", "コース"), default=boat)
        driver = get_value(row, "driver", "選手名", "name", default=f"{boat}号艇")

        win_rate = to_float(get_value(row, "win_rate", "勝率", "選手勝率"))
        motor_rate = to_float(get_value(row, "motor_rate", "モーター率", "motor"))
        avg_st = to_float(get_value(row, "avg_st", "平均ST", "st"), default=0.20)

        score = calculate_score(
            win_rate=win_rate,
            motor_rate=motor_rate,
            avg_st=avg_st,
            course=course,
        )

        boats.append({
            "boat": boat,
            "course": course,
            "driver": driver,
            "win_rate": win_rate,
            "motor_rate": motor_rate,
            "avg_st": avg_st,
            "score": score,
        })

    # スコアが高い順に並べます
    boats = sorted(boats, key=lambda x: x["score"], reverse=True)

    # 順位を付けます
    for index, boat in enumerate(boats, start=1):
        boat["rank"] = index

    # 信頼度を付けます
    boats = make_confidence_scores(boats)

    # 上位3艇を予想として使います
    predictions = []

    labels = {
        1: "1着候補",
        2: "2着候補",
        3: "3着候補",
    }

    for boat in boats[:3]:
        predictions.append({
            "rank": boat["rank"],
            "boat": boat["boat"],
            "course": boat["course"],
            "driver": boat["driver"],
            "label": labels.get(boat["rank"], f"{boat['rank']}着候補"),
            "confidence": boat["confidence"],
            "score": boat["score"],
        })

    first_row = rows[0]

    race = {
        "date": get_value(first_row, "date", "日付"),
        "stadium": get_value(first_row, "stadium", "場", "レース場"),
        "race_no": get_value(first_row, "race_no", "race", "レース番号", "R"),
    }

    result = {
        "updated_at": now_jst_string(),
        "race": race,
        "predictions": predictions,
        "all_boats": boats,
        "tickets": make_tickets(boats),
        "notice": "この予想はCSVデータを使った学習用の簡易予想です。実際の的中や利益を保証するものではありません。",
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"{OUTPUT_JSON} を作成しました")


if __name__ == "__main__":
    main()
