import 'package:material_ui/material_ui.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets.dart';

class Shell extends StatefulWidget {
  const Shell({super.key, required this.onSignOut});
  final VoidCallback onSignOut;
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int _tab = 0;
  static const _titles = ['Home', 'Lessons', 'Notes', 'Money', 'Messages'];

  @override
  Widget build(BuildContext context) {
    final pages = [HomeTab(onOpenTab: (i) => setState(() => _tab = i)), const LessonsTab(), const NotesTab(), const MoneyTab(), const MessagesTab()];
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          ClipOval(child: Image.asset('assets/logo.jpg', width: 30, height: 30, excludeFromSemantics: true)),
          const SizedBox(width: 10),
          Text(_titles[_tab], style: const TextStyle(fontWeight: FontWeight.w800)),
        ]),
        bottom: const Beads(),
        actions: [TextButton(onPressed: widget.onSignOut, child: const Text('Sign out'))],
      ),
      body: SafeArea(child: pages[_tab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.event_outlined), selectedIcon: Icon(Icons.event), label: 'Lessons'),
          NavigationDestination(icon: Icon(Icons.sticky_note_2_outlined), selectedIcon: Icon(Icons.sticky_note_2), label: 'Notes'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), selectedIcon: Icon(Icons.receipt_long), label: 'Money'),
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Messages'),
        ],
      ),
    );
  }
}

Future<void> openLink(BuildContext context, String url) async {
  final ok = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  if (!ok && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('We could not open that. Try again.')));
  }
}

Future<void> openPdf(BuildContext context, String kind, int id) async {
  try {
    final r = await Api.instance.get('/api/parent/pdf-link/$kind/$id/');
    if (context.mounted) await openLink(context, r['url'] as String);
  } on ApiError catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
  }
}

class HomeTab extends StatelessWidget {
  const HomeTab({super.key, required this.onOpenTab});
  final void Function(int) onOpenTab;

  @override
  Widget build(BuildContext context) {
    return Loader<Map<String, dynamic>>(
      load: () async => (await Api.instance.get('/api/parent/overview/')) as Map<String, dynamic>,
      builder: (context, d, reload) {
        final next = d['next_lesson'] as Map<String, dynamic>?;
        final owed = (d['owed'] as Map<String, dynamic>);
        final children = (d['children'] as List).cast<Map<String, dynamic>>();
        final unread = d['unread_messages'] as int;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text('Hello, ${(d['parent'] as String).split(' ').first}', style: Theme.of(context).textTheme.headlineSmall),
          Text('Times are shown in your time zone (${d['time_zone']}).', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 14),
          Card(
            color: Brand.navy,
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: next == null
                  ? const Text('No lesson booked yet. HILYS will message you with times.', style: TextStyle(color: Colors.white, fontSize: 16))
                  : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('NEXT LESSON', style: TextStyle(color: Color(0xFFF7BD45), fontWeight: FontWeight.w800, letterSpacing: 1.2, fontSize: 12)),
                      const SizedBox(height: 6),
                      Text('${next['child']} · ${next['when']}', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
                      Text('with ${next['teacher']}', style: const TextStyle(color: Colors.white70)),
                      if ((next['zoom'] as String).isNotEmpty) ...[
                        const SizedBox(height: 12),
                        FilledButton.icon(onPressed: () => openLink(context, next['zoom'] as String), icon: const Icon(Icons.videocam), label: const Text('Join on Zoom')),
                      ],
                    ]),
            ),
          ),
          if (owed.isNotEmpty)
            Card(
              child: ListTile(
                leading: const Icon(Icons.payments_outlined, color: Brand.orangeInk),
                title: Text('To pay: ${owed.entries.map((e) => '${e.key} ${e.value}').join(' + ')}'),
                subtitle: const Text('See invoices and how to pay'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => onOpenTab(3),
              ),
            ),
          if (unread > 0)
            Card(
              child: ListTile(
                leading: const Icon(Icons.mark_chat_unread_outlined, color: Brand.navy),
                title: Text('$unread new ${unread == 1 ? 'message' : 'messages'} from HILYS'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => onOpenTab(4),
              ),
            ),
          const SectionTitle('Your children'),
          for (final c in children) ChildCard(child: c),
        ]);
      },
    );
  }
}

