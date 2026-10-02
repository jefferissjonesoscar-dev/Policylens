// A small React hook that runs one analysis and tracks its state:
// "idle" -> "loading" -> "done" (with result) or "error" (with message).

import { useRef, useState } from "react";
import { analyzePolicy } from "./api.js";

export default function useAnalysis() {
  const [state, setState] = useState({ status: "idle", result: null, error: "" });
  // Counts requests so a slow earlier request can't overwrite a newer one's result.
  const latestRequest = useRef(0);

  async function run(input) {
    const requestNumber = ++latestRequest.current;
    setState({ status: "loading", result: null, error: "" });
    try {
      const result = await analyzePolicy(input);
      if (requestNumber === latestRequest.current) setState({ status: "done", result, error: "" });
    } catch (error) {
      if (requestNumber === latestRequest.current) setState({ status: "error", result: null, error: error.message });
    }
  }

  return { ...state, run };
}
