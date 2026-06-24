import 'dart:async';
import 'dart:developer' as developer;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/quiz_models.dart';
import '../data/quiz_repository.dart';

import 'package:freezed_annotation/freezed_annotation.dart';

part 'quiz_state.freezed.dart';

@freezed
abstract class QuizState with _$QuizState {
  const factory QuizState({
    @Default(AsyncLoading()) AsyncValue<Quiz?> quiz,
    @Default(QuizMode.instantFeedback) QuizMode mode,
    @Default(0) int currentQuestionIndex,
    @Default({}) Map<String, String> userAnswers,
    @Default(false) bool isSubmitted,
    @Default(AsyncData(null)) AsyncValue<Map<String, dynamic>?> gradeResult,
    @Default(false) bool isStreaming,
    String? progressMessage,
    @Default({}) Set<String> viewingAnswers,
    @Default({}) Set<String> loadingAnswers,
  }) = _QuizState;
}

final quizStateProvider = StateNotifierProvider.family.autoDispose<QuizNotifier, QuizState, String>((ref, quizId) {
  final keepAliveLink = ref.keepAlive();
  return QuizNotifier(ref.watch(quizRepositoryProvider), quizId, keepAliveLink);
});

class QuizNotifier extends StateNotifier<QuizState> {
  final QuizRepository _repository;
  final String quizId;
  final KeepAliveLink _keepAliveLink;
  StreamSubscription<Map<String, dynamic>>? _streamSubscription;

  @override
  void dispose() {
    _streamSubscription?.cancel();
    _keepAliveLink.close();
    super.dispose();
  }

  QuizNotifier(this._repository, this.quizId, this._keepAliveLink) : super(const QuizState()) {
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
    } finally {
      // Allow disposal after load completes
      _keepAliveLink.close();
    }
  }

  void startStreamingQuiz(Stream<Map<String, dynamic>> stream) {
    state = state.copyWith(
      isStreaming: true,
      progressMessage: "Đang phân tích định dạng văn bản...",
      quiz: const AsyncData(Quiz(title: "Đang xử lý PDF...", questions: [])),
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
        final quizId = event['quiz_id'];
        final title = event['title'];
        
        if (state.quiz is AsyncData && state.quiz.value != null) {
          final currentQuiz = state.quiz.value!;
          state = state.copyWith(
            isStreaming: false,
            quiz: AsyncData(currentQuiz.copyWith(
              id: quizId,
              title: title,
            ))
          );
        } else {
          state = state.copyWith(
            isStreaming: false,
            quiz: AsyncData(Quiz(
              id: quizId,
              title: title ?? "Không tìm thấy câu hỏi",
              questions: [],
            ))
          );
        }
        _keepAliveLink.close();
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
        if (state.quiz is! AsyncData) {
          state = state.copyWith(
            isStreaming: false,
            quiz: const AsyncData(Quiz(id: 'error', title: 'Lỗi', questions: []))
          );
        } else {
          state = state.copyWith(isStreaming: false);
        }
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
          resolveQuestion(nextQ.id, force: false);
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
          resolveQuestion(targetQ.id, force: false);
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
      developer.log("Error refreshing quiz: $e");
    }
  }

  void demandAnswer(String questionId) {
    // Add to viewing Answers
    final newViewing = Set<String>.from(state.viewingAnswers)..add(questionId);
    state = state.copyWith(viewingAnswers: newViewing);
    
    // Check if it needs resolving
    if (state.quiz.value != null) {
      final targetQ = state.quiz.value!.questions.firstWhere((q) => q.id == questionId);
      if (targetQ.correctAnswerId == null && !state.loadingAnswers.contains(questionId)) {
        resolveQuestion(questionId, force: false);
      }
    }
  }

  Future<void> resolveQuestion(String questionId, {bool force = true}) async {
    // Mark as loading
    final newLoading = Set<String>.from(state.loadingAnswers)..add(questionId);
    state = state.copyWith(loadingAnswers: newLoading);

    try {
      final result = await _repository.resolveQuestion(quizId, questionId, force: force);
      if (result['status'] == 'success') {
        // Force refresh local data
        await refreshQuiz();
      }
    } catch (e) {
      developer.log('Error resolving question: $e');
    } finally {
      // Remove from loading
      final endLoading = Set<String>.from(state.loadingAnswers)..remove(questionId);
      state = state.copyWith(loadingAnswers: endLoading);
    }
  }
}
