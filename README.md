SMS 알림 서버 템플릿
====================
로컬 머신(예: EC2, 온-프레미스)에 배포할 수 있는 FastAPI 기반 SMS 발송 서버이다. 
- SOLAPI를 통해 SMS를 전송한다.
- APScheduler로 매일 07:00, 19:00(Asia/Seoul) 개인화된 사용량 알림을 자동 전송한다.
- **Google Cloud Firestore의 두 컬렉션을 연동하여 전화번호와 사용량 데이터를 매핑한다.**
  - `personal_dashboard`: 사용자별 전화번호 정보
  - `intention_app_user`: 사용자별 앱 사용량 데이터

REST API 엔드포인트
------------------

### SMS 관련 기능 (관리용)
- `POST   /send/broadcast`        : 관리자용 즉시 브로드캐스트 (수동)

### Firestore 데이터 조회 기능
- `GET    /firestore/{collection_name}`                    : 컬렉션 전체 데이터 조회
- `GET    /firestore/{collection_name}/user/{user_id}`     : 특정 사용자 데이터 조회
- `GET    /firestore/{collection_name}/filter`             : 필드 값으로 필터링 조회
- `GET    /firestore/user/{user_id}/usage`                 : 사용자 일일 사용 시간 조회

### 자동 사용량 알림 기능 (테스트용)
- `POST   /test/morning-notification`                     : 오전 사용량 알림 테스트 (수동 실행)
- `POST   /test/evening-notification`                     : 오후 사용량 알림 테스트 (수동 실행)

**자동 스케줄러 (핵심 기능):**
- **오전 7시**: role이 "real"인 사용자들에게 각자의 전날 사용량을 개인화된 메시지로 개별 전송
- **오후 7시**: role이 "real"인 사용자들에게 각자의 당일 현재까지 사용량을 개인화된 메시지로 개별 전송
- **데이터 매핑**: `personal_dashboard`(전화번호, role) + `intention_app_user`(사용량) 자동 매핑
- **Slack 로깅**: SMS 발송 성공/실패 및 통계를 Slack으로 실시간 알림

**개인화된 알림 메시지 예시:**
- 오전: "김철수님, 어제 2시간 30분 동안 5회 사용하셨군요! 오늘도 열심히 사용해주세요! 💪"
- 오전 (사용 없음): "박영희님, 어제는 앱을 사용하지 않으셨네요. 오늘은 열심히 사용해주세요! 📱"
- 오후: "이민수님, 오늘 현재까지 1시간 15분 동안 3회 사용하셨군요! 남은 시간도 열심히 사용해주세요! 🔥"
- 오후 (사용 없음): "최영수님, 오늘은 아직 앱을 사용하지 않으셨네요. 남은 시간 동안 열심히 사용해주세요! 💪"

### Firestore API 사용 예시

#### 1. 컬렉션 전체 조회
```bash
curl -X GET "http://127.0.0.1:8000/firestore/intention_app_user"
```

#### 2. 특정 사용자 데이터 조회
```bash
curl -X GET "http://127.0.0.1:8000/firestore/intention_app_user/user/user123"
```

#### 3. real role 사용자 조회 (관리용)
```bash
# personal_dashboard에서 real role 사용자 조회
curl -X GET "http://127.0.0.1:8000/firestore/personal_dashboard/filter?field_name=role&field_value=real"
```

#### 4. 사용자 일일 사용 시간 조회
```bash
# 특정 날짜의 사용 시간
curl -X GET "http://127.0.0.1:8000/firestore/user/user123/usage?start_date=2024-01-01&end_date=2024-01-01"

# 일주일간 사용 시간
curl -X GET "http://127.0.0.1:8000/firestore/user/user123/usage?start_date=2024-01-01&end_date=2024-01-07"
```

#### 5. 자동 사용량 알림 테스트 (개발/테스트용)
```bash
# 오전 알림 테스트 - real role 사용자에게 전날 사용량 개별 전송
curl -X POST "http://127.0.0.1:8000/test/morning-notification"

# 오후 알림 테스트 - real role 사용자에게 당일 사용량 개별 전송
curl -X POST "http://127.0.0.1:8000/test/evening-notification"
```

