"""
🎯 Plugin Thử thách hàng ngày — gợi ý hoạt động học tập mỗi ngày khác nhau
Bé nói: "hôm nay học gì", "thử thách", "chơi gì đi"
"""
import random
from datetime import datetime, timezone, timedelta
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# Vietnamese time zone
VN_TZ = timezone(timedelta(hours=7))

# Daily challenges organized by day of week
DAILY_CHALLENGES = {
    0: {  # Monday
        "theme": "Toán học",
        "emoji": "🧮",
        "challenges": [
            "Giải 5 bài toán cộng trừ trong 100! Ai nhanh nhất nào? 🏃",
            "Thử thách bảng cửu chương! Mochi đố bạn nhỏ nhé! ✖️",
            "Toán đố vui: Mochi ra 3 bài toán có lời văn, bạn nhỏ giải nhé! 🐱",
        ],
    },
    1: {  # Tuesday
        "theme": "Tiếng Anh",
        "emoji": "🇬🇧",
        "challenges": [
            "Học 5 từ tiếng Anh về con vật! Cat, Dog, Bird... còn gì nữa nhỉ? 🐾",
            "Tập nói Hello, How are you? Mình roleplay nhé! 💬",
            "Học đếm từ 1 đến 20 bằng tiếng Anh! One, two, three... 🔢",
        ],
    },
    2: {  # Wednesday
        "theme": "Khoa học",
        "emoji": "🔬",
        "challenges": [
            "Hôm nay tìm hiểu: Tại sao trời mưa? 🌧️ Rất thú vị đó!",
            "Thử thách khoa học: Cầu vồng có mấy màu? Kể tên từng màu! 🌈",
            "Tìm hiểu về vũ trụ! Mặt trời to gấp bao nhiêu lần Trái đất nhỉ? 🌍",
        ],
    },
    3: {  # Thursday
        "theme": "Tiếng Việt",
        "emoji": "📝",
        "challenges": [
            "Luyện chính tả: Phân biệt s và x! Mochi đọc, bạn nhỏ trả lời! ✏️",
            "Học 3 thành ngữ hay! Mỗi thành ngữ có một bài học đặc biệt! 🎭",
            "Đọc hiểu: Mochi kể chuyện ngắn, bạn nhỏ trả lời câu hỏi nhé! 📖",
        ],
    },
    4: {  # Friday
        "theme": "Đố vui tổng hợp",
        "emoji": "🧩",
        "challenges": [
            "Ngày Thứ Sáu vui vẻ! 10 câu đố, mỗi câu đúng = 1 ngôi sao! ⭐",
            "Quiz kiến thức: Từ con vật đến địa lý, đố gì Mochi cũng ra! 🌟",
            "Trò chơi đoán từ: Mochi mô tả, bạn nhỏ đoán đó là cái gì! 🎲",
        ],
    },
    5: {  # Saturday
        "theme": "Khám phá thế giới",
        "emoji": "🌍",
        "challenges": [
            "Du lịch cuối tuần! Hôm nay mình bay đến Nhật Bản nhé! ✈️🇯🇵",
            "Khám phá ẩm thực! Mình tìm hiểu món ăn nổi tiếng thế giới! 🍕",
            "Tìm hiểu về động vật! Hôm nay học về loài nào nhỉ? 🐧",
        ],
    },
    6: {  # Sunday
        "theme": "Sáng tạo & Kể chuyện",
        "emoji": "📖",
        "challenges": [
            "Chủ nhật kể chuyện! Mochi bắt đầu, bạn nhỏ kể tiếp nhé! ✨",
            "Sáng tác chuyện! Bạn nhỏ nghĩ ra nhân vật, Mochi viết chuyện! 🎨",
            "Ngày thơ: Mochi đọc bài thơ hay, bạn nhỏ thử sáng tác nhé! 🌸",
        ],
    },
}

daily_challenge_function_desc = {
    "type": "function",
    "function": {
        "name": "daily_challenge",
        "description": (
            "Khi bé hỏi hôm nay học gì, chơi gì, có thử thách gì không, gợi ý hoạt động. "
            "Ví dụ: 'hôm nay học gì', 'có gì vui không', 'thử thách hôm nay', 'chơi gì đi', 'gợi ý đi'"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


@register_function("daily_challenge", daily_challenge_function_desc, ToolType.WAIT)
def daily_challenge():
    """Gợi ý thử thách học tập hàng ngày"""
    now = datetime.now(VN_TZ)
    weekday = now.weekday()
    day_info = DAILY_CHALLENGES[weekday]

    theme = day_info["theme"]
    emoji = day_info["emoji"]
    challenge = random.choice(day_info["challenges"])

    # Get Vietnamese day name
    vn_days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    day_name = vn_days[weekday]

    result = (
        f"🎯 Thử thách {day_name}!\n\n"
        f"{emoji} Chủ đề hôm nay: {theme}\n\n"
        f"{challenge}\n\n"
        f"Bạn nhỏ sẵn sàng chưa? Nói 'bắt đầu' là mình chơi luôn! 🚀"
    )

    logger.bind(tag=TAG).info(f"Daily challenge: {theme} - {day_name}")
    return ActionResponse(Action.RESPONSE, result, result)
