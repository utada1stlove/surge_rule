---
name: surge-rule-authoring
description: "Create and maintain Surge iPhone profiles and Rule Sets using a user's DAE-style traffic-splitting design, with GitHub-safe public/private separation. Use when editing Surge rules, organizing routing categories, or migrating DAE routing intent to Surge syntax."
---

# Surge Rule Authoring

Use this skill when the user wants to create, review, reorganize, or migrate Surge iPhone rules. The target is a maintainable text configuration in this repository, not live control of Surge.

## Operating boundary

- Do not require or invoke `surge-cli`.
- Do not claim that changing GitHub files changes the active iPhone Profile until Surge has fetched and applied the update.
- Treat the repository's public files as shareable. Never add subscription URLs, node passwords, tokens, UUIDs, PSKs, private keys, Controller keys, device MAC/IP addresses, private domains, or raw personal logs.
- Preserve the user's existing routing intent and rule order. If a DAE construct has no direct Surge equivalent, document it as a limitation or private override instead of inventing syntax.
- External writes such as `git push` require explicit user authorization in the current request.

## Default workflow

1. Read the repository `AGENTS.md`, current Profile, relevant Rule Sets, and migration notes before editing.
2. For a request such as “route service X through Y”, follow [the service-routing change guide](references/service-routing-change.md). Establish the requested hostnames, intended policy, affected Profile variant, and test case before making a change.
3. Preserve broad policy behavior first. Add category comments and rules before splitting policy groups.
4. Convert DAE intent into Surge rules using the reference below. Keep the most specific rules before broad catch-alls and keep `FINAL` last in the main `[Rule]` section.
5. Put public domain/IP rules in `rules/`. Keep personal nodes and private exceptions outside public files.
6. Update the relevant documentation when a new category, source, or limitation is introduced.
7. Run `surge-profile-lint` and the repository's basic validation. If a real Surge runtime is available, validate the Profile with that runtime; otherwise state that semantic validation remains pending.
8. Summarize changed files, policy mapping, unverified assumptions, the iPhone verification action, and the smallest rollback target.

## DAE migration principles

Use the user's DAE configuration as the source of routing intent, not as text to copy verbatim. Map:

```text
dae direct      → Surge DIRECT
dae proxy/group → Surge Proxy or a named future policy group
dae block       → Surge REJECT, only after checking false-positive risk
```

For the current repository, keep all public proxy categories under `Proxy` and mark future groups in comments, for example `AI Google → tw` and `AI other → sg`. Do not create a policy-group reference until that group exists in the Profile.

Read [Surge syntax reference](references/surge-syntax.md) when writing or reviewing syntax. Read [DAE migration map](references/dae-migration.md) when translating the mt6000 configuration or deciding whether a rule is public or private.

## Editing conventions

- Use clear Chinese section comments in `rules/*.list`.
- One matching rule per line; external Rule Sets must not append the policy name.
- Keep one routing intent per section. Prefer separate files once a section needs a different policy group.
- Record the source and reason for non-obvious domains.
- Avoid broad domains when a narrower service hostname is sufficient.
- Never remove an existing rule solely because it looks unusual; explain the conflict and ask for confirmation if removal changes behavior.
