package com.example.fnirsi

import android.Manifest
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.ClipboardManager
import android.content.ClipData
import android.content.Context
import android.content.pm.PackageManager
import android.os.*
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private val SERVICE_UUID = UUID.fromString("0000ee01-0000-1000-8000-00805f9b34fb")
    private val TX_UUID = UUID.fromString("0000ee03-0000-1000-8000-00805f9b34fb")
    private val CLIENT_CONFIG = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

    private lateinit var tvStatus: TextView
    private lateinit var tvDistance: TextView
    private lateinit var btnConnect: Button

    private var bluetoothGatt: BluetoothGatt? = null
    private var bluetoothAdapter: BluetoothAdapter? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvStatus = findViewById(R.id.tvStatus)
        tvDistance = findViewById(R.id.tvDistance)
        btnConnect = findViewById(R.id.btnConnect)

        val btManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = btManager.adapter

        btnConnect.setOnClickListener {
            checkPermissionsAndScan()
        }
    }

    private fun checkPermissionsAndScan() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ActivityCompat.requestPermissions(this, arrayOf(
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.ACCESS_FINE_LOCATION
            ), 1)
        } else {
            ActivityCompat.requestPermissions(this, arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION
            ), 1)
        }
        startScan()
    }

    private fun startScan() {
        tvStatus.text = "Ricerca dispositivi..."
        val scanner = bluetoothAdapter?.bluetoothLeScanner
        scanner?.startScan(object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult?) {
                val device = result?.device ?: return
                val name = device.name ?: ""
                if (name.contains("IR40") || name.contains("FNIRSI")) {
                    scanner.stopScan(this)
                    connectToDevice(device)
                }
            }
        })
    }

    private fun connectToDevice(device: BluetoothDevice) {
        tvStatus.text = "Connessione in corso..."
        bluetoothGatt = device.connectGatt(this, false, object : BluetoothGattCallback() {
            override fun onConnectionStateChange(gatt: BluetoothGatt?, status: Int, newState: Int) {
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    runOnUiThread { tvStatus.text = "🟢 Connesso" }
                    gatt?.discoverServices()
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    runOnUiThread { tvStatus.text = "🔴 Disconnesso" }
                }
            }

            override fun onServicesDiscovered(gatt: BluetoothGatt?, status: Int) {
                val service = gatt?.getService(SERVICE_UUID)
                val characteristic = service?.getCharacteristic(TX_UUID)
                if (characteristic != null) {
                    gatt.setCharacteristicNotification(characteristic, true)
                    val descriptor = characteristic.getDescriptor(CLIENT_CONFIG)
                    descriptor?.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                    gatt.writeDescriptor(descriptor)
                }
            }

            override fun onCharacteristicChanged(gatt: BluetoothGatt?, characteristic: BluetoothGattCharacteristic?) {
                val bytes = characteristic?.value ?: return
                if (bytes.size >= 8) {
                    val rawVal = ((bytes[4].toInt() and 0xFF) shl 24) or
                                 ((bytes[5].toInt() and 0xFF) shl 16) or
                                 ((bytes[6].toInt() and 0xFF) shl 8) or
                                 (bytes[7].toInt() and 0xFF)
                    val distance = (rawVal and 0xFFFFFFFF.toInt()) / 1000.0
                    val formatted = String.format("%.3f m", distance)

                    runOnUiThread {
                        tvDistance.text = formatted
                        copyToClipboard(String.format("%.3f", distance))
                        vibrate()
                    }
                }
            }
        })
    }

    private fun copyToClipboard(text: String) {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("Distance", text)
        clipboard.setPrimaryClip(clip)
    }

    private fun vibrate() {
        val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            vibrator.vibrate(120)
        }
    }
}
