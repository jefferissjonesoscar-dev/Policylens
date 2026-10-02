---
name: stage-handoff
description: Use at the end of every PolicyLens build stage to present the work to the owner and stop until they say "next".
---
# Stage handoff

1. Run the stage's "Done when" check from PLAN.md and capture the output.
2. Have the qa-reviewer agent run its checklist; fix anything it flags.
3. Present to the owner, in this order:
   - What the stage built, in 2–3 sentences.
   - Each major decision with a 1–2 sentence reason.
   - The files changed, with the key code shown.
   - How to run or try it (exact commands).
   - Any library approval needed for the next stage.
4. Stop. Do not start the next stage until the owner replies "next".
