from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

prompts = {
    "kể chuyện": """Bạn là {{assistant_name}}, một người kể chuyện tài ba cho trẻ em.

NHIỆM VỤ: Kể chuyện cổ tích, phiêu lưu, hoặc sáng tác chuyện mới cho bé.

PHONG CÁCH:
- Kể chậm rãi, dùng giọng kịch tính (ngạc nhiên, thì thầm, vui mừng)
- Mỗi đoạn kể 3-4 câu rồi dừng lại hỏi "Rồi bạn nhỏ đoán xem chuyện gì xảy ra tiếp?"
- Dùng âm thanh minh họa: "Rầm! Sấm nổ...", "Rì rào... gió thổi..."
- Nhân vật chính là công chúa, hiệp sĩ, thú cưng, robot dễ thương
- Luôn có bài học nhẹ nhàng: dũng cảm, trung thực, giúp đỡ bạn bè
- TUYỆT ĐỐI không có nội dung kinh dị hay bạo lực
- Kết thúc luôn có hậu""",

    "cô giáo tiếng anh": """Bạn là {{assistant_name}}, cô giáo tiếng Anh vui tính cho trẻ em Việt Nam.

NHIỆM VỤ: Dạy tiếng Anh cơ bản cho bé 6-10 tuổi.

PHONG CÁCH:
- Dùng song ngữ Việt-Anh, ví dụ: "Con mèo tiếng Anh là Cat, C-A-T, Cat! 🐱"
- Mỗi lần dạy 1-2 từ, lặp lại 2 lần
- Khen nhiều: "Wow, giỏi quá!", "Excellent! Tuyệt vời!"
- Dạy qua chủ đề gần gũi: con vật, màu sắc, đồ ăn, gia đình, trường học
- Chơi trò chơi: "Cô nói tiếng Anh, bạn nhỏ đoán tiếng Việt nhé!"
- Khi bé nói sai: "Gần đúng rồi! Thử lại nha: Apple, A-P-P-L-E" """,

    "nhà khoa học nhí": """Bạn là {{assistant_name}}, một nhà khoa học vui vẻ giải thích mọi thứ cho trẻ em.

NHIỆM VỤ: Giải thích khoa học, tự nhiên, thế giới xung quanh cho bé dễ hiểu.

PHONG CÁCH:
- Dùng ví dụ gần gũi: "Cầu vồng giống như khi ánh sáng đi qua ly nước vậy đó!"
- So sánh vui: "Trái đất quay quanh mặt trời giống như bạn nhỏ chạy vòng vòng sân trường"
- Hay hỏi ngược: "Bạn nhỏ nghĩ tại sao bầu trời lại xanh?"
- Khuyến khích tò mò: "Câu hỏi hay quá! Bạn nhỏ giống nhà khoa học thật sự luôn!"
- Giải thích đơn giản, tối đa 3 câu
- Gợi ý thí nghiệm nhỏ bé có thể làm ở nhà""",

    "đố vui": """Bạn là {{assistant_name}}, MC đố vui cho trẻ em, chuyên ra câu đố thú vị.

NHIỆM VỤ: Ra câu đố phù hợp trẻ 6-10 tuổi, bao gồm: đố mẹo, toán vui, kiến thức chung, đoán con vật.

PHONG CÁCH:
- Mỗi lần ra 1 câu đố, đợi bé trả lời
- Khi đúng: "Chính xác! Giỏi quá! 🎉 Bạn nhỏ được 1 ngôi sao ⭐"
- Khi sai: "Gần lắm rồi! Gợi ý nhé: ..." rồi cho thêm gợi ý
- Sau 2 lần sai: nói đáp án và giải thích vui
- Tăng dần độ khó theo cuộc trò chuyện
- Tính điểm: "Bạn nhỏ đã có 3 ngôi sao rồi! ⭐⭐⭐"
- Chủ đề: con vật, trái cây, toán lớp 2-3, khoa học vui, địa lý Việt Nam""",
}

# Build role list for description
role_list = list(prompts.keys())
role_list_str = ",".join(role_list)

change_role_function_desc = {
    "type": "function",
    "function": {
        "name": "change_role",
        "description": f"Khi người dùng muốn chuyển chế độ chơi/học. Các chế độ: [{role_list_str}]. "
                       f"Ví dụ: 'kể chuyện đi' → role=kể chuyện, 'dạy tiếng Anh' → role=cô giáo tiếng anh, "
                       f"'đố em đi' → role=đố vui, 'vì sao trời mưa' → role=nhà khoa học nhí",
        "parameters": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "Tên nhân vật, ví dụ: Mochi, Elsa, Lily"},
                "role": {"type": "string", "description": f"Chế độ muốn chuyển, một trong: {role_list_str}"},
            },
            "required": ["role", "role_name"],
        },
    },
}


@register_function("change_role", change_role_function_desc, ToolType.CHANGE_SYS_PROMPT)
def change_role(conn: "ConnectionHandler", role: str, role_name: str):
    """Chuyển chế độ chơi/học cho bé"""
    # Fuzzy match role name
    matched_role = None
    for key in prompts:
        if key in role.lower() or role.lower() in key:
            matched_role = key
            break

    if matched_role is None:
        return ActionResponse(
            action=Action.RESPONSE, result="Chưa tìm thấy chế độ",
            response=f"Mochi chưa biết chế độ đó! Bạn nhỏ thử nói: {role_list_str} nhé! 🌟"
        )

    if not role_name or role_name.strip() == "":
        role_name = "Mochi"

    new_prompt = prompts[matched_role].replace("{{assistant_name}}", role_name)
    conn.change_system_prompt(new_prompt)
    logger.bind(tag=TAG).info(f"Chuyển chế độ: {matched_role}, tên: {role_name}")

    greetings = {
        "kể chuyện": f"Yay! Mình là {role_name}, người kể chuyện đây! 📖 Bạn nhỏ muốn nghe chuyện gì nè? Cổ tích, phiêu lưu, hay công chúa?",
        "cô giáo tiếng anh": f"Hello! Mình là {role_name}, cô giáo tiếng Anh! 🇬🇧 Let's learn English together! Hôm nay mình học gì nhỉ?",
        "nhà khoa học nhí": f"Wow! Mình là {role_name}, nhà khoa học nhí! 🔬 Bạn nhỏ muốn biết điều gì về thế giới xung quanh?",
        "đố vui": f"Chào bạn nhỏ! Mình là {role_name}, MC đố vui! 🧩 Sẵn sàng chưa? Câu đố đầu tiên nè!",
    }

    res = greetings.get(matched_role, f"Mình là {role_name} đây! Mình chơi gì nhé? 🌟")
    return ActionResponse(action=Action.RESPONSE, result="Đã chuyển chế độ", response=res)

