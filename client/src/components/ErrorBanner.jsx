// Shows an error message from the server (already written in plain English).

export default function ErrorBanner({ message }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      {message}
    </div>
  );
}
