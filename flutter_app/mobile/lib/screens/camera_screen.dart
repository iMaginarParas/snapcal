import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  final ApiService _apiService = ApiService();
  File? _image;
  Meal? _detectedMeal;
  bool _isLoading = false;

  Future<void> _takePhoto() async {
    final XFile? photo = await _picker.pickImage(source: ImageSource.camera);
    if (photo != null) {
      setState(() {
        _image = File(photo.path);
        _detectedMeal = null;
        _isLoading = true;
      });
      
      final meal = await _apiService.uploadMeal(_image!);
      
      setState(() {
        _detectedMeal = meal;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detect Food')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets(20),
          child: Column(
            children: [
              if (_image != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: Image.file(_image!, height: 300, width: double.infinity, fit: BoxFit.cover),
                )
              else
                Container(
                  height: 300,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(Icons.camera_alt, size: 80, color: Colors.grey),
                ),
              const SizedBox(height: 30),
              if (_isLoading)
                const CircularProgressIndicator()
              else if (_detectedMeal != null)
                _buildMealResult()
              else
                ElevatedButton.icon(
                  onPressed: _takePhoto,
                  icon: const Icon(Icons.add_a_photo),
                  label: const Text('Capture Image'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMealResult() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets(20),
        child: Column(
          children: [
            Text(_detectedMeal!.foodName.toUpperCase(), 
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue)),
            const Divider(height: 30),
            _buildNutritionRow('Calories', '${_detectedMeal!.calories.toStringAsFixed(0)} kcal'),
            _buildNutritionRow('Protein', '${_detectedMeal!.protein.toStringAsFixed(1)} g'),
            _buildNutritionRow('Carbs', '${_detectedMeal!.carbs.toStringAsFixed(1)} g'),
            _buildNutritionRow('Fat', '${_detectedMeal!.fat.toStringAsFixed(1)} g'),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
              child: const Text('Save to Log'),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 16, color: Colors.grey)),
          Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
