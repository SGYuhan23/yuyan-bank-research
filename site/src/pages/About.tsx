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
          脱敏记录：原提示已指定客户和天数，模型留空的成本参数由验收程序补齐。它不是对当前问题的新模型调用，也不证明模型独立完成了全部参数抽取。
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
