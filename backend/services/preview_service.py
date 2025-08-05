import subprocess
import os
import time
from typing import Dict, Optional
from fastapi import HTTPException

# Store active preview processes to allow cleanup
active_processes = {}

def start_preview(project_id: str, file_paths: Dict[str, str]) -> str:
    """
    Start a temporary Node.js server for previewing the generated MERN project.

    Args:
        project_id (str): The ID of the project to preview.
        file_paths (Dict[str, str]): Dictionary of file paths for the generated project.

    Returns:
        str: The URL of the running preview server (e.g., http://localhost:4000).

    Raises:
        HTTPException: If the preview server fails to start.
    """
    # Assume the backend path (Express server) is in file_paths["backend"]
    project_dir = os.path.dirname(file_paths.get("backend", ""))
    if not project_dir or not os.path.exists(project_dir):
        raise HTTPException(status_code=400, detail="Invalid project directory")

    # Ensure node_modules is installed
    try:
        subprocess.run(
            ["npm.cmd", "install"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"npm install failed: {e.stderr}")

    # Start the Node server in the project directory
    try:
        process = subprocess.Popen(
            ["npm.cmd", "start"],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait briefly to ensure the server starts
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is not None:
            raise HTTPException(status_code=500, detail="Preview server failed to start")

        # Store the process for cleanup
        active_processes[project_id] = process

        # Assume MERN app runs on port 4000 (configurable in generated server.js)
        preview_url = "http://localhost:4000"
        return preview_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start preview: {str(e)}")

def stop_preview(project_id: str) -> None:
    """
    Stop the preview server for a given project.

    Args:
        project_id (str): The ID of the project whose preview server should be stopped.
    """
    process = active_processes.get(project_id)
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)  # Wait for graceful termination
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate
        finally:
            active_processes.pop(project_id, None)