import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modules import sorter


class FakeConn:
    def __init__(self, all_uids=None, unseen_uids=None):
        self.all_uids = all_uids or []
        self.unseen_uids = unseen_uids or []
        self.selected = []

    def select_folder(self, folder):
        self.selected.append(folder)

    def search(self, criteria):
        if criteria == ["ALL"]:
            return self.all_uids
        if criteria == ["UNSEEN"]:
            return self.unseen_uids
        raise AssertionError(f"Unexpected search criteria: {criteria}")


class SorterStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_state_file = sorter.STATE_FILE
        sorter.STATE_FILE = Path(self.temp_dir.name) / "state.json"

    def tearDown(self):
        sorter.STATE_FILE = self.original_state_file
        self.temp_dir.cleanup()

    def test_prime_startup_cursor_sets_highest_current_uid(self):
        conn = FakeConn(all_uids=[3, 7, 11])

        highest = sorter._prime_startup_cursor(conn)

        self.assertEqual(highest, 11)
        self.assertEqual(sorter._get_last_seen_uid(), 11)

    def test_prime_startup_cursor_overwrites_older_cursor_without_processing_backlog(self):
        sorter._set_last_seen_uid(10)
        conn = FakeConn(all_uids=[10, 12, 25])

        highest = sorter._prime_startup_cursor(conn)

        self.assertEqual(highest, 25)
        self.assertEqual(sorter._get_last_seen_uid(), 25)

    def test_process_unseen_only_passes_newer_uids_than_watermark(self):
        sorter._set_last_seen_uid(20)
        conn = FakeConn(unseen_uids=[18, 20, 21, 22])

        with patch.object(sorter, "_process_uids", return_value={"checked": 2, "kept": 1, "moved": 1, "skipped": 0, "errors": 0}) as process_uids:
            stats = sorter._process_unseen(conn)

        process_uids.assert_called_once_with(conn, [21, 22], "unseen")
        self.assertEqual(stats["checked"], 2)


if __name__ == "__main__":
    unittest.main()
