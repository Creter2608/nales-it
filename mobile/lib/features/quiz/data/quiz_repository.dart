import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_provider.dart';
import '../../../core/cache/cache_service.dart';
import '../domain/quiz_models.dart';

final quizRepositoryProvider = Provider((ref) {
  return QuizRepository(ref.watch(dioProvider));
});

class QuizRepository {
  final Dio _dio;
  
  QuizRepository(this._dio);

  Future<Quiz> getQuiz(String quizId) async {
    try {
      final response = await _dio.get('/api/v1/quiz/$quizId');
      final quiz = Quiz.fromJson(response.data);
      // Cache the latest version
      await CacheService.saveQuiz(quiz);
      return quiz;
    } on DioException {
      // Fallback to cache on network errors
      final cachedQuiz = CacheService.getQuiz(quizId);
      if (cachedQuiz != null) {
        return cachedQuiz;
      }
      rethrow;
    }
  }

  Future<Map<String, dynamic>> resolveQuestion(String quizId, String questionId, {bool force = false}) async {
    final response = await _dio.post(
      '/api/v1/quiz/resolve',
      data: {
        'quiz_id': quizId,
        'question_id': questionId,
        'force': force,
      },
    );
    return response.data;
  }

  Future<Map<String, dynamic>> gradeQuiz(String quizId, Map<String, String> userAnswers) async {
    final response = await _dio.post(
      '/api/v1/quiz/grade',
      data: {
        'quiz_id': quizId,
        'user_answers': userAnswers,
      },
    );
    return response.data;
  }
}
