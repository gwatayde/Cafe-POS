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

# --- IMAGE LIBRARY CHECK ---
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None
    print("Pillow library not found. Images will not be resized.")

# --- CONFIGURATION ---
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

# --- KV LAYOUT ---
KV = '''
ScreenManager:
    StartScreen:
        name: 'start'
    POSScreen:
        name: 'pos'
    InventoryScreen:
        name: 'inventory'
    ReceiptsScreen:
        name: 'receipts'
    AdminScreen:
        name: 'admin'

<StartScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: app.theme_cls.bg_dark
        padding: "50dp"
        spacing: "30dp"

        MDLabel:
            text: "WELCOME TO CAFE POS"
            halign: "center"
            font_style: "H4"
            theme_text_color: "Primary"

        MDRaisedButton:
            text: "START SHIFT"
            font_size: "24sp"
            size_hint: 0.6, 0.2
            pos_hint: {"center_x": 0.5}
            md_bg_color: 0, 0.7, 0, 1
            on_release: root.start_shift()

<InventoryRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: "50dp"
    padding: "10dp"
    spacing: "5dp"
    canvas.after:
        Color:
            rgba: 0.8, 0.8, 0.8, 1
        Line:
            points: [self.x, self.y, self.right, self.y]
            width: 1

    MDLabel:
        text: root.name
        size_hint_x: 0.5
        shorten: True

    MDLabel:
        text: root.start_qty
        size_hint_x: 0.25
        halign: "center"
        theme_text_color: "Secondary"

    MDLabel:
        text: root.current_qty
        size_hint_x: 0.25
        halign: "center"
        bold: True

<CategoryCard>:
    orientation: "vertical"
    size_hint: 1, None
    height: "120dp"
    padding: "20dp"
    elevation: 4
    radius: [15]
    md_bg_color: app.theme_cls.primary_color
    ripple_behavior: True

    MDLabel:
        text: root.category_name
        halign: "center"
        valign: "center"
        bold: True
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        font_style: "H5"

<ProductCard>:
    orientation: "vertical"
    size_hint: None, None
    size: "150dp", "250dp"
    padding: 0
    elevation: 3
    radius: [12]
    md_bg_color: app.theme_cls.bg_light
    ripple_behavior: True

    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            origin: self.center
    canvas.after:
        PopMatrix

    FitImage:
        source: root.image_source
        radius: [12, 12, 0, 0]
        size_hint_y: None
        height: "180dp"
        md_bg_color: 0.9, 0.9, 0.9, 1

    MDBoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: "70dp"
        padding: "5dp"

        MDLabel:
            text: root.name
            halign: "center"
            bold: True
            theme_text_color: "Primary"
            font_style: "Subtitle2"
            font_size: "13sp"

        MDLabel:
            text: "Select Size"
            halign: "center"
            theme_text_color: "Hint"
            font_size: "11sp"

<CartItem>:
    size_hint_y: None
    height: "40dp"
    spacing: "10dp"

    MDLabel:
        text: root.name
        size_hint_x: 0.5
        shorten: True
        font_size: "14sp"

    MDLabel:
        text: "P" + str(root.price)
        size_hint_x: 0.3
        halign: "right"

    MDIconButton:
        icon: "minus-circle"
        theme_text_color: "Error"
        on_release: root.remove_item()

<POSScreen>:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            id: pos_toolbar
            title: "Select Category"
            right_action_items: [["receipt", lambda x: setattr(root.manager, 'current', 'receipts')], ["chart-box", lambda x: setattr(root.manager, 'current', 'inventory')], ["cog", lambda x: setattr(root.manager, 'current', 'admin')]]
            elevation: 10

        MDBoxLayout:
            orientation: 'horizontal'

            # LEFT: MENU AREA
            MDBoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.65
                padding: "10dp"

                ScrollView:
                    do_scroll_x: False
                    MDBoxLayout:
                        id: menu_container
                        orientation: 'vertical'
                        adaptive_height: True
                        padding: "10dp"

            # RIGHT: CART AREA
            MDCard:
                orientation: 'vertical'
                size_hint_x: 0.35
                padding: "10dp"
                elevation: 4

                MDLabel:
                    text: "Current Order"
                    font_style: "H6"
                    halign: "center"
                    size_hint_y: None
                    height: "50dp"

                ScrollView:
                    MDBoxLayout:
                        id: cart_box
                        orientation: 'vertical'
                        adaptive_height: True
                        spacing: "5dp"

                MDBoxLayout:
                    size_hint_y: None
                    height: "50dp"
                    padding: "5dp"

                    MDLabel:
                        text: "Total:"
                        bold: True

                    MDLabel:
                        text: "P" + str(app.cart_total)
                        halign: "right"
                        bold: True
                        font_style: "H5"

                MDRaisedButton:
                    text: "CHECKOUT"
                    size_hint_x: 1
                    height: "60dp"
                    font_size: "20sp"
                    on_release: app.checkout()

<InventoryScreen>:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Inventory"
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'pos')]]
            elevation: 10

        # HEADER ROW
        MDBoxLayout:
            size_hint_y: None
            height: "40dp"
            padding: "10dp"
            spacing: "5dp"
            md_bg_color: 0.9, 0.9, 0.9, 1

            MDLabel:
                text: "ITEM"
                bold: True
                size_hint_x: 0.5

            MDLabel:
                text: "START"
                bold: True
                halign: "center"
                size_hint_x: 0.25

            MDLabel:
                text: "END"
                bold: True
                halign: "center"
                size_hint_x: 0.25

        ScrollView:
            MDBoxLayout:
                id: inventory_container
                orientation: 'vertical'
                adaptive_height: True

<ReceiptsScreen>:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Sales History"
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'pos')]]
            elevation: 10

        ScrollView:
            MDList:
                id: receipt_list

<AdminScreen>:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "Price Editor (Admin)"
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'pos')]]
            elevation: 10

        MDBoxLayout:
            orientation: 'vertical'
            padding: "20dp"
            spacing: "20dp"

            MDRaisedButton:
                text: "END SHIFT (EXPORT CSV REPORT)"
                size_hint_x: 1
                height: "50dp"
                md_bg_color: 0, 0, 0.7, 1 # Blue
                on_release: app.end_shift()

            MDRaisedButton:
                text: "TOGGLE EDIT MODE (UPLOAD IMAGES)"
                size_hint_x: 1
                height: "50dp"
                md_bg_color: 1, 0, 0, 1
                on_release: app.toggle_edit_mode()

            MDLabel:
                text: "Tap a product below to edit price:"
                halign: "center"
                size_hint_y: None
                height: "30dp"

            ScrollView:
                MDList:
                    id: admin_list
'''

