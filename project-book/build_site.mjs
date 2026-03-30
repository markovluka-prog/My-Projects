import crypto from "crypto";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const BOOK_DIR = __dirname;
export const REPO_ROOT = path.resolve(__dirname, "..");
export const OUTPUT_HTML = path.join(BOOK_DIR, "index.html");

const PROJECTS = [
  {
    key: "creative",
    title: "Creative an Invention",
    root: "Creative an invention.swiftpm",
    subtitle: "Локальный агент и рабочая среда для проектов",
    lead:
      "Проект собирает в одном месте локальный веб-интерфейс, сервер и агентное поведение. Это не просто страница, а основа для помощника, который живет рядом с файлами и умеет с ними работать.",
    docs: [],
    code: ["InventionApp/server.js", "InventionApp/watchdog.js", "InventionApp/index.html"],
    images: []
  },
  {
    key: "lit-gpt",
    title: "LIT GPT",
    root: "LIT gpt",
    subtitle: "Небольшой GPT-подобный чат-бот без внешних ML-библиотек",
    lead:
      "Проект показывает попытку построить языковую систему с нуля: словарь, веса, схожесть слов, обучение на тексте и собственная логика ответа.",
    docs: ["info.md", "context.md"],
    code: ["GPT.py", "INIT.py", "Functions.py", "Root_model.py", "Base_weight.py", "Dictionary.py"],
    images: []
  },
  {
    key: "vocabulary-race",
    title: "Vocabulary Race",
    root: "Vocabulary Race.swiftpm",
    subtitle: "Словесная настольная гонка в Swift Playgrounds и WebView",
    lead:
      "Здесь настольная игра превращается в интерактивную цифровую партию с полем, словарем, фишками и локальным экраном на одном устройстве.",
    docs: ["info.md", "description.md", "context.md", "roadmap.md", "changelog.md", "bugs.md"],
    code: ["ContentView.swift", "GameWeb/index.html", "MyApp.swift", "Package.swift"],
    images: ["GameWeb/assets/logo.png", "GameWeb/assets/field.png"]
  },
  {
    key: "knights",
    title: "Рыцари и Замки",
    root: "Рыцари и Замки.swiftpm",
    subtitle: "Пошаговая стратегия с ИИ, кампанией и обновлением через GitHub",
    lead:
      "Проект сочетает игровую механику, экранную стратегию и продуманную оболочку доставки обновлений. Это большая игра с тактическим ядром и множеством художественных материалов.",
    docs: ["info.md", "description.md", "context.md", "roadmap.md", "changelog.md", "bugs.md"],
    code: [
      "ContentView.swift",
      "KnightsGame/KnightsAndCastlesTests.swift",
      ".swiftpm/xcode/GitHubUpdater.swift",
      ".swiftpm/xcode/App.swift"
    ],
    images: ["KnightsGame/Knights_and_Castles_1920x1080.png"]
  },
  {
    key: "star",
    title: "Звезда Луки",
    root: "Звезда Луки",
    subtitle: "Физический трансформер и изобретение на основе LEGO Technic",
    lead:
      "Проект раскрывает изобретение как объект игры, конструкторскую систему и будущий продукт. Здесь есть форма, размеры, патентный взгляд, себестоимость и визуальные материалы.",
    docs: [
      "info.md",
      "concept.md",
      "design.md",
      "dimensions.md",
      "prototype.md",
      "cost.md",
      "market.md",
      "patent.md",
      "context.md"
    ],
    code: ["blender_model.py"],
    images: ["photo.png", "zvezda_luki_render.png"]
  },
  {
    key: "ninja-mechanics",
    title: "Механика Ниндзя",
    root: "Механика Ниндзя",
    subtitle: "Личная теория потока, удачи и пустой головы",
    lead:
      "Это не приложение и не игра, а развивающаяся авторская теория о состоянии, в котором действие становится точным, быстрым и как будто само собой складывающимся.",
    docs: ["info.md", "article.md", "theory.md", "experiments.md", "notes.md", "sources.md", "context.md"],
    code: [],
    images: []
  },
  {
    key: "nindzi",
    title: "Ниндзи",
    root: "Ниндзи",
    subtitle: "Художественный мир: книга, сцены и приключенческая вселенная",
    lead:
      "Проект держится на персонажах, островах, морских эпизодах, путешествиях и сценах. Внутри лежат материалы, из которых складывается полноценная подростковая приключенческая серия.",
    docs: ["info.md", "book.md", "screenplay.md"],
    code: ["render.py"],
    images: []
  },
  {
    key: "spring-gravity",
    title: "Пружинная гравитация Луки",
    root: "Пружинная гравитация Луки",
    subtitle: "Альтернативная физическая гипотеза с формулами и моделями",
    lead:
      "Проект описывает собственную модель гравитации, набор экспериментов, список слабых мест и несколько интерактивных страниц для проверки идеи наглядно.",
    docs: [
      "info.md",
      "theory.md",
      "experiments.md",
      "provements.md",
      "weaknesses.md",
      "notes.md",
      "sources.md",
      "context.md"
    ],
    code: ["calculator.html", "planets.html", "simulation.html"],
    images: []
  }
];

