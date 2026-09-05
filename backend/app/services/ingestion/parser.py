import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple


SPEAKER_TIMESTAMP_PATTERN = re.compile(
    r'^(?:[#*]*\s*)?(.*?)\s*\((?:(\d{1,2}:\d{2}:\d{2})|(\d{1,2}:\d{2}))\):\s*(.*)$'
)
TIMESTAMP_ONLY_PATTERN = re.compile(
    r'^\((?:(\d{1,2}:\d{2}:\d{2})|(\d{1,2}:\d{2}))\):\s*(.*)$'
)


def parse_transcript_file(file_path: Path) -> Dict[str, Any]:
    """Parses a transcript markdown file into structured metadata and dialogue blocks.

    Returns dict with 'metadata' and 'dialogue_blocks'.
    """
    content = file_path.read_text(encoding="utf-8")

    metadata: Dict[str, Any] = {}
    body = content

    # Split YAML frontmatter if present
    parts = content.split("---")
    if len(parts) >= 3 and parts[0].strip() == "":
        try:
            metadata = yaml.safe_load(parts[1]) or {}
            body = "---".join(parts[2:])
        except Exception:
            metadata = {}

    # Extract guest name from parent folder name if missing in frontmatter
    guest_name = metadata.get("guest") or file_path.parent.name.replace("-", " ").title()
    title = metadata.get("title") or f"{guest_name} Interview"

    metadata["guest"] = str(guest_name).strip()
    metadata["title"] = str(title).strip()
    metadata["youtube_url"] = str(metadata.get("youtube_url") or "")
    metadata["publish_date"] = str(metadata.get("publish_date") or "")

    # Parse dialogue blocks
    dialogue_blocks: List[Dict[str, str]] = []
    current_speaker = guest_name
    current_timestamp = "00:00:00"
    current_text_lines: List[str] = []

    lines = body.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        spk_match = SPEAKER_TIMESTAMP_PATTERN.match(stripped)
        ts_match = TIMESTAMP_ONLY_PATTERN.match(stripped)

        if spk_match:
            # Save previous dialogue block
            if current_text_lines:
                dialogue_blocks.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "text": " ".join(current_text_lines).strip()
                })
                current_text_lines = []

            spk_name = spk_match.group(1).strip()
            ts_val = spk_match.group(2) or spk_match.group(3)
            dialogue_text = spk_match.group(4).strip()

            if spk_name:
                current_speaker = spk_name
            if ts_val:
                current_timestamp = ts_val
            if dialogue_text:
                current_text_lines.append(dialogue_text)

        elif ts_match:
            if current_text_lines:
                dialogue_blocks.append({
                    "speaker": current_speaker,
                    "timestamp": current_timestamp,
                    "text": " ".join(current_text_lines).strip()
                })
                current_text_lines = []

            ts_val = ts_match.group(1) or ts_match.group(2)
            dialogue_text = ts_match.group(3).strip()

            if ts_val:
                current_timestamp = ts_val
            if dialogue_text:
                current_text_lines.append(dialogue_text)
        else:
            current_text_lines.append(stripped)

    # Append trailing dialogue block
    if current_text_lines:
        dialogue_blocks.append({
            "speaker": current_speaker,
            "timestamp": current_timestamp,
            "text": " ".join(current_text_lines).strip()
        })

    return {
        "metadata": metadata,
        "dialogue_blocks": dialogue_blocks
    }
