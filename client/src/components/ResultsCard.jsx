// The analysis result: risk badge with its reason, then the five bullets.

import Bullet from "./Bullet.jsx";
import RiskBadge from "./RiskBadge.jsx";

export default function ResultsCard({ result, title = "What you're agreeing to" }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <RiskBadge level={result.risk_level} />
      </div>
      <p className="mt-2 text-sm text-gray-600">{result.risk_reason}</p>

      <ul className="mt-4 divide-y divide-gray-100 border-t border-gray-100 pt-4">
        {result.bullets.map((bullet) => (
          <Bullet key={bullet.category} bullet={bullet} />
        ))}
      </ul>
    </section>
  );
}
