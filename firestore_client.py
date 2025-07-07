import os
from google.cloud import firestore
from config import FIRESTORE_PROJECT_ID, FIRESTORE_DATABASE_ID, FIRESTORE_REGION

def initialize_firestore():
    """
    Firestore 클라이언트를 초기화합니다.
    GOOGLE_APPLICATION_CREDENTIALS 환경 변수에 서비스 계정 키 파일의 경로가 설정되어 있어야 합니다.
    """
    try:
        # Google Cloud Firestore 클라이언트 생성
        # database 매개변수로 특정 데이터베이스 지정
        client = firestore.Client(
            project=FIRESTORE_PROJECT_ID,
            database=FIRESTORE_DATABASE_ID
        )
        return client
    except Exception as e:
        print(f"Firestore 클라이언트 초기화 실패: {e}")
        raise e

def get_collection_data(collection_name: str):
    """
    지정된 컬렉션의 모든 문서를 가져옵니다.

    :param collection_name: 조회할 컬렉션의 이름
    :return: 컬렉션의 문서 리스트
    """
    db = initialize_firestore()
    docs_ref = db.collection(collection_name).stream()

    documents = []
    for doc in docs_ref:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        documents.append(doc_data)

    return documents

def get_user_data(collection_name: str, user_id: str):
    """
    특정 사용자의 데이터를 조회합니다.
    
    :param collection_name: 조회할 컬렉션의 이름
    :param user_id: 조회할 사용자 ID
    :return: 해당 사용자의 문서 리스트
    """
    db = initialize_firestore()
    # user_id 필드로 필터링하여 조회
    docs_ref = db.collection(collection_name).where('user_id', '==', user_id).stream()
    
    documents = []
    for doc in docs_ref:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        documents.append(doc_data)
    
    return documents

def get_user_data_by_field(collection_name: str, field_name: str, field_value: str):
    """
    특정 필드 값으로 사용자 데이터를 조회합니다.
    
    :param collection_name: 조회할 컬렉션의 이름
    :param field_name: 필터링할 필드 이름 (예: 'email', 'username', 'phone' 등)
    :param field_value: 필터링할 필드 값
    :return: 조건에 맞는 문서 리스트
    """
    db = initialize_firestore()
    # 지정된 필드로 필터링하여 조회
    docs_ref = db.collection(collection_name).where(field_name, '==', field_value).stream()
    
    documents = []
    for doc in docs_ref:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        documents.append(doc_data)
    
    return documents

