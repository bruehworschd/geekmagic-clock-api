#!/usr/bin/env python3
"""Minimal client for the (unofficial, reverse-engineered) GeekMagic Clock HTTP API.

See README.md for background and the full list of discovered endpoints.

Usage:
    python3 client.py --host <device-ip> list
    python3 client.py --host <device-ip> upload foto.jpg --dir /image/
    python3 client.py --host <device-ip> activate /image/foto.jpg
    python3 client.py --host <device-ip> delete /image/foto.jpg
    python3 client.py --host <device-ip> autoplay --interval 30 --on
    python3 client.py --host <device-ip> space
"""

import argparse
import sys
import urllib.parse
import urllib.request


def _get(host: str, path: str) -> str:
    url = f"http://{host}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def list_files(host: str, directory: str = "/image/") -> str:
    return _get(host, f"/filelist?dir={directory}")


def space(host: str) -> str:
    return _get(host, "/space.json")


def activate(host: str, path: str) -> str:
    """Set an already-uploaded image as the active display. Raw path, no URL-encoding."""
    return _get(host, f"/set?img={path}")


def delete(host: str, path: str) -> str:
    """Delete a file. Path MUST be URL-encoded (unlike activate()), or the device replies 'Fail'."""
    encoded = urllib.parse.quote(path, safe="")
    return _get(host, f"/delete?file={encoded}")


def clear_all(host: str) -> str:
    return _get(host, "/set?clear=image")


def set_autoplay(host: str, interval_seconds: int, enabled: bool) -> str:
    return _get(host, f"/set?i_i={interval_seconds}&autoplay={1 if enabled else 0}")


def upload(host: str, file_path: str, directory: str = "/image/") -> str:
    """Upload a JPEG/GIF. No external deps — builds the multipart body by hand."""
    boundary = "----geekmagicclient"
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    filename = file_path.rsplit("/", 1)[-1]
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"http://{host}/doUpload?dir={directory}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True, help="Geräte-IP oder Hostname, ohne http://")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list").add_argument("--dir", default="/image/")
    sub.add_parser("space")

    p_upload = sub.add_parser("upload")
    p_upload.add_argument("file")
    p_upload.add_argument("--dir", default="/image/")

    p_activate = sub.add_parser("activate")
    p_activate.add_argument("path", help="z. B. /image/foto.jpg")

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("path", help="z. B. /image/foto.jpg (wird intern URL-kodiert)")

    sub.add_parser("clear")

    p_autoplay = sub.add_parser("autoplay")
    p_autoplay.add_argument("--interval", type=int, default=30)
    group = p_autoplay.add_mutually_exclusive_group(required=True)
    group.add_argument("--on", action="store_true")
    group.add_argument("--off", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        print(list_files(args.host, args.dir))
    elif args.command == "space":
        print(space(args.host))
    elif args.command == "upload":
        print(upload(args.host, args.file, args.dir))
    elif args.command == "activate":
        print(activate(args.host, args.path))
    elif args.command == "delete":
        print(delete(args.host, args.path))
    elif args.command == "clear":
        print(clear_all(args.host))
    elif args.command == "autoplay":
        print(set_autoplay(args.host, args.interval, args.on))

    return 0


if __name__ == "__main__":
    sys.exit(main())
