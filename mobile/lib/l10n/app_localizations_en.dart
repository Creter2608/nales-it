// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Nales-It AI Tutor';

  @override
  String get modeSelectionTitle => 'Select Quiz Mode';

  @override
  String get modeInstant => 'Practice';

  @override
  String get modeInstantDesc => 'Immediate color feedback.';

  @override
  String get modeExam => 'Exam';

  @override
  String get modeExamDesc => 'Graded at the end.';

  @override
  String get modeAi => 'AI Evaluation';

  @override
  String get modeAiDesc => 'AI reviews your overall skills.';

  @override
  String get modePractice => 'Free Mode';

  @override
  String get modePracticeDesc => 'No grading, just reading.';

  @override
  String get questionGridTitle => 'Question Grid';

  @override
  String get resolveDialogTitle => 'Request Re-solve?';

  @override
  String get resolveDialogDesc =>
      'Something feels off? Ask the AI Tutor to re-check and solve this again.';

  @override
  String get cancel => 'Cancel';

  @override
  String get resolve => 'Re-solve';

  @override
  String get resolvingMsg => 'Requesting AI to re-solve...';

  @override
  String get resolvedMsg => 'Solution updated!';

  @override
  String get resolveErrorMsg => 'Error: Cannot re-solve right now.';
}
