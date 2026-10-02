// Coloured badge for the overall risk level. The level is always written out in
// words too, so the badge doesn't rely on colour alone.

const STYLES = {
  Low: "bg-green-100 text-green-800 ring-green-600/20",
  Medium: "bg-amber-100 text-amber-900 ring-amber-600/20",
  High: "bg-red-100 text-red-800 ring-red-600/20",
};

export default function RiskBadge({ level }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ring-1 ring-inset ${
        STYLES[level] ?? "bg-gray-100 text-gray-800 ring-gray-500/20"
      }`}
    >
      {level} risk
    </span>
  );
}
