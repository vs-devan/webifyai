import os
import base64

def collect_files(temp_dir: str) -> dict:
    """
    Collect all files from the temporary directory, excluding plan.txt and issues.txt.
    Returns a dictionary with relative paths as keys and file contents as values.
    For images, content is base64 encoded.
    """
    files = {}
    temp_dir = os.path.abspath(temp_dir)  # Ensure absolute path
    
    print(f"DEBUG collect_files: Collecting from {temp_dir}")
    
    if not os.path.exists(temp_dir):
        print(f"DEBUG collect_files: Directory {temp_dir} does not exist")
        return files
    
    try:
        for root, _, fnames in os.walk(temp_dir):
            for fname in fnames:
                # Skip plan and issues files
                if fname in ['plan.txt', 'issues.txt']:
                    continue
                
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, temp_dir)
                
                # Normalize path separators for consistency
                rel_path = rel_path.replace('\\', '/')
                
                print(f"DEBUG collect_files: Processing {rel_path}")
                
                ext = os.path.splitext(fname)[1].lower()
                try:
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        # Handle image files as base64
                        with open(full_path, 'rb') as f:
                            files[rel_path] = base64.b64encode(f.read()).decode('utf-8')
                        print(f"DEBUG collect_files: Added image {rel_path}")
                    else:
                        # Handle text files
                        with open(full_path, 'r', encoding='utf-8') as f:
                            files[rel_path] = f.read()
                        print(f"DEBUG collect_files: Added text file {rel_path}")
                except Exception as e:
                    print(f"DEBUG collect_files: Error reading {rel_path}: {e}")
                    files[rel_path] = f"Error reading file: {e}"
    
    except Exception as e:
        print(f"DEBUG collect_files: Error walking directory {temp_dir}: {e}")
    
    print(f"DEBUG collect_files: Collected {len(files)} files")
    return files