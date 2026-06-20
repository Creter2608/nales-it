import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/quiz_models.dart';
import '../data/quiz_repository.dart';

class QuizState {
  final AsyncValue<Quiz?> quiz;
  final QuizMode mode;
  final int currentQuestionIndex;
  final Map<String, String> userAnswers; // questionId -> answerId
  final bool isSubmitted;
  final AsyncValue<Map<String, dynamic>?> gradeResult;

  QuizState({
    this.quiz = const AsyncLoading(),
    this.mode = QuizMode.instantFeedback,
    this.currentQuestionIndex = 0,
    this.userAnswers = const {},
    this.isSubmitted = false,
    this.gradeResult = const AsyncData(null),
  });

  QuizState copyWith({
    AsyncValue<Quiz?>? quiz,
    QuizMode? mode,
    int? currentQuestionIndex,
    Map<String, String>? userAnswers,
    bool? isSubmitted,
    AsyncValue<Map<String, dynamic>?>? gradeResult,
  }) {
    return QuizState(
      quiz: quiz ?? this.quiz,
      mode: mode ?? this.mode,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      userAnswers: userAnswers ?? this.userAnswers,
      isSubmitted: isSubmitted ?? this.isSubmitted,
      gradeResult: gradeResult ?? this.gradeResult,
    );
  }
}

final quizStateProvider = StateNotifierProvider.family<QuizNotifier, QuizState, String>((ref, quizId) {
  return QuizNotifier(ref.watch(quizRepositoryProvider), quizId);
});

class QuizNotifier extends StateNotifier<QuizState> {
  final QuizRepository _repository;
  final String quizId;

  QuizNotifier(this._repository, this.quizId) : super(QuizState()) {
    _loadQuiz();
  }

  Future<void> _loadQuiz() async {
    try {
      final quiz = await _repository.getQuiz(quizId);
      state = state.copyWith(quiz: AsyncData(quiz));
    } catch (e, stack) {
      state = state.copyWith(quiz: AsyncError(e, stack));
    }
  }

  void setMode(QuizMode mode) {
    state = state.copyWith(mode: mode);
  }

  void selectAnswer(String questionId, String answerId) {
    if (state.isSubmitted) return;
    
    final newAnswers = Map<String, String>.from(state.userAnswers);
    newAnswers[questionId] = answerId;
    state = state.copyWith(userAnswers: newAnswers);
  }

  void nextQuestion() {
    if (state.quiz is AsyncData && state.quiz.value != null) {
      if (state.currentQuestionIndex < state.quiz.value!.questions.length - 1) {
        state = state.copyWith(currentQuestionIndex: state.currentQuestionIndex + 1);
        
        // Lazy Loading: Kéo đáp án mới từ server nếu câu hiện tại chưa có đáp án
        final nextQ = state.quiz.value!.questions[state.currentQuestionIndex];
        if (nextQ.correctAnswerId == null) {
          refreshQuiz();
        }
      }
    }
  }

  void previousQuestion() {
    if (state.currentQuestionIndex > 0) {
      state = state.copyWith(currentQuestionIndex: state.currentQuestionIndex - 1);
    }
  }

  Future<void> submitQuiz() async {
    if (state.mode == QuizMode.practice || state.mode == QuizMode.instantFeedback) {
      state = state.copyWith(isSubmitted: true);
      return;
    }

    state = state.copyWith(isSubmitted: true, gradeResult: const AsyncLoading());
    try {
      final result = await _repository.gradeQuiz(quizId, state.userAnswers);
      state = state.copyWith(gradeResult: AsyncData(result));
    } catch (e, stack) {
      state = state.copyWith(gradeResult: AsyncError(e, stack));
    }
  }

  Future<void> refreshQuiz() async {
    if (state.quiz is! AsyncData || state.quiz.value == null) return;
    try {
      final updatedQuizData = await _repository.getQuiz(quizId);
      state = state.copyWith(quiz: AsyncData(updatedQuizData));
    } catch (e) {
      print("Lỗi refresh quiz: $e");
    }
  }

  Future<void> resolveQuestion(String questionId) async {
    try {
      final result = await _repository.resolveQuestion(quizId, questionId);
      if (result['status'] == 'success') {
        await refreshQuiz();
      }
    } catch (e) {
      throw Exception('Không thể giải lại lúc này: $e');
    }
  }
}
