import logging
from enum import Enum
import nh3
from app.services.artifacts.schemas import ArtifactType

logger = logging.getLogger("lenny_assistant.services.artifacts.sanitizer")


class ArtifactSanitizer:
    """Security sanitizer for Artifact Engine content (Markdown & HTML)."""

    ALLOWED_TAGS = {
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "br", "hr", "div", "span",
        "ul", "ol", "li",
        "code", "pre", "blockquote",
        "table", "thead", "tbody", "tr", "th", "td",
        "strong", "b", "em", "i", "u", "s",
        "a", "img", "section", "article", "header", "footer", "nav",
    }

    ALLOWED_ATTRIBUTES = {
        "a": {"href", "title", "target", "rel"},
        "img": {"src", "alt", "title", "width", "height"},
        "div": {"class", "id"},
        "span": {"class", "id"},
        "code": {"class"},
        "th": {"colspan", "rowspan", "scope"},
        "td": {"colspan", "rowspan"},
    }

    @classmethod
    def sanitize(cls, content: str, artifact_type: ArtifactType | str) -> str:
        """Sanitizes artifact content based on type."""
        if isinstance(artifact_type, Enum):
            type_str = str(artifact_type.value).lower()
        else:
            type_str = str(artifact_type).lower()

        if type_str == ArtifactType.MARKDOWN.value:
            # Markdown is plain text source code rendered via React markdown
            return content.strip()
        elif type_str == ArtifactType.HTML.value:
            # Sanitize HTML using nh3 Rust Ammonia bindings
            sanitized = nh3.clean(
                content,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                link_rel=None,
            )
            return sanitized.strip()
        else:
            raise ValueError(
                f"Unsupported artifact type '{artifact_type}'. Allowed types are 'markdown' and 'html'."
            )

    @classmethod
    def sanitize_html(cls, content: str) -> str:
        """Convenience method to sanitize HTML content."""
        return cls.sanitize(content, ArtifactType.HTML)

