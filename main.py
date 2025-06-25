"""main.py
FastAPI 애플리케이션 엔트리포인트
"""

from fastapi import FastAPI, HTTPException
import uvicorn

from models import PhoneNumber
from crud import load_recipients, save_recipients
from sms_sender import send_sms, broadcast
from scheduler import start_scheduler

app = FastAPI(title="SMS Notification Server", version="1.0.0")


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


@app.post("/send/{phone}", summary="특정 수신자에게 SMS 전송")
def send_to_one(phone: str, body: str = "실험 알림입니다."):
    if phone not in load_recipients():
        raise HTTPException(status_code=404, detail="수신자 목록에 없는 번호입니다.")
    return send_sms(phone, body)


@app.post("/send/broadcast", summary="모든 수신자에게 브로드캐스트")
def broadcast_now(body: str = "실험 알림입니다. 오늘도 좋은 하루 되십시오."):
    return broadcast(body)

@app.get("/", summary="헬스체크")
def health():
    return {"status": "ok"}

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