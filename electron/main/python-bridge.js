const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');

class PythonBridge {
  constructor(isDev) {
    this.isDev = isDev;
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.rl = null;
  }

  /**
   * Python 백엔드 프로세스 시작
   */
  async start() {
    return new Promise((resolve, reject) => {
      let pythonPath, scriptPath;

      if (this.isDev) {
        // 개발 모드: Python 모듈로 실행
        pythonPath = 'python';
        scriptPath = '-m';  // 모듈 실행 플래그
      } else {
        // 프로덕션: PyInstaller로 빌드된 실행 파일
        const resourcesPath = process.resourcesPath;
        if (process.platform === 'win32') {
          pythonPath = path.join(resourcesPath, 'python-backend', 'backend.exe');
        } else {
          pythonPath = path.join(resourcesPath, 'python-backend', 'backend');
        }
        scriptPath = null;
      }

      // 프로세스 시작
      const args = this.isDev ? ['-m', 'src.ipc.main'] : [];
      this.process = spawn(pythonPath, args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.join(__dirname, '../..'),
      });

      // stdout에서 JSON-RPC 응답 읽기
      this.rl = readline.createInterface({
        input: this.process.stdout,
        crlfDelay: Infinity,
      });

      this.rl.on('line', (line) => {
        this.handleResponse(line);
      });

      // stderr 로깅
      this.process.stderr.on('data', (data) => {
        console.error('Python stderr:', data.toString());
      });

      // 프로세스 종료 처리
      this.process.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        this.process = null;
      });

      // 프로세스 에러 처리
      this.process.on('error', (error) => {
        console.error('Python process error:', error);
        reject(error);
      });

      // 시작 확인 (ping 호출)
      setTimeout(async () => {
        try {
          await this.call('ping', {});
          resolve();
        } catch (error) {
          reject(error);
        }
      }, 1000);
    });
  }

  /**
   * Python 백엔드 프로세스 종료
   */
  async stop() {
    if (this.process) {
      try {
        await this.call('shutdown', {});
      } catch (error) {
        // 무시
      }

      this.process.kill();
      this.process = null;
    }

    if (this.rl) {
      this.rl.close();
      this.rl = null;
    }
  }

  /**
   * JSON-RPC 호출
   */
  async call(method, params = {}) {
    return new Promise((resolve, reject) => {
      if (!this.process) {
        reject(new Error('Python process not running'));
        return;
      }

      const id = ++this.requestId;
      const request = {
        jsonrpc: '2.0',
        id: id,
        method: method,
        params: params,
      };

      // 타임아웃 설정 (30초)
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`Request timeout: ${method}`));
      }, 30000);

      this.pendingRequests.set(id, { resolve, reject, timeout });

      // 요청 전송
      const requestStr = JSON.stringify(request) + '\n';
      this.process.stdin.write(requestStr);
    });
  }

  /**
   * JSON-RPC 응답 처리
   */
  handleResponse(line) {
    try {
      const response = JSON.parse(line);
      const pending = this.pendingRequests.get(response.id);

      if (pending) {
        clearTimeout(pending.timeout);
        this.pendingRequests.delete(response.id);

        if (response.error) {
          pending.reject(new Error(response.error.message));
        } else {
          pending.resolve(response.result);
        }
      }
    } catch (error) {
      console.error('Failed to parse response:', line);
    }
  }
}

module.exports = PythonBridge;
