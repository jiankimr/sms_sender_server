SMS 알림 서버 템플릿
====================
로컬 머신(예: EC2, 온-프레미스)에 배포할 수 있는 FastAPI 기반 SMS 발송 서버이다. 
- AWS End User Messaging (Pinpoint SMS and Voice v2)을 통해 SMS를 전송한다.
- APScheduler로 매일 07:00, 19:00(Asia/Seoul) 자동 브로드캐스트를 예약한다.
- 간단한 JSON 파일(`recipients.json`)에 수신자 전화번호를 저장한다.
- REST 엔드포인트를 제공한다.
  - `POST   /recipients`            : 수신자 등록 (전화번호 추가)
  - `GET    /recipients`            : 수신자 목록 조회
  - `POST   /send/{phone}`          : 특정 수신자 1회 발송
  - `POST   /send/broadcast`        : 모든 수신자 즉시 브로드캐스트

필수 환경 변수 (.env 파일 등)
-----------------------------
AWS_ACCESS_KEY_ID=<access_key>
AWS_SECRET_ACCESS_KEY=<secret_key>
AWS_REGION=us-east-1            # Pinpoint SMS and Voice v2 서비스를 사용하는 리전
SENDER_ID=AIGENT                # AWS에 등록되고 승인된 발신자 ID (선택 사항)
TOLL_FREE_NUMBER=+1234567890    # AWS에 등록된 발신용 전화번호 (Toll-Free, 10DLC 등. E.164 형식)

의존 패키지
-----------
pip install -r requirements.txt

서버 실행
---------
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

아키텍처 및 고려사항
--------------------
- **데이터 저장소**: 수신자 목록은 별도 데이터베이스 없이 로컬 `recipients.json` 파일에 저장됩니다. 이는 서버를 가볍고 단순하게 유지하기 위함입니다.
- **동시성 문제 (Concurrency)**: `POST /recipients` 엔드포인트를 통해 동시에 여러 수신자 등록 요청이 발생할 경우, 경쟁 조건(Race Condition)으로 인해 데이터가 누락되거나 중복 저장될 수 있습니다. 
  - **판단**: 현재 시스템은 운영자가 초기에 수신자를 한 번만 등록하고, 이후에는 수신자 목록을 거의 변경하지 않는 것을 전제로 합니다. 따라서 API를 통한 동적 수신자 추가 시의 동시성 문제는 고려하지 않아도 되는 상황으로 판단했습니다. 만약 API를 통해 수신자를 빈번하게 추가/삭제해야 하는 요구사항이 생긴다면, 파일 잠금(File Locking)이나 데이터베이스를 도입하여 이 문제를 해결해야 합니다.