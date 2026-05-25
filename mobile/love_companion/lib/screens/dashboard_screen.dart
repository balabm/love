import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/love_service.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Life Dashboard')),
      body: Consumer<LoveService>(
        builder: (_, service, __) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Connection status card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      service.connected ? Icons.wifi : Icons.wifi_off,
                      color: service.connected ? Colors.greenAccent : Colors.redAccent,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        service.connected
                            ? 'Connected to LOVE at ${service.serverUrl}'
                            : service.lastError ?? 'Disconnected',
                        style: const TextStyle(fontSize: 13),
                      ),
                    ),
                    if (!service.connected)
                      TextButton(onPressed: service.connect, child: const Text('Retry')),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Proactive pushes
            if (service.pushes.isNotEmpty) ...[
              const Text('Recent from LOVE', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...service.pushes.take(5).map((push) => Card(
                child: ListTile(
                  leading: _pushIcon(push.category),
                  title: Text(push.message, style: const TextStyle(fontSize: 14)),
                  subtitle: Text(push.category, style: const TextStyle(fontSize: 11)),
                ),
              )),
            ] else
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    'LOVE is watching for patterns.\nInsights will appear here.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white54),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _pushIcon(String category) {
    final icons = {
      'ALERT': Icons.warning_amber,
      'INSIGHT': Icons.lightbulb_outline,
      'NUDGE': Icons.notifications_active_outlined,
      'THOUGHT': Icons.psychology_outlined,
      'EVOLUTION': Icons.upgrade,
      'MEMORY': Icons.memory,
    };
    final colors = {
      'ALERT': Colors.orangeAccent,
      'INSIGHT': Colors.yellowAccent,
      'NUDGE': Colors.blueAccent,
      'THOUGHT': Colors.purpleAccent,
      'EVOLUTION': Colors.greenAccent,
      'MEMORY': Colors.tealAccent,
    };
    return Icon(icons[category] ?? Icons.circle, color: colors[category] ?? Colors.white54);
  }
}
