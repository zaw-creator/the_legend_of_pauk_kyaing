"""Live bridge: run inside an open Blender window so Claude can edit the model while you watch.

Start Blender with:  Blender naga.blend --python live_bridge.py
It listens on 127.0.0.1 only and needs the token in the file live_bridge.token (same folder).
Close the Blender window, or send the word QUIT, to stop it.
"""
import io
import os
import queue
import socket
import threading
import traceback
from contextlib import redirect_stdout

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(HERE, "live_bridge.token")).read().strip()
PORT = int(os.environ.get("NAGA_BRIDGE_PORT", "9877"))
jobs = queue.Queue()
NS = {"__name__": "live", "bpy": bpy}


def run_job():
    """Runs on Blender's main thread: executes queued code and hands back its output."""
    while not jobs.empty():
        code, box = jobs.get()
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                exec(compile(code, "<live>", "exec"), NS)
            box.append(buf.getvalue() or "ok")
        except Exception:
            box.append(buf.getvalue() + traceback.format_exc())
    return 0.05


def serve():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", PORT))
    srv.listen(4)
    while True:
        conn, _ = srv.accept()
        with conn:
            data = b""
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
                if data.endswith(b"\n<<END>>"):
                    break
            text = data.decode("utf-8")
            first, _, body = text.partition("\n")
            if first.strip() != TOKEN:
                conn.sendall(b"denied")
                continue
            body = body[: -len("\n<<END>>")] if body.endswith("\n<<END>>") else body
            if body.strip() == "QUIT":
                conn.sendall(b"bye")
                bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender(), first_interval=0.1)
                return
            box = []
            jobs.put((body, box))
            for _ in range(6000):
                if box:
                    break
                threading.Event().wait(0.05)
            conn.sendall((box[0] if box else "timeout").encode("utf-8"))


bpy.app.timers.register(run_job, persistent=True)
threading.Thread(target=serve, daemon=True).start()
print("Live bridge listening on 127.0.0.1:%d" % PORT)
