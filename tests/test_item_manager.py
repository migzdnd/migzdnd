import tempfile
import unittest

from item_manager import ItemManager


class ItemManagerTests(unittest.TestCase):
    def test_add_and_remove(self):
        manager = ItemManager(size=2)
        overflow = manager.add_item("iron_ingot", 150, max_stack=64)
        self.assertEqual(overflow, 22)
        self.assertEqual(manager.count("iron_ingot"), 128)

        removed = manager.remove_item("iron_ingot", 70)
        self.assertEqual(removed, 70)
        self.assertEqual(manager.count("iron_ingot"), 58)

    def test_compact_and_sort(self):
        manager = ItemManager(size=5)
        manager.add_item("zeta", 10, max_stack=64)
        manager.add_item("alpha", 4, max_stack=64)
        manager.add_item("alpha", 5, max_stack=64)
        manager.compact()
        manager.sort("name")

        stacks = [s for s in manager.slots if s]
        self.assertEqual(stacks[0].item_id, "alpha")
        self.assertEqual(stacks[0].quantity, 9)
        self.assertEqual(stacks[1].item_id, "zeta")

    def test_preset_and_persistence(self):
        manager = ItemManager(size=4)
        manager.add_item("wood", 16)
        manager.save_preset("build")
        manager.remove_item("wood", 16)

        manager.load_preset("build")
        self.assertEqual(manager.count("wood"), 16)

        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            manager.to_json(tf.name)
            loaded = ItemManager.from_json(tf.name)
            self.assertEqual(loaded.count("wood"), 16)
            self.assertIn("build", loaded.quick_presets)


if __name__ == "__main__":
    unittest.main()
