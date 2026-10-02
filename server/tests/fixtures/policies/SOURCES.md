# Real policy fixtures

Five real, publicly published policies used by the Stage 6 tests. Downloaded on
2026-10-02 from the public source repositories below. Two light edits were made
so the files read like pasted text: GitHub's YAML page header was removed, and
Mastodon's `%{domain}` server-name placeholder was replaced with `example.social`.
The policy wording itself is unchanged.

| File | Document | Source | License |
|---|---|---|---|
| github-privacy-statement.txt | GitHub General Privacy Statement | github/docs: content/site-policy/privacy-policies/github-general-privacy-statement.md | CC-BY-4.0 |
| github-terms-of-service.txt | GitHub Terms of Service | github/docs: content/site-policy/github-terms/github-terms-of-service.md | CC-BY-4.0 |
| github-cookies.txt | GitHub Cookies and Tracking Technologies | github/docs: content/site-policy/privacy-policies/github-cookies.md | CC-BY-4.0 |
| mastodon-privacy-policy.txt | Mastodon default server privacy policy | mastodon/mastodon: config/templates/privacy-policy.md | AGPL-3.0 |
| mastodon-terms-of-service.txt | Mastodon default server terms of service | mastodon/mastodon: config/templates/terms-of-service.md | AGPL-3.0 |

Policies change over time; these are snapshots, which is what tests need.
