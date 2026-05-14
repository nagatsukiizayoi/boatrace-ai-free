import json
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def make_prediction():
    # 日本時間
    now = datetime.now(ZoneInfo("Asia/Tokyo"))

    # 今回はサンプルとして固定のレース情報を使います
    race = {
        "date": now.strftime("%Y-%m-%d"),
        "stadium": "桐生",
        "race_no": "12R"
    }

    # 日付ごとに少し結果が変わるようにする
    seed_text = now.strftime("%Y%m%d") + race["stadium"] + race["race_no"]
    random.seed(seed_text)

    boats = []

    # 1〜6号艇に仮のスコアを付ける
    for boat_no in range(1, 7):
        base_score = random.randint(35, 85)

        # 今回は学習用として、内側の艇を少し有利にする
        course_bonus = (7 - boat_no) * 3

        score = base_score + course_bonus

        boats.append({
            "boat": boat_no,
            "score": score
        })

    # スコアが高い順に並べる
    boats.sort(key=lambda x: x["score"], reverse=True)

    # 上位3艇を予想として使う
    top3 = boats[:3]

    predictions = []

    for index, item in enumerate(top3):
        rank = index + 1

        predictions.append({
            "rank": rank,
            "boat": item["boat"],
            "label": f"{rank}着候補",
            "confidence": min(item["score"], 95)
        })

    # 買い目候補を作る
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
        "notice": "このページは学習用のサンプルです。表示されている予想は仮のデータです。実際の的中や利益を保証するものではありません。"
    }

    return data


def main():
    data = make_prediction()

    output_path = Path("docs/prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("prediction.json を作成しました")
    print(output_path)


if __name__ == "__main__":
    main()

