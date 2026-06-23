import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame. Wrap with ProviderScope for Riverpod.
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    
    // Allow the router to process and render the initial screen
    await tester.pumpAndSettle();

    // Verify that the app title "Nales-It" appears on the screen (e.g. AppBar or body).
    expect(find.textContaining('Nales-It', skipOffstage: false), findsWidgets);
  });
}
