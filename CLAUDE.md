# sparkedhost

Tiny Python client for the SparkedHost (Apollo Panel) API. Wraps the Pterodactyl-style `/api/client/*` endpoints at `https://control.sparkedhost.us`.

## Install

```bash
pip install git+https://github.com/Jkratz01/sparkedhost.git
# pin to a tag once cut: ...@v0.1.0
```

## Environment

| Var | Purpose | Required |
| --- | --- | --- |
| `SPARKEDHOST_API_KEY` | Bearer token (Apollo → API Credentials) | yes |
| `SPARKEDHOST_BASE_URL` | Override the panel URL | no, defaults to `https://control.sparkedhost.us` |

```bash
export SPARKEDHOST_API_KEY=...
```

Or pass directly: `Client(api_key="...")`.

## Quick start

```python
from sparkedhost import Client

client = Client()  # reads SPARKEDHOST_API_KEY

for s in client.list_servers():
    print(s.identifier, s.uuid, s.name)

server = client.server("fd90ffb0-108d-4e24-996a-dc9678174d76")
server.restart()
```

## API surface

### `Client`
- `Client(api_key=None, base_url=None, timeout=30)`
- `client.list_servers()` → list[Server], paginates fully
- `client.server(uuid)` → Server (fetches details)
- `client.account()` → dict

### `Server` — power
- `.start() / .stop() / .restart() / .kill()`
- `.power(signal)` where `signal ∈ {"start","stop","restart","kill"}`

### `Server` — status / commands
- `.resources()` → current CPU/RAM/disk/network
- `.send_command(command_string)` — write to console (server must be running)

### `Server` — files
| Method | Purpose |
| --- | --- |
| `list_files(directory="/")` | Directory listing |
| `read_file(path)` → str | Raw text contents |
| `write_file(path, content)` | Overwrite (str or bytes) |
| `replace_in_file(path, old, new, count=-1, must_exist=True)` | Read → `str.replace` → write |
| `delete_files(files, root="/")` | `files` is str or list |
| `rename_files([(from, to), ...], root="/")` | Bulk rename / move |
| `copy_file(location)` | Server-side copy |
| `create_folder(name, root="/")` | mkdir |
| `compress_files(files, root="/")` | Make archive |
| `decompress_file(file, root="/")` | Extract archive |
| `download_url(path)` → str | One-time signed download URL |
| `upload_url()` → str | One-time signed upload URL |
| `upload_file(local_path, remote_dir="/")` | Upload from local disk |

### `Server` — backups
- `.list_backups()`
- `.create_backup(name=None)`

### Server attributes
After `client.server(uuid)` or `client.list_servers()`, each `Server` has `.uuid`, `.identifier`, `.name`, `.node`, and the full panel response in `.attributes`.

## Errors

```python
from sparkedhost import APIError, AuthenticationError, NotFoundError, SparkedHostError
```
- `AuthenticationError` — 401 / 403
- `NotFoundError` — 404
- `APIError` — other 4xx / 5xx; `.status_code` and `.body` available

## Common recipes

**Restart every server:**
```python
for s in client.list_servers():
    s.restart()
```

**Edit `server.properties` in place:**
```python
s.replace_in_file("server.properties",
                  old="motd=A Minecraft Server",
                  new="motd=Hello world")
```

**Drop a config file straight from disk:**
```python
with open("local.yml") as f:
    s.write_file("config.yml", f.read())
```

**Wipe a logs folder:**
```python
listing = s.list_files("/logs")
files = [item["attributes"]["name"] for item in listing.get("data", [])]
if files:
    s.delete_files(files, root="/logs")
```

## Caveats / known assumptions

1. **`write_file` HTTP shape** — uses Pterodactyl convention `POST /files/write?file=PATH` with raw body. The OpenAPI spec implies `{"file": path}` in JSON body instead; if writes 4xx, flip the body shape.
2. **`list_servers` pagination** — assumes the standard `GET /api/client` endpoint with `meta.pagination`. If that route 404s, the panel may have renamed or removed it.
3. **No WebSocket console** — `send_command` is one-shot. Live log streaming requires the websocket endpoint (`/api/client/servers/{uuid}/websocket`), not yet wrapped.
4. **Not covered yet:** schedules, allocations, dedicated-node management, subusers, SSH keys, 2FA, databases. The spec has them; just not wrapped.

## Where it lives

- Repo: https://github.com/Jkratz01/sparkedhost
- Single module: [sparkedhost/client.py](sparkedhost/client.py)
- Examples: [example.py](example.py)
