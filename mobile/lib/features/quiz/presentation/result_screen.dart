import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../domain/quiz_models.dart';
import 'quiz_state.dart';

class ResultScreen extends ConsumerWidget {
  final String quizId;

  const ResultScreen({super.key, required this.quizId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final quizState = ref.watch(quizStateProvider(quizId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Kết Quả'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (quizState.mode == QuizMode.practice || quizState.mode == QuizMode.instantFeedback) ...[
                const Icon(Icons.check_circle, size: 80, color: Colors.blue),
                const SizedBox(height: 24),
                const Text('Bạn đã hoàn thành bài thi!', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              ] else ...[
                quizState.gradeResult.when(
                  data: (data) {
                    if (data == null) return const CircularProgressIndicator();
                    return Column(
                      children: [
                        Text('Điểm số: ${data["score"]} / ${data["total"]}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.blue)),
                        const SizedBox(height: 24),
                        if (quizState.mode == QuizMode.aiEvaluation) ...[
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(16)),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Row(
                                  children: [
                                    Icon(Icons.psychology, color: Colors.blue),
                                    SizedBox(width: 8),
                                    Text('Gia sư AI Nhận Xét', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.blue)),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Text(data["ai_feedback"] ?? '', style: const TextStyle(fontSize: 16)),
                              ],
                            ),
                          ),
                        ]
                      ],
                    );
                  },
                  loading: () => const Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('AI đang cẩn thận chấm bài và viết nhận xét...'),
                    ],
                  ),
                  error: (e, s) => Text('Lỗi chấm bài: $e'),
                ),
              ],
              const SizedBox(height: 40),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
                onPressed: () {
                  GoRouter.of(context).go('/');
                },
                icon: const Icon(Icons.home),
                label: const Text('Về trang chủ'),
              )
            ],
          ),
        ),
      ),
    );
  }
}
