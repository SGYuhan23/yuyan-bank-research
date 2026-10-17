const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("fs");
process.chdir(require("path").resolve(__dirname, "../.."));
(async () => {
  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:8765");
  await page.getByText("本地实际模型研究 · 未发布线上").waitFor();
  await page.locator('[data-run="qinan-source-audited"]').click();
  await page.getByRole("heading", { name: "公开事实与出处" }).waitFor();
  await page.screenshot({
    path: "client-research/docs/desktop.png",
    fullPage: true,
  });
  const original = await (
    await page.request.get("http://127.0.0.1:8765/api/runs/qinan-v3")
  ).json();
  const review = {
    run_id: "qinan-v3",
    hypothesis_id: "h1",
    evidence_version: original.result.evidence_version,
    action: "modify",
    reviewer: "自动化验收（非人工业务确认）",
    text: "测试修改：不得直接认定资金压力。",
    note: "自动化API持久化验收，不代表客户经理确认。",
  };
  const saved = await page.request.post("http://127.0.0.1:8765/api/reviews", {
    data: review,
  });
  if (!saved.ok()) throw Error("review save failed");
  const reread = await (
    await page.request.get("http://127.0.0.1:8765/api/runs/qinan-v3")
  ).json();
  if (!reread.reviews.some((r) => r.note === review.note))
    throw Error("review not persistent");
  const stale = await page.request.post("http://127.0.0.1:8765/api/reviews", {
    data: { ...review, evidence_version: "stale" },
  });
  if (stale.status() !== 400) throw Error("stale review accepted");
  const exportResponse = await page.request.get(
    "http://127.0.0.1:8765/api/runs/rifa-initial/export",
  );
  if (
    !exportResponse.ok() ||
    !(await exportResponse.text()).includes("访前档案")
  )
    throw Error("Export failed");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "client-research/docs/mobile.png",
    fullPage: true,
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > innerWidth,
  );
  if (overflow) throw Error("Mobile overflow");
  const bad = await page.request.post("http://127.0.0.1:8765/api/sources", {
    data: { url: "http://127.0.0.1:8080" },
  });
  if (bad.status() !== 400) throw Error("SSRF guard failed");
  const cross = await page.request.post("http://127.0.0.1:8765/api/runs", {
    headers: { Origin: "https://example.com" },
    data: {},
  });
  if (cross.status() !== 403) throw Error("Origin guard failed");
  if (errors.length) throw Error(errors.join("\n"));
  fs.writeFileSync(
    "client-research/docs/browser-results.json",
    JSON.stringify(
      {
        tested_at: new Date().toISOString(),
        checks: [
          "catalog connection",
          "real historical run rendering",
          "markdown export",
          "390px no horizontal overflow",
          "private source rejected",
          "cross-origin write rejected",
          "review saved and reloaded",
          "stale evidence review rejected",
        ],
        page_errors: errors,
      },
      null,
      2,
    ),
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