**사용 시간 조회 응답 예시:**
```json
{
  "user_id": "user123",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-01"
  },
  "total_usage": {
    "total_seconds": 7200,
    "formatted": "02:00:00",
    "hours": 2,
    "minutes": 0,
    "seconds": 0
  },
  "session_count": 3,
  "sessions": [
    {
      "session_id": "session_123",
      "task_name": "작업 1",
      "start_time": "2024-01-01T09:00:00+09:00",
      "end_time": "2024-01-01T10:30:00+09:00",
      "duration_seconds": 5400,
      "duration_formatted": "01:30:00"
    }
  ]
}
```

필수 환경 변수 (.env 파일 등)
-----------------------------

### SOLAPI 설정
```bash
SOLAPI_API_KEY=<your_api_key>           # SOLAPI에서 발급받은 API Key
SOLAPI_API_SECRET=<your_api_secret>     # SOLAPI에서 발급받은 API Secret
SENDER_PHONE=01000000000                # 등록된 발신번호 (01000000000 형식, - 제외)
```

### Slack 웹훅 설정
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...    # Slack 웹훅 URL
```

### Firestore 설정 (선택사항)
```bash
FIRESTORE_PROJECT_ID=intention-computing-451401    # GCP 프로젝트 ID
FIRESTORE_DATABASE_ID=intention-computing          # Firestore 데이터베이스 ID
FIRESTORE_REGION=asia-northeast3                   # Firestore 리전
```

의존 패키지
-----------
```bash
pip install -r requirements.txt
```

GCP 및 Firestore 설정
---------------------

### 1. gcloud CLI 설치 (Mac)
```bash
brew install google-cloud-sdk
```

### 2. Google Cloud 인증
```bash
# Google Cloud 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project intention-computing-451401

# Application Default Credentials 설정
gcloud auth application-default login
```

### 3. Firestore 데이터베이스 구조
```
intention-computing (Database)
├── personal_dashboard (Collection) - 사용자 기본 정보 및 전화번호
│   └── {user_id} (Document)
│       ├── name: string           # 사용자 이름
│       ├── phone: string          # 전화번호 (01000000000 형식, 하이픈 포함/미포함 모두 지원)
│       ├── role: string           # 사용자 역할 (real, beta 등)
│       ├── pw: string             # 비밀번호
│       ├── start_date: timestamp  # 시작일
│       └── stats: object          # 통계 정보
│           ├── week_1: number
│           ├── week_2: number
│           └── week_3: number
│
└── intention_app_user (Collection) - 앱 사용량 데이터
    └── {sanitized_user_id} (Document)
        ├── user_id: string
        ├── created_at: timestamp  
        ├── last_active: timestamp
        └── sessions (Sub-collection)
            └── {session_id} (Document)
                ├── task_name: string
                ├── intention: string  
                ├── start_time: timestamp
                ├── end_time: timestamp
                ├── device_info: object
                ├── final_rating: number | null
                ├── image_cnt: number
                ├── feedback_cnt: number
                ├── notification_cnt: number
                ├── focus_cnt: number
                ├── distract_cnt: number
                └── ... (기타 필드들)
