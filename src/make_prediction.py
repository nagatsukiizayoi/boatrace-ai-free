import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


RACE_PATH = Path("docs/race.json")
RACE_UPDATE_PATH = Path("docs/race_update.json")

# 常にトップページが読む最新予想
OUTPUT_PATH = Path("docs/prediction.json")

# 予想実行履歴
PREDICTION_RUNS_PATH = Path("docs/prediction_runs.json")


STAGE_FILE_MAP = {
    "PRE_NIGHT": Path("docs/prediction_pre_night.json"),
    "MORNING": Path("docs/prediction_morning.json"),
    "PRE_EXHIBITION": Path("docs/prediction_pre_exhibition.json"),
    "POST_EXHIBITION": Path("docs/prediction_post_exhibition.json"),
    "FINAL": Path("docs/prediction_final.json")
}


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


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def normalize_stage(stage):
    stage = str(stage or "PRE_NIGHT").upper()

    allowed = {
        "PRE_NIGHT",
        "MORNING",
        "PRE_EXHIBITION",
        "POST_EXHIBITION",
        "FINAL"
    }

    if stage not in allowed:
        return "PRE_NIGHT"

    return stage


def stage_usage(stage):
    """
    ステージごとに、どの情報を使うか決める。

    重要：
    PRE_NIGHT では当日情報を使わない。
    これにより、前日予想に未来情報が混ざることを防ぐ。
    """

    stage = normalize_stage(stage)

    if stage == "PRE_NIGHT":
        return {
            "use_weather": False,
            "use_exhibition": False,
            "use_odds": False
        }

    if stage == "MORNING":
        return {
            "use_weather": True,
            "use_exhibition": False,
            "use_odds": False
        }

    if stage == "PRE_EXHIBITION":
        return {
            "use_weather": True,
            "use_exhibition": False,
            "use_odds": True
        }

    if stage == "POST_EXHIBITION":
        return {
            "use_weather": True,
            "use_exhibition": True,
            "use_odds": True
        }

    if stage == "FINAL":
        return {
            "use_weather": True,
            "use_exhibition": True,
            "use_odds": True
        }

    return {
        "use_weather": False,
        "use_exhibition": False,
        "use_odds": False
    }


def default_race_data():
    today = now_jst().strftime("%Y-%m-%d")

    return {
        "race": {
            "date": today,
            "place": "サンプル競艇場",
            "race_no": "12R",
            "title": "サンプルレース",
            "deadline": "16:30"
        },
        "boats": [
            {
                "boat": 1,
                "course": 1,
                "driver": "山田 太郎",
                "win_rate": 7.20,
                "motor_rate": 45.0,
                "avg_st": 0.13
            },
            {
                "boat": 2,
                "course": 2,
                "driver": "佐藤 次郎",
                "win_rate": 6.10,
                "motor_rate": 38.0,
                "avg_st": 0.15
            },
            {
                "boat": 3,
                "course": 3,
                "driver": "鈴木 三郎",
                "win_rate": 6.60,
                "motor_rate": 41.5,
                "avg_st": 0.14
            },
            {
                "boat": 4,
                "course": 4,
                "driver": "田中 四郎",
                "win_rate": 5.80,
                "motor_rate": 35.0,
                "avg_st": 0.16
            },
            {
                "boat": 5,
                "course": 5,
                "driver": "高橋 五郎",
                "win_rate": 5.20,
                "motor_rate": 33.0,
                "avg_st": 0.17
            },
            {
                "boat": 6,
                "course": 6,
                "driver": "伊藤 六郎",
                "win_rate": 4.90,
                "motor_rate": 29.0,
                "avg_st": 0.18
            }
        ]
    }


def load_race_data():
    data = load_json(RACE_PATH)

    if not data:
        data = default_race_data()

    race = data.get("race", {})
    boats = data.get("boats", [])

    if not boats:
        data = default_race_data()
        race = data.get("race", {})
        boats = data.get("boats", [])

    return race, boats


