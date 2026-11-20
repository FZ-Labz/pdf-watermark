const assert = require('node:assert/strict');
const { execFileSync, spawn } = require('node:child_process');
const { once } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');
const { chromium } = require('playwright');

const nativeTestId = 'PDFWatermarkUpgradeTest';
const baselineVersion = '0.0.1';
const executable = 'PDF Watermark.exe';
const port = 9341;

async function connectToVersion(version) {
  const deadline = Date.now() + 90_000;
  let lastError;
  while (Date.now() < deadline) {
    let browser;
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`, { timeout: 2_000 });
      for (const context of browser.contexts()) {
        for (const page of context.pages()) {
          if (await page.getByText(`Version ${version}`, { exact: true }).isVisible()) return { browser, page };
        }
      }
    } catch (error) {
      lastError = error;
    }
    await browser?.close();
    await delay(250);
  }
  throw new Error(`Could not find the installed app running version ${version}`, { cause: lastError });
}

function pack(source, feed, version) {
  execFileSync('vpk', ['pack', '--packId', nativeTestId, '--packVersion', version,
    '--packDir', source, '--mainExe', executable, '--packTitle', 'PDF Watermark Upgrade Test',
    '--outputDir', feed, '--framework', 'webview2'], { stdio: 'inherit', timeout: 180_000, windowsHide: true });
}

async function capture(page, name) {
  if (!process.env.PDF_WATERMARK_REVIEW_IMAGES) return;
  const folder = path.resolve(process.env.PDF_WATERMARK_REVIEW_IMAGES, 'test_windows_upgrade');
  fs.mkdirSync(folder, { recursive: true });
  await page.screenshot({ path: path.join(folder, `${name}.png`), animations: 'disabled' });
}

async function run() {
  assert.equal(process.platform, 'win32');
  const portable = process.argv.includes('--portable');
  if (!portable) {
    assert.equal(process.env.GITHUB_ACTIONS, 'true', 'Use --portable locally or run Setup on a disposable runner.');
  }
  const root = fs.mkdtempSync(path.join(process.env.RUNNER_TEMP || os.tmpdir(), 'pdf-watermark-upgrade-'));
  const application = path.resolve('dist', 'PDF Watermark');
  const builtVersion = fs.readFileSync(path.join(application, '_internal', 'VERSION'), 'utf8').trim();
  assert.match(builtVersion, /^\d+\.\d+\.\d+$/);
  assert.notEqual(builtVersion, baselineVersion);

  const baselineApp = path.join(root, 'baseline-app');
  const baselineFeed = path.join(root, 'baseline-feed');
  const candidateFeed = path.join(root, 'candidate-feed');
  fs.cpSync(application, baselineApp, { recursive: true });
  fs.writeFileSync(path.join(baselineApp, '_internal', 'VERSION'), `${baselineVersion}\n`);
  pack(baselineApp, baselineFeed, baselineVersion);
  pack(application, candidateFeed, builtVersion);

  const appData = path.join(root, 'roaming');
  const settingsDir = path.join(appData, 'PDF Watermark');
  fs.mkdirSync(settingsDir, { recursive: true });
  const settingsPath = path.join(settingsDir, 'settings.json');
  const settings = { v: 3, opacity: 0.6, prefixText: 'FOR REVIEW' };
  fs.writeFileSync(settingsPath, JSON.stringify(settings));
  const log = path.join(settingsDir, 'app.log');
  const env = {
    ...process.env,
    APPDATA: appData,
    PDF_WATERMARK_UPDATE_URL: candidateFeed,
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port}`,
    WEBVIEW2_USER_DATA_FOLDER: path.join(root, 'webview'),
  };

  let installRoot;
  if (portable) {
    installRoot = path.join(root, 'portable');
    fs.mkdirSync(installRoot);
    execFileSync('tar.exe', ['-xf', path.join(baselineFeed, `${nativeTestId}-win-Portable.zip`), '-C', installRoot], {
      stdio: 'inherit', timeout: 90_000, windowsHide: true,
    });
  } else {
    installRoot = path.join(process.env.LOCALAPPDATA, nativeTestId);
    execFileSync(path.join(baselineFeed, `${nativeTestId}-win-Setup.exe`), ['--silent'], {
      env, stdio: 'inherit', timeout: 90_000, windowsHide: true,
    });
  }
  const installed = path.join(installRoot, 'current', executable);
  assert.ok(fs.existsSync(installed), `Missing installed app at ${installed}`);
  const app = spawn(installed, [], { cwd: root, env, stdio: 'ignore', windowsHide: true });
  let beforeUpdate;
  let afterUpdate;
  try {
    await once(app, 'spawn');
    beforeUpdate = await connectToVersion(baselineVersion);
    const offer = beforeUpdate.page.locator('#update[data-mode="available"]');
    await offer.waitFor({ timeout: 30_000 });
    assert.ok((await offer.innerText()).includes(`Version ${builtVersion} is ready`));
    await capture(beforeUpdate.page, '01-native-update-offered');
    await offer.getByRole('button', { name: 'Update now', exact: true }).click();

    afterUpdate = await connectToVersion(builtVersion);
    const confirmation = afterUpdate.page.locator('#update[data-mode="updated"]');
    await confirmation.waitFor({ timeout: 5_000 });
    assert.ok((await confirmation.innerText()).includes(`now on version ${builtVersion}`));
    await capture(afterUpdate.page, '02-native-update-confirmed');
    assert.equal(app.exitCode, 0, 'The old process should exit after handing off to Velopack.');
    assert.deepEqual(JSON.parse(fs.readFileSync(settingsPath, 'utf8')), settings);
    assert.equal(fs.readFileSync(path.join(settingsDir, 'version.txt'), 'utf8').trim(), builtVersion);
    console.log(`Installed update from ${baselineVersion} to ${builtVersion}; settings preserved.`);
  } finally {
    await beforeUpdate?.browser.close();
    await afterUpdate?.browser.close();
    if (app.exitCode === null) app.kill();
    if (fs.existsSync(log)) console.log(fs.readFileSync(log, 'utf8'));
    // The restarted app has a different PID. Close only this test copy.
    execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
      "Get-Process -Name 'PDF Watermark' -ErrorAction SilentlyContinue | Where-Object Path -eq $env:PDF_WATERMARK_TEST_EXE | Stop-Process -ErrorAction SilentlyContinue"], {
      env: { ...process.env, PDF_WATERMARK_TEST_EXE: installed }, timeout: 10_000, windowsHide: true,
    });
  }
}

run().catch(error => { console.error(error); process.exitCode = 1; });
