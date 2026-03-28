from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio
from core.utils.util import check_model_key


short_term_memory_prompt = """
# Trợ lý ghi nhớ cho trẻ em

## Nhiệm vụ
Phân tích lịch sử hội thoại và tóm tắt thông tin quan trọng về bé (user) để nhớ cho các cuộc trò chuyện sau.
Chỉ ghi nhận thông tin từ hội thoại thực, KHÔNG bịa ra thông tin.

## Quy tắc ghi nhớ
### 1. Ưu tiên ghi nhớ
- Tên, tuổi, lớp, trường học của bé
- Sở thích (con vật yêu thích, trò chơi, màu sắc...)
- Thành tích học tập (giải bao nhiêu bài toán, học từ tiếng Anh nào...)
- Cảm xúc đặc biệt (vui/buồn/lo/giận + nguyên nhân)
- Gia đình (tên ba mẹ, anh chị em, thú cưng...)
- Chế độ yêu thích (kể chuyện, đố vui, toán...)

### 2. Cập nhật
- Khi bé nói "tên con là X" → cập nhật tên
- Khi bé thay đổi sở thích → cập nhật, giữ sở thích cũ
- Gộp thông tin trùng lặp, ưu tiên thông tin mới nhất

### 3. Tối ưu dung lượng
- Dùng ký hiệu ngắn gọn: ✅ "Mai[8t/lớp3/thích mèo/giỏi toán]"
- Khi tổng ≥800 ký tự → xóa thông tin cũ ít quan trọng

## Cấu trúc ghi nhớ
Xuất ra dạng JSON, không giải thích:
```json
{
  "hồ_sơ_bé": {
    "tên": "",
    "tuổi": "",
    "lớp": "",
    "đặc_điểm": []
  },
  "sở_thích": {
    "yêu_thích": [],
    "chế_độ_hay_chơi": [],
    "con_vật_yêu_thích": ""
  },
  "học_tập": {
    "thành_tích": [],
    "từ_tiếng_anh_đã_học": [],
    "môn_giỏi": "",
    "cần_luyện": ""
  },
  "cảm_xúc": [
    {
      "ngày": "2024-03-20",
      "cảm_xúc": "vui",
      "lý_do": "được điểm 10"
    }
  ],
  "gia_đình": {
    "ba_mẹ": "",
    "anh_chị_em": "",
    "thú_cưng": ""
  },
  "kỷ_niệm_vui": [
    "Câu nói đáng nhớ của bé"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    # 从start开始找到下一个```结束
    end = json_code.find("```", start + 1)
    # print("start:", start, "end:", end)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        # api获取到总结记忆后直接返回
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        # 打印使用的模型信息
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"使用记忆保存模型: {model_info}")
        api_key = getattr(self.llm, "api_key", None)
        memory_key_msg = check_model_key("记忆总结专用LLM", api_key)
        if memory_key_msg:
            logger.bind(tag=TAG).error(memory_key_msg)
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM is not set for memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        content = data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "历史记忆：\n"
            msgStr += self.short_memory

        # 当前时间
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"当前时间：{time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)  # 检查json格式是否正确
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            # 当save_to_file为False时，调用Java端的聊天记录总结接口
            summary_id = session_id if session_id else self.role_id
            await generate_and_save_chat_summary(summary_id)
        logger.bind(tag=TAG).info(
            f"Save memory successful - Role: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
