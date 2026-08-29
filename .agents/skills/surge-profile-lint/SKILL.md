---
name: surge-profile-lint
description: Statically validate public Surge Profiles and Rule Sets for broken policy references, rule order, local Rule Set links, duplicate rules, and likely secrets. Use after editing Surge configuration in this repository.
---

# Surge Profile Lint

Run `scripts/lint_surge_profiles.py [repository-directory]` after changing a
public Profile or a file under `rules/`. It is an offline structural check; it
does not fetch remote Rule Sets and does not validate a Profile in the Surge
runtime.

Treat errors as blockers before committing. Warnings need a deliberate review:
they identify duplicated active rules and values that resemble credentials, but
can be false positives in a public example or comment-free placeholder.

The checker verifies the repository's public contract:

- each Profile has `[Rule]`, exactly one `FINAL`, and no effective rule after it;
- named policies used in rules exist in `[Proxy Group]` (or are Surge built-ins);
- first-party `raw.githubusercontent.com/utada1stlove/surge_rule` Rule Set URLs
  resolve to a local file in this checkout;
- local Rule Set files do not repeat the same effective rule.

It intentionally does not infer whether a broad domain is desirable, whether
an upstream list is semantically correct, or whether a runtime policy filter
will find a node. Review those questions with `surge-rule-authoring` and, for
material changes, `change-review`.
