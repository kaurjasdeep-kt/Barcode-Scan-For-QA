import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from io import BytesIO
from decimal import Decimal, InvalidOperation

try:
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    barcode = None
    Image = ImageOps = ImageTk = ImageWriter = None


def calculate_check_digit(item_13):
    if len(item_13) != 13 or not item_13.isdigit():
        raise ValueError("The item number must contain exactly 13 digits.")
    total = 0
    for position, digit in enumerate(reversed(item_13), start=1):
        total += int(digit) * (3 if position % 2 == 1 else 1)
    return str((10 - total % 10) % 10)


def format_date(value):
    value = value.strip()
    for pattern in ("%m/%d/%Y", "%Y-%m-%d", "%y%m%d"):
        try:
            return datetime.strptime(value, pattern).strftime("%y%m%d")
        except ValueError:
            pass
    raise ValueError("Enter the date as MM/DD/YYYY, YYYY-MM-DD, or YYMMDD.")


class GS1128App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GS1-128 Barcode Generator")
        self.geometry("1050x700")
        self.minsize(850, 620)

        self.date_ai = tk.StringVar(value="16")
        self.item_number = tk.StringVar()
        self.date_value = tk.StringVar(value=datetime.today().strftime("%m/%d/%Y"))
        self.sale_type = tk.StringVar(value="quantity")
        self.measure_value = tk.StringVar()
        self.payload_display = tk.StringVar(value="Enter the values and select Generate Barcode.")
        self.status = tk.StringVar(value="Ready. Ghostscript is not required.")

        self.barcode_image = None
        self.preview_image = None
        self.build_screen()
        self.sale_type.trace_add("write", lambda *_: self.update_measurement_labels())
        self.update_measurement_labels()

    def build_screen(self):
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Hint.TLabel", foreground="#555555")

        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="GS1-128 Barcode Generator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Generates a GS1-128 barcode with the required initial FNC1 character.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        form = ttk.LabelFrame(outer, text="Barcode information", padding=14)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Date AI:").grid(row=0, column=0, sticky="w", pady=6)
        ai_box = ttk.Frame(form)
        ai_box.grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Radiobutton(ai_box, text="15 - Best before", variable=self.date_ai, value="15").pack(side="left", padx=(0, 18))
        ttk.Radiobutton(ai_box, text="16 - Sell by", variable=self.date_ai, value="16").pack(side="left")

        ttk.Label(form, text="13-digit item number:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.item_number).grid(row=1, column=1, sticky="ew", padx=(12, 0))
        ttk.Label(form, text="The 14th GTIN check digit is calculated automatically.", style="Hint.TLabel").grid(row=2, column=1, sticky="w", padx=(12, 0))

        ttk.Label(form, text="Date:").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.date_value).grid(row=3, column=1, sticky="ew", padx=(12, 0))
        ttk.Label(form, text="Accepted: MM/DD/YYYY, YYYY-MM-DD, or YYMMDD", style="Hint.TLabel").grid(row=4, column=1, sticky="w", padx=(12, 0))

        ttk.Label(form, text="Item sold by:").grid(row=5, column=0, sticky="w", pady=6)
        type_box = ttk.Frame(form)
        type_box.grid(row=5, column=1, sticky="w", padx=(12, 0))
        ttk.Radiobutton(type_box, text="Weight (AI 3202)", variable=self.sale_type, value="weight").pack(side="left", padx=(0, 18))
        ttk.Radiobutton(type_box, text="Quantity (AI 30)", variable=self.sale_type, value="quantity").pack(side="left")

        self.measure_label = ttk.Label(form)
        self.measure_label.grid(row=6, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.measure_value).grid(row=6, column=1, sticky="ew", padx=(12, 0))
        self.measure_hint = ttk.Label(form, style="Hint.TLabel")
        self.measure_hint.grid(row=7, column=1, sticky="w", padx=(12, 0))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=12)
        ttk.Button(buttons, text="Generate Barcode", command=self.generate_barcode).pack(side="left")
        ttk.Button(buttons, text="Save PNG", command=self.save_png).pack(side="left", padx=8)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left")

        output = ttk.LabelFrame(outer, text="Generated barcode", padding=12)
        output.pack(fill="both", expand=True)
        ttk.Label(output, textvariable=self.payload_display, font=("Consolas", 10), wraplength=970).pack(anchor="w", pady=(0, 10))
        self.barcode_label = ttk.Label(output, anchor="center")
        self.barcode_label.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status, style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

    def update_measurement_labels(self):
        if self.sale_type.get() == "weight":
            self.measure_label.configure(text="Weight:")
            self.measure_hint.configure(text="Enter pounds with up to 2 decimals. Example: 12.34 becomes 001234.")
        else:
            self.measure_label.configure(text="Quantity:")
            self.measure_hint.configure(text="Enter a whole number from 0 through 999. Example: 3 becomes 003.")

    def build_payload(self):
        item = self.item_number.get().strip()
        gtin_14 = item + calculate_check_digit(item)
        date_data = format_date(self.date_value.get())
        ai = self.date_ai.get()
        if ai not in ("15", "16"):
            raise ValueError("Select date AI 15 or 16.")

        if self.sale_type.get() == "weight":
            try:
                weight = Decimal(self.measure_value.get().strip())
            except InvalidOperation:
                raise ValueError("Weight must be numeric, for example 12.34.")
            if weight < 0 or weight > Decimal("9999.99"):
                raise ValueError("Weight must be between 0 and 9999.99 pounds.")
            if weight.as_tuple().exponent < -2:
                raise ValueError("Weight may contain no more than two decimal places.")
            encoded_measure = f"{int(weight * 100):06d}"
            readable = f"(01){gtin_14}({ai}){date_data}(3202){encoded_measure}"
            compact = f"01{gtin_14}{ai}{date_data}3202{encoded_measure}"
        else:
            quantity = self.measure_value.get().strip()
            if not quantity.isdigit() or not 0 <= int(quantity) <= 999:
                raise ValueError("Quantity must be a whole number from 0 through 999.")
            encoded_measure = f"{int(quantity):03d}"
            readable = f"(01){gtin_14}({ai}){date_data}(30){encoded_measure}"
            compact = f"01{gtin_14}{ai}{date_data}30{encoded_measure}"

        return readable, compact

    def generate_barcode(self):
        if barcode is None:
            messagebox.showerror(
                "Missing packages",
                'Install the required packages using:\n\npython -m pip install "python-barcode[images]" Pillow',
            )
            return

        try:
            readable, compact = self.build_payload()
            gs1_class = barcode.get_barcode_class("gs1_128")
            symbol = gs1_class(compact, writer=ImageWriter())

            buffer = BytesIO()
            symbol.write(
                buffer,
                options={
                    "module_width": 0.34,
                    "module_height": 28.0,
                    "quiet_zone": 6.5,
                    "font_size": 0,
                    "text_distance": 1,
                    "write_text": False,
                    "background": "white",
                    "foreground": "black",
                    "dpi": 300,
                },
            )
            buffer.seek(0)
            image = Image.open(buffer).convert("RGB")
            image = ImageOps.expand(image, border=20, fill="white")
            self.barcode_image = image.copy()

            preview = image.copy()
            preview.thumbnail((970, 370), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(preview)
            self.barcode_label.configure(image=self.preview_image)
            self.payload_display.set(f"GS1 payload: {readable}    Encoded data: {compact}")
            self.status.set("GS1-128 barcode generated successfully. Display at 100% for scanning.")
        except Exception as error:
            self.status.set("Barcode generation failed.")
            messagebox.showerror("Unable to generate barcode", str(error))

    def save_png(self):
        if self.barcode_image is None:
            messagebox.showinfo("Nothing to save", "Generate a barcode first.")
            return
        filename = filedialog.asksaveasfilename(
            title="Save GS1-128 barcode",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile="gs1_128_barcode.png",
        )
        if filename:
            self.barcode_image.save(filename, "PNG", dpi=(300, 300))
            self.status.set(f"Saved: {filename}")

    def clear(self):
        self.item_number.set("")
        self.measure_value.set("")
        self.date_value.set(datetime.today().strftime("%m/%d/%Y"))
        self.payload_display.set("Enter the values and select Generate Barcode.")
        self.barcode_label.configure(image="")
        self.preview_image = None
        self.barcode_image = None
        self.status.set("Ready. Ghostscript is not required.")


if __name__ == "__main__":
    GS1128App().mainloop()
