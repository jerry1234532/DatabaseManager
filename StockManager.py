# stock_manager.py
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class StockManager:
    """
    Manages stock items and persists them to a JSON file.

    Each item looks like:
    {
        "id": int,
        "name": str,
        "quantity": int,
        "unit_price": float
    }
    """

    def __init__(self, filepath: str = "data/stock.json"):
        self.filepath = Path(filepath)
        self.items: List[Dict] = []
        self._load()

    # ---------- internal helpers ----------

    def _load(self) -> None:
        """Load items from JSON file (if it exists)."""
        if not self.filepath.exists():
            self.items = []
            return

        with self.filepath.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

        # Ensure it's a list and provide defaults for new fields
        if isinstance(data, list):
            self.items = data
        else:
            self.items = []

        # Ensure backwards compatibility: provide missing fields
        now_iso = datetime.now().isoformat()
        for item in self.items:
            if "type" not in item:
                item["type"] = ""
            if "date_added" not in item:
                item["date_added"] = now_iso

    def _save(self) -> None:
        """Save current items to JSON file."""
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        with self.filepath.open("w", encoding="utf-8") as f:
            json.dump(self.items, f, indent=2)

    def _next_id(self) -> int:
        """Generate the next integer ID."""
        return max((item["id"] for item in self.items), default=0) + 1

    def _find_index_by_id(self, item_id: int) -> Optional[int]:
        for idx, item in enumerate(self.items):
            if item["id"] == item_id:
                return idx
        return None

    # ---------- public API ----------

    def get_all(self) -> List[Dict]:
        """Return a copy of all items."""
        return list(self.items)

    def add_item(self, name: str, quantity: int, unit_price: float, item_type: str = "") -> Dict:
        """Add a new stock item and save to file."""
        new_item = {
            "id": self._next_id(),
            "name": name,
            "quantity": int(quantity),
            "unit_price": float(unit_price),
            "type": item_type,
            "date_added": datetime.now().isoformat(),
        }
        self.items.append(new_item)
        self._save()
        return new_item

    def update_item(self, item_id: int, **fields) -> Dict:
        """
        Update fields of an item by id, e.g.:
        manager.update_item(3, quantity=20, unit_price=1.99)
        """
        idx = self._find_index_by_id(item_id)
        if idx is None:
            raise KeyError(f"No item with id {item_id}")

        self.items[idx].update(fields)
        self._save()
        return self.items[idx]

    def delete_item(self, item_id: int) -> None:
        """Delete an item by id."""
        idx = self._find_index_by_id(item_id)
        if idx is None:
            raise KeyError(f"No item with id {item_id}")

        del self.items[idx]
        self._save()

    def get_item(self, item_id: int) -> Optional[Dict]:
        """Return a single item by id (or None if not found)."""
        idx = self._find_index_by_id(item_id)
        return self.items[idx] if idx is not None else None
