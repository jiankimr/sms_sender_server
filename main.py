"""main.py
FastAPI 애플리케이션 엔트리포인트
"""

from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel

from models import PhoneNumber
from crud import load_recipients, save_recipients
from sms_sender import send_sms, broadcast
from scheduler import start_scheduler
from firestore_client import get_collection_data, get_user_data, get_user_data_by_field, get_user_daily_usage

app = FastAPI(title="SMS Notification Server", version="1.0.0")


# --- Pydantic 모델 ---
class MessageBody(BaseModel):
    body: str


# -------------------------
# REST 엔드포인트
# -------------------------

@app.post("/recipients", summary="수신자 전화번호 등록", status_code=201)
def add_recipient(item: PhoneNumber):
    recipients = load_recipients()
    if item.phone in recipients:
        raise HTTPException(status_code=409, detail="이미 등록된 번호입니다.")
    recipients.append(item.phone)
    save_recipients(recipients)
    return {"count": len(recipients), "phone": item.phone}


@app.get("/recipients", summary="등록된 수신자 목록 조회")
def list_recipients():
    return load_recipients()


@app.post("/send/broadcast", summary="모든 수신자에게 브로드캐스트")
def broadcast_now(payload: MessageBody):
    return broadcast(payload.body)


@app.post("/send/{phone}", summary="특정 수신자에게 SMS 전송")
def send_to_one(phone: str, payload: MessageBody):
    if phone not in load_recipients():
        raise HTTPException(status_code=404, detail="수신자 목록에 없는 번호입니다.")
    return send_sms(phone, payload.body)


@app.get("/", summary="헬스체크")
def health():
    return {"status": "ok"}


@app.get("/firestore/{collection_name}", summary="Firestore 컬렉션 데이터 조회")
def read_collection(collection_name: str):
    """
    지정한 Firestore 컬렉션의 모든 문서를 조회합니다.
    """
    try:
        data = get_collection_data(collection_name)
        return data
    except Exception as e:
        # 구체적인 에러 처리가 필요할 수 있습니다.
        raise HTTPException(status_code=500, detail=f"Firestore 데이터 조회 중 오류 발생: {str(e)}")


@app.get("/firestore/{collection_name}/user/{user_id}", summary="특정 사용자의 Firestore 데이터 조회")
def read_user_data(collection_name: str, user_id: str):
    """
    지정한 Firestore 컬렉션에서 특정 사용자의 데이터만 조회합니다.
    user_id 필드로 필터링합니다.
    """
    try:
        data = get_user_data(collection_name, user_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 데이터 조회 중 오류 발생: {str(e)}")


@app.get("/firestore/{collection_name}/filter", summary="필드 값으로 Firestore 데이터 필터링 조회")
def read_filtered_data(collection_name: str, field_name: str, field_value: str):
    """
    지정한 Firestore 컬렉션에서 특정 필드 값으로 필터링하여 데이터를 조회합니다.
    쿼리 파라미터: field_name, field_value
    예: /firestore/users/filter?field_name=email&field_value=user@example.com
    """
    try:
        data = get_user_data_by_field(collection_name, field_name, field_value)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필터링된 데이터 조회 중 오류 발생: {str(e)}")


@app.get("/firestore/user/{user_id}/usage", summary="사용자 일일 사용 시간 조회")
def get_daily_usage(user_id: str, start_date: str, end_date: str):
    """
    특정 사용자의 지정된 날짜 범위 내 총 사용 시간을 계산합니다.
    모든 세션(task)의 start_time과 end_time을 합산하여 계산합니다.
    
    Parameters:
    - user_id: 사용자 ID (sanitized_user_id)
    - start_date: 시작 날짜 (YYYY-MM-DD 형식, 쿼리 파라미터)
    - end_date: 종료 날짜 (YYYY-MM-DD 형식, 쿼리 파라미터)
    
    Example:
    GET /firestore/user/user123/usage?start_date=2024-01-01&end_date=2024-01-01
    """
    try:
        # 날짜 형식 검증
        from datetime import datetime
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
        
        data = get_user_daily_usage(user_id, start_date, end_date)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용 시간 조회 중 오류 발생: {str(e)}")


@app.post("/test/morning-notification", summary="오전 사용량 알림 테스트")
def test_morning_notification():
    """
    오전 7시 스케줄러 기능을 수동으로 테스트합니다.
    전날 사용량 종합 통계를 모든 수신자에게 전송합니다.
    """
    try:
        from scheduler import _morning_usage_notification
        _morning_usage_notification()
        return {"status": "success", "message": "오전 사용량 알림이 전송되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오전 알림 테스트 중 오류 발생: {str(e)}")


@app.post("/test/evening-notification", summary="오후 사용량 알림 테스트")
def test_evening_notification():
    """
    오후 7시 스케줄러 기능을 수동으로 테스트합니다.
    당일 사용량 종합 통계를 모든 수신자에게 전송합니다.
    """
    try:
        from scheduler import _evening_usage_notification
        _evening_usage_notification()
        return {"status": "success", "message": "오후 사용량 알림이 전송되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오후 알림 테스트 중 오류 발생: {str(e)}")


# -------------------------
# 애플리케이션 시작 시 스케줄러 실행
# -------------------------

@app.on_event("startup")
def on_startup():
    start_scheduler()


# -------------------------
# 개발용 실행 스크립트
# -------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)