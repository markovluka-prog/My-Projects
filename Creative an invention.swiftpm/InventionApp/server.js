const http = require("http");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const { exec } = require("child_process");
const { promisify } = require("util");

const execAsync = promisify(exec);

const HOST = "0.0.0.0";
const PORT = Number(process.env.PORT || 8000);
const ROOT = __dirname;
const WORKSPACE_ROOT = "/workspaces/My-Projects";
const OLLAMA_URL = process.env.OLLAMA_URL || "http://127.0.0.1:11434";
const FAST_MODEL = process.env.OLLAMA_FAST_MODEL || "qwen2.5-coder:0.5b";
const APP_VERSION = "two-mode-v1";
let lastOllamaStartAttemptAt = 0;

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico": "image/x-icon",
  ".md": "text/markdown; charset=utf-8"
};

const MEMORY_PROMPT = `
Ты Лука AI. Это агентный системный промпт.

Твоя роль:
- Ты локальный агент по проектам, коду, файлам, исследованиям и веб-поиску.
- Ты не играешь персонажа и не болтаешь без пользы.
- Ты отвечаешь только по-русски.
- Твой стиль: краткий, прямой, полезный, без воды.

Память пользователя:
- Имя пользователя: Лука
- Стиль общения пользователя: краткий и прямой
- Рабочая директория в этой среде: ${WORKSPACE_ROOT}

Главные правила поведения:
- Сначала думай о том, что реально хочет пользователь, а не о красивом ответе.
- Если пользователь просит что-то сделать с кодом, файлами, папками, командой, сайтом или поиском, используй инструменты.
- Не перекладывай на пользователя то, что можно выяснить инструментами.
- Не задавай лишние вопросы, если разумное следующее действие очевидно.
- Если контекста мало, собери его сам инструментами, а потом отвечай.
- Если задача многошаговая, действуй как агент: анализируй, используй инструмент, оценивай результат, завершай.
- Если пользователь исправляет тебя, не спорь и не оправдывайся, а скорректируй действие или ответ.
- Если пользователь просит строковую операцию, преобразование текста, счёт, повтор, сравнение или короткую утилитарную вещь, отвечай точно и буквально.
- Если пользователь спрашивает о проекте, опирайся на переданный проектный контекст, а не выдумывай.
- Не используй канцелярит, маркетинговый стиль и шаблонные вступления.

Запреты:
- Не упоминай Anthropic, Alibaba, OpenAI или происхождение модели.
- Не говори "Как я могу помочь?" без необходимости.
- Не повторяй вопрос пользователя вместо ответа.
- Не добавляй вежливую болтовню, если можно ответить одной полезной фразой.
- Не придумывай факты о файлах, коде, проектах или интернете, если их можно проверить инструментами.

Как отвечать:
- Если можно ответить сразу и точно, дай короткий финальный ответ.
- Если нужен инструмент, вызови ровно один инструмент за ответ.
- После результата инструмента либо дай финальный ответ, либо вызови следующий нужный инструмент.
- В финальном ответе не описывай внутренний chain-of-thought.
- Когда уместно, давай сжатый результат, а не длинный пересказ.

Доступные инструменты:
- list_dir(path)
- read_file(path)
- write_file(path, content)
- mkdir(path)
- run_command(command)
- web_search(query)
- fetch_url(url)

Формат вывода:
- Всегда возвращай только JSON.
- Допустимы только два формата:
  {"type":"final","message":"..."}
  {"type":"tool","tool":"read_file","args":{"path":"..."},"reason":"..."}
- Никакого текста вне JSON.
- За один ответ максимум один вызов инструмента.
`;

const FAST_PROMPT = `
Ты Лука AI. Это системный промпт для быстрых смысловых ответов.

Личность и стиль:
- Отвечай только по-русски.
- Пиши кратко, прямо и по делу.
- Без канцелярита, без лишней вежливости, без шаблонных вступлений.
- Не пиши "Как я могу помочь?" без необходимости.
- Не повторяй вопрос пользователя вместо ответа.
- Не растягивай ответ, если можно сказать короче.

Память пользователя:
- Имя пользователя: Лука
- Стиль общения пользователя: краткий и прямой

Твоя роль:
- Ты локальный помощник по проектам, коду и исследованиям.
- Ты помогаешь думать, формулировать, объяснять, структурировать и уточнять.
- Ты не должен звучать как саппорт-бот.

Правила качества ответа:
- Если вопрос простой, отвечай просто.
- Если вопрос о пользователе, используй память.
- Если вопрос о проекте, используй проектный контекст.
- Если вопрос о смысле проекта, опиши проект своими словами в 1-2 фразах.
- Если вопрос просит буквальное преобразование текста, следуй формулировке буквально.
- Если ответ должен быть точным, не уходи в рассуждения.
- Если данных мало, задай один полезный уточняющий вопрос.
- Если пользователь исправляет тебя, исправься, а не объясняй прошлый ответ.

Факты памяти:
- Если спрашивают "Как меня зовут?" или эквивалент, правильный ответ: "Тебя зовут Лука."
- Если спрашивают "Кто ты?", отвечай: "Я Лука AI, локальный помощник по проектам, коду и исследованиям."

Запреты:
- Не упоминай Anthropic, Alibaba, OpenAI или происхождение модели.
- Не выдавай общие бот-фразы.
- Не отвечай одним словом, если нужен смысловой ответ.
- Не придумывай контекст, которого нет.
`.trim();

const ROUTER_PROMPT = `
Ты выбираешь режим обработки сообщения.
Отвечай только одним словом:
- fast: обычный разговор, объяснение, идеи, план, вопрос без инструментов
- direct: один очевидный инструмент, например прочитать файл, показать папку, поиск в интернете
- agent: сложная задача на код, редактирование файлов, несколько шагов, команды, исследование с инструментами
Никаких пояснений.
`.trim();

const SKILLS = {
  thinking: `
Thinking skill:
- Сначала молча разберись, что именно хочет пользователь.
- Разделяй факты, допущения и недостающий контекст.
- Если ответ может получиться шаблонным, переформулируй его в более точный.
- Если задача короткая, думай коротко; если сложная, разбей на части.
- Не показывай внутренние рассуждения полностью, показывай только полезный итог.
`.trim(),
  planning: `
Planning skill:
- Если пользователь просит план, стратегию, порядок действий или пошаговую проработку, отвечай структурно.
- Строй план от ближайшего шага к дальнему.
- Обычно давай 3-7 шагов.
- Для проектных задач делай план практичным: что сделать сейчас, что проверить, что отложить.
- Для coding-задач сначала составь краткий план, потом действуй.
`.trim(),
  editing: `
Editing skill:
- Если пользователь хочет исправить, переписать, дополнить или заполнить, сначала определи точный объект правки.
- Если можно править по имеющемуся контексту, правь уверенно.
- Если контекста не хватает, запроси или собери только минимум нужных данных.
- Не путай команду "исправь" с новым описанием проекта.
`.trim(),
  project_summary: `
Project summary skill:
- Если вопрос о проекте, опирайся на project context.
- Кратко пересказывай смысл проекта своими словами.
- Отличай описание, проблему, идею, аудиторию и статус.
- Если данных мало, честно скажи, чего не хватает.
`.trim(),
  patent: `
Patent skill:
- Если речь о патенте, новизне, аналогах, формуле или заявке, отвечай более строго и предметно.
- Отделяй идею, отличие от аналогов и потенциальные признаки формулы.
- Не выдумывай официальные патентные формулировки без опоры на контекст.
`.trim(),
  coding: `
Coding skill:
- Если задача связана с кодом, анализируй как инженер.
- Сначала пойми цель, потом найди нужный файл, затем меняй только то, что нужно.
- При возможности проверяй результат.
- Не отвечай общими словами там, где нужен конкретный технический вывод.
`.trim(),
  memory: `
Memory skill:
- Используй память о пользователе и проекте как факты.
- Если пользователь спрашивает о себе, опирайся на memory.
- Не путай имя пользователя и имя ассистента.
`.trim()
};

