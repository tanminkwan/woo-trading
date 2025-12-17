const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const PythonBridge = require('./python-bridge');

// 개발 모드 확인
const isDev = !app.isPackaged;
// Vite 개발 서버 사용 여부 (패키지되지 않았으면 개발 서버 사용)
const useDevServer = isDev;

let mainWindow = null;
let pythonBridge = null;

// ============ 중복 실행 방지 ============
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  // 이미 실행 중인 인스턴스가 있으면 종료
  app.quit();
} else {
  // 두 번째 인스턴스 실행 시도 시 기존 창 활성화
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.focus();
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: 'AutoStock - 자동매매 시스템',
    show: false,
  });

  // Vite 개발 서버 또는 빌드된 파일 로드
  if (useDevServer) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/dist/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // 창 닫기 시 백엔드도 종료
  mainWindow.on('closed', async () => {
    await stopPythonBackend();
    mainWindow = null;
  });
}

// Python 백엔드 시작
async function startPythonBackend() {
  pythonBridge = new PythonBridge(isDev);

  try {
    await pythonBridge.start();
    console.log('Python backend started successfully');
  } catch (error) {
    console.error('Failed to start Python backend:', error);
  }
}

// Python 백엔드 종료
async function stopPythonBackend() {
  if (pythonBridge) {
    console.log('Stopping Python backend...');
    try {
      await pythonBridge.stop();
      console.log('Python backend stopped');
    } catch (error) {
      console.error('Error stopping Python backend:', error);
    }
    pythonBridge = null;
  }
}

// IPC 핸들러 설정
function setupIpcHandlers() {
  // Python RPC 호출
  ipcMain.handle('python-rpc', async (event, method, params) => {
    if (!pythonBridge) {
      throw new Error('Python backend not initialized');
    }
    return await pythonBridge.call(method, params);
  });

  // 앱 정보
  ipcMain.handle('get-app-info', () => {
    return {
      version: app.getVersion(),
      isDev: isDev,
    };
  });
}

// 앱 시작 (중복 실행이 아닌 경우에만)
if (gotTheLock) {
  app.whenReady().then(async () => {
    setupIpcHandlers();
    await startPythonBackend();
    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });

  // 모든 창이 닫히면 앱 종료
  app.on('window-all-closed', async () => {
    await stopPythonBackend();

    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  // 앱 종료 전 정리
  app.on('before-quit', async () => {
    await stopPythonBackend();
  });
}
