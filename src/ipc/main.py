"""
IPC Main - JSON-RPC over stdin/stdout
Electron과 Python 간 통신을 담당
"""
import sys
import json
import logging
from typing import Any, Dict, Optional

from .handler import RpcHandler

# 로깅 설정 (stderr로 출력)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class JsonRpcServer:
    """JSON-RPC 2.0 서버 (stdin/stdout 기반)"""

    def __init__(self):
        self.handler = RpcHandler()
        self.running = True

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 요청 처리"""
        request_id = request.get('id')
        method = request.get('method', '')
        params = request.get('params', {})

        try:
            result = self.handler.call(method, params)
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result,
            }
        except Exception as e:
            logger.error(f"RPC error: {method} - {e}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32000,
                    'message': str(e),
                },
            }

    def run(self):
        """메인 루프 - stdin에서 요청을 읽고 stdout으로 응답"""
        logger.info("JSON-RPC Server started")

        while self.running:
            try:
                # stdin에서 한 줄 읽기
                line = sys.stdin.readline()

                if not line:
                    # EOF - 종료
                    break

                line = line.strip()
                if not line:
                    continue

                # JSON 파싱
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': f'Parse error: {e}',
                        },
                    }
                    self.send_response(response)
                    continue

                # shutdown 명령 처리
                if request.get('method') == 'shutdown':
                    self.running = False
                    response = {
                        'jsonrpc': '2.0',
                        'id': request.get('id'),
                        'result': {'status': 'shutdown'},
                    }
                    self.send_response(response)
                    break

                # 요청 처리
                response = self.process_request(request)
                self.send_response(response)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Server error: {e}")

        logger.info("JSON-RPC Server stopped")

    def send_response(self, response: Dict[str, Any]):
        """stdout으로 응답 전송"""
        response_str = json.dumps(response, ensure_ascii=False)
        print(response_str, flush=True)


def main():
    """엔트리포인트"""
    server = JsonRpcServer()
    server.run()


if __name__ == '__main__':
    main()