function selectSkills(message = "") {
  const text = normalizeText(message);
  const skillNames = ["thinking", "memory"];

  if (
    text.includes("план") ||
    text.includes("спланируй") ||
    text.includes("planning") ||
    text.includes("пошаг") ||
    text.includes("шаг за шагом") ||
    text.includes("roadmap")
  ) {
    skillNames.push("planning");
  }

  if (
    text.includes("исправь") ||
    text.includes("заполни") ||
    text.includes("перепиши") ||
    text.includes("отредактируй") ||
    text.includes("дополни")
  ) {
    skillNames.push("editing");
  }

  if (
    text.includes("проект") ||
    text.includes("сводк") ||
    text.includes("о чем") ||
    text.includes("какой проект") ||
    text.includes("описание")
  ) {
    skillNames.push("project_summary");
  }

  if (
    text.includes("патент") ||
    text.includes("аналог") ||
    text.includes("новизн") ||
    text.includes("формул")
  ) {
    skillNames.push("patent");
  }

  if (
    text.includes("код") ||
    text.includes("html") ||
    text.includes("js") ||
    text.includes("swift") ||
    text.includes("server.js") ||
    text.includes("index.html") ||
    text.includes("программ")
  ) {
    skillNames.push("coding");
  }

  return [...new Set(skillNames)];
}

function buildSkillContext(message = "") {
  return selectSkills(message)
    .map((name) => `[${name}]\n${SKILLS[name]}`)
    .join("\n\n");
}

function sendJson(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store"
  });
  res.end(body);
}

function startEventStream(res) {
  res.writeHead(200, {
    "Content-Type": "application/x-ndjson; charset=utf-8",
    "Cache-Control": "no-store",
    "Connection": "keep-alive"
  });
}

function sendStreamEvent(res, event) {
  res.write(`${JSON.stringify(event)}\n`);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 8 * 1024 * 1024) {
        reject(new Error("Request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function safeJoin(root, requestPath) {
  const normalized = path.normalize(requestPath).replace(/^(\.\.[/\\])+/, "");
  const fullPath = path.join(root, normalized);
  if (!fullPath.startsWith(root)) {
    return null;
  }
  return fullPath;
}

function resolveWorkspacePath(inputPath = ".") {
  const raw = decodeURIComponent(String(inputPath || ".").trim());
  const base = path.isAbsolute(raw) ? raw : path.join(WORKSPACE_ROOT, raw);
  const fullPath = path.resolve(base);
  if (!fullPath.startsWith(path.resolve(WORKSPACE_ROOT))) {
    throw new Error("Path is outside workspace root");
  }
  return fullPath;
}

function toWorkspaceRelative(targetPath) {
  const relative = path.relative(WORKSPACE_ROOT, targetPath).replace(/\\/g, "/");
  return relative || ".";
}

function runCommandCaptured(command, cwd = WORKSPACE_ROOT) {
  return new Promise((resolve) => {
    exec(command, {
      cwd,
      timeout: 15000,
      maxBuffer: 1024 * 1024
    }, (error, stdout, stderr) => {
      resolve({
        command,
        cwd,
        stdout: String(stdout || "").slice(0, 20000),
        stderr: String(stderr || "").slice(0, 20000),
        code: error && Number.isInteger(error.code) ? error.code : 0
      });
    });
  });
}

async function listDirTool(args) {
  const targetPath = resolveWorkspacePath(args.path || ".");
  const entries = await fsp.readdir(targetPath, { withFileTypes: true });
  return entries
    .slice(0, 200)
    .map((entry) => ({
      name: entry.name,
      type: entry.isDirectory() ? "dir" : "file"
    }));
}

async function readFileTool(args) {
  const targetPath = resolveWorkspacePath(args.path);
  const content = await fsp.readFile(targetPath, "utf8");
  return {
    path: targetPath,
    content
  };
}

async function writeFileTool(args) {
  const targetPath = resolveWorkspacePath(args.path);
  await fsp.mkdir(path.dirname(targetPath), { recursive: true });
  await fsp.writeFile(targetPath, String(args.content || ""), "utf8");
  return {
    path: targetPath,
    bytes: Buffer.byteLength(String(args.content || ""))
  };
}

async function mkdirTool(args) {
  const targetPath = resolveWorkspacePath(args.path);
  await fsp.mkdir(targetPath, { recursive: true });
  return { path: targetPath };
}

async function runCommandTool(args) {
  const command = String(args.command || "").trim();
  if (!command) {
    throw new Error("command is required");
  }
  const { stdout, stderr } = await execAsync(command, {
    cwd: WORKSPACE_ROOT,
    timeout: 8000,
    maxBuffer: 1024 * 1024
  });
  return {
    command,
    stdout: stdout.slice(0, 12000),
    stderr: stderr.slice(0, 12000)
  };
}

function stripHtml(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function webSearchTool(args) {
  const query = String(args.query || "").trim();
  if (!query) {
    throw new Error("query is required");
  }
  const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  const response = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0"
    }
  });
  const html = await response.text();
  const results = [];
  const regex = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = regex.exec(html)) && results.length < 5) {
    results.push({
      title: stripHtml(match[2]),
      url: match[1]
    });
  }
  return { query, results };
}

async function fetchUrlTool(args) {
  const url = String(args.url || "").trim();
  if (!url) {
    throw new Error("url is required");
  }
  let text = "";
  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0"
      }
    });
    text = await response.text();
  } catch (error) {
    const { stdout } = await execAsync(`curl -L --max-time 15 ${JSON.stringify(url)}`, {
      cwd: WORKSPACE_ROOT,
      timeout: 17000,
      maxBuffer: 1024 * 1024
    });
    text = stdout;
  }
  return {
    url,
    content: stripHtml(text).slice(0, 12000)
  };
}

const TOOLS = {
  list_dir: listDirTool,
  read_file: readFileTool,
  write_file: writeFileTool,
  mkdir: mkdirTool,
  run_command: runCommandTool,
  web_search: webSearchTool,
  fetch_url: fetchUrlTool
};

