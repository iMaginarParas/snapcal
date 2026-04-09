import 'dart:io';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class ApiService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000', // Update to your machine IP for physical device
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  Future<String?> login(String email, String password) async {
    try {
      final formData = FormData.fromMap({
        'username': email,
        'password': password,
      });
      final response = await _dio.post('/auth/login', data: formData);
      final token = response.data['access_token'];
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', token);
      
      return token;
    } catch (e) {
      print('Login Error: $e');
      return null;
    }
  }

  Future<bool> register(String email, String password) async {
    try {
      await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
      });
      return true;
    } catch (e) {
      print('Registration Error: $e');
      return false;
    }
  }

  Future<Map<String, dynamic>?> getDashboardStats() async {
    try {
      final token = await _getToken();
      final response = await _dio.get('/stats/dashboard', 
        options: Options(headers: {'Authorization': 'Bearer $token'}));
      return response.data;
    } catch (e) {
      print('Dashboard Stats Error: $e');
      return null;
    }
  }

  Future<Meal?> uploadMeal(File imageFile) async {
    try {
      final token = await _getToken();
      String fileName = imageFile.path.split('/').last;
      FormData formData = FormData.fromMap({
        "file": await MultipartFile.fromFile(imageFile.path, filename: fileName),
      });

      final response = await _dio.post('/meals/', 
        data: formData,
        options: Options(headers: {'Authorization': 'Bearer $token'}));
      
      return Meal.fromJson(response.data);
    } catch (e) {
      print('Meal Upload Error: $e');
      return null;
    }
  }

  Future<List<Meal>> getMeals() async {
    try {
      final token = await _getToken();
      final response = await _dio.get('/meals/', 
        options: Options(headers: {'Authorization': 'Bearer $token'}));
      return (response.data as List).map((m) => Meal.fromJson(m)).toList();
    } catch (e) {
      print('Get Meals Error: $e');
      return [];
    }
  }

  Future<bool> updateSteps(int steps, double distance, double calories) async {
    try {
      final token = await _getToken();
      final now = DateTime.now();
      final dateStr = "${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}";
      
      await _dio.post('/steps/', 
        data: {
          'step_count': steps,
          'distance': distance,
          'calories_burned': calories,
          'date': dateStr,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}));
      return true;
    } catch (e) {
      print('Update Steps Error: $e');
      return false;
    }
  }

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
}
