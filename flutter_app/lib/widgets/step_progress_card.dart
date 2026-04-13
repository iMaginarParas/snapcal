import 'package:flutter/material.dart';
import 'dart:math';

class StepProgressCard extends StatelessWidget {
  final int steps;
  final int goal;

  const StepProgressCard({
    Key? key,
    required this.steps,
    required this.goal,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    double progress = (steps / goal).clamp(0.0, 1.0);
    int remaining = max(0, goal - steps);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1E3A8A).withOpacity(0.8),
            const Color(0xFF3B82F6).withOpacity(0.5),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(32),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          SizedBox(
            height: 200,
            width: 200,
            child: Stack(
              alignment: Alignment.center,
              children: [
                ShaderMask(
                  shaderCallback: (rect) {
                    return const SweepGradient(
                      startAngle: 0.0,
                      endAngle: 2 * pi,
                      stops: [0.0, 1.0],
                      center: Alignment.center,
                      colors: [Color(0xFF60A5FA), Color(0xFF3B82F6)],
                    ).createShader(rect);
                  },
                  child: CircularProgressIndicator(
                    value: progress,
                    strokeWidth: 15,
                    backgroundColor: Colors.white.withOpacity(0.1),
                    valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'Steps Taken',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      steps.toString().replaceAllMapped(
                          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
                          (Match m) => '${m[1]},'),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 42,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$remaining remaining',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.6),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.flag, color: Colors.white70, size: 20),
              const SizedBox(width: 8),
              Text(
                'Step Goal: $goal steps',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
