import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/features/quiz/domain/quiz_models.dart';
import 'package:mobile/features/quiz/presentation/quiz_state.dart';
import 'package:mobile/core/config/app_config.dart';

void main() {
  // ---------------------------------------------------------------------------
  // Answer.fromJson
  // ---------------------------------------------------------------------------
  group('Answer.fromJson', () {
    test('parses valid JSON correctly', () {
      final json = {'id': 'a1', 'content': 'Paris'};

      final answer = Answer.fromJson(json);

      expect(answer.id, 'a1');
      expect(answer.content, 'Paris');
    });

    test('maps all fields from JSON', () {
      final json = {'id': 'b2', 'content': 'Tokyo'};

      final answer = Answer.fromJson(json);

      expect(answer.id, equals('b2'));
      expect(answer.content, equals('Tokyo'));
    });

    test('handles special characters in content', () {
      final json = {'id': 'c3', 'content': 'O\'Reilly & Sons <html>'};

      final answer = Answer.fromJson(json);

      expect(answer.content, "O'Reilly & Sons <html>");
    });

    test('handles empty string values', () {
      final json = {'id': '', 'content': ''};

      final answer = Answer.fromJson(json);

      expect(answer.id, '');
      expect(answer.content, '');
    });
  });

  // ---------------------------------------------------------------------------
  // Question.fromJson
  // ---------------------------------------------------------------------------
  group('Question.fromJson', () {
    test('parses JSON with all fields populated', () {
      final json = {
        'id': 1,
        'content': 'What is the capital of France?',
        'answers': [
          {'id': 'a', 'content': 'Paris'},
          {'id': 'b', 'content': 'London'},
        ],
        'correct_answer_id': 'a',
        'explanation': 'Paris is the capital of France.',
        'shared_context': 'Geography section',
        'image_base64': 'iVBORw0KGgo=',
      };

      final question = Question.fromJson(json);

      expect(question.id, '1'); // id is converted via toString()
      expect(question.content, 'What is the capital of France?');
      expect(question.answers, hasLength(2));
      expect(question.answers[0].id, 'a');
      expect(question.answers[0].content, 'Paris');
      expect(question.answers[1].id, 'b');
      expect(question.answers[1].content, 'London');
      expect(question.correctAnswerId, 'a');
      expect(question.explanation, 'Paris is the capital of France.');
      expect(question.sharedContext, 'Geography section');
      expect(question.imageBase64, 'iVBORw0KGgo=');
    });

    test('parses JSON with optional fields null', () {
      final json = {
        'id': 'q1',
        'content': 'Some question?',
        'answers': [
          {'id': 'x', 'content': 'Option X'},
        ],
        'correct_answer_id': null,
        'explanation': null,
        'shared_context': null,
        'image_base64': null,
      };

      final question = Question.fromJson(json);

      expect(question.correctAnswerId, isNull);
      expect(question.explanation, isNull);
      expect(question.sharedContext, isNull);
      expect(question.imageBase64, isNull);
    });

    test('parses JSON with optional fields absent', () {
      final json = {
        'id': 'q2',
        'content': 'Another question?',
        'answers': [],
      };

      final question = Question.fromJson(json);

      expect(question.correctAnswerId, isNull);
      expect(question.explanation, isNull);
      expect(question.sharedContext, isNull);
      expect(question.imageBase64, isNull);
      expect(question.answers, isEmpty);
    });

    test('converts numeric id to string', () {
      final json = {
        'id': 42,
        'content': 'Numeric ID question',
        'answers': [],
      };

      final question = Question.fromJson(json);

      expect(question.id, '42');
      expect(question.id, isA<String>());
    });

    test('parses multiple answers correctly', () {
      final json = {
        'id': 'q3',
        'content': 'Pick one',
        'answers': [
          {'id': 'a', 'content': 'Alpha'},
          {'id': 'b', 'content': 'Beta'},
          {'id': 'c', 'content': 'Gamma'},
          {'id': 'd', 'content': 'Delta'},
        ],
      };

      final question = Question.fromJson(json);

      expect(question.answers, hasLength(4));
      expect(question.answers.map((a) => a.id), ['a', 'b', 'c', 'd']);
    });
  });

  // ---------------------------------------------------------------------------
  // Quiz.fromJson
  // ---------------------------------------------------------------------------
  group('Quiz.fromJson', () {
    test('parses complete quiz JSON', () {
      final json = {
        'id': 'quiz-001',
        'title': 'History Quiz',
        'questions': [
          {
            'id': '1',
            'content': 'Who discovered America?',
            'answers': [
              {'id': 'a', 'content': 'Columbus'},
              {'id': 'b', 'content': 'Magellan'},
            ],
            'correct_answer_id': 'a',
            'explanation': 'Columbus in 1492.',
          },
          {
            'id': '2',
            'content': 'When did WW2 end?',
            'answers': [
              {'id': 'a', 'content': '1945'},
              {'id': 'b', 'content': '1944'},
            ],
          },
        ],
      };

      final quiz = Quiz.fromJson(json);

      expect(quiz.id, 'quiz-001');
      expect(quiz.title, 'History Quiz');
      expect(quiz.questions, hasLength(2));
      expect(quiz.questions[0].content, 'Who discovered America?');
      expect(quiz.questions[1].content, 'When did WW2 end?');
    });

    test('parses quiz with empty questions list', () {
      final json = {
        'id': 'quiz-empty',
        'title': 'Empty Quiz',
        'questions': [],
      };

      final quiz = Quiz.fromJson(json);

      expect(quiz.id, 'quiz-empty');
      expect(quiz.title, 'Empty Quiz');
      expect(quiz.questions, isEmpty);
    });

    test('parses quiz with null id', () {
      final json = {
        'id': null,
        'title': 'Draft Quiz',
        'questions': [],
      };

      final quiz = Quiz.fromJson(json);

      expect(quiz.id, isNull);
      expect(quiz.title, 'Draft Quiz');
    });

    test('nested questions have correct answer objects', () {
      final json = {
        'id': 'q-nested',
        'title': 'Nested Test',
        'questions': [
          {
            'id': '10',
            'content': 'Pick the right one',
            'answers': [
              {'id': 'opt1', 'content': 'First'},
              {'id': 'opt2', 'content': 'Second'},
            ],
            'correct_answer_id': 'opt1',
          },
        ],
      };

      final quiz = Quiz.fromJson(json);

      final question = quiz.questions.first;
      expect(question.answers.first, isA<Answer>());
      expect(question.answers.first.id, 'opt1');
      expect(question.correctAnswerId, 'opt1');
    });
  });

  // ---------------------------------------------------------------------------
  // QuizMode enum
  // ---------------------------------------------------------------------------
  group('QuizMode', () {
    test('has exactly 4 modes', () {
      expect(QuizMode.values, hasLength(4));
    });

    test('contains instantFeedback mode', () {
      expect(QuizMode.values, contains(QuizMode.instantFeedback));
    });

    test('contains exam mode', () {
      expect(QuizMode.values, contains(QuizMode.exam));
    });

    test('contains aiEvaluation mode', () {
      expect(QuizMode.values, contains(QuizMode.aiEvaluation));
    });

    test('contains practice mode', () {
      expect(QuizMode.values, contains(QuizMode.practice));
    });

    test('values are in expected order', () {
      expect(QuizMode.values[0], QuizMode.instantFeedback);
      expect(QuizMode.values[1], QuizMode.exam);
      expect(QuizMode.values[2], QuizMode.aiEvaluation);
      expect(QuizMode.values[3], QuizMode.practice);
    });
  });

  // ---------------------------------------------------------------------------
  // QuizState
  // ---------------------------------------------------------------------------
  group('QuizState', () {
    test('has correct default values', () {
      final state = QuizState();

      expect(state.quiz, isA<AsyncLoading<Quiz?>>());
      expect(state.mode, QuizMode.instantFeedback);
      expect(state.currentQuestionIndex, 0);
      expect(state.userAnswers, isEmpty);
      expect(state.isSubmitted, false);
      expect(state.gradeResult, isA<AsyncData<Map<String, dynamic>?>>());
      expect(state.gradeResult.value, isNull);
      expect(state.isStreaming, false);
      expect(state.progressMessage, isNull);
    });

    test('copyWith preserves unchanged fields', () {
      final original = QuizState(
        mode: QuizMode.exam,
        currentQuestionIndex: 3,
        userAnswers: {'q1': 'a1'},
        isSubmitted: true,
      );

      final copied = original.copyWith(isStreaming: true);

      // Changed field
      expect(copied.isStreaming, true);

      // Preserved fields
      expect(copied.mode, QuizMode.exam);
      expect(copied.currentQuestionIndex, 3);
      expect(copied.userAnswers, {'q1': 'a1'});
      expect(copied.isSubmitted, true);
    });

    test('copyWith updates specified fields', () {
      final original = QuizState();

      final updated = original.copyWith(
        mode: QuizMode.aiEvaluation,
        currentQuestionIndex: 5,
        isSubmitted: true,
        isStreaming: true,
        progressMessage: 'Processing...',
        userAnswers: {'q1': 'a', 'q2': 'b'},
      );

      expect(updated.mode, QuizMode.aiEvaluation);
      expect(updated.currentQuestionIndex, 5);
      expect(updated.isSubmitted, true);
      expect(updated.isStreaming, true);
      expect(updated.progressMessage, 'Processing...');
      expect(updated.userAnswers, hasLength(2));
    });

    test('copyWith can update quiz value', () {
      final original = QuizState();
      final quiz = Quiz(id: 'test', title: 'Test Quiz', questions: []);

      final updated = original.copyWith(quiz: AsyncData(quiz));

      expect(updated.quiz, isA<AsyncData<Quiz?>>());
      expect(updated.quiz.value?.id, 'test');
      expect(updated.quiz.value?.title, 'Test Quiz');
    });

    test('copyWith can update gradeResult', () {
      final original = QuizState();
      final gradeData = {'score': 8, 'total': 10};

      final updated = original.copyWith(gradeResult: AsyncData(gradeData));

      expect(updated.gradeResult, isA<AsyncData<Map<String, dynamic>?>>());
      expect(updated.gradeResult.value?['score'], 8);
      expect(updated.gradeResult.value?['total'], 10);
    });

    test('default userAnswers map is unmodifiable (const)', () {
      final state = QuizState();

      // The default is `const {}`, so operations that mutate should not affect
      // the original. copyWith creates a new state with a new map reference.
      final updated = state.copyWith(
        userAnswers: Map<String, String>.from(state.userAnswers)..['q1'] = 'a1',
      );

      expect(state.userAnswers, isEmpty);
      expect(updated.userAnswers, {'q1': 'a1'});
    });
  });

  // ---------------------------------------------------------------------------
  // AppConfig
  // ---------------------------------------------------------------------------
  group('AppConfig', () {
    test('has a non-empty default API base URL', () {
      expect(AppConfig.apiBaseUrl, isNotEmpty);
      expect(AppConfig.apiBaseUrl, contains('http'));
    });

    test('default API base URL points to localhost for dev', () {
      expect(AppConfig.apiBaseUrl, 'http://localhost:8000');
    });

    test('apiKey has a default value (may be empty in dev)', () {
      // In test environment without --dart-define, apiKey defaults to ''
      expect(AppConfig.apiKey, isA<String>());
    });

    test('connectTimeout is a positive duration', () {
      expect(AppConfig.connectTimeout.inSeconds, greaterThan(0));
    });

    test('connectTimeout is reasonable (not too short, not too long)', () {
      expect(AppConfig.connectTimeout.inSeconds, greaterThanOrEqualTo(5));
      expect(AppConfig.connectTimeout.inSeconds, lessThanOrEqualTo(120));
    });

    test('receiveTimeout is a positive duration', () {
      expect(AppConfig.receiveTimeout.inSeconds, greaterThan(0));
    });

    test('receiveTimeout is longer than connectTimeout', () {
      expect(
        AppConfig.receiveTimeout.inSeconds,
        greaterThan(AppConfig.connectTimeout.inSeconds),
      );
    });

    test('receiveTimeout accommodates SSE streaming (>= 1 minute)', () {
      expect(AppConfig.receiveTimeout.inMinutes, greaterThanOrEqualTo(1));
    });
  });
}
