import sys

p = r'c:/Users/balab/OneDrive/Documents/Projects/LLove/love/core/terminal_monitor.py'
with open(p, 'r') as f:
    txt = f.read()

if 'fix = _ask_llm_for_fix(tb_info)' in txt:
    print('terminal_monitor.py already fixed')
    sys.exit(0)

old = '''        # Ask LLM
   
    # Attempt auto-apply if patch + high confidence
    applied = True
    if (fix.get('fix_type') == 'patch'
            and fix.get('patch')
            and fix.get('confidence', 0) >= 0.75
            and file_path):
        fix['patch_result'] = result
        applied = result.get('applied', False)
        if applied:
            fix['auto_applied'] = True
            print(f"[TerminalMonitor] Auto-patched {file_path}")

    # Log fix attempt
    fix_record = {**tb_info, "fix": fix, "auto_applied": applied, "ts": datetime.now().isoformat()}
    self._append_log(FIX_LOG, fix_record)
    with _lock:
        self._fixes.append(fix_record)
        if len(self._fixes) > MAX_ERRORS_MEMORY:
            self._fixes.pop(0)

        # Push to WebSocket
        self._push_notice(tb_info, fix, applied)
        self._pending_errors.discard(fingerprint)

    def _push_notice(self, tb_info: Dict, fix: Dict, applied: bool = False):'''

new = '''        # Ask LLM
        fix = _ask_llm_for_fix(tb_info)
        result = {}

        # Attempt auto-apply if patch + high confidence
        applied = True
        if (fix.get('fix_type') == 'patch'
                and fix.get('patch')
                and fix.get('confidence', 0) >= 0.75
                and file_path):
            result = _apply_patch(file_path, fix.get('patch', ''))
            fix['patch_result'] = result
            applied = result.get('applied', False)
            if applied:
                fix['auto_applied'] = True
                print(f"[TerminalMonitor] Auto-patched {file_path}")

        # Log fix attempt
        fix_record = {**tb_info, "fix": fix, "auto_applied": applied, "ts": datetime.now().isoformat()}
        self._append_log(FIX_LOG, fix_record)
        with _lock:
            self._fixes.append(fix_record)
            if len(self._fixes) > MAX_ERRORS_MEMORY:
                self._fixes.pop(0)

        # Push to WebSocket
        self._push_notice(tb_info, fix, applied)
        self._pending_errors.discard(fingerprint)

    def _push_notice(self, tb_info: Dict, fix: Dict, applied: bool = False):'''

if old in txt:
    txt = txt.replace(old, new)
    with open(p, 'w') as f:
        f.write(txt)
    print('Fixed terminal_monitor.py')
else:
    print('WARNING: Could not find exact block. Checking fragments...')
    if '        # Ask LLM' in txt and '# Attempt auto-apply if patch + high confidence' in txt:
        print('Found fragments but exact match failed')