class ChildCard extends StatelessWidget {
  const ChildCard({super.key, required this.child});
  final Map<String, dynamic> child;
  @override
  Widget build(BuildContext context) {
    final p = child['progress'] as Map<String, dynamic>?;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: p == null ? null : () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProgressScreen(childId: child['id'] as int, name: child['name'] as String))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(child['name'] as String, style: Theme.of(context).textTheme.titleMedium)),
              StatusPill(child['stage'] as String, tone: toneFor(child['stage'] as String)),
            ]),
            const SizedBox(height: 4),
            Text([child['level'], child['package'], if ((child['teacher'] as String).isNotEmpty) 'with ${child['teacher']}'].where((x) => (x as String).isNotEmpty).join(' · '),
                style: Theme.of(context).textTheme.bodySmall),
            if (p != null) ...[
              const SizedBox(height: 12),
              Text('${p['book']}: ${p['done']} of ${p['total']} lessons', style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(99),
                child: LinearProgressIndicator(value: (p['done'] as int) / (p['total'] as int), minHeight: 10, color: Brand.tealInk, backgroundColor: const Color(0xFFEEF0F7),
                    semanticsLabel: 'Book progress', semanticsValue: '${p['done']} of ${p['total']}'),
              ),
              const SizedBox(height: 8),
              const Text('See every lesson →', style: TextStyle(color: Brand.navy, fontWeight: FontWeight.w600)),
            ],
          ]),
        ),
      ),
    );
  }
}

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key, required this.childId, required this.name});
  final int childId;
  final String name;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("$name's progress"), bottom: const Beads()),
      body: Loader<Map<String, dynamic>>(
        load: () async => (await Api.instance.get('/api/parent/children/$childId/progress/')) as Map<String, dynamic>,
        builder: (context, d, _) {
          final units = (d['units'] as List).cast<Map<String, dynamic>>();
          final certs = (d['certificates'] as List).cast<Map<String, dynamic>>();
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text('${d['book']}: ${d['done']} of ${d['total']} lessons done', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            for (final c in certs)
              Card(
                color: Brand.goodBg,
                child: ListTile(
                  leading: const Icon(Icons.workspace_premium, color: Brand.good),
                  title: Text('Certificate ${c['number']}'),
                  subtitle: Text('${c['book']} · Sizwe kakhulu!'),
                  trailing: const Icon(Icons.open_in_new),
                  onTap: () => openPdf(context, 'certificate', c['id'] as int),
                ),
              ),
            for (final u in units)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  radius: 16,
                  backgroundColor: u['done'] == true ? Brand.tealInk : const Color(0xFFEEF0F7),
                  child: Text('${u['number']}', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: u['done'] == true ? Colors.white : Brand.muted)),
                ),
                title: Text(u['title_nd'] as String, style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: Text('${u['title_en']}${(u['culture'] as String).isNotEmpty ? ' · ${u['culture']}' : ''}'),
                trailing: u['done'] == true ? const Icon(Icons.check_circle, color: Brand.tealInk, semanticLabel: 'Done') : null,
              ),
          ]);
        },
      ),
    );
  }
}

class LessonsTab extends StatelessWidget {
  const LessonsTab({super.key});
  @override
  Widget build(BuildContext context) {
    return Loader<List<dynamic>>(
      load: () async => (await Api.instance.get('/api/parent/timetable/')) as List<dynamic>,
      isEmpty: (d) => d.isEmpty,
      emptyTitle: 'No lessons booked',
      emptyText: 'Lessons appear here once your child starts.',
      builder: (context, d, _) => ListView(padding: const EdgeInsets.all(16), children: [
        Text('Upcoming lessons, in your time zone.', style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 10),
        for (final l in d.cast<Map<String, dynamic>>())
          Card(
            child: ListTile(
              title: Text(l['when'] as String, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text('${l['child']} · ${l['kind']} · ${l['minutes']} min with ${l['teacher']}'),
              trailing: StatusPill(l['status'] as String, tone: toneFor(l['status'] as String)),
            ),
          ),
      ]),
    );
  }
}

class NotesTab extends StatelessWidget {
  const NotesTab({super.key});
  @override
  Widget build(BuildContext context) {
    return Loader<List<dynamic>>(
      load: () async => (await Api.instance.get('/api/parent/notes/')) as List<dynamic>,
      isEmpty: (d) => d.isEmpty,
      emptyTitle: 'No lesson notes yet',
      emptyText: "After each lesson the teacher writes what your child learned. It appears here.",
      builder: (context, d, _) => ListView(padding: const EdgeInsets.all(16), children: [
        for (final n in d.cast<Map<String, dynamic>>())
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(child: Text('${n['child']} · ${n['when']}', style: const TextStyle(fontWeight: FontWeight.w700))),
                  StatusPill(n['status'] as String, tone: toneFor(n['status'] as String)),
                ]),
                if ((n['unit'] as String).isNotEmpty) ...[const SizedBox(height: 4), Text(n['unit'] as String, style: const TextStyle(color: Brand.navy, fontWeight: FontWeight.w600))],
                const SizedBox(height: 8),
                Text((n['note'] as String).isEmpty ? 'No note for this lesson.' : n['note'] as String),
                const SizedBox(height: 6),
                Text('${n['teacher']}', style: Theme.of(context).textTheme.bodySmall),
              ]),
            ),
          ),
      ]),
    );
  }
}