# --- LOGIC ---

# Unit Conversion (Grams/ML per 1 Unit)
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


# --- CLASSES ---

class StartScreen(MDScreen):
    def start_shift(self):
        app = MDApp.get_running_app()
        app.start_shift()


class CategoryCard(MDCard):
    category_name = StringProperty()

    def on_release(self):
        MDApp.get_running_app().load_products_for_category(self.category_name)


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
        MDApp.get_running_app().remove_from_cart(self)


class POSScreen(MDScreen): pass


class InventoryRow(ButtonBehavior, BoxLayout):
    name = StringProperty()
    start_qty = StringProperty()
    current_qty = StringProperty()

    def on_release(self):
        app = MDApp.get_running_app()
        raw_start = app.shift_start_data.get(self.name, 0)
        unit_size = UNIT_SIZES.get(self.name, 1)
        display_start = raw_start / unit_size

        content = BoxLayout(orientation='vertical', spacing="10dp", padding="10dp", size_hint_y=None, height="100dp")
        qty_field = MDTextField(text=f"{display_start:.2f}", hint_text="Actual Quantity (Units)", input_type="number")
        content.add_widget(qty_field)

        def save_changes(x):
            try:
                user_qty = float(qty_field.text)
                new_qty_raw = user_qty * unit_size
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

        dialog = MDDialog(title=f"Count Stock: {self.name}", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                                   MDRaisedButton(text="CONFIRM", on_release=save_changes)])
        dialog.open()


class InventoryScreen(MDScreen):
    def on_enter(self): self.load_inventory()

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
            list_box.add_widget(InventoryRow(name=item, start_qty=f"{start_unit:.2f}", current_qty=f"{qty_unit:.2f}"))


