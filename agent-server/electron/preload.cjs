const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('ragApi', {
  selectPdf: () => ipcRenderer.invoke('rag:selectPdf'),
  ingestPdf: (filePath) => ipcRenderer.invoke('rag:ingestPdf', filePath),
  query: (payload) => ipcRenderer.invoke('rag:query', payload),
  documents: () => ipcRenderer.invoke('rag:documents'),
  clear: () => ipcRenderer.invoke('rag:clear'),
});
