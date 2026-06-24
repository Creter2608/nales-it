import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import '../../features/quiz/domain/quiz_models.dart';

class CacheService {
  static const String _quizBoxName = 'quizzes';

  /// Initializes the Hive cache boxes. Call this during app startup.
  static Future<void> init() async {
    await Hive.openBox<String>(_quizBoxName);
  }

  /// Saves a Quiz to the cache.
  static Future<void> saveQuiz(Quiz quiz) async {
    if (quiz.id == null) return;
    final box = Hive.box<String>(_quizBoxName);
    // Serialize to JSON string since we didn't use Hive TypeAdapters
    final jsonString = jsonEncode(quiz.toJson());
    await box.put(quiz.id, jsonString);
  }

  /// Retrieves a Quiz from the cache by ID. Returns null if not found.
  static Quiz? getQuiz(String id) {
    final box = Hive.box<String>(_quizBoxName);
    final jsonString = box.get(id);
    if (jsonString != null) {
      try {
        final Map<String, dynamic> jsonMap = jsonDecode(jsonString);
        return Quiz.fromJson(jsonMap);
      } catch (e) {
        // Log corrupted cache error, but we don't have Sentry here unless we pass it.
        return null;
      }
    }
    return null;
  }

  /// Clears all cached quizzes.
  static Future<void> clearAll() async {
    final box = Hive.box<String>(_quizBoxName);
    await box.clear();
  }
}
