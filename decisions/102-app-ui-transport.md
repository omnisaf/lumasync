# 102 — The web UI is one static page plus one WebSocket, on one port (8765)

- **Status:** proposed — prototype default, team to confirm
- **Module:** whole team (app runner and `lumasync/web/index.html`; not a module)
- **Decided by:** first prototype build · **Date:** 2026-11-08

## Context

The page must show live values 30 times a second (fixture colours, meters, latency) and send control
changes back instantly. It must install cleanly on Python 3.14 on a Mac the day before a demo.

## Options considered

1. **Polling over plain HTTP** (the page asks "what's new?" many times a second). No extra library.
   Wasteful, and each request adds delay.
2. **WebSocket** (a connection that stays open so both sides can send messages at any time) using
   the small `websockets` library. One dependency, pure Python, installs everywhere.
3. **A web framework** (aiohttp, FastAPI). More features, more to install and learn; some need
   compiled parts that may lag behind new Python versions.

## What the prototype does and why

Option 2. One port serves both the page (plain GET `/`) and the WebSocket (`/ws`). On connect, the
server sends a `hello` message (library, devices, patch, looks); then a `state` message 30 times a
second; the page sends small `{"cmd": ...}` messages. `/api/state` returns one snapshot as JSON for
scripts and tests. Measured: about 27 state messages per second reach a client.

The page is a single HTML file with no build step and no external scripts, so it works offline in a
venue.

## What would change our mind / how to test it

- If several browsers (say a phone and a laptop) make the engine late (`tick max` rises), slow the
  state rate or send only changed fields.
- If the team wants phones on the venue Wi-Fi to control the show, run with `--host 0.0.0.0` and add
  a simple password first.

## Open questions for the team

- Does the UI need to work without the laptop screen (phone as remote)? That changes security needs.

## Owner's reasoning (when confirmed)

> (to be written by whoever confirms or replaces this, in their own words)
