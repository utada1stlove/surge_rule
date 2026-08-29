---
name: surge-log-triage
description: Diagnose Surge rule matches, policy selection, DNS, and proxy-node failures from minimally redacted request or service logs. Use when a connection is misrouted or a node is unavailable.
---

# Surge Log Triage

Use this skill to explain a single observed failure before changing rules,
profiles, DNS, or a VPS. Start from the smallest reproducible request rather
than a full device export.

## Safe input

Ask for only the event window needed to diagnose the request: timestamp/time
zone, target hostname (or a public service name), matched rule, selected policy
group, result/error, network type, and any correlated server-side service error.

Before sharing logs, remove or replace:

- subscription and managed-Profile URLs, query strings, tokens, UUIDs, PSKs,
  passwords, authorization headers, and certificates;
- private domains, LAN addresses, public server addresses not needed for the
  diagnosis, device names, MAC addresses, and local file paths; and
- unrelated requests, full packet captures, or complete proxy configurations.

Stop and ask for a redacted excerpt if the supplied material includes secrets.
Do not preserve raw logs in the repository.

## Diagnosis order

Classify the issue before suggesting a change:

1. **Capture** — did Surge see the request and which hostname did it use?
2. **Rule** — which first matching rule or `RULE-SET` selected the policy?
3. **Policy** — does that group contain/select a working node or `DIRECT`?
4. **DNS / reachability** — is resolution wrong, blocked, or merely followed by
   a connection failure?
5. **Node service** — do the relevant, redacted VPS service status and recent
   log lines show a listener, TLS, authentication, resource, or firewall issue?

Do not add a new domain rule to compensate for an unavailable node. Do not
restart a VPS service simply because a request matched an unexpected rule.

## Output

State source observations separately from inference. Return the likely layer,
the single smallest verification or fix, confidence, and a rollback if a
configuration change is proposed. Route rule edits to `surge-rule-authoring`,
private Profile status to `private-profile-ops`, and host/service checks to
`vps-surge-ops`.
