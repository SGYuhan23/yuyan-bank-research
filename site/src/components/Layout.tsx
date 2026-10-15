import { Link } from "react-router-dom";
import { source, boundary } from "../demo/scenarios";
export function Header() {
  return (
    <header className="header">
      <Link className="brand" to="/">
        <span className="brand-mark">研</span>渝研
        <span className="brand-sub">银行经营分析 Agent</span>
      </Link>
      <nav>
        <Link to="/demo">交互演示</Link>
        <Link to="/screenshots">真实界面</Link>
        <Link to="/about">项目说明</Link>
        <a href={source} target="_blank" rel="noreferrer">
          源码 ↗
        </a>
      </nav>
    </header>
  );
}
export function Footer() {
  return (
    <footer>
      <span>渝研 · 银行经营分析 Agent</span>
      <p>{boundary}</p>
    </footer>
  );
}