const TEXT_EXTENSIONS = new Set([
  ".md",
  ".txt",
  ".py",
  ".js",
  ".swift",
  ".html",
  ".json",
  ".plist",
  ".pyui"
]);

const CODE_EXTENSIONS = new Set([".py", ".js", ".swift", ".html", ".json", ".pyui"]);
const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]);
const IGNORE_DIRS = new Set([".git", ".build", "node_modules"]);
const DOC_LABELS = {
  "info.md": "Сводка проекта",
  "context.md": "Контекст и задачи",
  "description.md": "Описание",
  "concept.md": "Концепт",
  "design.md": "Дизайн",
  "dimensions.md": "Размеры и конструкция",
  "prototype.md": "Прототип",
  "cost.md": "Себестоимость",
  "market.md": "Рынок",
  "patent.md": "Патентный взгляд",
  "article.md": "Статья",
  "theory.md": "Теория",
  "experiments.md": "Эксперименты",
  "notes.md": "Заметки",
  "sources.md": "Источники",
  "book.md": "Текст книги",
  "screenplay.md": "Сценарные сцены",
  "roadmap.md": "План развития",
  "changelog.md": "История изменений",
  "bugs.md": "Проблемы и задачи",
  "provements.md": "Аргументы и подтверждения"
};

const MAX_FULL_TEXT_BYTES = 180_000;
const CODE_LINE_LIMIT = 140;
const WORD_SAMPLE_LIMIT = 36;
const TEXT_EXCERPT_LIMIT = 3_400;

function escapeHtml(value = "") {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(text = "") {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

function formatDate(value = new Date()) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC"
  }).format(value);
}

