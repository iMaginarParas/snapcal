import 'package:flutter/material.dart';

class MetricsRow extends StatelessWidget {
  final double distance;
  final int calories;
  final int duration;

  const MetricsRow({
    Key? key,
    required this.distance,
    required this.calories,
    required this.duration,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildMetricItem(
          icon: Icons.directions_walk,
          value: '${distance.toStringAsFixed(1)} km',
          label: 'Distance',
          progress: (distance / 10).clamp(0.0, 1.0),
          color: Colors.greenAccent,
        ),
        _buildMetricItem(
          icon: Icons.local_fire_department,
          value: '$calories kcal',
          label: 'Calories',
          progress: (calories / 500).clamp(0.0, 1.0),
          color: Colors.orangeAccent,
        ),
        _buildMetricItem(
          icon: Icons.timer,
          value: '$duration min',
          label: 'Active Time',
          progress: (duration / 60).clamp(0.0, 1.0),
          color: Colors.cyanAccent,
        ),
      ],
    );
  }

  Widget _buildMetricItem({
    required IconData icon,
    required String value,
    required String label,
    required double progress,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        margin: const EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white60,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 4,
              child: LinearProgressIndicator(
                value: progress,
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