async function serveStatic(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const requestPath = requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname;
  const filePath = safeJoin(ROOT, requestPath);

  if (!filePath) {
    sendJson(res, 403, { error: "Forbidden" });
    return;
  }

  fs.stat(filePath, (statError, stat) => {
    if (statError || !stat.isFile()) {
      sendJson(res, 404, { error: "Not found" });
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const stream = fs.createReadStream(filePath);
    res.writeHead(200, {
      "Content-Type": MIME_TYPES[ext] || "application/octet-stream",
      "Cache-Control": "no-store"
    });
    stream.pipe(res);
    stream.on("error", () => {
      if (!res.headersSent) {
        sendJson(res, 500, { error: "Failed to read file" });
      } else {
        res.destroy();
      }
    });
  });
}

async function handleWorkspaceList(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const targetPath = resolveWorkspacePath(requestUrl.searchParams.get("path") || ".");
  const entries = await fsp.readdir(targetPath, { withFileTypes: true });
  const mapped = await Promise.all(entries.slice(0, 400).map(async (entry) => {
    const fullPath = path.join(targetPath, entry.name);
    let size = 0;
    try {
      const stat = await fsp.stat(fullPath);
      size = stat.size;
    } catch (error) {
      size = 0;
    }
    return {
      name: entry.name,
      type: entry.isDirectory() ? "dir" : "file",
      path: toWorkspaceRelative(fullPath),
      size
    };
  }));
  sendJson(res, 200, {
    path: toWorkspaceRelative(targetPath),
    entries: mapped
  });
}

async function handleWorkspaceFile(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const targetPath = resolveWorkspacePath(requestUrl.searchParams.get("path") || ".");
  const stat = await fsp.stat(targetPath);
  if (!stat.isFile()) {
    sendJson(res, 400, { error: "Path is not a file" });
    return;
  }
  const content = await fsp.readFile(targetPath, "utf8");
  sendJson(res, 200, {
    path: toWorkspaceRelative(targetPath),
    content,
    size: stat.size
  });
}

async function handleWorkspaceRaw(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const targetPath = resolveWorkspacePath(requestUrl.searchParams.get("path") || ".");
  const stat = await fsp.stat(targetPath);
  if (!stat.isFile()) {
    sendJson(res, 400, { error: "Path is not a file" });
    return;
  }
  const ext = path.extname(targetPath).toLowerCase();
  res.writeHead(200, {
    "Content-Type": MIME_TYPES[ext] || "application/octet-stream",
    "Cache-Control": "no-store"
  });
  fs.createReadStream(targetPath).pipe(res);
}

async function handleWorkspaceWrite(req, res) {
  const body = JSON.parse(await readBody(req) || "{}");
  const targetPath = resolveWorkspacePath(body.path || ".");
  await fsp.mkdir(path.dirname(targetPath), { recursive: true });
  const content = String(body.content || "");
  await fsp.writeFile(targetPath, content, "utf8");
  sendJson(res, 200, {
    ok: true,
    path: toWorkspaceRelative(targetPath),
    bytes: Buffer.byteLength(content)
  });
}

async function handleWorkspaceRun(req, res) {
  const body = JSON.parse(await readBody(req) || "{}");
  const command = String(body.command || "").trim();
  const cwd = resolveWorkspacePath(body.cwd || ".");
  if (!command) {
    sendJson(res, 400, { error: "command is required" });
    return;
  }
  const result = await runCommandCaptured(command, cwd);
  sendJson(res, 200, result);
}

async function maybeReadText(targetPath) {
  try {
    return await fsp.readFile(targetPath, "utf8");
  } catch (error) {
    return "";
  }
}

function inferBootstrapField(name, files) {
  if (name.endsWith(".swiftpm") || files.includes("Package.swift")) return "Приложение";
  if (files.includes("concept.md")) return "Изобретение";
  if (files.includes("theory.md")) return "Теория";
  return "Проект";
}

function inferBootstrapStatus(text) {
  const raw = String(text || "").toLowerCase();
  if (raw.includes("готов")) return "ready";
  if (raw.includes("тест")) return "test";
  if (raw.includes("разработ")) return "dev";
  if (raw.includes("пауза")) return "paused";
  return "idea";
}

function stripMarkdown(text = "") {
  return String(text || "")
    .replace(/^#+\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^\s*-\s+/gm, "")
    .trim();
}

function shortText(text = "", maxLength = 220) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength - 1).trim()}…`;
}

function extractMarkdownSection(text, headings) {
  const lines = String(text || "").split(/\r?\n/);
  const normalized = headings.map((item) => String(item || "").toLowerCase().replace(/ё/g, "е"));
  let collecting = false;
  const buffer = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (/^##+\s+/.test(trimmed)) {
      const heading = trimmed.replace(/^##+\s+/, "").toLowerCase().replace(/ё/g, "е");
      if (collecting) break;
      if (normalized.some((item) => heading.includes(item))) {
        collecting = true;
        continue;
      }
    }
    if (collecting) buffer.push(line);
  }

  return stripMarkdown(buffer.join("\n")).trim();
}

function parseCheckboxSteps(text) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.match(/^\s*-\s*\[( |x)\]\s*(.+)$/i))
    .filter(Boolean)
    .map((match) => ({
      name: match[2].trim(),
      done: match[1].toLowerCase() === "x"
    }));
}

function inferAudience(text = "", field = "") {
  const raw = stripMarkdown(text).toLowerCase();
  if (raw.includes("ребен") || raw.includes("дет")) {
    return "Дети, которым нравится придумывать свои формы и сценарии игры.";
  }
  if (raw.includes("семьи") || raw.includes("друз")) {
    return "Семьи и компании друзей.";
  }
  if (String(field || "").toLowerCase().includes("прилож")) {
    return "Пользователи приложения.";
  }
  return "";
}

function firstNonHeadingParagraph(text = "") {
  const lines = String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  for (const line of lines) {
    if (!line.startsWith("#") && !line.startsWith("|") && !line.startsWith("- ") && !/^\d+\./.test(line)) {
      return stripMarkdown(line);
    }
  }
  return "";
}

async function handleBootstrapProjects(req, res) {
  const entries = await fsp.readdir(WORKSPACE_ROOT, { withFileTypes: true });
  const folders = entries.filter((entry) => entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "Claude");
  const projects = [];

  for (const folder of folders) {
    const fullPath = path.join(WORKSPACE_ROOT, folder.name);
    const childEntries = await fsp.readdir(fullPath, { withFileTypes: true }).catch(() => []);
    const fileNames = childEntries.filter((entry) => entry.isFile()).map((entry) => entry.name);
    const looksLikeProject =
      folder.name.endsWith(".swiftpm") ||
      fileNames.includes("info.md") ||
      fileNames.includes("context.md") ||
      fileNames.includes("concept.md") ||
      fileNames.includes("theory.md") ||
      fileNames.includes("Package.swift");

    if (!looksLikeProject) continue;

    const infoText = await maybeReadText(path.join(fullPath, "info.md"));
    const contextText = await maybeReadText(path.join(fullPath, "context.md"));
    const conceptText = await maybeReadText(path.join(fullPath, "concept.md"));
    const theoryText = await maybeReadText(path.join(fullPath, "theory.md"));
    const sourceText = infoText || conceptText || theoryText || contextText;
    const lines = sourceText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const desc = (lines.find((line) => !line.startsWith("#") && !line.startsWith("-")) || "").slice(0, 180);

    projects.push({
      name: folder.name.replace(/\.swiftpm$/, ""),
      path: toWorkspaceRelative(fullPath),
      field: inferBootstrapField(folder.name, fileNames),
      status: inferBootstrapStatus(`${infoText}\n${contextText}`),
      desc: desc || `Проект из папки ${folder.name}`,
      files: fileNames
    });
  }

  sendJson(res, 200, { projects });
}

async function handleProjectData(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const projectPath = requestUrl.searchParams.get("path") || "";
  if (!projectPath) {
    sendJson(res, 400, { error: "path is required" });
    return;
  }

  const fullPath = resolveWorkspacePath(projectPath);
  const childEntries = await fsp.readdir(fullPath, { withFileTypes: true }).catch(() => []);
  const fileNames = childEntries.filter((entry) => entry.isFile()).map((entry) => entry.name);

  const infoText = await maybeReadText(path.join(fullPath, "info.md"));
  const contextText = await maybeReadText(path.join(fullPath, "context.md"));
  const conceptText = await maybeReadText(path.join(fullPath, "concept.md"));
  const patentText = await maybeReadText(path.join(fullPath, "patent.md"));
  const theoryText = await maybeReadText(path.join(fullPath, "theory.md"));
  const roadmapText = await maybeReadText(path.join(fullPath, "roadmap.md"));
  const descriptionText = await maybeReadText(path.join(fullPath, "description.md"));

  const sourceText = infoText || conceptText || theoryText || contextText;
  const lines = sourceText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const projectType = inferBootstrapField(path.basename(fullPath), fileNames);
  const desc =
    extractMarkdownSection(infoText, ["description", "описание"]) ||
    extractMarkdownSection(descriptionText, ["что это", "описание"]) ||
    shortText(stripMarkdown(descriptionText || sourceText), 220) ||
    (lines.find((line) => !line.startsWith("#") && !line.startsWith("-")) || "").slice(0, 220);

  const concept = {
    problem: extractMarkdownSection(conceptText, ["проблема"]) || extractMarkdownSection(theoryText, ["проблема"]) || "",
    idea:
      extractMarkdownSection(conceptText, ["идея"]) ||
      extractMarkdownSection(descriptionText, ["что это"]) ||
      extractMarkdownSection(infoText, ["description", "описание"]) ||
      shortText(stripMarkdown(theoryText.split("---")[0] || theoryText), 260) ||
      firstNonHeadingParagraph(descriptionText) ||
      "",
    howItWorks:
      extractMarkdownSection(conceptText, ["принцип", "как устроено", "как это работает"]) ||
      extractMarkdownSection(descriptionText, ["как работает"]) ||
      extractMarkdownSection(theoryText, ["как устроено", "как работает"]) ||
      "",
    uniqueness: extractMarkdownSection(conceptText, ["уникальность"]) || "",
    analogs: extractMarkdownSection(conceptText, ["аналоги"]) || "",
    audience:
      extractMarkdownSection(conceptText, ["аудитория", "пользователь"]) ||
      extractMarkdownSection(infoText, ["audience", "target users", "пользователи"]) ||
      inferAudience(`${conceptText}\n${descriptionText}\n${infoText}\n${contextText}`, projectType)
  };

  const ipcMatches = stripMarkdown(patentText).match(/[A-H]\d{2}[A-Z]?\s*\d+\/\d+/g) || [];
  const patent = {
    abstract: extractMarkdownSection(patentText, ["реферат", "заметки"]) || "",
    claims: extractMarkdownSection(patentText, ["формула"]) || "",
    description: extractMarkdownSection(patentText, ["описание", "ключевые отличия от аналогов"]) || "",
    ipcClasses: [...new Set(ipcMatches)].join(", "),
    steps: parseCheckboxSteps(patentText)
  };

  const tasks = String(roadmapText || "")
    .split(/\r?\n/)
    .map((line) => stripMarkdown(line).trim())
    .filter((line) => line && !line.startsWith("#"))
    .slice(0, 10)
    .map((text, index) => ({
      id: `task-${index + 1}`,
      text,
      done: false
    }));

  const notes = [
    contextText ? `context.md: ${shortText(stripMarkdown(contextText), 1000)}` : "",
    descriptionText ? `description.md: ${shortText(stripMarkdown(descriptionText), 1000)}` : ""
  ]
    .filter(Boolean)
    .map((text, index) => ({
      id: `note-${index + 1}`,
      text,
      at: new Date().toISOString()
    }));

  sendJson(res, 200, {
    path: projectPath,
    desc: desc || `Проект из папки ${path.basename(fullPath)}`,
    field: projectType,
    status: inferBootstrapStatus(`${infoText}\n${contextText}`),
    concept,
    patent,
    tasks,
    notes,
    files: fileNames
  });
}

async function ollamaAvailable() {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`);
    if (!response.ok) return { ok: false, modelReady: false, models: [] };
    const data = await response.json();
    const models = Array.isArray(data.models) ? data.models : [];
    const modelNames = models.map((item) => item.name);
    return {
      ok: true,
      modelReady: modelNames.includes(FAST_MODEL),
      models,
      modelNames
    };
  } catch (error) {
    return { ok: false, modelReady: false, models: [], modelNames: [], error: error.message };
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function tryStartOllamaServer() {
  const now = Date.now();
  if (now - lastOllamaStartAttemptAt < 5000) {
    return false;
  }
  lastOllamaStartAttemptAt = now;

  try {
    await execAsync("command -v ollama", {
      cwd: WORKSPACE_ROOT,
      timeout: 2000
    });
  } catch (error) {
    return false;
  }

  try {
    await execAsync("nohup ollama serve >/tmp/ollama_autostart.log 2>&1 &", {
      cwd: WORKSPACE_ROOT,
      timeout: 2000
    });
  } catch (error) {
    return false;
  }

  for (let attempt = 0; attempt < 6; attempt += 1) {
    await sleep(500);
    const availability = await ollamaAvailable();
    if (availability.ok) {
      return true;
    }
  }

  return false;
}

function shortText(value, max = 1200) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, max);
}

