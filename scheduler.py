"""scheduler.py
APScheduler 기반 정기 브로드캐스트 관리
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import HTTPException

from config import TIMEZONE
from sms_sender import broadcast, send_sms
from firestore_client import get_all_users, get_user_daily_usage, get_all_users_with_info, format_duration_korean, get_users_with_phone
from crud import load_recipients

__all__ = ["start_scheduler"]

BROADCAST_BODY = "실험 알림입니다. 설정하신 목표를 확인해 주세요."


def _scheduled_job():
    """기존 브로드캐스트 (백업용으로 유지)"""
    try:
        broadcast(BROADCAST_BODY)
    except HTTPException as exc:
        # 일정 실패 시 로그만 출력
        print(f"[Scheduler] {exc.detail}")


def _morning_usage_notification():
    """오전 7시: 전날 사용량 알림 (개별 사용자별)"""
    try:
        # 전날 날짜 계산 (KST 기준)
        yesterday = (datetime.now(TIMEZONE) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 전화번호가 있는 사용자들만 조회
        users_with_phone = get_users_with_phone()
        
        if not users_with_phone:
            print("[Morning Scheduler] 전화번호가 있는 사용자가 없습니다.")
            return
        
        success_count = 0
        total_count = len(users_with_phone)
        
        for user_data in users_with_phone:
            try:
                user_id = user_data.get('user_id')
                username = user_data.get('name', user_data.get('user_id', '사용자'))
                phone = user_data.get('phone', '').strip()
                
                if not phone:
                    print(f"[Morning Scheduler] {username}님의 전화번호가 없습니다.")
                    continue
                
                # intention_app_user 컬렉션에서 각 사용자의 전날 사용량 조회
                usage_data = get_user_daily_usage(user_id, yesterday, yesterday)
                
                session_count = usage_data['session_count']
                formatted_time = usage_data['total_usage']['formatted']
                
                # 개인화된 메시지 생성
                if session_count > 0:
                    message = f"{username}님, 어제 {formatted_time} 동안 사용하셨군요! 오늘도 열심히 사용해주세요! 💪"#{session_count}회 
                else:
                    message = f"{username}님, 어제는 앱을 사용하지 않으셨네요. 오늘은 열심히 사용해주세요! 📱"
                
                # 해당 사용자의 전화번호로 개인화된 메시지 전송
                try:
                    send_sms(phone, message)
                    success_count += 1
                    print(f"[Morning Scheduler] {username}님({user_id}) 전날 사용량 알림 전송 완료: {phone}")
                except Exception as e:
                    print(f"[Morning Scheduler] SMS 전송 실패 ({phone}, {username}): {e}")
                
            except Exception as e:
                print(f"[Morning Scheduler] User {user_id} 사용량 조회 실패: {e}")
        
        print(f"[Morning Scheduler] 전날 개별 사용량 알림 완료: {success_count}/{total_count}명 전송 성공")
        
    except Exception as e:
        print(f"[Morning Scheduler] 오류 발생: {e}")


def _evening_usage_notification():
    """오후 7시: 당일 사용량 알림 (개별 사용자별)"""
    try:
        # 오늘 날짜 계산 (KST 기준)
        today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        
        # 전화번호가 있는 사용자들만 조회
        users_with_phone = get_users_with_phone()
        
        if not users_with_phone:
            print("[Evening Scheduler] 전화번호가 있는 사용자가 없습니다.")
            return
        
        success_count = 0
        total_count = len(users_with_phone)
        
        for user_data in users_with_phone:
            try:
                user_id = user_data.get('user_id')
                username = user_data.get('name', user_data.get('user_id', '사용자'))
                phone = user_data.get('phone', '').strip()
                
                if not phone:
                    print(f"[Evening Scheduler] {username}님의 전화번호가 없습니다.")
                    continue
                
                # intention_app_user 컬렉션에서 각 사용자의 오늘 사용량 조회
                usage_data = get_user_daily_usage(user_id, today, today)
                
                session_count = usage_data['session_count']
                formatted_time = usage_data['total_usage']['formatted']
                
                # 개인화된 메시지 생성
                if session_count > 0:
                    message = f"{username}님, 오늘 현재까지 {formatted_time} 동안 사용하셨군요! 남은 시간도 열심히 사용해주세요! 🔥" #{session_count}회 
                else:
                    message = f"{username}님, 오늘은 아직 앱을 사용하지 않으셨네요. 남은 시간 동안 열심히 사용해주세요! 💪"
                
                # 해당 사용자의 전화번호로 개인화된 메시지 전송
                try:
                    send_sms(phone, message)
                    success_count += 1
                    print(f"[Evening Scheduler] {username}님({user_id}) 당일 사용량 알림 전송 완료: {phone}")
                except Exception as e:
                    print(f"[Evening Scheduler] SMS 전송 실패 ({phone}, {username}): {e}")
                
            except Exception as e:
                print(f"[Evening Scheduler] User {user_id} 사용량 조회 실패: {e}")
        
        print(f"[Evening Scheduler] 당일 개별 사용량 알림 완료: {success_count}/{total_count}명 전송 성공")
        
    except Exception as e:
        print(f"[Evening Scheduler] 오류 발생: {e}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    
    # 개인화된 사용량 알림 스케줄 추가
    scheduler.add_job(_morning_usage_notification, CronTrigger(hour=7, minute=0), name="morning_usage_notification")
    scheduler.add_job(_evening_usage_notification, CronTrigger(hour=19, minute=0), name="evening_usage_notification")
    
    # 기존 브로드캐스트는 주석 처리 (필요시 활성화)
    # scheduler.add_job(_scheduled_job, CronTrigger(hour=7, minute=0), name="morning_broadcast")
    # scheduler.add_job(_scheduled_job, CronTrigger(hour=19, minute=0), name="evening_broadcast")
    
    scheduler.start()
    print("[Scheduler] 개인화된 사용량 알림 스케줄러 시작됨")
