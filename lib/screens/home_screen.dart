import 'package:flutter/material.dart';
import 'dart:async';
import '../services/health_service.dart';
import '../models/step_data.dart';
import '../widgets/step_progress_card.dart';
import '../widgets/metrics_row.dart';
import '../widgets/activity_list.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final HealthService _healthService = HealthService();
  int _steps = 0;
  double _distance = 0.0;
  int _calories = 0;
  int _activeTime = 0;
  List<StepData> _activities = [];
  bool _isLoading = true;
  bool _isSupported = true;
  StreamSubscription<int>? _stepSubscription;

  @override
  void initState() {
    super.initState();
    _checkHardwareAndStart();
  }

  Future<void> _checkHardwareAndStart() async {
    // 1. Check hardware compatibility
    _isSupported = await _healthService.isStepTrackingSupported();
    if (!_isSupported) {
      setState(() => _isLoading = false);
      return;
    }

    // 2. Perform initial fetch (Silent)
    await _fetchData(silent: false);

    // 3. Listen to real-time background stream
    _stepSubscription = _healthService.stepStream.listen((steps) {
       if (mounted) {
         setState(() {
           _steps = steps;
           _calories = (_steps * 0.04).toInt();
           _activeTime = (_steps / 100).toInt();
         });
       }
    }, onError: (err) => debugPrint("Stream Error: $err"));
  }

  @override
  void dispose() {
    _stepSubscription?.cancel();
    super.dispose();
  }

  Future<void> _fetchData({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);
    
    try {
      final bool granted = await _healthService.requestPermissions();
      if (granted) {
        final steps = await _healthService.getTodaySteps();
        final distance = await _healthService.getTodayDistance();
        final weekly = await _healthService.getWeeklySteps();
        
        if (mounted) {
          setState(() {
            _steps = steps;
            _distance = distance > 0 ? (distance / 1000) : 0.0;
            _calories = (steps * 0.04).toInt();
            _activeTime = (steps / 100).toInt();
            _activities = weekly;
            _isLoading = false;
          });
        }
      } else {
        if (mounted) setState(() => _isLoading = false);
      }
    } catch (e) {
      debugPrint("Error fetching data: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isSupported) {
      return Scaffold(
        backgroundColor: const Color(0xFF0F172A),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Text(
              "Step tracking hardware is not supported on this device.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white70, fontSize: 18),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => _fetchData(silent: false),
          color: Colors.blueAccent,
          backgroundColor: const Color(0xFF1E293B),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(),
                const SizedBox(height: 16),
                _buildWeeklyCalendar(),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: StepProgressCard(steps: _steps, goal: 10000),
                ),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: MetricsRow(
                    distance: _distance,
                    calories: _calories,
                    duration: _activeTime,
                  ),
                ),
                const SizedBox(height: 32),
                ActivityList(sessions: _activities),
                const SizedBox(height: 80),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'StepTracker',
                style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
              ),
              Text(
                'Production Release',
                style: TextStyle(color: Colors.white60, fontSize: 14),
              ),
            ],
          ),
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.sync, color: Colors.blueAccent),
                onPressed: () => _fetchData(silent: false),
                tooltip: 'Sync Now',
              ),
              const SizedBox(width: 8),
              CircleAvatar(
                backgroundColor: Colors.blueAccent.withOpacity(0.2),
                child: const Icon(Icons.person, color: Colors.blueAccent),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyCalendar() {
    final days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final dates = [30, 31, 1, 2, 3, 4, 5];
    
    return SizedBox(
      height: 85,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 8),
        itemCount: 7,
        itemBuilder: (context, index) {
          bool isSelected = index == 0; 
          return Container(
            width: 55,
            margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: isSelected ? Colors.blueAccent : const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  days[index],
                  style: TextStyle(
                    color: isSelected ? Colors.white : Colors.white60,
                    fontSize: 12,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  dates[index].toString(),
                  style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
