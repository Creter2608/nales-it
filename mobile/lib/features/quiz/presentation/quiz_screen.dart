import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:markdown/markdown.dart' as markdown;
import '../domain/quiz_models.dart';
import 'quiz_state.dart';
import 'result_screen.dart';

class MathMarkdownBuilder extends MarkdownElementBuilder {
  @override
  Widget visitElementAfter(element, TextStyle? preferredStyle) {
    if (element.textContent.isEmpty) return const SizedBox();
    return Math.tex(
      element.textContent,
      textStyle: preferredStyle?.copyWith(fontSize: 18),
      mathStyle: MathStyle.display,
    );
  }
}


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

  void _showGridNavigation(BuildContext context, Quiz quiz, QuizState state, WidgetRef ref) {
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
                  itemCount: quiz.questions.length + (state.isStreaming ? 3 : 0),
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
                    final isAnswered = state.userAnswers.containsKey(q.id);
                    return InkWell(
                      onTap: () {
                        Navigator.pop(context);
                        ref.read(quizStateProvider(widget.quizId).notifier).jumpToQuestion(index);
                        _pageController.jumpToPage(index);
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
      }
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
        if (quiz.questions.isEmpty) {
          if (quizState.isStreaming) {
            return Scaffold(
              appBar: AppBar(title: Text(quiz.title), backgroundColor: Colors.blue, foregroundColor: Colors.white),
              body: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(color: Colors.blue),
                    SizedBox(height: 16),
                    Text('Đang phân tích PDF và tải câu hỏi...', style: TextStyle(color: Colors.grey, fontSize: 16)),
                  ],
                ),
              ),
            );
          }
          return Scaffold(
            appBar: AppBar(title: const Text('Lỗi tải đề'), backgroundColor: Colors.blue, foregroundColor: Colors.white),
            body: const Center(child: Padding(padding: EdgeInsets.all(16), child: Text('Tài liệu rỗng hoặc AI không tìm thấy câu hỏi trắc nghiệm nào. Vui lòng tải file khác.', textAlign: TextAlign.center, style: TextStyle(fontSize: 16)))),
          );
        }
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
              IconButton(
                icon: const Icon(Icons.grid_view),
                tooltip: 'Bảng câu hỏi',
                onPressed: () => _showGridNavigation(context, quiz, quizState, ref),
              ),
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
                        if (q.sharedContext != null && q.sharedContext!.isNotEmpty) ...[
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.yellow.shade100,
                              border: Border.all(color: Colors.orange),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Row(
                                  children: [
                                    Icon(Icons.info_outline, color: Colors.orange),
                                    SizedBox(width: 8),
                                    Text('Thông tin chung:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange)),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                MarkdownBody(
                                  data: q.sharedContext!,
                                  builders: {'math': MathMarkdownBuilder()},
                                  extensionSet: markdown.ExtensionSet.gitHubFlavored,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],
                        if (q.imageBase64 != null && q.imageBase64!.isNotEmpty) ...[
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Image.memory(base64Decode(q.imageBase64!)),
                          ),
                          const SizedBox(height: 16),
                        ],
                        MarkdownBody(
                          data: q.content,
                          builders: {'math': MathMarkdownBuilder()},
                          extensionSet: markdown.ExtensionSet.gitHubFlavored,
                          styleSheet: MarkdownStyleSheet(p: const TextStyle(fontSize: 20)),
                        ),
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
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${ans.id}. ', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: btnColor != null && btnColor != Colors.blue.shade200 ? Colors.white : Colors.black87)),
                                  Expanded(
                                    child: MarkdownBody(
                                      data: ans.content,
                                      builders: {'math': MathMarkdownBuilder()},
                                      extensionSet: markdown.ExtensionSet.gitHubFlavored,
                                      styleSheet: MarkdownStyleSheet(p: TextStyle(fontSize: 16, color: btnColor != null && btnColor != Colors.blue.shade200 ? Colors.white : Colors.black87)),
                                    ),
                                  ),
                                ],
                              ),
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
                                MarkdownBody(
                                  data: q.explanation!,
                                  builders: {'math': MathMarkdownBuilder()},
                                  extensionSet: markdown.ExtensionSet.gitHubFlavored,
                                ),
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
