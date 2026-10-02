// Shown while the backend reads and analyses the policy (usually 10-60 seconds).

export default function LoadingState({ label = "Reading the policy…" }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" aria-hidden="true" />
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">Long policies can take up to a minute.</p>
      </div>
    </div>
  );
}
