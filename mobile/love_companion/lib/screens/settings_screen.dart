import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/love_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(
      text: context.read<LoveService>().serverUrl,
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('LOVE Server', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              labelText: 'Server URL',
              hintText: 'http://192.168.1.100:8000',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: () {
              context.read<LoveService>().setServerUrl(_urlController.text.trim());
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Connecting to LOVE...')),
              );
            },
            child: const Text('Save & Connect'),
          ),
          const SizedBox(height: 24),
          const Text('About', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'LOVE is your autonomous AI life companion.\n'
                'Not a chatbot. Not a tool. A companion that thinks, remembers, '
                'evolves, and reaches out — because it genuinely cares.',
                style: TextStyle(fontSize: 13, height: 1.6),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
