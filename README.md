# sparkedhost

A tiny Python client for the [SparkedHost](https://sparkedhost.com) (Apollo Panel) API.

List your servers, hit power buttons, read & write files, manage backups — all behind a small `Client` / `Server` API.

## Install

```bash
pip install git+https://github.com/Jkratz01/sparkedhost.git
```

## Setup

Grab an API key from Apollo → **API Credentials**, then:

```bash
export SPARKEDHOST_API_KEY=your_key_here
```

(or pass `Client(api_key="...")` directly.)

## Usage

```python
from sparkedhost import Client

client = Client()  # reads SPARKEDHOST_API_KEY

# List your servers
for s in client.list_servers():
    print(s.identifier, s.name)

# Pick one
server = client.server("fd90ffb0-108d-4e24-996a-dc9678174d76")

# Power
server.restart()
server.stop()
server.start()

# Files
server.read_file("server.properties")
server.write_file("server.properties", "motd=hello world\n")
server.replace_in_file("server.properties",
                       old="motd=A Minecraft Server",
                       new="motd=Hello!")
server.delete_files(["bad.log"], root="/logs")

# Backups
server.create_backup(name="pre-update")
```

See [`example.py`](example.py) for every operation, and [`CLAUDE.md`](CLAUDE.md) for the full API reference.

## Using with Claude Code

This repo ships a [`CLAUDE.md`](CLAUDE.md) so Claude sessions in *this* repo are auto-fluent. To get the same in a *consuming* project, add to that project's `CLAUDE.md`:

```
We use sparkedhost — see https://raw.githubusercontent.com/Jkratz01/sparkedhost/main/CLAUDE.md
```

Or in a one-off Claude Code session, type `@https://raw.githubusercontent.com/Jkratz01/sparkedhost/main/CLAUDE.md` to load it on demand.

## License

[MIT](LICENSE)
