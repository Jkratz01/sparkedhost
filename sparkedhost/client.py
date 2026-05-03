import os

import requests

from .exceptions import APIError, AuthenticationError, NotFoundError, SparkedHostError

DEFAULT_BASE_URL = "https://control.sparkedhost.us"
POWER_SIGNALS = ("start", "stop", "restart", "kill")


class Server:
    def __init__(self, client, uuid, attributes=None):
        self._client = client
        self.uuid = uuid
        self.attributes = attributes or {}

    @property
    def name(self):
        return self.attributes.get("name")

    @property
    def identifier(self):
        return self.attributes.get("identifier", self.uuid)

    @property
    def node(self):
        return self.attributes.get("node")

    def __repr__(self):
        return f"<Server uuid={self.uuid!r} name={self.name!r}>"

    # ---- Power ----
    def power(self, signal):
        if signal not in POWER_SIGNALS:
            raise ValueError(f"signal must be one of {POWER_SIGNALS}, got {signal!r}")
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/power",
            json={"signal": signal},
        )

    def start(self):
        self.power("start")

    def stop(self):
        self.power("stop")

    def restart(self):
        self.power("restart")

    def kill(self):
        self.power("kill")

    # ---- Status ----
    def resources(self):
        return self._client._request(
            "GET", f"/api/client/servers/{self.uuid}/resources"
        )

    def send_command(self, command):
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/command",
            json={"command": command},
        )

    # ---- Files ----
    def list_files(self, directory="/"):
        return self._client._request(
            "GET",
            f"/api/client/servers/{self.uuid}/files/list",
            params={"directory": directory},
        )

    def read_file(self, path):
        return self._client._request(
            "GET",
            f"/api/client/servers/{self.uuid}/files/contents",
            params={"file": path},
            raw=True,
        )

    def write_file(self, path, content):
        if isinstance(content, str):
            content = content.encode("utf-8")
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/write",
            params={"file": path},
            data=content,
            headers={"Content-Type": "application/octet-stream"},
        )

    def replace_in_file(self, path, old, new, *, count=-1, must_exist=True):
        content = self.read_file(path)
        if must_exist and old not in content:
            raise SparkedHostError(f"substring {old!r} not found in {path}")
        if count < 0:
            new_content = content.replace(old, new)
        else:
            new_content = content.replace(old, new, count)
        if new_content != content:
            self.write_file(path, new_content)
        return new_content

    def delete_files(self, files, root="/"):
        if isinstance(files, str):
            files = [files]
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/delete",
            json={"root": root, "files": list(files)},
        )

    def rename_files(self, renames, root="/"):
        if isinstance(renames, tuple) and len(renames) == 2 and isinstance(renames[0], str):
            renames = [renames]
        files = [{"from": f, "to": t} for f, t in renames]
        self._client._request(
            "PUT",
            f"/api/client/servers/{self.uuid}/files/rename",
            json={"root": root, "files": files},
        )

    def copy_file(self, location):
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/copy",
            json={"location": location},
        )

    def create_folder(self, name, root="/"):
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/create-folder",
            json={"root": root, "name": name},
        )

    def compress_files(self, files, root="/"):
        if isinstance(files, str):
            files = [files]
        return self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/compress",
            json={"root": root, "files": list(files)},
        )

    def decompress_file(self, file, root="/"):
        self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/files/decompress",
            json={"root": root, "file": file},
        )

    def download_url(self, path):
        data = self._client._request(
            "GET",
            f"/api/client/servers/{self.uuid}/files/download",
            params={"file": path},
        )
        return data.get("attributes", {}).get("url") if isinstance(data, dict) else None

    def upload_url(self):
        data = self._client._request(
            "GET", f"/api/client/servers/{self.uuid}/files/upload"
        )
        return data.get("attributes", {}).get("url") if isinstance(data, dict) else None

    def upload_file(self, local_path, remote_dir="/"):
        url = self.upload_url()
        if not url:
            raise SparkedHostError("failed to obtain upload URL")
        with open(local_path, "rb") as f:
            resp = requests.post(
                url,
                params={"directory": remote_dir},
                files={"files": (os.path.basename(local_path), f)},
                timeout=self._client.timeout,
            )
        if not resp.ok:
            raise APIError(resp.status_code, resp.text, body=resp.text)

    # ---- Backups ----
    def list_backups(self):
        return self._client._request(
            "GET", f"/api/client/servers/{self.uuid}/backups"
        )

    def create_backup(self, name=None):
        body = {}
        if name is not None:
            body["name"] = name
        return self._client._request(
            "POST",
            f"/api/client/servers/{self.uuid}/backups",
            json=body,
        )


class Client:
    def __init__(self, api_key=None, base_url=None, timeout=30):
        self.api_key = api_key or os.environ.get("SPARKEDHOST_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "no API key provided — pass api_key= or set SPARKEDHOST_API_KEY"
            )
        self.base_url = (
            base_url
            or os.environ.get("SPARKEDHOST_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method, path, *, params=None, json=None, data=None, headers=None, raw=False):
        url = f"{self.base_url}{path}"
        merged_headers = None
        if headers:
            merged_headers = dict(self.session.headers)
            merged_headers.update(headers)

        resp = self.session.request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            headers=merged_headers,
            timeout=self.timeout,
        )

        if resp.status_code == 401:
            raise AuthenticationError("invalid or expired API key (401)")
        if resp.status_code == 403:
            raise AuthenticationError(f"forbidden (403): {resp.text}")
        if resp.status_code == 404:
            raise NotFoundError(f"not found: {method} {path}")
        if not (200 <= resp.status_code < 300):
            raise APIError(resp.status_code, resp.text, body=resp.text)

        if resp.status_code == 204 or not resp.content:
            return None
        if raw:
            return resp.text
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # ---- Account ----
    def account(self):
        return self._request("GET", "/api/client/account")

    # ---- Servers ----
    def list_servers(self):
        results = []
        page = 1
        while True:
            data = self._request("GET", "/api/client", params={"page": page})
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                uuid = attrs.get("uuid") or attrs.get("identifier")
                results.append(Server(self, uuid, attrs))
            meta = data.get("meta", {}).get("pagination", {})
            if not meta or page >= meta.get("total_pages", 1):
                break
            page += 1
        return results

    def server(self, uuid):
        data = self._request("GET", f"/api/client/servers/{uuid}")
        attrs = data.get("attributes", {}) if isinstance(data, dict) else {}
        return Server(self, uuid, attrs)
