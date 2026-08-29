---
name: vps-surge-ops
description: Safely inspect and operate VPS hosts used for Surge services and proxy nodes, including systemd, Nginx, firewall, updates, backup, recovery, and Snell node deployment. Use for user-authorized server operations.
---

# VPS Surge Operations

Use this skill for Linux VPS hosts that provide the private Surge Profile
service or proxy nodes. Start with an inventory and make the smallest reversible
change that solves the requested problem.

## Authorization and secret boundary

- Read-only inspection is allowed for a host the user names. Summarize output;
  never repeat subscription URLs, credentials, private keys, PSKs, random
  private paths, or complete proxy configuration files.
- Installing packages/binaries, changing users, writing configuration, opening
  ports, changing firewall rules, reloading Nginx, restarting systemd units,
  applying updates, restoring backups, and deleting files are external state
  changes. Perform each only when the user requests that exact operation in the
  current turn.
- Before a remote write, state the target host, files/services affected,
  expected connectivity impact, validation, and smallest rollback. Do not
  combine routine package updates with proxy deployment or Profile changes.
- Preserve the SSH management path. Never replace firewall rules or restart
  networking blindly; confirm the existing SSH port and keep an active session
  until a changed service is verified.

## Read-only health inventory

For a health request, collect only the relevant pieces: OS/version and uptime;
disk/memory pressure; failed systemd units; the requested service status and
recent journal entries; listening TCP/UDP ports; timer state; and Nginx config
test when Nginx is involved. Do not dump all environment variables, process
arguments, or configuration files, since they can contain secrets.

Classify the result before proposing a repair:

1. host capacity or OS problem;
2. systemd unit/timer problem;
3. reverse-proxy or TLS problem;
4. firewall/listener reachability problem; or
5. client subscription/Profile/routing problem.

Use `private-profile-ops` for the Profile renderer's application-specific
status and recovery path.

## Change workflow

1. Establish baseline health and current listener/firewall state.
2. Identify the exact service, port, protocol, config path, and owner. Obtain
   the version/source and checksum from the protocol's official release or the
   user's approved package source.
3. Explain the write plan, validation command, and rollback before executing.
4. Make the smallest scoped change. Store secrets only in root-readable server
   files; never in this repository or shell history.
5. Verify the service is active, bound to the intended interface/port, and has
   no fresh errors. Where possible, run a client-side connectivity check.
6. Report what changed without echoing secrets, and identify the rollback
   command or backup retained.

## Updates, backup, and recovery

For updates, inspect pending packages and security impact before applying them.
For a backup, record what is protected, where it is stored, permissions, and a
restore test or verification; do not copy secret material into the repository.
For recovery, stop at the smallest failed layer and preserve working Profile
releases and node configurations until the user authorizes restoration.

## Protocol modules

Read [Snell node deployment](references/snell-node-deployment.md) only when the
user requests a Snell node. Add other protocols as separate modules rather than
assuming Snell configuration applies to them.
