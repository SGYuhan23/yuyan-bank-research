import { Link } from "react-router-dom";
import type { Scenario } from "../demo/scenarios";
export default function ScenarioCard({ scenario: s }: { scenario: Scenario }) {
  return (
    <Link className="scenario-card" to={"/demo/" + s.id}>
      <span className="eyebrow">
        DEMO {s.no} / {s.theme}
      </span>
      <h2>{s.title}</h2>
      <p>{s.subtitle}</p>
      <span className="text-link">
        开始这次分析 <span>↗</span>
      </span>
    </Link>
  );
}
