import os
import base64
from crewai.tools import tool  # Correct import for @tool decorator

@tool("read_file")
def read_file(path: str) -> str:
    """
    Read file content. Path required. Returns base64 for images.
    If the file does not exist, returns 'File not found'.
    Handles text files with UTF-8 encoding; treats images as base64.
    """
    # Normalize path separators and resolve absolute path
    path = os.path.normpath(path.replace("\\", "/"))
    
    # If path is not absolute, make it relative to current working directory
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    print(f"DEBUG read_file: Attempting to read '{path}'")
    
    if not os.path.exists(path):
        print(f"DEBUG read_file: File not found at '{path}'")
        return "File not found"
    
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        try:
            with open(path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
                print(f"DEBUG read_file: Successfully read image file, size: {len(content)} chars")
                return content
        except Exception as e:
            print(f"DEBUG read_file: Error reading image file: {e}")
            return f"Error reading image file: {e}"
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"DEBUG read_file: Successfully read text file, size: {len(content)} chars")
                return content
        except UnicodeDecodeError as e:
            print(f"DEBUG read_file: Unicode decode error: {e}")
            return f"File encoding error - treat as binary: {e}"
        except Exception as e:
            print(f"DEBUG read_file: Error reading text file: {e}")
            return f"Error reading file: {e}"

@tool("write_file")
def write_file(path: str, content: str) -> str:
    """
    Write content to file. Path and content required. For images, content must be base64.
    Creates directories if needed. Returns success message or error.
    Debug: Logs the received path for troubleshooting.
    """
    try:
        # Normalize path separators
        path = os.path.normpath(path.replace("\\", "/"))
        
        # Sanitize path: Strip any extra quotes the LLM might add
        path = path.strip().strip('"').strip("'")
        
        # If path is not absolute, make it relative to current working directory
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        print(f"DEBUG write_file: Sanitized path: '{path}', content length: {len(content)}")
        
        if not path or path.strip() == "":
            return "Error: Empty path provided"
            
        # Ensure directory exists
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
            print(f"DEBUG write_file: Created directory: {dir_path}")
        
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            try:
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(content))
                print(f"DEBUG write_file: Successfully wrote image to {path}")
                return f"Image written to {path}"
            except Exception as e:
                print(f"DEBUG write_file: Base64 decode error: {e}")
                return f"Base64 decode error: {e}"
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"DEBUG write_file: Successfully wrote text file to {path}")
            return f"File written to {path}"
    except Exception as e:
        print(f"DEBUG write_file: Error writing file: {e}")
        return f"Error writing file: {e}"

@tool("list_files")
def list_files(directory: str = ".") -> str:
    """
    List files in a directory. Directory optional (defaults to current).
    Returns newline-separated filenames or 'Directory not found'.
    """
    # Normalize path separators
    directory = os.path.normpath(directory.replace("\\", "/"))
    
    # If path is not absolute, make it relative to current working directory
    if not os.path.isabs(directory):
        directory = os.path.abspath(directory)
    
    print(f"DEBUG list_files: Listing directory '{directory}'")
    
    if not os.path.exists(directory):
        print(f"DEBUG list_files: Directory not found at '{directory}'")
        return "Directory not found"
    
    try:
        files = os.listdir(directory)
        print(f"DEBUG list_files: Found {len(files)} items: {files}")
        return "\n".join(files)
    except Exception as e:
        print(f"DEBUG list_files: Error listing directory: {e}")
        return f"Error listing directory: {e}"