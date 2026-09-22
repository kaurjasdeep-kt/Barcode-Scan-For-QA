import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import tempfile
import os
import shutil

APP_IDS = ["11", "12", "13", "14", "15"]

generated_file = None
barcode_image = None


def generate_barcode():
    global generated_file
    global barcode_image

    app_id = app_id_var.get()
    order = order_entry.get().strip()
    loyalty = loyalty_entry.get().strip()

    if not order.isdigit() or len(order) != 19:
        messagebox.showerror(
            "Validation Error",
            "Order Number must be exactly 19 digits."
        )
        return

    if not loyalty.isdigit() or len(loyalty) != 12:
        messagebox.showerror(
            "Validation Error",
            "Loyalty Number must be exactly 12 digits."
        )
        return

    barcode_value = f"2322{app_id}{order}{loyalty}"

    if len(barcode_value) != 37:
        messagebox.showerror(
            "Validation Error",
            f"Barcode length is {len(barcode_value)}. Expected 37."
        )
        return

    try:

        temp_base = os.path.join(
            tempfile.gettempdir(),
            "barcode_preview"
        )

        barcode = Code128(
            barcode_value,
            writer=ImageWriter()
        )

        options = {
            "module_width": 0.12,
            "module_height": 8,
            "quiet_zone": 2,
            "write_text": False
        }

        generated_file = barcode.save(
            temp_base,
            options
        )

        if not os.path.exists(generated_file):
            raise Exception("Barcode image was not created")

        image = Image.open(generated_file)

        # Force a centered, readable preview
        preview_width = 700

        ratio = preview_width / image.width
        preview_height = int(image.height * ratio)

        image = image.resize(
            (preview_width, preview_height),
            Image.LANCZOS
        )

        barcode_image = ImageTk.PhotoImage(image)

        barcode_label.config(
            image=barcode_image
        )

        barcode_label.image = barcode_image

        barcode_entry.delete(0, tk.END)
        barcode_entry.insert(0, barcode_value)

        save_button.config(
            state="normal"
        )

    except Exception as ex:
        messagebox.showerror(
            "Barcode Error",
            str(ex)
        )


def save_barcode():

    global generated_file

    if not generated_file:
        messagebox.showerror(
            "Error",
            "Generate a barcode first."
        )
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Files", "*.png")],
        title="Save Barcode"
    )

    if not save_path:
        return

    try:

        shutil.copy2(
            generated_file,
            save_path
        )

        messagebox.showinfo(
            "Success",
            f"Saved:\n{save_path}"
        )

    except Exception as ex:
        messagebox.showerror(
            "Save Error",
            str(ex)
        )


# ------------------------------
# GUI
# ------------------------------

root = tk.Tk()

root.title("Code 128 Barcode Generator")
root.geometry("1000x650")

root.grid_columnconfigure(
    0,
    weight=1
)

# Application ID

ttk.Label(
    root,
    text="Application ID"
).pack(
    pady=(20, 5)
)

app_id_var = tk.StringVar(
    value="11"
)

ttk.Combobox(
    root,
    textvariable=app_id_var,
    values=APP_IDS,
    state="readonly",
    width=10
).pack()

# Order Number

ttk.Label(
    root,
    text="Order Number (19 digits)"
).pack(
    pady=(15, 5)
)

order_entry = ttk.Entry(
    root,
    width=40
)

order_entry.pack()

# Loyalty Number

ttk.Label(
    root,
    text="Loyalty Number (12 digits)"
).pack(
    pady=(15, 5)
)

loyalty_entry = ttk.Entry(
    root,
    width=40
)

loyalty_entry.pack()

# Generate Button

ttk.Button(
    root,
    text="Generate Barcode",
    command=generate_barcode
).pack(
    pady=20
)

# Barcode Preview

barcode_frame = tk.Frame(root)

barcode_frame.pack(
    pady=10
)

barcode_label = tk.Label(
    barcode_frame
)

barcode_label.pack()

# Barcode Value

barcode_entry = tk.Entry(
    root,
    width=50,
    justify="center",
    font=("Consolas", 12)
)

barcode_entry.pack(
    pady=10
)

# Save Button

save_button = ttk.Button(
    root,
    text="Save Barcode PNG",
    command=save_barcode,
    state="disabled"
)

save_button.pack(
    pady=10
)

root.mainloop()