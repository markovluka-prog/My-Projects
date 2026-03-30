import crypto from "crypto";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { BOOK_DIR, REPO_ROOT, buildSite } from "./build_site.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STATE_PATH = path.join(BOOK_DIR, ".agent-state.json");
const LOG_PREFIX = "[project-book-agent]";
const POLL_INTERVAL_MS = Number(process.env.PROJECT_BOOK_POLL_MS || 15000);
const WATCH_IGNORE_DIRS = new Set([".git", "Claude", "project-book", "node_modules", ".build"]);

async function walkForSignature(rootDir) {
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  const chunks = [];

  for (const entry of entries) {
    if (WATCH_IGNORE_DIRS.has(entry.name)) continue;
    const absolutePath = path.join(rootDir, entry.name);

    if (entry.isDirectory()) {
      chunks.push(await walkForSignature(absolutePath));
      continue;
    }

    const stat = await fs.stat(absolutePath);
    chunks.push(`${absolutePath}|${stat.size}|${Math.floor(stat.mtimeMs)}`);
  }

  return chunks.join("\n");
}

async function computeSignature() {
  const raw = await walkForSignature(REPO_ROOT);
  return crypto.createHash("sha1").update(raw).digest("hex");
}

function runNodeScript(scriptPath) {
  return new Promise((resolve, reject) => {
    const child = spawn("node", [scriptPath], {
      cwd: BOOK_DIR,
      stdio: "inherit"
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`Script failed: ${path.basename(scriptPath)} (${code})`));
    });
  });
}

async function writeState(state) {
  await fs.writeFile(STATE_PATH, JSON.stringify(state, null, 2), "utf8");
}

async function readState() {
  try {
    const value = await fs.readFile(STATE_PATH, "utf8");
    return JSON.parse(value);
  } catch {
    return { signature: "", lastBuildAt: "", status: "idle" };
  }
}

async function buildOnce(signature) {
  const startedAt = new Date().toISOString();
  console.log(`${LOG_PREFIX} rebuild started`);
  try {
    const site = await buildSite();
    await runNodeScript(path.join(__dirname, "generate_pdf.mjs"));
    const state = {
      signature,
      status: "ok",
      lastBuildAt: new Date().toISOString(),
      lastError: "",
      lastSiteSignature: site.signature
    };
    await writeState(state);
    console.log(`${LOG_PREFIX} rebuild finished`);
  } catch (error) {
    const state = {
      signature,
      status: "error",
      lastBuildAt: startedAt,
      lastError: error instanceof Error ? error.message : String(error)
    };
    await writeState(state);
    console.error(`${LOG_PREFIX} rebuild failed: ${state.lastError}`);
  }
}

export async function runAgent({ once = false } = {}) {
  console.log(`${LOG_PREFIX} started`);
  let state = await readState();
  let isBuilding = false;

  async function tick(force = false) {
    if (isBuilding) return;
    const signature = await computeSignature();
    if (!force && signature === state.signature) return;

    isBuilding = true;
    try {
      await buildOnce(signature);
      state = await readState();
    } finally {
      isBuilding = false;
    }
  }

  await tick(true);

  if (once) return;

  setInterval(() => {
    tick(false).catch((error) => {
      console.error(`${LOG_PREFIX} tick failed: ${error instanceof Error ? error.message : String(error)}`);
    });
  }, POLL_INTERVAL_MS);

  await new Promise(() => {});
}

const once = process.argv.includes("--once");
const isDirectRun = process.argv[1] && path.resolve(process.argv[1]) === __filename;
if (isDirectRun) {
  await runAgent({ once });
}
