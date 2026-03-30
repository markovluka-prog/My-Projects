import path from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const htmlPath = path.join(__dirname, "index.html");
const pdfPath = path.join(__dirname, "Книга_проектов_Луки.pdf");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1400, height: 1980 },
  deviceScaleFactor: 2
});

await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
await page.emulateMedia({ media: "print" });
await page.waitForFunction(() => Array.from(document.images).every((img) => img.complete));
await page.pdf({
  path: pdfPath,
  format: "A4",
  printBackground: true,
  margin: { top: "0", right: "0", bottom: "0", left: "0" },
  preferCSSPageSize: true
});

await browser.close();
console.log(pdfPath);
