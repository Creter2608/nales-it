enum QuizMode {
  instantFeedback, // 1. Ôn luyện (Báo đúng/sai ngay)
  exam,            // 2. Thi thử (Giấu đáp án, chấm điểm cuối giờ)
  aiEvaluation,    // 3. Đánh giá AI (Nộp bài cho AI nhận xét)
  practice         // 4. Tự do (Không chấm điểm)
}

class Answer {
  final String id;
  final String content;

  Answer({required this.id, required this.content});

  factory Answer.fromJson(Map<String, dynamic> json) {
    return Answer(
      id: json['id'],
      content: json['content'],
    );
  }
}

class Question {
  final String id;
  final String content;
  final List<Answer> answers;
  final String? correctAnswerId;
  final String? explanation;

  Question({
    required this.id,
    required this.content,
    required this.answers,
    this.correctAnswerId,
    this.explanation,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json['id'].toString(),
      content: json['content'],
      answers: (json['answers'] as List).map((e) => Answer.fromJson(e)).toList(),
      correctAnswerId: json['correct_answer_id'],
      explanation: json['explanation'],
    );
  }
}

class Quiz {
  final String? id;
  final String title;
  final List<Question> questions;

  Quiz({this.id, required this.title, required this.questions});

  factory Quiz.fromJson(Map<String, dynamic> json) {
    return Quiz(
      id: json['id'],
      title: json['title'],
      questions: (json['questions'] as List).map((e) => Question.fromJson(e)).toList(),
    );
  }
}
