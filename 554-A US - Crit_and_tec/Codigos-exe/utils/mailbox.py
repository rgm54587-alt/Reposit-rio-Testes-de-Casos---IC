from __future__ import annotations

import email
import imaplib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message
from html import unescape

from utils.config import Settings


_LINK_RE = re.compile(r"https?://[^\s\"'<>]+")


@dataclass(frozen=True)
class MailMessage:
    subject: str
    text: str

    def find_link(self, required_fragment: str) -> str:
        candidates = [unescape(link) for link in _LINK_RE.findall(self.text)]
        for link in candidates:
            if required_fragment in link:
                return link
        raise AssertionError(
            f"Nenhum link contendo {required_fragment!r} foi encontrado no e-mail."
        )


class MailboxClient:
    def __init__(self, settings: Settings):
        self.s = settings

    def wait_for_message(self, recipient: str, subject: str) -> MailMessage:
        deadline = time.monotonic() + self.s.email_wait_seconds
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                message = self._fetch(recipient, subject)
                if message:
                    return message
            except Exception as exc:  # pragma: no cover - diagnostic retry path
                last_error = exc
            time.sleep(1)
        detail = f" Último erro: {last_error}" if last_error else ""
        raise AssertionError(
            f"E-mail para {recipient!r} com assunto {subject!r} não chegou em "
            f"{self.s.email_wait_seconds}s.{detail}"
        )

    def _fetch(self, recipient: str, subject: str) -> MailMessage | None:
        if self.s.mail_backend == "mailhog":
            return self._fetch_mailhog(recipient, subject)
        if self.s.mail_backend == "imap":
            return self._fetch_imap(recipient, subject)
        raise RuntimeError("MAIL_BACKEND deve ser 'mailhog' ou 'imap'.")

    def _fetch_mailhog(self, recipient: str, subject: str) -> MailMessage | None:
        query = urllib.parse.urlencode({"kind": "to", "query": recipient})
        url = f"{self.s.mailhog_base_url}/api/v2/search?{query}"
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.load(response)
        for item in payload.get("items", []):
            headers = item.get("Content", {}).get("Headers", {})
            item_subject = " ".join(headers.get("Subject", []))
            if subject.lower() not in item_subject.lower():
                continue
            body = item.get("Content", {}).get("Body", "")
            return MailMessage(subject=item_subject, text=body)
        return None

    def _fetch_imap(self, recipient: str, subject: str) -> MailMessage | None:
        if not (self.s.imap_host and self.s.imap_username and self.s.imap_password):
            raise RuntimeError("Configure IMAP_HOST, IMAP_USERNAME e IMAP_PASSWORD.")
        klass = imaplib.IMAP4_SSL if self.s.imap_use_ssl else imaplib.IMAP4
        with klass(self.s.imap_host, self.s.imap_port) as client:
            client.login(self.s.imap_username, self.s.imap_password)
            client.select("INBOX")
            status, data = client.search(None, f'(TO "{recipient}" SUBJECT "{subject}")')
            if status != "OK" or not data or not data[0]:
                return None
            latest = data[0].split()[-1]
            status, raw = client.fetch(latest, "(RFC822)")
            if status != "OK":
                return None
            msg = email.message_from_bytes(raw[0][1])
            return MailMessage(subject=str(msg.get("Subject", "")), text=self._body(msg))

    @staticmethod
    def _body(message: Message) -> str:
        chunks: list[str] = []
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() in {"text/plain", "text/html"}:
                    payload = part.get_payload(decode=True) or b""
                    chunks.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
        else:
            payload = message.get_payload(decode=True) or b""
            chunks.append(payload.decode(message.get_content_charset() or "utf-8", errors="replace"))
        return "\n".join(chunks)
