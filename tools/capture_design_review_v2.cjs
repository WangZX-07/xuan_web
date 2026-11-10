const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

const PROJECT_ROOT = path.resolve(__dirname, "..");
const REVIEW_FILE = path.join(PROJECT_ROOT, "design-review", "index.html");
const OUTPUT_DIR = path.join(PROJECT_ROOT, "design-review", "renders", "segments");
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const jobs = [
  {
    name: "public-desktop",
    width: 1440,
    height: 1000,
    views: [
      ["hero", null],
      ["problem", ".problem-statement"],
      ["capabilities", ".capabilities"],
      ["workflow", ".workflow"],
      ["tici", ".tici-section"],
      ["progress", ".progress-section"],
      ["safety", ".safety-section"],
      ["download", ".download-section"],
    ],
  },
  {
    name: "public-mobile",
    width: 390,
    height: 844,
    views: [
      ["hero", null],
      ["problem", ".problem-statement"],
      ["capabilities", ".capabilities"],
      ["workflow", ".workflow"],
      ["tici", ".tici-section"],
      ["progress", ".progress-section"],
      ["safety", ".safety-section"],
      ["download", ".download-section"],
    ],
  },
  { name: "admin-overview", width: 1440, height: 900, views: [["screen", null]] },
  { name: "admin-upload", width: 1440, height: 900, views: [["screen", null]] },
  { name: "admin-releases", width: 1440, height: 900, views: [["screen", null]] },
  { name: "admin-cms", width: 1440, height: 900, views: [["screen", null]] },
  { name: "admin-history", width: 1440, height: 900, views: [["screen", null]] },
];

app.commandLine.appendSwitch("force-device-scale-factor", "1");
app.commandLine.appendSwitch("disable-gpu");

app.whenReady().then(async () => {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const win = new BrowserWindow({
    width: 1440,
    height: 1000,
    show: false,
    useContentSize: true,
    backgroundColor: "#ffffff",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
    },
  });

  try {
    for (const job of jobs) {
      console.log(`loading ${job.name}`);
      win.setContentSize(job.width, job.height);
      const url = new URL(pathToFileURL(REVIEW_FILE));
      url.searchParams.set("screen", job.name);
      url.searchParams.set("capture", "1");
      await win.loadURL(url.toString());
      await win.webContents.executeJavaScript(`
        document.documentElement.style.scrollBehavior = 'auto';
        document.body.style.scrollBehavior = 'auto';
        document.querySelectorAll('[data-review-only], .review-toolbar').forEach((element) => element.remove());
      `, true);
      await Promise.race([
        win.webContents.executeJavaScript(`Promise.all([
          document.fonts ? document.fonts.ready : Promise.resolve(),
          Promise.all([...document.images].map((image) => image.complete
            ? Promise.resolve()
            : new Promise((resolve) => {
                image.addEventListener('load', resolve, { once: true });
                image.addEventListener('error', resolve, { once: true });
              })))
        ])`, true),
        delay(5000),
      ]);
      await delay(300);

      const dimensions = await win.webContents.executeJavaScript(`({
        width: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
        brokenImages: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length
      })`, true);
      console.log(`${job.name}: ${JSON.stringify(dimensions)}`);

      for (const [viewName, selector] of job.views) {
        const screenSelector = `[data-screen="${job.name}"]`;
        await win.webContents.executeJavaScript(selector
          ? `(() => { const screen = document.querySelector(${JSON.stringify(screenSelector)}); const el = screen && screen.querySelector(${JSON.stringify(selector)}); if (!el) throw new Error('Missing ${selector} in ${screenSelector}'); window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY, behavior: 'instant' }); })()`
          : "window.scrollTo({ top: 0, behavior: 'instant' })", true);
        await delay(180);
        const image = await win.webContents.capturePage();
        const outputPath = path.join(OUTPUT_DIR, `${job.name}-${viewName}.png`);
        fs.writeFileSync(outputPath, image.toPNG());
        console.log(outputPath);
      }
    }
  } catch (error) {
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
  } finally {
    win.destroy();
    app.quit();
  }
});
