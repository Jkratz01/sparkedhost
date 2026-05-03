# sparkedhost — full reference

A Python client for the **SparkedHost** game-hosting panel ("Apollo Panel"), which is a Pterodactyl fork. Wraps the Bearer-authenticated `/api/client/*` endpoints at `https://control.sparkedhost.us`.

> If you're an LLM helping a user use this library, you can answer every "how do I..." question from this file. Do not guess endpoints — every operation supported is listed here. Anything not listed is **not yet wrapped**; see "Out of scope" at the bottom.

Repo: https://github.com/Jkratz01/sparkedhost · Source: [sparkedhost/client.py](sparkedhost/client.py) · Examples: [example.py](example.py)

---

## 1. Install

```bash
# normal install from PyPI (recommended)
pip install sparkedhost

# pin a specific version
pip install sparkedhost==0.1.0

# install latest unreleased changes straight from GitHub main
pip install git+https://github.com/Jkratz01/sparkedhost.git
```

PyPI: https://pypi.org/project/sparkedhost/. Runtime dep: `requests>=2.25`. Python 3.8+.

## 2. Environment

| Var | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SPARKEDHOST_API_KEY` | yes | — | Bearer token. Get it from Apollo → **Account Settings → API Credentials** (a `ptlc_…` string ~48 chars). |
| `SPARKEDHOST_BASE_URL` | no | `https://control.sparkedhost.us` | Override only if SparkedHost migrates panels. |

Programmatic override: `Client(api_key="...", base_url="...", timeout=30)`. Direct args win over env vars.

**Never commit the key.** The repo's `.gitignore` excludes `.env`.

## 3. 60-second quickstart

```python
from sparkedhost import Client

client = Client()                                     # uses SPARKEDHOST_API_KEY

for s in client.list_servers():                       # paginates automatically
    print(s.identifier, s.name, "→", s.uuid)

server = client.server("fd90ffb0-108d-4e24-996a-dc9678174d76")
server.restart()
server.send_command("say hello")
text = server.read_file("server.properties")
server.write_file("server.properties", text + "\n# touched\n")
```

## 4. Authentication contract

Every request sends `Authorization: Bearer <key>` and `Accept: application/json`. The client maps HTTP status to exceptions:

| Status | Raises | Notes |
| --- | --- | --- |
| 2xx | — | Returns parsed JSON, raw text (when `raw=True`), or `None` on 204. |
| 401 | `AuthenticationError` | Invalid/expired key. |
| 403 | `AuthenticationError` | Key valid but lacks permission for that resource. |
| 404 | `NotFoundError` | Wrong UUID, wrong path, deleted resource. |
| other 4xx/5xx | `APIError` | Inspect `.status_code` and `.body` (raw response text). |

```python
from sparkedhost import APIError, AuthenticationError, NotFoundError, SparkedHostError
# SparkedHostError is the base class — catch it to catch all of the above.
```

## 5. Class reference

### 5.1 `Client(api_key=None, base_url=None, timeout=30)`

| Method | Signature | Returns | Endpoint |
| --- | --- | --- | --- |
| `account()` | `() -> dict` | Account envelope (see §6) | `GET /api/client/account` |
| `list_servers()` | `() -> list[Server]` | All accessible servers; paginates fully | `GET /api/client?page=N` |
| `server(uuid)` | `(str) -> Server` | Single server with `.attributes` populated | `GET /api/client/servers/{uuid}` |

### 5.2 `Server`

Constructed by the `Client`; never instantiate directly.

**Properties (read-only, populated on construction):**

| Attr | Type | Source |
| --- | --- | --- |
| `.uuid` | `str` | Constructor arg |
| `.identifier` | `str` | `attributes.identifier` (8-char short id) |
| `.name` | `str \| None` | `attributes.name` |
| `.node` | `str \| None` | `attributes.node` |
| `.attributes` | `dict` | Full server payload (see §6 for keys) |

**Power — all return `None`:**

| Method | Endpoint | Body |
| --- | --- | --- |
| `power(signal)` | `POST /servers/{uuid}/power` | `{"signal": signal}` where signal ∈ `{"start","stop","restart","kill"}` |
| `start()` | same | shortcut for `power("start")` |
| `stop()` | same | gracefully stop |
| `restart()` | same | stop+start |
| `kill()` | same | force-kill (use sparingly — risks data loss) |

**Status / commands:**

| Method | Returns | Endpoint |
| --- | --- | --- |
| `resources()` | `dict` (envelope, see §6.3) | `GET /servers/{uuid}/resources` |
| `send_command(command: str)` | `None` | `POST /servers/{uuid}/command` body `{"command": ...}`. **Server must be running** or panel returns 502. |

