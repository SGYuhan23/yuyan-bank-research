const $ = (id) => document.getElementById(id);
let catalog, current, selectedId, parentId, poller;
const labels = {
  running: "执行中",
  failed: "执行失败",
  completed: "完成",
  accepted: "环评受理",
  proposed: "拟审批",
  approved: "环评批准",
  construction: "建设中",
  disclosed: "已披露",
  unknown: "未知",
  withdrawn: "已撤回",
  insufficient: "证据不足",
  needs_review: "待人工复核",
  project: "项目口径",
  consolidated: "合并口径",
  company: "法人口径",
  subsidiary: "子公司口径",
  source_audit_revision: "作者源文修订",
  rule_review_started: "规则复核",
  hypothesis_assertion_guard: "保守规则撤回",
  model_call: "模型调用",
  tool_started: "开始工具",
  tool_result: "工具完成",
  validation_failed: "校验未通过",
  run_failed: "运行失败",
  search_sources: "检索来源索引",
  read_source: "读取原文",
  calculate: "确定性计算",
};
const label = (x) => labels[x] || x;
const localtime = (x) =>
  new Date(x).toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    hour12: false,
  });
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
async function api(url, body) {
  const r = await fetch(
    url,
    body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {},
  );
  const d = await r.json();
  if (!r.ok) throw Error(d.error || r.status);
  return d;
}
function company() {
  return catalog.companies.find(
    (c) =>
      c.legal_name === $("company").value ||
      c.aliases.includes($("company").value),
  );
}
function sources() {
  const c = company();
  $("sources").innerHTML = c
    ? catalog.sources
        .filter((s) => s.company_ids.includes(c.company_id))
        .map(
          (s) =>
            `<label><input type="checkbox" name="source" value="${esc(s.source_id)}" checked><span>${esc(s.title)}<br><small>${esc(s.published_at)}</small></span></label>`,
        )
        .join("")
    : '<p class="small">请输入已核验样本企业名称。其他企业尚无资料，不自动补造。</p>';
}
async function history() {
  const list = (await api("/api/runs"))
    .filter((r) => !r.id.endsWith("-baseline"))
    .sort((a, b) => a.started_at.localeCompare(b.started_at));
  $("history").innerHTML = list
    .reverse()
    .map(
      (r) =>
        `<button data-run="${esc(r.id)}">${esc(catalog.companies.find((c) => c.company_id === r.company_id)?.legal_name || r.company_id)}<br><small>${esc(label(r.status))} · ${esc(localtime(r.started_at))}</small></button>`,
    )
    .join("");
  $("history")
    .querySelectorAll("button")
    .forEach((b) => (b.onclick = () => load(b.dataset.run)));
}
function cite(id) {
  const s = current.evidence.find((s) => s.source_id === id);
  return s
    ? `<a class="source" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)} · ${esc(s.published_at)}</a>`
    : esc(id);
}
function list(xs) {
  return "<ul>" + xs.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul>";
}
async function load(id) {
  selectedId = id;
  clearTimeout(poller);
  current = await api("/api/runs/" + id);
  const c = catalog.companies.find((c) => c.company_id === current.company_id);
  $("title").textContent = c?.legal_name || current.company_id;
  $("company").value = c?.legal_name || "";
  sources();
  $("status").textContent =
    `${current.status === "completed" ? "历史真实运行已完成，待人工复核" : current.status === "failed" ? "运行失败，未生成成功档案" : "实际研究执行中"} · ${current.mode === "author_source_audit_not_human_signoff" ? "作者源文校核 · 非人工签核" : current.mode === "live" ? "在线抓取原文" : current.mode === "deterministic_review_of_real_model_output" ? "历史模型输出的规则复核 · 本轮未调用模型" : "保存原文读取"} · ${localtime(current.started_at)}（北京时间） · ${current.run_id}`;
  $("progress").innerHTML = current.records
    .map(
      (r) =>
        `<div class="step">${r.sequence}. ${esc(label(r.kind))} ${esc(label(r.tool) || r.phase || "")} ${esc(r.error || r.decision_summary || "")}</div>`,
    )
    .join("");
  $("progress").scrollTop = $("progress").scrollHeight;
  $("export").hidden = !current.result;
  if (!current.result) {
    $("content").innerHTML =
      '<div class="empty"><h3>以实际工具结果为准</h3><p>完成前不显示预置判断。读取失败会保留失败状态。</p></div>';
    if (current.status === "running")
      poller = setTimeout(() => load(id).catch(error), 1500);
    return;
  }
  $("export").href = "/api/runs/" + id + "/export";
  $("export").download = "渝研-" + current.company_id + ".md";
  render();
  await history();
}
function render() {
  const d = current.result.dossier,
    delta = current.result.delta;
  let html = `<div class="card warning"><strong>研究草稿，须使用者最终复核</strong><p class="small">通过引用校验不等于判断正确。历史样本包含已知错误，见评测报告；本页保留原文供审阅，不能直接当成客户事实或产品建议。</p></div><div class="card"><span class="label">发生什么</span><p>${esc(d.what_changed)}</p><span class="label">为什么值得了解 · 待核实判断</span><p>${esc(d.why_relevant)}</p></div><h3>下一步问什么</h3>${list(d.next_questions)}`;
  if (current.result.parent_run_id)
    html += `<div class="card warning"><h3>与父版本相比</h3><p>新增事实：${esc(delta.new_facts.join("、") || "无")}<br>被替代事件：${esc(delta.superseded_events.join("、") || "无")}<br>已撤回假设：${esc(delta.withdrawn_hypotheses.join("、") || "无")}</p><small>历史事实保留。旧版本人工确认不自动继承。</small></div>`;
  html +=
    "<h3>公开事实与出处</h3>" +
    d.facts
      .map(
        (f) =>
          `<div class="card"><p>${esc(f.statement)}</p>${cite(f.source_id)}<p class="small">${esc(f.page_or_section)} · ${esc(f.period)} · ${esc(label(f.scope))}</p><details><summary>查看原文</summary><div class="quote">${esc(f.excerpt)}</div></details><p class="small">限制：${esc(f.limitations)}</p></div>`,
      )
      .join("");
  html +=
    "<h3>事件阶段</h3>" +
    d.events
      .map(
        (e) =>
          `<div class="card"><p>${esc(e.event_type)} · ${esc(label(e.stage))}</p><small>事件 ${esc(e.event_date || "未知")} / 发布 ${esc(e.published_at)} / 项目 ${esc(e.project_id || "无")}<br>替代 ${esc(e.supersedes.join("、") || "无")} / 冲突 ${esc(e.conflicts.join("、") || "无")}</small></div>`,
      )
      .join("");
  html +=
    "<h3>程序计算</h3>" +
    (current.calculations.length
      ? current.calculations
          .map(
            (c) =>
              `<div class="card"><p>${esc(c.formula)} = <strong>${esc(c.result)} ${esc(c.result_unit)}</strong></p><small>输入 ${esc(c.inputs.left)}、${esc(c.inputs.right)} ${esc(c.inputs.unit)} · ${esc(c.inputs.period)}</small></div>`,
          )
          .join("")
      : '<p class="small">本次未执行计算。</p>');
  html +=
    "<h3>服务假设 · 可以确认、修改或撤回</h3>" +
    d.hypotheses
      .map(
        (h, i) =>
          `<div class="card ${h.status === "withdrawn" ? "warning" : ""}"><span class="label">${esc(label(h.status))}</span><h3>${esc(h.title)}</h3><p>${esc(h.reasoning_summary)}</p><p class="small">支持：${h.supporting_evidence.map(cite).join(" / ") || "无"}<br>反证：${h.counter_evidence.map(cite).join(" / ") || "未发现不等于不存在"}</p><strong class="small">仍需了解</strong>${list(h.missing_information)}${list(h.questions_to_verify)}<details class="review"><summary>人工复核此假设</summary><form data-review="${i}"><select name="action"><option value="confirm">确认待访方向</option><option value="modify">修改</option><option value="withdraw">撤回</option></select><input name="reviewer" placeholder="复核人" required><textarea name="text" placeholder="修改后的内容（修改时必填）"></textarea><textarea name="note" placeholder="复核依据及限制" required></textarea><button>保存复核记录</button></form></details></div>`,
      )
      .join("");
  html += `<h3>人工复核记录</h3>${(current.reviews || []).map((r) => `<div class="card"><p>${esc(r.reviewer)} · ${esc(r.action)} · ${esc(r.note)}</p><p>${esc(r.after.review_text)}</p><small>证据版本 ${esc(r.evidence_version.slice(0, 12))} · ${esc(r.created_at)}</small></div>`).join("") || '<p class="small">尚无人工复核。</p>'}<div class="card warning"><h3>资料覆盖与停止原因</h3><p>${esc(d.coverage_limit)}</p><p>${esc(d.stop_reason)}</p>${list(d.missing_information)}</div><button id="update">以此档案更新（使用左侧所选资料）</button><details><summary>实际 trace / 证据版本</summary><pre>${esc(JSON.stringify({ version: current.result.evidence_version, records: current.records }, null, 2))}</pre></details>`;
  $("content").innerHTML = html;
  $("update").onclick = () => {
    parentId = selectedId;
    start();
  };
  document.querySelectorAll("[data-review]").forEach(
    (f) =>
      (f.onsubmit = async (e) => {
        e.preventDefault();
        try {
          const data = Object.fromEntries(new FormData(f));
          await api("/api/reviews", {
            ...data,
            run_id: selectedId,
            hypothesis_id: d.hypotheses[+f.dataset.review].hypothesis_id,
            evidence_version: current.result.evidence_version,
          });
          await load(selectedId);
        } catch (e) {
          error(e);
        }
      }),
  );
}
function error(e) {
  $("form-error").textContent = e.message;
  $("start").disabled = false;
}
async function start() {
  try {
    const c = company();
    if (!c) throw Error("此企业尚未核验，请选择样本。不会生成虚构档案。");
    $("start").disabled = true;
    $("form-error").textContent = "";
    const r = await api("/api/runs", {
      company_id: c.company_id,
      task: $("task").value,
      mode: $("source-mode").value,
      source_ids: [...document.querySelectorAll("[name=source]:checked")].map(
        (x) => x.value,
      ),
      parent: parentId,
    });
    parentId = null;
    $("start").disabled = false;
    await load(r.id);
  } catch (e) {
    error(e);
  }
}
$("research").onsubmit = (e) => {
  e.preventDefault();
  parentId = null;
  start();
};
$("company").onchange = sources;
$("import").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const c = company();
    if (!c) throw Error("先选择明确企业主体");
    await api("/api/sources", {
      company_id: c.company_id,
      url: $("new-url").value,
      title: $("new-title").value,
      publisher: $("new-publisher").value,
      published_at: $("new-date").value,
      period: $("new-period").value,
      pages: $("new-pages").value.split(",").map(Number),
    });
    catalog = await api("/api/catalog");
    sources();
    $("form-error").textContent =
      "资料已读取并加入。请点击以此档案更新，重新检验判断。";
  } catch (e) {
    error(e);
  }
};
(async () => {
  try {
    catalog = await api("/api/catalog");
    $("mode").textContent = catalog.model_configured
      ? "本地实际模型研究 · 未发布线上"
      : "本地服务 · 模型未配置";
    $("companies").innerHTML = catalog.companies
      .map((c) => `<option value="${esc(c.legal_name)}">`)
      .join("");
    await history();
  } catch (e) {
    $("mode").textContent = "静态文件预览 · 无实时Agent";
    $("start").disabled = true;
    $("form-error").textContent =
      "请按README启动本地服务。此静态页面不会模拟在线执行。";
  }
})();
