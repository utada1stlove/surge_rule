---
name: private-profile-ops
description: "Safely operate the VPS-hosted private Surge Profile service: inspect status, refresh templates, switch Sub-Store sources, diagnose failures, and recover a prior release. Use for the repository's private Profile service, not for public rule edits."
---

# Private Profile Operations

Use this skill for the private service that renders the public Profile templates
with a locally stored Sub-Store URL. Read
`docs/operations/private-profile-service.md` before operating it.

## Data and authorization boundary

- The private Profile URL, subscription URL, secret files, node credentials,
  random paths, and rendered Profile contents are sensitive. Do not fetch,
  print, quote, or store them unless the user specifically requests the exact
  value for their own use.
- Read-only health checks may run against the SSH host that the user names or
  that this repository documents. Summarize sensitive command output rather
  than reproducing it.
- `surge-profilectl update`, `set*`, `clear*`, service installation, Nginx
  reloads, systemd changes, and remote file edits change external state. Run
  them only after the user has explicitly requested that exact operation in the
  current turn.
- Never copy `/etc/surge-profile/secrets.json` off the server or into this
  repository. Never place a private URL into a Git commit, issue, log, or
  generated artifact.

## Routine operations

Start with a health view that does not disclose URLs:

```bash
ssh HOST surge-profilectl status
ssh HOST systemctl list-timers surge-profile-render.timer --no-pager
ssh HOST journalctl -u surge-profile-render.service -n 20 --no-pager
```

Interpret results in this order: configured source, last successful release,
timer availability, then renderer failure. The renderer's atomic release model
means a failed update should leave the prior successful Profile active; do not
attempt a reinstall before confirming that condition.

For a template refresh explicitly requested by the user, run the documented
`surge-profilectl update`, then repeat the status check. For a source switch,
use the matching `set-default`, `set main`, `set simple`, or `clear` command;
the control command uses hidden input and validates before keeping the new
value. Do not simulate typed secrets or ask the user to paste them into chat.

## Diagnosis and recovery

Separate the failure layer before changing anything:

1. GitHub template fetch or validation failure;
2. Sub-Store response invalid or unavailable;
3. rendering/release failure;
4. Nginx/private URL reachability; or
5. iPhone Profile refresh/cache behavior.

Read the latest renderer log and status first. If the service reports an older
successful release, preserve it and investigate the failed candidate. Restore a
subscription override only with the corresponding `clear` command after the
user requests it. Treat service reinstallation as a separate, explicitly
authorized deployment task.

## Handoff

Report the host alias, read-only health result, last successful release state,
failed layer (if any), and the next smallest safe action. State clearly when
the iPhone still needs to refresh/apply the managed Profile.