**Files** — all paths use `/` as the separator. `/` is the server's home directory (typically `/home/container`). Methods with `root=` treat names as **relative** to `root`; methods with `path=` use the full path from `/`.

| Method | Returns | Endpoint |
| --- | --- | --- |
| `list_files(directory="/")` | `dict` (list envelope) | `GET /servers/{uuid}/files/list?directory=...` |
| `read_file(path)` | `str` (raw contents) | `GET /servers/{uuid}/files/contents?file=...` |
| `write_file(path, content: str \| bytes)` | `None` | `POST /servers/{uuid}/files/write?file=...`, body = raw content. Overwrites unconditionally. Strings are UTF-8 encoded. |
| `replace_in_file(path, old, new, *, count=-1, must_exist=True)` | `str` (the new content) | Read → `str.replace` → write. Skips the write if no change. Raises `SparkedHostError` if `must_exist` and `old` not present. |
| `delete_files(files, root="/")` | `None` | `POST /servers/{uuid}/files/delete` body `{"root": root, "files": [...]}`. `files` accepts a single string or an iterable. |
| `rename_files(renames, root="/")` | `None` | `PUT /servers/{uuid}/files/rename` body `{"root": root, "files": [{"from": ..., "to": ...}, ...]}`. Accepts a single `(from, to)` tuple or a list. Doubles as **move** (when `to` contains a path). |
| `copy_file(location)` | `None` | `POST /servers/{uuid}/files/copy` body `{"location": ...}`. Server-side copy; produces `<name> copy.<ext>` next to the original. |
| `create_folder(name, root="/")` | `None` | `POST /servers/{uuid}/files/create-folder` body `{"root": root, "name": name}` |
| `compress_files(files, root="/")` | `dict` (the new archive's file entry) | `POST /servers/{uuid}/files/compress` body `{"root": root, "files": [...]}`. Always produces a `.tar.gz`. |
| `decompress_file(file, root="/")` | `None` | `POST /servers/{uuid}/files/decompress` body `{"root": root, "file": file}`. Supports `.zip`, `.tar.gz`, `.tar.xz`, etc. |
| `download_url(path)` | `str` (one-time URL) | `GET /servers/{uuid}/files/download?file=...`. URL expires in seconds — fetch immediately. |
| `upload_url()` | `str` (one-time URL) | `GET /servers/{uuid}/files/upload`. POST a multipart form with field `files` to that URL, optional `?directory=` query. |
| `upload_file(local_path, remote_dir="/")` | `None` | Convenience wrapper: gets `upload_url()` and posts the local file. |

**Backups:**

| Method | Returns | Endpoint |
| --- | --- | --- |
| `list_backups()` | `dict` (list envelope of backups) | `GET /servers/{uuid}/backups` |
| `create_backup(name=None)` | `dict` (the new backup's envelope) | `POST /servers/{uuid}/backups`, body `{"name": ...}` if provided. **Async on the panel side** — poll `list_backups()` and check `attributes.completed_at` to know when it's done. |

## 6. Response envelopes

All Apollo responses follow the Pterodactyl JSON:API style.

### 6.1 Single resource

```jsonc
{
  "object": "server",
  "attributes": { /* the actual fields */ }
}
```

In code: `data["attributes"]`.

### 6.2 List

```jsonc
{
  "object": "list",
  "data": [
    { "object": "server", "attributes": { ... } },
    { "object": "server", "attributes": { ... } }
  ],
  "meta": {
    "pagination": { "total": 14, "count": 14, "per_page": 50, "current_page": 1, "total_pages": 1 }
  }
}
```

`Client.list_servers()` walks all pages and returns `Server` objects directly — you don't need to parse pagination. Other list endpoints (`list_files`, `list_backups`) return the raw envelope so you'd do `[i["attributes"] for i in resp["data"]]`.

### 6.3 Useful attribute keys (verified or standard for this panel family)

**`account()` → `attributes`:** `id`, `admin` (bool), `username`, `email`, `first_name`, `last_name`, `language`.

**Server (`Server.attributes` and items in `list_servers()` data):**
`server_owner` (bool), `identifier` (8-char), `uuid`, `name`, `node`, `description`,
`limits`: `{memory, swap, disk, io, cpu}` (MiB / weight / %),
`feature_limits`: `{databases, allocations, backups}`,
`is_suspended` (bool), `is_installing` (bool),
`relationships.allocations.data[0].attributes`: `{ip, ip_alias, port, is_default}` — your connection address.

**`resources()` → `attributes`:** `current_state` (`"running" | "starting" | "stopping" | "offline"`),
`is_suspended` (bool),
`resources`: `{memory_bytes, cpu_absolute, disk_bytes, network_rx_bytes, network_tx_bytes, uptime}` (uptime in ms).

**`list_files()` → each `data[i].attributes`:** `name`, `mode` (`"-rwxr-xr-x"`), `mode_bits` (octal string), `size` (bytes), `is_file` (bool), `is_symlink` (bool), `mimetype`, `created_at`, `modified_at`.

**Backup (`list_backups()` items / `create_backup()` return):** `uuid`, `name`, `ignored_files`, `sha256_hash` (null until done), `bytes` (0 until done), `created_at`, `completed_at` (null while running), `is_locked`, `is_successful`.

## 7. Cookbook

### Restart all running servers
```python
for s in client.list_servers():
    if s.attributes.get("is_suspended"):
        continue
    if s.resources()["attributes"]["current_state"] == "running":
        s.restart()
```

### Edit a config in place
```python
server.replace_in_file(
    "server.properties",
    old="motd=A Minecraft Server",
    new="motd=Welcome",
)
```

### Push a local file to the server
```python
with open("/tmp/config.yml", "rb") as f:
    server.write_file("plugins/MyPlugin/config.yml", f.read())
```
Or for a binary upload via the panel's upload service:
```python
server.upload_file("/tmp/world.zip", remote_dir="/")
server.decompress_file("world.zip", root="/")
server.delete_files(["world.zip"], root="/")
```

### List + filter files in a directory
```python
listing = server.list_files("/logs")
log_files = [
    item["attributes"]["name"]
    for item in listing["data"]
    if item["attributes"]["is_file"] and item["attributes"]["name"].endswith(".log")
]
```

### Delete every file in a folder (server-side)
```python
listing = server.list_files("/logs")
names = [i["attributes"]["name"] for i in listing["data"]]
if names:
    server.delete_files(names, root="/logs")
```

### Move / rename
```python
server.rename_files([("old.yml", "new.yml")], root="/configs")
server.rename_files([("configs/old.yml", "backup/old.yml")], root="/")  # cross-dir = move
```

### Create a backup and wait for it to finish
```python
import time

resp = server.create_backup(name="pre-update")
backup_uuid = resp["attributes"]["uuid"]

while True:
    page = server.list_backups()
    me = next(b for b in page["data"] if b["attributes"]["uuid"] == backup_uuid)
    if me["attributes"]["completed_at"]:
        print("done, hash:", me["attributes"]["sha256_hash"])
        break
    time.sleep(5)
```

### Send a Minecraft `say` command (server must be running)
```python
state = server.resources()["attributes"]["current_state"]
if state == "running":
    server.send_command("say maintenance in 5 minutes")
```

### Get the connection address
```python
ip = server.attributes["relationships"]["allocations"]["data"][0]["attributes"]["ip_alias"]
port = server.attributes["relationships"]["allocations"]["data"][0]["attributes"]["port"]
print(f"connect to {ip}:{port}")
```

### Find a server by name
```python
def by_name(name):
    for s in client.list_servers():
        if s.name == name:
            return s
    raise LookupError(name)
```

### Catch all errors uniformly
```python
from sparkedhost import SparkedHostError
try:
    server.restart()
except SparkedHostError as e:
    log.exception("panel call failed: %s", e)
```

## 8. Invariants & gotchas

- **Paths use `/`**, never `\`. Leading `/` is the server's home directory.
- **`root` vs `path`**: file ops with a `root=` kwarg take **bare names** in `files`/`name`; ops with a `path=` argument take the **full** path. Mixing them silently writes to the wrong place.
- **`write_file` overwrites** with no confirmation. To append, do `read_file` → concatenate → `write_file`.
- **Power signals are lowercase** (`"start"`, not `"Start"`).
- **`send_command` requires a running server** — calling it on an offline server returns 502; the lib raises `APIError(502, ...)`.
- **`download_url` and `upload_url` are short-lived** (seconds). Use immediately; don't cache.
- **`create_backup` is async.** The returned backup has `completed_at: null` and `bytes: 0`. Poll `list_backups()` until `completed_at` is set.
- **`list_servers` is one HTTP call per page.** With many servers, cache the result instead of calling it in a loop.
- **`Server` objects don't refresh.** `server.attributes` is a snapshot from when you fetched it. Re-call `client.server(uuid)` to refresh.
- **Identifier vs UUID**: the panel's REST API takes the **UUID** in `/servers/{uuid}/...`. The 8-char `identifier` is just for display. This client uses UUIDs throughout.
- **No retry / no rate-limit handling.** Single attempt per call. If the panel returns 429, `APIError(429, ...)` is raised and you should back off.

## 9. Anti-patterns (don't do these)

```python
# DON'T: instantiate Server directly — it won't have a Client and breaks every call.
from sparkedhost import Server
s = Server(None, "uuid")  # BAD

# DO:
s = client.server("uuid")
```

```python
# DON'T: paste the API key in source. Use env vars.
client = Client(api_key="ptlc_realKeyHere")  # BAD

# DO:
client = Client()  # reads SPARKEDHOST_API_KEY
```

```python
# DON'T: list_servers() in a hot loop.
for _ in range(100):
    for s in client.list_servers():  # BAD: 100 * (pages) HTTP calls
        ...

# DO: cache it.
servers = client.list_servers()
for _ in range(100):
    for s in servers:
        ...
```

```python
# DON'T: use kill() as the default stop.
server.kill()  # BAD: hard-kill, can corrupt world saves

# DO:
server.stop()      # graceful
server.kill()      # only after stop() times out
```

## 10. Out of scope (not yet wrapped)

These endpoints exist on the panel but are not in the client. PRs welcome; meanwhile drop to raw `Client._request(method, path, json=...)`.

- WebSocket console + live log streaming (`/api/client/servers/{uuid}/websocket`)
- Server schedules (cron)
- Allocations management (network ports)
- Subusers and per-user permissions
- Database creation/management
- 2FA enable/disable, SSH keys, API key CRUD on the account
- Dedicated-node management (the entire `/api/client/dedicated/*` tree)
- Workshop / Steam content management
- The `/api/client/servers/{uuid}/setup/finish` flow (initial provisioning)

## 11. Verification

The repo ships [smoke_test.py](smoke_test.py). To verify the client works in your environment:

```bash
export SPARKEDHOST_API_KEY=...
python smoke_test.py                              # read-only checks
SPARKEDHOST_TEST_WRITES=1 python smoke_test.py    # adds a write/read/delete round-trip
SPARKEDHOST_TEST_SERVER_UUID=<uuid> python smoke_test.py  # target a specific server
```

A passing run confirms auth, pagination, server lookup, resources, file listing, and (optionally) the file write convention against the live panel.

## 12. Versioning

`__version__` is exported from the package (`from sparkedhost import __version__`). The repo currently ships `0.1.1`. Bumping conventions are not enforced — when in doubt, semver.

## 13. CLI

Installing the package also drops a `sparkedhost` command on `$PATH`. Every command reads `SPARKEDHOST_API_KEY` from the environment. Add `--json` to commands that support it for machine-parseable output.

```
sparkedhost --help
sparkedhost --version

sparkedhost account
sparkedhost servers                       # uuid + name table
sparkedhost servers --with-state          # also fetch each server's current_state (slower)
sparkedhost servers --json                # raw JSON of every server's attributes

sparkedhost power <uuid> {start|stop|restart|kill}
sparkedhost cmd <uuid> "say hello"        # send a console command (server must be running)
sparkedhost resources <uuid>              # state + memory + cpu + disk + uptime
sparkedhost resources <uuid> --json

sparkedhost ls <uuid>                     # list /
sparkedhost ls <uuid> /logs               # list /logs
sparkedhost cat <uuid> server.properties  # write file contents to stdout
echo "motd=hello" | sparkedhost write <uuid> server.properties
sparkedhost write <uuid> config.yml --from-file ./local-config.yml
sparkedhost rm <uuid> bad.log old.log --root /logs
sparkedhost mv <uuid> old.txt new.txt
sparkedhost mkdir <uuid> backups
sparkedhost upload <uuid> /tmp/world.zip /

sparkedhost backup <uuid> "pre-update"
sparkedhost backups <uuid>                # uuid, status (done/pending), size, name
```

**Pipe / redirect patterns:**
```bash
# back up a config file to local disk
sparkedhost cat <uuid> server.properties > server.properties.bak

# round-trip edit
sparkedhost cat <uuid> server.properties \
  | sed 's/^motd=.*/motd=Hello world/' \
  | sparkedhost write <uuid> server.properties

# get just the running server UUIDs
sparkedhost servers --json | jq -r '.[] | select(.is_suspended | not) | .uuid'
```

Exit codes: `0` on success, `1` on `SparkedHostError` (with the message on stderr), `130` on `Ctrl-C`.
