import { Button, Tag } from "antd";
import { Link } from "react-router-dom";
import { Header, Footer } from "../components/Layout";
import { source, asset } from "../demo/scenarios";
export default function Landing() {
  return (
    <>
      <Header />
      <main className="landing">
        <section className="hero">
          <div className="hero-copy">
            <Tag color="cyan">交互式合成数据演示 · 无需登录</Tag>
            <h1>
              渝研<span>银行经营分析 Agent</span>
            </h1>
            <p className="lead">
              把一个经营问题，从自然语言提问，走到参数确认、工具计算、结果校验和经营解释。
            </p>
            <p className="muted">
              当前围绕两个场景验证：客户经理时间有限时先经营谁，以及企业回款变化如何影响现金流。
            </p>
            <div className="actions">
              <Link to="/demo">
                <Button type="primary" size="large">
                  开始 Agent 演示 ↗
                </Button>
              </Link>
              <Button
                size="large"
                onClick={() =>
                  document
                    .getElementById("understand")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                30 秒看懂
              </Button>
              <a href={source} target="_blank" rel="noreferrer">
                查看源码 ↗
              </a>
            </div>
          </div>
          <aside className="responsibility">
            <p className="eyebrow">一个经营问题，三种责任</p>
            <h2>
              让解释有依据，
              <br />
              让计算可核对。
            </h2>
            {[
              ["AI", "听懂问题 · 整理参数 · 解释结果"],
              ["程序", "计算金额 · 推导日期\n重算现金流 · 分配经营资源"],
              ["人", "确认参数 · 判断业务\n做客户和风险决策"],
            ].map(([a, b]) => (
              <div className="role-row" key={a}>
                <strong>{a}</strong>
                <span>{b}</span>
              </div>
            ))}
            <p className="aside-note">关键金额和日期不交给模型自由生成。</p>
          </aside>
        </section>
        <section id="understand">
          <p className="eyebrow">从问题到可核对的结果</p>
          <h2>30 秒看懂渝研</h2>
          <div className="four-steps">
            {[
              [
                "提出经营问题",
                "例如：“客户经理本期只有 150 小时，哪些客户机会应该先验证？”",
              ],
              [
                "Agent 理解问题",
                "把自然语言问题整理成客户、工时、延期天数、成本等可确认参数。",
              ],
              [
                "工具完成计算",
                "金额、日期、现金流和资源配置由确定性程序计算。",
              ],
              [
                "返回经营结论",
                "不只给数字，还说明为什么、有哪些假设、下一步应验证什么。",
              ],
            ].map(([title, text], i) => (
              <article key={title}>
                <span className="number">0{i + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="flow-section">
          <h2>一条 Agent 分析链路</h2>
          <ol className="flow">
            {[
              "用户提问",
              "理解问题",
              "参数确认",
              "调用工具",
              "结果校验",
              "经营解释",
            ].map((s, i) => (
              <li key={s}>
                <small>0{i + 1}</small>
                <strong>{s}</strong>
                <span>→</span>
              </li>
            ))}
          </ol>
          <p className="muted">
            AI 负责理解与解释；关键业务数字由程序计算；最终经营判断留给人。
          </p>
        </section>
        <section>
          <p className="eyebrow">两个业务方向</p>
          <h2>Agent 目前解决什么问题？</h2>
          <div className="business-grid">
            <article>
              <span className="eyebrow">客户经营</span>
              <h3>时间有限，先经营谁？</h3>
              <p>
                银行客户经理不可能同时跟进所有机会。系统比较客户交易、员工、供应链连接等特征，以及每项任务所需工时和假设价值，帮助判断哪些机会更值得先验证。
              </p>
              <Link to="/demo/allocation">进入客户经营 Demo →</Link>
            </article>
            <article>
              <span className="eyebrow">企业资金</span>
              <h3>有订单，为什么还是会缺现金？</h3>
              <p>
                企业采购和生产需要先花钱，客户货款往往以后才到账。系统把合同条件、预计回款和实际到账分开，重新计算不同回款变化下的资金缺口。
              </p>
              <Link to="/demo/cashflow">进入资金管理 Demo →</Link>
            </article>
          </div>
        </section>
        <section className="demo-invite">
          <div>
            <p className="eyebrow">无需输入 · 四个已验证的问题</p>
            <h2>亲手看 Agent 完成一次分析</h2>
            <p>
              选择一个已经验证的业务问题，完整查看 Agent
              如何理解问题、确认参数、调用工具并返回结果。
            </p>
          </div>
          <Link to="/demo">
            <Button size="large" type="primary">
              进入 Agent 演示 ↗
            </Button>
          </Link>
        </section>
        <section>
          <h2>研究的是理解、计算与决策的边界</h2>
          <p className="section-intro">
            这个项目关注的是：哪些经营问题适合交给 AI
            理解和解释，哪些关键计算必须由程序完成，以及人在什么地方需要确认和决策。
          </p>
          <div className="research-roles">
            {[
              ["AI", "问题理解 / 资料整理 / 自然语言解释"],
              ["程序", "金额 / 日期 / 现金流 / 资源配置"],
              ["人", "参数确认 / 客户策略 / 经营判断 / 风险与授信"],
            ].map(([a, b]) => (
              <div key={a}>
                <h3>{a}</h3>
                <p>{b}</p>
              </div>
            ))}
          </div>
        </section>
        <section>
          <div className="section-heading">
            <h2>真实系统界面</h2>
            <Link to="/screenshots">查看全部 →</Link>
          </div>
          <p className="muted">
            以下截图来自本地运行的完整产品，GitHub Pages
            使用同一业务逻辑制作交互式公开演示。
          </p>
          <div className="preview-grid">
            {[
              ["01-fuling-overview", "客户经营分析"],
              ["04-supplier-overview", "供应商资金管理"],
            ].map(([id, title]) => (
              <Link to="/screenshots" key={id}>
                <img
                  loading="lazy"
                  src={asset("assets/screenshots/" + id + ".png")}
                  alt={title}
                />
                <h3>{title}</h3>
              </Link>
            ))}
          </div>
          <div className="reading-links">
            <a href={source + "/tree/main/docs/reports"}>研究报告 ↗</a>
            <a href={source}>完整源码 ↗</a>
            <Link to="/about">项目说明与数据边界 →</Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
