// Actual authenticated browser smoke; LIVE_BROWSER_RUN=1 also calls the model.
const { chromium } = require('../agent-platform/frontend/node_modules/@playwright/test');
const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const ctx = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 1000 } });
    const credentials = JSON.parse(fs.readFileSync(path.join(__dirname, '../agent-platform/.deer-flow/acceptance/account.json')));
    const login = await ctx.request.post('http://127.0.0.1:3000/api/v1/auth/login/local', {
      form: { username: credentials.email, password: credentials.password }, headers: { Origin: 'http://127.0.0.1:3000' },
    });
    assert.equal(login.status(), 200);
    await ctx.addCookies([{ name: 'locale', value: 'zh-CN', domain: '127.0.0.1', path: '/' }]);
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:3000/', { waitUntil: 'networkidle' });
    assert.match(page.url(), /workspace\/chats\/new$/);
    await page.locator('textarea').waitFor({ state: 'visible', timeout: 60000 });
    assert.equal(await page.locator('textarea').count(), 1);
    await page.screenshot({ path: path.join(__dirname, 'evidence/general-home.png') });
    const checks = { login: true, chat_entry: true };
    if (process.env.LIVE_BROWSER_RUN === '1') {
      await page.locator('textarea').fill('请直接回复：连接检查通过。不需要工具，不要创建文件。');
      await page.locator('textarea').press('Enter');
      await page.waitForURL(/workspace\/chats\/(?!new)[a-f0-9-]+$/, { timeout: 60000 });
      await page.getByText('连接检查通过。', { exact: true }).or(page.getByText('连接检查通过', { exact: true })).first().waitFor({ timeout: 90000 });
      checks.live_chat = true;
    }
    const passed = fs.readdirSync(path.join(__dirname, 'evidence')).filter(n => n.startsWith('live-') && n.endsWith('.json'))
      .map(n => ({ n, modified: fs.statSync(path.join(__dirname, 'evidence', n)).mtimeMs }))
      .sort((a, b) => b.modified - a.modified)
      .map(({ n }) => JSON.parse(fs.readFileSync(path.join(__dirname, 'evidence', n))))
      .find(x => x.checks?.first_total && x.checks?.second_total);
    assert.ok(passed, 'Run live_acceptance.py first');
    await page.goto('http://127.0.0.1:3000/workspace/chats/' + passed.thread_id, { waitUntil: 'networkidle' });
    await page.getByText('report-v2.html', { exact: true }).first().click();
    const preview = page.getByLabel('预览', { exact: true });
    await preview.waitFor({ timeout: 60000 });
    await preview.click();
    await page.locator('iframe').first().waitFor({ timeout: 60000 });
    await page.screenshot({ path: path.join(__dirname, 'evidence/general-artifact.png') });
    checks.artifact_preview = true;
    await page.reload({ waitUntil: 'networkidle' });
    assert.ok(await page.getByText('report-v2.html', { exact: true }).count());
    checks.reload_retains_history = true;
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://127.0.0.1:3000/workspace/chats/new', { waitUntil: 'networkidle' });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: path.join(__dirname, 'evidence/general-mobile.png') });
    checks.mobile_no_overflow = true;
    assert.deepEqual(errors, []);
    checks.no_page_errors = true;
    fs.writeFileSync(path.join(__dirname, 'evidence/general-browser.json'), JSON.stringify({ checks }, null, 2));
    console.log(JSON.stringify(checks));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