function formatSize(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let size = bytes / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && size >= 1024; index += 1) {
    size /= 1024;
    unit = units[index];
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${unit}`;
}

function formatNumber(value = 0) {
  return new Intl.NumberFormat("ru-RU").format(value);
}

function getExtension(filePath) {
  return path.extname(filePath).toLowerCase();
}

function normalizeRelative(filePath) {
  return filePath.split(path.sep).join("/");
}

function stripFrontmatter(content = "") {
  if (!content.startsWith("---")) return content;
  const parts = content.split("\n");
  let index = 1;
  while (index < parts.length && parts[index].trim() !== "---") {
    index += 1;
  }
  if (index >= parts.length) return content;
  return parts.slice(index + 1).join("\n").trim();
}

function parseFrontmatterValue(content = "", keys = []) {
  if (!content.startsWith("---")) return "";
  const lines = content.split("\n");
  let index = 1;
  while (index < lines.length && lines[index].trim() !== "---") {
    const line = lines[index];
    const match = line.match(/^([A-Za-zА-Яа-яёЁ_][^:]*):\s*(.+)$/);
    if (match) {
      const key = match[1].trim().toLowerCase();
      if (keys.map((item) => item.toLowerCase()).includes(key)) {
        return match[2].trim();
      }
    }
    index += 1;
  }
  return "";
}

function renderInline(text = "") {
  let value = escapeHtml(text);
  value = value.replace(/`([^`]+)`/g, "<code>$1</code>");
  value = value.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  value = value.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  value = value.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  return value;
}

function renderParagraphs(lines = []) {
  if (!lines.length) return "";
  return `<p>${renderInline(lines.join(" ").trim())}</p>`;
}

function renderMarkdownTable(buffer) {
  const rows = buffer
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) =>
      line
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((cell) => renderInline(cell.trim()))
    );

  if (rows.length < 2) return "";
  const [header] = rows;
  const body = rows.slice(2);
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${header.map((cell) => `<th>${cell}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${body
            .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderMarkdown(content = "") {
  const source = stripFrontmatter(content);
  const lines = source.replace(/\r/g, "").split("\n");
  const html = [];
  let paragraph = [];
  let listItems = [];
  let listType = "";
  let codeFence = false;
  let codeBuffer = [];
  let tableBuffer = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    html.push(renderParagraphs(paragraph));
    paragraph = [];
  }

  function flushList() {
    if (!listItems.length) return;
    html.push(`<${listType}>${listItems.map((item) => `<li>${renderInline(item)}</li>`).join("")}</${listType}>`);
    listItems = [];
    listType = "";
  }

  function flushTable() {
    if (!tableBuffer.length) return;
    html.push(renderMarkdownTable(tableBuffer));
    tableBuffer = [];
  }

  function flushCode() {
    if (!codeBuffer.length) return;
    html.push(`<pre class="code-block"><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
    codeBuffer = [];
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      flushParagraph();
      flushList();
      flushTable();
      if (codeFence) {
        flushCode();
        codeFence = false;
      } else {
        codeFence = true;
      }
      continue;
    }

    if (codeFence) {
      codeBuffer.push(line);
      continue;
    }

    const nextLine = lines[index + 1]?.trim() || "";
    const currentIsTable = trimmed.includes("|");
    const nextIsTableDivider = /^[:\-\s|]+$/.test(nextLine) && nextLine.includes("-");
    if ((currentIsTable && nextIsTableDivider) || tableBuffer.length) {
      flushParagraph();
      flushList();
      if (trimmed) {
        tableBuffer.push(line);
        continue;
      }
      flushTable();
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      flushTable();
      const level = Math.min(heading[1].length + 2, 6);
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const blockquote = trimmed.match(/^>\s?(.*)$/);
    if (blockquote) {
      flushParagraph();
      flushList();
      flushTable();
      html.push(`<blockquote><p>${renderInline(blockquote[1])}</p></blockquote>`);
      continue;
    }

    const unordered = trimmed.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      flushParagraph();
      flushTable();
      if (listType && listType !== "ul") flushList();
      listType = "ul";
      listItems.push(unordered[1]);
      continue;
    }

    const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
    if (ordered) {
      flushParagraph();
      flushTable();
      if (listType && listType !== "ol") flushList();
      listType = "ol";
      listItems.push(ordered[1]);
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  flushTable();
  flushCode();

  return html.join("\n");
}

function takeLines(text = "", limit = CODE_LINE_LIMIT) {
  const lines = text.replace(/\r/g, "").split("\n");
  const excerpt = lines.slice(0, limit);
  return {
    text: excerpt.join("\n"),
    lineCount: lines.length,
    truncated: lines.length > limit
  };
}

function summarizeWordList(content = "") {
  const words = content
    .replace(/\r/g, "\n")
    .split(/\s+/)
    .map((item) => item.trim())
    .filter(Boolean);
  return {
    count: words.length,
    sample: words.slice(0, WORD_SAMPLE_LIMIT)
  };
}

function summarizeLargeText(content = "") {
  const excerpt = content.slice(0, TEXT_EXCERPT_LIMIT).trim();
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  const lines = content.replace(/\r/g, "").split("\n").length;
  return {
    excerpt,
    words,
    lines,
    truncated: content.length > TEXT_EXCERPT_LIMIT
  };
}

async function walkFiles(rootDir) {
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue;
    const absolutePath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      const nested = await walkFiles(absolutePath);
      files.push(...nested);
      continue;
    }
    files.push(absolutePath);
  }
  return files;
}

function classifyTextEntry(relativePath, extension, content) {
  const baseName = path.basename(relativePath).toLowerCase();
  if (extension === ".md") return "document";
  if (baseName.includes("dictionary") || baseName.includes("words")) return "word-list";
  if (extension === ".txt" && content.split("\n").length > 200) return "large-text";
  if (CODE_EXTENSIONS.has(extension)) return "code";
  return "document";
}

