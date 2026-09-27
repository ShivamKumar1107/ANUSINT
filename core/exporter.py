import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def export_to_json(username: str, data: Dict[str, Any], output_dir: str = "reports") -> str:
    """Saves profile or analysis data to a formatted JSON file."""
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_report_{timestamp}.json"
    filepath = Path(output_dir) / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    return str(filepath)