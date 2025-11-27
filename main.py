import tkinter as tk
from tkinter import ttk, messagebox

from OrderManager import OrderManager      # DATA manager (JSON etc.)
from StockManager import StockManager      # DATA manager for stock


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Business System - Main Menu")
        self.geometry("400x250")

        # shared managers
        self.stock_manager = StockManager("data/stock.json")
        self.order_manager = OrderManager()   # <--- create this!

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
            text="Orders / Sales Manager",
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
        # open orders window (GUI), pass in the shared OrderManager
        OrdersWindow(self, self.order_manager)

    def open_payments_window(self):
        messagebox.showinfo("Payments", "Payments window not implemented yet.", parent=self)


# ================== STOCK WINDOW ==================

class StockApp(tk.Toplevel):
    def __init__(self, parent, manager: StockManager):
        super().__init__(parent)
        self.transient(parent)
        self.title("RIG PC Stock Manager V0.1")
        self.geometry("700x400")

        # Use the shared manager passed from the main menu
        self.stock_manager = manager
        # Predefined choices for item `type`
        self.type_choices = ["Motherboard", "CPU", "GPU", "RAM", "PSU", "Storage", "Accessory", "Other"]

        self._build_ui()
        self._build_context_menu()
        self._load_items_into_tree()

    def _build_ui(self):
        # Treeview
        columns = ("id", "type", "name", "quantity", "unit_price", "date_added")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").capitalize())
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click bindings
        self.tree.bind("<Button-3>", self._on_right_click)  # Windows/Linux
        self.tree.bind("<Button-2>", self._on_right_click)  # macOS (middle/right)

        # Add-item form
        form = ttk.Frame(self)
        form.pack(fill="x", padx=10, pady=5)

        # Layout: Type | Name | Quantity | Unit price | Add button
        ttk.Label(form, text="Type").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Name").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Quantity").grid(row=0, column=4, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Unit price").grid(row=0, column=6, padx=5, pady=2, sticky="e")

        self.type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.qty_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            values=self.type_choices,
            width=12,
            state="readonly",
        )
        self.type_combo.grid(row=0, column=1, padx=5)
        ttk.Entry(form, textvariable=self.name_var, width=25).grid(row=0, column=3, padx=5)
        ttk.Entry(form, textvariable=self.qty_var, width=8).grid(row=0, column=5, padx=5)
        ttk.Entry(form, textvariable=self.price_var, width=10).grid(row=0, column=7, padx=5)

        ttk.Button(form, text="Add item", command=self.on_add_item).grid(row=0, column=8, padx=10)

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
                values=(
                    item.get("id"),
                    item.get("type", ""),
                    item.get("name", ""),
                    item.get("quantity", ""),
                    item.get("unit_price", ""),
                    item.get("date_added", ""),
                ),
            )

    def on_add_item(self):
        item_type = self.type_var.get().strip()
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

        self.stock_manager.add_item(name, qty, price, item_type=item_type)

        self.type_var.set("")
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

        self.type_var = tk.StringVar(value=item.get("type", ""))
        self.name_var = tk.StringVar(value=item.get("name", ""))
        self.qty_var = tk.StringVar(value=str(item.get("quantity", "")))
        self.price_var = tk.StringVar(value=str(item.get("unit_price", "")))
        self.date_var = tk.StringVar(value=item.get("date_added", ""))

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Type:").grid(row=0, column=0, sticky="e", pady=5)
        # Use parent's predefined choices for type (parent is StockApp)
        self.type_combo = ttk.Combobox(
            frame,
            textvariable=self.type_var,
            width=25,
            values=parent.type_choices,
            state="readonly"
        )
        self.type_combo.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.name_var, width=25).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Quantity:").grid(row=2, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.qty_var, width=10).grid(row=2, column=1, pady=5, sticky="w")

        ttk.Label(frame, text="Unit price:").grid(row=3, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.price_var, width=10).grid(row=3, column=1, pady=5, sticky="w")

        ttk.Label(frame, text="Date added:").grid(row=4, column=0, sticky="e", pady=5)
        ttk.Entry(frame, textvariable=self.date_var, width=25, state="readonly").grid(row=4, column=1, pady=5, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

        self.resizable(False, False)
        self.focus()

    def _save(self):
        name = self.name_var.get().strip()
        item_type = self.type_var.get().strip()
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
                type=item_type,
            )
        except KeyError:
            messagebox.showerror("Error", "Item no longer exists.", parent=self)
            self.destroy()
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()


# ================== ORDERS WINDOW ==================

