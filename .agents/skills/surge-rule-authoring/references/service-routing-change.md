# Service Routing Change

Use this guide for a focused request such as “make service X use Japan”, “add a
TikTok split”, or “block an advertising endpoint”. It describes a repository
change, not an instruction to modify the active iPhone Profile remotely.

## Intake

Record the following before editing:

- service and observed hostname(s), plus the evidence source if the hostname is
  not already present in a maintained Rule Set;
- requested outcome: `DIRECT`, `REJECT`, `Proxy`, or an existing named policy
  group; and
- intended scope: multi-policy `surge-main.conf`, simple Profile, or both.

Do not infer a named policy group from a country name. A rule can refer only to
`DIRECT`, a Surge built-in, or a group defined in the target Profile. If the
request requires a new group, describe its node-selection behavior and its
fallback before adding any rules.

## Change design

1. Check the effective order in `[Rule]`. A more-specific local exception must
   precede an upstream Rule Set that would otherwise match it. Keep `FINAL`
   last.
2. Prefer an existing maintained upstream Rule Set when it accurately covers
   the service. Otherwise add narrow, public domain/IP matchers to the smallest
   suitable file under `rules/`, with a Chinese comment that states the purpose
   and source/reason.
3. Bind a local Rule Set to its policy in the Profile's `RULE-SET` line; do not
   append policy names to lines inside a `.list` file.
4. A named split normally belongs only in `surge-main.conf` and
   `profile.example.conf`. The simple Profile deliberately has only
   `DIRECT` / `Proxy` / `REJECT`; leave it unchanged unless the request changes
   one of those broad outcomes.
5. If the Sub-Store rule-section template is intended to mirror the main
   Profile's rules, update it in the same change and explain any intentional
   difference.

## Validation and handoff

Run:

```bash
python3 .agents/skills/surge-profile-lint/scripts/lint_surge_profiles.py .
bash .agents/skills/basic-validation/scripts/validate_workspace.sh .
git diff --check
```

Then give the user one iPhone-side check: refresh/apply the relevant managed
Profile, make a request to the target service, and inspect its matched rule and
selected policy in Surge. Do not claim the behavior is live until this is done.

For rollback, identify the specific commit or the smallest changed Rule Set /
`[Rule]` binding to revert. Do not mix a routing rollback with unrelated DNS,
node, or subscription changes.
