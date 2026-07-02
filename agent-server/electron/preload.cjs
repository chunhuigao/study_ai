const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('agentApi', {
  chat: (payload) => ipcRenderer.invoke('agent:chat', payload),
  getTokenUsage: () => ipcRenderer.invoke('agent:getTokenUsage'),
});
