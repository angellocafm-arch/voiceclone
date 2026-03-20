"""
VoiceClone — Channel Base Classes

Abstract base for all messaging channel plugins.
Inspired by OpenClaw's plugin architecture (MIT).

All channels implement the same interface: start, stop, send, listen.
This allows the system to treat Telegram, WhatsApp, etc. identically.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional


class ChannelType(Enum):
    """Supported channel types."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SIGNAL = "signal"
    IMESSAGE = "imessage"


class ChannelStatus(Enum):
    """Channel connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class IncomingMessage:
    """
    A message received from a channel.

    Normalized format — all channels produce the same structure.
    """
    channel: str                    # "telegram", "whatsapp", etc.
    sender_id: str                  # Unique sender identifier
    sender_name: str                # Display name
    text: Optional[str] = None      # Text content
    audio_path: Optional[str] = None  # Path to audio file (if voice message)
    media_path: Optional[str] = None  # Path to media file (image, video)
    media_type: Optional[str] = None  # "image", "video", "document"
    reply_to: Optional[str] = None  # Message ID being replied to
    timestamp: float = 0.0         # Unix timestamp
    raw: dict[str, Any] = field(default_factory=dict)  # Channel-specific raw data

    @property
    def has_text(self) -> bool:
        return bool(self.text)

    @property
    def has_audio(self) -> bool:
        return bool(self.audio_path)

    @property
    def has_media(self) -> bool:
        return bool(self.media_path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "text": self.text,
            "has_audio": self.has_audio,
            "has_media": self.has_media,
            "timestamp": self.timestamp,
        }


@dataclass
class OutgoingMessage:
    """
    A message to send through a channel.
    """
    text: Optional[str] = None      # Text content
    audio_path: Optional[str] = None  # Audio file to send
    as_voice: bool = False          # Send audio as voice note
    reply_to: Optional[str] = None  # Reply to specific message
    media_path: Optional[str] = None  # Media file to send


@dataclass
class ChannelConfig:
    """
    Configuration for a channel plugin.
    """
    channel_type: str
    enabled: bool = True
    announce_messages: bool = True   # Read incoming messages aloud
    auto_reply: bool = False         # Automatically reply to messages
    allowed_senders: list[str] = field(default_factory=lambda: ["*"])
    extra: dict[str, Any] = field(default_factory=dict)


class ChannelPlugin(ABC):
    """
    Abstract base class for messaging channel plugins.

    Inspired by OpenClaw's plugin architecture.
    Each channel implements this interface to provide a uniform
    way to receive and send messages.

    Lifecycle:
        plugin = TelegramChannel(config)
        await plugin.start()       # Connect
        async for msg in plugin.listen():  # Receive messages
            ...
        await plugin.send(to, msg) # Send messages
        await plugin.stop()        # Disconnect
    """

    def __init__(self, config: ChannelConfig) -> None:
        self.config = config
        self._status = ChannelStatus.DISCONNECTED

    @property
    def channel_type(self) -> str:
        """Return the channel type identifier."""
        return self.config.channel_type

    @property
    def status(self) -> ChannelStatus:
        """Current connection status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Whether the channel is connected and receiving."""
        return self._status == ChannelStatus.CONNECTED

    def is_sender_allowed(self, sender_id: str) -> bool:
        """Check if a sender is in the allowed list."""
        if "*" in self.config.allowed_senders:
            return True
        return sender_id in self.config.allowed_senders

    @abstractmethod
    async def start(self) -> None:
        """
        Initialize and connect to the channel.

        Raises:
            ConnectionError: If connection fails.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """
        Disconnect and clean up resources.
        """
        ...

    @abstractmethod
    async def send(self, to: str, message: OutgoingMessage) -> dict[str, Any]:
        """
        Send a message through the channel.

        Args:
            to: Recipient identifier (chat ID, phone number, etc.)
            message: Message to send.

        Returns:
            Dict with send result (success, message_id, etc.)
        """
        ...

    @abstractmethod
    async def listen(self) -> AsyncIterator[IncomingMessage]:
        """
        Listen for incoming messages.

        Yields IncomingMessage objects as they arrive.
        This is an async generator that runs indefinitely.
        """
        ...
        yield  # type: ignore  # Make it an async generator

    def get_status(self) -> dict[str, Any]:
        """Get channel status for the frontend."""
        return {
            "type": self.channel_type,
            "status": self._status.value,
            "connected": self.is_connected,
            "enabled": self.config.enabled,
            "announce": self.config.announce_messages,
        }