```

서버 실행
---------
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

FastAPI 생성 API 문서
--------------------
서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

아키텍처 및 고려사항
--------------------
- **데이터 아키텍처**: 
  - `personal_dashboard` 컬렉션: 사용자 기본 정보 및 전화번호 저장
  - `intention_app_user` 컬렉션: 앱 사용량 데이터 저장 (sessions 서브컬렉션)
  - 두 컬렉션을 user_id로 매핑하여 전화번호와 사용량 데이터를 연결
- **Firestore 연동**: Google Cloud Firestore를 통해 사용자 세션 데이터와 사용 시간을 조회할 수 있습니다. `google-cloud-firestore` 라이브러리를 사용하여 multi-database 환경을 지원합니다.
- **개인화된 알림 시스템**: APScheduler를 사용하여 매일 오전 7시와 오후 7시에 개인화된 사용량 알림을 자동 전송합니다.
  - `personal_dashboard`에서 전화번호가 있고 role이 "real"인 사용자만 대상으로 선별
  - 전화번호 정규화: 하이픈 포함/미포함 형식 모두 지원
  - Slack 로깅: SMS 발송 결과를 실시간으로 Slack에 알림
  - `intention_app_user`에서 각 사용자의 개별 사용량 데이터를 조회
  - 각 사용자가 본인의 전화번호로 본인의 사용량만 수신 (개인정보 보호)
  - 사용자명(name)과 사용 시간, 세션 수를 포함한 격려 메시지
  - 한국 시간대(KST) 기준으로 동작
- **수신자 관리**: 기존 `recipients.json` 파일 방식에서 Firestore 기반으로 변경되어 더 안정적이고 확장 가능한 구조
- **데이터 정합성**: 두 컬렉션 모두에 존재하고 유효한 전화번호가 있는 사용자만 SMS 발송 대상에 포함

관련 링크
---------
- **Firestore Console**: https://console.cloud.google.com/firestore/databases/intention-computing/data/panel/chat_users/Anonymous?inv=1&invt=Ab1Haw&project=intention-computing-451401
- **Dashboard GitHub**: https://github.com/wngjs3/intention_dashboard

## 🚀 운영 배포 정보

### 📡 배포된 서버 정보
**SMS 서버가 GCP VM에 성공적으로 배포되어 운영 중입니다.**

- **서버 주소**: `34.64.237.127:8000`
- **API 문서**: http://34.64.237.127:8000/docs
- **상태 확인**: http://34.64.237.127:8000/ (응답: `{"status":"ok"}`)
- **배포일**: 2025년 7월 8일

### ⚡ 자동화된 기능들
- ✅ **자동 SMS 발송**: 매일 **오전 7시**, **오후 7시**에 실제 사용자들에게 개인화된 사용량 알림 자동 전송
- ✅ **서비스 자동 시작**: 서버 재부팅 시 자동으로 SMS 서비스 시작 (`systemd` 서비스로 등록)
- ✅ **24/7 운영**: 콘솔에서 수동으로 삭제하기 전까지 지속적으로 운영
- ✅ **오류 복구**: 서비스 장애 시 자동 재시작 (3초 후 재시작)

### 🎯 운영 중인 스케줄러
```
매일 오전 7시 (KST) → role="real" 사용자들에게 전날 사용량 개별 SMS 발송
매일 오후 7시 (KST) → role="real" 사용자들에게 당일 사용량 개별 SMS 발송
```

### 🔧 서버 관리 명령어
SSH로 서버 접속 후 사용 가능한 명령어들:

```bash
# 서비스 상태 확인
sudo systemctl status sms-sender.service

# 서비스 재시작
sudo systemctl restart sms-sender.service

# 서비스 중지
sudo systemctl stop sms-sender.service

# 실시간 로그 확인
sudo journalctl -u sms-sender.service -f

# 최근 로그 50줄 확인
sudo journalctl -u sms-sender.service -n 50
```

### 📊 모니터링 및 테스트
```bash
# API 상태 확인
curl http://34.64.237.127:8000/

# 오전 알림 수동 테스트
curl -X POST http://34.64.237.127:8000/test/morning-notification

# 오후 알림 수동 테스트  
curl -X POST http://34.64.237.127:8000/test/evening-notification

# Firestore 연결 테스트
curl http://34.64.237.127:8000/firestore/personal_dashboard/filter?field_name=role&field_value=real
```

### 🛡️ 보안 설정
- **방화벽**: GCP 방화벽 규칙으로 8000번 포트만 외부 접근 허용
- **인증**: GCP 서비스 계정을 통한 Firestore 접근
- **환경변수**: 민감한 정보 (API 키, 웹훅 URL 등)는 `.env` 파일로 보호

### ⚠️ 중요 사항
- **서버 중지**: GCP 콘솔에서 VM 인스턴스를 중지하거나 삭제하기 전까지 계속 운영됩니다
- **비용 관리**: VM 운영 비용이 지속적으로 발생하니 필요시 콘솔에서 관리하세요
- **로그 모니터링**: Slack으로 SMS 발송 결과가 실시간으로 알림되므로 모니터링 가능합니다