function normalizeText(value = "") {
  return String(value || "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/\s+/g, " ")
    .trim();
}

function summarizeProject(project) {
  if (!project) return null;
  return {
    name: project.name || "",
    status: project.status || "",
    field: project.field || "",
    activeTab: project.activeTab || "",
    desc: shortText(project.desc || "", 300),
    concept: {
      problem: shortText(project.concept?.problem || "", 200),
      idea: shortText(project.concept?.idea || "", 200),
      howItWorks: shortText(project.concept?.howItWorks || "", 200),
      uniqueness: shortText(project.concept?.uniqueness || "", 160)
    },
    notesCount: Array.isArray(project.notes) ? project.notes.length : 0,
    tasksCount: Array.isArray(project.tasks) ? project.tasks.length : 0
  };
}

function projectSummaryText(project) {
  if (!project) return "Проект не выбран.";
  const bits = [
    project.name ? `Название: ${project.name}.` : "",
    project.status ? `Статус: ${project.status}.` : "",
    project.field ? `Категория: ${project.field}.` : "",
    project.desc ? `Описание: ${shortText(project.desc, 160)}.` : "",
    project.concept?.problem ? `Проблема: ${shortText(project.concept.problem, 160)}.` : "",
    project.concept?.idea ? `Идея: ${shortText(project.concept.idea, 160)}.` : "",
    project.concept?.audience ? `Аудитория: ${shortText(project.concept.audience, 120)}.` : ""
  ].filter(Boolean);
  return bits.join(" ");
}

function describeProject(project) {
  if (!project) {
    return "Сейчас активный проект не выбран.";
  }

  const idea = shortText(project.concept?.idea || "", 220);
  const problem = shortText(project.concept?.problem || "", 220);
  const desc = shortText(project.desc || "", 220);
  const audience = shortText(project.concept?.audience || "", 140);
  const clean = (value) =>
    String(value || "")
      .replace(/^это\s+/i, "")
      .replace(/^проект\s+/i, "")
      .trim();
  const cleanIdea = clean(idea);
  const cleanProblem = clean(problem);

  if (desc) return desc;
  if (cleanIdea && cleanProblem) {
    if (cleanIdea.toLowerCase().includes(cleanProblem.toLowerCase().slice(0, 40))) {
      return `${project.name} — ${cleanIdea}.`;
    }
    return `${project.name} — ${cleanIdea}. Он нужен, чтобы решить проблему: ${cleanProblem}.`;
  }
  if (cleanIdea) return `${project.name} — ${cleanIdea}.`;
  if (cleanProblem) return `${project.name} — проект, который решает задачу: ${cleanProblem}.`;
  if (audience) return `${project.name} — проект для ${audience}.`;
  return `${project.name} — проект, по которому пока мало заполненных данных.`;
}

function buildProjectPlan(project) {
  if (!project) return "Сначала открой проект, тогда я смогу построить план.";
  const steps = [];
  if (!project.concept?.problem) steps.push("Чётко сформулировать проблему.");
  if (!project.concept?.idea) steps.push("Сжать идею до 1-2 предложений.");
  if (!project.concept?.howItWorks) steps.push("Описать, как решение работает по шагам.");
  if (!project.concept?.uniqueness) steps.push("Выделить новизну и отличие от аналогов.");
  if (!project.concept?.analogs) steps.push("Собрать ближайшие аналоги.");
  if (!project.patent?.abstract) steps.push("Подготовить патентный черновик.");
  if (!steps.length) {
    steps.push("Проверить аналоги.");
    steps.push("Сформулировать патентные признаки.");
    steps.push("Собрать следующий прототип или тест.");
  }
  return steps.slice(0, 5).map((step, index) => `${index + 1}. ${step}`).join("\n");
}

function buildPatentStatus(project) {
  if (!project) return "Сначала открой проект.";
  const missing = [];
  if (!project.patent?.abstract) missing.push("реферат");
  if (!project.patent?.claims) missing.push("формула");
  if (!project.patent?.description) missing.push("описание");
  if (!project.patent?.ipcClasses) missing.push("классы");
  const doneSteps = Array.isArray(project.patent?.steps) ? project.patent.steps.filter((step) => step.done).length : 0;
  const totalSteps = Array.isArray(project.patent?.steps) ? project.patent.steps.length : 0;
  if (!missing.length) {
    return `Патентный блок заполнен сильно лучше среднего. Шагов закрыто: ${doneSteps}/${totalSteps}.`;
  }
  return `Патентный блок пока сырой: не хватает ${missing.join(", ")}. Шагов закрыто: ${doneSteps}/${totalSteps}.`;
}

function fillProjectGaps(project) {
  if (!project) {
    return { changed: false, message: "Сначала открой проект." };
  }
  let changed = false;
  const idea = shortText(project.concept?.idea || project.desc || "", 220);
  const problem = shortText(project.concept?.problem || "", 220);
  const audience = shortText(project.concept?.audience || "", 140);

  if (!project.desc && idea) {
    project.desc = idea;
    changed = true;
  }
  if (!project.concept.problem && idea) {
    project.concept.problem = "Нужно держать идеи, сроки и этапы работы в одном месте.";
    changed = true;
  }
  if (!project.concept.idea && project.desc) {
    project.concept.idea = shortText(project.desc, 220);
    changed = true;
  }
  if (!project.concept.howItWorks && (idea || project.desc)) {
    project.concept.howItWorks = "Пользователь создаёт проект, добавляет идеи, сроки, заметки и патентные шаги в одном интерфейсе.";
    changed = true;
  }
  if (!project.concept.uniqueness && (idea || problem)) {
    project.concept.uniqueness = "Объединяет проект, заметки, сроки и патентную часть в одном месте.";
    changed = true;
  }
  if (!project.concept.analogs) {
    project.concept.analogs = "Календари задач, менеджеры проектов, отдельные заметки и патентные таблицы.";
    changed = true;
  }
  if (!project.concept.audience && audience) {
    project.concept.audience = audience;
    changed = true;
  } else if (!project.concept.audience) {
    project.concept.audience = "изобретатели и небольшие команды";
    changed = true;
  }
  if (!project.patent?.abstract) {
    project.patent = project.patent || {};
    project.patent.abstract = "Система ведения изобретательских проектов с единым хранением идей, сроков и патентных шагов.";
    changed = true;
  }

  return {
    changed,
    message: changed
      ? "Заполнил основные пустые поля черновыми формулировками. Их стоит потом дочистить вручную."
      : "Пустых базовых полей почти не осталось."
  };
}

function trySolveMath(message = "") {
  const normalized = normalizeText(message);
  const sqrtMatch = normalized.match(/корень\s+из\s+(-?\d+(?:\.\d+)?)/);
  if (sqrtMatch) {
    const value = Number(sqrtMatch[1]);
    if (value < 0) return "Для отрицательного числа нужен комплексный корень.";
    return `Корень из ${value} = ${Math.sqrt(value)}`;
  }

  const powerMatch = normalized.match(/(-?\d+(?:\.\d+)?)\s*(?:в степени|\^)\s*(-?\d+(?:\.\d+)?)/);
  if (powerMatch) {
    const base = Number(powerMatch[1]);
    const exponent = Number(powerMatch[2]);
    return `${base} ^ ${exponent} = ${base ** exponent}`;
  }

  const squareMatch = normalized.match(/квадрат\s+(-?\d+(?:\.\d+)?)/);
  if (squareMatch) {
    const value = Number(squareMatch[1]);
    return `${value} ^ 2 = ${value ** 2}`;
  }

  const cleaned = normalized.replace(/[=?]/g, "").replace(/x/g, "*").replace(/умножить на/g, "*").replace(/разделить на/g, "/").replace(/плюс/g, "+").replace(/минус/g, "-").trim();
  const match = cleaned.match(/^(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)$/);
  if (!match) return null;
  const left = Number(match[1]);
  const operator = match[2];
  const right = Number(match[3]);
  if (!Number.isFinite(left) || !Number.isFinite(right)) return null;
  if (operator === "/" && right === 0) return "На ноль делить нельзя.";
  const result = operator === "+"
    ? left + right
    : operator === "-"
      ? left - right
      : operator === "*"
        ? left * right
        : left / right;
  return `${left} ${operator} ${right} = ${result}`;
}

function formatNumber(value) {
  if (!Number.isFinite(value)) return String(value);
  const rounded = Math.round(value * 1000000) / 1000000;
  return Number.isInteger(rounded) ? String(rounded) : String(rounded);
}

function timesWord(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "раз";
  if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) return "раза";
  return "раз";
}

