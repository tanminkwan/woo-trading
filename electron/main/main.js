const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const PythonBridge = require('./python-bridge');

// 개발 모드 확인
const isDev = !app.isPackaged;
// Vite 개발 서버 사용 여부 (NODE_ENV=development 시에만)
const useDevServer = process.env.NODE_ENV === 'development';

let mainWindow = null;
let pythonBridge = null;

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

  mainWindow.on('closed', () => {
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

// 앱 시작
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
  if (pythonBridge) {
    await pythonBridge.stop();
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 앱 종료 전 정리
app.on('before-quit', async () => {
  if (pythonBridge) {
    await pythonBridge.stop();
  }
});
