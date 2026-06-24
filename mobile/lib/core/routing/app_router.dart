import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/upload/presentation/upload_screen.dart';
import '../../features/quiz/presentation/quiz_screen.dart';
import '../../features/quiz/presentation/result_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const UploadScreen(),
      ),
      GoRoute(
        path: '/quiz/:quizId',
        builder: (context, state) {
          final quizId = state.pathParameters['quizId']!;
          return QuizScreen(quizId: quizId);
        },
        routes: [
          GoRoute(
            path: 'result',
            builder: (context, state) {
              final quizId = state.pathParameters['quizId']!;
              return ResultScreen(quizId: quizId);
            },
          ),
        ],
      ),
    ],
  );
});
