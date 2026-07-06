const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('ragApi', {
  ingestPdf: (filePath) => ipcRenderer.invoke('rag:ingestPdf', filePath),
  query: (payload) => ipcRenderer.invoke('rag:query', payload),
  documents: () => ipcRenderer.invoke('rag:documents'),
  clear: () => ipcRenderer.invoke('rag:clear'),
});

