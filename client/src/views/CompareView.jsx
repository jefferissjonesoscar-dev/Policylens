// Stage 7: compare two policies side by side (stacked on phones).
// Each side is an independent analysis, so one can finish or fail without the other.

import Disclaimer from "../components/Disclaimer.jsx";
import ComparisonTable from "../components/ComparisonTable.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import InputTabs from "../components/InputTabs.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ResultsCard from "../components/ResultsCard.jsx";
import useAnalysis from "../useAnalysis.js";

function CompareSide({ label, analysis }) {
  return (
    <div className="min-w-0 space-y-4">
      <h2 className="text-sm font-semibold tracking-wide text-gray-500 uppercase">{label}</h2>
      <InputTabs onSubmit={analysis.run} disabled={analysis.status === "loading"} submitLabel={`Analyze ${label}`} />
      {analysis.status === "loading" && <LoadingState />}
      {analysis.status === "error" && <ErrorBanner message={analysis.error} />}
      {analysis.status === "done" && <ResultsCard result={analysis.result} title={label} />}
    </div>
  );
}

export default function CompareView() {
  const first = useAnalysis();
  const second = useAnalysis();
  const anyDone = first.status === "done" || second.status === "done";
  const bothDone = first.status === "done" && second.status === "done";

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <CompareSide label="Policy A" analysis={first} />
        <CompareSide label="Policy B" analysis={second} />
      </div>
      {bothDone && <ComparisonTable first={first.result} second={second.result} />}
      {anyDone && <Disclaimer />}
    </div>
  );
}
