// Main screen: one policy in, one summary out.

import Disclaimer from "../components/Disclaimer.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import InputTabs from "../components/InputTabs.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ResultsCard from "../components/ResultsCard.jsx";
import useAnalysis from "../useAnalysis.js";

export default function AnalyzeView() {
  const analysis = useAnalysis();

  return (
    <div className="space-y-6">
      <InputTabs onSubmit={analysis.run} disabled={analysis.status === "loading"} />
      {analysis.status === "loading" && <LoadingState />}
      {analysis.status === "error" && <ErrorBanner message={analysis.error} />}
      {analysis.status === "done" && (
        <>
          <ResultsCard result={analysis.result} />
          <Disclaimer />
        </>
      )}
    </div>
  );
}