function preferredTitle(relativePath, content) {
  const baseName = path.basename(relativePath);
  const frontmatterTitle = parseFrontmatterValue(content, ["name", "название", "title"]);
  if (frontmatterTitle) return frontmatterTitle;
  const body = stripFrontmatter(content);
  const heading = body.match(/^#\s+(.+)$/m);
  if (heading) return heading[1].trim();
  return DOC_LABELS[baseName] || baseName.replace(path.extname(baseName), "");
}

function chooseImages(project, images) {
  const configured = project.images
    .map((configuredPath) => images.find((entry) => entry.relativePath === configuredPath))
    .filter(Boolean);

  if (configured.length) return configured;

  return images.slice(0, 6);
}

function orderEntries(entries, configuredOrder = []) {
  const orderMap = new Map(configuredOrder.map((item, index) => [normalizeRelative(item), index]));
  return [...entries].sort((left, right) => {
    const leftOrder = orderMap.has(left.relativePath) ? orderMap.get(left.relativePath) : Number.MAX_SAFE_INTEGER;
    const rightOrder = orderMap.has(right.relativePath) ? orderMap.get(right.relativePath) : Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return left.relativePath.localeCompare(right.relativePath, "ru");
  });
}

function renderDocumentCard(entry) {
  return `
    <article class="panel panel-doc">
      <div class="panel-meta">${entry.metaLabel}</div>
      <h3>${escapeHtml(entry.title)}</h3>
      <div class="rich-text">
        ${entry.rendered}
      </div>
    </article>
  `;
}

function renderCodeCard(entry) {
  const excerpt = takeLines(entry.content, CODE_LINE_LIMIT);
  const info = [`${formatNumber(excerpt.lineCount)} строк`, entry.languageLabel];
  if (excerpt.truncated) info.push("фрагмент");

  return `
    <article class="panel panel-code">
      <div class="panel-meta">${info.join(" · ")}</div>
      <h3>${escapeHtml(entry.title)}</h3>
      <pre class="code-block"><code>${escapeHtml(excerpt.text)}</code></pre>
    </article>
  `;
}

function renderDataCard(entry) {
  if (entry.kind === "word-list") {
    return `
      <article class="panel panel-data">
        <div class="panel-meta">словари и корпуса</div>
        <h3>${escapeHtml(entry.title)}</h3>
        <p>Файл содержит ${formatNumber(entry.summary.count)} слов или токенов. Ниже показан начальный срез, чтобы на сайте и в книге было видно характер материала без перегрузки на десятки страниц.</p>
        <div class="chip-wrap">
          ${entry.summary.sample.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}
        </div>
      </article>
    `;
  }

  return `
    <article class="panel panel-data">
      <div class="panel-meta">большие текстовые материалы</div>
      <h3>${escapeHtml(entry.title)}</h3>
      <p>Материал содержит ${formatNumber(entry.summary.words)} слов и ${formatNumber(entry.summary.lines)} строк. В книге показывается выдержка, а полный текст остаётся в проекте.</p>
      <div class="rich-text">
        <p>${renderInline(entry.summary.excerpt)}</p>
        ${entry.summary.truncated ? "<p class=\"note\">Текст сокращён в витринной версии, чтобы сохранить читаемость сайта и PDF.</p>" : ""}
      </div>
    </article>
  `;
}

function renderGallery(project, images) {
  if (!images.length) return "";
  return `
    <section class="chapter-block">
      <div class="section-head">
        <h3>Визуальные материалы</h3>
        <p>Выбранные изображения из проекта.</p>
      </div>
      <div class="gallery">
        ${images
          .map(
            (entry) => `
              <figure class="gallery-item">
                <img src="${escapeHtml(entry.webPath)}" alt="${escapeHtml(project.title)}">
                <figcaption>${escapeHtml(entry.caption)}</figcaption>
              </figure>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

function groupBinaryAssets(entries) {
  const groups = new Map();
  for (const entry of entries) {
    const label = entry.extension ? entry.extension.replace(".", "").toUpperCase() : "FILE";
    const current = groups.get(label) || { count: 0, bytes: 0 };
    current.count += 1;
    current.bytes += entry.size;
    groups.set(label, current);
  }

  return [...groups.entries()]
    .sort((left, right) => right[1].bytes - left[1].bytes)
    .map(([label, value]) => ({
      label,
      count: value.count,
      size: formatSize(value.bytes)
    }));
}

function renderBinarySummary(entries) {
  if (!entries.length) return "";
  const groups = groupBinaryAssets(entries);
  return `
    <section class="chapter-block">
      <div class="section-head">
        <h3>Набор артефактов</h3>
        <p>Бинарные и графические материалы, которые участвуют в проекте как ресурсы, модели, сохранения и дополнительные исходники.</p>
      </div>
      <div class="stats-grid stats-grid--small">
        ${groups
          .map(
            (item) => `
              <div class="stat-card">
                <strong>${escapeHtml(item.label)}</strong>
                <span>${formatNumber(item.count)} файлов</span>
                <span>${escapeHtml(item.size)}</span>
              </div>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

async function collectProject(project) {
  const rootDir = path.join(REPO_ROOT, project.root);
  const absoluteFiles = await walkFiles(rootDir);
  const textEntries = [];
  const images = [];
  const binaries = [];

  for (const absolutePath of absoluteFiles) {
    const stat = await fs.stat(absolutePath);
    const relativePath = normalizeRelative(path.relative(rootDir, absolutePath));
    const extension = getExtension(relativePath);

    if (IMAGE_EXTENSIONS.has(extension)) {
      images.push({
        absolutePath,
        relativePath,
        extension,
        size: stat.size,
        caption: path.basename(relativePath, extension).replaceAll("_", " "),
        webPath: escapeHtml(normalizeRelative(path.relative(BOOK_DIR, absolutePath)))
      });
      continue;
    }

    if (!TEXT_EXTENSIONS.has(extension)) {
      binaries.push({ relativePath, extension, size: stat.size });
      continue;
    }

    const content = await fs.readFile(absolutePath, "utf8");
    const kind = classifyTextEntry(relativePath, extension, content);
    const title = preferredTitle(relativePath, content);
    const metaLabel = DOC_LABELS[path.basename(relativePath)] || project.subtitle;
    textEntries.push({
      absolutePath,
      relativePath,
      extension,
      size: stat.size,
      content,
      kind,
      title,
      metaLabel,
      rendered: renderMarkdown(content),
      languageLabel: extension.replace(".", "").toUpperCase() || "TEXT"
    });
  }

  const docs = orderEntries(
    textEntries.filter((entry) => entry.kind === "document" && entry.size <= MAX_FULL_TEXT_BYTES),
    project.docs
  );
  const code = orderEntries(
    textEntries.filter((entry) => entry.kind === "code"),
    project.code
  );
  const datasets = orderEntries(
    textEntries
      .filter((entry) => entry.kind === "word-list" || entry.kind === "large-text")
      .map((entry) => ({
        ...entry,
        summary: entry.kind === "word-list" ? summarizeWordList(entry.content) : summarizeLargeText(entry.content)
      })),
    []
  );
  const featuredImages = chooseImages(project, images);

  const docWordCount = docs
    .map((entry) => stripFrontmatter(entry.content).split(/\s+/).filter(Boolean).length)
    .reduce((sum, value) => sum + value, 0);

  return {
    ...project,
    files: absoluteFiles.length,
    docs,
    code,
    datasets,
    images: featuredImages,
    binaryAssets: binaries,
    stats: {
      files: absoluteFiles.length,
      text: textEntries.length,
      docs: docs.length,
      code: code.length,
      images: images.length,
      binaries: binaries.length,
      words: docWordCount
    }
  };
}

function renderProjectSection(project) {
  return `
    <section class="chapter chapter-break" id="${escapeHtml(project.key)}">
      <div class="chapter-head">
        <span class="eyebrow">${escapeHtml(project.subtitle)}</span>
        <h2>${escapeHtml(project.title)}</h2>
        <p class="lead">${escapeHtml(project.lead)}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <strong>${formatNumber(project.stats.files)}</strong>
          <span>файлов в проекте</span>
        </div>
        <div class="stat-card">
          <strong>${formatNumber(project.stats.docs)}</strong>
          <span>текстовых глав и заметок</span>
        </div>
        <div class="stat-card">
          <strong>${formatNumber(project.stats.code)}</strong>
          <span>ключевых кодовых материалов</span>
        </div>
        <div class="stat-card">
          <strong>${formatNumber(project.stats.images)}</strong>
          <span>изображений и экранов</span>
        </div>
      </div>

      ${renderGallery(project, project.images)}

      ${
        project.docs.length
          ? `
            <section class="chapter-block">
              <div class="section-head">
                <h3>Основные материалы проекта</h3>
                <p>Здесь собраны тексты, которые напрямую описывают идею, устройство, развитие и смысл проекта.</p>
              </div>
              <div class="panel-stack">
                ${project.docs.map(renderDocumentCard).join("")}
              </div>
            </section>
          `
          : ""
      }

      ${
        project.datasets.length
          ? `
            <section class="chapter-block">
              <div class="section-head">
                <h3>Корпуса, словари и большие текстовые материалы</h3>
                <p>Эти материалы важны для проекта, но в книге показываются аккуратно и выборочно, чтобы сохранить читаемость.</p>
              </div>
              <div class="panel-stack">
                ${project.datasets.map(renderDataCard).join("")}
              </div>
            </section>
          `
          : ""
      }

      ${
        project.code.length
          ? `
            <section class="chapter-block">
              <div class="section-head">
                <h3>Код и механика</h3>
                <p>Выбранные фрагменты, по которым видно, как проект устроен технически.</p>
              </div>
              <div class="panel-stack">
                ${project.code.map(renderCodeCard).join("")}
              </div>
            </section>
          `
          : ""
      }

      ${renderBinarySummary(project.binaryAssets)}
    </section>
  `;
}

function renderIndex(portfolio) {
  const totalFiles = portfolio.projects.reduce((sum, project) => sum + project.stats.files, 0);
  const totalDocs = portfolio.projects.reduce((sum, project) => sum + project.stats.docs, 0);
  const totalCode = portfolio.projects.reduce((sum, project) => sum + project.stats.code, 0);
  const totalImages = portfolio.projects.reduce((sum, project) => sum + project.stats.images, 0);

  return `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Большая книга проектов Луки</title>
  <style>
    :root {
      --paper: #ffffff;
      --paper-soft: #f2fbff;
      --paper-deep: #e4f3ff;
      --accent: #1278c0;
      --accent-soft: #d8efff;
      --line: rgba(18, 120, 192, 0.18);
      --ink: #0f1114;
      --muted: #32424d;
      --shadow: 0 18px 42px rgba(18, 120, 192, 0.10);
      --radius: 22px;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
      background:
        radial-gradient(circle at top left, rgba(141, 195, 230, 0.20), transparent 24%),
        linear-gradient(180deg, #ffffff 0%, #f3fbff 46%, #e4f4ff 100%);
    }

    body {
      margin: 0;
      color: var(--ink);
      font-family: "Georgia", "Times New Roman", serif;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    @page {
      size: A4;
      margin: 0;
    }

    .sitebar {
      width: min(1120px, calc(100vw - 24px));
      margin: 14px auto 10px;
      padding: 14px 18px;
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 18px;
      align-items: center;
      position: sticky;
      top: 12px;
      z-index: 50;
      border-radius: 24px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.92);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .site-title {
      font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
      font-size: 18pt;
      font-weight: 700;
      white-space: nowrap;
    }

    .site-nav {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }

    .site-nav a {
      padding: 8px 12px;
      border-radius: 999px;
      text-decoration: none;
      color: var(--ink);
      background: var(--accent-soft);
      border: 1px solid rgba(18, 120, 192, 0.10);
      font-size: 9pt;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .chapter {
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto 12px;
      padding: 18mm 17mm 18mm;
      background:
        radial-gradient(circle at top right, rgba(98, 171, 217, 0.13), transparent 20%),
        radial-gradient(circle at bottom left, rgba(141, 195, 230, 0.16), transparent 26%),
        linear-gradient(180deg, #ffffff 0%, #f7fcff 46%, #f0f8ff 100%);
      position: relative;
      box-shadow: var(--shadow);
      break-after: page;
    }

    .chapter::before {
      content: "";
      position: absolute;
      inset: 7mm;
      border: 1px solid var(--line);
      pointer-events: none;
    }

    .chapter-break {
      break-before: page;
      page-break-before: always;
    }

    .cover {
      display: grid;
      align-content: space-between;
      background:
        radial-gradient(circle at 18% 18%, rgba(98, 171, 217, 0.18), transparent 18%),
        radial-gradient(circle at 82% 22%, rgba(18, 120, 192, 0.14), transparent 20%),
        linear-gradient(135deg, #ffffff 0%, #f2fbff 54%, #e7f5ff 100%);
    }

    .cover-grid,
    .cover-bottom,
    .section-head,
    .chapter-head {
      display: grid;
      gap: 12px;
    }

    .cover-grid {
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16mm;
      min-height: 210mm;
      align-items: start;
    }

    .eyebrow {
      display: inline-flex;
      width: fit-content;
      padding: 7px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--muted);
      font-size: 9pt;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      margin: 0;
      font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
      line-height: 1.05;
      font-weight: 700;
      color: var(--ink);
    }

    h1 {
      font-size: 32pt;
    }

    h2 {
      font-size: 24pt;
    }

    h3 {
      font-size: 16pt;
    }

    h4,
    h5,
    h6 {
      font-size: 12pt;
      margin-top: 10px;
    }

    p,
    li,
    td,
    th {
      font-size: 10.7pt;
      line-height: 1.64;
    }

    p {
      margin: 0;
    }

    p + p {
      margin-top: 10px;
    }

    a {
      color: inherit;
    }

    code {
      padding: 0 4px;
      border-radius: 6px;
      background: #e9f5ff;
      font-family: "SFMono-Regular", "Consolas", "Menlo", monospace;
      font-size: 0.95em;
    }

    .lead {
      font-size: 12.2pt;
      line-height: 1.7;
      max-width: 108mm;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }

    .stats-grid--small {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .stat-card {
      display: grid;
      gap: 4px;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid var(--line);
    }

    .stat-card strong {
      font-size: 18pt;
    }

    .panel-stack,
    .cover-points,
    .contents-list {
      display: grid;
      gap: 12px;
    }

    .panel,
    .contents-item {
      padding: 18px 20px;
      border-radius: var(--radius);
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.94);
    }

    .panel-meta {
      margin-bottom: 8px;
      font-size: 8.9pt;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .panel h3 {
      margin-bottom: 10px;
    }

    .rich-text {
      display: grid;
      gap: 10px;
    }

    .rich-text ul,
    .rich-text ol {
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 7px;
    }

    blockquote {
      margin: 0;
      padding-left: 16px;
      border-left: 3px solid var(--accent);
    }

    .table-wrap {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th,
    td {
      padding: 10px;
      border-top: 1px solid var(--line);
      vertical-align: top;
      text-align: left;
    }

    th {
      background: #edf8ff;
      font-size: 8.8pt;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .code-block {
      margin: 0;
      padding: 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: #f2faff;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 9.1pt;
      line-height: 1.54;
      font-family: "SFMono-Regular", "Consolas", "Menlo", monospace;
    }

    .chapter-block {
      margin-top: 10mm;
      display: grid;
      gap: 12px;
    }

    .gallery {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .gallery-item {
      margin: 0;
      display: grid;
      gap: 8px;
      padding: 10px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.94);
    }

    .gallery-item img {
      width: 100%;
      height: auto;
      display: block;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fff;
    }

    .gallery-item figcaption,
    .note,
    .cover-note {
      color: var(--muted);
      font-size: 9.2pt;
      line-height: 1.45;
    }

    .chip-wrap {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      font-size: 9pt;
    }

    .cover-visual {
      display: grid;
      gap: 10px;
      align-content: start;
    }

    .cover-visual-card {
      padding: 16px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.94);
    }

    .contents-item {
      display: grid;
      grid-template-columns: 44px 1fr;
      gap: 12px;
      align-items: start;
      text-decoration: none;
      color: inherit;
    }

    .contents-item strong {
      font-size: 11pt;
    }

    .contents-item b {
      font-size: 12pt;
    }

    @media print {
      html,
      body {
        background: transparent;
      }

      .sitebar {
        display: none;
      }

      .chapter {
        margin: 0;
        box-shadow: none;
      }
    }

    @media (max-width: 920px) {
      .sitebar,
      .chapter {
        width: 100%;
        max-width: 100%;
        margin-left: 0;
        margin-right: 0;
        border-radius: 0;
      }

      .sitebar {
        top: 0;
        width: 100%;
        margin: 0 0 10px;
        border-radius: 0 0 24px 24px;
        grid-template-columns: 1fr;
      }

      .site-nav {
        justify-content: flex-start;
      }

      .chapter {
        min-height: auto;
        padding: 24px 18px 28px;
      }

      .chapter::before {
        inset: 8px;
      }

      .cover-grid,
      .stats-grid,
      .stats-grid--small,
      .gallery {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="sitebar">
    <div class="site-title">Большая книга проектов Луки</div>
    <nav class="site-nav">
      <a href="#top">Вверх</a>
      ${portfolio.projects.map((project) => `<a href="#${escapeHtml(project.key)}">${escapeHtml(project.title)}</a>`).join("")}
    </nav>
  </div>

  <section class="chapter cover" id="top">
    <div class="cover-grid">
      <div class="cover-bottom">
        <span class="eyebrow">Сайт и книга из исходных материалов</span>
        <h1>Большая книга проектов Луки</h1>
        <p class="lead">Этот документ собирается автоматически из самих проектов. Агент перечитывает тексты, код, изображения и важные данные, а потом заново строит сайт и печатную книгу из единого источника.</p>
        <div class="stats-grid">
          <div class="stat-card">
            <strong>${formatNumber(portfolio.projects.length)}</strong>
            <span>проектов в книге</span>
          </div>
          <div class="stat-card">
            <strong>${formatNumber(totalFiles)}</strong>
            <span>файлов просмотрено агентом</span>
          </div>
          <div class="stat-card">
            <strong>${formatNumber(totalDocs)}</strong>
            <span>текстовых блоков вошло в книгу</span>
          </div>
          <div class="stat-card">
            <strong>${formatNumber(totalCode + totalImages)}</strong>
            <span>кодовых и визуальных материалов</span>
          </div>
        </div>
        <div class="cover-points">
          <div class="cover-visual-card">
            <h3>Что делает агент</h3>
            <p>Он отслеживает изменения по проектам, исключает служебные каталоги, заново собирает HTML-сайт, а затем экспортирует PDF через Playwright. Оба формата всегда строятся из одной и той же актуальной структуры.</p>
          </div>
          <div class="cover-visual-card">
            <h3>Когда собрана эта версия</h3>
            <p>${escapeHtml(portfolio.generatedAt)}</p>
            <p class="cover-note">Сигнатура входных данных: ${escapeHtml(portfolio.signature)}</p>
          </div>
        </div>
      </div>

      <div class="cover-visual">
        <div class="cover-visual-card">
          <h3>Содержание</h3>
          <div class="contents-list">
            ${portfolio.projects
              .map(
                (project, index) => `
                  <a class="contents-item" href="#${escapeHtml(project.key)}">
                    <strong>${String(index + 1).padStart(2, "0")}</strong>
                    <span><b>${escapeHtml(project.title)}</b><br>${escapeHtml(project.subtitle)}</span>
                  </a>
                `
              )
              .join("")}
          </div>
        </div>
      </div>
    </div>
  </section>

  ${portfolio.projects.map(renderProjectSection).join("\n")}
</body>
</html>`;
}

export async function buildSite() {
  const projects = [];

  for (const project of PROJECTS) {
    projects.push(await collectProject(project));
  }

  const signatureSource = JSON.stringify(
    projects.map((project) => ({
      key: project.key,
      stats: project.stats,
      docs: project.docs.map((entry) => [entry.relativePath, entry.size]),
      code: project.code.map((entry) => [entry.relativePath, entry.size]),
      data: project.datasets.map((entry) => [entry.relativePath, entry.size]),
      images: project.images.map((entry) => [entry.relativePath, entry.size]),
      binaryAssets: project.binaryAssets.map((entry) => [entry.relativePath, entry.size])
    }))
  );

  const portfolio = {
    generatedAt: `${formatDate(new Date())} UTC`,
    signature: crypto.createHash("sha1").update(signatureSource).digest("hex").slice(0, 12),
    projects
  };

  const html = renderIndex(portfolio);
  await fs.writeFile(OUTPUT_HTML, html, "utf8");

  return {
    output: OUTPUT_HTML,
    signature: portfolio.signature,
    projects: portfolio.projects.length
  };
}

const isDirectRun = process.argv[1] && path.resolve(process.argv[1]) === __filename;
if (isDirectRun) {
  const result = await buildSite();
  console.log(JSON.stringify(result));
}
