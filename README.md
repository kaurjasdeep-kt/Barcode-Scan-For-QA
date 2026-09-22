# Barcode Generator (Web)

A local web page that generates Code 128 and GS1-128 barcodes, with a
dropdown to pick which one. Works in any browser, including on your phone
(as long as the phone is on the same Wi-Fi as the PC running it).

## Setup (one-time, each person)

1. Install Python 3.10+ if you don't have it.
2. Open a terminal in this folder and run:

   ```
   pip install -r requirements.txt
   ```

## Run it

```
python webapp.py
```

The terminal will print two URLs, e.g.:

```
* Running on http://127.0.0.1:5000
* Running on http://192.168.1.162:5000
```

- Open the `127.0.0.1` link on the same PC.
- Open the `192.168.x.x` link from your phone or another device **on the
  same Wi-Fi network**.

Leave the terminal window open while using the app — closing it stops the
server.

## Notes

- No public/internet URL is used — everything stays on your local network.
- Each teammate runs their own copy locally; there is no shared server.
