import 'dart:async';
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
  final bool isStreaming;
  final String? progressMessage;

  QuizState({
    this.quiz = const AsyncLoading(),
    this.mode = QuizMode.instantFeedback,
    this.currentQuestionIndex = 0,
    this.userAnswers = const {},
    this.isSubmitted = false,
    this.gradeResult = const AsyncData(null),
    this.isStreaming = false,
    this.progressMessage,
  });

  QuizState copyWith({
    AsyncValue<Quiz?>? quiz,
    QuizMode? mode,
    int? currentQuestionIndex,
    Map<String, String>? userAnswers,
    bool? isSubmitted,
    AsyncValue<Map<String, dynamic>?>? gradeResult,
    bool? isStreaming,
    String? progressMessage,
  }) {
    return QuizState(
      quiz: quiz ?? this.quiz,
      mode: mode ?? this.mode,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      userAnswers: userAnswers ?? this.userAnswers,
      isSubmitted: isSubmitted ?? this.isSubmitted,
      gradeResult: gradeResult ?? this.gradeResult,
      isStreaming: isStreaming ?? this.isStreaming,
      progressMessage: progressMessage ?? this.progressMessage,
    );
  }
}

final quizStateProvider = StateNotifierProvider.family.autoDispose<QuizNotifier, QuizState, String>((ref, quizId) {
  return QuizNotifier(ref.watch(quizRepositoryProvider), quizId);
});

class QuizNotifier extends StateNotifier<QuizState> {
  final QuizRepository _repository;
  final String quizId;
  StreamSubscription<Map<String, dynamic>>? _streamSubscription;

  @override
  void dispose() {
    _streamSubscription?.cancel();
    super.dispose();
  }

  QuizNotifier(this._repository, this.quizId) : super(QuizState()) {
    if (quizId != "streaming") {
      _loadQuiz();
    }
  }

  Future<void> _loadQuiz() async {
    try {
      final quiz = await _repository.getQuiz(quizId);
      state = state.copyWith(quiz: AsyncData(quiz));
    } catch (e, stack) {
      state = state.copyWith(quiz: AsyncError(e, stack));
    }
  }

  void startStreamingQuiz(Stream<Map<String, dynamic>> stream) {
    state = state.copyWith(
      isStreaming: true,
      progressMessage: "Đang phân tích định dạng văn bản...",
      quiz: AsyncData(Quiz(title: "Đang xử lý PDF...", questions: [])),
    );

    _streamSubscription?.cancel();
    _streamSubscription = stream.listen((event) {
      final type = event['type'];
      final currentQuiz = state.quiz.value;
      if (currentQuiz == null) return;

      if (type == 'chunk') {
        final newQuestions = (event['questions'] as List)
            .map((e) => Question.fromJson(e))
            .toList();
        state = state.copyWith(
          quiz: AsyncData(
            Quiz(
              id: currentQuiz.id,
              title: currentQuiz.title,
              questions: [...currentQuiz.questions, ...newQuestions],
            ),
          ),
          progressMessage: "Đã trích xuất ${currentQuiz.questions.length + newQuestions.length} câu hỏi...",
        );
      } else if (type == 'progress') {
        state = state.copyWith(progressMessage: event['message']);
      } else if (type == 'images_mapped') {
        final updates = event['updates'] as List;
        final updateMap = {for (var u in updates) u['id'].toString(): u['image_base64']};
        final updatedQuestions = currentQuiz.questions.map((q) {
          if (updateMap.containsKey(q.id)) {
            return Question(
              id: q.id,
              content: q.content,
              answers: q.answers,
              correctAnswerId: q.correctAnswerId,
              explanation: q.explanation,
              sharedContext: q.sharedContext,
              imageBase64: updateMap[q.id],
            );
          }
          return q;
        }).toList();
        state = state.copyWith(
          quiz: AsyncData(
            Quiz(
              id: currentQuiz.id,
              title: currentQuiz.title,
              questions: updatedQuestions,
            ),
          ),
        );
      } else if (type == 'answers_solved') {
        final updates = event['updates'] as List;
        final updateMap = {for (var u in updates) u['id'].toString(): u};
        final updatedQuestions = currentQuiz.questions.map((q) {
          if (updateMap.containsKey(q.id)) {
            final u = updateMap[q.id];
            return Question(
              id: q.id,
              content: q.content,
              answers: q.answers,
              correctAnswerId: u['correct_answer_id'],
              explanation: u['explanation'],
              sharedContext: q.sharedContext,
              imageBase64: q.imageBase64,
            );
          }
          return q;
        }).toList();
        state = state.copyWith(
          quiz: AsyncData(
            Quiz(
              id: currentQuiz.id,
              title: currentQuiz.title,
              questions: updatedQuestions,
            ),
          ),
        );
      } else if (type == 'done') {
        final finalQuizData = event['quiz_data'];
        final finalTitle = event['title'] ?? currentQuiz.title;
        final finalId = event['quiz_id'] ?? currentQuiz.id;
        state = state.copyWith(
          isStreaming: false,
          quiz: AsyncData(
            Quiz(
              id: finalId,
              title: finalTitle,
              questions: currentQuiz.questions, // Keep the built list, since we updated incrementally!
            ),
          ),
        );
      } else if (type == 'error') {
        state = state.copyWith(
          isStreaming: false,
          quiz: AsyncError(event['detail'] ?? "Unknown error", StackTrace.current),
        );
      }
    }, onError: (error) {
      state = state.copyWith(
        isStreaming: false,
        quiz: AsyncError(error, StackTrace.current),
      );
    }, onDone: () {
      if (state.isStreaming) {
        state = state.copyWith(isStreaming: false);
      }
    });
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

  void jumpToQuestion(int index) {
    if (state.quiz is AsyncData && state.quiz.value != null) {
      if (index >= 0 && index < state.quiz.value!.questions.length) {
        state = state.copyWith(currentQuestionIndex: index);
        
        final targetQ = state.quiz.value!.questions[index];
        if (targetQ.correctAnswerId == null) {
          refreshQuiz();
        }
      }
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
