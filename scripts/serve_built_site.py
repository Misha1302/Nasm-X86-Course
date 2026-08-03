#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


class VitePressHandler(SimpleHTTPRequestHandler):
    root: Path
    base: str

    def _map_path(self) -> str | None:
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if not path.startswith(self.base):
            return None
        rel = path[len(self.base):].lstrip("/")
        if not rel:
            rel = "index.html"
        elif rel.endswith("/"):
            rel += "index.html"
        elif not Path(rel).suffix:
            html = self.root / f"{rel}.html"
            directory_index = self.root / rel / "index.html"
            if html.is_file():
                rel += ".html"
            elif directory_index.is_file():
                rel = f"{rel}/index.html"
        candidate = (self.root / rel).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        return "/" + quote(rel, safe="/@:+~!$&'()*,-._")

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        mapped = self._map_path()
        if mapped is None:
            self.send_error(404, "outside configured base path")
            return
        self.path = mapped
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib hook
        mapped = self._map_path()
        if mapped is None:
            self.send_error(404, "outside configured base path")
            return
        self.path = mapped
        super().do_HEAD()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a built VitePress tree with clean URL support.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--base", default="/")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    ns = parser.parse_args()

    root = Path(ns.root).resolve()
    if not (root / "index.html").is_file():
        raise SystemExit(f"SITE-SERVER-ROOT: missing {root / 'index.html'}")
    base = "/" + ns.base.strip("/") + "/" if ns.base.strip("/") else "/"

    class Handler(VitePressHandler):
        pass

    Handler.root = root
    Handler.base = base

    os.chdir(root)
    server = ThreadingHTTPServer((ns.host, ns.port), Handler)
    print(f"SITE_SERVER_ROOT={root}", flush=True)
    print(f"SITE_SERVER_BASE={base}", flush=True)
    print(f"SITE_SERVER_URL=http://{ns.host}:{ns.port}{base}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