def load_update_data():
    update = load_json(RACE_UPDATE_PATH, default={})

    stage = normalize_stage(update.get("stage", "PRE_NIGHT"))
    weather = update.get("weather", {})
    update_boats = update.get("boats", [])

    update_by_boat = {}

    for item in update_boats:
        boat_no = to_int(item.get("boat"), 0)

        if boat_no:
            update_by_boat[boat_no] = item

    return {
        "stage": stage,
        "weather": weather,
        "boats": update_by_boat,
        "raw": update
    }


def course_bonus(course):
    course = to_int(course, 6)

    bonus_map = {
        1: 18,
        2: 12,
        3: 8,
        4: 5,
        5: 2,
        6: 0
    }

    return bonus_map.get(course, 0)


def mark_for_rank(rank):
    if rank == 1:
        return "◎", "本命"
    elif rank == 2:
        return "○", "対抗"
    elif rank == 3:
        return "▲", "単穴"
    elif rank == 4:
        return "△", "連下"
    elif rank == 5:
        return "☆", "穴"
    else:
        return "×", "押さえ"


def calculate_base_score(boat):
    win_rate = to_float(boat.get("win_rate"), 0)
    motor_rate = to_float(boat.get("motor_rate"), 0)
    avg_st = to_float(boat.get("avg_st"), 0.18)
    course = to_int(
        boat.get("course", boat.get("boat")),
        to_int(boat.get("boat"), 6)
    )

    win_score = win_rate * 12
    motor_score = motor_rate * 0.7
    st_score = max(0, (0.22 - avg_st) * 140)
    course_score = course_bonus(course)

    return win_score + motor_score + st_score + course_score


def rank_values_by_small_is_good(items, key):
    valid = []

    for item in items:
        value = item.get(key)

        if value is None or value == "":
            continue

        valid.append({
            "boat": item["boat"],
            "value": to_float(value)
        })

    valid.sort(key=lambda x: x["value"])

    ranks = {}

    for index, item in enumerate(valid, start=1):
        ranks[item["boat"]] = index

    return ranks


def exhibition_rank_bonus(rank):
    bonus_map = {
        1: 10,
        2: 7,
        3: 4,
        4: 2,
        5: 0,
        6: -2
    }

    return bonus_map.get(rank, 0)


def st_rank_bonus(rank):
    bonus_map = {
        1: 7,
        2: 5,
        3: 3,
        4: 1,
        5: 0,
        6: -2
    }

    return bonus_map.get(rank, 0)


def tilt_bonus(tilt):
    tilt = to_float(tilt, 0)

    if tilt >= 0.5:
        return 1.5
    elif tilt <= -0.5:
        return 0.5
    else:
        return 1.0


def odds_bonus(win_odds):
    odds = to_float(win_odds, 0)

    if odds <= 0:
        return 0

    if odds <= 2:
        return 6
    elif odds <= 4:
        return 4
    elif odds <= 8:
        return 2
    elif odds <= 15:
        return 0
    else:
        return -1


def weather_adjustment(weather, boat):
    wind_speed = to_float(weather.get("wind_speed"), 0)
    wave_height = to_float(weather.get("wave_height"), 0)
    wind_direction = str(weather.get("wind_direction", ""))

    course = to_int(
        boat.get("course", boat.get("boat")),
        to_int(boat.get("boat"), 6)
    )

    avg_st = to_float(boat.get("avg_st"), 0.18)

    adjustment = 0

    if wind_speed >= 5:
        if course >= 5:
            adjustment -= 2
        if avg_st >= 0.18:
            adjustment -= 1

    if wave_height >= 5:
        if course >= 5:
            adjustment -= 2
        if avg_st >= 0.18:
            adjustment -= 1

    if "追" in wind_direction:
        if avg_st <= 0.15:
            adjustment += 2

    if "向" in wind_direction:
        if course <= 2:
            adjustment += 1.5

    return adjustment