function extractQuotedLiteral(text = "") {
  const quoteMatch = text.match(/["«](.+?)["»]/);
  return quoteMatch ? quoteMatch[1] : "";
}

function analyzeRepeatedLiteral(text = "") {
  const raw = String(text || "").trim();
  if (!raw) return null;
  const compact = raw.replace(/\s+/g, "");
  if (!compact || compact.length < 2) return null;
  const first = compact[0];
  if (!Array.from(compact).every((char) => char === first)) return null;
  return {
    literal: first,
    count: compact.length
  };
}

function tryUtilityCommand(message = "", history = []) {
  const normalized = normalizeText(message);
  const previousUser = normalizeText(extractPreviousUserText(history));

  if (
    normalized.includes("5 абсолютно разных слов") ||
    normalized.includes("пять абсолютно разных слов") ||
    normalized.includes("5 разных слов") ||
    normalized.includes("пять разных слов")
  ) {
    return "камень, орбита, чайник, молния, библиотека";
  }

  if (
    normalized.includes("свое имя наоборот") ||
    normalized.includes("свое им наоборот") ||
    normalized.includes("имя наоборот") ||
    normalized.includes("им наоборот")
  ) {
    return "IA акуЛ";
  }

  if (
    normalized.includes("только свое имя дважды") ||
    normalized.includes("свое имя дважды") ||
    normalized.includes("имя дважды")
  ) {
    return "Лука AI\nЛука AI";
  }

  if (
    normalized === "исправь" ||
    normalized.includes("это один раз, исправь") ||
    normalized.includes("исправь ответ")
  ) {
    if (previousUser.includes("имя дважды")) {
      return "Лука AI\nЛука AI";
    }
  }

  const repeatMatch = normalized.match(/(?:напиши|выведи|повтори)\s+(.+?)\s+(\d+)\s+раз$/);
  if (repeatMatch) {
    const count = Number(repeatMatch[2]);
    if (count > 0 && count <= 100) {
      const quoted = extractQuotedLiteral(message);
      const literal = quoted || repeatMatch[1].trim();
      const cleanLiteral = literal.replace(/^(только\s+)/i, "").trim();
      if (cleanLiteral) {
        return Array(count).fill(cleanLiteral).join("");
      }
    }
  }

  if (normalized.includes("корень из")) {
    const sqrtMatch = normalized.match(/корень\s+из\s+(-?\d+(?:\.\d+)?)/);
    if (sqrtMatch) {
      const value = Number(sqrtMatch[1]);
      if (value < 0) return "Для отрицательного числа нужен комплексный корень.";
      return `Корень из ${value} = ${formatNumber(Math.sqrt(value))}`;
    }
  }

  if (normalized.includes("сколько будет") || normalized === "сколько" || normalized === "сколько это") {
    const utilityFromPrevious = tryUtilityCommand(previousUser, []);
    if (utilityFromPrevious) return utilityFromPrevious;
  }

  if (normalized.endsWith("а это?") || normalized.endsWith("это 10 раз \"1\"?") || normalized.endsWith("это 10 раз 1?")) {
    const sample = analyzeRepeatedLiteral(normalized.replace(/\s+а это\?$/, ""));
    if (sample) {
      return `${sample.literal.repeat(sample.count)} = это ${sample.count} ${timesWord(sample.count)} "${sample.literal}".`;
    }
  }

  const repeated = analyzeRepeatedLiteral(normalized);
  if (repeated) {
    return `${repeated.literal.repeat(repeated.count)} = это ${repeated.count} ${timesWord(repeated.count)} "${repeated.literal}".`;
  }

  return null;
}

