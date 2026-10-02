// Stage 7: once both policies are analysed, line their bullets up topic by topic
// so differences are easy to spot. Quotes stay in each policy's own card.

import { CATEGORY_LABELS } from "./Bullet.jsx";
import RiskBadge from "./RiskBadge.jsx";

export default function ComparisonTable({ first, second }) {
  const textFor = (result, category) => result.bullets.find((b) => b.category === category)?.text ?? "—";

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
      <h2 className="text-lg font-semibold text-gray-900">Side by side</h2>
      <dl className="mt-4 divide-y divide-gray-100">
        {/* Column headings; on phones each row labels its own A and B instead. */}
        <div className="hidden gap-4 pb-2 text-xs font-semibold tracking-wide text-gray-500 uppercase sm:grid sm:grid-cols-[10rem_1fr_1fr]">
          <span />
          <span>Policy A</span>
          <span>Policy B</span>
        </div>
        <div className="grid gap-2 py-3 sm:grid-cols-[10rem_1fr_1fr] sm:gap-4">
          <dt className="text-sm font-semibold text-gray-700">Overall risk</dt>
          <dd><span className="mr-2 text-xs text-gray-500 sm:hidden">A</span><RiskBadge level={first.risk_level} /></dd>
          <dd><span className="mr-2 text-xs text-gray-500 sm:hidden">B</span><RiskBadge level={second.risk_level} /></dd>
        </div>
        {Object.entries(CATEGORY_LABELS).map(([category, label]) => (
          <div key={category} className="grid gap-2 py-3 sm:grid-cols-[10rem_1fr_1fr] sm:gap-4">
            <dt className="text-sm font-semibold text-gray-700">{label}</dt>
            <dd className="text-sm text-gray-900"><span className="font-semibold text-gray-500 sm:hidden">A: </span>{textFor(first, category)}</dd>
            <dd className="text-sm text-gray-900"><span className="font-semibold text-gray-500 sm:hidden">B: </span>{textFor(second, category)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
