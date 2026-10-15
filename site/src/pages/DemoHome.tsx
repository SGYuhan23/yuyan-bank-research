import { Header, Footer } from "../components/Layout";
import ScenarioCard from "../components/ScenarioCard";
import { scenarios } from "../demo/scenarios";
export default function DemoHome() {
  return (
    <>
      <Header />
      <main className="page">
        <p className="eyebrow">亲手看一次完整分析</p>
        <h1>
          选一个经营问题，
          <br />
          跟着 Agent 走一遍。
        </h1>
        <p className="section-intro">
          不用键盘输入。先看完整问题，确认分析参数，再查看浏览器实时计算的结果与依据。
        </p>
        <div className="scenario-grid">
          {scenarios.map((s) => (
            <ScenarioCard key={s.id} scenario={s} />
          ))}
        </div>
        <p className="muted">
          这是受控公开演示，不提供在线模型服务。每次确认后都重新执行计算，结果不是预制答案。
        </p>
      </main>
      <Footer />
    </>
  );
}
