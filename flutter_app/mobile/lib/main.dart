import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/dashboard_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/steps_screen.dart';
import 'screens/history_screen.dart';
import 'screens/login_screen.dart';
import 'services/step_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final stepService = StepService();
  await stepService.initPlatformState();

  final prefs = await SharedPreferences.getInstance();
  final hasToken = prefs.getString('token') != null;

  runApp(
    MultiProvider(
      providers: [
        Provider<StepService>.value(value: stepService),
      ],
      child: FitSnapApp(initialRoute: hasToken ? '/' : '/login'),
    ),
  );
}

class FitSnapApp extends StatelessWidget {
  final String initialRoute;
  const FitSnapApp({super.key, required this.initialRoute});

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
      initialRoute: initialRoute,
      routes: {
        '/': (context) => const DashboardScreen(),
        '/login': (context) => const LoginScreen(),
        '/camera': (context) => const CameraScreen(),
        '/steps': (context) => const StepsScreen(),
        '/history': (context) => const HistoryScreen(),
      },
    );
  }
}
