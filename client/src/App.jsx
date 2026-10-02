// PolicyLens app shell: header, mode switcher and the selected screen.

import { useState } from "react";
import AnalyzeView from "./views/AnalyzeView.jsx";
import CompareView from "./views/CompareView.jsx";
import PermissionsView from "./views/PermissionsView.jsx";

const MODES = [
  { id: "analyze", label: "Analyze", view: AnalyzeView },
  { id: "compare", label: "Compare", view: CompareView },
  { id: "permissions", label: "App permissions", view: PermissionsView },
];

export default function App() {
  const [mode, setMode] = useState("analyze");
  const ActiveView = MODES.find((m) => m.id === mode).view;

  return (
    <div className="min-h-screen bg-gray-50">
      <main className={`mx-auto px-4 py-8 sm:py-12 ${mode === "compare" ? "max-w-6xl" : "max-w-2xl"}`}>
        <header>
          <h1 className="text-3xl font-bold text-gray-900">PolicyLens</h1>
          <p className="mt-2 text-gray-600">
            See what you're really agreeing to, in five plain-language points.
          </p>
        </header>

        <nav aria-label="Mode" className="mt-6 flex gap-4 border-b border-gray-200">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-current={mode === m.id ? "page" : undefined}
              onClick={() => setMode(m.id)}
              className={`-mb-px border-b-2 px-1 pb-2 text-sm font-medium ${
                mode === m.id ? "border-indigo-600 text-indigo-700" : "border-transparent text-gray-500 hover:text-gray-800"
              }`}
            >
              {m.label}
            </button>
          ))}
        </nav>

        <div className="mt-6">
          <ActiveView />
        </div>
      </main>
    </div>
  );
}
