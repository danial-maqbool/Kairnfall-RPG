from pathlib import Path
p = Path('src/Kairnfall.Core/RealmSocial.cs')
text = p.read_text()
old_left = 'if(left.RecentPlayers.GetValueOrDefault(right.Id)<State.Time-30) { left.RecentPlayers[right.Id]=State.Time; changed=true; }'
new_left = 'if(!left.RecentPlayers.ContainsKey(right.Id)||left.RecentPlayers[right.Id]<State.Time-30) { left.RecentPlayers[right.Id]=State.Time; changed=true; }'
old_right = 'if(right.RecentPlayers.GetValueOrDefault(left.Id)<State.Time-30) { right.RecentPlayers[left.Id]=State.Time; changed=true; }'
new_right = 'if(!right.RecentPlayers.ContainsKey(left.Id)||right.RecentPlayers[left.Id]<State.Time-30) { right.RecentPlayers[left.Id]=State.Time; changed=true; }'
if old_left not in text or old_right not in text:
    raise SystemExit('recent-player refinement anchors were not found')
p.write_text(text.replace(old_left,new_left,1).replace(old_right,new_right,1))
print('recent-player first-contact refinement applied')
