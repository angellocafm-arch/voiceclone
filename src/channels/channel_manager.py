"""
VoiceClone — Channel Manager

Manages all active messaging channels. Provides a unified interface
to receive and send messages across Telegram, WhatsApp, etc.

Pipeline:
  Incoming message → channel_manager.on_message → voice announce → queue
  Outgoing message → channel_manager.send → channel plugin → delivered

Security: Messages from channels NEVER auto-execute OS actions.
They are announced (voice) and require local confirmation.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from src.channels.base import (
    ChannelConfig,
    ChannelPlugin,
    ChannelStatus,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)

# Registry of channel types → classes
CHANNEL_REGISTRY: dict[str, type[ChannelPlugin]] = {}


def register_channel(channel_type: str, cls: type[ChannelPlugin]) -> None:
    """Register a channel plugin class."""
    CHANNEL_REGISTRY[channel_type] = cls


# ─── Register built-in channels ──────────────────────────

def _register_builtins() -> None:
    """Register built-in channel types."""
    try:
        from src.channels.telegram_channel import TelegramChannel
        register_channel("telegram", TelegramChannel)
    except ImportError:
        logger.debug("Telegram channel not available (missing dependencies)")

    try:
        from src.channels.whatsapp_channel import WhatsAppChannel
        register_channel("whatsapp", WhatsAppChannel)
    except ImportError:
        logger.debug("WhatsApp channel not available")

_register_builtins()


class ChannelManager:
    """
    Manages all messaging channel plugins.

    Provides:
    - Unified message receiving across all channels
    - Unified message sending
    - Channel lifecycle management (start/stop)
    - Message history for the frontend
    - Callback system for voice announcements
    """

    def __init__(
        self,
        config_path: str | Path = "~/.voiceclone/channels.json",
        on_message: Optional[Callable[[IncomingMessage], Any]] = None,
    ) -> None:
        self.config_path = Path(config_path).expanduser()
        self.channels: dict[str, ChannelPlugin] = {}
        self.message_history: list[IncomingMessage] = []
        self._on_message_callback = on_message
        self._tasks: list[asyncio.Task] = []
        self._max_history = 500

    # ─── Configuration ────────────────────────────────────

    def load_config(self) -> dict[str, ChannelConfig]:
        """Load channel configurations from disk."""
        if not self.config_path.exists():
            return {}

        try:
            data = json.loads(self.config_path.read_text())
            configs: dict[str, ChannelConfig] = {}

            for channel_type, cfg in data.items():
                if isinstance(cfg, dict):
                    configs[channel_type] = ChannelConfig(
                        channel_type=channel_type,
                        enabled=cfg.get("enabled", True),
                        announce_messages=cfg.get("announce_messages", True),
                        auto_reply=cfg.get("auto_reply", False),
                        allowed_senders=cfg.get("allowed_senders", ["*"]),
                        extra=cfg,
                    )

            return configs
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to load channel config: %s", e)
            return {}

    def save_config(self, configs: dict[str, dict[str, Any]]) -> None:
        """Save channel configurations to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(configs, indent=2))

    # ─── Lifecycle ────────────────────────────────────────

    async def start_all(self) -> dict[str, bool]:
        """
        Start all configured and enabled channels.

        Returns:
            Dict mapping channel_type → success boolean.
        """
        configs = self.load_config()
        results: dict[str, bool] = {}

        for channel_type, config in configs.items():
            if not config.enabled:
                results[channel_type] = False
                continue

            try:
                success = await self.start_channel(channel_type, config)
                results[channel_type] = success
            except Exception as e:
                logger.error("Failed to start channel '%s': %s", channel_type, e)
                results[channel_type] = False

        return results

    async def start_channel(
        self,
        channel_type: str,
        config: Optional[ChannelConfig] = None,
    ) -> bool:
        """
        Start a specific channel.

        Args:
            channel_type: Channel type identifier.
            config: Channel configuration (loads from disk if not provided).

        Returns:
            True if started successfully.
        """
        # Get or create config
        if config is None:
            configs = self.load_config()
            config = configs.get(channel_type)
            if not config:
                logger.error("No config found for channel: %s", channel_type)
                return False

        # Get channel class
        channel_cls = CHANNEL_REGISTRY.get(channel_type)
        if not channel_cls:
            logger.error("Unknown channel type: %s", channel_type)
            return False

        # Stop existing channel if running
        if channel_type in self.channels:
            await self.stop_channel(channel_type)

        # Create and start
        try:
            channel = channel_cls(config)
            await channel.start()
            self.channels[channel_type] = channel

            # Start listener task
            task = asyncio.create_task(
                self._listen_channel(channel_type, channel)
            )
            self._tasks.append(task)

            logger.info("Channel '%s' started", channel_type)
            return True

        except Exception as e:
            logger.error("Failed to start '%s': %s", channel_type, e)
            return False

    async def stop_channel(self, channel_type: str) -> None:
        """Stop a specific channel."""
        channel = self.channels.pop(channel_type, None)
        if channel:
            await channel.stop()
            logger.info("Channel '%s' stopped", channel_type)

    async def stop_all(self) -> None:
        """Stop all channels and cancel listener tasks."""
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        for channel_type in list(self.channels.keys()):
            await self.stop_channel(channel_type)

    # ─── Message Handling ─────────────────────────────────

    async def _listen_channel(
        self,
        channel_type: str,
        channel: ChannelPlugin,
    ) -> None:
        """Background task: listen for messages from a channel."""
        try:
            async for msg in channel.listen():
                await self._process_incoming(msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Channel '%s' listener error: %s", channel_type, e)

    async def _process_incoming(self, msg: IncomingMessage) -> None:
        """Process an incoming message from any channel."""
        # Add to history
        self.message_history.append(msg)
        if len(self.message_history) > self._max_history:
            self.message_history = self.message_history[-self._max_history:]

        # Call callback (for voice announce, etc.)
        if self._on_message_callback:
            try:
                result = self._on_message_callback(msg)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error("Message callback error: %s", e)

        logger.info(
            "Message from %s via %s: %s",
            msg.sender_name,
            msg.channel,
            (msg.text or "[media]")[:50],
        )

    # ─── Send ─────────────────────────────────────────────

    async def send(
        self,
        channel_type: str,
        to: str,
        message: OutgoingMessage,
    ) -> dict[str, Any]:
        """
        Send a message through a specific channel.

        Args:
            channel_type: Channel to send through.
            to: Recipient identifier.
            message: Message to send.

        Returns:
            Send result dict.
        """
        channel = self.channels.get(channel_type)
        if not channel:
            return {"error": f"Channel '{channel_type}' not active", "success": False}

        if not channel.is_connected:
            return {"error": f"Channel '{channel_type}' not connected", "success": False}

        return await channel.send(to, message)

    # ─── Status ───────────────────────────────────────────

    def get_all_status(self) -> list[dict[str, Any]]:
        """Get status of all channels for the frontend."""
        statuses: list[dict[str, Any]] = []

        # Active channels
        for channel_type, channel in self.channels.items():
            statuses.append(channel.get_status())

        # Configured but not active
        configs = self.load_config()
        for channel_type, config in configs.items():
            if channel_type not in self.channels:
                statuses.append({
                    "type": channel_type,
                    "status": "disconnected",
                    "connected": False,
                    "enabled": config.enabled,
                })

        return statuses

    def get_recent_messages(
        self,
        channel_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get recent messages, optionally filtered by channel."""
        msgs = self.message_history
        if channel_type:
            msgs = [m for m in msgs if m.channel == channel_type]
        return [m.to_dict() for m in msgs[-limit:]]

    # ─── Channel Configuration ────────────────────────────

    async def configure_channel(
        self,
        channel_type: str,
        config_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Configure a new channel or update existing.

        Args:
            channel_type: Channel type.
            config_data: Configuration dict (includes bot_token, etc.)

        Returns:
            Result dict.
        """
        # Load existing config
        configs = self.load_config()
        raw_configs: dict[str, dict[str, Any]] = {}
        if self.config_path.exists():
            try:
                raw_configs = json.loads(self.config_path.read_text())
            except json.JSONDecodeError:
                pass

        # Update config
        raw_configs[channel_type] = {
            "enabled": config_data.get("enabled", True),
            "announce_messages": config_data.get("announce_messages", True),
            "auto_reply": config_data.get("auto_reply", False),
            "allowed_senders": config_data.get("allowed_senders", ["*"]),
            **config_data,
        }

        # Save
        self.save_config(raw_configs)

        return {
            "success": True,
            "channel_type": channel_type,
            "message": f"Channel '{channel_type}' configured. Restart to apply.",
        }

    async def remove_channel(self, channel_type: str) -> dict[str, Any]:
        """Remove a channel configuration."""
        # Stop if running
        if channel_type in self.channels:
            await self.stop_channel(channel_type)

        # Remove from config
        if self.config_path.exists():
            try:
                raw_configs = json.loads(self.config_path.read_text())
                raw_configs.pop(channel_type, None)
                self.save_config(raw_configs)
            except json.JSONDecodeError:
                pass

        return {"success": True, "removed": channel_type}
