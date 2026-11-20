const assert = require('node:assert/strict');
const { mkdir } = require('node:fs/promises');
const path = require('node:path');
const { after, before, test } = require('node:test');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const appUrl = pathToFileURL(path.join(__dirname, '../ui/index.html')).href;
const currentVersion = '1.8.1';
const releasePage = 'https://github.com/FZ-Labz/pdf-watermark/releases/latest';
let browser;

before(async () => {
  browser = await chromium.launch({ executablePath: process.env.PDF_WATERMARK_TEST_BROWSER });
});
after(async () => { await browser?.close(); });

async function openApp(context, { version = currentVersion, previous = null, every = 120, available = null } = {}) {
  const page = await browser.newPage();
  context.after(() => page.close());
  await page.clock.install({ time: new Date('2026-01-01T00:00:00Z') });
  await page.clock.pauseAt(new Date('2026-01-01T00:01:00Z'));
  await page.goto(appUrl);
  await page.evaluate(({ version, previous, every, available, releasePage }) => {
    const state = window.testUpdater = { available, checks: 0, installs: 0, opened: [] };
    window.pywebview = { api: {
      load_settings: async () => ({}),
      load_companies: async () => [],
      initial_sources: async () => [],
      app_info: async () => ({ version, updated_from: previous, check_every: every }),
      check_update: async () => {
        state.checks++;
        return state.available ? { version: state.available, page: releasePage } : null;
      },
      install_update: () => {
        state.installs++;
        return new Promise(resolve => { state.finishInstall = resolve; });
      },
      open_url: async url => { state.opened.push(url); },
      log_js_error: async () => {},
    } };
    window.dispatchEvent(new Event('pywebviewready'));
  }, { version, previous, every, available, releasePage });
  await page.getByText(`Version ${version}`, { exact: true }).waitFor();
  return page;
}

function card(page, mode) {
  return page.locator(`#update[data-mode="${mode}"]`);
}

async function screenshot(page, label) {
  const root = process.env.PDF_WATERMARK_REVIEW_IMAGES;
  if (!root) return;
  const directory = path.resolve(root, 'test_update_card');
  await mkdir(directory, { recursive: true });
  await page.screenshot({ path: path.join(directory, `${label}.png`), animations: 'disabled' });
}

test('checks at startup and every two minutes, and Later suppresses only the offered version', async context => {
  const page = await openApp(context, { available: '1.8.2' });
  await card(page, 'available').waitFor();
  assert.match(await card(page, 'available').innerText(), /Version 1\.8\.2/);
  assert.equal(await page.evaluate(() => window.testUpdater.checks), 1);
  await screenshot(page, '01-update-available');
  await page.getByRole('button', { name: 'Later', exact: true }).click();
  await page.locator('#update').waitFor({ state: 'hidden' });

  await page.clock.fastForward(119_999);
  assert.equal(await page.evaluate(() => window.testUpdater.checks), 1);
  await page.clock.fastForward(1);
  assert.equal(await page.evaluate(() => window.testUpdater.checks), 2);
  assert.equal(await page.locator('#update').isVisible(), false);

  await page.evaluate(() => { window.testUpdater.available = '1.8.3'; });
  await page.clock.fastForward(120_000);
  await card(page, 'available').waitFor();
  assert.match(await card(page, 'available').innerText(), /Version 1\.8\.3/);
  assert.equal(await page.evaluate(() => window.testUpdater.checks), 3);
  await screenshot(page, '02-newer-release-after-dismissal');
});

test('shows download progress, skips polling during install and offers a link after failure', async context => {
  const page = await openApp(context, { available: '1.8.2' });
  await page.getByRole('button', { name: 'Update now', exact: true }).click();
  await card(page, 'updating').waitFor();
  assert.equal(await page.getByRole('button', { name: 'Update now' }).isVisible(), false);
  await screenshot(page, '03-downloading');
  await page.clock.fastForward(120_000);
  assert.deepEqual(await page.evaluate(() => [window.testUpdater.checks, window.testUpdater.installs]), [1, 1]);

  await page.evaluate(() => window.testUpdater.finishInstall('Could not download the update.'));
  await card(page, 'failed').waitFor();
  assert.match(await card(page, 'failed').innerText(), /Could not download the update/);
  await screenshot(page, '04-download-failed');
  await page.getByRole('button', { name: 'Open download page' }).click();
  assert.deepEqual(await page.evaluate(() => window.testUpdater.opened), [releasePage]);
});

test('shows the new version after restart and stays quiet on later launches without updates', async context => {
  const page = await openApp(context, { version: '1.8.2', previous: currentVersion, every: 0 });
  await card(page, 'updated').waitFor();
  assert.match(await card(page, 'updated').innerText(), /now on version 1\.8\.2/);
  await screenshot(page, '05-upgrade-confirmed');
  await page.clock.fastForward(8_000);
  await page.locator('#update').waitFor({ state: 'hidden' });
  assert.equal(await page.evaluate(() => window.testUpdater.checks), 0);

  const nextLaunch = await openApp(context, { version: '1.8.2', every: 0 });
  await nextLaunch.clock.fastForward(120_000);
  assert.equal(await nextLaunch.locator('#update').isVisible(), false);
  assert.equal(await nextLaunch.evaluate(() => window.testUpdater.checks), 0);
  await screenshot(nextLaunch, '06-no-updates-offered');
});
