#!/usr/bin/env node
import { existsSync } from "node:fs";
import net from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn, spawnSync } from "node:child_process";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const serverDir = join(root, "agent-server");
const venvDir = join(serverDir, ".venv");
const venvPython = join(venvDir, "bin", "python");
const pnpm = process.env.PNPM || "pnpm";
const host = process.env.RELAY_HOST || "127.0.0.1";
const apiPort = process.env.RELAY_API_PORT || "8000";
const webPort = process.env.RELAY_WEB_PORT || "5173";

const children = new Set();

function log(message) {
  console.log(`\n[Relay] ${message}`);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "inherit",
    env: { ...process.env, CI: "true", ...options.env }
  });

  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function canRun(command, args = []) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "ignore",
    env: process.env
  });
  return result.status === 0;
}

function findPython() {
  const candidates = [process.env.PYTHON, "python3", "python"].filter(Boolean);
  for (const candidate of candidates) {
    if (canRun(candidate, ["--version"])) {
      return candidate;
    }
  }
  console.error("[Relay] 未找到 Python。请安装 Python 3.11+ 后重试。");
  process.exit(1);
}

function ensureBackend() {
  if (!existsSync(venvPython)) {
    log("创建后端虚拟环境 agent-server/.venv");
    run(findPython(), ["-m", "venv", venvDir]);
  }

  const depsReady = spawnSync(venvPython, ["-c", "import fastapi, uvicorn"], {
    cwd: root,
    stdio: "ignore"
  });

  if (depsReady.status !== 0) {
    log("安装后端依赖");
    run(venvPython, ["-m", "pip", "install", "-e", "agent-server"]);
  }
}

function ensureFrontend() {
  if (!existsSync(join(root, "node_modules"))) {
    log("安装前端依赖");
    run(pnpm, ["install"]);
  }
}

function findListener(port) {
  const result = spawnSync("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN"], {
    cwd: root,
    encoding: "utf8"
  });

  if (result.status !== 0 || !result.stdout.trim()) {
    return "";
  }

  return result.stdout
    .trim()
    .split("\n")
    .slice(1)
    .map((line) => line.trim().replace(/\s+/g, " "))
    .join("\n");
}

function assertPortFree(label, port) {
  return new Promise((resolvePort, rejectPort) => {
    const server = net.createServer();
    server.once("error", (error) => {
      if (error.code === "EADDRINUSE") {
        const listener = findListener(port);
        const detail = listener ? `\n占用进程:\n${listener}` : "";
        rejectPort(
          new Error(
            `${label}端口 ${port} 已被占用。${detail}\n\n` +
              `处理方式：\n` +
              `1. 停掉占用进程后重新运行 pnpm start\n` +
              `2. 或换端口运行：RELAY_API_PORT=8010 RELAY_WEB_PORT=5174 pnpm start`
          )
        );
        return;
      }
      rejectPort(error);
    });
    server.once("listening", () => {
      server.close(() => resolvePort());
    });
    server.listen(Number(port), host);
  });
}

function start(name, command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: options.cwd || root,
    stdio: "inherit",
    env: { ...process.env, ...options.env }
  });
  children.add(child);

  child.on("exit", (code, signal) => {
    children.delete(child);
    if (signal) {
      return;
    }
    if (code && code !== 0) {
      console.error(`[Relay] ${name} 已退出，状态码 ${code}`);
      shutdown(code);
    }
  });

  return child;
}

function shutdown(code = 0) {
  for (const child of children) {
    child.kill("SIGTERM");
  }
  process.exit(code);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

ensureBackend();
ensureFrontend();

try {
  await assertPortFree("后端", apiPort);
  await assertPortFree("前端", webPort);
} catch (error) {
  console.error(`\n[Relay] ${error.message}`);
  process.exit(1);
}

log(`后端: http://${host}:${apiPort}`);
log(`前端: http://${host}:${webPort}`);
log("按 Ctrl+C 停止所有服务");

start(
  "Relay API",
  venvPython,
  ["-m", "uvicorn", "relay.server:app", "--reload", "--host", host, "--port", apiPort],
  {
    cwd: root,
    env: { PYTHONPATH: serverDir }
  }
);

start("Relay Web", pnpm, ["exec", "vite", "--host", host, "--port", webPort, "--strictPort"]);
