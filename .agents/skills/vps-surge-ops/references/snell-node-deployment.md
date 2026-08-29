# Snell Node Deployment

Use this module only after the user explicitly requests a Snell installation,
update, repair, or removal on a named VPS. It does not authorize a server
change by itself.

## Preflight

Establish and report, without exposing credentials:

- VPS OS/architecture and existing service manager;
- intended public listener address and port, and whether TCP/UDP reachability
  is required by the selected Snell version and client mode;
- existing listener/firewall state and SSH management port;
- the official Snell release source, selected version, and checksum/signature
  verification method; and
- how the client node will enter the user's private Sub-Store input or other
  private node source.

Do not put a Snell PSK, server address, subscription URL, or generated client
link in Git, chat summaries, CI logs, or public Profile templates.

## Deployment plan

Before writing, name the service account, binary path, root-readable config
path, systemd unit name, listener port, firewall operation, verification, and
rollback. Keep the configuration file mode restricted (normally root-readable
only). Prefer a dedicated systemd unit and explicit service ownership over a
background shell process.

Install from the official release selected during preflight, verify its
integrity, write the private configuration, install/enable the service, and
open only the intended port while preserving SSH access. Do not infer package
manager commands or a release artifact from another distribution/version.

## Verification and integration

Verify, in order:

1. systemd reports the unit active and recent logs have no startup error;
2. the expected listener is bound locally;
3. the firewall exposes only the intended port;
4. a client using the private node source can connect; and
5. the node appears in the expected Sub-Store output or Surge policy group.

Adding a Snell node normally changes only the private node/subscription chain;
it does not require a new public Surge rule or policy group unless the user
also asks for traffic segmentation.

## Rollback

Retain the prior binary/config and firewall state until client verification
succeeds. On failure, disable the new unit, restore the prior known-good unit
or config, remove only the newly opened service port, and confirm SSH remains
reachable. Do not delete a working node or rotate its PSK without an explicit
request.
