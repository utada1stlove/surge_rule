---
name: change-review
description: Perform a read-only, evidence-first review of a diff for behavioral risk, missing validation, scope drift, and artifact inconsistencies. Use for reviews or before material releases.
---

# Change Review

Inspect the changed implementation and the called behavior, not only the diff
surface. Report findings with location, trigger, impact, and evidence. Keep
facts separate from assumptions and do not edit files while reviewing.

For material changes, use an independent reviewer agent when available. For
small changes, deterministic checks plus a focused self-review are sufficient.
