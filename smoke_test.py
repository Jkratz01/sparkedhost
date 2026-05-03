"""Smoke test for the sparkedhost client.

Runs read-only checks first, then optional write/read/delete cycle.

Required:
  SPARKEDHOST_API_KEY   - your API key

Optional:
  SPARKEDHOST_TEST_SERVER_UUID  - target a specific server (otherwise uses the first one)
  SPARKEDHOST_TEST_WRITES=1     - exercise the write/read/delete cycle
"""
import os
import sys


def section(title):
    print(f"\n=== {title} ===")


def ok(msg):
    print(f"  [OK]   {msg}")


def fail(msg):
    print(f"  [FAIL] {msg}")


try:
    from sparkedhost import APIError, AuthenticationError, Client, NotFoundError
except ImportError as e:
    print(f"could not import sparkedhost: {e}")
    print("from this directory, run:  .venv/bin/pip install -e .")
    sys.exit(1)


if not os.environ.get("SPARKEDHOST_API_KEY"):
    print("SPARKEDHOST_API_KEY env var is not set.")
    print("get a key from Apollo -> API Credentials, then:")
    print("  export SPARKEDHOST_API_KEY=your_key_here")
    sys.exit(1)


client = Client()

# 1. Auth
section("auth (GET /api/client/account)")
try:
    acct = client.account()
    ok(f"authenticated as: {acct.get('attributes', {}).get('email', acct)}")
except AuthenticationError as e:
    fail(str(e))
    sys.exit(1)
except APIError as e:
    fail(f"unexpected: {e}")
    sys.exit(1)

# 2. List servers
section("list servers (GET /api/client)")
try:
    servers = client.list_servers()
    ok(f"found {len(servers)} server(s)")
    for s in servers[:10]:
        print(f"        - {s.identifier}  {s.name!r}  uuid={s.uuid}")
except APIError as e:
    fail(f"list_servers: {e}")
    servers = []

# Pick a target
target_uuid = os.environ.get("SPARKEDHOST_TEST_SERVER_UUID") or (
    servers[0].uuid if servers else None
)
if not target_uuid:
    print("\nno server to inspect further; stopping here")
    sys.exit(0)

server = client.server(target_uuid)
print(f"\ntarget server: {server.name!r}  uuid={server.uuid}")

# 3. Resources
section("resources (GET /servers/{uuid}/resources)")
try:
    res = server.resources()
    state = res.get("attributes", {}).get("current_state", res)
    ok(f"current_state={state}")
except APIError as e:
    fail(f"resources: {e}")

# 4. List root files
section("list files / (GET /servers/{uuid}/files/list)")
try:
    listing = server.list_files("/")
    items = listing.get("data", []) if isinstance(listing, dict) else []
    names = [i.get("attributes", {}).get("name") for i in items]
    ok(f"{len(items)} entries: {names[:8]}{' ...' if len(names) > 8 else ''}")
except APIError as e:
    fail(f"list_files: {e}")

# 5. Write/read/delete cycle (optional)
if os.environ.get("SPARKEDHOST_TEST_WRITES") == "1":
    section("write/read/delete cycle")
    test_path = "_sparkedhost_smoke.txt"
    test_payload = "hello from sparkedhost smoke test\n"
    try:
        server.write_file(test_path, test_payload)
        ok(f"wrote {test_path}")
    except APIError as e:
        fail(f"write_file: {e}")
        print("\n>>> if this 4xx'd, the write endpoint convention may need flipping")
        print(">>> see CLAUDE.md 'Caveats' section")
        sys.exit(1)

    try:
        got = server.read_file(test_path)
        if got == test_payload:
            ok("read_file returned exact payload written")
        else:
            fail(f"read_file mismatch: got {got!r}")
    except APIError as e:
        fail(f"read_file: {e}")

    try:
        server.delete_files([test_path], root="/")
        ok(f"deleted {test_path}")
    except APIError as e:
        fail(f"delete_files: {e}")
else:
    print("\nset SPARKEDHOST_TEST_WRITES=1 to exercise write/read/delete")

print("\nsmoke test complete")
