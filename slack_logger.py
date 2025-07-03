"""slack_logger.py
Slack 로깅 모듈
SMS 발송 결과와 오류를 Slack으로 전송하는 기능을 담당합니다.
"""

import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from config import SLACK_WEBHOOK_URL, TIMEZONE


class SlackLogger:
    """Slack 로깅 클래스"""
    
    def __init__(self, webhook_url: str = SLACK_WEBHOOK_URL):
        self.webhook_url = webhook_url
    
    def _send_to_slack(self, payload: Dict[str, Any]) -> bool:
        """
        Slack으로 메시지를 전송합니다.
        
        Args:
            payload: Slack API 페이로드
            
        Returns:
            전송 성공 여부
        """
        try:
            response = requests.post(
                self.webhook_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack 전송 실패: {e}")
            return False
    
    def log_sms_success(self, phone: str, message: str, user_info: Optional[str] = None) -> None:
        """
        SMS 발송 성공 로그를 Slack으로 전송합니다.
        
        Args:
            phone: 수신 전화번호
            message: 발송된 메시지 내용
            user_info: 사용자 정보 (선택사항)
        """
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        
        # 메시지 길이 제한 (Slack 메시지 길이 제한 고려)
        display_message = message[:100] + "..." if len(message) > 100 else message
        
        payload = {
            "text": f"✅ SMS 발송 성공",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📱 SMS 발송 성공"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*전화번호:*\n{phone}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*발송 시간:*\n{current_time}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*메시지 내용:*\n```{display_message}```"
                    }
                }
            ]
        }
        
        if user_info:
            payload["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*사용자 정보:*\n{user_info}"
                }
            })
        
        self._send_to_slack(payload)
    
    def log_sms_failure(self, phone: str, message: str, error: str, user_info: Optional[str] = None) -> None:
        """
        SMS 발송 실패 로그를 Slack으로 전송합니다.
        
        Args:
            phone: 수신 전화번호
            message: 발송 시도한 메시지 내용
            error: 오류 메시지
            user_info: 사용자 정보 (선택사항)
        """
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        
        # 메시지 길이 제한
        display_message = message[:100] + "..." if len(message) > 100 else message
        
        payload = {
            "text": f"❌ SMS 발송 실패",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 SMS 발송 실패"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*전화번호:*\n{phone}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*실패 시간:*\n{current_time}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*메시지 내용:*\n```{display_message}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*오류 내용:*\n```{error}```"
                    }
                }
            ]
        }
        
        if user_info:
            payload["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*사용자 정보:*\n{user_info}"
                }
            })
        
        self._send_to_slack(payload)
    
    def log_broadcast_result(self, total_count: int, success_count: int, failed_count: int) -> None:
        """
        브로드캐스트 결과를 Slack으로 전송합니다.
        
        Args:
            total_count: 전체 수신자 수
            success_count: 성공한 발송 수
            failed_count: 실패한 발송 수
        """
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
        
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        payload = {
            "text": f"📢 브로드캐스트 완료",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📢 SMS 브로드캐스트 완료"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*전체 수신자:*\n{total_count}명"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*성공:*\n{success_count}명"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*실패:*\n{failed_count}명"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*성공률:*\n{success_rate:.1f}%"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*완료 시간:*\n{current_time}"
                    }
                }
            ]
        }
        
        self._send_to_slack(payload)


# 전역 인스턴스
slack_logger = SlackLogger() 