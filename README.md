# 📏 FNIRSI IR40 - CAD Bridge

A lightweight Python GUI application that interfaces with the **FNIRSI IR40** laser distance meter via Bluetooth LE (GATT). 

It automatically captures measurements, converts units, and copies values to the clipboard in real-time for seamless integration into CAD software (AutoCAD, Rhino, SolidWorks, Revit, etc.).

---

## ✨ Features

* 📡 **BLE Connection**: Automatic device discovery and GATT notification handling.
* 📋 **Auto-Clipboard**: Instantly copies every measurement to your clipboard ready for `CTRL+V`.
* 🌍 **Localization (EN/IT)**: Multi-language support driven by an external `translations.json`. Default language set to **English**.
* 📐 **Unit Conversion**: Automatic live conversion to **m**, **dm**, **cm**, or **mm**.
* 🇪🇺 **European CAD Support**: Toggle between dot (`.`) and comma (`,`) decimal separators.
* 💾 **CSV Logging**: Automatically logs history to `fnirsi_measurements.csv`.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.9 or higher
* FNIRSI IR40 Laser Distance Meter (Bluetooth turned ON)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/pollopersiano/fnirsi-ir40-cad-bridge.git](https://github.com/pollopersiano/fnirsi-ir40-cad-bridge.git)
   cd fnirsi-ir40-cad-bridge