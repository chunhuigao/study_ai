import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverDir = path.resolve(__dirname, '..');
const rootDir = path.resolve(serverDir, '..');
const webDistDir = path.join(rootDir, 'dist');

const isDev = process.env.NODE_ENV !== 'production';
const rendererUrl = process.env.VITE_DEV_SERVER_URL ?? 'http://127.0.0.1:5173';

function createWindow() {
  const win = new BrowserWindow({
    width: 1040,
    height: 760,
    minWidth: 760,
    minHeight: 560,
    title: 'Electron Agent',
    backgroundColor: '#f5f2eb',
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

function callAgent(payload) {
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON ?? 'python3';
    const child = spawn(
      pythonCommand,
      [path.join(serverDir, 'agent_bridge.py')],
      {
        cwd: serverDir,
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );

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
        reject(
          new Error(stderr.trim() || `Agent 进程异常退出，退出码 ${code}`),
        );
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Agent 返回了无法解析的结果: ${error.message}`));
      }
    });

    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}

function getTokenUsage() {
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON ?? 'python3';
    const child = spawn(
      pythonCommand,
      [path.join(serverDir, 'agent_bridge.py'), '--get-token-usage'],
      {
        cwd: serverDir,
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );

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
        reject(
          new Error(stderr.trim() || `获取 Token 用量失败，退出码 ${code}`),
        );
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`解析 Token 用量失败: ${error.message}`));
      }
    });
  });
}

ipcMain.handle('agent:chat', async (_event, payload) => {
  if (!payload || typeof payload !== 'object') {
    throw new Error('请求参数无效');
  }

  const messages = Array.isArray(payload.messages) ? payload.messages : [];
  const maxSteps = Number.isInteger(payload.maxSteps) ? payload.maxSteps : 100;

  return callAgent({ messages, maxSteps });
});

ipcMain.handle('agent:getTokenUsage', async () => {
  return getTokenUsage();
});

function runPythonCommand(args) {
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON ?? 'python3';
    const child = spawn(
      pythonCommand,
      [path.join(serverDir, 'agent_bridge.py'), ...args],
      {
        cwd: serverDir,
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );

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
        reject(new Error(stderr.trim() || `命令执行失败，退出码 ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`解析结果失败: ${error.message}`));
      }
    });
  });
}

ipcMain.handle('agent:getModels', async () => {
  return runPythonCommand(['--get-models']);
});

ipcMain.handle('agent:switchModel', async (_event, modelId) => {
  if (!modelId || typeof modelId !== 'string') {
    throw new Error('模型ID无效');
  }
  return runPythonCommand(['--switch-model', modelId]);
});

ipcMain.handle('agent:getSkills', async () => {
  return runPythonCommand(['--get-skills']);
});

ipcMain.handle('agent:setSkillEnabled', async (_event, skillId, enabled) => {
  if (!skillId || typeof skillId !== 'string') {
    throw new Error('skill id 无效');
  }
  return runPythonCommand([
    '--set-skill-enabled',
    skillId,
    enabled ? 'true' : 'false',
  ]);
});

ipcMain.handle('agent:upsertSkill', async (_event, skill) => {
  if (!skill || typeof skill !== 'object') {
    throw new Error('skill 配置无效');
  }
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON ?? 'python3';
    const child = spawn(
      pythonCommand,
      [path.join(serverDir, 'agent_bridge.py'), '--upsert-skill'],
      {
        cwd: serverDir,
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );

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
        reject(new Error(stderr.trim() || `保存 skill 失败，退出码 ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`解析 skill 结果失败: ${error.message}`));
      }
    });

    child.stdin.write(JSON.stringify(skill));
    child.stdin.end();
  });
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