class MoneyTab extends StatelessWidget {
  const MoneyTab({super.key});
  @override
  Widget build(BuildContext context) {
    return Loader<List<dynamic>>(
      load: () async => (await Api.instance.get('/api/parent/documents/')) as List<dynamic>,
      isEmpty: (d) => d.isEmpty,
      emptyTitle: 'No invoices yet',
      emptyText: 'Invoices and receipts appear here.',
      builder: (context, d, _) => ListView(padding: const EdgeInsets.all(16), children: [
        Card(
          color: Brand.warnBg,
          child: const Padding(
            padding: EdgeInsets.all(14),
            child: Text('Pay by Mukuru, EcoCash Diaspora or Western Union, then send the reference to HILYS on WhatsApp.'),
          ),
        ),
        for (final doc in d.cast<Map<String, dynamic>>())
          Card(
            child: ListTile(
              title: Text('${doc['kind']} ${doc['number']}', style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text([
                if (doc['date'] != null) DateFormat('d MMM yyyy').format(DateTime.parse(doc['date'] as String)),
                if (doc['total'] != null) '${doc['currency']} ${doc['total']}',
                if (doc['outstanding'] != null && doc['outstanding'] != '0.00') 'to pay ${doc['currency']} ${doc['outstanding']}',
              ].join(' · ')),
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                StatusPill(doc['status'] as String, tone: toneFor(doc['status'] as String)),
                const SizedBox(width: 6),
                const Icon(Icons.open_in_new, size: 20, semanticLabel: 'Open PDF'),
              ]),
              onTap: () => openPdf(context, 'document', doc['id'] as int),
            ),
          ),
      ]),
    );
  }
}

class MessagesTab extends StatefulWidget {
  const MessagesTab({super.key});
  @override
  State<MessagesTab> createState() => _MessagesTabState();
}

class _MessagesTabState extends State<MessagesTab> {
  final _text = TextEditingController();
  List<Map<String, dynamic>>? _msgs;
  String? _error;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final d = await Api.instance.get('/api/parent/messages/');
      setState(() => _msgs = (d as List).cast<Map<String, dynamic>>());
    } on ApiError catch (e) {
      setState(() => _error = e.message);
    }
  }

  Future<void> _send() async {
    if (_text.text.trim().isEmpty) return;
    setState(() => _sending = true);
    try {
      final d = await Api.instance.post('/api/parent/messages/', {'body': _text.text.trim()});
      _text.clear();
      setState(() => _msgs = (d as List).cast<Map<String, dynamic>>());
    } on ApiError catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) return Center(child: Text(_error!));
    if (_msgs == null) return const Center(child: CircularProgressIndicator());
    return Column(children: [
      Expanded(
        child: _msgs!.isEmpty
            ? const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('Write to HILYS here: questions, lesson changes, anything.', textAlign: TextAlign.center)))
            : ListView(padding: const EdgeInsets.all(16), reverse: true, children: [
                for (final m in _msgs!.reversed)
                  Align(
                    alignment: m['mine'] == true ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      constraints: const BoxConstraints(maxWidth: 320),
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: m['mine'] == true ? const Color(0xFFE5E8F6) : Colors.white,
                        border: Border.all(color: Brand.line),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(m['from'] as String, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                        const SizedBox(height: 2),
                        Text(m['body'] as String),
                      ]),
                    ),
                  ),
              ]),
      ),
      Container(
        color: Colors.white,
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
        child: Row(children: [
          Expanded(child: TextField(controller: _text, minLines: 1, maxLines: 4, decoration: const InputDecoration(hintText: 'Write a message…', isDense: true))),
          const SizedBox(width: 8),
          FilledButton(onPressed: _sending ? null : _send, child: const Text('Send')),
        ]),
      ),
    ]);
  }
}
