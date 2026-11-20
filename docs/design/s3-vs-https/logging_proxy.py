"""A tiny logging reverse proxy, to see what Icechunk's HTTP and S3 clients actually send.

    python logging_proxy.py UPSTREAM PORT LOGFILE
    e.g. python logging_proxy.py https://data.source.coop 8765 requests.jsonl

Each request is forwarded to UPSTREAM (path and query unchanged, Host rewritten) and one JSON line
is written per request: method, path, query, request headers, status, response size, upstream
server-timing, time to first byte and total time. Bodies are streamed, not stored. Local testing only.
"""
import asyncio
import json
import sys
import time

import aiohttp
from aiohttp import web

UPSTREAM, PORT, LOG = sys.argv[1].rstrip("/"), int(sys.argv[2]), sys.argv[3]
HOP = {"host", "connection", "keep-alive", "transfer-encoding", "te", "upgrade",
       "proxy-connection", "content-length"}
# Keep Content-Length on responses: Icechunk's clients refuse a chunked response without it.
RESP_HOP = HOP - {"content-length"}


async def handle(request, session, log):
    t0 = time.perf_counter()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}
    body = await request.read()
    url = UPSTREAM + request.rel_url.path_qs
    async with session.request(request.method, url, headers=headers, data=body or None,
                               allow_redirects=False, auto_decompress=False) as up:
        ttfb = time.perf_counter() - t0
        resp = web.StreamResponse(status=up.status, headers={
            k: v for k, v in up.headers.items() if k.lower() not in RESP_HOP})
        await resp.prepare(request)
        n = 0
        async for chunk in up.content.iter_chunked(1 << 16):
            n += len(chunk)
            await resp.write(chunk)
        await resp.write_eof()
        log.write(json.dumps({
            "t": round(t0, 4), "method": request.method, "path": request.path,
            "query": request.query_string, "req_headers": dict(request.headers),
            "status": up.status, "bytes": n, "server_timing": up.headers.get("server-timing"),
            "cf_cache": up.headers.get("cf-cache-status"),
            "ttfb_s": round(ttfb, 4), "total_s": round(time.perf_counter() - t0, 4)}) + "\n")
        log.flush()
        return resp


async def main():
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=256))
    log = open(LOG, "a")
    app = web.Application(client_max_size=1 << 30)
    app.router.add_route("*", "/{tail:.*}", lambda r: handle(r, session, log))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", PORT).start()
    print(f"proxying http://127.0.0.1:{PORT} -> {UPSTREAM}, log {LOG}", flush=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
