import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FNIRSI IR40 Bridge',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF121212),
        primaryColor: Colors.blueAccent,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  BluetoothDevice? _connectedDevice;
  StreamSubscription? _notifySubscription;
  String _status = "Disconnesso";
  String _lastDistance = "--- m";
  bool _isConnecting = false;

  final String serviceUuid = "ee01";
  final String txUuid = "ee03";

  Future<void> _startScanAndConnect() async {
    setState(() {
      _isConnecting = true;
      _status = "Ricerca laser...";
    });

    try {
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 8));

      FlutterBluePlus.scanResults.listen((results) async {
        for (ScanResult r in results) {
          if (r.device.platformName.contains("IR40") ||
              r.device.platformName.contains("FNIRSI") ||
              r.advertisementData.serviceUuids.any((u) => u.toString().contains(serviceUuid))) {
            
            await FlutterBluePlus.stopScan();
            await _connectToDevice(r.device);
            break;
          }
        }
      });
    } catch (e) {
      setState(() {
        _status = "Errore: $e";
        _isConnecting = false;
      });
    }
  }

  Future<void> _connectToDevice(BluetoothDevice device) async {
    setState(() => _status = "Connessione a ${device.platformName}...");
    try {
      await device.connect(autoConnect: false);
      _connectedDevice = device;

      List<BluetoothService> services = await device.discoverServices();
      for (var service in services) {
        if (service.uuid.toString().contains(serviceUuid)) {
          for (var characteristic in service.characteristics) {
            if (characteristic.uuid.toString().contains(txUuid)) {
              await characteristic.setNotifyValue(true);
              _notifySubscription = characteristic.lastValueStream.listen(_handleData);
              setState(() {
                _status = "🟢 Connesso";
                _isConnecting = false;
              });
            }
          }
        }
      }
    } catch (e) {
      setState(() {
        _status = "Errore connessione: $e";
        _isConnecting = false;
      });
    }
  }

  void _handleData(List<int> bytes) {
    if (bytes.length >= 8) {
      int rawVal = (bytes[4] << 24) | (bytes[5] << 16) | (bytes[6] << 8) | bytes[7];
      rawVal = rawVal & 0xFFFFFFFF;
      double distance = rawVal / 1000.0;
      String formatted = "${distance.toStringAsFixed(3)} m";

      setState(() {
        _lastDistance = formatted;
      });

      // Copia negli appunti
      Clipboard.setData(ClipboardData(text: distance.toStringAsFixed(3)));

      // Vibrazione nativa
      HapticFeedback.vibrate();
    }
  }

  @override
  void dispose() {
    _notifySubscription?.cancel();
    _connectedDevice?.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_status, style: const TextStyle(fontSize: 16, color: Colors.grey)),
              const SizedBox(height: 30),
              Text(
                _lastDistance,
                style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.greenAccent),
              ),
              const SizedBox(height: 40),
              ElevatedButton(
                onPressed: _isConnecting ? null : _startScanAndConnect,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                ),
                child: Text(_isConnecting ? "Connessione..." : "Connetti Laser"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
