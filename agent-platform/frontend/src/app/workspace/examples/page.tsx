"use client";

import {
  ArrowUpRight,
  Download,
  BookOpen,
  ImageIcon,
  Workflow,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SidebarTrigger } from "@/components/ui/sidebar";

type Result = {
  strategy: string;
  stress: string;
  rm: number;
  loan: number;
  deposit: number;
  interest: number;
  funding: number;
  ftp: number;
  fees: number;
  el: number;
  service: number;
  contribution: number;
  hours: number;
  capacity: number;
  feasible: boolean;
  concentration: number;
};
type Data = {
  version: string;
  disclosure: string;
  strategies: string[];
  stresses: string[];
  results: Result[];
  assumptions: {
    parameter: string;
    value: string;
    type: string;
    reason: string;
  }[];
  sources: {
    title: string;
    url: string;
    published: string;
    period: string;
    fact: string;
    type: string;
    retrieved: string;
  }[];
};
const number = (v: number) =>
  v.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
const card = "rounded-2xl border bg-card p-6 shadow-sm";

export default function ExamplesPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [stress, setStress] = useState("正常环境");
  const [rm, setRm] = useState(3);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const c = new AbortController();
    setError(false);
    void fetch("/examples/fuling/results.json", { signal: c.signal })
      .then((r) => {
        if (!r.ok) throw Error();
        return r.json() as Promise<Data>;
      })
      .then(setData)
      .catch(() => {
        if (!c.signal.aborted) setError(true);
      });
    return () => c.abort();
  }, [retry]);
  const rows =
    data?.results.filter((x) => x.stress === stress && x.rm === rm) ?? [];
  const baseline = rows[0];
  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-10">
        <div className="mb-4 md:hidden">
          <SidebarTrigger aria-label="打开导航" />
        </div>
        <header className="mb-10 flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-muted-foreground mb-3 text-xs tracking-[0.2em]">
              渝研 / 成果与实验
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">
              {selected === "fuling"
                ? "涪陵 · 2027经营情景研究"
                : selected === "image"
                  ? "从原图到新版本"
                  : selected === "diagram"
                    ? "复杂流程的可编辑交付"
                    : "先看成果，再开始自己的研究"}
            </h1>
            <p className="text-muted-foreground mt-3 max-w-2xl text-sm leading-7">
              {selected
                ? "独立作品 · 合成案例 · 可检查来源与计算过程"
                : "直接打开报告、图片和图形。无需输入提示词；需要自己的结果时，再进入 Agent 工作台。"}
            </p>
          </div>
          <Link
            href="/workspace/chats/new"
            className="bg-primary text-primary-foreground inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm"
          >
            开始新任务 <ArrowUpRight size={16} />
          </Link>
        </header>
        {selected && (
          <button
            className="mb-6 flex items-center gap-2 text-sm underline underline-offset-4"
            onClick={() => setSelected(null)}
          >
            <ArrowLeft size={16} />
            返回全部案例
          </button>
        )}
        {!selected && (
          <div className="grid gap-5 md:grid-cols-3">
            <button
              className={`${card} text-left transition hover:-translate-y-1 hover:shadow-md`}
              onClick={() => setSelected("fuling")}
            >
              <div className="mb-7 flex h-40 items-end rounded-xl bg-emerald-950 p-6 text-emerald-50">
                <BookOpen size={42} />
                <span className="ml-auto text-4xl font-light">2027</span>
              </div>
              <p className="text-xs text-emerald-700 dark:text-emerald-400">
                经营研究 · 计算实验版
              </p>
              <h2 className="my-3 text-xl font-semibold">
                有限资源，如何配置？
              </h2>
              <p className="text-muted-foreground text-sm leading-6">
                120户合成客户，5种经营策略，7类压力情景。打开即可比较收益、风险和人员约束。
              </p>
              <span className="mt-6 inline-flex items-center gap-2 text-sm font-medium">
                打开研究 <ArrowUpRight size={16} />
              </span>
            </button>
            <button
              className={`${card} text-left transition hover:-translate-y-1 hover:shadow-md`}
              onClick={() => setSelected("image")}
            >
              <img
                src="/examples/image-edit.png"
                alt="真实图片模型编辑后的窗边橘猫"
                className="mb-7 h-40 w-full rounded-xl object-cover"
              />
              <p className="text-xs text-violet-700 dark:text-violet-400">
                图片创作 · 真实模型运行
              </p>
              <h2 className="my-3 text-xl font-semibold">保留主体，修改环境</h2>
              <p className="text-muted-foreground text-sm leading-6">
                生成后继续编辑。查看原图与夜景版本，原始文件保持不变。
              </p>
              <span className="mt-6 inline-flex items-center gap-2 text-sm font-medium">
                查看图片 <ImageIcon size={16} />
              </span>
            </button>
            <button
              className={`${card} text-left transition hover:-translate-y-1 hover:shadow-md`}
              onClick={() => setSelected("diagram")}
            >
              <div className="mb-7 flex h-40 items-center justify-center rounded-xl bg-sky-50 text-sky-800 dark:bg-sky-950 dark:text-sky-200">
                <Workflow size={68} />
              </div>
              <p className="text-xs text-sky-700 dark:text-sky-400">
                流程设计 · SVG + Draw.io
              </p>
              <h2 className="my-3 text-xl font-semibold">分支、汇合与反馈</h2>
              <p className="text-muted-foreground text-sm leading-6">
                自动分层排布，保留反馈路径。预览后下载可继续修改的图形源文件。
              </p>
              <span className="mt-6 inline-flex items-center gap-2 text-sm font-medium">
                打开流程图 <ArrowUpRight size={16} />
              </span>
            </button>
          </div>
        )}
        {selected === "image" && (
          <section className={card}>
            <div className="grid gap-6 md:grid-cols-2">
              {["image-original", "image-edit"].map((name, i) => (
                <figure key={name}>
                  <img
                    className="w-full rounded-xl"
                    src={`/examples/${name}.png`}
                    alt={i ? "编辑后的夜景" : "原始水彩橘猫"}
                  />
                  <figcaption className="mt-3 text-sm">
                    {i
                      ? "编辑版本：蓝紫色夜空与月亮"
                      : "原图：窗边橘猫水彩插画"}
                  </figcaption>
                </figure>
              ))}
            </div>
            <p className="text-muted-foreground mt-6 text-sm leading-7">
              真实 Qwen Image 2.0
              生成与编辑。修改要求：保留橘猫与窗边水彩构图，将窗外改为蓝紫色夜空与月亮。图像编辑是生成式变换，不保证未指定区域逐像素不变。验收时间：2026-10-13；已验证原文件哈希未变。
            </p>
            <a
              className="mt-4 inline-flex items-center gap-2 underline"
              href="/examples/image-edit.png"
              download
            >
              <Download size={16} />
              下载编辑结果
            </a>
          </section>
        )}
        {selected === "diagram" && (
          <section className={card}>
            <img
              src="/examples/process.svg"
              alt="研究任务的分支汇合与反馈流程"
              className="max-h-[70vh] w-full object-contain"
            />
            <div className="mt-6 flex flex-wrap gap-6">
              {["svg", "drawio"].map((ext) => (
                <a
                  key={ext}
                  className="inline-flex items-center gap-2 underline"
                  href={`/examples/process.${ext}`}
                  download
                >
                  <Download size={16} />
                  下载 {ext.toUpperCase()}
                </a>
              ))}
            </div>
            <p className="text-muted-foreground mt-4 text-sm">
              这是确定性图形工具生成的示例；支持24个节点与48条连线。密集网络仍可能出现连线交叉，下载源文件后可进一步调整。
            </p>
          </section>
        )}
        {selected === "fuling" &&
          (error ? (
            <div role="alert" className={card}>
              研究数据加载失败。
              <button
                className="ml-3 underline"
                onClick={() => setRetry(retry + 1)}
              >
                重试
              </button>
            </div>
          ) : !data ? (
            <p role="status">正在读取计算结果…</p>
          ) : (
            <div className="space-y-6">
              <section className={card}>
                <p className="text-xs font-medium text-emerald-700 dark:text-emerald-400">
                  阅读结论之前
                </p>
                <h2 className="mt-3 text-xl font-semibold">
                  这是一项可复算的经营实验，不是真实支行预算。
                </h2>
                <p className="text-muted-foreground mt-4 text-sm leading-7">
                  {data.disclosure}{" "}
                  本版已完成组合计算、策略比较与压力测试；完整区域产业研究、公开年报参数校准及15–25页正式报告尚在扩充。
                </p>
                <p className="mt-4 text-sm leading-7">
                  研究问题：贷款扩张增加收入，也消耗资金和风险预算；低成本负债能改善资金贡献，但获客和服务需要人手。不能仅按贷款规模挑选方案。
                </p>
              </section>
              <section className={card}>
                <div className="flex flex-wrap items-end justify-between gap-6">
                  <div>
                    <h2 className="text-xl font-semibold">比较经营方案</h2>
                    <p className="text-muted-foreground mt-2 text-sm">
                      单位：万元 / 年。选择情景即可读取 Python
                      模型的可复算结果。
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-4">
                    <label className="text-sm">
                      压力情景
                      <select
                        aria-label="压力情景"
                        value={stress}
                        onChange={(e) => setStress(e.target.value)}
                        className="bg-background mt-2 block rounded-lg border p-2"
                      >
                        {data.stresses.map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                    <label className="text-sm">
                      客户经理人数
                      <select
                        aria-label="客户经理人数"
                        value={rm}
                        onChange={(e) => setRm(Number(e.target.value))}
                        className="bg-background mt-2 block rounded-lg border p-2"
                      >
                        {Array.from({ length: 12 }, (_, i) => i + 1).map(
                          (n) => (
                            <option key={n}>{n}</option>
                          ),
                        )}
                      </select>
                    </label>
                  </div>
                </div>
                <div className="mt-6 overflow-x-auto">
                  <table className="w-full min-w-[680px] text-left text-sm">
                    <thead className="text-muted-foreground border-b">
                      <tr>
                        {[
                          "策略",
                          "贷款",
                          "存款",
                          "风险调整贡献",
                          "较基线",
                          "预期损失代理",
                          "产能",
                        ].map((h) => (
                          <th key={h} className="px-3 py-3 font-medium">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r) => (
                        <tr className="border-b last:border-0" key={r.strategy}>
                          <th className="px-3 py-4 font-medium">
                            {r.strategy}
                          </th>
                          <td className="px-3">{number(r.loan)}</td>
                          <td className="px-3">{number(r.deposit)}</td>
                          <td className="px-3 font-medium">
                            {number(r.contribution)}
                          </td>
                          <td className="px-3">
                            {number(
                              r.contribution - (baseline?.contribution ?? 0),
                            )}
                          </td>
                          <td className="px-3">{number(r.el)}</td>
                          <td className="px-3">
                            {r.feasible ? "可覆盖" : "超出产能"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-muted-foreground mt-5 text-sm leading-7">
                  负值表示在给定假设下无法覆盖资金、风险和人员成本，不应隐藏。贡献
                  = 贷款利息 − 存款成本 + 净资金FTP + 手续费 − 预期损失代理 −
                  人员成本；不等于财务报表净利润。策略没有自动获得“最优”标签。
                </p>
              </section>
              <section className="grid gap-6 md:grid-cols-2">
                <div className={card}>
                  <h2 className="text-xl font-semibold">假设账本</h2>
                  <div className="mt-4 space-y-4">
                    {data.assumptions.map((a) => (
                      <div
                        key={a.parameter}
                        className="border-b pb-4 last:border-0"
                      >
                        <p className="text-sm font-medium">
                          {a.parameter} · {a.value}
                        </p>
                        <p className="text-muted-foreground mt-1 text-xs leading-6">
                          {a.type} / {a.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className={card}>
                  <h2 className="text-xl font-semibold">公开证据与边界</h2>
                  {data.sources.map((s) => (
                    <div className="mt-5" key={s.url}>
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm font-medium underline underline-offset-4"
                      >
                        {s.title} ↗
                      </a>
                      <p className="mt-2 text-sm leading-6">{s.fact}</p>
                      <p className="text-muted-foreground mt-2 text-xs leading-6">
                        {s.type} · 统计期 {s.period}
                        <br />
                        发布：{s.published} · 读取：{s.retrieved}
                      </p>
                    </div>
                  ))}
                  <p className="text-muted-foreground mt-5 text-sm leading-7">
                    区域增速不能推导具体客户信用或支行贷款增长率。当前未获得客户级真实分布，合成数据不代表当地客户结构。
                  </p>
                </div>
              </section>
              <section className={card}>
                <h2 className="text-xl font-semibold">带走数据，检查计算</h2>
                <div className="mt-5 flex flex-wrap gap-5">
                  {[
                    ["customers.csv", "合成客户数据"],
                    ["scenarios.csv", "420组计算结果"],
                    ["results.json", "假设与来源"],
                    ["model.py", "Python计算源码"],
                    ["README.md", "数据字典与完整参数"],
                    ["research-note.md", "研究计算说明"],
                  ].map(([file, label]) => (
                    <a
                      key={file}
                      className="inline-flex items-center gap-2 text-sm underline"
                      href={`/examples/fuling/${file}`}
                      download
                    >
                      <Download size={16} />
                      {label}
                    </a>
                  ))}
                </div>
                <p className="text-muted-foreground mt-4 text-xs">
                  版本 {data.version} ·
                  运行不需要模型密钥。修改源码中的定价、风险或策略参数即可重新计算。
                </p>
              </section>
            </div>
          ))}
        <footer className="text-muted-foreground mt-10 border-t pt-5 text-xs leading-6">
          独立个人作品，与银行无合作或系统接入关系。模型生成的媒体与合成数据已分别标注。案例可浏览，自己的文件与对话仍保存在独立会话中。
        </footer>
      </div>
    </main>
  );
}