class ReceiptsScreen(MDScreen):
    def on_enter(self): self.load_receipts()

    def load_receipts(self):
        app = MDApp.get_running_app()
        self.ids.receipt_list.clear_widgets()
        for r in app.receipts_data[::-1]:
            item_summary = ", ".join([item['name'] for item in r['items']])
            li = ThreeLineAvatarIconListItem(text=f"Order #{r['id']} - P{r['total']}",
                                             secondary_text=f"{r['date']}", tertiary_text=item_summary)
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
                    li = OneLineAvatarIconListItem(text=f"{name} {size} - P{price}")
                    icon = IconRightWidget(icon="pencil")
                    icon.bind(on_release=partial(self.edit_price, name, size, category, price))
                    li.add_widget(icon)
                    self.ids.admin_list.add_widget(li)

    def edit_price(self, product_name, size, category, old_price, instance):
        app = MDApp.get_running_app()
        field = MDTextField(text=str(old_price), hint_text="Enter new price")

        def save(x):
            try:
                app.update_price(category, product_name, size, float(field.text))
                dialog.dismiss()
                self.load_prices()
            except:
                toast("Invalid")

        dialog = MDDialog(title=f"Edit: {product_name} {size}", type="custom", content_cls=field,
                          buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                                   MDRaisedButton(text="SAVE", on_release=save)])
        dialog.open()


