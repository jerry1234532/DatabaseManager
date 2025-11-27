# order_manager.py
import json
from pathlib import Path
from typing import List, Dict, Optional


class OrderManager:
    """
    Manages:
      - sales / talks  (kind = "sale")
      - parts orders   (kind = "parts")

    Each order:
    {
        "id": int,
        "kind": "sale" | "parts",
        "title": str,        # short description
        "contact": str,      # customer or supplier
        "from_where": str,   # where parts came from / who you spoke to
        "by_who": str,       # which staff member
        "date": str,         # e.g. "2025-01-31"
        "status": str,       # "open", "ordered", "received", "won", etc.
        "notes": str
    }
    """

    def __init__(self, filename: str = "orders.json"):
        # data/ folder next to script or exe
        base_dir = Path(".").resolve()
        data_dir = base_dir / "data"
        data_dir.mkdir(exist_ok=True)

        self.filepath: Path = data_dir / filename
        self.orders: List[Dict] = []
        self._load()

    # ---------- internal helpers ----------

    def _load(self) -> None:
        if not self.filepath.exists():
            self.orders = []
            return

        try:
            with self.filepath.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

        self.orders = data if isinstance(data, list) else []

    def _save(self) -> None:
        self.filepath.parent.mkdir(exist_ok=True, parents=True)
        with self.filepath.open("w", encoding="utf-8") as f:
            json.dump(self.orders, f, indent=2)

    def _next_id(self) -> int:
        return max((o["id"] for o in self.orders), default=0) + 1

    def _find_index(self, order_id: int) -> Optional[int]:
        for i, o in enumerate(self.orders):
            if o["id"] == order_id:
                return i
        return None

    # ---------- public API ----------

    def get_all(self) -> List[Dict]:
        return list(self.orders)

    def get_by_kind(self, kind: str) -> List[Dict]:
        kind = kind.lower()
        return [o for o in self.orders if o.get("kind") == kind]

    def add_order(
        self,
        kind: str,       # "sale" or "parts"
        title: str,
        contact: str,
        from_where: str,
        by_who: str,
        date: str,
        status: str,
        notes: str = "",
    ) -> Dict:
        order = {
            "id": self._next_id(),
            "kind": kind.lower(),
            "title": title,
            "contact": contact,
            "from_where": from_where,
            "by_who": by_who,
            "date": date,
            "status": status,
            "notes": notes,
        }
        self.orders.append(order)
        self._save()
        return order

    def update_order(self, order_id: int, **fields) -> Dict:
        idx = self._find_index(order_id)
        if idx is None:
            raise KeyError(f"No order with id {order_id}")
        self.orders[idx].update(fields)
        self._save()
        return self.orders[idx]

    def delete_order(self, order_id: int) -> None:
        idx = self._find_index(order_id)
        if idx is None:
            raise KeyError(f"No order with id {order_id}")
        del self.orders[idx]
        self._save()

    def get_order(self, order_id: int) -> Optional[Dict]:
        idx = self._find_index(order_id)
        return self.orders[idx] if idx is not None else None
