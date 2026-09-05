import os
import shutil
import zipfile
import logging
from pathlib import Path
import httpx

logger = logging.getLogger("lenny_assistant.ingestion.downloader")

DEFAULT_REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts"
DEFAULT_ZIP_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts/archive/refs/heads/main.zip"


def fetch_transcript_repository(
    repo_url: str = DEFAULT_REPO_URL,
    data_dir: str = "data/transcripts",
    force: bool = False
) -> dict:
    """Obtains the official transcript repository via zip download or git clone.

    Returns a dict with 'status', 'path', and 'message'.
    """
    target_path = Path(data_dir).resolve()
    episodes_dir = target_path / "episodes"

    if episodes_dir.exists() and any(episodes_dir.iterdir()) and not force:
        logger.info(f"Reusing existing transcript repository at: {target_path}")
        return {
            "status": "reused",
            "path": target_path,
            "message": f"Reused existing transcript repository at {target_path}"
        }

    logger.info(f"Downloading transcript archive from: {DEFAULT_ZIP_URL}")
    target_path.mkdir(parents=True, exist_ok=True)
    zip_path = target_path / "repo.zip"

    try:
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            response = client.get(DEFAULT_ZIP_URL)
            response.raise_for_status()
            zip_path.write_bytes(response.content)

        logger.info(f"Extracting transcript archive to: {target_path}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        # Zip extracts to 'lennys-podcast-transcripts-main/'
        extracted_folder = target_path / "lennys-podcast-transcripts-main"
        if extracted_folder.exists():
            for item in extracted_folder.iterdir():
                dest = target_path / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            shutil.rmtree(extracted_folder)

        if zip_path.exists():
            zip_path.unlink()

        return {
            "status": "downloaded",
            "path": target_path,
            "message": f"Successfully downloaded and extracted repository to {target_path}"
        }

    except Exception as e:
        logger.error(f"Failed to download repository: {e}")
        raise RuntimeError(f"Could not obtain transcript repository from {repo_url}: {e}") from e