# --- APP ---
class CafeApp(MDApp):
    cart_total = NumericProperty(0)
    inventory_data = {}
    shift_start_data = {}
    product_data = {}
    receipts_data = []
    image_map = {}
    cart_items = []
    is_edit_mode = BooleanProperty(False)

    def build(self):
        self.theme_cls.primary_palette = "Brown"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.load_data()
        return Builder.load_string(KV)

    def on_start(self):
        if os.path.exists(SHIFT_START_FILE):
            self.root.current = 'pos'
            self.load_category_menu()
        else:
            self.root.current = 'start'

    def start_shift(self):
        self.shift_start_data = self.inventory_data.copy()
        with open(SHIFT_START_FILE, 'w') as f: json.dump(self.shift_start_data, f, indent=4)
        toast("Shift Started!")
        self.root.current = 'pos'
        self.load_category_menu()

    def end_shift(self):
        if not os.path.exists(SHIFT_START_FILE): return toast("No shift running")

        # --- CONFIRMATION DIALOG ---
        self.dialog_ref = MDDialog(
            title="End Shift?",
            text="Are you sure you want to close the shift and save the report?",
            buttons=[
                MDFlatButton(text="NO", on_release=lambda x: self.dialog_ref.dismiss()),
                MDRaisedButton(text="YES", on_release=lambda x: self.finalize_end_shift())
            ]
        )
        self.dialog_ref.open()

    def finalize_end_shift(self):
        self.dialog_ref.dismiss()

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
                    writer.writerow([item, f"{raw_start / unit_size:.2f}", f"{raw_end / unit_size:.2f}",
                                     f"{(raw_end - raw_start) / unit_size:.2f}"])
                writer.writerow([])
                writer.writerow(["SALES LOG"])
                for r in self.receipts_data:
                    writer.writerow([r['id'], r['date'], r['total'], "; ".join([i['name'] for i in r['items']])])
            toast(f"Saved: {filename}")
            self.shift_start_data = {}
            self.receipts_data = []
            self.save_receipts()
            if os.path.exists(SHIFT_START_FILE): os.remove(SHIFT_START_FILE)
            self.root.current = 'start'
        except Exception as e:
            toast(f"Error: {e}")

    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode
        toast(f"Edit Mode: {self.is_edit_mode}")
        try:
            grid = self.root.get_screen('pos').ids.menu_container.children[0]
            for w in grid.children:
                if isinstance(w, ProductCard): w.start_shake() if self.is_edit_mode else w.stop_shake()
        except:
            pass

    def open_image_selector(self, product_name):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        content.add_widget(file_chooser)
        btn = MDRaisedButton(text="SELECT", size_hint_y=None, height="50dp")
        content.add_widget(btn)
        popup = Popup(title=f"Image for {product_name}", content=content, size_hint=(0.9, 0.9))

        def select(x):
            if file_chooser.selection:
                self.save_product_image(product_name, file_chooser.selection[0])
                popup.dismiss()

        btn.bind(on_release=select)
        popup.open()

    def save_product_image(self, product_name, original_path):
        safe_name = product_name.replace(" ", "_") + os.path.splitext(original_path)[1]
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
            toast("Saved!")
            self.load_products_for_category([k for k, v in self.product_data.items() if product_name in v][0])
        except:
            toast("Error saving image")

    def load_category_menu(self):
        self.current_view = "categories"
        screen = self.root.get_screen('pos')
        screen.ids.pos_toolbar.title = "Select Category"
        screen.ids.pos_toolbar.left_action_items = []
        screen.ids.menu_container.clear_widgets()
        grid = MDGridLayout(cols=2, spacing="15dp", padding="20dp", adaptive_height=True)
        for cat in self.product_data: grid.add_widget(CategoryCard(category_name=cat))
        screen.ids.menu_container.add_widget(grid)

    def load_products_for_category(self, category_name):
        self.current_view = "products"
        screen = self.root.get_screen('pos')
        screen.ids.pos_toolbar.title = category_name
        screen.ids.pos_toolbar.left_action_items = [["arrow-left", lambda x: self.load_category_menu()]]
        screen.ids.menu_container.clear_widgets()
        grid = MDGridLayout(cols=3, spacing="10dp", padding="10dp", adaptive_height=True)
        for name, sizes in self.product_data.get(category_name, {}).items():
            img = self.image_map.get(name, "placeholder.png")
            card = ProductCard(name=name, sizes=sizes, image_source=img)
            if self.is_edit_mode: card.start_shake()
            grid.add_widget(card)
        screen.ids.menu_container.add_widget(grid)

    def show_size_selection(self, product_name, sizes_dict):
        box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing="10dp", padding=[0, "10dp", 0, 0])
        dialog = MDDialog(title=f"{product_name}", type="custom", content_cls=box)
        for size, price in sizes_dict.items():
            btn = MDRectangleFlatButton(text=f"{size} - P{price}", size_hint_x=1,
                                        on_release=lambda x, s=size, p=price: (dialog.dismiss(),
                                                                               self.add_to_cart(f"{product_name} {s}",
                                                                                                p)))
            box.add_widget(btn)
        dialog.open()

    def add_to_cart(self, name, price):
        self.cart_items.append({"name": name, "price": price})
        self.update_cart_ui()

    def remove_from_cart(self, item_widget):
        for i, item in enumerate(self.cart_items):
            if item['name'] == item_widget.name:
                del self.cart_items[i]
                break
        self.update_cart_ui()

    def update_cart_ui(self):
        screen = self.root.get_screen('pos')
        screen.ids.cart_box.clear_widgets()
        for item in self.cart_items: screen.ids.cart_box.add_widget(CartItem(name=item['name'], price=item['price']))
        self.cart_total = sum(i['price'] for i in self.cart_items)

    def checkout(self):
        if not self.cart_items: return toast("Empty Cart")
        for item in self.cart_items:
            if item['name'] in RECIPES:
                for ing, amt in RECIPES[item['name']].items():
                    self.inventory_data[ing] = self.inventory_data.get(ing, 0) - amt
        self.save_inventory()
        self.receipts_data.append(
            {"id": str(int(time.time())), "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "total": self.cart_total,
             "items": self.cart_items})
        self.save_receipts()
        self.cart_items = []
        self.update_cart_ui()
        toast("Done!")

    def load_data(self):
        if not os.path.exists(INVENTORY_FILE):
            self.inventory_data = DEFAULT_INVENTORY.copy()
            self.save_inventory()
        else:
            with open(INVENTORY_FILE) as f:
                self.inventory_data = json.load(f)

        if not os.path.exists(PRODUCTS_FILE):
            self.product_data = DEFAULT_PRODUCTS.copy()
            self.save_products()
        else:
            with open(PRODUCTS_FILE) as f:
                self.product_data = json.load(f)

        if os.path.exists(RECEIPTS_FILE):
            with open(RECEIPTS_FILE) as f: self.receipts_data = json.load(f)

        if os.path.exists(IMAGES_FILE):
            with open(IMAGES_FILE) as f: self.image_map = json.load(f)

        if os.path.exists(SHIFT_START_FILE):
            with open(SHIFT_START_FILE) as f: self.shift_start_data = json.load(f)

    def save_inventory(self):
        with open(INVENTORY_FILE, 'w') as f: json.dump(self.inventory_data, f, indent=4)

    def save_products(self):
        with open(PRODUCTS_FILE, 'w') as f: json.dump(self.product_data, f, indent=4)

    def save_receipts(self):
        with open(RECEIPTS_FILE, 'w') as f: json.dump(self.receipts_data, f, indent=4)

    def save_images(self):
        with open(IMAGES_FILE, 'w') as f: json.dump(self.image_map, f, indent=4)

    def update_price(self, cat, name, size, price):
        self.product_data[cat][name][size] = price
        self.save_products()
        if self.current_view == "products": self.load_products_for_category(cat)


if __name__ == '__main__':
    CafeApp().run()