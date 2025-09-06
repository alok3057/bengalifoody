#https://chatgpt.com/c/68bbec0e-4104-8323-8c4b-2480aade70e7
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

DB_FILE = "zomato_app.db"
ADMIN_PASSWORD = "admin123"


class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        # Create table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                available TEXT DEFAULT 'Yes',
                image_path TEXT
            )
        """)
        self.conn.commit()

        # --- Migration: check missing columns ---
        cur.execute("PRAGMA table_info(menu_items)")
        cols = [row[1] for row in cur.fetchall()]
        if "image_path" not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN image_path TEXT")
            self.conn.commit()
        if "available" not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN available TEXT DEFAULT 'Yes'")
            self.conn.commit()

        # Orders table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
        """)
        self.conn.commit()

        # Order items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_id INTEGER,
                qty INTEGER,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(item_id) REFERENCES menu_items(id)
            )
        """)
        self.conn.commit()

        # Seed sample items if empty
        cur.execute("SELECT COUNT(*) FROM menu_items")
        if cur.fetchone()[0] == 0:
            sample_items = [
                ("Crispy Salted Fries", "Crispy and salty potato fries", 2.49, "Yes", ""),
                ("Grilled Veg Patty", "Grilled veg patty with lettuce & sauce", 3.99, "Yes", ""),
                ("Paneer Curry", "Creamy paneer curry with naan", 5.49, "Yes", ""),
                ("Cheese Pizza", "Classic cheese & tomato pizza", 6.99, "Yes", ""),
            ]
            cur.executemany("INSERT INTO menu_items (name, description, price, available, image_path) VALUES (?, ?, ?, ?, ?)", sample_items)
            self.conn.commit()

    def get_menu_items(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, description, price, available, image_path FROM menu_items WHERE available='Yes'")
        return cur.fetchall()

    def add_menu_item(self, name, description, price, available, image_path):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO menu_items (name, description, price, available, image_path) VALUES (?, ?, ?, ?, ?)",
                    (name, description, price, available, image_path))
        self.conn.commit()

    def get_orders(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, created, total FROM orders ORDER BY created DESC")
        return cur.fetchall()

    def get_order_items(self, order_id):
        cur = self.conn.cursor()
        cur.execute("SELECT m.name, oi.qty, m.price FROM order_items oi JOIN menu_items m ON oi.item_id=m.id WHERE order_id=?", (order_id,))
        return cur.fetchall()

    def save_order(self, cart):
        cur = self.conn.cursor()
        total = sum(item['price'] * item['qty'] for item in cart)
        cur.execute("INSERT INTO orders (total) VALUES (?)", (total,))
        order_id = cur.lastrowid
        for item in cart:
            cur.execute("INSERT INTO order_items (order_id, item_id, qty) VALUES (?, ?, ?)",
                        (order_id, item['id'], item['qty']))
        self.conn.commit()
        return order_id


class ZomatoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Foody Bengali")
        self.title("Click Me 9831316751")
        self.geometry("900x600")
        self.configure(bg="#f8f8f8")

        self.db = Database()
        self.cart = []

        self.create_widgets()

    def create_widgets(self):
        nav_frame = tk.Frame(self, bg="#e23744")
        nav_frame.pack(side="top", fill="x")

        tk.Label(nav_frame, text="🍴Foodi Bengali", bg="#e23744", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)

        tk.Label(nav_frame, text="Call Me 9831316751", bg="#e23744", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=25)


        tk.Button(nav_frame, text="Menu", command=self.show_menu_frame, bg="white",
                  fg="#e23744").pack(side="left", padx=5, pady=5)
        tk.Button(nav_frame, text=f"Cart (0)", command=self.show_cart_frame, bg="white",
                  fg="#e23744").pack(side="left", padx=5, pady=5)
        tk.Button(nav_frame, text="Orders", command=self.show_orders_frame, bg="white",
                  fg="#e23744").pack(side="left", padx=5, pady=5)

        self.admin_btn = tk.Button(nav_frame, text="Admin", command=self.admin_login, bg="white",
                                   fg="#e23744")
        self.admin_btn.pack(side="right", padx=5, pady=5)

        self.container = tk.Frame(self, bg="#f8f8f8")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (MenuFrame, CartFrame, OrdersFrame, AdminFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_menu_frame()

    def show_menu_frame(self):
        self.frames[MenuFrame].refresh()
        self.frames[MenuFrame].tkraise()

    def show_cart_frame(self):
        self.frames[CartFrame].refresh()
        self.frames[CartFrame].tkraise()

    def show_orders_frame(self):
        self.frames[OrdersFrame].refresh()
        self.frames[OrdersFrame].tkraise()

    def show_admin_frame(self):
        self.frames[AdminFrame].refresh()
        self.frames[AdminFrame].tkraise()

    def admin_login(self):
        win = tk.Toplevel(self)
        win.title("Admin Login")
        tk.Label(win, text="Enter Admin Password:").pack(pady=5)
        pwd_entry = tk.Entry(win, show="*")
        pwd_entry.pack(pady=5)

        def check_pwd():
            if pwd_entry.get() == ADMIN_PASSWORD:
                win.destroy()
                self.show_admin_frame()
            else:
                messagebox.showerror("Error", "Invalid password")

        tk.Button(win, text="Login", command=check_pwd).pack(pady=5)


class MenuFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.canvas = tk.Canvas(self, bg="white")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def refresh(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        items = self.app.db.get_menu_items()
        for item in items:
            iid, name, desc, price, available, image_path = item
            frame = tk.Frame(self.scrollable_frame, bd=1, relief="solid", bg="white")
            frame.pack(fill="x", pady=5, padx=10)

            # Load image if available
            if image_path and os.path.exists(image_path):
                try:
                    if PIL_AVAILABLE:
                        img = Image.open(image_path).resize((80, 80))
                        photo = ImageTk.PhotoImage(img)
                    else:
                        photo = tk.PhotoImage(file=image_path)
                    img_label = tk.Label(frame, image=photo, bg="white")
                    img_label.image = photo
                    img_label.pack(side="left", padx=5, pady=5)
                except Exception:
                    pass

            info = tk.Frame(frame, bg="white")
            info.pack(side="left", fill="both", expand=True)
            tk.Label(info, text=name, font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
            tk.Label(info, text=desc, font=("Arial", 10), bg="white").pack(anchor="w")
            tk.Label(info, text=f"₹{price:.2f}", font=("Arial", 10, "bold"), fg="#e23744", bg="white").pack(anchor="w")

            tk.Button(frame, text="Add to Cart", bg="#e23744", fg="white",
                      command=lambda i=item: self.add_to_cart(i)).pack(side="right", padx=10, pady=10)

    def add_to_cart(self, item):
        iid, name, desc, price, available, image_path = item
        for it in self.app.cart:
            if it['id'] == iid:
                it['qty'] += 1
                break
        else:
            self.app.cart.append({'id': iid, 'name': name, 'price': price, 'qty': 1})
        self.app.admin_btn.config(text=f"Cart ({len(self.app.cart)})")
        messagebox.showinfo("Cart", f"{name} added to cart")


class CartFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.text = tk.Text(self, state="disabled")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Place Order", command=self.place_order, bg="#e23744", fg="white").pack(pady=10)

    def refresh(self):
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        total = 0
        for it in self.app.cart:
            subtotal = it['price'] * it['qty']
            total += subtotal
            self.text.insert(tk.END, f"{it['name']} x{it['qty']} = ₹{subtotal:.2f}\n")
        self.text.insert(tk.END, f"\nTotal: ₹{total:.2f}")
        self.text.config(state="disabled")

    def place_order(self):
        if not self.app.cart:
            messagebox.showwarning("Empty", "Your cart is empty!")
            return
        self.app.db.save_order(self.app.cart)
        self.app.cart.clear()
        messagebox.showinfo("Order Placed", "Your order has been placed successfully!")
        self.refresh()


class OrdersFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.orders_list = tk.Listbox(self)
        self.orders_list.pack(side="left", fill="y", padx=10, pady=10)
        self.orders_list.bind("<<ListboxSelect>>", self.on_select)

        self.order_detail = tk.Text(self, state="disabled")
        self.order_detail.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh(self):
        self.orders_list.delete(0, tk.END)
        orders = self.app.db.get_orders()
        for oid, created, total in orders:
            self.orders_list.insert(tk.END, f"Order {oid} - {created[:16]} - ₹{total:.2f}")

    def on_select(self, event):
        sel = self.orders_list.curselection()
        if not sel:
            return
        oid = int(self.orders_list.get(sel[0]).split()[1])
        items = self.app.db.get_order_items(oid)
        self.order_detail.config(state="normal")
        self.order_detail.delete("1.0", tk.END)
        total = 0
        for name, qty, price in items:
            subtotal = price * qty
            total += subtotal
            self.order_detail.insert(tk.END, f"{name} x{qty} = ₹{subtotal:.2f}\n")
        self.order_detail.insert(tk.END, f"\nTotal: ₹{total:.2f}")
        self.order_detail.config(state="disabled")


class AdminFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app

        btns = tk.Frame(self, bg="white")
        btns.pack(fill="x", pady=10)
        tk.Button(btns, text="Add Item", command=self.add_item, bg="#e23744", fg="white").pack(side="left", padx=5)
        self.tree = ttk.Treeview(self, columns=("Price", "Available", "Description", "Image"), show="headings")
        for col in ("Price", "Available", "Description", "Image"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        items = self.app.db.get_menu_items()
        for iid, name, desc, price, available, image_path in items:
            self.tree.insert("", "end", values=(f"₹{price:.2f}", available, desc, image_path or ""))

    def add_item(self):
        win = tk.Toplevel(self)
        win.title("Add Menu Item")
        tk.Label(win, text="Name").pack()
        name_entry = tk.Entry(win)
        name_entry.pack()
        tk.Label(win, text="Description").pack()
        desc_entry = tk.Entry(win)
        desc_entry.pack()
        tk.Label(win, text="Price").pack()
        price_entry = tk.Entry(win)
        price_entry.pack()
        tk.Label(win, text="Available (Yes/No)").pack()
        avail_entry = tk.Entry(win)
        avail_entry.insert(0, "Yes")
        avail_entry.pack()
        tk.Label(win, text="Image Path").pack()
        img_path_var = tk.StringVar()
        tk.Entry(win, textvariable=img_path_var).pack()
        tk.Button(win, text="Browse", command=lambda: img_path_var.set(filedialog.askopenfilename())).pack()

        def save_item():
            try:
                self.app.db.add_menu_item(
                    name_entry.get(),
                    desc_entry.get(),
                    float(price_entry.get()),
                    avail_entry.get(),
                    img_path_var.get()
                )
                win.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(win, text="Save", command=save_item, bg="#e23744", fg="white").pack(pady=5)


if __name__ == "__main__":
    app = ZomatoApp()
    app.mainloop()
