import os
import requests
from typing import Optional
from urllib.parse import urlparse
from app.core.config import settings

def download_file(url: str, task_id: str) -> Optional[str]:
    """
    Download a file from URL and save it to the storage directory.
    Returns the local file path if successful, None otherwise.
    """
    try:
        # Create task directory if it doesn't exist
        task_dir = os.path.join(settings.STORAGE_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # Get file name from URL
        file_name = os.path.basename(urlparse(url).path)
        if not file_name:
            file_name = f"file_{hash(url)}.mp4"

        local_path = os.path.join(task_dir, file_name)

        # Download file in chunks
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return local_path

    except Exception as e:
        print(f"Error downloading file from {url}: {str(e)}")
        return None 