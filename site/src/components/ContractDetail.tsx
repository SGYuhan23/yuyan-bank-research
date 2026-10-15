import { useState } from "react";
import { Button, Collapse } from "antd";
import { changeAcceptance, addDays } from "../../js/contract-engine.js";
export default function ContractDetail({ initial }: { initial: any }) {
  const [changed, setChanged] = useState(false);
  const original = initial.events.find(
    (e) => e.event_id === "O1-acceptance",
  ).planned_date;
  const c = changed ? changeAcceptance(initial, addDays(original, 3)) : initial;
  const date = (id: string) =>
    c.events.find((e) => e.event_id === id).planned_date;
  return (
    <Collapse
      className="contract-detail"
      items={[
        {
          key: "contract",
          label: "计算依据：验收、开票如何影响预计回款？",
          children: (
            <>
              <p>
                独立合同示例，不修改上方已确认的延期情景。条件型合同只推导仍处于预计状态的日期。
              </p>
              <div className="contract-chain">
                {[
                  ["验收", "O1-acceptance"],
                  ["开票（验收 +2 天）", "O1-invoice"],
                  ["预计回款（开票 +7 天）", "O1-receivable"],
                ].map(([label, id]) => (
                  <div key={id}>
                    <span>{label}</span>
                    <strong>{date(id)}</strong>
                  </div>
                ))}
              </div>
              <p>
                固定日期合同（FIXED_DATE）对照：{date("O2-receivable")}
                ，不随上述验收变化。
              </p>
              <Button onClick={() => setChanged(!changed)}>
                {changed ? "恢复原验收日期" : "演示验收推迟 3 天"}
              </Button>
              <p className="small muted">
                预计 PROJECTED ≠ 已确认 CONFIRMED ≠ 已入账
                POSTED。此操作不会自动确认或入账。
              </p>
            </>
          ),
        },
      ]}
    />
  );
}
