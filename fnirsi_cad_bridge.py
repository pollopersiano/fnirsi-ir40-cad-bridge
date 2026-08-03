import asyncio
import csv
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyperclip
from bleak import BleakScanner, BleakClient

# --- UUID BLE ---
SERVICE_UUID = "0000ee01-0000-1000-8000-00805f9b34fb"
RX_CHAR_UUID = "0000ee02-0000-1000-8000-00805f9b34fb"  # Notifiche misura
TX_CHAR_UUID = "0000ee03-0000-1000-8000-00805f9b34fb"  # Scrittura comandi

# --- COMANDI ESSENZIALI ---
CMD_START_CONTINUOUS = bytes([0x00, 0x07, 0x02, 0x08, 0x0E, 0x00, 0x00, 0x00, 0x01])
CMD_STOP_CONTINUOUS  = bytes([0x00, 0x07, 0x02, 0x08, 0x0E, 0x00, 0x00, 0x00, 0x00])
CMD_PING             = bytes([0x00, 0x01, 0x02]) 

CSV_FILE = "fnirsi_measurements.csv"
LANG_FILE = "translations.json"

class FNIRSIApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = "en"  # Default Inglese
        self.load_translations()
        
        self.root.title(self.t("title"))
        self.root.geometry("550x680")
        self.root.configure(bg="#242424")

        self.client = None
        self.is_connected = False
        self.is_measuring = False

        self.autocopy = tk.BooleanVar(value=True)
        self.use_comma = tk.BooleanVar(value=False)
        self.unit_var = tk.StringVar(value="m")

        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()

        self.setup_csv()
        self.build_ui()

    def load_translations(self):
        default_trans = {
            "en": {
                "title": "FNIRSI IR40 - CAD Bridge", "status_disconnected": "Status: Disconnected 🔴",
                "status_searching": "Status: Searching device... 🟡", "status_connected": "Status: Connected ✅",
                "btn_connect": "Connect Bluetooth", "btn_disconnect": "Disconnect",
                "btn_start_meas": "Start Measurement", "btn_stop_meas": "Stop Measurement",
                "lbl_unit": "App/CAD Unit:",
                "chk_comma": "Use comma (,) instead of dot (.) for European CAD",
                "chk_autocopy": "Auto-copy to clipboard (ready for CTRL+V)",
                "lbl_history": "Measurement History (saved to CSV):", "col_time": "Time",
                "col_value": "Copied Value", "col_raw": "Raw (mm)", "err_not_found_title": "Error",
                "err_not_found_msg": "FNIRSI IR40 not found!\nMake sure it is powered on.",
                "err_conn_msg": "Could not connect:\n"
            }
        }
        if os.path.exists(LANG_FILE):
            try:
                with open(LANG_FILE, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception:
                self.translations = default_trans
        else:
            self.translations = default_trans

    def t(self, key):
        return self.translations.get(self.current_lang, {}).get(key, key)

    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def setup_csv(self):
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Value", "Unit", "Raw_mm"])

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#242424")
        style.configure("TLabel", background="#242424", foreground="#ffffff", font=("Segoe UI", 10))

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header: Stato + Lingua
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(header_frame, text=self.t("status_disconnected"), font=("Segoe UI", 11, "bold"), foreground="#FF6B6B")
        self.status_label.pack(side=tk.LEFT)

        lang_cb = ttk.Combobox(header_frame, values=["🇬🇧 EN", "🇮🇹 IT"], state="readonly", width=6)
        lang_cb.current(0)
        lang_cb.pack(side=tk.RIGHT)
        lang_cb.bind("<<ComboboxSelected>>", self.change_language)

        # Pulsanti Connessione / Misura
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_connect = tk.Button(btn_frame, text=self.t("btn_connect"), command=self.toggle_connection,
                                     bg="#43AA59", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10, pady=5)
        self.btn_connect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_measure = tk.Button(btn_frame, text=self.t("btn_start_meas"), command=self.toggle_measurement,
                                     bg="#CCA949", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10, pady=5, state=tk.DISABLED)
        self.btn_measure.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Display Misura Grande
        disp_frame = tk.Frame(main_frame, bg="#1E1E1E", bd=1, relief=tk.SOLID)
        disp_frame.pack(fill=tk.X, pady=15, ipady=15)

        self.lbl_measure = tk.Label(disp_frame, text="0.000 m", font=("Segoe UI", 36, "bold"), bg="#1E1E1E", fg="#4E9F3D")
        self.lbl_measure.pack()

        # Selezione Unità App/CAD
        opts_frame = ttk.Frame(main_frame)
        opts_frame.pack(fill=tk.X, pady=5)

        self.lbl_unit_title = ttk.Label(opts_frame, text=self.t("lbl_unit"), font=("Segoe UI", 10, "bold"))
        self.lbl_unit_title.pack(side=tk.LEFT, padx=(0, 10))

        unit_cb = ttk.Combobox(opts_frame, textvariable=self.unit_var, state="readonly", width=18,
                               values=["m (Meters)", "dm (Decimeters)", "cm (Centimeters)", "mm (Millimeters)"])
        unit_cb.current(0)
        unit_cb.pack(side=tk.LEFT)

        # Checkbox Opzioni
        chk_frame = ttk.Frame(main_frame)
        chk_frame.pack(fill=tk.X, pady=(10, 5))

        self.chk_comma_btn = tk.Checkbutton(chk_frame, text=self.t("chk_comma"), variable=self.use_comma,
                                            bg="#242424", fg="white", selectcolor="#1E1E1E", font=("Segoe UI", 10))
        self.chk_comma_btn.pack(anchor=tk.W)

        self.chk_autocopy_btn = tk.Checkbutton(chk_frame, text=self.t("chk_autocopy"), variable=self.autocopy,
                                               bg="#242424", fg="white", selectcolor="#1E1E1E", font=("Segoe UI", 10))
        self.chk_autocopy_btn.pack(anchor=tk.W, pady=(3, 0))

        # Tabella Storico
        self.lbl_history_title = ttk.Label(main_frame, text=self.t("lbl_history"), font=("Segoe UI", 10, "bold"))
        self.lbl_history_title.pack(anchor=tk.W, pady=(12, 5))

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("time", "value_formatted", "value_mm")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        self.tree.heading("time", text=self.t("col_time"))
        self.tree.heading("value_formatted", text=self.t("col_value"))
        self.tree.heading("value_mm", text=self.t("col_raw"))

        self.tree.column("time", width=110, anchor=tk.CENTER)
        self.tree.column("value_formatted", width=180, anchor=tk.CENTER)
        self.tree.column("value_mm", width=120, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def change_language(self, event):
        selection = event.widget.get()
        self.current_lang = "en" if "EN" in selection else "it"
        
        self.root.title(self.t("title"))
        self.lbl_unit_title.config(text=self.t("lbl_unit"))
        self.chk_comma_btn.config(text=self.t("chk_comma"))
        self.chk_autocopy_btn.config(text=self.t("chk_autocopy"))
        self.lbl_history_title.config(text=self.t("lbl_history"))
        
        self.tree.heading("time", text=self.t("col_time"))
        self.tree.heading("value_formatted", text=self.t("col_value"))
        self.tree.heading("value_mm", text=self.t("col_raw"))

        if not self.is_connected:
            self.status_label.config(text=self.t("status_disconnected"))
            self.btn_connect.config(text=self.t("btn_connect"))
            self.btn_measure.config(text=self.t("btn_start_meas"))
        else:
            self.status_label.config(text=self.t("status_connected"))
            self.btn_connect.config(text=self.t("btn_disconnect"))
            self.btn_measure.config(text=self.t("btn_stop_meas") if self.is_measuring else self.t("btn_start_meas"))

    def toggle_connection(self):
        if not self.is_connected:
            self.btn_connect.config(state=tk.DISABLED, text="..." )
            self.status_label.config(text=self.t("status_searching"), foreground="#FFB03A")
            asyncio.run_coroutine_threadsafe(self.connect_ble(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.disconnect_ble(), self.loop)

    async def connect_ble(self):
        try:
            device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name and "fnirsi" in d.name.lower(),
                timeout=10.0
            )

            if not device:
                self.root.after(0, lambda: messagebox.showerror(self.t("err_not_found_title"), self.t("err_not_found_msg")))
                self.root.after(0, self.reset_conn_ui)
                return

            self.client = BleakClient(device.address)
            await self.client.connect()
            await self.client.start_notify(RX_CHAR_UUID, self.handle_ble_notification)

            self.is_connected = True
            asyncio.run_coroutine_threadsafe(self._keep_alive_loop(), self.loop)

            self.root.after(0, lambda: self.status_label.config(text=self.t("status_connected"), foreground="#4E9F3D"))
            self.root.after(0, lambda: self.btn_connect.config(state=tk.NORMAL, text=self.t("btn_disconnect"), bg="#AA4343"))
            self.root.after(0, lambda: self.btn_measure.config(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(self.t("err_not_found_title"), f"{self.t('err_conn_msg')}{e}"))
            self.root.after(0, self.reset_conn_ui)

    async def _keep_alive_loop(self):
        while self.is_connected:
            try:
                if self.client and self.client.is_connected and not self.is_measuring:
                    await self.client.write_gatt_char(TX_CHAR_UUID, CMD_PING)
                await asyncio.sleep(2.0)
            except Exception:
                break

    async def disconnect_ble(self):
        self.is_connected = False
        try:
            if self.client and self.client.is_connected:
                if self.is_measuring:
                    await self.client.write_gatt_char(TX_CHAR_UUID, CMD_STOP_CONTINUOUS)
                await self.client.stop_notify(RX_CHAR_UUID)
                await self.client.disconnect()
        except Exception:
            pass

        self.is_measuring = False
        self.root.after(0, self.reset_conn_ui)

    def reset_conn_ui(self):
        self.status_label.config(text=self.t("status_disconnected"), foreground="#FF6B6B")
        self.btn_connect.config(state=tk.NORMAL, text=self.t("btn_connect"), bg="#43AA59")
        self.btn_measure.config(state=tk.DISABLED, text=self.t("btn_start_meas"), bg="#CCA949")

    def toggle_measurement(self):
        if not self.is_measuring:
            asyncio.run_coroutine_threadsafe(self.send_cmd(CMD_START_CONTINUOUS), self.loop)
            self.is_measuring = True
            self.btn_measure.config(text=self.t("btn_stop_meas"), bg="#AA4343")
        else:
            asyncio.run_coroutine_threadsafe(self.send_cmd(CMD_STOP_CONTINUOUS), self.loop)
            self.is_measuring = False
            self.btn_measure.config(text=self.t("btn_start_meas"), bg="#CCA949")

    async def send_cmd(self, cmd):
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(TX_CHAR_UUID, cmd)
            except Exception as e:
                print(f"Error sending command: {e}")

    def handle_ble_notification(self, sender, data: bytearray):
        if len(data) >= 16:
            raw_mm = int.from_bytes(data[14:16], byteorder='big', signed=False)
            if raw_mm > 50:
                now_str = datetime.now().strftime("%H:%M:%S")
                self.root.after(0, lambda: self.update_measurement(now_str, raw_mm))

    def update_measurement(self, timestamp, raw_mm):
        unit_selected = self.unit_var.get()

        if "dm" in unit_selected:
            converted_val = raw_mm / 100.0
            val_str = f"{converted_val:.2f}"
            unit_code = "dm"
        elif "cm" in unit_selected:
            converted_val = raw_mm / 10.0
            val_str = f"{converted_val:.1f}"
            unit_code = "cm"
        elif "mm" in unit_selected:
            converted_val = raw_mm
            val_str = f"{converted_val}"
            unit_code = "mm"
        else:
            converted_val = raw_mm / 1000.0
            val_str = f"{converted_val:.3f}"
            unit_code = "m"

        if self.use_comma.get():
            val_str = val_str.replace('.', ',')

        display_str = f"{val_str} {unit_code}"
        self.lbl_measure.config(text=display_str)

        if self.autocopy.get():
            try:
                pyperclip.copy(val_str)
            except Exception:
                pass

        self.tree.insert("", 0, values=(timestamp, display_str, f"{raw_mm} mm"))

        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, val_str, unit_code, raw_mm])

if __name__ == "__main__":
    root = tk.Tk()
    app = FNIRSIApp(root)
    root.mainloop()