"""scheduler.py
APScheduler 기반 정기 브로드캐스트 관리
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import TIMEZONE
from sms_sender import send_sms
from firestore_client import get_user_daily_usage, get_users_with_phone
from slack_logger import slack_logger

__all__ = ["start_scheduler"]

# 한국 시간대 명시적 설정
KST = pytz.timezone('Asia/Seoul')


def _morning_usage_notification():
    """오전 7시: 전날 사용량 알림 (real role 사용자만)"""
    try:
        # 전날 날짜 계산 (KST 기준으로 명시적 설정)
        kst_now = datetime.now(KST)
        yesterday = (kst_now - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"[Morning Scheduler] 현재 KST 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"[Morning Scheduler] 조회 대상 날짜: {yesterday}")
        
        # real role을 가진 사용자들만 조회
        users_with_phone = get_users_with_phone(role_filter="real")

        # 현재 날짜 및 시간 (KST)
        now_kst = datetime.now(KST)
        
        if not users_with_phone:
            print("[Morning Scheduler] real role을 가진 사용자가 없습니다.")
            return
        
        success_count = 0
        failed_count = 0
        total_count = len(users_with_phone)
        
        for user_data in users_with_phone:
            try:
                # 사용자별 날짜 필터링
                dashboard_data = user_data.get('dashboard_data', {})
                start_date = dashboard_data.get('start_date')
                end_date = dashboard_data.get('end_date')

                if isinstance(start_date, datetime):
                    start_date = start_date.astimezone(KST)
                if isinstance(end_date, datetime):
                    end_date = end_date.astimezone(KST)

                # 날짜 유효성 검사
                if not (start_date and start_date <= now_kst and (not end_date or end_date >= now_kst)):
                    continue

                user_id = user_data.get('user_id')
                username = user_data.get('name', user_data.get('user_id', '사용자'))
                phone = user_data.get('phone', '').strip()
                
                if not phone:
                    print(f"[Morning Scheduler] {username}님의 전화번호가 없습니다.")
                    continue
                
                # intention_app_user 컬렉션에서 각 사용자의 전날 사용량 조회
                usage_data = get_user_daily_usage(user_id, yesterday, yesterday)
                
                total_seconds = usage_data['total_usage']['total_seconds']
                formatted_time = usage_data['total_usage']['formatted']
                
                # 전날 사용 시간이 2시간(7200초) 미만인 경우에만 알림 발송
                if total_seconds < 7200:
                    if total_seconds > 0:
                        message = f"{username}님, 어제 {formatted_time} 동안 사용하셨네요. 오늘은 조금만 더 힘내봐요! 💪"
                    else:
                        message = f"{username}님, 어제는 앱을 사용하지 않으셨네요. 오늘은 앱을 꼭 사용해보세요! 💻"
                    
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
                else:
                    # 사용 시간이 2시간 이상인 경우 건너뛰기
                    print(f"[Morning Scheduler] {username}님({user_id})은/는 전날 목표 사용 시간을 달성하여 알림을 건너뜁니다.")

            except Exception as e:
                print(f"[Morning Scheduler] User {user_id} 처리 실패: {e}")
                failed_count += 1
        
        # 실제 발송 대상자 수 조정 (total_count는 조회된 전체 사용자 수 유지)
        print(f"[Morning Scheduler] 전날 사용량 2시간 미만 real 사용자 대상 알림 완료: {success_count}명 전송 성공, {failed_count}명 실패")
        
        # 슬랙에 최종 결과 로깅
        slack_logger.log_broadcast_result(total_count, success_count, failed_count)
        
    except Exception as e:
        print(f"[Morning Scheduler] 오류 발생: {e}")


def _evening_usage_notification():
    """오후 7시: 당일 사용량 알림 (real role 사용자만)"""
    try:
        # 오늘 날짜 계산 (KST 기준으로 명시적 설정)
        kst_now = datetime.now(KST)
        today = kst_now.strftime('%Y-%m-%d')
        
        print(f"[Evening Scheduler] 현재 KST 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"[Evening Scheduler] 조회 대상 날짜: {today}")
        
        # real role을 가진 사용자들만 조회
        users_with_phone = get_users_with_phone(role_filter="real")

        # 현재 날짜 및 시간 (KST)
        now_kst = datetime.now(KST)
        
        if not users_with_phone:
            print("[Evening Scheduler] real role을 가진 사용자가 없습니다.")
            return
        
        success_count = 0
        failed_count = 0
        total_count = len(users_with_phone)
        
        for user_data in users_with_phone:
            try:
                # 사용자별 날짜 필터링
                dashboard_data = user_data.get('dashboard_data', {})
                start_date = dashboard_data.get('start_date')
                end_date = dashboard_data.get('end_date')

                if isinstance(start_date, datetime):
                    start_date = start_date.astimezone(KST)
                if isinstance(end_date, datetime):
                    end_date = end_date.astimezone(KST)

                # 날짜 유효성 검사
                if not (start_date and start_date <= now_kst and (not end_date or end_date >= now_kst)):
                    continue

                user_id = user_data.get('user_id')
                username = user_data.get('name', user_data.get('user_id', '사용자'))
                phone = user_data.get('phone', '').strip()
                
                if not phone:
                    print(f"[Evening Scheduler] {username}님의 전화번호가 없습니다.")
                    continue
                
                # intention_app_user 컬렉션에서 각 사용자의 오늘 사용량 조회
                usage_data = get_user_daily_usage(user_id, today, today)
                
                total_seconds = usage_data['total_usage']['total_seconds']
                formatted_time = usage_data['total_usage']['formatted']

                # 당일 사용 시간이 2시간(7200초) 미만인 경우에만 알림 발송
                if total_seconds < 7200:
                    if total_seconds > 0:
                        message = f"{username}님, 오늘 현재까지 {formatted_time} 사용하셨어요. 남은 시간도 화이팅! 🔥"
                    else:
                        message = f"{username}님, 오늘은 아직 앱을 사용하지 않으셨네요. 지금부터 어플 실행 어떠세요? 💪"
                    
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
                else:
                    # 사용 시간이 2시간 이상인 경우 건너뛰기
                    print(f"[Evening Scheduler] {username}님({user_id})은/는 당일 목표 사용 시간을 달성하여 알림을 건너뜁니다.")
            
            except Exception as e:
                print(f"[Evening Scheduler] User {user_id} 처리 실패: {e}")
                failed_count += 1
        
        print(f"[Evening Scheduler] 당일 사용량 2시간 미만 real 사용자 대상 알림 완료: {success_count}명 전송 성공, {failed_count}명 실패")
        
        # 슬랙에 최종 결과 로깅
        slack_logger.log_broadcast_result(total_count, success_count, failed_count)
        
    except Exception as e:
        print(f"[Evening Scheduler] 오류 발생: {e}")


def start_scheduler():
    # 스케줄러를 한국 시간대로 명시적 설정
    scheduler = BackgroundScheduler(timezone=KST)
    
    # 개인화된 사용량 알림 스케줄 추가 (한국 시간 기준)
    scheduler.add_job(_morning_usage_notification, CronTrigger(hour=7, minute=0, timezone=KST), name="morning_usage_notification")
    scheduler.add_job(_evening_usage_notification, CronTrigger(hour=19, minute=0, timezone=KST), name="evening_usage_notification")
    
    scheduler.start()
    print("[Scheduler] real 사용자 대상 사용량 알림 스케줄러 시작됨 (KST 기준)")
    
    # 스케줄러 상태 확인
    print(f"[Scheduler] 등록된 작업 수: {len(scheduler.get_jobs())}")
    for job in scheduler.get_jobs():
        next_run_kst = job.next_run_time.astimezone(KST) if job.next_run_time else None
        print(f"[Scheduler] 작업: {job.name} - 다음 실행: {next_run_kst}")
