from sparkedhost import Client

client = Client()  # reads SPARKEDHOST_API_KEY from env

# 1. List all servers
servers = client.list_servers()
for s in servers:
    print(f"{s.identifier}  {s.uuid}  {s.name}")

# 2. Pick one (replace with a real UUID from the list above)
server = client.server("fd90ffb0-108d-4e24-996a-dc9678174d76")

# 3. Power actions
server.start()
server.restart()
server.stop()
server.kill()

# 4. Live resource usage
print(server.resources())

# 5. Send a console command
server.send_command("say hello from python")

# 6. Files: list a directory
print(server.list_files("/"))

# 7. Files: read a file
contents = server.read_file("server.properties")
print(contents)

# 8. Files: replace the entire file
server.write_file("server.properties", "motd=hello world\n")

# 9. Files: replace text inside a file (read -> str.replace -> write)
server.replace_in_file(
    "server.properties",
    old="motd=A Minecraft Server",
    new="motd=Hello from python",
)

# 10. Files: delete
server.delete_files(["bad.log", "old.log"], root="/logs")

# 11. Files: rename / move
server.rename_files([("old_name.txt", "new_name.txt")], root="/")

# 12. Files: make a folder
server.create_folder("mods_backup", root="/")

# 13. Files: upload a local file
server.upload_file("/path/to/local/file.zip", remote_dir="/")

# 14. Backups
print(server.list_backups())
server.create_backup(name="pre-update")
