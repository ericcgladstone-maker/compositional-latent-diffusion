"""Live viewer backend.

A thin FastAPI layer over the canonical World. The browser never reimplements
the model -- it sends commands and renders the frames this server streams from
the same engine the sweep uses. There is therefore no second model to drift.

Protocol (JSON over one WebSocket at /ws):

  client -> server
    {type:"build",     config:{...}}           build a fresh world from a config
    {type:"build_phase", phase:"V1", overrides:{...}}  build from a phase preset
    {type:"run",       fps:20, max_ticks:1000} start the stepping loop
    {type:"pause"}                              pause stepping
    {type:"step"}                               advance one tick
    {type:"reset"}                              rebuild with the current config
    {type:"set_param", name:"capacity", value:6}  live hot-tweak (Schelling knob)
    {type:"sweep",     phases:[...], replications:30, with_invariants:false}

  server -> client
    {type:"built", ...network/config/bigthings..., frame:{...}}
    {type:"frame", t, metrics, agents}
    {type:"status", running, t, reason}
    {type:"sweep_progress", done, total, message}
    {type:"sweep_done", outdir}
    {type:"error", message}
"""

import asyncio
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config as C
from . import phases as P
from .model import World

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER_DIR = os.path.join(os.path.dirname(HERE), "viewer")

app = FastAPI(title="Latent Adoption ABM viewer")


@app.get("/registry")
def registry():
    return JSONResponse(C.registry_payload())


@app.get("/phases")
def phases():
    return JSONResponse(P.phase_list_payload())


@app.get("/")
def index():
    with open(os.path.join(VIEWER_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


# static assets (app.js, style.css)
app.mount("/static", StaticFiles(directory=VIEWER_DIR), name="static")


class Session:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.world: Optional[World] = None
        self.running = False
        self.run_task: Optional[asyncio.Task] = None
        self.outbox: asyncio.Queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()

    # --- outbound ---------------------------------------------------------
    async def sender_loop(self):
        while True:
            msg = await self.outbox.get()
            if msg is None:
                break
            await self.ws.send_json(msg)

    def send(self, msg: dict):
        self.outbox.put_nowait(msg)

    # --- world lifecycle --------------------------------------------------
    def _build_world(self, cfg: dict):
        self.running = False
        self.world = World(cfg)
        positions = self.world.positions()
        self.send({
            "type": "built",
            "config": self.world.cfg,
            "n_agents": self.world.n,
            "n_element_types": self.world.n_element_types,
            "big_things": [{"bid": b.bid, "label": b.label, "required": list(b.required)}
                           for b in self.world.big_things],
            "edges": self.world.edges(),
            "positions": positions,
            "frame": self._frame_payload(),
        })

    def _frame_payload(self) -> dict:
        return {
            "type": "frame",
            "t": self.world.t,
            "metrics": self.world.history[-1],
            "agents": self.world.agent_states(),
        }

    # --- stepping loop ----------------------------------------------------
    async def run_loop(self, fps: int, max_ticks: int):
        self.running = True
        delay = 1.0 / max(1, fps)
        start_t = self.world.t
        while self.running and (self.world.t - start_t) < max_ticks:
            self.world.step()
            self.send(self._frame_payload())
            if self.world.quiescent():
                self.running = False
                self.send({"type": "status", "running": False, "t": self.world.t,
                           "reason": "quiescent"})
                return
            await asyncio.sleep(delay)
        self.running = False
        self.send({"type": "status", "running": False, "t": self.world.t,
                   "reason": "stopped"})

    # --- sweep ------------------------------------------------------------
    async def run_sweep(self, phase_ids, replications, with_invariants):
        from . import sweep as S

        def progress(done, total, message):
            # called from worker thread -> hop back to the loop
            self.loop.call_soon_threadsafe(
                self.outbox.put_nowait,
                {"type": "sweep_progress", "done": done, "total": total,
                 "message": message})

        def work():
            return S.run_sweep(phase_ids, replications=replications,
                               with_invariants=with_invariants, progress=progress,
                               tag="viewer")

        outdir = await self.loop.run_in_executor(None, work)
        self.send({"type": "sweep_done", "outdir": outdir})

    # --- command dispatch -------------------------------------------------
    async def handle(self, msg: dict):
        t = msg.get("type")
        try:
            if t == "build":
                cfg = C.validate_config(msg.get("config", {}))
                self._build_world(cfg)
            elif t == "build_phase":
                cfg = P.config_for_phase(msg["phase"], msg.get("overrides"))
                self._build_world(cfg)
            elif t == "run":
                if self.world is None:
                    self.send({"type": "error", "message": "build a world first"})
                    return
                if self.run_task and not self.run_task.done():
                    self.running = False
                    await self.run_task
                self.run_task = asyncio.create_task(
                    self.run_loop(int(msg.get("fps", 20)),
                                  int(msg.get("max_ticks", self.world.cfg["run_length"]))))
            elif t == "pause":
                self.running = False
            elif t == "step":
                if self.world is None:
                    return
                self.world.step()
                self.send(self._frame_payload())
            elif t == "reset":
                if self.world is not None:
                    self._build_world(self.world.cfg)
            elif t == "set_param":
                if self.world is None:
                    return
                name, value = msg["name"], msg["value"]
                self.world.cfg = C.validate_config({**self.world.cfg, name: value})
                # keep derived state consistent for hot tweaks
                self.world.chunk_cost = 2 if self.world.cfg["differential_slot_cost"] else 1
                self.send({"type": "status", "running": self.running,
                           "t": self.world.t, "reason": f"set {name}={value}"})
            elif t == "sweep":
                phase_ids = msg.get("phases") or [p["id"] for p in P.PHASES]
                await self.run_sweep(
                    phase_ids,
                    int(msg.get("replications", C.PARAM_INDEX["replications"].default)),
                    bool(msg.get("with_invariants", False)))
            else:
                self.send({"type": "error", "message": f"unknown command {t!r}"})
        except Exception as exc:  # surface model errors to the UI, don't crash the socket
            self.send({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    async def receive_loop(self):
        while True:
            msg = await self.ws.receive_json()
            await self.handle(msg)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    session = Session(ws)
    sender = asyncio.create_task(session.sender_loop())
    try:
        await session.receive_loop()
    except WebSocketDisconnect:
        pass
    finally:
        session.running = False
        session.outbox.put_nowait(None)
        sender.cancel()


def serve(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning")
