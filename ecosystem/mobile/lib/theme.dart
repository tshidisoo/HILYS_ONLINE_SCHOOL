// HILYS brand tokens for the parent app. The same values as the website, staff app and PDFs.
import 'package:material_ui/material_ui.dart';

class Brand {
  static const navy = Color(0xFF1F2F86);
  static const orangeInk = Color(0xFFB94515); // text and filled buttons
  static const orange = Color(0xFFE8642C); // decoration only
  static const tealInk = Color(0xFF0F7A7A);
  static const ink = Color(0xFF141A3A);
  static const muted = Color(0xFF4A5170);
  static const line = Color(0xFFDDE0EC);
  static const bg = Color(0xFFF6F7FB);
  static const surface = Color(0xFFFFFFFF);
  static const good = Color(0xFF0F7A5A);
  static const goodBg = Color(0xFFE2F4EC);
  static const warn = Color(0xFF8A5A00);
  static const warnBg = Color(0xFFFDF1D7);
  static const bad = Color(0xFFB3261E);
  static const badBg = Color(0xFFFBE6E4);

  static ThemeData theme() {
    final scheme = ColorScheme.fromSeed(seedColor: navy, primary: navy, secondary: orangeInk, surface: surface);
    return ThemeData(
      colorScheme: scheme,
      scaffoldBackgroundColor: bg,
      useMaterial3: true,
      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontWeight: FontWeight.w800, color: ink, fontSize: 24),
        titleMedium: TextStyle(fontWeight: FontWeight.w700, color: ink, fontSize: 17),
        bodyMedium: TextStyle(color: ink, fontSize: 16, height: 1.4),
        bodySmall: TextStyle(color: muted, fontSize: 14, height: 1.35),
      ),
      appBarTheme: const AppBarTheme(backgroundColor: surface, foregroundColor: ink, elevation: 0, centerTitle: false),
      cardTheme: CardThemeData(
        color: surface, elevation: 0, margin: const EdgeInsets.only(bottom: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: line)),
      ),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(
        backgroundColor: orangeInk, foregroundColor: Colors.white, minimumSize: const Size(48, 48),
        shape: const StadiumBorder(), textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
      outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(
        foregroundColor: navy, minimumSize: const Size(48, 44), shape: const StadiumBorder(), side: const BorderSide(color: line))),
      inputDecorationTheme: InputDecorationTheme(
        filled: true, fillColor: surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: line)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: line)),
      ),
      navigationBarTheme: NavigationBarThemeData(backgroundColor: surface, indicatorColor: navy.withValues(alpha: 0.12)),
    );
  }
}

/// A small coloured status label. One meaning per colour, as in the staff app.
class StatusPill extends StatelessWidget {
  const StatusPill(this.text, {super.key, this.tone = 'neutral'});
  final String text;
  final String tone;

  @override
  Widget build(BuildContext context) {
    final colors = {
      'good': (Brand.goodBg, Brand.good),
      'warn': (Brand.warnBg, Brand.warn),
      'bad': (Brand.badBg, Brand.bad),
      'info': (const Color(0xFFE5E8F6), Brand.navy),
    };
    final (bg, fg) = colors[tone] ?? (const Color(0xFFEEF0F7), Brand.muted);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 13)),
    );
  }
}

String toneFor(String status) {
  final s = status.toLowerCase();
  if (s.contains('paid') && !s.contains('part')) return 'good';
  if (s.contains('taught') || s.contains('active') || s.contains('done')) return 'good';
  if (s.contains('part') || s.contains('missed') || s.contains('cut short') || s.contains('paused')) return 'warn';
  if (s.contains('cancel') || s.contains('overdue')) return 'bad';
  return 'info';
}
