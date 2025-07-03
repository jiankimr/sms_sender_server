"""models.py
Pydantic 데이터 모델 정의
"""

import re
from pydantic import BaseModel, validator, Field


def normalize_phone_number(phone_number: str) -> str:
    """
    전화번호를 정규화합니다.
    - 하이픈(-), 공백, 괄호 등을 제거
    - 한국 전화번호 형식 처리 (010-xxxx-xxxx -> 01xxxxxxxx)
    
    Args:
        phone_number: 원본 전화번호 문자열
        
    Returns:
        정규화된 전화번호 (숫자만 포함)
    """
    if not phone_number:
        return ""
    
    # 하이픈, 공백, 괄호, 점 등 제거
    normalized = re.sub(r'[-\s\(\)\.]', '', phone_number.strip())
    
    # + 기호는 유지 (국제번호 형식)
    if normalized.startswith('+'):
        return normalized
    
    # 한국 전화번호 처리
    if normalized.startswith('010') and len(normalized) == 11:
        return normalized
    elif normalized.startswith('10') and len(normalized) == 10:
        # 10xxxxxxxx 형식을 010xxxxxxxx로 변환
        return '0' + normalized
        
    return normalized


class PhoneNumber(BaseModel):
    """전화번호 모델 (하이픈 포함/미포함 모두 지원)"""
    
    phone: str = Field(..., description="전화번호 (하이픈 포함/미포함 가능)")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v:
            raise ValueError("전화번호는 필수입니다.")
        
        # 전화번호 정규화
        normalized = normalize_phone_number(v)
        
        # 정규화된 번호 검증
        if not re.match(r'^\+?[0-9]{10,15}$', normalized):
            raise ValueError("유효하지 않은 전화번호 형식입니다.")
        
        return normalized


class MessageBody(BaseModel):
    """SMS 메시지 본문"""
    body: str = Field(..., min_length=1, max_length=2000, description="SMS 메시지 내용")
