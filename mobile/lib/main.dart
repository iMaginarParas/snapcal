import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/dashboard_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/steps_screen.dart';
import 'screens/history_screen.dart';
import 'services/step_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final stepService = StepService();
  await stepService.initPlatformState();

  runApp(
    MultiProvider(
      providers: [
        Provider<StepService>.value(value: stepService),
      ],
      child: const FitSnapApp(),
    ),
  );
}

class FitSnapApp extends StatelessWidget {
  const FitSnapApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitSnap AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.light,
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.dark,
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const DashboardScreen(),
        '/camera': (context) => const CameraScreen(),
        '/steps': (context) => const StepsScreen(),
        '/history': (context) => const HistoryScreen(),
      },
    );
  }
}