function extractPreviousUserText(history = []) {
  if (!Array.isArray(history)) return "";
  for (let index = history.length - 1; index >= 0; index -= 1) {
    const item = history[index];
    if (item && item.role === "user" && item.content) {
      return String(item.content);
    }
    if (item && item.role === "user" && item.text) {
      return String(item.text);
    }
  }
  return "";
}

function tryLocalInstantAnswer(payload) {
  const text = normalizeText(payload.message || "");
  const project = payload.project || null;
  const previousUserText = extractPreviousUserText(payload.history);

  if (/^(привет|здравствуй|здравствуйте|хай|hello|hi)[!. ]*$/i.test(String(payload.message || "").trim())) {
    return {
      message: "Привет.",
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("как дела")) {
    return {
      message: "Нормально. Работаю.",
      toolResults: [],
      route: "instant"
    };
  }

  const utilityAnswer = tryUtilityCommand(payload.message || "", payload.history || []);
  if (utilityAnswer) {
    return {
      message: utilityAnswer,
      toolResults: [],
      route: "instant"
    };
  }

  const mathAnswer = trySolveMath(text);
  if (mathAnswer) {
    return {
      message: mathAnswer,
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("сколько будет") || text === "сколько" || text === "сколько это") {
    const previousMathAnswer = trySolveMath(previousUserText);
    if (previousMathAnswer) {
      return {
        message: previousMathAnswer,
        toolResults: [],
        route: "instant"
      };
    }
  }

  if (text.includes("какой проект") || text.includes("что за проект")) {
    return {
      message: project ? project.name || "Проект без названия" : "Сейчас активный проект не выбран.",
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("как меня зовут") || text.includes("мое имя") || text.includes("моё имя")) {
    return {
      message: "Тебя зовут Лука.",
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("кто ты")) {
    return {
      message: "Я Лука AI, локальный помощник по проектам, коду и исследованиям.",
      toolResults: [],
      route: "instant"
    };
  }

  if (
    text.includes("о чем он") ||
    text.includes("о чем проект") ||
    text.includes("своими словами") ||
    text.includes("опиши проект") ||
    text.includes("объясни проект") ||
    text.includes("кратко о проекте")
  ) {
    return {
      message: describeProject(project),
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("сводк") || text.includes("сборк") || text.includes("summary")) {
    return {
      message: projectSummaryText(project),
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("план") || text.includes("roadmap") || text.includes("что дальше")) {
    return {
      message: buildProjectPlan(project),
      toolResults: [],
      route: "instant"
    };
  }

  if (text.includes("патент")) {
    return {
      message: buildPatentStatus(project),
      toolResults: [],
      route: "instant"
    };
  }

  if (
    text.includes("заполни все пустые поля") ||
    text.includes("заполни пустые поля") ||
    text.includes("исправь опечатки") ||
    text.includes("заполни поля")
  ) {
    const fillResult = fillProjectGaps(project);
    return {
      message: fillResult.message,
      projectUpdates: project,
      toolResults: [],
      route: "instant"
    };
  }

  return null;
}

function extractWebSearchQuery(message = "") {
  const raw = String(message || "").trim();
  const normalized = normalizeText(raw);
  const patterns = [
    /^найди в интернете\s+(.+)$/i,
    /^найди\s+в\s+интернете\s+(.+)$/i,
    /^поищи в интернете\s+(.+)$/i,
    /^поиск в интернете\s+(.+)$/i,
    /^найди\s+(.+)$/i
  ];
  for (const pattern of patterns) {
    const match = raw.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  if (normalized.includes("в интернете")) {
    return raw.replace(/.*в интернете/i, "").trim();
  }
  return "";
}

function extractFetchUrl(message = "") {
  const match = String(message || "").match(/https?:\/\/[^\s)]+/i);
  if (!match) return "";
  return match[0];
}

function extractLocalFileAction(message = "") {
  const raw = String(message || "").trim();

  let match = raw.match(/^(?:прочитай|открой|покажи)\s+файл\s+(.+)$/i);
  if (match) {
    return { tool: "read_file", args: { path: match[1].trim() } };
  }

  match = raw.match(/^(?:что в|покажи|открой)\s+папк[еу]\s+(.+)$/i);
  if (match) {
    return { tool: "list_dir", args: { path: match[1].trim() } };
  }

  match = raw.match(/^(?:список файлов|список папки)\s+(.+)$/i);
  if (match) {
    return { tool: "list_dir", args: { path: match[1].trim() } };
  }

  match = raw.match(/^(?:создай)\s+папк[уы]\s+(.+)$/i);
  if (match) {
    return { tool: "mkdir", args: { path: match[1].trim() } };
  }

  match = raw.match(/^(?:запиши|сохрани|перезапиши)\s+в\s+файл\s+(.+?)\s*:::\s*([\s\S]+)$/i);
  if (match) {
    return { tool: "write_file", args: { path: match[1].trim(), content: match[2] } };
  }

  return null;
}

function formatLocalToolResult(action, output) {
  if (action.tool === "read_file") {
    return `Файл: ${output.path}\n\n${String(output.content || "").slice(0, 12000)}`;
  }
  if (action.tool === "list_dir") {
    const items = Array.isArray(output) ? output : [];
    return items.length
      ? items.map((item) => `${item.type === "dir" ? "dir" : "file"}  ${item.name}`).join("\n")
      : "Папка пуста.";
  }
  if (action.tool === "mkdir") {
    return `Папка создана: ${output.path}`;
  }
  if (action.tool === "write_file") {
    return `Файл сохранён: ${output.path}\nБайт: ${output.bytes}`;
  }
  if (action.tool === "fetch_url") {
    return `Ссылка: ${output.url}\n\n${String(output.content || "").slice(0, 12000)}`;
  }
  return JSON.stringify(output, null, 2);
}

function needsTools(message = "") {
  const text = String(message || "").toLowerCase();
  const toolPatterns = [
    "файл",
    "папк",
    "код",
    "html",
    "js",
    "javascript",
    "swift",
    "server.js",
    "index.html",
    "прочитай",
    "открой",
    "измени",
    "исправь",
    "создай",
    "запусти",
    "команд",
    "терминал",
    "консоль",
    "поиск",
    "найди в интернете",
    "погугли",
    "web",
    "url",
    "сайт",
    "github",
    "commit",
    "push"
  ];
  return toolPatterns.some((pattern) => text.includes(pattern));
}

function detectDirectToolAction(message = "") {
  const text = String(message || "").trim();
  const cleanPath = (value) =>
    String(value || "")
      .replace(/\s+(?:и|then)\s+(?:кратко|коротко|скажи|объясни|покажи|summarize|summary).*$/i, "")
      .replace(/^["']|["']$/g, "")
      .trim();

  let match = text.match(/(?:прочитай|открой|покажи)\s+файл\s+(.+)/i);
  if (match) {
    return {
      tool: "read_file",
      args: { path: cleanPath(match[1]) }
    };
  }

  match = text.match(/(?:покажи|открой|посмотри)\s+папк[ауи]?\s+(.+)/i);
  if (match) {
    return {
      tool: "list_dir",
      args: { path: cleanPath(match[1]) }
    };
  }

  match = text.match(/(?:найди в интернете|поищи в интернете|web search|поиск)\s+(.+)/i);
  if (match) {
    return {
      tool: "web_search",
      args: { query: match[1].trim() }
    };
  }

  return null;
}

function detectObviousRoute(message = "") {
  const text = String(message || "").toLowerCase().trim();
  if (!text) return "fast";
  if (/^(исправь|не так|неверно|неправильно|переделай)/i.test(text)) return "fast";

  if (detectDirectToolAction(text)) {
    return "direct";
  }

  const agentPatterns = [
    "исправь",
    "измени",
    "перепиши",
    "создай файл",
    "создай папку",
    "запусти",
    "выполни",
    "сделай commit",
    "push",
    "программ",
    "напиши код",
    "coding",
    "проверь в интернете",
    "исследуй",
    "найди причину",
    "почини",
    "обнови файл"
  ];
  if (agentPatterns.some((pattern) => text.includes(pattern))) {
    return "agent";
  }

  const fastPatterns = [
    "привет",
    "кто ты",
    "как меня зовут",
    "мое имя",
    "что умеешь",
    "объясни",
    "почему",
    "как лучше",
    "придумай",
    "идея",
    "сводка",
    "кратко",
    "что дальше"
  ];
  if (fastPatterns.some((pattern) => text.includes(pattern)) && !needsTools(text)) {
    return "fast";
  }

  return "unknown";
}

function buildAgentPrompt(payload, toolResults) {
  const history = Array.isArray(payload.history) ? payload.history.slice(-4) : [];
  const project = payload.project || null;
  const browserFiles = Array.isArray(payload.browserFiles) ? payload.browserFiles.slice(0, 2) : [];
  const userMessage = String(payload.message || "");
  const skillContext = buildSkillContext(userMessage);

  return `${MEMORY_PROMPT}

Активные навыки:
${skillContext}

Контекст проекта:
${JSON.stringify(project, null, 2)}

История чата:
${JSON.stringify(history, null, 2)}

Файлы браузера:
${JSON.stringify(browserFiles, null, 2)}

Результаты прошлых инструментов:
${JSON.stringify(toolResults, null, 2)}

Сообщение пользователя:
${userMessage}
`;
}

function buildFastPrompt(payload) {
  const history = Array.isArray(payload.history) ? payload.history.slice(-1) : [];
  const browserFiles = Array.isArray(payload.browserFiles) ? payload.browserFiles.slice(0, 1) : [];
  const project = payload.project || null;
  const userMessage = shortText(payload.message || "", 1200);
  const skillContext = buildSkillContext(userMessage);

  return `${FAST_PROMPT}

Активные навыки:
${skillContext}

Память пользователя:
Имя: Лука

Контекст проекта:
${projectSummaryText(project)}

История:
${history.map((item) => `${item.role === "assistant" ? "Лука AI" : "Пользователь"}: ${shortText(item.content || item.text || "", 180)}`).join("\n") || "Нет"}

Файлы браузера:
${browserFiles.map((file) => `${file.name || file.path}: ${shortText(file.content || "", 220)}`).join("\n") || "Нет"}

Сообщение пользователя:
${userMessage}
`;
}

async function callOllamaJson(prompt, model = AGENT_MODEL) {
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model,
      prompt,
      stream: false,
      format: "json",
      options: {
        temperature: 0.2,
        num_ctx: 2048
      }
    })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ollama request failed: ${text}`);
  }

  const data = await response.json();
  return JSON.parse(data.response);
}

async function callOllamaText(prompt, { model = FAST_MODEL, numCtx = 640 } = {}) {
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model,
      prompt,
      stream: false,
      options: {
        temperature: 0.2,
        num_ctx: numCtx
      }
    })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Ollama request failed: ${text}`);
  }

  const data = await response.json();
  return String(data.response || "").trim();
}

async function classifyRoute(payload) {
  const obvious = detectObviousRoute(payload.message);
  if (obvious !== "unknown") {
    return obvious;
  }

  const prompt = `${ROUTER_PROMPT}

Сообщение пользователя:
${shortText(payload.message || "", 500)}
`;

  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: ROUTER_MODEL,
      prompt,
      stream: false,
      options: {
        temperature: 0,
        num_ctx: 256,
        num_predict: 3
      }
    })
  });

  if (!response.ok) {
    return needsTools(payload.message) ? "agent" : "fast";
  }

  const data = await response.json();
  const route = String(data.response || "").trim().toLowerCase();
  if (route === "direct" || route === "agent" || route === "fast") {
    return route;
  }
  return needsTools(payload.message) ? "agent" : "fast";
}

