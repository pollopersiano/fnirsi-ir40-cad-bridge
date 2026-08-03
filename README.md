Markdown
# 📏 FNIRSI IR40 - CAD Bridge

A lightweight Python GUI application that interfaces with the **FNIRSI IR40** laser distance meter via Bluetooth LE (GATT).

It automatically captures measurements, converts units on the fly, and copies values to the clipboard in real-time for seamless integration into CAD software (AutoCAD, Rhino, SolidWorks, Revit, BricsCAD, etc.).

---

## ✨ Features

* 📡 **BLE Connection**: Automatic device discovery and reliable GATT notification handling.
* 📋 **Auto-Clipboard**: Instantly copies every measurement to your clipboard ready for CTRL+V into your CAD software.
* 🌍 **Multi-Language (EN/IT)**: Multi-language support driven by an external `translations.json`. Default language set to **English**.
* 📐 **Unit Conversion**: Automatic live conversion to **m**, **dm**, **cm**, or **mm**.
* 🇪🇺 **European CAD Support**: Toggle between dot (.) and comma (,) decimal separators to match CAD regional settings.
* 💾 **CSV Logging**: Automatically logs measurement history to `fnirsi_measurements.csv`.

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.9** or higher installed on your computer.
* **FNIRSI IR40** Laser Distance Meter (with Bluetooth turned ON).
* Bluetooth enabled on your PC.

### 2. Installation

Clone the repository and enter the folder:

git clone https://github.com/pollopersiano/fnirsi-ir40-cad-bridge.git
cd fnirsi-ir40-cad-bridge


Install the required Python packages:

pip install bleak pyperclip


### 3. Run the Application

Execute the main script from your terminal or command prompt:

python fnirsi_cad_bridge.py


---

## 📂 Project Structure

📁 fnirsi-ir40-cad-bridge/

├── 📄 fnirsi_cad_bridge.py     # Main application script
├── 📄 translations.json        # External UI translations (EN/IT)
├── 📄 README.md                # Project documentation
└── 📄 .gitignore               # Keeps log files out of Git


---

## ⚙️ How It Works

1. **Connect:** Click **Connect Bluetooth**. The app scans for the FNIRSI IR40 device.
2. **Measure:** Click **Start Measurement** or press the physical button on your laser device.
3. **Auto-Paste:** The measurement is converted and copied to your clipboard. Switch to CAD and press **CTRL+V**.

---

## 🙏 Credits & Acknowledgements

Special thanks to [MultiMote/fnirsi-ir40-webtool](https://github.com/MultiMote/fnirsi-ir40-webtool) for the initial reverse engineering of the FNIRSI IR40 Bluetooth protocol.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
