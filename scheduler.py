"""scheduler.py
APScheduler 기반 정기 브로드캐스트 관리
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TIMEZONE
from sms_sender import send_sms
from firestore_client import get_user_daily_usage, get_users_with_phone
from slack_logger import slack_logger

__all__ = ["start_scheduler"]


def _morning_usage_notification():
    """오전 7시: 전날 사용량 알림 (real role 사용자만)"""
    try:
        # 전날 날짜 계산 (KST 기준)
        yesterday = (datetime.now(TIMEZONE) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # real role을 가진 사용자들만 조회
        users_with_phone = get_users_with_phone(role_filter="real")
        
        if not users_with_phone:
            print("[Morning Scheduler] real role을 가진 사용자가 없습니다.")
            return
        
        success_count = 0
        failed_count = 0
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
                    message = f"{username}님, 어제 {formatted_time} 동안 사용하셨군요! 오늘도 열심히 사용해주세요! 💪"
                else:
                    message = f"{username}님, 어제는 앱을 사용하지 않으셨네요. 오늘은 열심히 사용해주세요! 📱"
                
                # 사용자 정보 생성 (Slack 로깅용)
                user_info = f"사용자 ID: {user_id}, 이름: {username}, Role: {user_data.get('role', 'N/A')}"
                
                # 해당 사용자의 전화번호로 개인화된 메시지 전송
                try:
                    send_sms(phone, message, user_info)
                    success_count += 1
                    print(f"[Morning Scheduler] {username}님({user_id}) 전날 사용량 알림 전송 완료: {phone}")
                except Exception as e:
                    print(f"[Morning Scheduler] SMS 전송 실패 ({phone}, {username}): {e}")
                    failed_count += 1
                
            except Exception as e:
                print(f"[Morning Scheduler] User {user_id} 사용량 조회 실패: {e}")
        
        print(f"[Morning Scheduler] 전날 real 사용량 알림 완료: {success_count}/{total_count}명 전송 성공, {failed_count}명 실패")
        
        # 슬랙에 최종 결과 로깅
        slack_logger.log_broadcast_result(total_count, success_count, failed_count)
        
    except Exception as e:
        print(f"[Morning Scheduler] 오류 발생: {e}")


def _evening_usage_notification():
    """오후 7시: 당일 사용량 알림 (real role 사용자만)"""
    try:
        # 오늘 날짜 계산 (KST 기준)
        today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        
        # real role을 가진 사용자들만 조회
        users_with_phone = get_users_with_phone(role_filter="real")
        
        if not users_with_phone:
            print("[Evening Scheduler] real role을 가진 사용자가 없습니다.")
            return
        
        success_count = 0
        failed_count = 0
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
                    message = f"{username}님, 오늘 현재까지 {formatted_time} 동안 사용하셨군요! 남은 시간도 열심히 사용해주세요! 🔥"
                else:
                    message = f"{username}님, 오늘은 아직 앱을 사용하지 않으셨네요. 남은 시간 동안 열심히 사용해주세요! 💪"
                
                # 사용자 정보 생성 (Slack 로깅용)
                user_info = f"사용자 ID: {user_id}, 이름: {username}, Role: {user_data.get('role', 'N/A')}"
                
                # 해당 사용자의 전화번호로 개인화된 메시지 전송
                try:
                    send_sms(phone, message, user_info)
                    success_count += 1
                    print(f"[Evening Scheduler] {username}님({user_id}) 당일 사용량 알림 전송 완료: {phone}")
                except Exception as e:
                    print(f"[Evening Scheduler] SMS 전송 실패 ({phone}, {username}): {e}")
                    failed_count += 1
                
            except Exception as e:
                print(f"[Evening Scheduler] User {user_id} 사용량 조회 실패: {e}")
        
        print(f"[Evening Scheduler] 당일 real 사용량 알림 완료: {success_count}/{total_count}명 전송 성공, {failed_count}명 실패")
        
        # 슬랙에 최종 결과 로깅
        slack_logger.log_broadcast_result(total_count, success_count, failed_count)
        
    except Exception as e:
        print(f"[Evening Scheduler] 오류 발생: {e}")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    
    # 개인화된 사용량 알림 스케줄 추가
    scheduler.add_job(_morning_usage_notification, CronTrigger(hour=7, minute=0), name="morning_usage_notification")
    scheduler.add_job(_evening_usage_notification, CronTrigger(hour=19, minute=0), name="evening_usage_notification")
    
    scheduler.start()
    print("[Scheduler] real 사용자 대상 사용량 알림 스케줄러 시작됨")
    
    # 스케줄러 상태 확인
    print(f"[Scheduler] 등록된 작업 수: {len(scheduler.get_jobs())}")
    for job in scheduler.get_jobs():
        print(f"[Scheduler] 작업: {job.name} - 다음 실행: {job.next_run_time}")
