import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/quiz_models.dart';
import '../quiz_state.dart';

/// Shows a grid bottom sheet for quick question navigation.
void showQuestionGridSheet({
  required BuildContext context,
  required Quiz quiz,
  required QuizState quizState,
  required WidgetRef ref,
  required String quizId,
  required PageController pageController,
}) {
  showModalBottomSheet(
    context: context,
    builder: (ctx) {
      return Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text('Bảng câu hỏi', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Expanded(
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 5,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 8,
                ),
                itemCount: quiz.questions.length + (quizState.isStreaming ? 3 : 0),
                itemBuilder: (context, index) {
                  if (index >= quiz.questions.length) {
                    return Container(
                      decoration: BoxDecoration(
                        color: Colors.grey.shade200,
                        border: Border.all(color: Colors.grey.shade400),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    );
                  }
                  
                  final q = quiz.questions[index];
                  final isAnswered = quizState.userAnswers.containsKey(q.id);
                  return InkWell(
                    onTap: () {
                      Navigator.pop(context);
                      ref.read(quizStateProvider(quizId).notifier).jumpToQuestion(index);
                      pageController.jumpToPage(index);
                    },
                    child: Container(
                      decoration: BoxDecoration(
                        color: isAnswered ? Colors.blue.shade100 : Colors.white,
                        border: Border.all(color: Colors.blue),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: Text('${index + 1}', style: TextStyle(fontWeight: FontWeight.bold, color: isAnswered ? Colors.blue.shade900 : Colors.black87)),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      );
    },
  );
}
