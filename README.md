# sparkedhost

A tiny Python client for the [SparkedHost](https://sparkedhost.com) (Apollo Panel) API.

List your servers, hit power buttons, read & write files, manage backups — all behind a small `Client` / `Server` API.

## Install

```bash
pip install sparkedhost
```

Or pull the latest from `main` directly:

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

## CLI

Installing also drops a `sparkedhost` command on your `PATH`:

```bash
sparkedhost servers                              # list servers
sparkedhost power <uuid> restart                 # power action
sparkedhost cmd <uuid> "say hello"               # console command
sparkedhost ls <uuid> /logs                      # list a directory
sparkedhost cat <uuid> server.properties         # read a file
echo "motd=hi" | sparkedhost write <uuid> server.properties
sparkedhost rm <uuid> bad.log --root /logs
sparkedhost backup <uuid> "pre-update"
```

`sparkedhost --help` lists every subcommand. Commands that fetch data accept `--json` for raw output (pipeable to `jq`).

## Using with Claude Code

This repo ships a [`CLAUDE.md`](CLAUDE.md) so Claude sessions in *this* repo are auto-fluent. To get the same in a *consuming* project, add to that project's `CLAUDE.md`:

```
We use sparkedhost — see https://raw.githubusercontent.com/Jkratz01/sparkedhost/main/CLAUDE.md
```

Or in a one-off Claude Code session, type `@https://raw.githubusercontent.com/Jkratz01/sparkedhost/main/CLAUDE.md` to load it on demand.

## License

[MIT](LICENSE)
