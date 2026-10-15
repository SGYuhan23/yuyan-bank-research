import { Dropdown, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { scenarios } from "../demo/scenarios";
export function UserMessage({ text }: { text: string }) {
  return (
    <article className="user-message">
      <span className="message-label">业务问题</span>
      <p>
        {text
          .split(/(150 小时|不设置行业上限|C1|延期 14 天|30 万元)/g)
          .map((part, i) => (i % 2 ? <strong key={i}>{part}</strong> : part))}
      </p>
    </article>
  );
}
export function AgentLabel() {
  return (
    <div className="agent-label">
      <span className="agent-avatar">研</span>
      <strong>渝研</strong>
      <span>银行经营分析 Agent</span>
    </div>
  );
}
export function ScenarioComposer() {
  const navigate = useNavigate();
  return (
    <div className="scenario-composer">
      <Dropdown
        trigger={["click"]}
        menu={{
          items: scenarios.map((s) => ({
            key: s.id,
            label: `${s.no} · ${s.title}`,
          })),
          onClick: ({ key }) => navigate("/demo/" + key),
        }}
      >
        <Button block size="large">
          选择一个演示问题 <span aria-hidden="true">⌄</span>
        </Button>
      </Dropdown>
      <p>受控问题 · 实时计算 · 无在线模型调用</p>
    </div>
  );
}
