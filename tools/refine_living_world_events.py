from pathlib import Path

path = Path(__file__).resolve().parent / "apply_living_world_events.py"
text = path.read_text(encoding="utf-8")
marker = text.index("# Hunting Guide prioritizes local public incidents")
start = text.index('replace_once("client/Scripts/HuntingGuidePanel.cs",', marker)
end = text.index("# The exact source uses ()=>null, not null!; handle current spelling.", start)
text = text[:start] + text[end:]
path.write_text(text, encoding="utf-8")
print("Living-world candidate helper refined for current HuntingGuide source.")
