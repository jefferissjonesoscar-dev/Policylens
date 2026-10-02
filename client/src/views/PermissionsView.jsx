// Stage 7: explain Android or iOS app permissions in plain language.
// The user pastes permission names (one per line or comma-separated), as listed
// in an app's store page, manifest (AndroidManifest.xml) or Info.plist.

import { useState } from "react";
import { explainPermissions } from "../api.js";
import Disclaimer from "../components/Disclaimer.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

const EXAMPLE = "android.permission.ACCESS_FINE_LOCATION\nandroid.permission.READ_CONTACTS\nNSCameraUsageDescription";

export default function PermissionsView() {
  const [input, setInput] = useState("");
  const [state, setState] = useState({ status: "idle", result: null, error: "" });

  async function handleSubmit(event) {
    event.preventDefault();
    if (!input.trim()) {
      setState({ status: "error", result: null, error: "Paste at least one permission name." });
      return;
    }
    setState({ status: "loading", result: null, error: "" });
    try {
      setState({ status: "done", result: await explainPermissions(input), error: "" });
    } catch (error) {
      setState({ status: "error", result: null, error: error.message });
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">App permissions</span>
          <span className="block text-sm text-gray-500">
            Android names like <code>android.permission.CAMERA</code> or iOS keys like{" "}
            <code>NSCameraUsageDescription</code>, one per line.
          </span>
          <textarea
            rows={6}
            value={input}
            placeholder={EXAMPLE}
            onChange={(e) => setInput(e.target.value)}
            className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
          />
        </label>
        <button
          type="submit"
          disabled={state.status === "loading"}
          className="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 sm:w-auto"
        >
          Explain permissions
        </button>
      </form>

      {state.status === "error" && <ErrorBanner message={state.error} />}

      {state.status === "done" && (
        <>
          <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6" aria-live="polite">
            <h2 className="text-lg font-semibold text-gray-900">What these permissions allow</h2>
            <ul className="mt-4 divide-y divide-gray-100">
              {state.result.permissions.map((p) => (
                <li key={p.name} className="py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-gray-900">{p.title}</p>
                    {p.risk_level && <RiskBadge level={p.risk_level} />}
                  </div>
                  <p className="mt-1 text-sm text-gray-700">{p.explanation}</p>
                  <p className="mt-1 font-mono text-xs break-all text-gray-400">
                    {p.platform ? `${p.platform}: ` : ""}{p.name}
                  </p>
                </li>
              ))}
            </ul>
          </section>
          <Disclaimer />
        </>
      )}
    </div>
  );
}
