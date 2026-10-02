# PolicyLens browser extension

A Chrome/Edge extension (Manifest V3) that summarises the policy on the page
you're viewing. It reads the page's visible text and sends it to your
PolicyLens server, then shows the same 5-bullet summary as the web app.

## Install (developer mode)

1. Start the PolicyLens server (`cd server && python -m app.main`).
2. Open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked**
   and choose this `extension/` folder.
3. Open any privacy policy, click the PolicyLens icon, then **Analyze this page**.

## Server address

By default the extension talks to `http://localhost:8000`. To use a deployed
server, open **Settings** in the popup and enter its address; Chrome will ask
you to allow the extension to contact that site.

## Permissions it asks for

- `activeTab` + `scripting`: read the text of the current tab, only when you click the button.
- `storage`: remember the server address.
- Host access to `localhost:8000` (and any server you add in Settings): send the text for analysis.
