import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/quiz_models.dart';
import 'quiz_state.dart';
import 'result_screen.dart';

class QuizScreen extends ConsumerStatefulWidget {
  final String quizId;

  const QuizScreen({super.key, required this.quizId});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  final PageController _pageController = PageController();
  bool _modeSelected = false;

  void _showModeSelection(BuildContext context, WidgetRef ref) {
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
              const Text('Chọn Chế Độ Làm Bài', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.flash_on, color: Colors.blue),
                title: const Text('Ôn luyện'),
                subtitle: const Text('Báo màu xanh đỏ ngay khi chọn.'),
                onTap: () {
                  ref.read(quizStateProvider(widget.quizId).notifier).setMode(QuizMode.instantFeedback);
                  setState(() => _modeSelected = true);
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.timer, color: Colors.blue),
                title: const Text('Thi thử'),
                subtitle: const Text('Chấm điểm ở cuối giờ.'),
                onTap: () {
                  ref.read(quizStateProvider(widget.quizId).notifier).setMode(QuizMode.exam);
                  setState(() => _modeSelected = true);
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.smart_toy, color: Colors.blue),
                title: const Text('Đánh giá AI'),
                subtitle: const Text('AI nhận xét tổng quan kỹ năng của bạn.'),
                onTap: () {
                  ref.read(quizStateProvider(widget.quizId).notifier).setMode(QuizMode.aiEvaluation);
                  setState(() => _modeSelected = true);
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Icon(Icons.menu_book, color: Colors.blue),
                title: const Text('Tự do'),
                subtitle: const Text('Không chấm điểm, chỉ đọc câu hỏi.'),
                onTap: () {
                  ref.read(quizStateProvider(widget.quizId).notifier).setMode(QuizMode.practice);
                  setState(() => _modeSelected = true);
                  Navigator.pop(context);
                },
              ),
            ],
          ),
        );
      }
    );
  }

  void _showResolveDialog(BuildContext context, QuizNotifier notifier, String questionId) {
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
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Đã cập nhật lời giải mới!')),
                  );
                }
              } catch (e) {
                if (mounted) {
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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _showModeSelection(context, ref);
    });
  }

  @override
  Widget build(BuildContext context) {
    final quizState = ref.watch(quizStateProvider(widget.quizId));

    if (!_modeSelected) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return quizState.quiz.when(
      data: (quiz) {
        if (quiz == null) return const Scaffold(body: Center(child: Text('Không tìm thấy bài thi.')));
        
        if (quizState.isSubmitted) {
          return ResultScreen(quizId: widget.quizId);
        }

        final currentQ = quiz.questions[quizState.currentQuestionIndex];
        final userAnswerId = quizState.userAnswers[currentQ.id];
        
        final isInstantMode = quizState.mode == QuizMode.instantFeedback;
        final showExplanation = isInstantMode && userAnswerId != null;

        return Scaffold(
          appBar: AppBar(
            title: Text(quiz.title, style: const TextStyle(fontSize: 16)),
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
            actions: [
              TextButton(
                onPressed: () {
                  ref.read(quizStateProvider(widget.quizId).notifier).submitQuiz();
                },
                child: const Text('Nộp bài', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              )
            ],
          ),
          body: Column(
            children: [
              LinearProgressIndicator(
                value: (quizState.currentQuestionIndex + 1) / quiz.questions.length,
                backgroundColor: Colors.blue.shade100,
                color: Colors.blue,
              ),
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Câu ${quizState.currentQuestionIndex + 1}/${quiz.questions.length}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    IconButton(
                      icon: const Icon(Icons.flag, color: Colors.red),
                      tooltip: 'Báo cáo / Giải lại',
                      onPressed: () {
                        final notifier = ref.read(quizStateProvider(widget.quizId).notifier);
                        _showResolveDialog(context, notifier, quiz.questions[quizState.currentQuestionIndex].id);
                      },
                    ),
                  ],
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: quiz.questions.length,
                  itemBuilder: (context, index) {
                    final q = quiz.questions[index];
                    return ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text(q.content, style: const TextStyle(fontSize: 20)),
                        const SizedBox(height: 24),
                        ...q.answers.map((ans) {
                          Color? btnColor;
                          if (isInstantMode && userAnswerId != null) {
                            if (ans.id == q.correctAnswerId) {
                              btnColor = Colors.green;
                            } else if (ans.id == userAnswerId) {
                              btnColor = Colors.red;
                            }
                          } else {
                            if (userAnswerId == ans.id) {
                              btnColor = Colors.blue.shade200;
                            }
                          }

                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: btnColor,
                                alignment: Alignment.centerLeft,
                                padding: const EdgeInsets.all(16),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              ),
                              onPressed: () {
                                ref.read(quizStateProvider(widget.quizId).notifier).selectAnswer(q.id, ans.id);
                              },
                              child: Text('${ans.id}. ${ans.content}', style: TextStyle(fontSize: 16, color: btnColor != null && btnColor != Colors.blue.shade200 ? Colors.white : Colors.black87)),
                            ),
                          );
                        }),
                        if (showExplanation && q.explanation != null) ...[
                          const SizedBox(height: 24),
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(color: Colors.amber.shade50, borderRadius: BorderRadius.circular(12)),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('💡 Giải thích từ AI:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange)),
                                const SizedBox(height: 8),
                                Text(q.explanation!),
                                const SizedBox(height: 12),
                                const Text('🤖 Lời giải này được sinh ra bởi AI nên có thể không chính xác 100%. Vui lòng tham khảo thêm tài liệu chính thống.', style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic)),
                              ],
                            ),
                          )
                        ]
                      ],
                    );
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    ElevatedButton(
                      onPressed: quizState.currentQuestionIndex > 0 ? () {
                        ref.read(quizStateProvider(widget.quizId).notifier).previousQuestion();
                        _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
                      } : null,
                      child: const Text('Câu trước'),
                    ),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, foregroundColor: Colors.white),
                      onPressed: quizState.currentQuestionIndex < quiz.questions.length - 1 ? () {
                        ref.read(quizStateProvider(widget.quizId).notifier).nextQuestion();
                        _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
                      } : () {
                        ref.read(quizStateProvider(widget.quizId).notifier).submitQuiz();
                      },
                      child: Text(quizState.currentQuestionIndex < quiz.questions.length - 1 ? 'Câu tiếp' : 'Nộp bài'),
                    ),
                  ],
                ),
              )
            ],
          ),
        );
      },
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, s) => Scaffold(body: Center(child: Text('Lỗi tải bài thi: $e'))),
    );
  }
}
