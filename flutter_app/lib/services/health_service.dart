import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../models/step_data.dart';

class HealthService {
  static const MethodChannel _channel = MethodChannel('health_bridge');
  static const EventChannel _eventChannel = EventChannel('step_event_channel');

  bool get _isSupported => !kIsWeb && (Platform.isAndroid || Platform.isIOS);

  // Stream for real-time foreground/background step updates
  Stream<int> get stepStream {
    if (!Platform.isAndroid) return Stream.value(0);
    return _eventChannel
        .receiveBroadcastStream()
        .map((event) => event is int ? event : (event as num).toInt());
  }

  Future<bool> isStepTrackingSupported() async {
    if (!_isSupported) return false;
    try {
      final bool supported = await _channel.invokeMethod('isStepTrackingSupported');
      return supported;
    } on PlatformException {
      // iOS might not have 'isStepTrackingSupported' method implemented in the switch case
      // Let's check AppDelegate.swift again.
      return Platform.isIOS; 
    }
  }

  Future<bool> requestPermissions() async {
    if (!_isSupported) return true;
    try {
      final bool granted = await _channel.invokeMethod('requestPermissions');
      return granted;
    } on PlatformException catch (e) {
      print("Failed to request permissions: '${e.message}'.");
      return false;
    }
  }

  Future<int> getTodaySteps() async {
    if (!_isSupported) return 0;
    try {
      final int steps = await _channel.invokeMethod('getTodaySteps');
      return steps;
    } on PlatformException catch (e) {
      print("Failed to get today steps: '${e.message}'.");
      return 0;
    }
  }

  Future<double> getTodayDistance() async {
    if (!_isSupported) return 0.0;
    try {
      final double distance = await _channel.invokeMethod('getTodayDistance');
      return distance;
    } on PlatformException catch (e) {
      print("Failed to get today distance: '${e.message}'.");
      return 0.0;
    }
  }

  Future<List<StepData>> getWeeklySteps() async {
    if (!_isSupported) return [];
    try {
      final String result = await _channel.invokeMethod('getWeeklySteps');
      final List<dynamic> data = jsonDecode(result);
      return data.map((item) => StepData.fromJson(item)).toList();
    } on PlatformException catch (e) {
      print("Failed to get weekly steps: '${e.message}'.");
      return [];
    }
  }
}
