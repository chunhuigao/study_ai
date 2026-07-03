const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('agentApi', {
  chat: (payload) => ipcRenderer.invoke('agent:chat', payload),
  getTokenUsage: () => ipcRenderer.invoke('agent:getTokenUsage'),
  getModels: () => ipcRenderer.invoke('agent:getModels'),
  switchModel: (modelId) => ipcRenderer.invoke('agent:switchModel', modelId),
  getSkills: () => ipcRenderer.invoke('agent:getSkills'),
  setSkillEnabled: (skillId, enabled) =>
    ipcRenderer.invoke('agent:setSkillEnabled', skillId, enabled),
  upsertSkill: (skill) => ipcRenderer.invoke('agent:upsertSkill', skill),
});
