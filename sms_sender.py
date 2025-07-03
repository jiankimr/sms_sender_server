"""sms_sender.py
SOLAPI 기반 SMS 발송 모듈
"""

from typing import List

from fastapi import HTTPException
from solapi.model import RequestMessage

from config import message_service, SENDER_PHONE
from crud import load_recipients

__all__ = ["send_sms", "broadcast"]


def send_sms(phone: str, body: str) -> dict:
    """단일 SMS 발송"""
    try:
        # SOLAPI 메시지 모델 생성
        message = RequestMessage(
            from_=SENDER_PHONE,  # 발신번호 (등록된 발신번호만 사용 가능)
            to=phone,  # 수신번호
            text=body,
        )
        
        # 메시지 발송
        response = message_service.send(message)
        
        return {
            "group_id": response.group_info.group_id,
            "total_count": response.group_info.count.total,
            "success_count": response.group_info.count.registered_success,
            "failed_count": response.group_info.count.registered_failed,
            "status": "success"
        }
    except Exception as e:
        # 발송 실패 시
        raise HTTPException(status_code=500, detail=f"SMS 발송 실패: {str(e)}")


def broadcast(body: str) -> List[dict]:
    """등록된 모든 수신자에게 메시지 발송"""
    recipients = load_recipients()
    if not recipients:
        raise HTTPException(status_code=400, detail="수신자 목록이 비어 있습니다.")
    
    results = []
    for phone in recipients:
        try:
            # 개별 발송 시 일부 실패가 전체를 중단시키지 않도록 예외 처리
            result = send_sms(phone, body)
            results.append({"phone": phone, **result})
        except HTTPException as exc:
            # 실패한 경우, 로그 대신 결과 리스트에 에러 정보 추가
            results.append({"phone": phone, "status": "failed", "detail": exc.detail})
    return results
