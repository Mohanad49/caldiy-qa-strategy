from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    api_key: str
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> Settings:
        api_key = os.getenv("CALDIY_API_KEY")
        if not api_key:
            raise RuntimeError("CALDIY_API_KEY is not set; run through make test-api or source ignored .env")
        api_port = os.getenv("CALDIY_API_PORT", "5555")
        base_url = os.getenv("CALDIY_API_URL", f"http://localhost:{api_port}")
        return cls(base_url=base_url.rstrip("/"), api_key=api_key)
