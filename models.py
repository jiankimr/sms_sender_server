"""models.py
Pydantic 데이터 모델 정의
"""

from ast import pattern
from pydantic import BaseModel, constr


class PhoneNumber(BaseModel):
    """E.164 포맷 (+82...) 10~15자리 전화번호 모델"""

    phone: constr(pattern=r"^\+?[0-9]{10,15}$")