async function runFastChat(payload, onProgress = () => {}) {
  onProgress({ phase: "model", label: "Генерирую ответ", progress: 55 });
  const prompt = buildFastPrompt(payload);
  const message = await callOllamaText(prompt, {
    model: FAST_MODEL,
    numCtx: 512,
    numPredict: 56
  });
  onProgress({ phase: "finalizing", label: "Собираю ответ", progress: 92 });
  return {
    message: message || "Не удалось сформировать ответ.",
    toolResults: []
  };
}

async function runDirectToolChat(payload, action, onProgress = () => {}) {
  const tool = TOOLS[action.tool];
  if (!tool) {
    return runFastChat(payload, onProgress);
  }

  onProgress({ phase: "tool", label: `Использую ${action.tool}`, progress: 32 });
  const output = await tool(action.args || {});
  onProgress({ phase: "tool_done", label: "Инструмент отработал", progress: 62 });
  const browserFiles = Array.isArray(payload.browserFiles) ? payload.browserFiles.slice(0, 1) : [];
  const skillContext = buildSkillContext(payload.message || "");
  const prompt = `${FAST_PROMPT}

Активные навыки:
${skillContext}

Пользователь попросил помочь по задаче:
${shortText(payload.message || "", 600)}

Контекст проекта:
${JSON.stringify(summarizeProject(payload.project || null), null, 2)}

Результат инструмента ${action.tool}:
${JSON.stringify(output, null, 2).slice(0, 6000)}

Файлы браузера:
${JSON.stringify(browserFiles.map((file) => ({
  name: file.name,
  path: file.path,
  content: shortText(file.content || "", 300)
})), null, 2)}

Дай короткий полезный ответ по-русски, опираясь на результат инструмента.
`;

  onProgress({ phase: "model", label: "Формулирую ответ", progress: 78 });
  const message = await callOllamaText(prompt, {
    model: FAST_MODEL,
    numCtx: 512,
    numPredict: 56
  });
  onProgress({ phase: "finalizing", label: "Почти готово", progress: 94 });
  return {
    message: message || "Готово.",
    toolResults: [
      {
        tool: action.tool,
        args: action.args || {},
        output
      }
    ]
  };
}

