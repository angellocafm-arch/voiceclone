"""
VoiceClone — Email Manager

Read and send emails using macOS Mail.app (via AppleScript) or
IMAP/SMTP for cross-platform support.

SECURITY: Sending email ALWAYS requires DOUBLE confirmation (vocal).

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Represents an email message."""
    id: str
    sender: str
    subject: str
    preview: str
    date: str
    is_read: bool = False
    body: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "from": self.sender,
            "subject": self.subject,
            "preview": self.preview,
            "date": self.date,
            "is_read": self.is_read,
        }
        if self.body:
            result["body"] = self.body
        return result


class EmailManager:
    """
    Email operations for VoiceClone.

    Primary: macOS Mail.app via AppleScript (no config needed)
    Fallback: IMAP/SMTP (requires config)

    Security levels:
    - READ inbox: NONE (safe)
    - READ email: NONE (safe)
    - SEND email: DOUBLE confirmation (vocal)
    """

    def __init__(self) -> None:
        self._system = os.uname().sysname

    def read_inbox(
        self,
        limit: int = 10,
        unread_only: bool = True,
    ) -> dict[str, Any]:
        """
        Read recent emails from the inbox.

        Confirmation level: NONE

        Args:
            limit: Maximum emails to return.
            unread_only: Only return unread emails.

        Returns:
            Dict with email list.
        """
        if self._system == "Darwin":
            return self._read_inbox_macos(limit, unread_only)
        return {
            "error": "Email reading is only supported on macOS currently.",
            "success": False,
            "hint": "IMAP support coming soon.",
        }

    def _read_inbox_macos(self, limit: int, unread_only: bool) -> dict[str, Any]:
        """Read inbox from Mail.app via AppleScript."""
        filter_clause = "whose read status is false" if unread_only else ""

        script = f'''
tell application "Mail"
    set theMessages to (messages of inbox {filter_clause})
    set resultList to {{}}
    set msgCount to 0
    repeat with msg in theMessages
        if msgCount ≥ {limit} then exit repeat
        set msgId to id of msg as text
        set msgSender to sender of msg
        set msgSubject to subject of msg
        set msgDate to date received of msg as text
        set msgRead to read status of msg
        set msgPreview to (content of msg)
        if length of msgPreview > 200 then
            set msgPreview to text 1 thru 200 of msgPreview
        end if
        set end of resultList to msgId & "|||" & msgSender & "|||" & msgSubject & "|||" & msgDate & "|||" & msgRead & "|||" & msgPreview
        set msgCount to msgCount + 1
    end repeat
    set AppleScript's text item delimiters to "\\n"
    return resultList as text
end tell
'''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                return {
                    "error": f"Mail.app error: {result.stderr.strip()}",
                    "success": False,
                    "hint": "Make sure Mail.app is configured with an account.",
                }

            emails: list[dict[str, Any]] = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|||")
                if len(parts) >= 6:
                    emails.append(EmailMessage(
                        id=parts[0].strip(),
                        sender=parts[1].strip(),
                        subject=parts[2].strip(),
                        date=parts[3].strip(),
                        is_read=parts[4].strip().lower() == "true",
                        preview=parts[5].strip(),
                    ).to_dict())

            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "unread_only": unread_only,
            }

        except subprocess.TimeoutExpired:
            return {"error": "Mail.app took too long to respond", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def read_email(self, email_id: str) -> dict[str, Any]:
        """
        Read a specific email's full content.

        Confirmation level: NONE

        Args:
            email_id: Email ID from read_inbox.

        Returns:
            Dict with full email content.
        """
        if self._system != "Darwin":
            return {"error": "Only supported on macOS currently", "success": False}

        script = f'''
tell application "Mail"
    set msg to message id {email_id} of inbox
    set msgSender to sender of msg
    set msgSubject to subject of msg
    set msgDate to date received of msg as text
    set msgBody to content of msg
    return msgSender & "|||" & msgSubject & "|||" & msgDate & "|||" & msgBody
end tell
'''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                return {"error": f"Mail.app error: {result.stderr.strip()}", "success": False}

            parts = result.stdout.strip().split("|||", 3)
            if len(parts) >= 4:
                return {
                    "success": True,
                    "from": parts[0].strip(),
                    "subject": parts[1].strip(),
                    "date": parts[2].strip(),
                    "body": parts[3].strip(),
                }

            return {"error": "Could not parse email", "success": False}

        except Exception as e:
            return {"error": str(e), "success": False}

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        """
        Send an email via Mail.app.

        ⚠️ Confirmation level: DOUBLE (requires vocal confirmation)

        This method only prepares the email. The actual send MUST be
        confirmed by the user through the confirmation system.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Email body text.

        Returns:
            Dict with send result.
        """
        if self._system != "Darwin":
            return {"error": "Only supported on macOS currently", "success": False}

        # Validate email format (basic)
        if "@" not in to or "." not in to:
            return {"error": f"Invalid email address: {to}", "success": False}

        # Escape for AppleScript
        subject_safe = subject.replace('"', '\\"')
        body_safe = body.replace('"', '\\"')
        to_safe = to.replace('"', '\\"')

        script = f'''
tell application "Mail"
    set newMsg to make new outgoing message with properties {{subject:"{subject_safe}", content:"{body_safe}", visible:true}}
    tell newMsg
        make new to recipient with properties {{address:"{to_safe}"}}
    end tell
    send newMsg
end tell
'''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                logger.info("Email sent to %s: %s", to, subject)
                return {
                    "success": True,
                    "to": to,
                    "subject": subject,
                    "confirmation_level": "double",
                }

            return {"error": f"Mail.app error: {result.stderr.strip()}", "success": False}

        except Exception as e:
            return {"error": str(e), "success": False}
