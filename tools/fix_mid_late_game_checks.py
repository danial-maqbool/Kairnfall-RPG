#!/usr/bin/env python3
from pathlib import Path

p=Path('tools/world_probe/MidLateGameContentChecks.cs')
text=p.read_text(encoding='utf-8')
old='''        var dungeons=data.Zones.Where(z=>z.Kind=="dungeon").OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();\n'''
new='''        // The hunting-route pass also creates two beginner dungeon-kind zones that deliberately reuse\n        // existing bosses. Canonical authored boss dungeons are the boss-lore arenas created from DUNGEONS.\n        var dungeons=data.Zones.Where(z=>z.Kind=="dungeon"&&z.Boss!=""\n            &&string.Equals(z.Lore,data.Mob(z.Boss).Lore,StringComparison.Ordinal))\n            .OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();\n'''
if old not in text: raise SystemExit('boss-dungeon fixture anchor missing')
text=text.replace(old,new,1)
old='''            var low=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});\n            Need(!low.Ok&&low.Message.Contains("character level",StringComparison.OrdinalIgnoreCase),"Under-level expedition was not rejected by level.");\n            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);\n'''
new='''            var low=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});\n            Need(!low.Ok&&low.Message.Contains("character level",StringComparison.OrdinalIgnoreCase),"Under-level expedition was not rejected by level.");\n            // Rejected commands restore RealmState from a deep copy; reacquire the authoritative character before fixture seeding.\n            p=realm.Player(p.Id);\n            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);\n'''
if old not in text: raise SystemExit('rollback fixture anchor missing')
text=text.replace(old,new,1)
p.write_text(text,encoding='utf-8')
print('Area 7 verification fixtures corrected')
