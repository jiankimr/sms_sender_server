"""sms_sender.py
SNS Publish 및 Broadcast 기능 모듈
"""

from typing import List

from fastapi import HTTPException

from config import SENDER_ID, sns_client
from crud import load_recipients

__all__ = ["send_sms", "broadcast"]


def send_sms(phone: str, body: str) -> dict:
    """단일 SMS 발송"""
    try:
        response = sns_client.publish(
            PhoneNumber=phone,
            Message=body,
            MessageAttributes={
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": SENDER_ID,
                },
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                },
            },
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def broadcast(body: str) -> List[dict]:
    """등록된 모든 수신자에게 메시지 발송"""
    recipients = load_recipients()
    if not recipients:
        raise HTTPException(status_code=400, detail="수신자 목록이 비어 있습니다.")
    return [send_sms(phone, body) for phone in recipients]
