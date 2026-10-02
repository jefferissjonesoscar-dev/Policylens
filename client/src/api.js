// Functions that talk to the PolicyLens backend.
//
// Every backend error comes back as {"error": {"code", "message"}} with a
// plain-English message, so we pass that message straight to the UI.

// Largest PDF we send. The server enforces its own limit too; checking here
// saves the user a long upload that would be rejected.
export const MAX_PDF_BYTES = 10 * 1024 * 1024; // 10 MB

async function postJson(path, body) {
  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    // fetch only throws when no response arrived at all (offline, server down).
    throw new Error("Couldn't reach the PolicyLens server. Check your connection and try again.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // A non-JSON reply (e.g. a proxy error page) is handled below.
  }

  if (!response.ok) {
    throw new Error(data?.error?.message ?? `The server returned an error (${response.status}).`);
  }
  return data;
}

// Analyse a policy. input is {type: "text" | "url" | "pdf", value: string}.
export function analyzePolicy(input) {
  return postJson("/api/analyze", input);
}

// Explain a list of app permissions (Stage 7). permissions is a string of names.
export function explainPermissions(permissions) {
  return postJson("/api/permissions", { permissions });
}

// Read a File and return its contents as base64 (without the "data:...;base64," prefix).
export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] ?? "");
    reader.onerror = () => reject(new Error("Couldn't read that file. Try choosing it again."));
    reader.readAsDataURL(file);
  });
}
