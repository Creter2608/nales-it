import 'package:flutter/material.dart';
import '../quiz_state.dart';

/// Shows a dialog asking if the user wants AI to re-solve a question.
void showResolveDialog({
  required BuildContext context,
  required QuizNotifier notifier,
  required String questionId,
}) {
  showDialog(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('Yêu cầu giải lại?'),
      content: const Text('Bạn thấy cấn cấn? Yêu cầu Gia sư AI kiểm tra và giải lại câu này?'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('Hủy'),
        ),
        TextButton(
          onPressed: () async {
            Navigator.pop(ctx);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Đang yêu cầu AI giải lại...')),
            );
            try {
              await notifier.resolveQuestion(questionId);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Đã cập nhật lời giải mới!')),
                );
              }
            } catch (e) {
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Lỗi: Không thể giải lại lúc này.')),
                );
              }
            }
          },
          child: const Text('Giải lại'),
        ),
      ],
    ),
  );
}
