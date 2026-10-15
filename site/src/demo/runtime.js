// Presentation adapter only. All business calculations delegate to frozen engines.
import { optimize, valueActions } from "../../js/fuling-engine.js";
import { evaluate, simulate } from "../../js/supplier-engine.js";
import { prepareReconcile, reconcile } from "../../js/ledger-engine.js";
import { ScenarioState } from "../../js/scenario-state.js";
export class GuidedSession {
  constructor(data, id) {
    this.data = data;
    this.id = id;
    this.ledger = structuredClone(data.supplier.initial_case);
    if (id === "reconcile") this.ledger = prepareReconcile(this.ledger);
    this.binding = new ScenarioState();
    this.receipts = {};
    this.result = null;
    this.previous = null;
    this.variant = false;
    this.propose(false);
  }
  propose(followup) {
    this.variant = followup;
    this.previous = this.result;
    this.result = null;
    const p =
      this.id === "allocation"
        ? { available_hours: 150, industry_limit: followup ? 0.25 : null }
        : this.id === "cashflow"
          ? {
              customer_id: followup ? "ALL" : "C1",
              delay_days: followup ? 30 : 14,
              discount: "0",
              fee_fen: 0,
              advance_fen: 0,
            }
          : this.id === "customer"
            ? { comparison_indices: [0, 1], deposit_fen: 10000000 }
            : {
                event_id: "O1-materials",
                observed_balance_fen: followup
                  ? evaluate(this.ledger).actual_balance_fen +
                    this.ledger.events.find(
                      (e) => e.event_id === "O1-materials",
                    ).amount_fen
                  : 0,
                posted_date: "2027-01-08",
                as_of: "2027-01-09",
              };
    return this.binding.propose(p, this.ledger.version);
  }
  confirm() {
    return this.binding.confirm(this.ledger.version);
  }
  run() {
    const before = structuredClone(this.ledger);
    const out = this.binding.calculate((p) => {
      if (this.id === "allocation") {
        const result = optimize(
          this.data.fuling.actions,
          p.available_hours,
          p.industry_limit,
        );
        return {
          ...result,
          free: p.industry_limit
            ? optimize(this.data.fuling.actions, p.available_hours, null)
            : null,
          actions: this.data.fuling.actions.filter((a) =>
            result.selected.includes(a.id),
          ),
        };
      }
      if (this.id === "customer")
        return {
          customers: p.comparison_indices.map((i) => {
            const customer = this.data.fuling.comparisons[i],
              actions = valueActions(customer, this.data.fuling.actions);
            return {
              customer,
              actions,
              best: actions.reduce((a, b) =>
                a.benefit_fen > b.benefit_fen ? a : b,
              ),
            };
          }),
        };
      if (this.id === "cashflow")
        return {
          baseline: evaluate(this.ledger),
          scenario: simulate(this.ledger, p),
        };
      try {
        const next = reconcile(
          this.ledger,
          {
            ...p,
            base_version: this.ledger.version,
            idempotency_key: this.binding.request.request_id,
          },
          this.receipts,
        );
        this.ledger = next.case;
        this.receipts = next.receipts;
        return {
          ok: true,
          before,
          after: structuredClone(this.ledger),
          computed: evaluate(this.ledger).actual_balance_fen,
          observed: p.observed_balance_fen,
        };
      } catch (error) {
        if (error.difference_fen === undefined) throw error;
        if (JSON.stringify(before) !== JSON.stringify(this.ledger))
          throw Error("回滚状态异常");
        return {
          ok: false,
          before,
          after: structuredClone(this.ledger),
          computed: p.observed_balance_fen - error.difference_fen,
          observed: p.observed_balance_fen,
          difference_fen: error.difference_fen,
        };
      }
    }, this.ledger.version);
    this.result = out;
    return out;
  }
}
