import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'theme.dart';

/// Loads data and shows loading, error (with retry) and empty states the same way on every tab.
class Loader<T> extends StatefulWidget {
  const Loader({super.key, required this.load, required this.builder, this.isEmpty, this.emptyTitle, this.emptyText});
  final Future<T> Function() load;
  final Widget Function(BuildContext, T, Future<void> Function()) builder;
  final bool Function(T)? isEmpty;
  final String? emptyTitle;
  final String? emptyText;

  @override
  State<Loader<T>> createState() => _LoaderState<T>();
}

class _LoaderState<T> extends State<Loader<T>> {
  T? _data;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    setState(() {
      _loading = _data == null;
      _error = null;
    });
    try {
      final d = await widget.load();
      if (mounted) setState(() => _data = d);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Text('We could not load this.', style: TextStyle(fontWeight: FontWeight.w700, color: Brand.bad, fontSize: 17)),
            const SizedBox(height: 6),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _reload, child: const Text('Try again')),
          ]),
        ),
      );
    }
    final data = _data as T;
    if (widget.isEmpty?.call(data) ?? false) {
      return RefreshIndicator(
        onRefresh: _reload,
        child: ListView(padding: const EdgeInsets.all(32), children: [
          const SizedBox(height: 60),
          Text(widget.emptyTitle ?? 'Nothing here yet', textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          if (widget.emptyText != null) Text(widget.emptyText!, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
        ]),
      );
    }
    return RefreshIndicator(onRefresh: _reload, child: widget.builder(context, data, _reload));
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(0, 18, 0, 8),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium),
      );
}

/// The bead strip from the HILYS logo, under the app bar.
class Beads extends StatelessWidget implements PreferredSizeWidget {
  const Beads({super.key});
  @override
  Size get preferredSize => const Size.fromHeight(5);
  @override
  Widget build(BuildContext context) => Row(
        children: List.generate(
          40,
          (i) => Expanded(child: Container(height: 5, color: [Brand.orange, const Color(0xFF138A8A), Brand.navy][i % 3])),
        ),
      );
}
