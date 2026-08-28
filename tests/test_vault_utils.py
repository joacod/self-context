from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vault_utils  # type: ignore  # noqa: E402


class PageRecordTests(unittest.TestCase):
    def test_valid_page_reads_bytes_once_and_preserves_record_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            page = vault / "core" / "concept.md"
            page.parent.mkdir()
            content = (
                "---\n"
                "type: concept\n"
                "title: Synthetic Page\n"
                "description: A synthetic page.\n"
                "tags: [synthetic]\n"
                "status: active\n"
                "generated: 2026-08-28\n"
                "verified: null\n"
                "sources: []\n"
                "assertion_kind: user_stated_fact\n"
                "stale_after: null\n"
                "---\n\n"
                "Café body.\n"
            ).encode("utf-8")
            page.write_bytes(content)

            with mock.patch.object(
                vault_utils, "safe_read_bytes", wraps=vault_utils.safe_read_bytes
            ) as read_bytes, mock.patch.object(
                vault_utils, "safe_read_text", wraps=vault_utils.safe_read_text
            ) as read_text:
                record = vault_utils.page_record(page, vault)

            self.assertEqual(read_bytes.call_count, 1)
            read_text.assert_not_called()
            self.assertEqual(record["content_hash"], hashlib.sha256(content).hexdigest())
            self.assertEqual(record["title"], "Synthetic Page")
            self.assertEqual(record["text"], content.decode("utf-8"))
            self.assertIsNone(record["read_error"])

    def test_malformed_utf8_keeps_stable_read_error_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            page = vault / "core" / "malformed.md"
            page.parent.mkdir()
            page.write_bytes(b"---\ntitle: malformed\n---\ninvalid: \xff\n")

            record = vault_utils.page_record(page, vault)

            self.assertEqual(
                record["read_error"],
                "UnicodeDecodeError: file is not valid UTF-8",
            )
            self.assertEqual(
                record["content_hash"],
                hashlib.sha256(b"").hexdigest(),
            )
            self.assertNotIn("text", record)

    def test_filesystem_failure_keeps_stable_read_error_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            page = vault / "core" / "missing.md"

            record = vault_utils.page_record(page, vault)

            self.assertEqual(
                record["read_error"],
                "FileNotFoundError: unable to read file",
            )
            self.assertEqual(
                record["content_hash"],
                hashlib.sha256(b"").hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
