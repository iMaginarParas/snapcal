class StepData {
  final int steps;
  final double distanceMeters;
  final int calories;
  final int durationMinutes;
  final DateTime timestamp;

  StepData({
    required this.steps,
    required this.distanceMeters,
    this.calories = 0,
    this.durationMinutes = 0,
    required this.timestamp,
  });

  factory StepData.fromJson(Map<String, dynamic> json) {
    return StepData(
      steps: json['steps'] ?? 0,
      distanceMeters: (json['distance'] ?? 0.0).toDouble(),
      calories: json['calories'] ?? 0,
      durationMinutes: json['duration'] ?? 0,
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp']) 
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'steps': steps,
    'distance': distanceMeters,
    'calories': calories,
    'duration': durationMinutes,
    'timestamp': timestamp.toIso8601String(),
  };
}
