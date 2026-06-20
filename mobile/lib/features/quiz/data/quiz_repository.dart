import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../upload/data/upload_repository.dart';
import '../domain/quiz_models.dart';

final quizRepositoryProvider = Provider((ref) {
  return QuizRepository(ref.watch(dioProvider));
});

class QuizRepository {
  final Dio _dio;
  
  QuizRepository(this._dio);

  Future<Quiz> getQuiz(String quizId) async {
    final response = await _dio.get('/api/v1/quiz/$quizId');
    return Quiz.fromJson(response.data);
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
