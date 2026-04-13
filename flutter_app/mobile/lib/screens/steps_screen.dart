import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/step_service.dart';

class StepsScreen extends StatelessWidget {
  const StepsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final stepService = Provider.of<StepService>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Activity Tracker')),
      body: SingleChildScrollView(
        padding: const EdgeInsets(20),
        child: Column(
          children: [
            _buildCircularProgress(stepService.todaySteps, 10000),
            const SizedBox(height: 30),
            _buildMetricsGrid(stepService),
            const SizedBox(height: 30),
            const Text('Weekly Progress', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            _buildStepsChart(),
          ],
        ),
      ),
    );
  }

  Widget _buildCircularProgress(int steps, int goal) {
    double progress = steps / goal;
    return Center(
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            height: 200,
            width: 200,
            child: CircularProgressIndicator(
              value: progress,
              strokeWidth: 15,
              backgroundColor: Colors.grey.shade200,
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.green),
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('$steps', style: const TextStyle(fontSize: 40, fontWeight: FontWeight.bold)),
              const Text('Steps Today', style: TextStyle(color: Colors.grey)),
              Text('Goal: $goal', style: const TextStyle(fontSize: 12, color: Colors.blue)),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildMetricsGrid(StepService steps) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      crossAxisSpacing: 15,
      mainAxisSpacing: 15,
      childAspectRatio: 1.2,
      children: [
        _buildMetricCard('Distance', '${(steps.distance / 1000).toStringAsFixed(2)}', 'km', Icons.directions_walk, Colors.blue),
        _buildMetricCard('Calories', '${steps.caloriesBurned.toStringAsFixed(0)}', 'kcal', Icons.local_fire_department, Colors.orange),
      ],
    );
  }

  Widget _buildMetricCard(String title, String value, String unit, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets(15),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 30),
          const SizedBox(height: 10),
          Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          Text('$unit $title', style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildStepsChart() {
    return SizedBox(
      height: 200,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: 12000,
          barGroups: [
            BarChartGroupData(x: 0, barRods: [BarRodData(toY: 5000, color: Colors.blue)]),
            BarChartGroupData(x: 1, barRods: [BarRodData(toY: 8000, color: Colors.blue)]),
            BarChartGroupData(x: 2, barRods: [BarRodData(toY: 10000, color: Colors.green)]),
            BarChartGroupData(x: 3, barRods: [BarRodData(toY: 6000, color: Colors.blue)]),
            BarChartGroupData(x: 4, barRods: [BarRodData(toY: 11000, color: Colors.green)]),
            BarChartGroupData(x: 5, barRods: [BarRodData(toY: 7500, color: Colors.blue)]),
            BarChartGroupData(x: 6, barRods: [BarRodData(toY: 9200, color: Colors.blue)]),
          ],
        ),
      ),
    );
  }
}
