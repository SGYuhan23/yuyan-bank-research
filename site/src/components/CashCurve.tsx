export default function CashCurve({
  baseline,
  scenario,
}: {
  baseline: any;
  scenario: any;
}) {
  const all = [...baseline.series, ...scenario.series],
    lo = Math.min(0, ...all.map((p) => p.balance_fen)),
    hi = Math.max(1, ...all.map((p) => p.balance_fen)),
    start = Date.parse(all[0].date),
    end = Math.max(...all.map((p) => Date.parse(p.date)));
  const x = (p: any) =>
      58 + ((Date.parse(p.date) - start) / (end - start || 1)) * 610,
    y = (v: number) => 24 + ((hi - v) / (hi - lo)) * 170;
  const points = (s: any) =>
    s.series.map((p) => `${x(p)},${y(p.balance_fen)}`).join(" ");
  return (
    <figure className="cash-curve">
      <figcaption>
        <strong>每日现金余额</strong>
        <span>
          <i className="legend base" />
          基准 <i className="legend" />
          本次情景
        </span>
      </figcaption>
      <svg
        viewBox="0 0 700 230"
        role="img"
        aria-label="基准与延期情景的每日现金曲线"
      >
        {[hi, 0, lo].map((n, i) => (
          <g key={i}>
            <line
              x1="58"
              x2="668"
              y1={y(n)}
              y2={y(n)}
              stroke="#dce3e0"
              strokeDasharray="4 5"
            />
            <text
              x="48"
              y={y(n) + 4}
              textAnchor="end"
              fontSize="11"
              fill="#667871"
            >
              {(n / 1000000).toFixed(1)}万
            </text>
          </g>
        ))}
        <polyline
          points={points(baseline)}
          fill="none"
          stroke="#a5b5ae"
          strokeWidth="2"
          strokeDasharray="5 4"
        />
        <polyline
          className="curve-line"
          points={points(scenario)}
          fill="none"
          stroke="#187263"
          strokeWidth="2.5"
        />
        <text x="58" y="220" fontSize="11" fill="#667871">
          {all[0].date}
        </text>
        <text x="668" y="220" textAnchor="end" fontSize="11" fill="#667871">
          {new Date(end).toISOString().slice(0, 10)}
        </text>
      </svg>
      <p className="small muted">
        按日终余额计算；预计回款不等于已经到账，日终余额不能保证日内支付。
      </p>
    </figure>
  );
}
