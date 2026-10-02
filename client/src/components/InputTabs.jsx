// The input form: three tabs (URL / Paste / PDF) and an Analyze button.
// Calls onSubmit({type, value}) with what the backend expects.

import { useId, useState } from "react";
import { MAX_PDF_BYTES, fileToBase64 } from "../api.js";

const TABS = [
  { id: "url", label: "URL" },
  { id: "text", label: "Paste" },
  { id: "pdf", label: "PDF" },
];

export default function InputTabs({ onSubmit, disabled, submitLabel = "Analyze policy" }) {
  const [tab, setTab] = useState("url");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [formError, setFormError] = useState("");
  const idPrefix = useId(); // keeps ids unique when the form appears twice (Compare mode)

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    if (tab === "url") {
      if (!url.trim()) return setFormError("Enter the link to a privacy policy or terms page.");
      onSubmit({ type: "url", value: url.trim() });
    } else if (tab === "text") {
      if (!text.trim()) return setFormError("Paste the policy text first.");
      onSubmit({ type: "text", value: text });
    } else {
      if (!file) return setFormError("Choose a PDF file first.");
      if (file.size > MAX_PDF_BYTES) return setFormError("That PDF is larger than 10 MB.");
      try {
        onSubmit({ type: "pdf", value: await fileToBase64(file) });
      } catch (error) {
        setFormError(error.message);
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
      <div role="tablist" aria-label="How to provide the policy" className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`${idPrefix}-panel`}
            onClick={() => {
              setTab(t.id);
              setFormError("");
            }}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
              tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div id={`${idPrefix}-panel`} role="tabpanel" aria-labelledby={`${idPrefix}-tab-${tab}`} className="mt-4">
        {tab === "url" && (
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Policy page link</span>
            <input
              type="url"
              inputMode="url"
              placeholder="https://example.com/privacy"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
            />
          </label>
        )}

        {tab === "text" && (
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Policy text</span>
            <textarea
              rows={8}
              placeholder="Paste the full privacy policy or terms of service here…"
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
            />
          </label>
        )}

        {tab === "pdf" && (
          <label className="block">
            <span className="text-sm font-medium text-gray-700">PDF file (up to 10 MB)</span>
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm text-gray-700 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
            />
          </label>
        )}
      </div>

      {formError && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {formError}
        </p>
      )}

      <button
        type="submit"
        disabled={disabled}
        className="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
      >
        {submitLabel}
      </button>
    </form>
  );
}
