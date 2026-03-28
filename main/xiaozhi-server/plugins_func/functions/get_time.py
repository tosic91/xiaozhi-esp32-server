"""
⏰ Plugin hỏi giờ cho bé - trả lời thời gian thân thiện + nhắc nhở phù hợp
"""
from datetime import datetime, timezone, timedelta
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

get_time_function_desc = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": (
            "Khi bé hỏi giờ, ngày, thứ mấy, hoặc bất kỳ câu hỏi về thời gian. "
            "Ví dụ: 'mấy giờ rồi', 'hôm nay thứ mấy', 'ngày bao nhiêu'"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def _get_vn_weekday(weekday: int) -> str:
    """Convert weekday number to Vietnamese"""
    days = {
        0: "Thứ Hai",
        1: "Thứ Ba",
        2: "Thứ Tư",
        3: "Thứ Năm",
        4: "Thứ Sáu",
        5: "Thứ Bảy",
        6: "Chủ Nhật",
    }
    return days.get(weekday, "")


def _get_time_period(hour: int) -> tuple[str, str]:
    """Get time period name and activity reminder for kids"""
    if 5 <= hour < 7:
        return "sáng sớm", "Dậy sớm giỏi quá! 🌅 Nhớ đánh răng rửa mặt nhé!"
    elif 7 <= hour < 11:
        return "buổi sáng", "Buổi sáng là lúc học tập tốt nhất đó! 📚"
    elif 11 <= hour < 13:
        return "trưa", "Sắp đến giờ ăn trưa rồi! 🍚 Ăn no rồi nghỉ ngơi nhé!"
    elif 13 <= hour < 14:
        return "đầu chiều", "Ngủ trưa một chút cho khỏe nha! 😴"
    elif 14 <= hour < 17:
        return "buổi chiều", "Chiều rồi! Làm bài tập xong rồi đi chơi nha! ⚽"
    elif 17 <= hour < 19:
        return "chiều tối", "Sắp tối rồi! Chơi vui nhé! 🌇"
    elif 19 <= hour < 20:
        return "tối", "Buổi tối rồi! Ăn cơm xong ôn bài nha! 🌙"
    elif 20 <= hour < 21:
        return "tối muộn", "Sắp đến giờ đi ngủ rồi! 🛏️ Chuẩn bị đi ngủ nha!"
    elif 21 <= hour < 23:
        return "khuya", "Trời ơi, khuya lắm rồi! 😲 Đi ngủ ngay nha bạn nhỏ! 💤"
    else:
        return "đêm khuya", "Muộn lắm rồi! Ngủ ngon nha bạn nhỏ! 🌟💤"


@register_function("get_time", get_time_function_desc, ToolType.WAIT)
def get_time():
    """Trả về thời gian thân thiện cho bé"""
    # Vietnam timezone (UTC+7)
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz)

    hour = now.hour
    minute = now.minute
    weekday = _get_vn_weekday(now.weekday())
    date_str = now.strftime("%d/%m/%Y")
    period_name, reminder = _get_time_period(hour)

    # Format time in kid-friendly way
    if minute == 0:
        time_str = f"{hour} giờ đúng"
    elif minute == 30:
        time_str = f"{hour} giờ rưỡi"
    elif minute < 10:
        time_str = f"{hour} giờ lẻ {minute} phút"
    else:
        time_str = f"{hour} giờ {minute} phút"

    result = (
        f"Bây giờ là {time_str} {period_name}! ⏰\n"
        f"Hôm nay là {weekday}, ngày {date_str}.\n"
        f"{reminder}"
    )

    logger.bind(tag=TAG).info(f"Trả lời giờ: {time_str}")
    return ActionResponse(Action.RESPONSE, result, result)
