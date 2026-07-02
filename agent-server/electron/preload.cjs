const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('agentApi', {
  chat: (payload) => ipcRenderer.invoke('agent:chat', payload)
});
