import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def collect_files(temp_dir: str, exclude_files: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Enhanced file collection with better error handling and filtering.
    
    Args:
        temp_dir: Directory to collect files from
        exclude_files: List of files to exclude (defaults to plan.txt, issues.txt)
    
    Returns:
        Dictionary mapping relative paths to file contents
    """
    if exclude_files is None:
        exclude_files = ['plan.txt', 'issues.txt', 'generation.log']
    
    files = {}
    temp_path = Path(temp_dir)
    
    if not temp_path.exists():
        logger.error(f"Directory does not exist: {temp_path}")
        return files
    
    try:
        for root, dirs, filenames in os.walk(temp_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
            
            for filename in filenames:
                # Skip excluded files and hidden files
                if filename in exclude_files or filename.startswith('.'):
                    continue
                
                full_path = Path(root) / filename
                try:
                    rel_path = full_path.relative_to(temp_path)
                    
                    # Handle different file types
                    if _is_image_file(filename):
                        content = _read_image_file(full_path)
                    else:
                        content = _read_text_file(full_path)
                    
                    if content is not None:
                        files[str(rel_path).replace('\\', '/')] = content
                        
                except Exception as e:
                    logger.warning(f"Failed to process file {full_path}: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error collecting files from {temp_dir}: {e}")
    
    logger.info(f"Collected {len(files)} files from {temp_dir}")
    return files

def _is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
    return Path(filename).suffix.lower() in image_extensions

def _read_image_file(filepath: Path) -> Optional[str]:
    """Read image file and return base64 encoded content."""
    try:
        with open(filepath, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            ext = filepath.suffix.lower().lstrip('.')
            return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        logger.error(f"Failed to read image {filepath}: {e}")
        return None

def _read_text_file(filepath: Path, encodings: List[str] = None) -> Optional[str]:
    """Read text file with multiple encoding attempts."""
    if encodings is None:
        encodings = ['utf-8', 'utf-16', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
                # Basic check for binary content
                if '\x00' in content:
                    logger.warning(f"File {filepath} appears to contain binary data")
                    return None
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            logger.error(f"Error reading {filepath} with {encoding}: {e}")
            return None
    
    logger.error(f"Could not read {filepath} with any supported encoding")
    return None

def create_file_manifest(files_dict: Dict[str, str], output_path: Optional[str] = None) -> Dict:
    """Create a manifest of generated files with metadata."""
    manifest = {
        "generated_at": str(Path().cwd()),
        "total_files": len(files_dict),
        "files": {}
    }
    
    for filepath, content in files_dict.items():
        file_info = {
            "size_bytes": len(content.encode('utf-8')) if isinstance(content, str) else len(content),
            "lines": content.count('\n') + 1 if isinstance(content, str) else 0,
            "type": _classify_file_type(filepath),
            "is_image": _is_image_file(filepath)
        }
        manifest["files"][filepath] = file_info
    
    # Calculate totals
    manifest["total_size_bytes"] = sum(f["size_bytes"] for f in manifest["files"].values())
    manifest["total_lines"] = sum(f["lines"] for f in manifest["files"].values())
    
    # Save manifest if path provided
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"File manifest saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save manifest to {output_path}: {e}")
    
    return manifest

def _classify_file_type(filepath: str) -> str:
    """Classify file type based on path and extension."""
    path = Path(filepath)
    ext = path.suffix.lower()
    
    # Configuration files
    if path.name in ['package.json', '.env', '.env.example', 'vercel.json', 'docker-compose.yml']:
        return 'configuration'
    
    # Documentation
    if ext in ['.md', '.txt'] or 'readme' in path.name.lower():
        return 'documentation'
    
    # Frontend files
    if ext in ['.js', '.jsx', '.ts', '.tsx'] and any(part in str(path) for part in ['src', 'components', 'pages', 'hooks']):
        return 'frontend'
    
    # Backend files
    if ext in ['.js', '.ts'] and any(part in str(path) for part in ['server', 'routes', 'models', 'middleware', 'controllers']):
        return 'backend'
    
    # Styles
    if ext in ['.css', '.scss', '.sass', '.less']:
        return 'styles'
    
    # Static assets
    if ext in ['.html', '.htm']:
        return 'template'
    
    if _is_image_file(path.name):
        return 'image'
    
    return 'other'

def validate_file_structure(files_dict: Dict[str, str]) -> Dict[str, List[str]]:
    """Validate the generated file structure for common issues."""
    issues = {
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check for required files
    required_files = ['package.json']
    for req_file in required_files:
        if not any(req_file in path for path in files_dict.keys()):
            issues["errors"].append(f"Missing required file: {req_file}")
    
    # Check for React app structure
    react_indicators = ['App.js', 'App.jsx', 'index.js', 'index.jsx']
    if not any(indicator in ''.join(files_dict.keys()) for indicator in react_indicators):
        issues["warnings"].append("No obvious React entry point found")
    
    # Check for Express server
    server_indicators = ['server.js', 'app.js', 'index.js']
    has_server = any(
        indicator in path and any(backend_term in files_dict[path].lower() 
                                for backend_term in ['express', 'app.listen', 'server'])
        for path in files_dict.keys() 
        for indicator in server_indicators
    )
    
    if not has_server:
        issues["warnings"].append("No obvious Express server file found")
    
    # Check package.json validity
    package_files = [path for path in files_dict.keys() if 'package.json' in path]
    for pkg_file in package_files:
        try:
            pkg_data = json.loads(files_dict[pkg_file])
            if 'name' not in pkg_data:
                issues["warnings"].append(f"package.json missing 'name' field: {pkg_file}")
            if 'dependencies' not in pkg_data and 'devDependencies' not in pkg_data:
                issues["warnings"].append(f"package.json has no dependencies: {pkg_file}")
        except json.JSONDecodeError:
            issues["errors"].append(f"Invalid JSON in package.json: {pkg_file}")
    
    # File size checks
    for filepath, content in files_dict.items():
        size = len(content.encode('utf-8')) if isinstance(content, str) else len(content)
        if size == 0:
            issues["errors"].append(f"Empty file: {filepath}")
        elif size < 10:  # Very small files might be incomplete
            issues["warnings"].append(f"Very small file (might be incomplete): {filepath}")
        elif size > 1024 * 1024:  # Files over 1MB
            issues["warnings"].append(f"Large file detected: {filepath} ({size:,} bytes)")
    
    # Security checks
    security_patterns = {
        'hardcoded_secrets': [r'password.*=.*["\'][^"\']{8,}["\']', r'api[_-]?key.*=.*["\'][^"\']+["\']'],
        'sql_injection_risk': [r'SELECT.*\+.*', r'query.*\+.*'],
        'xss_risk': [r'innerHTML.*=.*[^)]+\)', r'dangerouslySetInnerHTML']
    }
    
    import re
    for filepath, content in files_dict.items():
        if isinstance(content, str):
            for risk_type, patterns in security_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues["warnings"].append(f"Potential {risk_type} in {filepath}")
                        break
    
    return issues