"""scheduler.py
APScheduler 기반 정기 브로드캐스트 관리
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import HTTPException

from config import TIMEZONE
from sms_sender import broadcast

__all__ = ["start_scheduler"]

BROADCAST_BODY = "실험 알림입니다. 설정하신 목표를 확인해 주세요."


def _scheduled_job():
    try:
        broadcast(BROADCAST_BODY)
    except HTTPException as exc:
        # 일정 실패 시 로그만 출력
        print(f"[Scheduler] {exc.detail}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(_scheduled_job, CronTrigger(hour=7, minute=0), name="morning_broadcast")
    scheduler.add_job(_scheduled_job, CronTrigger(hour=19, minute=0), name="evening_broadcast")
    scheduler.start()
