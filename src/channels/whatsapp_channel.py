"""
VoiceClone — WhatsApp Channel Plugin (Placeholder)

WhatsApp integration via:
- Option A: WhatsApp Business API (requires Business account + payment)
- Option B: whatsapp-web.js bridge (Node.js microservice)

This is a placeholder implementation. Full implementation will be
Phase 2 after Telegram is stable.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from src.channels.base import (
    ChannelConfig,
    ChannelPlugin,
    ChannelStatus,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)


class WhatsAppChannel(ChannelPlugin):
    """
    WhatsApp channel plugin (placeholder).

    TODO: Implement one of:
    1. WhatsApp Business API client
    2. whatsapp-web.js bridge (Node.js subprocess)
    3. Baileys Python wrapper
    """

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)

    async def start(self) -> None:
        """Start WhatsApp connection (not yet implemented)."""
        logger.warning("WhatsApp channel is not yet implemented")
        self._status = ChannelStatus.ERROR
        raise NotImplementedError(
            "WhatsApp support is coming soon. "
            "Currently supported: Telegram."
        )

    async def stop(self) -> None:
        """Stop WhatsApp connection."""
        self._status = ChannelStatus.DISCONNECTED

    async def send(self, to: str, message: OutgoingMessage) -> dict[str, Any]:
        """Send a WhatsApp message (not yet implemented)."""
        return {
            "error": "WhatsApp not yet implemented",
            "success": False,
            "hint": "Use Telegram for now.",
        }

    async def listen(self) -> AsyncIterator[IncomingMessage]:
        """Listen for WhatsApp messages (not yet implemented)."""
        raise NotImplementedError("WhatsApp listener not implemented")
        yield  # type: ignore
