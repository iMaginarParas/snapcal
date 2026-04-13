import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text('Settings', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSettingsItem('Step Goal', Icons.flag, '10,000 steps'),
          const Divider(color: Colors.white10),
          _buildSettingsItem('Health Services', Icons.sync, 'Syncing steps'),
          const Divider(color: Colors.white10),
          _buildSettingsItem('Notifications', Icons.notifications, 'All enabled'),
          const Divider(color: Colors.white10),
          _buildSettingsItem('About Us', Icons.info, 'v1.0.0'),
          const SizedBox(height: 32),
          Text(
            'LOG OUT',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.redAccent.withOpacity(0.8),
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsItem(String title, IconData icon, String subtitle) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.blueAccent.withAlpha(50),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: Colors.blueAccent, size: 20),
      ),
      title: Text(title, style: const TextStyle(color: Colors.white)),
      subtitle: Text(subtitle, style: const TextStyle(color: Colors.white38)),
      trailing: const Icon(Icons.chevron_right, color: Colors.white12),
      onTap: () {},
    );
  }
}
