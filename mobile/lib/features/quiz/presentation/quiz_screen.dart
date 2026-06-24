import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as markdown;
import 'package:flutter_animate/flutter_animate.dart';
import 'package:skeletonizer/skeletonizer.dart';
import '../domain/quiz_models.dart';
import 'quiz_state.dart';
import 'result_screen.dart';
import 'widgets/math_markdown_builder.dart';
import 'widgets/mode_selection_sheet.dart';
import 'widgets/question_grid_sheet.dart';
import 'widgets/resolve_dialog.dart';

class QuizScreen extends ConsumerStatefulWidget {
  final String quizId;

  const QuizScreen({super.key, required this.quizId});

  @override
  ConsumerState<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends ConsumerState<QuizScreen> {
  final PageController _pageController = PageController();
  bool _modeSelected = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      showModeSelectionSheet(
        context: context,
        ref: ref,
        quizId: widget.quizId,
        onModeSelected: () => setState(() => _modeSelected = true),
      );
    });
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
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
              appBar: AppBar(title: Text(quiz.title)),
              body: Column(
                children: [
                  LinearProgressIndicator(color: Colors.blue, backgroundColor: Colors.blue.shade100),
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(quizState.progressMessage ?? 'Đang tải...', style: const TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  Expanded(
                    child: Skeletonizer(
                      enabled: true,
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          const Text('Đang phân tích tài liệu để tạo câu hỏi trắc nghiệm...', style: TextStyle(fontSize: 20)),
                          const SizedBox(height: 24),
                          for (int i = 0; i < 4; i++)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: ElevatedButton(
                                onPressed: null,
                                child: Container(
                                  width: double.infinity,
                                  alignment: Alignment.centerLeft,
                                  child: const Text('Loading answer placeholder...'),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
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

        final isInstantMode = quizState.mode == QuizMode.instantFeedback;

        return Scaffold(
          appBar: AppBar(
            title: Text(quiz.title, style: const TextStyle(fontSize: 16)),
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
            actions: [
              IconButton(
                icon: const Icon(Icons.grid_view),
                tooltip: 'Bảng câu hỏi',
                onPressed: () => showQuestionGridSheet(
                  context: context,
                  quiz: quiz,
                  quizState: quizState,
                  ref: ref,
                  quizId: widget.quizId,
                  pageController: _pageController,
                ),
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
                        showResolveDialog(
                          context: context,
                          notifier: notifier,
                          questionId: quiz.questions[quizState.currentQuestionIndex].id,
                        );
                      },
                    ),
                  ],
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  physics: const BouncingScrollPhysics(),
                  onPageChanged: (index) {
                    ref.read(quizStateProvider(widget.quizId).notifier).jumpToQuestion(index);
                  },
                  itemCount: quiz.questions.length,
                  itemBuilder: (context, index) {
                    final q = quiz.questions[index];
                    final qUserAnswerId = quizState.userAnswers[q.id];
                    final isViewingAnswer = quizState.viewingAnswers.contains(q.id);
                    
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
                          if (isInstantMode && qUserAnswerId != null && isViewingAnswer) {
                            if (ans.id == q.correctAnswerId) {
                              btnColor = Colors.green;
                            } else if (ans.id == qUserAnswerId) {
                              btnColor = Colors.red;
                            }
                          } else {
                            if (qUserAnswerId == ans.id) {
                              btnColor = Colors.blue.shade200;
                            }
                          }

                          Widget btn = Padding(
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

                          if (isInstantMode && qUserAnswerId == ans.id && isViewingAnswer && ans.id != q.correctAnswerId) {
                            btn = btn.animate().shakeX(duration: 300.ms, amount: 3);
                          } else if (qUserAnswerId == ans.id) {
                            btn = btn.animate().scaleXY(end: 1.02, duration: 100.ms).then().scaleXY(end: 1.0, duration: 100.ms);
                          }
                          
                          return btn;
                        }),
                        if (isInstantMode && qUserAnswerId != null) ...[
                          const SizedBox(height: 16),
                          if (!isViewingAnswer)
                            Center(
                              child: ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                                onPressed: () {
                                  ref.read(quizStateProvider(widget.quizId).notifier).demandAnswer(q.id);
                                },
                                icon: const Icon(Icons.visibility),
                                label: const Text('Xem đáp án chi tiết'),
                              ),
                            )
                          else if (quizState.loadingAnswers.contains(q.id))
                            const Center(
                              child: Padding(
                                padding: EdgeInsets.all(16.0),
                                child: Column(
                                  children: [
                                    CircularProgressIndicator(),
                                    SizedBox(height: 8),
                                    Text('AI đang giải đáp án...', style: TextStyle(color: Colors.grey)),
                                  ],
                                ),
                              ),
                            )
                          else if (q.explanation != null)
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
