#!/usr/bin/env python3
"""
Hermes Animation Studio — Backend API
Drives Blender MCP + GitHub Actions cloud rendering from web dashboard.
"""

import os
import json
import time
import threading
import subprocess
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ─── Config ───
PORT = 8080
DASHBOARD_DIR = Path(__file__).parent
REPO_DIR = DASHBOARD_DIR.parent
GITHUB_REPO = "imishbahu-commits/manim-cloud"
GITHUB_TOKEN = None  # loaded from ~/.git-credentials

# Job tracking
jobs = {}

def load_github_token():
    """Load GitHub PAT from git credentials."""
    global GITHUB_TOKEN
    cred_file = Path.home() / ".git-credentials"
    if cred_file.exists():
        import re
        content = cred_file.read_text()
        match = re.search(r'ghp_[A-Za-z0-9]+', content)
        if match:
            GITHUB_TOKEN = match.group(0)
            return True
    return False

def trigger_workflow(prompt, style, duration, voice):
    """Trigger GitHub Actions workflow and return run ID."""
    # Prepare scene data as JSON
    scene_data = {
        "prompt": prompt,
        "style": style,
        "duration": int(duration),
        "voice": voice,
        "scenes": parse_prompt_to_scenes(prompt, style, duration),
    }
    
    # Write scene data to file and push to repo
    scene_file = REPO_DIR / "dashboard" / "current_scene.json"
    scene_file.write_text(json.dumps(scene_data, indent=2))
    
    # Git push the scene file
    subprocess.run(
        ["git", "add", "dashboard/current_scene.json"],
        cwd=str(REPO_DIR), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", f"Dashboard: new scene - {prompt[:50]}"],
        cwd=str(REPO_DIR), capture_output=True
    )
    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=str(REPO_DIR), capture_output=True
    )
    
    # Trigger the workflow
    workflow_file = "ai-animation.yml"
    if style in ("3d_realistic",):
        workflow_file = "blender-video.yml"
    elif style == "lottie":
        workflow_file = "ai-video.yml"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "ref": "main",
        "inputs": {
            "topic": prompt[:80],
        }
    }
    
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if resp.status_code == 204:
        return {"success": True, "message": "Workflow triggered"}
    else:
        return {"success": False, "error": f"GitHub API error: {resp.status_code}"}


def parse_prompt_to_scenes(prompt, style, duration):
    """Parse a text prompt into scene definitions."""
    # Simple heuristic: split by sentences, create one scene per sentence
    sentences = [s.strip() for s in prompt.replace('...', '.').split('.') if s.strip()]
    
    if not sentences:
        sentences = [prompt]
    
    # Target ~10 seconds per scene
    total_duration = int(duration)
    scene_duration = max(8, min(15, total_duration // max(len(sentences), 1)))
    num_scenes = max(1, total_duration // scene_duration)
    
    cameras = ["push-in", "pan-left", "dolly-in", "push-in-slow", "pan-right"]
    
    scenes = []
    for i in range(num_scenes):
        narration = sentences[i % len(sentences)] if sentences else f"Scene {i+1}"
        scenes.append({
            "scene": i + 1,
            "narration": narration,
            "prompt": prompt[:200],
            "camera": cameras[i % len(cameras)],
            "duration": scene_duration,
        })
    
    return scenes


def check_job_status(job_id):
    """Poll GitHub Actions run status."""
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "No GitHub token"}
    
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=1&event=workflow_dispatch",
        headers=headers,
        timeout=10
    )
    
    if resp.status_code == 200:
        runs = resp.json().get("workflow_runs", [])
        if runs:
            run = runs[0]
            return {
                "status": run["status"],
                "conclusion": run.get("conclusion", ""),
                "run_id": run["id"],
                "html_url": run["html_url"],
            }
    return {"status": "unknown"}


def download_artifact(run_id=None):
    """Download the latest artifact (video) from GitHub Actions."""
    if not GITHUB_TOKEN:
        return None
    
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/artifacts?per_page=5",
        headers=headers,
        timeout=15
    )
    
    if resp.status_code == 200:
        artifacts = resp.json().get("artifacts", [])
        for art in artifacts:
            if "video" in art["name"].lower() or "final" in art["name"].lower():
                # Download artifact
                dl_resp = requests.get(
                    f"https://api.github.com/repos/{GITHUB_REPO}/actions/artifacts/{art['id']}/zip",
                    headers=headers,
                    timeout=60
                )
                if dl_resp.status_code == 200:
                    # Save and extract
                    zip_path = Path("/tmp/artifact_download.zip")
                    zip_path.write_bytes(dl_resp.content)
                    import zipfile
                    with zipfile.ZipFile(zip_path) as z:
                        z.extractall("/tmp/artifact_download/")
                    
                    # Find mp4
                    for root, dirs, files in os.walk("/tmp/artifact_download/"):
                        for f in files:
                            if f.endswith(".mp4"):
                                return os.path.join(root, f)
    return None


class DashboardHandler(BaseHTTPRequestHandler):
    def serve_file(self, path, content_type):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/' or parsed.path == '/index.html':
            self.serve_file(DASHBOARD_DIR / "index.html", 'text/html')
        elif parsed.path.startswith('/api/status'):
            # Check job status
            status = check_job_status(0)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        elif parsed.path.startswith('/api/video/'):
            # Serve downloaded video
            video_path = f"/tmp/artifact_download/{parsed.path.split('/')[-1]}"
            if os.path.exists(video_path):
                self.serve_file(video_path, 'video/mp4')
            else:
                self.send_error(404)
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/generate':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            prompt = data.get('prompt', '')
            style = data.get('style', 'oversimplified')
            duration = data.get('duration', '30')
            voice = data.get('voice', 'en-US-ChristopherNeural')
            
            # Trigger the workflow
            result = trigger_workflow(prompt, style, duration, voice)
            
            if result["success"]:
                # Start background polling
                job_id = f"job_{int(time.time())}"
                jobs[job_id] = {"status": "running", "start_time": time.time()}
                
                def poll_job():
                    for _ in range(60):  # Poll for up to 30 min
                        time.sleep(30)
                        status = check_job_status(job_id)
                        if status.get("status") == "completed":
                            if status.get("conclusion") == "success":
                                video = download_artifact()
                                if video:
                                    jobs[job_id] = {
                                        "status": "complete",
                                        "video_path": video,
                                        "video_url": f"/api/video/{os.path.basename(video)}",
                                    }
                                else:
                                    jobs[job_id] = {"status": "error", "message": "No video found"}
                            else:
                                jobs[job_id] = {"status": "error", "message": "Build failed"}
                            return
                    
                    jobs[job_id] = {"status": "error", "message": "Timeout"}
                
                thread = threading.Thread(target=poll_job, daemon=True)
                thread.start()
                
                response = {
                    "success": True,
                    "job_id": job_id,
                    "message": "Animation generation started! Check progress below."
                }
            else:
                response = result
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed.path == '/api/poll':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            job_id = data.get('job_id', '')
            
            job = jobs.get(job_id, {"status": "unknown"})
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(job).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs


def main():
    print("=" * 50)
    print("  Hermes Animation Studio Dashboard")
    print("=" * 50)
    
    if load_github_token():
        print(f"  ✓ GitHub token loaded")
    else:
        print(f"  ⚠ No GitHub token found")
    
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f"\n  🚀 Dashboard running on port {PORT}")
    print(f"  📱 Open: http://localhost:{PORT}")
    print(f"\n  Waiting for prompts...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