def normalize_confidence(score, min_score, max_score):
    if max_score == min_score:
        return 70

    value = 50 + ((score - min_score) / (max_score - min_score)) * 45
    return int(round(max(50, min(95, value))))


def build_boats(race_boats, update_data):
    stage = update_data.get("stage", "PRE_NIGHT")
    usage = stage_usage(stage)

    weather = update_data.get("weather", {}) if usage["use_weather"] else {}
    update_by_boat = update_data.get("boats", {})

    merged_boats = []

    for boat in race_boats:
        boat_no = to_int(boat.get("boat"), 0)
        update = update_by_boat.get(boat_no, {})

        item = {
            "boat": boat_no,
            "course": to_int(boat.get("course", boat_no), boat_no),
            "driver": boat.get("driver", f"{boat_no}号艇"),
            "win_rate": to_float(boat.get("win_rate"), 0),
            "motor_rate": to_float(boat.get("motor_rate"), 0),
            "avg_st": to_float(boat.get("avg_st"), 0.18),

            # 以下はステージによって使う・使わないを分ける
            "exhibition_time": update.get("exhibition_time") if usage["use_exhibition"] else None,
            "exhibition_st": update.get("exhibition_st") if usage["use_exhibition"] else None,
            "tilt": update.get("tilt") if usage["use_exhibition"] else None,
            "win_odds": update.get("win_odds") if usage["use_odds"] else None
        }

        merged_boats.append(item)

    exhibition_time_ranks = rank_values_by_small_is_good(merged_boats, "exhibition_time")
    exhibition_st_ranks = rank_values_by_small_is_good(merged_boats, "exhibition_st")

    scored_boats = []

    for boat in merged_boats:
        boat_no = boat["boat"]

        base_score = calculate_base_score(boat)

        weather_score = 0
        if usage["use_weather"]:
            weather_score = weather_adjustment(weather, boat)

        exhibition_time_rank = exhibition_time_ranks.get(boat_no)
        exhibition_st_rank = exhibition_st_ranks.get(boat_no)

        exhibition_score = 0

        if usage["use_exhibition"]:
            if exhibition_time_rank:
                exhibition_score += exhibition_rank_bonus(exhibition_time_rank)

            if exhibition_st_rank:
                exhibition_score += st_rank_bonus(exhibition_st_rank)

            if boat.get("tilt") is not None:
                exhibition_score += tilt_bonus(boat.get("tilt"))

        odds_score = 0

        if usage["use_odds"]:
            odds_score = odds_bonus(boat.get("win_odds"))

        total_score = base_score + weather_score + exhibition_score + odds_score

        boat["base_score"] = round(base_score, 2)
        boat["weather_score"] = round(weather_score, 2)
        boat["exhibition_score"] = round(exhibition_score, 2)
        boat["odds_score"] = round(odds_score, 2)
        boat["score"] = round(total_score, 2)
        boat["exhibition_time_rank"] = exhibition_time_rank
        boat["exhibition_st_rank"] = exhibition_st_rank

        scored_boats.append(boat)

    scored_boats.sort(key=lambda x: x["score"], reverse=True)

    scores = [b["score"] for b in scored_boats]
    min_score = min(scores)
    max_score = max(scores)

    for index, boat in enumerate(scored_boats, start=1):
        mark, mark_name = mark_for_rank(index)

        boat["rank"] = index
        boat["mark"] = mark
        boat["mark_name"] = mark_name
        boat["confidence"] = normalize_confidence(boat["score"], min_score, max_score)

    return scored_boats