class OrdersWindow(tk.Toplevel):
    def __init__(self, parent, order_manager: OrderManager):
        super().__init__(parent)
        self.title("Order / Sales Manager")
        self.geometry("900x400")

        self.order_manager = order_manager

        self._build_ui()
        self._load_orders()

        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Label(top, text="View:").pack(side="left")
        self.filter_var = tk.StringVar(value="all")
        filter_box = ttk.Combobox(
            top,
            textvariable=self.filter_var,
            values=["all", "sale", "parts"],
            width=10,
            state="readonly",
        )
        filter_box.pack(side="left", padx=5)
        filter_box.bind("<<ComboboxSelected>>", lambda e: self._load_orders())

        # Treeview
        columns = (
            "id",
            "kind",
            "title",
            "contact",
            "from_where",
            "by_who",
            "date",
            "status",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Simple form to add new order
        form = ttk.LabelFrame(self, text="Add new order")
        form.pack(fill="x", padx=10, pady=5)

        # row 0
        ttk.Label(form, text="Type").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Title").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Contact").grid(row=0, column=4, padx=5, pady=2, sticky="e")

        self.kind_var = tk.StringVar(value="sale")
        self.title_var = tk.StringVar()
        self.contact_var = tk.StringVar()

        ttk.Combobox(
            form,
            textvariable=self.kind_var,
            values=["sale", "parts"],
            width=8,
            state="readonly",
        ).grid(row=0, column=1, padx=5, pady=2)

        ttk.Entry(form, textvariable=self.title_var, width=25).grid(
            row=0, column=3, padx=5, pady=2
        )
        ttk.Entry(form, textvariable=self.contact_var, width=20).grid(
            row=0, column=5, padx=5, pady=2
        )

        # row 1
        ttk.Label(form, text="From where").grid(
            row=1, column=0, padx=5, pady=2, sticky="e"
        )
        ttk.Label(form, text="By who").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(
            row=1, column=4, padx=5, pady=2, sticky="e"
        )

        self.from_where_var = tk.StringVar()
        self.by_who_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="open")

        ttk.Entry(form, textvariable=self.from_where_var, width=20).grid(
            row=1, column=1, padx=5, pady=2
        )
        ttk.Entry(form, textvariable=self.by_who_var, width=20).grid(
            row=1, column=3, padx=5, pady=2
        )
        ttk.Entry(form, textvariable=self.date_var, width=12).grid(
            row=1, column=5, padx=5, pady=2
        )

        # row 2
        ttk.Label(form, text="Status").grid(
            row=2, column=0, padx=5, pady=2, sticky="e"
        )
        ttk.Label(form, text="Notes").grid(
            row=2, column=2, padx=5, pady=2, sticky="e"
        )

        self.notes_var = tk.StringVar()

        ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=["open", "in_talks", "ordered", "received", "won", "lost", "closed"],
            width=12,
            state="readonly",
        ).grid(row=2, column=1, padx=5, pady=2)

        ttk.Entry(form, textvariable=self.notes_var, width=40).grid(
            row=2, column=3, columnspan=3, padx=5, pady=2, sticky="w"
        )

        ttk.Button(form, text="Add", command=self.on_add).grid(
            row=0, column=6, rowspan=3, padx=10
        )

    def _load_orders(self):
        # Clear
        for row in self.tree.get_children():
            self.tree.delete(row)

        filt = self.filter_var.get()
        if filt == "sale":
            orders = self.order_manager.get_by_kind("sale")
        elif filt == "parts":
            orders = self.order_manager.get_by_kind("parts")
        else:
            orders = self.order_manager.get_all()

        for o in orders:
            self.tree.insert(
                "",
                "end",
                values=(
                    o["id"],
                    o["kind"],
                    o["title"],
                    o["contact"],
                    o["from_where"],
                    o["by_who"],
                    o["date"],
                    o["status"],
                ),
            )

    def on_add(self):
        title = self.title_var.get().strip()
        kind = self.kind_var.get().strip()
        contact = self.contact_var.get().strip()
        from_where = self.from_where_var.get().strip()
        by_who = self.by_who_var.get().strip()
        date = self.date_var.get().strip()
        status = self.status_var.get().strip()
        notes = self.notes_var.get().strip()

        if not title:
            messagebox.showerror("Error", "Title is required.", parent=self)
            return

        self.order_manager.add_order(
            kind=kind,
            title=title,
            contact=contact,
            from_where=from_where,
            by_who=by_who,
            date=date,
            status=status,
            notes=notes,
        )

        # clear fields & reload list
        self.title_var.set("")
        self.contact_var.set("")
        self.from_where_var.set("")
        self.by_who_var.set("")
        self.date_var.set("")
        self.notes_var.set("")
        self._load_orders()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()

