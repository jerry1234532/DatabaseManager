import tkinter as tk
from tkinter import ttk, messagebox

from StockManager import StockManager   # your previous class


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Business System - Main Menu")
        self.geometry("400x250")

        # You can share managers across windows if you like
        self.stock_manager = StockManager("data/stock.json")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Main Menu", font=("Arial", 16)).pack(pady=10)

        ttk.Button(
            frame,
            text="Stock Manager",
            command=self.open_stock_window
        ).pack(fill="x", pady=5)

        ttk.Button(
            frame,
            text="Orders (todo)",
            command=self.open_orders_window
        ).pack(fill="x", pady=5)

        ttk.Button(
            frame,
            text="Payments (todo)",
            command=self.open_payments_window
        ).pack(fill="x", pady=5)

        ttk.Separator(frame).pack(fill="x", pady=10)

        ttk.Button(frame, text="Quit", command=self.destroy).pack(pady=5)

    # --------- button callbacks ----------

    def open_stock_window(self):
        StockApp(self, self.stock_manager)

    def open_orders_window(self):
        messagebox.showinfo("Orders", "Orders window not implemented yet.", parent=self)

    def open_payments_window(self):
        messagebox.showinfo("Payments", "Payments window not implemented yet.", parent=self)
    






class StockApp(tk.Toplevel):
    def __init__(self, parent, manager: StockManager):
        super().__init__(parent)
        self.transient(parent)
        self.title("RIG PC Stock Manager V0.1")
        self.geometry("700x400")

        # Use the shared manager passed from the main menu
        self.stock_manager = manager

        self._build_ui()
        self._build_context_menu()
        self._load_items_into_tree()

    def _build_ui(self):
        # Treeview
        columns = ("id", "name", "quantity", "unit_price")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click bindings
        self.tree.bind("<Button-3>", self._on_right_click)  # Windows/Linux
        self.tree.bind("<Button-2>", self._on_right_click)  # macOS (often middle/right)

        # Add-item form
        form = ttk.Frame(self)
        form.pack(fill="x", padx=10, pady=5)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Quantity").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Unit price").grid(row=0, column=4, padx=5, pady=2, sticky="e")

        self.name_var = tk.StringVar()
        self.qty_var = tk.StringVar()
        self.price_var = tk.StringVar()

        ttk.Entry(form, textvariable=self.name_var, width=20).grid(row=0, column=1, padx=5)
        ttk.Entry(form, textvariable=self.qty_var, width=10).grid(row=0, column=3, padx=5)
        ttk.Entry(form, textvariable=self.price_var, width=10).grid(row=0, column=5, padx=5)

        ttk.Button(form, text="Add item", command=self.on_add_item).grid(
            row=0, column=6, padx=10
        )

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit item", command=self.on_edit_item)
        self.context_menu.add_command(label="Delete item", command=self.on_delete_item)

    def _on_right_click(self, event):
        # Identify row under cursor
        row_id = self.tree.identify_row(event.y)
        if row_id:
            # Select the row
            self.tree.selection_set(row_id)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _load_items_into_tree(self):
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert rows from StockManager
        for item in self.stock_manager.get_all():
            self.tree.insert(
                "",
                "end",
                values=(item["id"], item["name"], item["quantity"], item["unit_price"]),
            )

    def on_add_item(self):
        name = self.name_var.get().strip()
        qty_text = self.qty_var.get().strip()
        price_text = self.price_var.get().strip()

        if not name or not qty_text or not price_text:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            qty = int(qty_text)
            price = float(price_text)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be an integer and price a number.")
            return

        self.stock_manager.add_item(name, qty, price)

        self.name_var.set("")
        self.qty_var.set("")
        self.price_var.set("")
        self._load_items_into_tree()

    # --------- context menu callbacks ---------

    def _get_selected_item_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        # ID is in the first column (index 0)
        return int(item["values"][0])

    def on_delete_item(self):
        item_id = self._get_selected_item_id()
        if item_id is None:
            return

        if not messagebox.askyesno("Delete", "Are you sure you want to delete this item?"):
            return

        try:
            self.stock_manager.delete_item(item_id)
        except KeyError:
            messagebox.showerror("Error", "Item no longer exists.")
        self._load_items_into_tree()

    def on_edit_item(self):
        item_id = self._get_selected_item_id()
        if item_id is None:
            return

        item = self.stock_manager.get_item(item_id)
        if not item:
            messagebox.showerror("Error", "Item not found.")
            return

        # Open edit dialog
        EditItemDialog(self, self.stock_manager, item, on_saved=self._load_items_into_tree)


# --------- Edit dialog window ---------

class EditItemDialog(tk.Toplevel):
    def __init__(self, parent, manager: StockManager, item: dict, on_saved):
        super().__init__(parent)
        self.title(f"Edit item #{item['id']}")
        self.manager = manager
        self.item = item
        self.on_saved = on_saved

        self.transient(parent)  # stay on top of parent
        self.grab_set()         # modal

        self.name_var = tk.StringVar(value=item["name"])
        self.qty_var = tk.StringVar(value=str(item["quantity"]))
        self.price_var = tk.StringVar(value=str(item["unit_price"]))

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.name_var, width=25).grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.qty_var, width=10).grid(row=1, column=1, pady=5, sticky="w")

        ttk.Label(frame, text="Unit price:").grid(row=2, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.price_var, width=10).grid(row=2, column=1, pady=5, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

        self.resizable(False, False)
        self.focus()

    def _save(self):
        name = self.name_var.get().strip()
        qty_text = self.qty_var.get().strip()
        price_text = self.price_var.get().strip()

        if not name or not qty_text or not price_text:
            messagebox.showerror("Error", "Please fill in all fields.", parent=self)
            return

        try:
            qty = int(qty_text)
            price = float(price_text)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be an integer and price a number.", parent=self)
            return

        try:
            self.manager.update_item(
                self.item["id"],
                name=name,
                quantity=qty,
                unit_price=price,
            )
        except KeyError:
            messagebox.showerror("Error", "Item no longer exists.", parent=self)
            self.destroy()
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
