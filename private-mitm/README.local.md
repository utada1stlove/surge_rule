# Local MITM material

This directory stores private Surge MITM configuration for local deployment.

## Files

- `mitm.conf`: private `[MITM]` section used by the VPS renderer.
- `ca-p12`: optional separate PKCS#12 file, only if the configuration is changed to reference a file instead of embedding `ca-p12`.

## Current format

The current `mitm.conf` already contains:

- `ca-passphrase`: the password protecting the PKCS#12 data;
- `ca-p12`: Base64-encoded PKCS#12 data containing the MITM CA certificate and private key;

Therefore, a separate `ca.p12` file is not required for the current setup. The long `ca-p12 = ...` value is the certificate bundle itself, encoded as text for inclusion in the Surge profile.

## Security rules

- Do not commit files under this directory except this README.
- Do not paste `ca-passphrase` or `ca-p12` into the public profile, public Rule Sets, issues, or chat logs.
- The VPS copy must be transferred over SSH/SCP/rsync and stored with restrictive permissions.
- Keep the MITM hostname list narrow; do not enable interception for all domains unless explicitly intended.
- If this directory or the CA password is exposed, generate a new MITM CA and replace the affected configuration.

## Deployment model

The public repository provides the public Surge configuration. A private deployment step copies `mitm.conf` to the VPS, where the renderer combines it with the public profile before serving the private profile endpoint.

Ignored files are not transferred by `git pull`; use an explicit private sync step such as SCP or rsync.
