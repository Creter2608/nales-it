import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/quiz_models.dart';
import '../quiz_state.dart';
import '../../../../l10n/app_localizations.dart';

/// Shows a bottom sheet for selecting quiz mode.
void showModeSelectionSheet({
  required BuildContext context,
  required WidgetRef ref,
  required String quizId,
  required VoidCallback onModeSelected,
}) {
  showModalBottomSheet(
    context: context,
    isDismissible: false,
    enableDrag: false,
    builder: (ctx) {
      return Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(AppLocalizations.of(ctx)!.modeSelectionTitle, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.flash_on, color: Colors.blue),
              title: Text(AppLocalizations.of(ctx)!.modeInstant),
              subtitle: Text(AppLocalizations.of(ctx)!.modeInstantDesc),
              onTap: () {
                ref.read(quizStateProvider(quizId).notifier).setMode(QuizMode.instantFeedback);
                onModeSelected();
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.timer, color: Colors.blue),
              title: Text(AppLocalizations.of(ctx)!.modeExam),
              subtitle: Text(AppLocalizations.of(ctx)!.modeExamDesc),
              onTap: () {
                ref.read(quizStateProvider(quizId).notifier).setMode(QuizMode.exam);
                onModeSelected();
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.smart_toy, color: Colors.blue),
              title: Text(AppLocalizations.of(ctx)!.modeAi),
              subtitle: Text(AppLocalizations.of(ctx)!.modeAiDesc),
              onTap: () {
                ref.read(quizStateProvider(quizId).notifier).setMode(QuizMode.aiEvaluation);
                onModeSelected();
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.menu_book, color: Colors.blue),
              title: Text(AppLocalizations.of(ctx)!.modePractice),
              subtitle: Text(AppLocalizations.of(ctx)!.modePracticeDesc),
              onTap: () {
                ref.read(quizStateProvider(quizId).notifier).setMode(QuizMode.practice);
                onModeSelected();
                Navigator.pop(context);
              },
            ),
          ],
        ),
      );
    },
  );
}