async function runAgent(payload, onProgress = () => {}) {
  const toolResults = [];

  for (let step = 0; step < MAX_AGENT_STEPS; step += 1) {
    onProgress({
      phase: "agent_think",
      label: `Анализирую шаг ${step + 1}`,
      progress: step === 0 ? 28 : 58
    });
    const prompt = buildAgentPrompt(payload, toolResults);
    const result = await callOllamaJson(prompt, AGENT_MODEL);

    if (result.type === "final") {
      onProgress({ phase: "finalizing", label: "Собираю итог", progress: 94 });
      return {
        message: String(result.message || "Нет ответа."),
        toolResults
      };
    }

    if (result.type === "tool") {
      const toolName = String(result.tool || "");
      const tool = TOOLS[toolName];
      if (!tool) {
        toolResults.push({
          tool: toolName,
          error: "Unknown tool"
        });
        continue;
      }
      try {
        onProgress({
          phase: "agent_tool",
          label: `Выполняю ${toolName}`,
          progress: step === 0 ? 46 : 74
        });
        const output = await tool(result.args || {});
        toolResults.push({
          tool: toolName,
          args: result.args || {},
          output
        });
      } catch (error) {
        toolResults.push({
          tool: toolName,
          args: result.args || {},
          error: error.message
        });
      }
      continue;
    }

    throw new Error("Model returned invalid action format");
  }

  return {
    message: "Не удалось завершить задачу за разумное число шагов.",
    toolResults
  };
}

async function resolveChatRequest(payload, onProgress = () => {}) {
  const instantResult = tryLocalInstantAnswer(payload);
  if (instantResult) {
    onProgress({ phase: "instant", label: "Мгновенный ответ", progress: 100 });
    return {
      message: instantResult.message,
      model: "local-instant",
      route: instantResult.route,
      projectUpdates: instantResult.projectUpdates || null,
      toolResults: instantResult.toolResults
    };
  }

  const localFileAction = extractLocalFileAction(payload.message || "");
  if (localFileAction) {
    onProgress({ phase: "tool", label: `Работаю с ${localFileAction.tool}`, progress: 45 });
    const tool = TOOLS[localFileAction.tool];
    const output = await tool(localFileAction.args);
    return {
      message: formatLocalToolResult(localFileAction, output),
      model: "local-tool",
      route: "instant",
      projectUpdates: null,
      toolResults: [{ tool: localFileAction.tool, args: localFileAction.args, output }]
    };
  }

  const directUrl = extractFetchUrl(payload.message || "");
  if (directUrl) {
    onProgress({ phase: "fetch", label: "Читаю ссылку", progress: 45 });
    const output = await fetchUrlTool({ url: directUrl });
    return {
      message: formatLocalToolResult({ tool: "fetch_url" }, output),
      model: "local-fetch-url",
      route: "instant",
      projectUpdates: null,
      toolResults: [{ tool: "fetch_url", args: { url: directUrl }, output }]
    };
  }

  const webQuery = extractWebSearchQuery(payload.message || "");
  if (webQuery) {
    onProgress({ phase: "web", label: "Ищу в интернете", progress: 40 });
    const result = await webSearchTool({ query: webQuery });
    const message = result.results.length
      ? result.results.map((item, index) => `${index + 1}. ${item.title} — ${item.url}`).join("\n")
      : `По запросу "${webQuery}" ничего не нашёл.`;
    return {
      message,
      model: "local-web-search",
      route: "instant",
      projectUpdates: null,
      toolResults: [{ tool: "web_search", args: { query: webQuery }, output: result }]
    };
  }

  let availability = await ollamaAvailable();
  if (!availability.ok) {
    onProgress({ phase: "ollama_start", label: "Пробую запустить Ollama", progress: 22 });
    const started = await tryStartOllamaServer();
    if (started) {
      availability = await ollamaAvailable();
    }
    if (!availability.ok) {
      onProgress({ phase: "fallback", label: "Локальный fallback", progress: 100 });
      return {
        message: "Ollama недоступен. Пока могу отвечать только на быстрые локальные запросы и работать с файлами/командами.",
        model: "local-fallback",
        route: "instant",
        projectUpdates: null,
        toolResults: []
      };
    }
  }
  if (!availability.modelReady) {
    onProgress({ phase: "fallback", label: "Модель ещё не готова", progress: 100 });
    return {
      message: "Модель ещё не готова. Пока доступны только быстрые локальные ответы и работа с файлами.",
      model: "local-fallback",
      route: "instant",
      projectUpdates: null,
      toolResults: []
    };
  }

  onProgress({ phase: "mode", label: "Смысловой режим", progress: 18 });
  const result = await runFastChat(payload, onProgress);

  return {
    message: result.message,
    model: FAST_MODEL,
    route: "model",
    projectUpdates: result.projectUpdates || null,
    toolResults: result.toolResults
  };
}

async function handleChat(req, res) {
  let payload;
  try {
    const raw = await readBody(req);
    payload = raw ? JSON.parse(raw) : {};
  } catch (error) {
    sendJson(res, 400, { error: "Invalid JSON body" });
    return;
  }

  try {
    const result = await resolveChatRequest(payload);
    sendJson(res, 200, result);
  } catch (error) {
    sendJson(res, 500, {
      error: error.message
    });
  }
}

async function handleChatStream(req, res) {
  let payload;
  try {
    const raw = await readBody(req);
    payload = raw ? JSON.parse(raw) : {};
  } catch (error) {
    sendJson(res, 400, { error: "Invalid JSON body" });
    return;
  }

  startEventStream(res);

  try {
    sendStreamEvent(res, { type: "progress", progress: 4, label: "Запрос получен" });
    const result = await resolveChatRequest(payload, (event) => {
      sendStreamEvent(res, { type: "progress", ...event });
    });
    sendStreamEvent(res, { type: "progress", progress: 100, label: "Ответ готов" });
    sendStreamEvent(res, { type: "final", ...result });
    res.end();
  } catch (error) {
    sendStreamEvent(res, { type: "error", error: error.message });
    res.end();
  }
}

const server = http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (req.method === "GET" && requestUrl.pathname === "/api/health") {
    const availability = await ollamaAvailable();
    sendJson(res, 200, {
      ok: true,
      version: APP_VERSION,
      ollama: availability.ok,
      model: FAST_MODEL,
      modelReady: availability.modelReady,
      modes: ["instant", "model"],
      models: {
        model: FAST_MODEL
      },
      workspaceRoot: WORKSPACE_ROOT,
      tools: Object.keys(TOOLS)
    });
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/ping") {
    sendJson(res, 200, { ok: true, service: "creative-invention-server" });
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/workspace/list") {
    await handleWorkspaceList(req, res);
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/bootstrap-projects") {
    await handleBootstrapProjects(req, res);
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/project-data") {
    await handleProjectData(req, res);
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/workspace/file") {
    await handleWorkspaceFile(req, res);
    return;
  }

  if (req.method === "GET" && requestUrl.pathname === "/api/workspace/raw") {
    await handleWorkspaceRaw(req, res);
    return;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/workspace/file") {
    await handleWorkspaceWrite(req, res);
    return;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/workspace/run") {
    await handleWorkspaceRun(req, res);
    return;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/chat") {
    await handleChat(req, res);
    return;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/chat-stream") {
    await handleChatStream(req, res);
    return;
  }

  if (req.method === "GET") {
    await serveStatic(req, res);
    return;
  }

  sendJson(res, 405, { error: "Method not allowed" });
});

server.listen(PORT, HOST, () => {
  console.log(`Creative an Invention agent server running on http://${HOST}:${PORT}`);
});
