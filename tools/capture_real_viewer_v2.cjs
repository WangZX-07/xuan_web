const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const TICI_PATH = path.join(ROOT, "lungtic-website", ".review-runtime", "synthetic-lung-demo.tici");
const OUTPUT_PATH = path.join(ROOT, "lungtic-website", "design-review", "assets", "real-tici-workbench.png");
const REVIEW_USERNAME = process.env.LUNGTIC_REVIEW_USERNAME;
const REVIEW_PASSWORD = process.env.LUNGTIC_REVIEW_PASSWORD;
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitFor(win, expression, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await win.webContents.executeJavaScript(`Boolean(${expression})`, true)) return;
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${expression}`);
}

async function setFileInput(win, filePath) {
  const debug = win.webContents.debugger;
  debug.attach("1.3");
  try {
    const { root } = await debug.sendCommand("DOM.getDocument", { depth: -1, pierce: true });
    const { nodeId } = await debug.sendCommand("DOM.querySelector", {
      nodeId: root.nodeId,
      selector: 'input[type="file"]',
    });
    if (!nodeId) throw new Error("TICI file input was not found");
    await debug.sendCommand("DOM.setFileInputFiles", { files: [filePath], nodeId });
  } finally {
    debug.detach();
  }
}

app.commandLine.appendSwitch("force-device-scale-factor", "1");
app.commandLine.appendSwitch("disable-gpu");

app.whenReady().then(async () => {
  if (!REVIEW_USERNAME || !REVIEW_PASSWORD) {
    throw new Error("Set LUNGTIC_REVIEW_USERNAME and LUNGTIC_REVIEW_PASSWORD before capture.");
  }

  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
    backgroundColor: "#f5f7fa",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
    },
  });

  let stage = "load-login";
  try {
    await win.loadURL("http://127.0.0.1:5173/#/login");
    stage = "authenticate";
    const loginResult = await win.webContents.executeJavaScript(`
      fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: ${JSON.stringify(REVIEW_USERNAME)},
          password: ${JSON.stringify(REVIEW_PASSWORD)},
          role: 'admin'
        })
      }).then(async (response) => {
        const body = await response.json().catch(() => ({}));
        return { ok: response.ok, status: response.status, body };
      })
    `, true);
    if (!loginResult.ok) {
      throw new Error(`Login returned ${loginResult.status}: ${JSON.stringify(loginResult.body)}`);
    }
    const login = loginResult.body;

    await win.webContents.executeJavaScript(`
      localStorage.setItem('lungtic_token', ${JSON.stringify(login.access_token)});
      window.location.hash = '#/dashboard/tici-viewer';
    `, true);

    stage = "open-viewer";
    await waitFor(win, "document.querySelector('.open-panel')");
    stage = "select-synthetic-file";
    await setFileInput(win, TICI_PATH);
    stage = "render-tici";
    await waitFor(win, "document.querySelector('.viewer-shell') && document.querySelector('.image-layer')", 60000);
    await delay(2500);
    await win.webContents.executeJavaScript(`
      document.querySelectorAll('.n-layout-header .n-tag, .n-layout-header .n-button')
        .forEach((element) => { element.style.visibility = 'hidden'; });
    `, true);

    stage = "verify-synthetic-labels";
    const state = await win.webContents.executeJavaScript(`({
      hash: location.hash,
      viewer: Boolean(document.querySelector('.viewer-shell')),
      image: Boolean(document.querySelector('.image-layer')),
      patient: document.body.innerText.includes('SYNTHETIC-ONLY'),
      phase: document.body.innerText.includes('Phase 1')
    })`, true);
    console.log(JSON.stringify(state));

    stage = "write-screenshot";
    fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
    const image = await win.webContents.capturePage();
    fs.writeFileSync(OUTPUT_PATH, image.toPNG());
    console.log(OUTPUT_PATH);
  } catch (error) {
    console.error(`Capture failed during ${stage}: ${error && error.stack ? error.stack : error}`);
    process.exitCode = 1;
  } finally {
    win.destroy();
    app.quit();
  }
});
