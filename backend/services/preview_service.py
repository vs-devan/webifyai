# backend/services/preview_service.py
import subprocess
import os
import time
from typing import Dict, Optional
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

active_processes = {}

def start_preview(project_id: str, file_paths: Dict[str, str]) -> str:
    logger.info(f"Starting preview for project {project_id}")
    project_dir = os.path.dirname(file_paths.get("backend", ""))
    logger.info(f"Project directory: {project_dir}")
    if not project_dir or not os.path.exists(project_dir):
        logger.error(f"Invalid project directory: {project_dir}")
        raise HTTPException(status_code=400, detail=f"Invalid project directory: {project_dir}")

    logger.info("Running npm install")
    try:
        result = subprocess.run(
            ["npm.cmd", "install"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"npm install output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"npm install failed: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"npm install failed: {e.stderr}")

    logger.info("Starting Node server")
    try:
        process = subprocess.Popen(
            ["npm.cmd", "start"],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2)
        if process.poll() is not None:
            error_output = process.stderr.read() if process.stderr else "Unknown error"
            logger.error(f"Preview server failed: {error_output}")
            raise HTTPException(status_code=500, detail=f"Preview server failed: {error_output}")

        active_processes[project_id] = process
        preview_url = "http://localhost:4000"
        logger.info(f"Preview started at {preview_url}")
        return preview_url
    except Exception as e:
        logger.error(f"Failed to start preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start preview: {str(e)}")

def stop_preview(project_id: str) -> None:
    process = active_processes.get(project_id)
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
            logger.info(f"Preview stopped for project {project_id}")
        except subprocess.TimeoutExpired:
            process.kill()
            logger.warning(f"Force killed preview for project {project_id}")
        finally:
            active_processes.pop(project_id, None)