def make_ticket_groups(boats):
    if len(boats) < 3:
        return []

    top1 = boats[0]
    top2 = boats[1]
    top3 = boats[2]

    top4 = boats[3] if len(boats) >= 4 else boats[2]
    top5 = boats[4] if len(boats) >= 5 else boats[2]

    b1 = top1["boat"]
    b2 = top2["boat"]
    b3 = top3["boat"]
    b4 = top4["boat"]
    b5 = top5["boat"]

    ticket_groups = [
        {
            "name": "本線",
            "description": "◎本命を1着に固定した中心買い目です。",
            "risk": "低リスク",
            "tickets": [
                {
                    "ticket": f"{b1}-{b2}-{b3}",
                    "amount": 300,
                    "reason": "◎→○→▲ の基本形"
                },
                {
                    "ticket": f"{b1}-{b3}-{b2}",
                    "amount": 300,
                    "reason": "◎→▲→○ の入れ替わり"
                }
            ]
        },
        {
            "name": "押さえ",
            "description": "○や▲が上位に来る場合を押さえます。",
            "risk": "中リスク",
            "tickets": [
                {
                    "ticket": f"{b2}-{b1}-{b3}",
                    "amount": 200,
                    "reason": "○が◎を逆転する形"
                },
                {
                    "ticket": f"{b1}-{b2}-{b4}",
                    "amount": 200,
                    "reason": "3着に△が入る形"
                },
                {
                    "ticket": f"{b1}-{b4}-{b2}",
                    "amount": 100,
                    "reason": "2着に△が浮上する形"
                }
            ]
        },
        {
            "name": "穴狙い",
            "description": "△や☆が絡む高配当狙いです。",
            "risk": "高リスク",
            "tickets": [
                {
                    "ticket": f"{b3}-{b1}-{b2}",
                    "amount": 100,
                    "reason": "▲が1着に来る波乱"
                },
                {
                    "ticket": f"{b1}-{b3}-{b4}",
                    "amount": 100,
                    "reason": "3着に△が絡む形"
                },
                {
                    "ticket": f"{b1}-{b2}-{b5}",
                    "amount": 100,
                    "reason": "3着に☆が絡む形"
                }
            ]
        }
    ]

    return ticket_groups


def calculate_total_amount(ticket_groups):
    total = 0

    for group in ticket_groups:
        for ticket in group.get("tickets", []):
            total += to_int(ticket.get("amount"), 0)

    return total


def flatten_tickets(ticket_groups):
    tickets = []

    for group in ticket_groups:
        for ticket in group.get("tickets", []):
            tickets.append(ticket.get("ticket"))

    return tickets


def estimate_ticket_probability(ticket, boats):
    boat_map = {b["boat"]: b for b in boats}

    try:
        parts = [to_int(x) for x in str(ticket).split("-")]
    except Exception:
        return 0

    if len(parts) != 3:
        return 0

    score_sum = sum(max(1, b["score"]) for b in boats)
    prob = 1.0
    remaining_sum = score_sum

    for boat_no in parts:
        b = boat_map.get(boat_no)

        if not b:
            return 0

        score = max(1, b["score"])
        prob *= score / remaining_sum
        remaining_sum -= score

        if remaining_sum <= 0:
            break

    return round(prob, 5)


def add_ticket_probabilities(ticket_groups, boats):
    for group in ticket_groups:
        for ticket in group.get("tickets", []):
            ticket_text = ticket.get("ticket")
            ticket["probability"] = estimate_ticket_probability(ticket_text, boats)

    return ticket_groups


def make_race_id(race):
    date = race.get("date", "")
    place = race.get("place") or race.get("stadium") or race.get("venue") or ""
    race_no = race.get("race_no", "")

    return f"{date}_{place}_{race_no}"


def stage_file_path(stage):
    stage = normalize_stage(stage)
    return STAGE_FILE_MAP.get(stage, Path("docs/prediction_pre_night.json"))


