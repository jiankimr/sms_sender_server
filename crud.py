"""crud.py
수신자(전화번호) 로컬 저장/로드 헬퍼
"""

import json
from typing import List

from config import RECIPIENT_FILE


def load_recipients() -> List[str]:
    if not RECIPIENT_FILE.exists():
        return []
    with open(RECIPIENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recipients(recipients: List[str]):
    with open(RECIPIENT_FILE, "w", encoding="utf-8") as f:
        json.dump(recipients, f, ensure_ascii=False, indent=2)
