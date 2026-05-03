import argparse
import json
import sys

from . import Client, SparkedHostError, __version__


def _print_json(obj):
    json.dump(obj, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def cmd_account(args, client):
    data = client.account()
    if args.json:
        _print_json(data)
        return
    a = data.get("attributes", data)
    print(f"id:    {a.get('id')}")
    print(f"email: {a.get('email')}")
    name = f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
    if name:
        print(f"name:  {name}")


def cmd_servers(args, client):
    servers = client.list_servers()
    if args.json:
        _print_json([s.attributes for s in servers])
        return
    if not servers:
        print("(no servers)")
        return
    for s in servers:
        state = ""
        if args.with_state:
            try:
                state = s.resources()["attributes"]["current_state"]
            except SparkedHostError:
                state = "?"
        line = f"{s.identifier:10}  {s.uuid}  {s.name or ''}"
        if state:
            line += f"  [{state}]"
        print(line)


def cmd_power(args, client):
    client.server(args.uuid).power(args.signal)
    print(f"sent {args.signal} to {args.uuid}")


def cmd_cmd(args, client):
    client.server(args.uuid).send_command(args.command)
    print(f"sent command to {args.uuid}")


def cmd_resources(args, client):
    data = client.server(args.uuid).resources()
    if args.json:
        _print_json(data)
        return
    a = data.get("attributes", {})
    r = a.get("resources", {})
    print(f"state:   {a.get('current_state')}")
    print(f"memory:  {r.get('memory_bytes', 0) / 1024**2:.1f} MiB")
    print(f"cpu:     {r.get('cpu_absolute', 0):.2f}%")
    print(f"disk:    {r.get('disk_bytes', 0) / 1024**2:.1f} MiB")
    print(f"uptime:  {r.get('uptime', 0) / 1000:.0f}s")


def cmd_ls(args, client):
    listing = client.server(args.uuid).list_files(args.path)
    if args.json:
        _print_json(listing)
        return
    items = listing.get("data", []) if isinstance(listing, dict) else []
    for item in items:
        a = item.get("attributes", {})
        kind = "-" if a.get("is_file") else "d"
        size = a.get("size", 0)
        print(f"{kind} {str(a.get('mode_bits', '----')):>4} {size:>10}  {a.get('name')}")


def cmd_cat(args, client):
    sys.stdout.write(client.server(args.uuid).read_file(args.path))


def cmd_write(args, client):
    if args.from_file:
        with open(args.from_file, "rb") as f:
            content = f.read()
    else:
        content = sys.stdin.buffer.read()
    client.server(args.uuid).write_file(args.path, content)
    print(f"wrote {len(content)} bytes to {args.path}", file=sys.stderr)


def cmd_rm(args, client):
    client.server(args.uuid).delete_files(args.files, root=args.root)
    print(f"deleted {len(args.files)} item(s) under {args.root}")


def cmd_mv(args, client):
    client.server(args.uuid).rename_files([(args.src, args.dst)], root=args.root)
    print(f"renamed {args.src} -> {args.dst} under {args.root}")


def cmd_mkdir(args, client):
    client.server(args.uuid).create_folder(args.name, root=args.root)
    print(f"created {args.root}/{args.name}")


def cmd_upload(args, client):
    client.server(args.uuid).upload_file(args.local, remote_dir=args.remote_dir)
    print(f"uploaded {args.local} to {args.remote_dir}")


def cmd_backup(args, client):
    data = client.server(args.uuid).create_backup(name=args.name)
    if args.json:
        _print_json(data)
        return
    a = data.get("attributes", {})
    print(f"backup queued: {a.get('uuid')}  name={a.get('name')!r}")


def cmd_backups(args, client):
    data = client.server(args.uuid).list_backups()
    if args.json:
        _print_json(data)
        return
    for item in data.get("data", []):
        a = item.get("attributes", {})
        done = "done   " if a.get("completed_at") else "pending"
        size = (a.get("bytes") or 0) / 1024**2
        print(f"{a.get('uuid')}  {done}  {size:8.1f} MiB  {a.get('name')}")


def _add_common(parser):
    parser.add_argument("--json", action="store_true", help="emit raw JSON")


def build_parser():
    p = argparse.ArgumentParser(
        prog="sparkedhost",
        description="SparkedHost (Apollo Panel) CLI. Reads SPARKEDHOST_API_KEY from env.",
    )
    p.add_argument("--version", action="version", version=f"sparkedhost {__version__}")
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    sp = sub.add_parser("account", help="show account info")
    _add_common(sp)
    sp.set_defaults(func=cmd_account)

    sp = sub.add_parser("servers", help="list all servers")
    _add_common(sp)
    sp.add_argument("--with-state", action="store_true",
                    help="also fetch each server's current_state (slower)")
    sp.set_defaults(func=cmd_servers)

    sp = sub.add_parser("power", help="send a power signal")
    sp.add_argument("uuid")
    sp.add_argument("signal", choices=["start", "stop", "restart", "kill"])
    sp.set_defaults(func=cmd_power)

    sp = sub.add_parser("cmd", help="send a console command (server must be running)")
    sp.add_argument("uuid")
    sp.add_argument("command")
    sp.set_defaults(func=cmd_cmd)

    sp = sub.add_parser("resources", help="show current resource usage")
    sp.add_argument("uuid")
    _add_common(sp)
    sp.set_defaults(func=cmd_resources)

    sp = sub.add_parser("ls", help="list files in a directory")
    sp.add_argument("uuid")
    sp.add_argument("path", nargs="?", default="/")
    _add_common(sp)
    sp.set_defaults(func=cmd_ls)

    sp = sub.add_parser("cat", help="read a file to stdout")
    sp.add_argument("uuid")
    sp.add_argument("path")
    sp.set_defaults(func=cmd_cat)

    sp = sub.add_parser("write", help="write a file (content from stdin, or --from-file)")
    sp.add_argument("uuid")
    sp.add_argument("path")
    sp.add_argument("--from-file", metavar="LOCAL_PATH",
                    help="read content from this local file instead of stdin")
    sp.set_defaults(func=cmd_write)

    sp = sub.add_parser("rm", help="delete files")
    sp.add_argument("uuid")
    sp.add_argument("files", nargs="+", metavar="FILE")
    sp.add_argument("--root", default="/", help="parent directory (default: /)")
    sp.set_defaults(func=cmd_rm)

    sp = sub.add_parser("mv", help="rename or move a file")
    sp.add_argument("uuid")
    sp.add_argument("src")
    sp.add_argument("dst")
    sp.add_argument("--root", default="/", help="parent directory (default: /)")
    sp.set_defaults(func=cmd_mv)

    sp = sub.add_parser("mkdir", help="create a folder")
    sp.add_argument("uuid")
    sp.add_argument("name")
    sp.add_argument("--root", default="/", help="parent directory (default: /)")
    sp.set_defaults(func=cmd_mkdir)

    sp = sub.add_parser("upload", help="upload a local file")
    sp.add_argument("uuid")
    sp.add_argument("local", metavar="LOCAL_PATH")
    sp.add_argument("remote_dir", nargs="?", default="/", metavar="REMOTE_DIR")
    sp.set_defaults(func=cmd_upload)

    sp = sub.add_parser("backup", help="create a backup")
    sp.add_argument("uuid")
    sp.add_argument("name", nargs="?")
    _add_common(sp)
    sp.set_defaults(func=cmd_backup)

    sp = sub.add_parser("backups", help="list backups")
    sp.add_argument("uuid")
    _add_common(sp)
    sp.set_defaults(func=cmd_backups)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "json"):
        args.json = False
    try:
        client = Client()
        args.func(args, client)
    except SparkedHostError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
