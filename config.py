"""config.py
공통 설정 및 리소스 초기화 모듈
--------------------------------
환경 변수 로드, 경로 설정, SOLAPI 클라이언트 생성 등을 담당한다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from solapi import SolapiMessageService

# .env 파일 로드
load_dotenv()

# 기본 디렉터리(프로젝트 루트)
BASE_DIR = Path(__file__).resolve().parent
RECIPIENT_FILE = BASE_DIR / "recipients.json"

# SOLAPI 환경 변수
SOLAPI_API_KEY = os.getenv("SOLAPI_API_KEY")
SOLAPI_API_SECRET = os.getenv("SOLAPI_API_SECRET")
SENDER_PHONE = os.getenv("SENDER_PHONE")  # 발신번호 (01000000000 형식)

# Slack 웹훅 URL
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not SOLAPI_API_KEY:
    raise RuntimeError("SOLAPI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
if not SOLAPI_API_SECRET:
    raise RuntimeError("SOLAPI_API_SECRET 환경 변수가 설정되어 있지 않습니다.")
if not SENDER_PHONE:
    raise RuntimeError("SENDER_PHONE 환경 변수가 설정되어 있지 않습니다.")

# SOLAPI 메시지 서비스 클라이언트 초기화
message_service = SolapiMessageService(
    api_key=SOLAPI_API_KEY, 
    api_secret=SOLAPI_API_SECRET
)

# 타임존(Asia/Seoul)
import pytz
TIMEZONE = pytz.timezone("Asia/Seoul")

# Firestore 설정
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "intention-computing-451401")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "intention-computing")
FIRESTORE_REGION = os.getenv("FIRESTORE_REGION", "asia-northeast3")
