import 'package:flutter_test/flutter_test.dart';
import 'package:hilys_parent/screens/login.dart';
import 'package:material_ui/material_ui.dart';

void main() {
  testWidgets('Sign-in screen greets the parent and has both fields', (tester) async {
    await tester.pumpWidget(MaterialApp(home: LoginScreen(onSignedIn: () {})));
    expect(find.text('Salibonani!'), findsOneWidget);
    expect(find.text('Username or email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
  });
}
