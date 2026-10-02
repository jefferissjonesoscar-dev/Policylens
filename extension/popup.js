// PolicyLens browser extension popup.
//
// When the user clicks "Analyze this page", we read the visible text of the
// current tab and send it to the PolicyLens server as pasted text. Sending the
// text (rather than the URL) means pages that need a login or build their
// content with JavaScript work too, because we read what the user already sees.
//
// All text from the server is inserted with textContent, never innerHTML, so
// nothing in a policy or a summary can run as code inside the extension.

const DEFAULT_SERVER = "http://localhost:8000";

// Same labels as the web app (client/src/components/Bullet.jsx).
const CATEGORY_LABELS = {
  data_collected: "What they collect",
  sharing: "Who they share it with",
  retention: "How long they keep it",
  user_rights: "Your rights",
  unusual: "Watch out for",
};

const $ = (id) => document.getElementById(id);

// ---------- Settings: which PolicyLens server to use ----------

async function getServer() {
  const { server } = await chrome.storage.sync.get({ server: DEFAULT_SERVER });
  return server.replace(/\/+$/, ""); // drop trailing slashes
}

async function saveServer() {
  const value = $("server").value.trim() || DEFAULT_SERVER;
  let origin;
  try {
    origin = new URL(value).origin;
  } catch {
    return showError("That server address isn't a valid URL.");
  }
  // The extension may only contact servers the user has allowed. localhost:8000
  // is allowed in manifest.json; any other server needs the user's permission.
  const granted = await chrome.permissions.request({ origins: [`${origin}/*`] });
  if (!granted) return showError("PolicyLens needs permission to contact that server.");

  await chrome.storage.sync.set({ server: value });
  $("saved").hidden = false;
  setTimeout(() => ($("saved").hidden = true), 2000);
}

// ---------- Reading the current page ----------

// Runs inside the web page, not in the popup. It must be self-contained.
function readPageText() {
  // Prefer the page's main content area when the site marks one.
  const main = document.querySelector("main, article, [role='main']");
  const element = main && main.innerText.trim().length > 500 ? main : document.body;
  return element.innerText;
}

async function getCurrentPageText() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !/^https?:/.test(tab.url ?? "")) {
    throw new Error("Open a web page with a privacy policy or terms of service first.");
  }
  const [injection] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: readPageText });
  return injection?.result ?? "";
}

// ---------- Talking to the server ----------

async function analyze(text) {
  const server = await getServer();
  let response;
  try {
    response = await fetch(`${server}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "text", value: text }),
    });
  } catch {
    throw new Error(`Couldn't reach the PolicyLens server at ${server}. Is it running?`);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.error?.message ?? `The server returned an error (${response.status}).`);
  }
  return data;
}

// ---------- Showing results ----------

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderResult(result) {
  const container = $("result");
  container.replaceChildren();

  const head = element("div", "result-head");
  head.append(element("h2", "", "What you're agreeing to"));
  head.append(element("span", `badge ${result.risk_level}`, `${result.risk_level} risk`));
  container.append(head, element("p", "muted", result.risk_reason));

  const list = element("ul");
  for (const bullet of result.bullets) {
    const item = element("li");
    item.append(element("p", "category", CATEGORY_LABELS[bullet.category] ?? bullet.category));
    item.append(element("p", "text", bullet.text));
    if (bullet.quote) {
      // <details> gives a built-in, keyboard-accessible "show more" toggle.
      const details = element("details", "quote");
      details.append(element("summary", "", "Show original text"));
      details.append(element("blockquote", "", `“${bullet.quote}”`));
      item.append(details);
    }
    list.append(item);
  }
  container.append(list);
  container.append(element("p", "disclaimer", "This is a summary, not legal advice."));
  container.hidden = false;
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}

async function onAnalyzeClick() {
  const button = $("analyze");
  button.disabled = true;
  $("error").hidden = true;
  $("result").hidden = true;
  $("status").textContent = "Reading the policy… this can take up to a minute.";
  $("status").hidden = false;
  try {
    const text = await getCurrentPageText();
    renderResult(await analyze(text));
  } catch (error) {
    showError(error.message);
  } finally {
    $("status").hidden = true;
    button.disabled = false;
  }
}

// ---------- Start ----------

$("analyze").addEventListener("click", onAnalyzeClick);
$("save").addEventListener("click", saveServer);
getServer().then((server) => ($("server").value = server));
