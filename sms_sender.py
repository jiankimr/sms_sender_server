"""sms_sender.py
SOLAPI 기반 SMS 발송 모듈
"""

from typing import List, Optional

from fastapi import HTTPException
from solapi.model import RequestMessage

from config import message_service, SENDER_PHONE
from crud import load_recipients
from slack_logger import slack_logger

__all__ = ["send_sms", "broadcast"]


def send_sms(phone: str, body: str, user_info: Optional[str] = None) -> dict:
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
        
        result = {
            "group_id": response.group_info.group_id,
            "total_count": response.group_info.count.total,
            "success_count": response.group_info.count.registered_success,
            "failed_count": response.group_info.count.registered_failed,
            "status": "success"
        }
        
        # 성공 로그를 Slack으로 전송
        slack_logger.log_sms_success(phone, body, user_info)
        
        return result
    except Exception as e:
        error_msg = f"SMS 발송 실패: {str(e)}"
        
        # 실패 로그를 Slack으로 전송
        slack_logger.log_sms_failure(phone, body, str(e), user_info)
        
        # 발송 실패 시
        raise HTTPException(status_code=500, detail=error_msg)


def broadcast(body: str) -> List[dict]:
    """등록된 모든 수신자에게 메시지 발송"""
    recipients = load_recipients()
    if not recipients:
        raise HTTPException(status_code=400, detail="수신자 목록이 비어 있습니다.")
    
    results = []
    success_count = 0
    failed_count = 0
    
    for phone in recipients:
        try:
            # 개별 발송 시 일부 실패가 전체를 중단시키지 않도록 예외 처리
            result = send_sms(phone, body)
            results.append({"phone": phone, **result})
            success_count += 1
        except HTTPException as exc:
            # 실패한 경우, 로그 대신 결과 리스트에 에러 정보 추가
            results.append({"phone": phone, "status": "failed", "detail": exc.detail})
            failed_count += 1
    
    # 브로드캐스트 결과를 Slack으로 전송
    slack_logger.log_broadcast_result(len(recipients), success_count, failed_count)
    
    return results
