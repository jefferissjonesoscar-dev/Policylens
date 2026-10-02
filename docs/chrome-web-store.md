# Publishing PolicyLens on the Chrome Web Store

Everything to copy into the Chrome Web Store form, plus the steps.

## Before you start

1. The server is online (see "Put it online" in the README) and you know its address,
   e.g. `https://policylens-xxxx.onrender.com`.
2. Build the zip from the repository root:
   ```bash
   python extension/make_store_zip.py https://policylens-xxxx.onrender.com
   ```
   This writes `extension/dist/policylens-extension.zip`, set up to talk only to your server.
3. Register as a Chrome Web Store developer at https://chrome.google.com/webstore/devconsole
   (one-time US$5 fee).

## Steps

1. In the developer dashboard, click **New item** and upload the zip.
2. Fill in the **Store listing**, **Privacy** and **Distribution** tabs with the text below.
3. Click **Submit for review**. Review usually takes a few days.

## Store listing tab

**Name:** PolicyLens

**Summary** (max 132 characters):
> Reads the terms or privacy policy on your screen and tells you, point by point, what you're agreeing to.

**Description:**
> Nobody reads the terms and conditions. PolicyLens reads them for you.
>
> Open any privacy policy or terms of service, click the PolicyLens icon, and get:
>
> • Five plain-English points: what they collect, who they share it with, how long they keep it, your rights, and the one term to watch out for.
> • A Low, Medium or High risk rating with a one-line reason.
> • The exact sentence from the policy behind every point, so you can check it yourself.
>
> Suspicious or surprising terms are highlighted so they don't slip past you.
>
> PolicyLens only reads a page when you click the button. It doesn't track your browsing, has no accounts, and doesn't store what you analyse.
>
> PolicyLens gives a summary, not legal advice.

**Category:** Tools (or Productivity)

**Language:** English

**Icon:** the 128×128 icon is already inside the zip.

**Screenshots:** upload `docs/screenshots/store-1280x800.png` (1280×800).

## Privacy tab

**Single purpose:**
> Summarise the privacy policy or terms of service on the current page in plain language.

**Permission justifications:**

| Permission | Justification |
| --- | --- |
| `activeTab` | Reads the text of the current tab, only when the user clicks "Analyze this page". |
| `scripting` | Runs a small function in the current tab to read its visible text after the user clicks the button. |
| `storage` | Remembers the PolicyLens server address. |
| Host permission (your server) | Sends the page text to the PolicyLens server, which returns the summary. |

**Remote code:** No, I am not using remote code. (The extension only receives JSON data, never code.)

**Data usage:** tick **Website content** (the policy text is sent for analysis). Leave everything else unticked.
Then tick all three certifications (not sold, not used for unrelated purposes, not used for creditworthiness).

**Privacy policy URL:** `https://policylens-xxxx.onrender.com/privacy.html` (your server address + `/privacy.html`).

## Distribution tab

**Visibility:** Public (or Unlisted to share it only with people who have the link).
**Regions:** All regions.

## Updating later

Bump `"version"` in `extension/manifest.json` (e.g. 0.1.0 → 0.1.1), rebuild the zip,
and upload it under **Package** in the dashboard.
