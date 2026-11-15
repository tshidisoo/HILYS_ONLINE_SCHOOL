import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'screens/login.dart';
import 'screens/shell.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const HilysApp());
}

class HilysApp extends StatefulWidget {
  const HilysApp({super.key});
  @override
  State<HilysApp> createState() => _HilysAppState();
}

class _HilysAppState extends State<HilysApp> {
  bool? _signedIn;

  @override
  void initState() {
    super.initState();
    Api.instance.onSignedOut = () => setState(() => _signedIn = false);
    Api.instance.restore().then((ok) => setState(() => _signedIn = ok));
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HILYS',
      debugShowCheckedModeBanner: false,
      theme: Brand.theme(),
      home: switch (_signedIn) {
        null => const Scaffold(body: Center(child: CircularProgressIndicator())),
        false => LoginScreen(onSignedIn: () => setState(() => _signedIn = true)),
        true => Shell(onSignOut: () async {
            await Api.instance.signOut();
            setState(() => _signedIn = false);
          }),
      },
    );
  }
}
