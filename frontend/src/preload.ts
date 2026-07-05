import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("relayShell", {
  platform: process.platform
});

