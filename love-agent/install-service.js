/**
 * Installs LOVE Agent as a Windows startup task.
 * Run once: node install-service.js
 * This adds it to Task Scheduler to auto-run at login.
 */
const { execSync } = require('child_process');
const path = require('path');
const os = require('os');

const nodePath = process.execPath;
const agentPath = path.join(__dirname, 'agent.js');
const taskName = 'LOVE-Agent';

if (os.platform() !== 'win32') {
  console.log('Windows only. For Linux/Mac, add to crontab:');
  console.log(`@reboot node ${agentPath} &`);
  process.exit(0);
}

const cmd = [
  'schtasks /Create /F',
  `/TN "${taskName}"`,
  `/TR "\"${nodePath}\" \"${agentPath}\""`,
  '/SC ONLOGON',
  '/RL HIGHEST',
  '/DELAY 0000:30',
].join(' ');

try {
  execSync(cmd);
  console.log(`✓ Task '${taskName}' created — LOVE Agent will start automatically at login.`);
  console.log('To remove: schtasks /Delete /TN LOVE-Agent /F');
} catch (e) {
  console.error('Failed to create task. Try running as Administrator.');
  console.error(e.message);
}
