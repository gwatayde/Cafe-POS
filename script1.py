import json
import os
import shutil
import time
import csv
from datetime import datetime
from functools import partial

# --- IMPORTS ---
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, DictProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.list import OneLineAvatarIconListItem, ThreeLineAvatarIconListItem, IconRightWidget, IconLeftWidget
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.toast import toast

# --- IMAGE LIBRARY ---
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None
    print("Pillow library not found. Images will not be resized.")

# --- PERFORMANCE SETTING ---
Clock.max_iteration = 150

# --- FILE PATHS ---
INVENTORY_FILE = 'inventory.json'
PRODUCTS_FILE = 'products.json'
RECEIPTS_FILE = 'receipts.json'
IMAGES_FILE = 'product_images.json'
SHIFT_START_FILE = 'shift_start.json'
IMAGE_DIR = 'product_images'

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# --- UNIT CONVERSION LOGIC ---
UNIT_SIZES = {
    "Beans": 1000,
    "Milk": 1000,
    "Biscoff Spread": 1000,
    "Biscoff Crackers": 1000,
    "Condense": 1000,
    "Choco Sauce": 1000,
    "White Choco Sauce": 1000,
    "Caramel Sauce": 1000,
    "Fructose": 1000,
    "Whip Cream": 1000,
    "Hazelnut Syrup": 750,
    "Salted Caramel Syrup": 750,
    "Strawberry Syrup": 750,
    "Irish Cream Syrup": 750,
    "Vanilla Syrup": 750,
    "Caramel Syrup": 750,
    "Butterscotch Syrup": 750
}

# --- DATA CONFIGURATION ---
DEFAULT_INVENTORY = {
    "12oz Cups Hot": 100, "16oz Cups Hot": 100, "16oz Cups Iced": 100, "22oz Cups Iced": 100,
    "Strawless lid hot": 200, "Strawless lid iced": 200, "Dome lid": 100,
    "Beans": 5000, "Milk": 10000, "Fructose": 2000, "Sugar": 1000, "Water": 5000,
    "Condense": 2000, "Choco Sauce": 2000, "White Choco Sauce": 1000, "Caramel Sauce": 1000,
    "Whip Cream": 500, "Cinnamon Powder": 100, "Biscoff Spread": 500,
    "Hazelnut Syrup": 750, "Salted Caramel Syrup": 750, "Strawberry Syrup": 750,
    "Irish Cream Syrup": 750, "Vanilla Syrup": 750, "Caramel Syrup": 750, "Butterscotch Syrup": 750,
    "Biscoff Crackers": 1000
}

DEFAULT_PRODUCTS = {
    "HOT COFFEE": {
        "Americano": {"12oz": 60, "16oz": 70},
        "Cafe Latte": {"12oz": 80, "16oz": 90},
        "Cappuccino": {"12oz": 80, "16oz": 90},
        "Caramel Macchiato": {"12oz": 90, "16oz": 100},
        "Salted Caramel": {"12oz": 95, "16oz": 105},
        "Spanish Latte": {"12oz": 90, "16oz": 100},
        "Vietnamese": {"12oz": 85, "16oz": 95},
        "Choko Hazelnut": {"12oz": 95, "16oz": 105},
        "Kafe Mocha": {"12oz": 95, "16oz": 105},
        "White Mocha": {"12oz": 95, "16oz": 105},
    },
    "ICED COFFEE": {
        "Iced Americano": {"16oz": 70, "22oz": 80},
        "Iced Latte": {"16oz": 90, "22oz": 100},
        "Iced Cappuccino": {"16oz": 90, "22oz": 100},
        "Iced Caramel Macchiato": {"16oz": 100, "22oz": 110},
        "Iced Salted Caramel": {"16oz": 110, "22oz": 120},
        "Iced Spanish Latte": {"16oz": 100, "22oz": 110},
        "Iced Vietnamese": {"16oz": 95, "22oz": 105},
        "Iced Shaken Hazelnut": {"16oz": 100, "22oz": 110},
        "Biscoff Latte": {"16oz": 110, "22oz": 120},
        "Ube Espresso": {"16oz": 110, "22oz": 120},
        "Oreo Latte": {"16oz": 110, "22oz": 120},
        "Strawberry Coffee": {"16oz": 105, "22oz": 115},
    },
    "FLAVORED COFFEE": {
        "Buttered Scotch": {"12oz": 85, "16oz": 95, "22oz": 105},
        "Hazelnut": {"12oz": 85, "16oz": 95, "22oz": 105},
        "Vanilla": {"12oz": 85, "16oz": 95, "22oz": 105},
    },
    "NON-COFFEE DRINKS": {
        "Iced Choco": {"16oz": 90, "22oz": 100},
        "Strawberry Choco": {"16oz": 100, "22oz": 110},
        "Oreo Blend": {"16oz": 100, "22oz": 110},
        "Oreo Matcha": {"16oz": 110, "22oz": 120},
        "Ube Matcha": {"16oz": 110, "22oz": 120},
        "Oreo Ube": {"16oz": 110, "22oz": 120},
    }
}

