"""
Test perzistence dat sorter_rules přes restart (simulace Railway redeploymentu).

Ověřuje, že pravidla zapsaná do SQLite přežijí:
1. Uzavření a znovuotevření DB připojení (simulace restartu procesu)
2. Znovunačtení modulu s jiným DATA_DIR (simulace nového kontejneru se stejným Volume)
"""
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _reload_with_data_dir(data_dir: Path):
    """Znovu načte sorter_rules s nastaveným DATA_DIR — simuluje restart s persistentním Volume."""
    import src.config as config
    config.DATA_DIR = data_dir

    # Znovu načti sorter_rules, aby si vzal nový DATA_DIR
    import src.sorter_rules as rules_mod
    rules_mod.RULES_DB = data_dir / "sorter_rules.db"
    importlib.reload(rules_mod)
    return rules_mod


class DataPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.rules = _reload_with_data_dir(self.data_dir)

    def tearDown(self):
        self.temp_dir.cleanup()
        # Vrať modul do původního stavu
        importlib.reload(sys.modules["src.sorter_rules"])

    def test_rule_survives_connection_close_and_reopen(self):
        """Pravidlo přežije uzavření DB připojení (každý _connect() otevírá nové)."""
        self.rules.add_move_rule("from_address", "spam@example.com")

        # Nové připojení — žádná globální proměnná nedrží stav
        with self.rules._connect() as conn:
            rows = conn.execute("SELECT * FROM sorter_rules").fetchall()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rule_value"], "spam@example.com")

    def test_rule_survives_module_reload(self):
        """Pravidlo přežije reload modulu — simulace restartu procesu se stejným DATA_DIR."""
        self.rules.add_move_rule("from_address", "persist@example.com")

        # Simulace restartu: reload modulu, stejný data_dir
        reloaded = _reload_with_data_dir(self.data_dir)

        with reloaded._connect() as conn:
            rows = conn.execute("SELECT * FROM sorter_rules").fetchall()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rule_value"], "persist@example.com")

    def test_multiple_rules_all_survive_reload(self):
        """Více pravidel přežije reload — stejná ID a created_at."""
        self.rules.add_move_rule("from_address", "a@example.com")
        self.rules.add_move_rule("from_address", "b@example.com")
        self.rules.add_move_rule("content_hash", "abc123")

        # Snapshot před restartem
        with self.rules._connect() as conn:
            before = {r["rule_value"]: dict(r) for r in conn.execute("SELECT * FROM sorter_rules").fetchall()}

        reloaded = _reload_with_data_dir(self.data_dir)

        with reloaded._connect() as conn:
            after = {r["rule_value"]: dict(r) for r in conn.execute("SELECT * FROM sorter_rules").fetchall()}

        self.assertEqual(before.keys(), after.keys())
        for key in before:
            self.assertEqual(before[key]["id"], after[key]["id"])
            self.assertEqual(before[key]["created_at"], after[key]["created_at"])

    def test_match_works_after_reload(self):
        """match_move_rule funguje po reloadu — pravidlo aktivně matchuje email."""
        sender = "newsletter@spam.com"
        self.rules.add_move_rule("from_address", sender)

        reloaded = _reload_with_data_dir(self.data_dir)
        result = reloaded.match_move_rule(sender, subject="Hello", body="Content")

        self.assertIsNotNone(result)
        self.assertEqual(result["rule_type"], "from_address")
        self.assertEqual(result["rule_value"], sender)
        self.assertEqual(result["action"], "MOVE")

    def test_duplicate_rule_not_created_after_reload(self):
        """INSERT OR IGNORE — druhé přidání stejného pravidla po reloadu nevytvoří duplicitu."""
        self.rules.add_move_rule("from_address", "dup@example.com")

        reloaded = _reload_with_data_dir(self.data_dir)
        created = reloaded.add_move_rule("from_address", "dup@example.com")

        self.assertFalse(created)  # pravidlo existovalo, nezaloženo znovu

        with reloaded._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM sorter_rules").fetchone()[0]

        self.assertEqual(count, 1)

    def test_delete_rule_removes_it_from_db(self):
        """Smazání pravidla ho skutečně odstraní z persistentní DB."""
        self.rules.add_move_rule("from_address", "delete@example.com")

        deleted = self.rules.delete_move_rule("from_address", "delete@example.com")

        self.assertTrue(deleted)
        with self.rules._connect() as conn:
            count = conn.execute(
                """
                SELECT COUNT(*) FROM sorter_rules
                WHERE rule_type = 'from_address' AND rule_value = 'delete@example.com' AND action = 'MOVE'
                """
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_deleted_rule_no_longer_matches_after_reload(self):
        """Po smazání a reloadu se pravidlo už nepoužije na další emaily."""
        sender = "undo@example.com"
        self.rules.add_move_rule("from_address", sender)
        self.rules.delete_move_rule("from_address", sender)

        reloaded = _reload_with_data_dir(self.data_dir)
        result = reloaded.match_move_rule(sender, subject="Hello", body="Content")

        self.assertIsNone(result)

    def test_empty_volume_starts_clean(self):
        """Nový DATA_DIR (prázdný Volume) začíná s prázdnou tabulkou — žádná ghost data."""
        fresh_dir = Path(tempfile.mkdtemp())
        try:
            fresh = _reload_with_data_dir(fresh_dir)
            with fresh._connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM sorter_rules").fetchone()[0]
            self.assertEqual(count, 0)
        finally:
            import shutil
            shutil.rmtree(fresh_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
