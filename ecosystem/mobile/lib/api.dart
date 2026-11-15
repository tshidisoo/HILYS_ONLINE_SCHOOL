// One way to talk to the HILYS API. Errors come back in plain words.
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Set at build time: flutter build web --dart-define=API_URL=https://api.hilys.com
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://127.0.0.1:8000');

class ApiError implements Exception {
  ApiError(this.message, {this.status = 0});
  final String message;
  final int status;
  @override
  String toString() => message;
}

class Api {
  Api._();
  static final Api instance = Api._();
  static const _tokenKey = 'hilys-parent-token';
  String? _token;
  void Function()? onSignedOut;

  Future<bool> restore() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(_tokenKey);
    return _token != null;
  }

  Future<void> _save(String? token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    if (token == null) {
      await prefs.remove(_tokenKey);
    } else {
      await prefs.setString(_tokenKey, token);
    }
  }

  Future<Map<String, dynamic>> signIn(String username, String password) async {
    final data = await post('/api/auth/login/', {'username': username, 'password': password, 'app': 'parent'});
    await _save(data['token'] as String);
    return data['user'] as Map<String, dynamic>;
  }

  Future<void> signOut() async {
    try {
      await post('/api/auth/logout/', {});
    } catch (_) {
      // Already signed out on the server.
    }
    await _save(null);
  }

  Map<String, String> get _headers => {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Token $_token',
      };

  Future<dynamic> get(String path) => _send(() => http.get(Uri.parse('$apiUrl$path'), headers: _headers));

  Future<dynamic> post(String path, Map<String, dynamic> body) =>
      _send(() => http.post(Uri.parse('$apiUrl$path'), headers: _headers, body: jsonEncode(body)));

  Future<dynamic> _send(Future<http.Response> Function() call) async {
    http.Response res;
    try {
      res = await call().timeout(const Duration(seconds: 20));
    } catch (_) {
      throw ApiError('We could not reach HILYS. Check your internet and try again.');
    }
    final text = utf8.decode(res.bodyBytes);
    final data = text.isEmpty ? null : jsonDecode(text);
    if (res.statusCode == 401) {
      await _save(null);
      onSignedOut?.call();
      throw ApiError('Please sign in again.', status: 401);
    }
    if (res.statusCode >= 500) throw ApiError('Something went wrong on our side. Try again in a minute.', status: res.statusCode);
    if (res.statusCode >= 400) {
      var message = 'Please check and try again.';
      if (data is Map && data.isNotEmpty) {
        final first = data['detail'] ?? data.values.first;
        message = first is List ? first.join(' ') : '$first';
      }
      throw ApiError(message, status: res.statusCode);
    }
    return data;
  }
}
