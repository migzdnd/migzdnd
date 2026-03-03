"""Hytale-style Item Manager clone.

This module provides a lightweight inventory management engine inspired by
item-management plugins used in sandbox games.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ItemStack:
    """Represents a stack of one item type."""

    item_id: str
    quantity: int
    max_stack: int = 64
    metadata: Dict[str, str] = field(default_factory=dict)

    def add(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        free = self.max_stack - self.quantity
        added = min(amount, free)
        self.quantity += added
        return amount - added

    def remove(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        removed = min(amount, self.quantity)
        self.quantity -= removed
        return removed

    @property
    def is_empty(self) -> bool:
        return self.quantity <= 0


@dataclass
class ItemManager:
    """Inventory manager with searching, sorting, grouping, and presets."""

    size: int = 54
    slots: List[Optional[ItemStack]] = field(default_factory=list)
    quick_presets: Dict[str, List[Optional[ItemStack]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.slots:
            self.slots = [None for _ in range(self.size)]
        if len(self.slots) != self.size:
            raise ValueError("slots length must equal size")

    def add_item(self, item_id: str, amount: int, max_stack: int = 64, metadata: Optional[Dict[str, str]] = None) -> int:
        """Add items and return amount that could not fit."""
        if amount < 0:
            raise ValueError("amount must be non-negative")
        metadata = metadata or {}
        remaining = amount

        # Fill existing stacks first.
        for slot in self.slots:
            if slot and slot.item_id == item_id and slot.max_stack == max_stack and slot.metadata == metadata:
                remaining = slot.add(remaining)
                if remaining == 0:
                    return 0

        # Create new stacks in empty slots.
        for idx, slot in enumerate(self.slots):
            if slot is None:
                to_add = min(remaining, max_stack)
                self.slots[idx] = ItemStack(item_id=item_id, quantity=to_add, max_stack=max_stack, metadata=dict(metadata))
                remaining -= to_add
                if remaining == 0:
                    return 0

        return remaining

    def remove_item(self, item_id: str, amount: int) -> int:
        """Remove up to amount of item_id and return removed amount."""
        if amount < 0:
            raise ValueError("amount must be non-negative")
        target = amount
        removed = 0
        for idx, slot in enumerate(self.slots):
            if slot and slot.item_id == item_id:
                take = slot.remove(target)
                removed += take
                target -= take
                if slot.is_empty:
                    self.slots[idx] = None
                if target == 0:
                    break
        return removed

    def count(self, item_id: str) -> int:
        return sum(slot.quantity for slot in self.slots if slot and slot.item_id == item_id)

    def search(self, query: str) -> List[ItemStack]:
        needle = query.lower().strip()
        return [slot for slot in self.slots if slot and needle in slot.item_id.lower()]

    def compact(self) -> None:
        """Merge matching stacks then move all non-empty stacks to the front."""
        grouped: Dict[tuple, int] = {}
        for slot in self.slots:
            if slot:
                key = (slot.item_id, slot.max_stack, tuple(sorted(slot.metadata.items())))
                grouped[key] = grouped.get(key, 0) + slot.quantity

        packed: List[Optional[ItemStack]] = []
        for (item_id, max_stack, metadata_items), quantity in grouped.items():
            metadata = dict(metadata_items)
            while quantity > 0:
                take = min(quantity, max_stack)
                packed.append(ItemStack(item_id=item_id, quantity=take, max_stack=max_stack, metadata=metadata))
                quantity -= take

        packed.sort(key=lambda stack: (stack.item_id, -stack.quantity))
        self.slots = packed + [None for _ in range(self.size - len(packed))]

    def sort(self, mode: str = "name") -> None:
        stacks = [slot for slot in self.slots if slot]
        if mode == "name":
            stacks.sort(key=lambda s: (s.item_id.lower(), -s.quantity))
        elif mode == "amount":
            stacks.sort(key=lambda s: (-s.quantity, s.item_id.lower()))
        else:
            raise ValueError("mode must be 'name' or 'amount'")
        self.slots = stacks + [None for _ in range(self.size - len(stacks))]

    def save_preset(self, name: str) -> None:
        self.quick_presets[name] = [None if slot is None else ItemStack(**self._stack_to_dict(slot)) for slot in self.slots]

    def load_preset(self, name: str) -> None:
        if name not in self.quick_presets:
            raise KeyError(f"Unknown preset: {name}")
        self.slots = [None if slot is None else ItemStack(**self._stack_to_dict(slot)) for slot in self.quick_presets[name]]

    def to_json(self, path: str | Path) -> None:
        payload = {
            "size": self.size,
            "slots": [None if slot is None else self._stack_to_dict(slot) for slot in self.slots],
            "quick_presets": {
                name: [None if slot is None else self._stack_to_dict(slot) for slot in slots]
                for name, slots in self.quick_presets.items()
            },
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "ItemManager":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        manager = cls(size=payload["size"])
        manager.slots = [None if slot is None else ItemStack(**slot) for slot in payload["slots"]]
        manager.quick_presets = {
            name: [None if slot is None else ItemStack(**slot) for slot in slots]
            for name, slots in payload.get("quick_presets", {}).items()
        }
        return manager

    @staticmethod
    def _stack_to_dict(stack: ItemStack) -> Dict[str, object]:
        return {
            "item_id": stack.item_id,
            "quantity": stack.quantity,
            "max_stack": stack.max_stack,
            "metadata": dict(stack.metadata),
        }
