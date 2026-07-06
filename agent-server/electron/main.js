import { app, BrowserWindow, ipcMain } from 'electron';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverDir = path.resolve(__dirname, '..');
const rootDir = path.resolve(serverDir, '..');
const webDistDir = path.join(rootDir, 'dist');

const isDev = process.env.NODE_ENV !== 'production';
const rendererUrl = process.env.VITE_DEV_SERVER_URL ?? 'http://127.0.0.1:5173';

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 920,
    minHeight: 640,
    title: 'AI RAG Learning',
    backgroundColor: '#f7f8fa',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    win.loadURL(rendererUrl);
  } else {
    win.loadFile(path.join(webDistDir, 'index.html'));
  }
}

function runPython(args, payload) {
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON ?? 'python3';
    const child = spawn(pythonCommand, [path.join(serverDir, 'agent_bridge.py'), ...args], {
      cwd: serverDir,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', (error) => {
      reject(new Error(`无法启动 Python: ${error.message}`));
    });
    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Python 进程异常退出，退出码 ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Python 返回了无法解析的结果: ${error.message}`));
      }
    });

    if (payload) {
      child.stdin.write(JSON.stringify(payload));
    }
    child.stdin.end();
  });
}

ipcMain.handle('rag:ingestPdf', async (_event, filePath) => {
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('PDF 文件路径无效');
  }
  return runPython(['--rag-ingest-pdf', filePath]);
});

ipcMain.handle('rag:query', async (_event, payload) => {
  return runPython(['--rag-query'], payload || {});
});

ipcMain.handle('rag:documents', async () => {
  return runPython(['--rag-documents']);
});

ipcMain.handle('rag:clear', async () => {
  return runPython(['--rag-clear']);
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

