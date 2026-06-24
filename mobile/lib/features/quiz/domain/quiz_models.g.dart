// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'quiz_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_Answer _$AnswerFromJson(Map<String, dynamic> json) =>
    _Answer(id: _idToString(json['id']), content: json['content'] as String);

Map<String, dynamic> _$AnswerToJson(_Answer instance) => <String, dynamic>{
  'id': instance.id,
  'content': instance.content,
};

_Question _$QuestionFromJson(Map<String, dynamic> json) => _Question(
  id: _idToString(json['id']),
  content: json['content'] as String,
  answers: (json['answers'] as List<dynamic>)
      .map((e) => Answer.fromJson(e as Map<String, dynamic>))
      .toList(),
  correctAnswerId: json['correct_answer_id'] as String?,
  explanation: json['explanation'] as String?,
  sharedContext: json['shared_context'] as String?,
  imageBase64: json['image_base64'] as String?,
);

Map<String, dynamic> _$QuestionToJson(_Question instance) => <String, dynamic>{
  'id': instance.id,
  'content': instance.content,
  'answers': instance.answers,
  'correct_answer_id': instance.correctAnswerId,
  'explanation': instance.explanation,
  'shared_context': instance.sharedContext,
  'image_base64': instance.imageBase64,
};

_Quiz _$QuizFromJson(Map<String, dynamic> json) => _Quiz(
  id: _nullableIdToString(json['id']),
  title: json['title'] as String,
  questions: (json['questions'] as List<dynamic>)
      .map((e) => Question.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$QuizToJson(_Quiz instance) => <String, dynamic>{
  'id': instance.id,
  'title': instance.title,
  'questions': instance.questions,
};
