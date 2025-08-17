import re
from typing import Dict, List, Any

def validate_description(description: str) -> Dict[str, Any]:
    """Validate user input description."""
    errors = []
    warnings = []
    
    if not description or not description.strip():
        errors.append("Description cannot be empty")
    elif len(description.strip()) < 20:
        errors.append("Description too short (minimum 20 characters)")
    elif len(description) > 5000:
        warnings.append("Very long description may impact performance")
    
    # Check for minimum requirements
    required_keywords = ['react', 'express', 'mongodb', 'node']
    missing_keywords = [kw for kw in required_keywords 
                       if kw not in description.lower()]
    
    if missing_keywords:
        warnings.append(f"Description may be missing MERN stack components: {missing_keywords}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def validate_generated_files(files_dict: Dict[str, str]) -> Dict[str, Any]:
    """Validate generated file structure and content."""
    errors = []
    warnings = []
    
    # Check minimum required files
    required_files = [
        'package.json',
        'server.js',
        ('src/App.js', 'client/src/App.js', 'frontend/src/App.js')
    ]
    
    for req_file in required_files:
        if isinstance(req_file, tuple):
            if not any(f in files_dict for f in req_file):
                errors.append(f"Missing React App component (expected one of: {req_file})")
        elif req_file not in files_dict:
            errors.append(f"Missing required file: {req_file}")
    
    # Validate package.json if present
    if 'package.json' in files_dict:
        try:
            import json
            package_data = json.loads(files_dict['package.json'])
            if 'dependencies' not in package_data:
                warnings.append("package.json missing dependencies section")
        except json.JSONDecodeError:
            errors.append("Invalid JSON in package.json")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors, 
        "warnings": warnings
    }