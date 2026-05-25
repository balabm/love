import 'dart:convert';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ChatMessage {
  final String id;
  final String role; // 'user' or 'love'
  final String content;
  final String? thinking;
  final DateTime timestamp;
  bool isLoading;

  ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    this.thinking,
    DateTime? timestamp,
    this.isLoading = false,
  }) : timestamp = timestamp ?? DateTime.now();
}

class ProactivePush {
  final String category;
  final String message;
  final String priority;
  final DateTime timestamp;

  ProactivePush({
    required this.category,
    required this.message,
    required this.priority,
    required this.timestamp,
  });

  factory ProactivePush.fromJson(Map<String, dynamic> json) => ProactivePush(
    category: json['category'] ?? 'INSIGHT',
    message: json['message'] ?? '',
    priority: json['priority'] ?? 'normal',
    timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
  );
}

class LoveService extends ChangeNotifier {
  static const String _serverUrlKey = 'love_server_url';
  static const String _defaultUrl = 'http://192.168.1.100:8000'; // Change in settings

  String _serverUrl = _defaultUrl;
  WebSocketChannel? _wsChannel;
  bool _connected = false;
  bool _connecting = false;
  final List<ChatMessage> _messages = [];
  final List<ProactivePush> _pushes = [];
  String? _lastError;
  Timer? _reconnectTimer;

  String get serverUrl => _serverUrl;
  bool get connected => _connected;
  bool get connecting => _connecting;
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  List<ProactivePush> get pushes => List.unmodifiable(_pushes);
  String? get lastError => _lastError;

  LoveService() {
    _loadServerUrl();
  }

  Future<void> _loadServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _serverUrl = prefs.getString(_serverUrlKey) ?? _defaultUrl;
    notifyListeners();
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_serverUrlKey, url);
    notifyListeners();
    // Reconnect with new URL
    disconnect();
    await connect();
  }

  Future<void> connect() async {
    if (_connecting || _connected) return;
    _connecting = true;
    _lastError = null;
    notifyListeners();

    try {
      final wsUrl = _serverUrl.replaceFirst('http', 'ws') + '/ws';
      _wsChannel = WebSocketChannel.connect(Uri.parse(wsUrl));

      _wsChannel!.stream.listen(
        (data) {
          try {
            final json = jsonDecode(data as String);
            _handleMessage(json);
          } catch (e) {
            debugPrint('WS parse error: $e');
          }
        },
        onError: (error) {
          _connected = false;
          _lastError = 'Connection error: $error';
          notifyListeners();
          _scheduleReconnect();
        },
        onDone: () {
          _connected = false;
          notifyListeners();
          _scheduleReconnect();
        },
      );

      _connected = true;
      _connecting = false;
      notifyListeners();
    } catch (e) {
      _connected = false;
      _connecting = false;
      _lastError = 'Failed to connect: $e';
      notifyListeners();
      _scheduleReconnect();
    }
  }

  void _handleMessage(Map<String, dynamic> json) {
    final type = json['type'] as String?;

    if (type == 'proactive_push') {
      // LOVE reached out proactively
      final push = ProactivePush.fromJson(json);
      _pushes.insert(0, push);
      // Also show as a chat message from LOVE
      _messages.add(ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        role: 'love',
        content: '[${push.category}] ${push.message}',
      ));
      notifyListeners();
    } else if (type == 'heartbeat') {
      // Keep-alive, ignore
    } else if (json.containsKey('response')) {
      // Regular chat response
      final msgId = json['id'] as String?;
      if (msgId != null) {
        final idx = _messages.indexWhere((m) => m.id == msgId && m.isLoading);
        if (idx >= 0) {
          _messages[idx] = ChatMessage(
            id: msgId,
            role: 'love',
            content: json['response'] as String? ?? '',
            thinking: json['thinking'] as String?,
          );
          notifyListeners();
        }
      }
    }
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), connect);
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _wsChannel?.sink.close();
    _wsChannel = null;
    _connected = false;
    notifyListeners();
  }

  Future<ChatMessage> sendMessage(String text) async {
    final msgId = DateTime.now().millisecondsSinceEpoch.toString();

    // Add user message
    _messages.add(ChatMessage(id: '${msgId}_u', role: 'user', content: text));

    // Add loading placeholder
    final loadingMsg = ChatMessage(
      id: msgId,
      role: 'love',
      content: '',
      isLoading: true,
    );
    _messages.add(loadingMsg);
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text, 'mode': 'general'}),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final idx = _messages.indexWhere((m) => m.id == msgId);
        if (idx >= 0) {
          _messages[idx] = ChatMessage(
            id: msgId,
            role: 'love',
            content: data['response'] as String? ?? 'No response',
            thinking: data['thinking'] as String?,
          );
        }
      } else {
        _updateLoadingMsg(msgId, 'Error: ${response.statusCode}');
      }
    } catch (e) {
      _updateLoadingMsg(msgId, 'Failed to reach LOVE: $e');
    }

    notifyListeners();
    return _messages.firstWhere((m) => m.id == msgId);
  }

  void _updateLoadingMsg(String id, String content) {
    final idx = _messages.indexWhere((m) => m.id == id);
    if (idx >= 0) {
      _messages[idx] = ChatMessage(id: id, role: 'love', content: content);
    }
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
