from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from io import BytesIO
from decimal import Decimal, InvalidOperation

import barcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageOps

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

APP_IDS = ["11", "12", "13", "14", "15"]


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


def build_code128_value(app_id, order, loyalty):
    if app_id not in APP_IDS:
        raise ValueError("Invalid Application ID.")
    if not order.isdigit() or len(order) != 19:
        raise ValueError("Order Number must be exactly 19 digits.")
    if not loyalty.isdigit() or len(loyalty) != 12:
        raise ValueError("Loyalty Number must be exactly 12 digits.")

    barcode_value = f"2322{app_id}{order}{loyalty}"
    if len(barcode_value) != 37:
        raise ValueError(f"Barcode length is {len(barcode_value)}. Expected 37.")
    return barcode_value


def build_gs1_payload(date_ai, item_number, date_value, sale_type, measure_value):
    item = item_number.strip()
    gtin_14 = item + calculate_check_digit(item)
    date_data = format_date(date_value)

    if date_ai not in ("15", "16"):
        raise ValueError("Select date AI 15 or 16.")

    if sale_type == "weight":
        try:
            weight = Decimal(measure_value.strip())
        except InvalidOperation:
            raise ValueError("Weight must be numeric, for example 12.34.")
        if weight < 0 or weight > Decimal("9999.99"):
            raise ValueError("Weight must be between 0 and 9999.99 pounds.")
        if weight.as_tuple().exponent < -2:
            raise ValueError("Weight may contain no more than two decimal places.")
        encoded_measure = f"{int(weight * 100):06d}"
        readable = f"(01){gtin_14}({date_ai}){date_data}(3202){encoded_measure}"
        compact = f"01{gtin_14}{date_ai}{date_data}3202{encoded_measure}"
    else:
        quantity = measure_value.strip()
        if not quantity.isdigit() or not 0 <= int(quantity) <= 999:
            raise ValueError("Quantity must be a whole number from 0 through 999.")
        encoded_measure = f"{int(quantity):03d}"
        readable = f"(01){gtin_14}({date_ai}){date_data}(30){encoded_measure}"
        compact = f"01{gtin_14}{date_ai}{date_data}30{encoded_measure}"

    return readable, compact


def render_code128_png(barcode_value):
    barcode_obj = Code128(barcode_value, writer=ImageWriter())
    buffer = BytesIO()
    barcode_obj.write(
        buffer,
        options={
            "module_width": 0.3,
            "module_height": 20,
            "quiet_zone": 4,
            "write_text": False,
        },
    )
    buffer.seek(0)
    return buffer


def render_gs1_png(compact_value):
    gs1_class = barcode.get_barcode_class("gs1_128")
    symbol = gs1_class(compact_value, writer=ImageWriter())
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
    out = BytesIO()
    image.save(out, "PNG")
    out.seek(0)
    return out


@app.route("/")
def index():
    return render_template("index.html", app_ids=APP_IDS)


@app.route("/api/code128", methods=["POST"])
def api_code128():
    data = request.get_json(force=True)
    try:
        value = build_code128_value(
            data.get("app_id", ""),
            data.get("order", ""),
            data.get("loyalty", ""),
        )
        return jsonify({"ok": True, "value": value, "image_url": f"/img/code128?v={value}"})
    except ValueError as ex:
        return jsonify({"ok": False, "error": str(ex)}), 400


@app.route("/img/code128")
def img_code128():
    value = request.args.get("v", "")
    if not value.isdigit():
        return "Invalid barcode value", 400
    buffer = render_code128_png(value)
    return send_file(buffer, mimetype="image/png")


@app.route("/api/gs1128", methods=["POST"])
def api_gs1128():
    data = request.get_json(force=True)
    try:
        readable, compact = build_gs1_payload(
            data.get("date_ai", ""),
            data.get("item_number", ""),
            data.get("date_value", ""),
            data.get("sale_type", ""),
            data.get("measure_value", ""),
        )
        return jsonify({
            "ok": True,
            "readable": readable,
            "compact": compact,
            "image_url": f"/img/gs1128?v={compact}",
        })
    except ValueError as ex:
        return jsonify({"ok": False, "error": str(ex)}), 400


@app.route("/img/gs1128")
def img_gs1128():
    value = request.args.get("v", "")
    if not value:
        return "Invalid barcode value", 400
    try:
        buffer = render_gs1_png(value)
    except Exception as ex:
        return str(ex), 400
    return send_file(buffer, mimetype="image/png")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
