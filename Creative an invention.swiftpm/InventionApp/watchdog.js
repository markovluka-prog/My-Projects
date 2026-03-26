const { spawn } = require("child_process");

const APP_DIR = __dirname;
const SERVER_ENTRY = `${APP_DIR}/server.js`;
const APP_PING = "http://127.0.0.1:8000/api/ping";
const OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags";

let startingServer = false;
let startingOllama = false;

async function isAlive(url) {
  try {
    const response = await fetch(url, { method: "GET" });
    return response.ok;
  } catch (error) {
    return false;
  }
}

function spawnDetached(command, args, logName) {
  const child = spawn(command, args, {
    cwd: APP_DIR,
    detached: true,
    stdio: "ignore"
  });
  child.unref();
  console.log(`[watchdog] spawned ${logName}`);
}

async function ensureServer() {
  const alive = await isAlive(APP_PING);
  if (alive || startingServer) return;
  startingServer = true;
  try {
    spawnDetached("node", [SERVER_ENTRY], "server.js");
  } finally {
    setTimeout(() => {
      startingServer = false;
    }, 4000);
  }
}

async function ensureOllama() {
  const alive = await isAlive(OLLAMA_TAGS);
  if (alive || startingOllama) return;
  startingOllama = true;
  try {
    spawnDetached("ollama", ["serve"], "ollama serve");
  } finally {
    setTimeout(() => {
      startingOllama = false;
    }, 4000);
  }
}

async function tick() {
  await Promise.all([ensureServer(), ensureOllama()]);
}

console.log("[watchdog] started");
tick();
setInterval(tick, 5000);
