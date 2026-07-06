import { app, BrowserWindow } from "electron";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const isDev = Boolean(process.env.VITE_DEV_SERVER_URL);
const __dirname = dirname(fileURLToPath(import.meta.url));

function createWindow() {
  const window = new BrowserWindow({
    width: 1120,
    height: 760,
    minWidth: 920,
    minHeight: 620,
    title: "Relay",
    backgroundColor: "#f7f3ea",
    webPreferences: {
      preload: join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev && process.env.VITE_DEV_SERVER_URL) {
    window.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    window.loadFile(join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
