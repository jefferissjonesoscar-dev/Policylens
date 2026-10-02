// One summary bullet: its topic, the plain-language point, and a toggle that
// reveals the exact sentence from the policy that backs it up.

import { useState } from "react";

// Labels for the categories the backend returns, in the order they appear.
export const CATEGORY_LABELS = {
  data_collected: "What they collect",
  sharing: "Who they share it with",
  retention: "How long they keep it",
  user_rights: "Your rights",
  unusual: "Watch out for",
};

export default function Bullet({ bullet }) {
  const [open, setOpen] = useState(false);
  const hasQuote = bullet.quote.trim() !== "";

  return (
    <li className="py-4 first:pt-0 last:pb-0">
      <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase">
        {CATEGORY_LABELS[bullet.category] ?? bullet.category}
      </p>
      <p className="mt-1 text-gray-900">{bullet.text}</p>

      {hasQuote ? (
        <>
          <button
            type="button"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
            className="mt-2 text-sm font-medium text-indigo-700 hover:text-indigo-900"
          >
            {open ? "Hide original text" : "Show original text"}
          </button>
          {open && (
            <blockquote className="mt-2 border-l-4 border-indigo-200 bg-indigo-50/50 px-3 py-2 text-sm text-gray-700 italic">
              “{bullet.quote}”
            </blockquote>
          )}
        </>
      ) : (
        <p className="mt-2 text-sm text-gray-500">The policy doesn't mention this.</p>
      )}
    </li>
  );
}
