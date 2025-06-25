"""sms_sender.py
Pinpoint SMS and Voice v2 API 기반 SMS 발송 모듈
"""

from typing import List

from botocore.exceptions import ClientError
from fastapi import HTTPException

from config import sms_voice_client, TOLL_FREE_NUMBER
from crud import load_recipients

__all__ = ["send_sms", "broadcast"]


def send_sms(phone: str, body: str) -> dict:
    """단일 SMS 발송"""
    try:
        response = sms_voice_client.send_text_message(
            DestinationPhoneNumber=phone,
            OriginationIdentity=TOLL_FREE_NUMBER,
            MessageBody=body,
            MessageType="TRANSACTIONAL",
        )
        return response
    except ClientError as e:
        # Boto3 클라이언트 오류 (e.g., 잘못된 파라미터, 권한 없음)
        error_code = e.response.get("Error", {}).get("Code")
        error_message = e.response.get("Error", {}).get("Message")
        raise HTTPException(
            status_code=500, detail=f"AWS API Error: {error_code} - {error_message}"
        )
    except Exception as e:
        # 기타 서버 오류
        raise HTTPException(status_code=500, detail=str(e))


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
            results.append(result)
        except HTTPException as exc:
            # 실패한 경우, 로그 대신 결과 리스트에 에러 정보 추가
            results.append({"phone": phone, "status": "failed", "detail": exc.detail})
    return results
