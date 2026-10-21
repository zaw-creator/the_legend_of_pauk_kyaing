"""Send a Python file (or a string with -c) to the open Blender window and print what it returns.

    python3 bridge_send.py step.py
    python3 bridge_send.py -c "print(len(bpy.data.objects))"
"""
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(HERE, "live_bridge.token")).read().strip()
PORT = int(os.environ.get("NAGA_BRIDGE_PORT", "9877"))

if len(sys.argv) >= 3 and sys.argv[1] == "-c":
    code = sys.argv[2]
else:
    code = open(sys.argv[1], encoding="utf-8").read()

with socket.create_connection(("127.0.0.1", PORT), timeout=300) as s:
    s.sendall((TOKEN + "\n" + code + "\n<<END>>").encode("utf-8"))
    out = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        out += chunk
print(out.decode("utf-8"))
