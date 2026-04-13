import 'dart:async';
import 'package:pedometer/pedometer.dart';
import 'package:permission_handler/permission_handler.dart';
import 'api_service.dart';

class StepService {
  final ApiService _apiService = ApiService();
  late Stream<StepCount> _stepCountStream;
  int _todaySteps = 0;
  double _stepLength = 0.78; // meters

  int get todaySteps => _todaySteps;
  double get distance => _todaySteps * _stepLength;
  double get caloriesBurned => _todaySteps * 0.04;

  Future<void> initPlatformState() async {
    if (await Permission.activityRecognition.request().isGranted) {
      _stepCountStream = Pedometer.stepCountStream;
      _stepCountStream.listen(_onStepCount).onError(_onStepCountError);
    }
  }

  void _onStepCount(StepCount event) {
    // Note: event.steps is total steps since boot.
    // In a production app, we would store the midnight value and subtract.
    _todaySteps = event.steps; 
    _syncWithBackend();
  }

  void _onStepCountError(error) {
    print('Step Count Error: $error');
  }

  void _syncWithBackend() {
    _apiService.updateSteps(_todaySteps, distance, caloriesBurned);
  }
}
