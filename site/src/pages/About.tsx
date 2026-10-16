import { Link } from "react-router-dom";
import { Header, Footer } from "../components/Layout";
import { source } from "../demo/scenarios";
export default function About() {
  return (
    <>
      <Header />
      <main className="page prose">
        <p className="eyebrow">项目说明</p>
        <h1>理解问题、核对计算、保留判断。</h1>
        <p className="lead">
          渝研是一个银行经营分析 Agent，也是一次关于 AI
          与确定性工具责任边界的个人研究与产品实践。
        </p>
        <h2>这次演示如何工作？</h2>
        <p>
          选择完整业务问题后，场景预设提供可确认参数。浏览器执行经营资源优化、现金流或原子余额核对，再根据工具输出生成受控解释。执行轨迹是可观察的步骤，不是模型的隐藏思维过程。
        </p>
        <p>
          C1 延期情景同时展示一条已有 Qwen
          脱敏调用记录。本次问题已明确客户、延期天数及成本条件；记录中的参数提案字段完整，程序检查字段、业务边界和账本版本后进入确认和确定性工具执行，未补字段或修正提案。Pages 展示已有记录并在浏览器本地重算，不实时调用在线模型。一次受控调用不等于证明模型能够独立处理任意银行问题。
        </p>
        <h2>数据与决策边界</h2>
        <p>
          客户、订单及经营参数均为合成输入，不代表实际客户分布。公开事实只用于理解产业背景；FTP、单价、采用率与成本是研究假设。输出不是实际业务结果，不连接真实银行系统，不提供授信决策。
        </p>
        <h2>完整实现与研究材料</h2>
        <p>
          完整实现包含 Agent
          编排、经营分析工具、账本机制和前后端交互；源码、技术说明和第三方许可均保留在
          GitHub 仓库中。
        </p>
        <div className="reading-links">
          <a href={source}>查看完整源码 ↗</a>
          <a href={source + "/blob/main/REPRODUCIBILITY.md"}>本地复现 ↗</a>
          <a href={source + "/tree/main/docs/reports"}>研究报告 ↗</a>
          <Link to="/demo">进入演示 →</Link>
        </div>
      </main>
      <Footer />
    </>
  );
}
