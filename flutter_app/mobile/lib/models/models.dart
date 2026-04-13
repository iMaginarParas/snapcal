class User {
  final int id;
  final String email;
  final double? height;
  final double? weight;
  final int? age;
  final String? gender;

  User({
    required this.id,
    required this.email,
    this.height,
    this.weight,
    this.age,
    this.gender,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      height: json['height']?.toDouble(),
      weight: json['weight']?.toDouble(),
      age: json['age'],
      gender: json['gender'],
    );
  }
}

class Meal {
  final int id;
  final String foodName;
  final double calories;
  final double protein;
  final double carbs;
  final double fat;
  final String? portionSize;
  final String? imageUrl;
  final DateTime createdAt;

  Meal({
    required this.id,
    required this.foodName,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    this.portionSize,
    this.imageUrl,
    required this.createdAt,
  });

  factory Meal.fromJson(Map<String, dynamic> json) {
    return Meal(
      id: json['id'],
      foodName: json['food_name'],
      calories: json['calories'].toDouble(),
      protein: json['protein'].toDouble(),
      carbs: json['carbs'].toDouble(),
      fat: json['fat'].toDouble(),
      portionSize: json['portion_size'],
      imageUrl: json['image_url'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class StepData {
  final int steps;
  final double distance;
  final double caloriesBurned;
  final DateTime date;

  StepData({
    required this.steps,
    required this.distance,
    required this.caloriesBurned,
    required this.date,
  });

  factory StepData.fromJson(Map<String, dynamic> json) {
    return StepData(
      steps: json['step_count'],
      distance: json['distance'].toDouble(),
      caloriesBurned: json['calories_burned'].toDouble(),
      date: DateTime.parse(json['date']),
    );
  }
}
