from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB client setup
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/webgenai"))
db = client["webgenai"]
projects_collection = db["projects"]

def create_project(description: str, file_paths: Dict[str, str]) -> str:
    """
    Store a new project in MongoDB and return its ID.
    
    Args:
        description (str): User-provided description of the project.
        file_paths (Dict[str, str]): Dictionary of generated file paths.
    
    Returns:
        str: The ID of the created project.
    """
    project_data = {
        "description": description,
        "file_paths": file_paths,
        "created_at": datetime.now()
    }
    result = projects_collection.insert_one(project_data)
    return str(result.inserted_id)

def get_project(project_id: str) -> Optional[Dict]:
    """
    Retrieve a project by its ID from MongoDB.
    
    Args:
        project_id (str): The ID of the project to retrieve.
    
    Returns:
        Optional[Dict]: The project data if found, else None.
    """
    try:
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if project:
            # Convert ObjectId to string for JSON compatibility
            project["id"] = str(project["_id"])
            del project["_id"]
            return project
        return None
    except Exception:
        return None