RECIPES = {
    "Americano 12oz": {"Beans": 18, "Water": 200, "12oz Cups Hot": 1, "Strawless lid hot": 1},
    "Americano 16oz": {"Beans": 36, "Water": 300, "16oz Cups Hot": 1, "Strawless lid hot": 1},
    "Cafe Latte 12oz": {"Beans": 18, "Milk": 180, "12oz Cups Hot": 1, "Strawless lid hot": 1},
    "Cafe Latte 16oz": {"Beans": 36, "Milk": 200, "16oz Cups Hot": 1, "Strawless lid hot": 1},
    "Cappuccino 12oz": {"Beans": 18, "Milk": 150, "12oz Cups Hot": 1, "Strawless lid hot": 1},
    "Cappuccino 16oz": {"Beans": 36, "Milk": 180, "16oz Cups Hot": 1, "Strawless lid hot": 1},
    "Caramel Macchiato 12oz": {"Beans": 18, "Milk": 150, "Caramel Syrup": 20, "12oz Cups Hot": 1},
    "Caramel Macchiato 16oz": {"Beans": 36, "Milk": 200, "Caramel Syrup": 30, "16oz Cups Hot": 1},
    "Salted Caramel 12oz": {"Beans": 18, "Milk": 150, "Salted Caramel Syrup": 20, "12oz Cups Hot": 1},
    "Salted Caramel 16oz": {"Beans": 36, "Milk": 200, "Salted Caramel Syrup": 30, "16oz Cups Hot": 1},
    "Spanish Latte 12oz": {"Beans": 18, "Milk": 150, "Condense": 20, "12oz Cups Hot": 1},
    "Spanish Latte 16oz": {"Beans": 36, "Milk": 200, "Condense": 30, "16oz Cups Hot": 1},
    "Vietnamese 12oz": {"Beans": 18, "Water": 100, "Condense": 30, "12oz Cups Hot": 1},
    "Vietnamese 16oz": {"Beans": 36, "Water": 150, "Condense": 40, "16oz Cups Hot": 1},
    "Choko Hazelnut 12oz": {"Beans": 18, "Milk": 180, "Hazelnut Syrup": 15, "Choco Sauce": 15, "12oz Cups Hot": 1},
    "Choko Hazelnut 16oz": {"Beans": 36, "Milk": 200, "Hazelnut Syrup": 20, "Choco Sauce": 20, "16oz Cups Hot": 1},
    "Kafe Mocha 12oz": {"Beans": 18, "Milk": 180, "Choco Sauce": 20, "12oz Cups Hot": 1},
    "Kafe Mocha 16oz": {"Beans": 36, "Milk": 200, "Choco Sauce": 30, "16oz Cups Hot": 1},
    "White Mocha 12oz": {"Beans": 18, "Milk": 180, "White Choco Sauce": 20, "12oz Cups Hot": 1},
    "White Mocha 16oz": {"Beans": 36, "Milk": 200, "White Choco Sauce": 30, "16oz Cups Hot": 1},
    "Iced Americano 16oz": {"Beans": 36, "Water": 200, "16oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Americano 22oz": {"Beans": 36, "Water": 250, "22oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Latte 16oz": {"Beans": 36, "Milk": 200, "16oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Latte 22oz": {"Beans": 36, "Milk": 250, "22oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Cappuccino 16oz": {"Beans": 36, "Milk": 180, "16oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Cappuccino 22oz": {"Beans": 36, "Milk": 220, "22oz Cups Iced": 1, "Strawless lid iced": 1},
    "Iced Caramel Macchiato 16oz": {"Beans": 36, "Milk": 200, "Caramel Syrup": 30, "16oz Cups Iced": 1},
    "Iced Caramel Macchiato 22oz": {"Beans": 36, "Milk": 250, "Caramel Syrup": 40, "22oz Cups Iced": 1},
    "Iced Salted Caramel 16oz": {"Beans": 36, "Milk": 200, "Salted Caramel Syrup": 30, "16oz Cups Iced": 1},
    "Iced Salted Caramel 22oz": {"Beans": 36, "Milk": 250, "Salted Caramel Syrup": 40, "22oz Cups Iced": 1},
    "Iced Spanish Latte 16oz": {"Beans": 36, "Milk": 200, "Condense": 30, "16oz Cups Iced": 1},
    "Iced Spanish Latte 22oz": {"Beans": 36, "Milk": 250, "Condense": 40, "22oz Cups Iced": 1},
    "Iced Vietnamese 16oz": {"Beans": 36, "Water": 150, "Condense": 40, "16oz Cups Iced": 1},
    "Iced Vietnamese 22oz": {"Beans": 36, "Water": 200, "Condense": 50, "22oz Cups Iced": 1},
    "Iced Shaken Hazelnut 16oz": {"Beans": 36, "Milk": 150, "Hazelnut Syrup": 20, "16oz Cups Iced": 1},
    "Iced Shaken Hazelnut 22oz": {"Beans": 36, "Milk": 200, "Hazelnut Syrup": 30, "22oz Cups Iced": 1},
    "Biscoff Latte 16oz": {"Beans": 36, "Milk": 200, "Biscoff Spread": 20, "16oz Cups Iced": 1},
    "Biscoff Latte 22oz": {"Beans": 36, "Milk": 250, "Biscoff Spread": 30, "22oz Cups Iced": 1},
    "Ube Espresso 16oz": {"Beans": 36, "Milk": 200, "16oz Cups Iced": 1},
    "Ube Espresso 22oz": {"Beans": 36, "Milk": 250, "22oz Cups Iced": 1},
    "Oreo Latte 16oz": {"Beans": 36, "Milk": 200, "16oz Cups Iced": 1},
    "Oreo Latte 22oz": {"Beans": 36, "Milk": 250, "22oz Cups Iced": 1},
    "Strawberry Coffee 16oz": {"Beans": 36, "Milk": 200, "Strawberry Syrup": 20, "16oz Cups Iced": 1},
    "Strawberry Coffee 22oz": {"Beans": 36, "Milk": 250, "Strawberry Syrup": 30, "22oz Cups Iced": 1},
    "Buttered Scotch 12oz": {"Beans": 18, "Milk": 150, "Butterscotch Syrup": 20, "12oz Cups Hot": 1},
    "Buttered Scotch 16oz": {"Beans": 36, "Milk": 200, "Butterscotch Syrup": 30, "16oz Cups Hot": 1},
    "Buttered Scotch 22oz": {"Beans": 36, "Milk": 250, "Butterscotch Syrup": 40, "22oz Cups Iced": 1},
    "Hazelnut 12oz": {"Beans": 18, "Milk": 150, "Hazelnut Syrup": 20, "12oz Cups Hot": 1},
    "Hazelnut 16oz": {"Beans": 36, "Milk": 200, "Hazelnut Syrup": 30, "16oz Cups Hot": 1},
    "Hazelnut 22oz": {"Beans": 36, "Milk": 250, "Hazelnut Syrup": 40, "22oz Cups Iced": 1},
    "Vanilla 12oz": {"Beans": 18, "Milk": 150, "Vanilla Syrup": 20, "12oz Cups Hot": 1},
    "Vanilla 16oz": {"Beans": 36, "Milk": 200, "Vanilla Syrup": 30, "16oz Cups Hot": 1},
    "Vanilla 22oz": {"Beans": 36, "Milk": 250, "Vanilla Syrup": 40, "22oz Cups Iced": 1},
    "Iced Choco 16oz": {"Milk": 200, "Choco Sauce": 30, "16oz Cups Iced": 1},
    "Iced Choco 22oz": {"Milk": 250, "Choco Sauce": 40, "22oz Cups Iced": 1},
    "Oreo Blend 16oz": {"Milk": 200, "Vanilla Syrup": 10, "16oz Cups Iced": 1},
    "Oreo Blend 22oz": {"Milk": 250, "Vanilla Syrup": 20, "22oz Cups Iced": 1},
    "Strawberry Choco 16oz": {"Milk": 200, "Strawberry Syrup": 20, "Choco Sauce": 20, "16oz Cups Iced": 1},
    "Strawberry Choco 22oz": {"Milk": 250, "Strawberry Syrup": 30, "Choco Sauce": 30, "22oz Cups Iced": 1},
    "Oreo Matcha 16oz": {"Milk": 200, "16oz Cups Iced": 1},
    "Oreo Matcha 22oz": {"Milk": 250, "22oz Cups Iced": 1},
    "Ube Matcha 16oz": {"Milk": 200, "16oz Cups Iced": 1},
    "Ube Matcha 22oz": {"Milk": 250, "22oz Cups Iced": 1},
    "Oreo Ube 16oz": {"Milk": 200, "16oz Cups Iced": 1},
    "Oreo Ube 22oz": {"Milk": 250, "22oz Cups Iced": 1},
}


# --- UI CLASSES ---

class StartScreen(MDScreen):
    def start_shift(self):
        app = MDApp.get_running_app()
        app.start_shift()


class CategoryCard(MDCard):
    category_name = StringProperty()

    def on_release(self):
        app = MDApp.get_running_app()
        app.load_products_for_category(self.category_name)


class ProductCard(MDCard):
    name = StringProperty()
    sizes = DictProperty()
    image_source = StringProperty("placeholder.png")
    angle = NumericProperty(0)

    def on_release(self):
        app = MDApp.get_running_app()
        if app.is_edit_mode:
            app.open_image_selector(self.name)
        else:
            app.show_size_selection(self.name, self.sizes)

    def start_shake(self):
        anim = Animation(angle=2, duration=0.1) + Animation(angle=-2, duration=0.1)
        anim.repeat = True
        anim.start(self)

    def stop_shake(self):
        Animation.cancel_all(self)
        self.angle = 0


class CartItem(BoxLayout):
    name = StringProperty()
    price = NumericProperty()

    def remove_item(self):
        app = MDApp.get_running_app()
        app.remove_from_cart(self)


class POSScreen(MDScreen):
    pass


# --- UPDATED INVENTORY ROW: SYNCED START & END ---
class InventoryRow(ButtonBehavior, BoxLayout):
    name = StringProperty()
    start_qty = StringProperty()
    current_qty = StringProperty()

    def on_release(self):
        app = MDApp.get_running_app()

        # Calculate current display unit
        raw_start = app.shift_start_data.get(self.name, 0)
        unit_size = UNIT_SIZES.get(self.name, 1)
        display_start = raw_start / unit_size

        # Layout for Popup
        content = BoxLayout(orientation='vertical', spacing="10dp", padding="10dp", size_hint_y=None, height="100dp")

        # Only ONE field: Actual Count
        qty_field = MDTextField(text=f"{display_start:.2f}", hint_text="Actual Quantity (Units)", input_type="number")
        content.add_widget(qty_field)

        def save_changes(x):
            try:
                user_qty = float(qty_field.text)

                # Convert back to Raw
                new_qty_raw = user_qty * unit_size

                # --- CRITICAL: Update BOTH Start and Current ---
                # This synchronizes the columns, acting as a stock reset.
                app.inventory_data[self.name] = new_qty_raw
                app.shift_start_data[self.name] = new_qty_raw

                app.save_inventory()
                with open(SHIFT_START_FILE, 'w') as f:
                    json.dump(app.shift_start_data, f, indent=4)

                toast(f"Stock Reset: {self.name}")
                dialog.dismiss()
                app.root.get_screen('inventory').load_inventory()

            except ValueError:
                toast("Please enter valid numbers")

        dialog = MDDialog(
            title=f"Count Stock: {self.name}",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="CONFIRM COUNT", on_release=save_changes)
            ]
        )
        dialog.open()


class InventoryScreen(MDScreen):
    def on_enter(self):
        self.load_inventory()

    def load_inventory(self):
        app = MDApp.get_running_app()
        list_box = self.ids.inventory_container
        list_box.clear_widgets()

        current_inv = app.inventory_data
        start_inv = app.shift_start_data if app.shift_start_data else {}

        for item, raw_qty in current_inv.items():
            raw_start = start_inv.get(item, 0)

            unit_size = UNIT_SIZES.get(item, 1)

            qty_unit = raw_qty / unit_size
            start_unit = raw_start / unit_size

            str_start = f"{start_unit:.2f}"
            str_curr = f"{qty_unit:.2f}"

            row = InventoryRow(
                name=item,
                start_qty=str_start,
                current_qty=str_curr
            )
            list_box.add_widget(row)


class ReceiptsScreen(MDScreen):
    def on_enter(self):
        self.load_receipts()

    def load_receipts(self):
        app = MDApp.get_running_app()
        self.ids.receipt_list.clear_widgets()
        reversed_receipts = app.receipts_data[::-1]
        for r in reversed_receipts:
            item_summary = ", ".join([item['name'] for item in r['items']])
            if len(item_summary) > 40:
                item_summary = item_summary[:40] + "..."
            li = ThreeLineAvatarIconListItem(
                text=f"Order #{r['id']} - P{r['total']}",
                secondary_text=f"{r['date']}",
                tertiary_text=item_summary
            )
            li.add_widget(IconLeftWidget(icon="receipt"))
            self.ids.receipt_list.add_widget(li)


class AdminScreen(MDScreen):
    def on_enter(self):
        self.load_prices()

    def load_prices(self):
        app = MDApp.get_running_app()
        self.ids.admin_list.clear_widgets()
        for category, items in app.product_data.items():
            for name, size_dict in items.items():
                for size, price in size_dict.items():
                    full_name = f"{name} {size}"
                    li = OneLineAvatarIconListItem(text=f"{full_name} - P{price}")
                    icon = IconRightWidget(icon="pencil")
                    icon.bind(on_release=partial(self.edit_price, name, size, category, price))
                    li.add_widget(icon)
                    self.ids.admin_list.add_widget(li)

    def edit_price(self, product_name, size, category, old_price, instance):
        app = MDApp.get_running_app()

        def save_new_price(instance):
            try:
                new_price = float(field.text)
                app.update_price(category, product_name, size, new_price)
                dialog.dismiss()
                self.load_prices()
            except ValueError:
                toast("Invalid Price")

        field = MDTextField(text=str(old_price), hint_text="Enter new price")
        dialog = MDDialog(
            title=f"Edit: {product_name} {size}",
            type="custom", content_cls=field,
            buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                     MDRaisedButton(text="SAVE", on_release=save_new_price)]
        )
        dialog.open()


# --- MAIN APPLICATION ---

class CafeApp(MDApp):
    cart_total = NumericProperty(0)
    inventory_data = {}
    shift_start_data = {}
    product_data = {}
    receipts_data = []
    image_map = {}
    cart_items = []
    dialog_ref = None
    current_view = StringProperty("categories")
    is_edit_mode = BooleanProperty(False)

    def build(self):
        self.theme_cls.primary_palette = "Brown"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.load_data()
        return Builder.load_file('app.kv')

    def on_start(self):
        if os.path.exists(SHIFT_START_FILE):
            self.root.current = 'pos'
            self.load_category_menu()
        else:
            self.root.current = 'start'

    # --- SHIFT MANAGEMENT ---
    def start_shift(self):
        self.shift_start_data = self.inventory_data.copy()
        with open(SHIFT_START_FILE, 'w') as f:
            json.dump(self.shift_start_data, f, indent=4)
        toast("Shift Started!")
        self.root.current = 'pos'
        self.load_category_menu()

    def end_shift(self):
        if not os.path.exists(SHIFT_START_FILE):
            toast("Shift hasn't started yet!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"Report_{timestamp}.csv"

        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["INVENTORY REPORT", timestamp])
                writer.writerow(["Item", "Start (Units)", "End (Units)", "Diff (Units)"])

                for item, raw_end in self.inventory_data.items():
                    raw_start = self.shift_start_data.get(item, 0)

                    unit_size = UNIT_SIZES.get(item, 1)
                    u_start = raw_start / unit_size
                    u_end = raw_end / unit_size
                    u_diff = u_end - u_start

                    writer.writerow([item, f"{u_start:.2f}", f"{u_end:.2f}", f"{u_diff:.2f}"])

                writer.writerow([])
                writer.writerow(["SALES LOG"])
                writer.writerow(["Order ID", "Date", "Total", "Items"])

                for r in self.receipts_data:
                    items_str = "; ".join([i['name'] for i in r['items']])
                    writer.writerow([r['id'], r['date'], r['total'], items_str])

            toast(f"Shift Ends. Saved: {filename}")

            self.shift_start_data = {}
            self.receipts_data = []
            self.save_receipts()

            if os.path.exists(SHIFT_START_FILE):
                os.remove(SHIFT_START_FILE)

            self.root.current = 'start'

        except Exception as e:
            toast(f"Export Error: {e}")

    # --- EDIT MODE ---
    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode
        toast(f"Edit Mode: {'ON' if self.is_edit_mode else 'OFF'}")

        try:
            pos_screen = self.root.get_screen('pos')
            container = pos_screen.ids.menu_container
            if container.children:
                grid = container.children[0]
                for widget in grid.children:
                    if isinstance(widget, ProductCard):
                        if self.is_edit_mode:
                            widget.start_shake()
                        else:
                            widget.stop_shake()
        except Exception as e:
            print(f"Shake update error: {e}")

    def open_image_selector(self, product_name):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        content.add_widget(file_chooser)
        btn = MDRaisedButton(text="SELECT", size_hint_y=None, height="50dp")
        content.add_widget(btn)

        popup = Popup(title=f"Image for {product_name}", content=content, size_hint=(0.9, 0.9))

        def select_file(instance):
            if file_chooser.selection:
                self.save_product_image(product_name, file_chooser.selection[0])
                popup.dismiss()

        btn.bind(on_release=select_file)
        popup.open()

    def save_product_image(self, product_name, original_path):
        extension = os.path.splitext(original_path)[1]
        safe_name = product_name.replace(" ", "_") + extension
        new_path = os.path.join(IMAGE_DIR, safe_name)

        try:
            if PILImage:
                with PILImage.open(original_path) as img:
                    img.thumbnail((300, 400))
                    img.save(new_path)
            else:
                shutil.copy(original_path, new_path)

            self.image_map[product_name] = new_path
            self.save_images()
            toast("Image Saved!")

            cat_found = None
            for cat, items in self.product_data.items():
                if product_name in items:
                    cat_found = cat
                    break
            if cat_found and self.current_view == "products":
                self.load_products_for_category(cat_found)

        except Exception as e:
            toast(f"Error: {e}")

    # --- NAVIGATION & CART ---
    def load_category_menu(self):
        self.current_view = "categories"
        pos_screen = self.root.get_screen('pos')
        container = pos_screen.ids.menu_container
        container.clear_widgets()
        pos_screen.ids.pos_toolbar.title = "Select Category"
        pos_screen.ids.pos_toolbar.left_action_items = []

        grid = MDGridLayout(cols=2, spacing="15dp", padding="20dp", adaptive_height=True)
        for category in self.product_data.keys():
            card = CategoryCard(category_name=category)
            grid.add_widget(card)
        container.add_widget(grid)

    def load_products_for_category(self, category_name):
        self.current_view = "products"
        pos_screen = self.root.get_screen('pos')
        container = pos_screen.ids.menu_container
        container.clear_widgets()
        pos_screen.ids.pos_toolbar.title = category_name
        pos_screen.ids.pos_toolbar.left_action_items = [["arrow-left", lambda x: self.load_category_menu()]]

        grid = MDGridLayout(cols=3, spacing="15dp", padding="10dp", adaptive_height=True)
        products = self.product_data.get(category_name, {})
        for name, sizes in products.items():
            img = self.image_map.get(name, "placeholder.png")
            card = ProductCard(name=name, sizes=sizes, image_source=img)
            if self.is_edit_mode: card.start_shake()
            grid.add_widget(card)
        container.add_widget(grid)

    def show_size_selection(self, product_name, sizes_dict):
        content_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="10dp",
                                  padding=[0, "10dp", 0, 0])
        self.dialog_ref = MDDialog(title=f"Select Size: {product_name}", type="custom", content_cls=content_box)
        for size, price in sorted(sizes_dict.items()):
            btn = MDRectangleFlatButton(text=f"{size} - P{price}", size_hint_x=1, height="50dp",
                                        on_release=partial(self.finish_selection, product_name, size, price))
            content_box.add_widget(btn)
        self.dialog_ref.open()

    def finish_selection(self, name, size, price, instance):
        self.dialog_ref.dismiss()
        self.add_to_cart(f"{name} {size}", price)

    def add_to_cart(self, name, price):
        self.cart_items.append({"name": name, "price": price})
        self.update_cart_ui()

    def remove_from_cart(self, widget_instance):
        for i, item in enumerate(self.cart_items):
            if item['name'] == widget_instance.name:
                del self.cart_items[i]
                break
        self.update_cart_ui()

    def update_cart_ui(self):
        pos_screen = self.root.get_screen('pos')
        pos_screen.ids.cart_box.clear_widgets()
        for item in self.cart_items:
            w = CartItem(name=item['name'], price=item['price'])
            pos_screen.ids.cart_box.add_widget(w)
        self.cart_total = sum(item['price'] for item in self.cart_items)

    def checkout(self):
        if not self.cart_items:
            toast("Cart is empty")
            return

        missing_items = []
        temp_inventory = self.inventory_data.copy()

        for item in self.cart_items:
            product_name = item['name']
            if product_name in RECIPES:
                ingredients = RECIPES[product_name]
                for ing_name, amount in ingredients.items():
                    if ing_name in temp_inventory:
                        if temp_inventory[ing_name] >= amount:
                            temp_inventory[ing_name] -= amount
                        else:
                            missing_items.append(ing_name)
                    else:
                        # Fallback: create it if missing
                        temp_inventory[ing_name] = -amount
                        missing_items.append(f"{ing_name} (Unknown)")

        if missing_items:
            toast(f"Low Stock: {', '.join(list(set(missing_items)))}")
            return

        self.inventory_data = temp_inventory
        self.save_inventory()
        new_receipt = {"id": str(int(time.time())), "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                       "total": self.cart_total, "items": self.cart_items}
        self.receipts_data.append(new_receipt)
        self.save_receipts()
        self.cart_items = []
        self.update_cart_ui()
        toast("Order Complete!")

    # --- DATA ---
    def load_data(self):
        # 1. Inventory: FIX LOAD LOGIC
        if not os.path.exists(INVENTORY_FILE):
            self.inventory_data = DEFAULT_INVENTORY.copy()  # Set memory
            self.save_inventory()  # Save to file
        else:
            with open(INVENTORY_FILE, 'r') as f:
                self.inventory_data = json.load(f)

        # 2. Products
        if not os.path.exists(PRODUCTS_FILE):
            self.product_data = DEFAULT_PRODUCTS.copy()
            self.save_products()
        else:
            with open(PRODUCTS_FILE, 'r') as f:
                self.product_data = json.load(f)

        # 3. Receipts
        if os.path.exists(RECEIPTS_FILE):
            with open(RECEIPTS_FILE, 'r') as f:
                try:
                    self.receipts_data = json.load(f)
                except:
                    self.receipts_data = []

        # 4. Images
        if os.path.exists(IMAGES_FILE):
            with open(IMAGES_FILE, 'r') as f:
                try:
                    self.image_map = json.load(f)
                except:
                    self.image_map = {}

        # 5. Shift Snapshot
        if os.path.exists(SHIFT_START_FILE):
            with open(SHIFT_START_FILE, 'r') as f:
                try:
                    self.shift_start_data = json.load(f)
                except:
                    self.shift_start_data = {}

    def save_inventory(self):
        with open(INVENTORY_FILE, 'w') as f: json.dump(self.inventory_data, f, indent=4)

    def save_products(self):
        with open(PRODUCTS_FILE, 'w') as f: json.dump(self.product_data, f, indent=4)

    def save_receipts(self):
        with open(RECEIPTS_FILE, 'w') as f: json.dump(self.receipts_data, f, indent=4)

    def save_images(self):
        with open(IMAGES_FILE, 'w') as f: json.dump(self.image_map, f, indent=4)

    def update_price(self, category, product_name, size, new_price):
        self.product_data[category][product_name][size] = new_price
        self.save_products()
        if self.current_view == "products": self.load_products_for_category(category)


if __name__ == '__main__':
    CafeApp().run()