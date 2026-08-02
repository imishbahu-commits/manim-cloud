#!/usr/bin/env python3
"""
blender_drive.py — Drive Blender via MCP addon socket (localhost:9876).
Sends execute_code commands to build + render scenes.
"""

import socket, json, time, sys, os

HOST, PORT = "localhost", 9876
TIMEOUT = 120


def wait_for_addon(timeout=60):
    print(f"Waiting for Blender addon on {HOST}:{PORT}...")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((HOST, PORT))
            s.close()
            print(f"  Addon ready ({time.time()-t0:.1f}s)")
            return True
        except (ConnectionRefusedError, OSError):
            time.sleep(1)
    print("  TIMEOUT — addon never responded")
    return False


def send_command(cmd_type, params=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    s.connect((HOST, PORT))
    msg = json.dumps({"type": cmd_type, "params": params or {}})
    s.sendall(msg.encode())
    # Read response
    chunks = []
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            data = b"".join(chunks)
            resp = json.loads(data.decode())
            s.close()
            return resp
        except json.JSONDecodeError:
            continue
    s.close()
    return json.loads(b"".join(chunks).decode())


def execute(code):
    resp = send_command("execute_code", {"code": code})
    print(f"  execute_code → {resp.get('executed', '?')} | {resp.get('result', '')[:200]}")
    return resp


def main():
    if not wait_for_addon(60):
        sys.exit("Addon not ready")

    # Build scene via MCP socket
    scene_script = open("/home/runner/work/manim-cloud/manim-cloud/scripts/blender_scene.py").read()
    build_code = scene_script + "\n\nbuild_all()\n"
    print("\n=== BUILDING SCENE via MCP ===")
    resp = execute(build_code)

    # Render segments directly via headless blender (more reliable for long renders)
    print("\n=== RENDER DONE — scene saved, will render via headless blender ===")

    # Signal: scene is built, workflow continues with headless render
    print("MCP_BUILD_COMPLETE")


if __name__ == "__main__":
    main()
