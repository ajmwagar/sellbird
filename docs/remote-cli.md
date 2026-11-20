# Hosted CLI over HTTPS

The CLI can run against a hosted Sellbird instead of the local checkout's
SQLite database. It sends an allowlisted command to `/remote-api/cli`; the
server runs the same CLI in a child process with its own config, database and
credentials, and returns stdout/stderr.

## Server

Set an API key on the hosted install:

```env
SELLBIRD_API_KEY=sk-sellbird-...
SELLBIRD_API_HOST=sellbird-api.fpl.dev
```

Expose the API host (or a no-Vouch path for `/remote-api`) at the TLS edge.
The dashboard itself stays behind its normal SSO/token auth.

## Client

Create `~/.config/sellbird/remote.env`:

```env
SELLBIRD_API_URL=https://sellbird-api.fpl.dev
SELLBIRD_API_KEY=sk-sellbird-...
```

Then normal read/control commands use the hosted install automatically:

```bash
sellbird status
sellbird outbox
sellbird usage
sellbird warmup
sellbird inboxes list
sellbird sending pause
```

Force the local checkout with `SELLBIRD_LOCAL=1`. The explicit form is:

```bash
sellbird remote status
```

Remote commands are allowlisted: `status`, `companies`, `outbox`, `usage`,
`warmup`, `runs`, `inboxes list`, and `sending pause|resume|status`. Setup,
OAuth, training and long-running loops stay local/server-only.
