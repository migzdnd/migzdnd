# Hytale Item Manager (Replica)

This repository provides a clean-room replica of an **Item Manager** style plugin behavior for Hytale-like inventories.

## Included features

- Stack-aware item insertion/removal with overflow handling.
- Item counting and fuzzy search by item id.
- Inventory compacting (merge similar stacks and pack to front).
- Sorting by item name or stack amount.
- Quick presets to save/restore loadouts.
- JSON persistence for inventory and presets.

## Project layout

- `item_manager.py` – core item manager engine.
- `tests/test_item_manager.py` – unit tests.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Example

```python
from item_manager import ItemManager

manager = ItemManager(size=9)
manager.add_item("iron_ingot", 70)
manager.add_item("health_potion", 5, max_stack=16)
manager.compact()
manager.save_preset("adventure")
manager.to_json("inventory.json")
```