def build_prediction_json():
    current_time = now_jst()

    race, race_boats = load_race_data()
    update_data = load_update_data()

    stage = normalize_stage(update_data.get("stage", "PRE_NIGHT"))
    usage = stage_usage(stage)

    boats = build_boats(race_boats, update_data)

    predictions = []

    for boat in boats[:3]:
        predictions.append({
            "rank": boat["rank"],
            "mark": boat["mark"],
            "mark_name": boat["mark_name"],
            "boat": boat["boat"],
            "course": boat["course"],
            "driver": boat["driver"],
            "label": f"{boat['rank']}着候補",
            "confidence": boat["confidence"],
            "score": boat["score"],
            "base_score": boat["base_score"],
            "weather_score": boat["weather_score"],
            "exhibition_score": boat["exhibition_score"],
            "odds_score": boat["odds_score"]
        })

    ticket_groups = make_ticket_groups(boats)
    ticket_groups = add_ticket_probabilities(ticket_groups, boats)

    normalized_race = {
        "date": race.get("date", current_time.strftime("%Y-%m-%d")),
        "place": race.get("place") or race.get("stadium") or race.get("venue") or "未設定",
        "stadium": race.get("stadium") or race.get("place") or race.get("venue") or "未設定",
        "race_no": race.get("race_no", "未設定"),
        "title": race.get("title", ""),
        "deadline": race.get("deadline", "")
    }

    data = {
        "prediction_run_id": current_time.strftime("%Y%m%d%H%M%S"),
        "updated_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "stage": stage,
        "stage_usage": usage,
        "race_id": make_race_id(normalized_race),
        "race": normalized_race,
        "weather": update_data.get("weather", {}) if usage["use_weather"] else {},
        "predictions": predictions,
        "all_boats": boats,
        "ticket_groups": ticket_groups,
        "tickets": flatten_tickets(ticket_groups),
        "total_amount": calculate_total_amount(ticket_groups),
        "source": {
            "race_file": str(RACE_PATH),
            "update_file": str(RACE_UPDATE_PATH),
            "update_file_exists": RACE_UPDATE_PATH.exists(),
            "stage_file": str(stage_file_path(stage))
        },
        "notice": "このページは学習用・分析練習用です。実際の購入や利益を保証するものではありません。"
    }

    return data


def make_run_summary(prediction_data, stage_specific_path):
    predictions = prediction_data.get("predictions", [])
    tickets = prediction_data.get("tickets", [])

    top_boats = []

    for item in predictions:
        top_boats.append({
            "rank": item.get("rank"),
            "mark": item.get("mark"),
            "boat": item.get("boat"),
            "driver": item.get("driver"),
            "score": item.get("score")
        })

    return {
        "prediction_run_id": prediction_data.get("prediction_run_id"),
        "updated_at": prediction_data.get("updated_at"),
        "stage": prediction_data.get("stage"),
        "race_id": prediction_data.get("race_id"),
        "race": prediction_data.get("race", {}),
        "stage_file": str(stage_specific_path),
        "top_boats": top_boats,
        "tickets": tickets,
        "total_amount": prediction_data.get("total_amount", 0)
    }


def update_prediction_runs(prediction_data, stage_specific_path):
    runs_data = load_json(PREDICTION_RUNS_PATH, default={
        "updated_at": "",
        "runs": []
    })

    runs = runs_data.get("runs", [])
    runs.append(make_run_summary(prediction_data, stage_specific_path))

    # 多くなりすぎないよう、最新100件だけ残す
    runs = runs[-100:]

    runs_data["updated_at"] = now_jst().strftime("%Y-%m-%d %H:%M:%S")
    runs_data["runs"] = runs

    save_json(PREDICTION_RUNS_PATH, runs_data)


def save_prediction_outputs(prediction_data):
    stage = normalize_stage(prediction_data.get("stage", "PRE_NIGHT"))
    stage_path = stage_file_path(stage)

    # 1. 現在表示用を保存
    save_json(OUTPUT_PATH, prediction_data)

    # 2. ステージ別にも保存
    save_json(stage_path, prediction_data)

    # 3. 実行履歴を保存
    update_prediction_runs(prediction_data, stage_path)

    return stage_path


def main():
    data = build_prediction_json()
    stage_path = save_prediction_outputs(data)

    print("prediction.json を作成しました。")
    print(f"stage: {data.get('stage')}")
    print(f"latest output: {OUTPUT_PATH}")
    print(f"stage output: {stage_path}")
    print(f"runs output: {PREDICTION_RUNS_PATH}")


if __name__ == "__main__":
    main()

