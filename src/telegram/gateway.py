"""
src/telegram/gateway.py — Telegram Inline Keyboard Decision & Review Gate.

Handles sending interactive approval gates, track selection menus, and
Cloudflare-tunneled review links directly to the user's Telegram chat.
"""

import os
import time
import json
import urllib.request
import urllib.parse
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable


@dataclass
class TelegramButton:
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        d = {"text": self.text}
        if self.callback_data:
            d["callback_data"] = self.callback_data
        if self.url:
            d["url"] = self.url
        return d


class TelegramGateway:
    """Interacts with Telegram Bot API to present decision gates and collect responses."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "8293122782")
        self.dry_run = dry_run
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(
        self,
        text: str,
        buttons: Optional[List[List[TelegramButton]]] = None,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """
        Send formatted text message with optional inline keyboard buttons.
        Returns message_id on success.
        """
        if self.dry_run or not self.bot_token:
            print("\n[TELEGRAM DRY-RUN MESSAGE]")
            print(f"Chat: {self.chat_id}")
            print(f"Text:\n{text}")
            if buttons:
                print("Buttons:")
                for row in buttons:
                    row_str = " | ".join([f"[{b.text}]" + (f" -> {b.url or b.callback_data}") for b in row])
                    print(f"  {row_str}")
            return 999999

        url = f"{self.base_url}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if buttons:
            keyboard = [[btn.to_dict() for btn in row] for row in buttons]
            payload["reply_markup"] = {"inline_keyboard": keyboard}

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    return res["result"].get("message_id")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram message: {e}")
        return None

    def send_photo(
        self,
        photo_path: str,
        caption: str = "",
        buttons: Optional[List[List[TelegramButton]]] = None,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Send a photo image file to Telegram."""
        if self.dry_run or not self.bot_token or not os.path.exists(photo_path):
            print(f"[DRY-RUN PHOTO] {photo_path} - Caption: {caption}")
            return 999998

        url = f"{self.base_url}/sendPhoto"
        import subprocess

        cmd = [
            "curl", "-s", "-X", "POST", url,
            "-F", f"chat_id={self.chat_id}",
            "-F", f"photo=@{photo_path}",
            "-F", f"caption={caption}",
            "-F", f"parse_mode={parse_mode}",
        ]

        if buttons:
            keyboard = [[btn.to_dict() if hasattr(btn, "to_dict") else btn for btn in row] for row in buttons]
            cmd.extend(["-F", f"reply_markup={json.dumps({'inline_keyboard': keyboard})}"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(res.stdout)
            if data.get("ok"):
                return data["result"].get("message_id")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram photo: {e}")
        return None

    def send_video(
        self,
        video_path: str,
        caption: str = "",
        buttons: Optional[List[List[TelegramButton]]] = None,
        parse_mode: str = "HTML",
    ) -> Optional[int]:
        """Send a playable MP4 video file directly to Telegram."""
        if self.dry_run or not self.bot_token or not os.path.exists(video_path):
            print(f"[DRY-RUN VIDEO] {video_path} - Caption: {caption}")
            return 999997

        url = f"{self.base_url}/sendVideo"
        import subprocess

        cmd = [
            "curl", "-s", "-X", "POST", url,
            "-F", f"chat_id={self.chat_id}",
            "-F", f"video=@{video_path}",
            "-F", f"caption={caption}",
            "-F", f"parse_mode={parse_mode}",
        ]

        if buttons:
            keyboard = [[btn.to_dict() if hasattr(btn, "to_dict") else btn for btn in row] for row in buttons]
            cmd.extend(["-F", f"reply_markup={json.dumps({'inline_keyboard': keyboard})}"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            data = json.loads(res.stdout)
            if data.get("ok"):
                return data["result"].get("message_id")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram video: {e}")
        return None

    def send_concept_review_gate(
        self,
        project_title: str,
        track_title: str,
        album_title: str,
        concept_summary: str,
        estimated_cost: float,
    ) -> Optional[int]:
        """Present Stage 1 Video Concept Review Gate."""
        text = (
            f"🎬 <b>VØIDRIDE VIDEO CONCEPT GATE</b>\n\n"
            f"<b>Project:</b> {project_title}\n"
            f"<b>Track:</b> {track_title} (<i>{album_title}</i>)\n"
            f"<b>Estimated Inference:</b> ${estimated_cost:.4f}\n\n"
            f"<b>Concept Brief:</b>\n{concept_summary}\n\n"
            f"Tap an action below to direct next steps:"
        )

        buttons = [
            [
                TelegramButton(
                    text="✅ Approve Storyboard", callback_data=f"concept:approve"
                ),
                TelegramButton(
                    text="🔄 Reroll Brief", callback_data=f"concept:reroll"
                ),
            ],
            [
                TelegramButton(
                    text="🎵 Switch Track", callback_data=f"concept:switch_track"
                ),
                TelegramButton(
                    text="❌ Cancel", callback_data=f"concept:cancel"
                ),
            ],
        ]

        return self.send_message(text, buttons=buttons)

    def send_render_review_gate(
        self,
        project_title: str,
        track_title: str,
        duration: float,
        cloudflare_url: str,
    ) -> Optional[int]:
        """Present Stage 2 Rough Cut / Video Review Gate with Cloudflare URL."""
        text = (
            f"👀 <b>VIDEO PREVIEW READY FOR REVIEW</b>\n\n"
            f"<b>Project:</b> {project_title}\n"
            f"<b>Track:</b> {track_title}\n"
            f"<b>Duration:</b> {duration:.1f}s\n\n"
            f"Your video has been rendered locally with Tesseract and tunneled "
            f"via Cloudflare for instant mobile playback."
        )

        buttons = [
            [
                TelegramButton(
                    text="⚡ Stream Video (Cloudflare)", url=cloudflare_url
                )
            ],
            [
                TelegramButton(
                    text="🚀 Finalize & Export 4K", callback_data="render:finalize"
                ),
                TelegramButton(
                    text="✂️ Request Revisions", callback_data="render:revise"
                ),
            ],
        ]

        return self.send_message(text, buttons=buttons)

    def wait_for_callback(
        self,
        target_prefix: str,
        timeout_seconds: int = 120,
        poll_interval: int = 3,
    ) -> Optional[str]:
        """
        Poll for inline keyboard button click matching target_prefix.
        Returns the clicked callback_data, or None if timed out.
        """
        if self.dry_run or not self.bot_token:
            print(f"[DRY-RUN] Simulating instant button click for '{target_prefix}:approve'")
            return f"{target_prefix}:approve"

        start_time = time.time()
        last_update_id = 0

        while time.time() - start_time < timeout_seconds:
            url = f"{self.base_url}/getUpdates?offset={last_update_id + 1}&timeout=5"
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            last_update_id = update["update_id"]
                            if "callback_query" in update:
                                cb = update["callback_query"]
                                cb_data = cb.get("data", "")
                                if cb_data.startswith(target_prefix):
                                    # Acknowledge callback
                                    self._answer_callback_query(cb["id"], "Received!")
                                    return cb_data
            except Exception:
                pass
            time.sleep(poll_interval)

        return None

    def _answer_callback_query(self, query_id: str, text: str):
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": query_id, "text": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception:
            pass
