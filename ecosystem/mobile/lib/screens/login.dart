import 'package:material_ui/material_ui.dart';

import '../api.dart';
import '../theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.onSignedIn});
  final VoidCallback onSignedIn;
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _user = TextEditingController();
  final _pass = TextEditingController();
  String? _error;
  bool _busy = false;

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Api.instance.signIn(_user.text.trim(), _pass.text);
      widget.onSignedIn();
    } on ApiError catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: AutofillGroup(
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Center(child: ClipOval(child: Image.asset('assets/logo.jpg', width: 104, height: 104, semanticLabel: 'HILYS logo'))),
                  const SizedBox(height: 18),
                  Text('Salibonani!', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Brand.navy)),
                  const SizedBox(height: 4),
                  Text("Your child's isiNdebele lessons, notes and progress.", textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
                  const SizedBox(height: 28),
                  TextField(controller: _user, autofillHints: const [AutofillHints.username], textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(labelText: 'Username or email')),
                  const SizedBox(height: 14),
                  TextField(controller: _pass, obscureText: true, autofillHints: const [AutofillHints.password], onSubmitted: (_) => _submit(),
                      decoration: const InputDecoration(labelText: 'Password')),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: Brand.bad, fontWeight: FontWeight.w700))),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Signing in…' : 'Sign in')),
                  const SizedBox(height: 14),
                  Text('HILYS sends your login on WhatsApp when your child starts.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
