import hashlib
from typing import Dict, Any, List

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except Exception:
    def count_tokens(text: str) -> int:
        # Fallback word-ratio approximation (~1.3 tokens per word)
        return int(len(text.split()) * 1.3)


def chunk_transcript(
    parsed_transcript: Dict[str, Any],
    min_tokens: int = 500,
    max_tokens: int = 800,
    overlap_tokens: int = 100
) -> List[Dict[str, Any]]:
    """Chunks transcript dialogue blocks into token-bounded windows with overlap.

    Returns list of dict payloads ready for TranscriptChunk ORM insertion.
    """
    metadata = parsed_transcript.get("metadata", {})
    dialogue_blocks = parsed_transcript.get("dialogue_blocks", [])

    guest = metadata.get("guest", "Unknown Guest")
    episode_title = metadata.get("title", "Lenny's Podcast")
    publish_date = metadata.get("publish_date", "")
    source_url = metadata.get("youtube_url", "")

    if not dialogue_blocks:
        return []

    chunks: List[Dict[str, Any]] = []
    
    current_tokens = 0
    current_blocks: List[Dict[str, str]] = []
    
    for block in dialogue_blocks:
        block_text = f"{block['speaker']} ({block['timestamp']}): {block['text']}"
        block_tokens = count_tokens(block_text)

        if current_tokens + block_tokens > max_tokens and current_blocks:
            # Package current chunk
            chunk_text = "\n\n".join([f"{b['speaker']} ({b['timestamp']}): {b['text']}" for b in current_blocks])
            first_block = current_blocks[0]
            
            chunk_hash = hashlib.sha256(
                f"{episode_title}:{guest}:{first_block['timestamp']}:{first_block['speaker']}:{chunk_text}".encode("utf-8")
            ).hexdigest()

            chunks.append({
                "chunk_hash": chunk_hash,
                "guest": guest,
                "episode_title": episode_title,
                "publish_date": publish_date,
                "timestamp": first_block["timestamp"],
                "speaker": first_block["speaker"],
                "chunk_text": chunk_text,
                "source_url": source_url,
            })

            # Calculate overlap blocks
            overlap_accumulated = 0
            new_blocks = []
            for b in reversed(current_blocks):
                bt = count_tokens(f"{b['speaker']} ({b['timestamp']}): {b['text']}")
                if overlap_accumulated + bt <= overlap_tokens:
                    new_blocks.insert(0, b)
                    overlap_accumulated += bt
                else:
                    break

            current_blocks = new_blocks
            current_tokens = sum([count_tokens(f"{b['speaker']} ({b['timestamp']}): {b['text']}") for b in current_blocks])

        current_blocks.append(block)
        current_tokens += block_tokens

    # Append remaining blocks as final chunk
    if current_blocks:
        chunk_text = "\n\n".join([f"{b['speaker']} ({b['timestamp']}): {b['text']}" for b in current_blocks])
        first_block = current_blocks[0]
        
        chunk_hash = hashlib.sha256(
            f"{episode_title}:{guest}:{first_block['timestamp']}:{first_block['speaker']}:{chunk_text}".encode("utf-8")
        ).hexdigest()

        chunks.append({
            "chunk_hash": chunk_hash,
            "guest": guest,
            "episode_title": episode_title,
            "publish_date": publish_date,
            "timestamp": first_block["timestamp"],
            "speaker": first_block["speaker"],
            "chunk_text": chunk_text,
            "source_url": source_url,
        })

    return chunks
