---
name: verify-quotes
description: Use after any change to the PolicyLens prompt or analysis code to confirm every returned quote exists verbatim in the source policy.
---
# Verify quotes

1. Run the live tests, which analyse every fixture in `server/tests/fixtures/policies/` plus `prompt-injection-policy.txt`: `cd server && POLICYLENS_LIVE_TESTS=1 python -m unittest tests.test_real_policies -v`.
2. Normalise both source and quote: collapse whitespace, convert curly quotes and dashes to plain ones, trim.
3. A quote passes only if the normalised quote is a substring of the normalised source.
4. Bullets saying "Not stated in the policy" must have an empty quote and still pass.
5. Report a table: fixture, bullets passed / 5, any failing quote text.
6. Any failure blocks the stage handoff until fixed.
