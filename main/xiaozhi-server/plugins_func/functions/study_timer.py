"""
📚 Plugin Pomodoro cho bé — quản lý thời gian học tập
"Mình học bài" → Mochi bắt đầu đếm giờ
"Mình xong rồi" → Mochi khen + tổng kết
"""
import time
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Store study sessions per connection
_study_sessions = {}

# ═══════════════════════════════════════
# 1. BẮT ĐẦU HỌC BÀI
# ═══════════════════════════════════════

start_study_function_desc = {
    "type": "function",
    "function": {
        "name": "start_study",
        "description": (
            "Khi bé muốn bắt đầu học bài, tập trung, làm bài tập. "
            "Ví dụ: 'mình học bài', 'bắt đầu học', 'tập trung', 'pomodoro', 'hẹn giờ học'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "minutes": {
                    "type": "integer",
                    "description": "Số phút muốn học (mặc định 15 phút cho bé). Tối đa 30 phút.",
                },
                "subject": {
                    "type": "string",
                    "description": "Môn học, ví dụ: toán, tiếng Việt, tiếng Anh. Mặc định: bài tập",
                },
            },
            "required": [],
        },
    },
}


@register_function("start_study", start_study_function_desc, ToolType.SYSTEM_CTL)
def start_study(conn: "ConnectionHandler", minutes: int = 15, subject: str = "bài tập"):
    """Bắt đầu phiên học tập"""
    # Cap at 30 minutes for kids
    minutes = min(max(minutes, 5), 30)

    session_id = id(conn)
    _study_sessions[session_id] = {
        "start_time": time.time(),
        "duration_minutes": minutes,
        "subject": subject,
        "completed": False,
    }

    logger.bind(tag=TAG).info(f"Bắt đầu phiên học {subject}: {minutes} phút")

    response = (
        f"OK bạn nhỏ! 📚 Mình học {subject} {minutes} phút nhé!\n\n"
        f"⏰ Bắt đầu nào! Tập trung học đi, Mochi chờ ở đây!\n"
        f"🎯 Khi nào xong thì nói 'mình xong rồi' nhé!\n\n"
        f"💪 Bạn nhỏ làm được mà! Cố lên!"
    )

    return ActionResponse(
        action=Action.RESPONSE,
        result="Đã bắt đầu phiên học",
        response=response,
    )


# ═══════════════════════════════════════
# 2. KẾT THÚC / KIỂM TRA PHIÊN HỌC
# ═══════════════════════════════════════

finish_study_function_desc = {
    "type": "function",
    "function": {
        "name": "finish_study",
        "description": (
            "Khi bé nói đã học xong, hoàn thành bài tập, muốn nghỉ. "
            "Ví dụ: 'xong rồi', 'mình xong rồi', 'học xong', 'hết giờ chưa', 'còn bao lâu'"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


@register_function("finish_study", finish_study_function_desc, ToolType.SYSTEM_CTL)
def finish_study(conn: "ConnectionHandler"):
    """Kết thúc phiên học tập và tổng kết"""
    session_id = id(conn)
    session = _study_sessions.get(session_id)

    if not session:
        return ActionResponse(
            action=Action.RESPONSE,
            result="Chưa có phiên học",
            response="Bạn nhỏ chưa bắt đầu học mà! 😄 Nói 'mình học bài' để bắt đầu nhé!",
        )

    elapsed = time.time() - session["start_time"]
    elapsed_minutes = int(elapsed / 60)
    target = session["duration_minutes"]
    subject = session["subject"]

    # Clean up session
    del _study_sessions[session_id]

    if elapsed_minutes >= target:
        # Completed full session!
        stars = "⭐" * min(elapsed_minutes // 5, 6)
        response = (
            f"🎉 GIỎI QUÁ! Bạn nhỏ đã học {subject} được {elapsed_minutes} phút!\n\n"
            f"Đạt mục tiêu {target} phút rồi! {stars}\n"
            f"🏅 Bạn nhỏ được 1 huy chương chăm chỉ!\n\n"
            f"Bây giờ nghỉ ngơi 5 phút nhé! Uống nước, vận động chút! 💧🏃‍♀️"
        )
    elif elapsed_minutes >= target * 0.7:
        # Almost completed
        response = (
            f"Tốt lắm! 😊 Bạn nhỏ đã học {subject} được {elapsed_minutes} phút!\n\n"
            f"Gần đạt mục tiêu {target} phút rồi! ⭐⭐\n"
            f"Lần sau cố thêm chút nữa nhé! 💪\n"
            f"Nghỉ ngơi uống nước đi nha! 💧"
        )
    elif elapsed_minutes >= 1:
        response = (
            f"Bạn nhỏ học {subject} được {elapsed_minutes} phút! ⭐\n\n"
            f"Lần sau mình thử học lâu hơn nhé — mục tiêu {target} phút! 🎯\n"
            f"Cố lên, Mochi tin bạn nhỏ làm được! 💪"
        )
    else:
        response = (
            f"Ơ, mới bắt đầu mà! 😄\n"
            f"Thử tập trung thêm chút nữa nhé bạn nhỏ!\n"
            f"Mình cùng học {subject} nào! 📚"
        )

    logger.bind(tag=TAG).info(f"Kết thúc phiên học {subject}: {elapsed_minutes}/{target} phút")
    return ActionResponse(action=Action.RESPONSE, result="Phiên học kết thúc", response=response)