def get_user_daily_usage(user_id: str, start_date: str, end_date: str):
    """
    특정 사용자의 지정된 날짜 범위 내 총 사용 시간을 계산합니다.
    
    :param user_id: 사용자 ID (sanitized_user_id)
    :param start_date: 시작 날짜 (YYYY-MM-DD 형식)
    :param end_date: 종료 날짜 (YYYY-MM-DD 형식) 
    :return: 총 사용 시간 정보 (초 단위 및 시간/분/초 형식)
    """
    from datetime import datetime, timezone
    import pytz
    
    db = initialize_firestore()
    
    # 날짜 문자열을 datetime 객체로 변환 (KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=kst)
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=kst)
    
    # 사용자 문서의 sessions 서브컬렉션 조회
    sessions_ref = db.collection('intention_app_user').document(user_id).collection('sessions')
    
    # 지정된 날짜 범위 내의 세션들을 쿼리
    sessions_query = sessions_ref.where('start_time', '>=', start_datetime).where('start_time', '<=', end_datetime)
    sessions = sessions_query.stream()
    
    total_seconds = 0
    session_count = 0
    session_details = []
    
    for session in sessions:
        session_data = session.to_dict()
        
        # start_time과 end_time이 모두 존재하는지 확인
        if 'start_time' in session_data and 'end_time' in session_data:
            start_time = session_data['start_time']
            end_time = session_data['end_time']
            
            # None이 아닌지 확인
            if start_time and end_time:
                # 세션 지속 시간 계산 (초 단위)
                duration_seconds = (end_time - start_time).total_seconds()
                
                # 음수 시간 방지 (end_time이 start_time보다 이른 경우)
                if duration_seconds > 0:
                    total_seconds += duration_seconds
                    session_count += 1
                    
                    session_details.append({
                        'session_id': session.id,
                        'task_name': session_data.get('task_name', ''),
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': int(duration_seconds),
                        'duration_formatted': format_duration_korean(int(duration_seconds)),
                        'duration_hms': format_duration(int(duration_seconds))
                    })
    
    # 총 사용 시간을 시간/분/초로 변환
    total_hours = int(total_seconds // 3600)
    total_minutes = int((total_seconds % 3600) // 60)
    remaining_seconds = int(total_seconds % 60)
    
    return {
        'user_id': user_id,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        },
        'total_usage': {
            'total_seconds': int(total_seconds),
            'formatted': format_duration_korean(int(total_seconds)),
            'formatted_hms': f"{total_hours:02d}:{total_minutes:02d}:{remaining_seconds:02d}",
            'hours': total_hours,
            'minutes': total_minutes,
            'seconds': remaining_seconds
        },
        'session_count': session_count,
        'sessions': session_details
    }

def format_duration(seconds):
    """
    초를 시:분:초 형식으로 변환합니다.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_duration_korean(seconds):
    """
    초를 한국어 시간 형식으로 변환합니다. (예: "2시간 30분", "45분", "1시간")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0 and minutes > 0:
        return f"{hours}시간 {minutes}분"
    elif hours > 0:
        return f"{hours}시간"
    elif minutes > 0:
        return f"{minutes}분"
    else:
        return "1분 미만"

def get_all_users():
    """
    intention_app_user 컬렉션의 모든 사용자 ID를 가져옵니다.
    
    :return: 사용자 ID 리스트
    """
    db = initialize_firestore()
    users_ref = db.collection('intention_app_user')
    users = users_ref.stream()
    
    user_ids = []
    for user in users:
        user_ids.append(user.id)  # document ID가 sanitized_user_id
    
    return user_ids

def get_all_users_with_info():
    """
    intention_app_user 컬렉션의 모든 사용자 정보를 가져옵니다.
    
    :return: 사용자 정보 딕셔너리 리스트 (user_id, 사용자 데이터 포함)
    """
    db = initialize_firestore()
    users_ref = db.collection('intention_app_user')
    users = users_ref.stream()
    
    user_list = []
    for user in users:
        user_data = user.to_dict()
        user_data['user_id'] = user.id  # document ID 추가
        user_list.append(user_data)
    
    return user_list

def get_user_info(user_id: str):
    """
    특정 사용자의 정보를 가져옵니다.
    
    :param user_id: 사용자 ID
    :return: 사용자 정보 딕셔너리
    """
    db = initialize_firestore()
    user_ref = db.collection('intention_app_user').document(user_id)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['user_id'] = user_id
        return user_data
    else:
        return None

def get_users_with_phone(role_filter: str = None):
    """
    personal_dashboard 컬렉션에서 유효한 전화번호가 있는 사용자들과
    intention_app_user 컬렉션의 사용자 ID를 매핑하여 가져옵니다.
    
    :param role_filter: 특정 role을 가진 사용자만 필터링 (예: "real")
    :return: 전화번호가 있는 사용자 정보 딕셔너리 리스트 (user_id, phone, name 등 포함)
    """
    db = initialize_firestore()
    
    # personal_dashboard에서 전화번호가 있는 사용자들 조회
    dashboard_users_ref = db.collection('personal_dashboard')
    dashboard_users = dashboard_users_ref.stream()
    
    # intention_app_user에서 실제 존재하는 사용자 ID들 조회
    app_users_ref = db.collection('intention_app_user')
    app_users = app_users_ref.stream()
    existing_user_ids = set()
    for user in app_users:
        existing_user_ids.add(user.id)
    
    users_with_phone = []
    for user in dashboard_users_ref.stream():
        user_data = user.to_dict()
        user_id = user.id  # document ID가 user_id
        
        # 전화번호가 있고 빈 문자열이 아닌 경우만 확인
        phone = user_data.get('phone', '').strip()
        if phone and user_id in existing_user_ids:
            # role 필터링 적용
            user_role = user_data.get('role', '').strip()
            if role_filter is None or user_role == role_filter:
                # intention_app_user에 실제 존재하는 사용자만 포함
                users_with_phone.append({
                    'user_id': user_id,
                    'phone': phone,
                    'name': user_data.get('name', user_id),
                    'role': user_role,
                    'dashboard_data': user_data
                })
    
    return users_with_phone 