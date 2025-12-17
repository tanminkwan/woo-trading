const { contextBridge, ipcRenderer } = require('electron');

// Renderer 프로세스에서 사용할 API 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // Python RPC 호출
  pythonRpc: (method, params) => ipcRenderer.invoke('python-rpc', method, params),

  // 앱 정보
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // 엔진 관련 API
  engine: {
    start: () => ipcRenderer.invoke('python-rpc', 'engine.start', {}),
    stop: () => ipcRenderer.invoke('python-rpc', 'engine.stop', {}),
    pause: () => ipcRenderer.invoke('python-rpc', 'engine.pause', {}),
    resume: () => ipcRenderer.invoke('python-rpc', 'engine.resume', {}),
    getStatus: () => ipcRenderer.invoke('python-rpc', 'engine.status', {}),
  },

  // 종목 관련 API
  stocks: {
    list: () => ipcRenderer.invoke('python-rpc', 'stocks.list', {}),
    add: (stock) => ipcRenderer.invoke('python-rpc', 'stocks.add', stock),
    update: (code, data) => ipcRenderer.invoke('python-rpc', 'stocks.update', { code, ...data }),
    delete: (code) => ipcRenderer.invoke('python-rpc', 'stocks.delete', { code }),
    toggle: (code) => ipcRenderer.invoke('python-rpc', 'stocks.toggle', { code }),
  },

  // 로그 관련 API
  logs: {
    get: (limit) => ipcRenderer.invoke('python-rpc', 'logs.get', { limit: limit || 100 }),
  },

  // 백테스트 관련 API
  backtest: {
    run: (params) => ipcRenderer.invoke('python-rpc', 'backtest.run', params),
  },

  // 설정 관련 API
  config: {
    get: () => ipcRenderer.invoke('python-rpc', 'config.get', {}),
    save: (config) => ipcRenderer.invoke('python-rpc', 'config.save', config),
    reload: () => ipcRenderer.invoke('python-rpc', 'config.reload', {}),
  },
});
