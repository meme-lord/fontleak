from pydantic import BaseModel, Field, field_validator, ValidationError
import string
import os
from urllib.parse import urlparse
from .logger import logger
from typing import Optional


class Settings(BaseModel):
    host: str = Field(
        ...,
        description="Base URL where the application is accessible (e.g., http://localhost:4242)",
    )

    @field_validator("host")
    def validate_host(cls, v):
        # Remove trailing slash if present
        v = v.rstrip("/")

        # Parse the URL
        parsed = urlparse(v)

        # Validate the URL
        if not parsed.scheme and not v.startswith("//"):
            raise ValueError(f"Relative URL {repr(v)} is not allowed")

        if not parsed.netloc:
            raise ValueError(f"URL {repr(v)} must contain a network location")

        return v


try:
    settings = Settings(host="http://localhost:4242")
    logger.info("Application settings loaded successfully. Host: %s", settings.host)
except ValidationError as e:
    logger.critical("Failed to load application settings:\n%s", str(e))
    raise SystemExit(1) from e


class BaseLeakSetupParams(BaseModel):
    selector: str = Field(
        default=os.getenv("SELECTOR", "script:first-of-type"),
        description="CSS selector for target element",
    )
    parent: str = Field(
        default=os.getenv("PARENT", "body"), description="Parent element (body or head)"
    )
    alphabet: str = Field(
        default=os.getenv("ALPHABET", string.printable),
        description="Characters to include in the font",
    )
    attr: str = Field(
        default=os.getenv("ATTR", "textContent"), description="Attribute to exfiltrate"
    )

    @field_validator("parent")
    def validate_parent(cls, v):
        if v not in ["body", "head"]:
            raise ValueError("Parent must be either 'body' or 'head'")
        return v

    @field_validator("alphabet")
    def validate_alphabet(cls, v):
        if not all(ord(c) < 256 for c in v):
            raise ValueError("fontleak only supports ASCII characters for now")

        # Create ordered set of characters while preserving order
        seen = set()
        unique_chars = []
        for c in v:
            if c not in seen:
                seen.add(c)
                unique_chars.append(c)
        v = "".join(unique_chars)

        return v


class DynamicLeakSetupParams(BaseLeakSetupParams):
    id: Optional[str] = Field(
        default=None, description="Unique identifier for the payload"
    )


class StaticLeakSetupParams(BaseLeakSetupParams):
    length: int = Field(
        default=int(os.getenv("LENGTH", 100)), description="Length of the payload"
    )
    browser: str = Field(
        default=os.getenv("BROWSER", "all"),
        description="Browser compatibility (all, chrome, firefox, safari)",
    )

    @field_validator("browser")
    def validate_browser(cls, v):
        if v not in ["all", "chrome", "firefox", "safari"]:
            raise ValueError("Invalid browser option")
        return v


class LeakParams(BaseModel):
    idx: Optional[int] = Field(
        default=None, description="Index of the character to leak in the reconstruction"
    )
    char_idx: int = Field(
        default=0, description="Index of the character to leak in the alphabet"
    )
    id: Optional[str] = Field(
        default=None, description="Unique identifier for the payload"
    )
