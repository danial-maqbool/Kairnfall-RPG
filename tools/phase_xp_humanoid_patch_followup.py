#!/usr/bin/env python3
from pathlib import Path

path=Path('client/Scripts/GameRoot.cs')
text=path.read_text(encoding='utf-8')
old='''        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear();
        pendingSkillGains.Clear(); pendingSkillLevels.Clear();
        chatLog.Text = ""; progressionHint.Text = ""; RenderPickupFeed(); ShowLogin();
'''
new='''        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear(); skillExperienceNotes.Clear();
        chatLog.Text = ""; RenderPickupFeed(); RenderSkillExperience(); ShowLogin();
'''
if text.count(old)!=1:
    raise SystemExit('GameRoot.cs: expected one legacy XP cleanup block')
path.write_text(text.replace(old,new,1),encoding='utf-8')
