"""
VoiceClone — Telegram Channel Plugin

Receives messages via Telegram Bot API and can send text/voice responses.
Uses python-telegram-bot library (async).

Pipeline:
  Incoming: Telegram message → normalize → IncomingMessage → voice announce
  Outgoing: OutgoingMessage → synthesize voice → send to Telegram

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Any, AsyncIterator, Optional

from src.channels.base import (
    ChannelConfig,
    ChannelPlugin,
    ChannelStatus,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)


class TelegramChannel(ChannelPlugin):
    """
    Telegram Bot channel plugin.

    Config extra keys:
        bot_token: str - Telegram Bot API token from @BotFather
        download_dir: str - Directory for downloaded media (default: ~/.voiceclone/media/telegram)
    """

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)
        self._bot_token: str = config.extra.get("bot_token", "")
        self._download_dir: str = config.extra.get(
            "download_dir",
            os.path.expanduser("~/.voiceclone/media/telegram"),
        )
        self._app = None  # telegram.ext.Application
        self._message_queue: asyncio.Queue[IncomingMessage] = asyncio.Queue()
        self._running = False

    async def start(self) -> None:
        """
        Start the Telegram bot and begin polling for messages.

        Raises:
            ConnectionError: If bot token is invalid.
            ImportError: If python-telegram-bot is not installed.
        """
        if not self._bot_token:
            raise ConnectionError(
                "Telegram bot token not configured. "
                "Get one from @BotFather on Telegram."
            )

        try:
            from telegram import Update
            from telegram.ext import (
                Application,
                MessageHandler,
                filters,
            )
        except ImportError:
            raise ImportError(
                "python-telegram-bot not installed. "
                "Run: pip install python-telegram-bot"
            )

        os.makedirs(self._download_dir, exist_ok=True)

        self._status = ChannelStatus.CONNECTING
        logger.info("Starting Telegram channel...")

        try:
            self._app = Application.builder().token(self._bot_token).build()

            # Register message handler
            handler = MessageHandler(
                filters.ALL & ~filters.COMMAND,
                self._handle_message,
            )
            self._app.add_handler(handler)

            # Initialize and start polling
            await self._app.initialize()
            await self._app.start()
            await self._app.updater.start_polling(drop_pending_updates=True)

            self._status = ChannelStatus.CONNECTED
            self._running = True
            logger.info("Telegram channel connected")

        except Exception as e:
            self._status = ChannelStatus.ERROR
            logger.error("Telegram connection failed: %s", e)
            raise ConnectionError(f"Telegram connection failed: {e}")

    async def stop(self) -> None:
        """Stop the Telegram bot gracefully."""
        self._running = False
        if self._app:
            try:
                await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
            except Exception as e:
                logger.error("Error stopping Telegram: %s", e)
        self._status = ChannelStatus.DISCONNECTED
        logger.info("Telegram channel stopped")

    async def send(self, to: str, message: OutgoingMessage) -> dict[str, Any]:
        """
        Send a message to a Telegram chat.

        Args:
            to: Telegram chat ID.
            message: Message to send.

        Returns:
            Dict with send result.
        """
        if not self._app or not self.is_connected:
            return {"error": "Telegram not connected", "success": False}

        try:
            bot = self._app.bot
            chat_id = int(to)
            sent_messages = []

            # Send text
            if message.text:
                msg = await bot.send_message(chat_id=chat_id, text=message.text)
                sent_messages.append({"type": "text", "message_id": msg.message_id})

            # Send audio
            if message.audio_path and os.path.isfile(message.audio_path):
                with open(message.audio_path, "rb") as audio_file:
                    if message.as_voice:
                        msg = await bot.send_voice(chat_id=chat_id, voice=audio_file)
                    else:
                        msg = await bot.send_audio(chat_id=chat_id, audio=audio_file)
                    sent_messages.append({"type": "audio", "message_id": msg.message_id})

            # Send media
            if message.media_path and os.path.isfile(message.media_path):
                with open(message.media_path, "rb") as media_file:
                    msg = await bot.send_document(chat_id=chat_id, document=media_file)
                    sent_messages.append({"type": "media", "message_id": msg.message_id})

            return {
                "success": True,
                "to": to,
                "messages_sent": len(sent_messages),
                "details": sent_messages,
            }

        except Exception as e:
            logger.error("Telegram send error: %s", e)
            return {"error": str(e), "success": False}

    async def listen(self) -> AsyncIterator[IncomingMessage]:
        """
        Listen for incoming Telegram messages.

        Messages are queued by the internal handler and yielded here.
        """
        while self._running:
            try:
                msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                yield msg
            except asyncio.TimeoutError:
                continue

    async def _handle_message(self, update: Any, context: Any) -> None:
        """
        Internal handler for incoming Telegram updates.

        Normalizes the update into an IncomingMessage and queues it.
        """
        try:
            message = update.effective_message
            if not message:
                return

            user = update.effective_user
            sender_id = str(user.id) if user else "unknown"
            sender_name = user.full_name if user else "Unknown"

            # Check sender authorization
            if not self.is_sender_allowed(sender_id):
                logger.info("Ignored message from unauthorized sender: %s", sender_id)
                return

            incoming = IncomingMessage(
                channel="telegram",
                sender_id=sender_id,
                sender_name=sender_name,
                text=message.text or message.caption,
                timestamp=message.date.timestamp() if message.date else 0,
            )

            # Handle voice messages
            if message.voice:
                audio_path = await self._download_file(
                    message.voice.file_id, "voice", ".ogg"
                )
                incoming.audio_path = audio_path

            # Handle audio files
            elif message.audio:
                audio_path = await self._download_file(
                    message.audio.file_id, "audio", ".mp3"
                )
                incoming.audio_path = audio_path

            # Handle photos
            if message.photo:
                photo = message.photo[-1]  # Largest size
                media_path = await self._download_file(
                    photo.file_id, "photo", ".jpg"
                )
                incoming.media_path = media_path
                incoming.media_type = "image"

            # Handle documents
            elif message.document:
                ext = os.path.splitext(message.document.file_name or ".bin")[1]
                media_path = await self._download_file(
                    message.document.file_id, "doc", ext
                )
                incoming.media_path = media_path
                incoming.media_type = "document"

            await self._message_queue.put(incoming)
            logger.info(
                "Telegram message from %s: %s",
                sender_name,
                (incoming.text or "[media]")[:50],
            )

        except Exception as e:
            logger.error("Error handling Telegram message: %s", e)

    async def _download_file(
        self,
        file_id: str,
        prefix: str,
        extension: str,
    ) -> Optional[str]:
        """Download a file from Telegram to local storage."""
        try:
            bot = self._app.bot
            file = await bot.get_file(file_id)

            filename = f"{prefix}_{file_id[:12]}{extension}"
            filepath = os.path.join(self._download_dir, filename)

            await file.download_to_drive(filepath)
            logger.info("Downloaded Telegram file: %s", filepath)
            return filepath

        except Exception as e:
            logger.error("Failed to download Telegram file: %s", e)
            return None
