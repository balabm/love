panel_path = "ui/src/components/SentinelPanel.jsx"
with open(panel_path, "r", encoding="utf-8") as f:
    panel = f.read()

# SentinelPanel has 3 arrays with the same engine list
old_marker = '"sacred_ritual_designer", "contemplation_keeper",'
new_marker = '"sacred_ritual_designer", "contemplation_keeper",\n                "inner_critic_tamer", "perfectionism_healer", "comparison_detoxifier",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("Done.")
