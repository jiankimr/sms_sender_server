"""config.py
공통 설정 및 리소스 초기화 모듈
--------------------------------
환경 변수 로드, 경로 설정, boto3 세션(SNS) 생성 등을 담당한다.
"""

import os
from pathlib import Path

from boto3 import Session
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 디렉터리(프로젝트 루트)
BASE_DIR = Path(__file__).resolve().parent
RECIPIENT_FILE = BASE_DIR / "recipients.json"

# 환경 변수
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SENDER_ID = os.getenv("SENDER_ID", "AIGENT")
TOLL_FREE_NUMBER = os.getenv("TOLL_FREE_NUMBER")

if not TOLL_FREE_NUMBER:
    raise RuntimeError("TOLL_FREE_NUMBER 환경 변수가 설정되어 있지 않습니다.")

# boto3 세션 및 SNS 클라이언트 초기화
session = Session(region_name=AWS_REGION)
sns_client = session.client("sns")

# 타임존(Asia/Seoul)
import pytz
TIMEZONE = pytz.timezone("Asia/Seoul")
