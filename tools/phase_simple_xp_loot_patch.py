#!/usr/bin/env python3
from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace("src/Kairnfall.Core/Mechanics.cs", '''    public static double PlayerLevelValue(Character p,bool includeCreditRemainder=false)
    {
        double mastery=Math.Clamp(Total(p)/(60.0*Threshold(SkillCap)),0,1);
        long wholeTraining=ChallengeProgression.OverallTraining(p);
        double equivalent=BeginnerProgression.OverallEquivalentXp(wholeTraining);
        if(includeCreditRemainder&&double.IsFinite(p.OverallCreditRemainder)&&p.OverallCreditRemainder>0)
        {
            double fraction=Math.Clamp(p.OverallCreditRemainder,0,.999999999);
            double next=BeginnerProgression.OverallEquivalentXp(wholeTraining+1);
            equivalent+=(next-equivalent)*fraction;
        }
        double ratio=Math.Clamp(equivalent/(60.0*Threshold(SkillCap)),0,1);
        double credited=1+199*Math.Pow(ratio,0.30);
        // Late mastery approaches the cap continuously. It does not create a final-point jump.
        double mastered=1+199*Math.Pow(mastery,1.5);
        return Math.Clamp(Math.Max(credited,mastered),1,PlayerCap);
    }
    public static int PlayerLevel(Character p)=>Math.Clamp((int)Math.Floor(PlayerLevelValue(p)),1,PlayerCap);
    public static double PlayerLevelProgress(Character p)
    {
        int level=PlayerLevel(p);
        return level>=PlayerCap?1:Math.Clamp(PlayerLevelValue(p,true)-level,0,1);
    }
''', '''    public static double PlayerLevelValue(Character p)
    {
        // Character XP is simply the sum of awarded skill XP. Skill challenge rules
        // already reduce weak/trivial actions, so do not apply a second hidden filter.
        long total=Total(p);
        double equivalent=BeginnerProgression.OverallEquivalentXp(total);
        double ratio=Math.Clamp(equivalent/(60.0*Threshold(SkillCap)),0,1);
        double trained=1+199*Math.Pow(ratio,0.30);
        // Late mastery still approaches the cap continuously.
        double mastery=Math.Clamp(total/(60.0*Threshold(SkillCap)),0,1);
        double mastered=1+199*Math.Pow(mastery,1.5);
        return Math.Clamp(Math.Max(trained,mastered),1,PlayerCap);
    }
    public static int PlayerLevel(Character p)=>Math.Clamp((int)Math.Floor(PlayerLevelValue(p)),1,PlayerCap);
    public static double PlayerLevelProgress(Character p)
    {
        int level=PlayerLevel(p);
        return level>=PlayerCap?1:Math.Clamp(PlayerLevelValue(p)-level,0,1);
    }
''')

replace("src/Kairnfall.Core/Loot.cs", '''public sealed class LootPile
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
''', '''public sealed class LootPile
{
    public const double LifetimeSeconds=180;
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
''')

replace("src/Kairnfall.Core/RealmCombat.cs", 'Expires=State.Time+300', 'Expires=State.Time+LootPile.LifetimeSeconds')

replace("src/Kairnfall.Core/RealmEngine.cs", '''        foreach(var l in Loot.Values.Where(x=>x.Expires<=State.Time).ToList()) { Loot.Remove(l.Id); EconomicDirty=true; }
''', '''        foreach(var l in Loot.Values.Where(x=>!double.IsFinite(x.Expires)||x.Expires<=State.Time).ToList()) { Loot.Remove(l.Id); EconomicDirty=true; }
''')
replace("src/Kairnfall.Core/RealmEngine.cs", '''    public List<LootPile> VisibleLoot(string player)
    {
        var p=Player(player); return Loot.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=30).Select(Wire.Copy).ToList();
    }
''', '''    public List<LootPile> VisibleLoot(string player)
    {
        var p=Player(player); return Loot.Values
            .Where(x=>double.IsFinite(x.Expires)&&x.Expires>State.Time&&x.Zone==p.Zone&&x.Position.Distance(p.Position)<=30)
            .Select(Wire.Copy).ToList();
    }
''')

replace("client/Scripts/WorldView.cs", '''            foreach (var pile in Loot)
            {
                visuals.Add(new Visual((float)pile.Position.Y, "loot", pile.Id, pile.Position, pile));
                interactions.Add(new WorldTarget("loot", pile.Id, "Dropped loot", pile.Position));
            }
''', '''            foreach (var pile in Loot)
            {
                if (!double.IsFinite(pile.Expires) || pile.Expires <= RealmTime) continue;
                visuals.Add(new Visual((float)pile.Position.Y, "loot", pile.Id, pile.Position, pile));
                interactions.Add(new WorldTarget("loot", pile.Id, "Dropped loot", pile.Position));
            }
''')

replace("client/Scripts/GameRoot.Experience.cs", '''    private Label interactionHint = null!;
    private VBoxContainer pickupFeed = null!, skillExperienceFeed = null!;
    private ProgressBar characterExperienceBar = null!;
''', '''    private Label interactionHint = null!, skillExperienceText = null!;
    private VBoxContainer pickupFeed = null!;
    private ProgressBar characterExperienceBar = null!, skillExperienceBar = null!;
''')
replace("client/Scripts/GameRoot.Experience.cs", '''    private readonly List<PickupNote> pickupNotes = [];
    private readonly List<SkillExperienceNote> skillExperienceNotes = [];
    private sealed record PickupNote(string Template, Rarity Rarity, int Quantity, double Until);
    private sealed record SkillExperienceNote(string Skill,long Gain,long Xp,int BeforeLevel,int Level,double Until);
''', '''    private readonly List<PickupNote> pickupNotes = [];
    private string lastExperienceSkill = "";
    private sealed record PickupNote(string Template, Rarity Rarity, int Quantity, double Until);
''')
replace("client/Scripts/GameRoot.Experience.cs", '''        skillExperienceFeed = new VBoxContainer
        {
            Name = "SkillExperienceFeed", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -165, OffsetRight = 165, OffsetTop = -346, OffsetBottom = -264,
            MouseFilter = MouseFilterEnum.Ignore
        };
        skillExperienceFeed.AddThemeConstantOverride("separation", 3); hud.AddChild(skillExperienceFeed);
        characterExperienceBar = Ui.Bar(new Color("c2a55f"), 0);
        characterExperienceBar.Name = "CharacterExperienceBar";
        characterExperienceBar.AnchorLeft = 0; characterExperienceBar.AnchorRight = 1;
        characterExperienceBar.AnchorTop = characterExperienceBar.AnchorBottom = 1;
        characterExperienceBar.OffsetLeft = 8; characterExperienceBar.OffsetRight = -8;
        characterExperienceBar.OffsetTop = -7; characterExperienceBar.OffsetBottom = -1;
        characterExperienceBar.CustomMinimumSize = new Vector2(0, 6);
        characterExperienceBar.MouseFilter = MouseFilterEnum.Ignore; hud.AddChild(characterExperienceBar);
''', '')
replace("client/Scripts/GameRoot.Experience.cs", '''        if (skillExperienceNotes.RemoveAll(x => now >= x.Until) > 0) RenderSkillExperience();
''', '')
replace("client/Scripts/GameRoot.Experience.cs", '''        foreach (var skill in Data.Skills)
        {
            long beforeXp=previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            long currentXp=current.Self.SkillXp.GetValueOrDefault(skill.Id);
            long gained=currentXp-beforeXp;
            if(gained>0) ShowSkillExperience(skill.Id,gained,beforeXp,currentXp,now);
        }
''', '''        foreach (var skill in Data.Skills)
        {
            long beforeXp=previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            long currentXp=current.Self.SkillXp.GetValueOrDefault(skill.Id);
            if(currentXp>beforeXp) lastExperienceSkill=skill.Id;
        }
''')
replace("client/Scripts/GameRoot.Experience.cs", '''    private void ShowSkillExperience(string skill,long gained,long beforeXp,long currentXp,double now)
    {
        int existing=skillExperienceNotes.FindIndex(x=>x.Skill==skill&&x.Until>now);
        long totalGain=gained; int beforeLevel=Progression.SkillLevel(beforeXp);
        if(existing>=0)
        {
            totalGain+=skillExperienceNotes[existing].Gain;
            beforeLevel=skillExperienceNotes[existing].BeforeLevel;
            skillExperienceNotes.RemoveAt(existing);
        }
        skillExperienceNotes.Add(new(skill,totalGain,currentXp,beforeLevel,Progression.SkillLevel(currentXp),now+2.6));
        if(skillExperienceNotes.Count>3)skillExperienceNotes.RemoveRange(0,skillExperienceNotes.Count-3);
        RenderSkillExperience();
    }

    private void RenderSkillExperience()
    {
        if(skillExperienceFeed is null)return;
        Ui.Clear(skillExperienceFeed);
        foreach(var note in skillExperienceNotes)
        {
            var card=new PanelContainer { MouseFilter=MouseFilterEnum.Ignore };
            card.AddThemeStyleboxOverride("panel",Ui.Box(new Color("1c1a17"),new Color("647a5f"),4));
            skillExperienceFeed.AddChild(card);
            var column=Ui.Column(card); column.MouseFilter=MouseFilterEnum.Ignore; column.AddThemeConstantOverride("separation",1);
            string levels=note.Level>note.BeforeLevel?$" · Level {note.BeforeLevel} → {note.Level}":$" · Level {note.Level}";
            column.AddChild(Ui.Label(Data.Skill(note.Skill).Name+$"  +{note.Gain:N0} XP"+levels,11,Ui.Success));
            var bar=Ui.Bar(new Color("789b62"),312); bar.Name="SkillExperienceBar_"+note.Skill;
            bar.CustomMinimumSize=new Vector2(312,7); bar.MaxValue=100; bar.Value=Progression.SkillLevelProgress(note.Xp)*100;
            int level=Progression.SkillLevel(note.Xp);
            if(level>=Progression.SkillCap) bar.TooltipText=Data.Skill(note.Skill).Name+" mastered";
            else
            {
                long floor=Progression.Threshold(level),ceiling=Progression.Threshold(level+1);
                bar.TooltipText=$"{note.Xp-floor:N0} / {ceiling-floor:N0} XP toward level {level+1}";
            }
            column.AddChild(bar);
        }
    }

''', '')

replace("client/Scripts/GameRoot.Hud.cs", '''        experiencePacing = Ui.Label("", 11, Ui.Muted, true); experiencePacing.Name = "ExperiencePacing"; column.AddChild(experiencePacing);
        healthText = Ui.Label("", 13); column.AddChild(healthText); health = Ui.Bar(new Color("a94c46"), 262); column.AddChild(health);
''', '''        experiencePacing = Ui.Label("", 11, Ui.Muted, true); experiencePacing.Name = "ExperiencePacing"; column.AddChild(experiencePacing);
        characterExperienceBar = Ui.Bar(new Color("c2a55f"), 262); characterExperienceBar.Name = "CharacterExperienceBar";
        characterExperienceBar.CustomMinimumSize = new Vector2(262, 9); characterExperienceBar.MouseFilter = MouseFilterEnum.Ignore; column.AddChild(characterExperienceBar);
        skillExperienceText = Ui.Label("Skill XP · train any skill", 11, Ui.Muted, true); skillExperienceText.Name = "SkillExperienceText"; column.AddChild(skillExperienceText);
        skillExperienceBar = Ui.Bar(new Color("789b62"), 262); skillExperienceBar.Name = "SkillExperienceBar";
        skillExperienceBar.CustomMinimumSize = new Vector2(262, 9); skillExperienceBar.MouseFilter = MouseFilterEnum.Ignore; column.AddChild(skillExperienceBar);
        healthText = Ui.Label("", 13); column.AddChild(healthText); health = Ui.Bar(new Color("a94c46"), 262); column.AddChild(health);
''')
replace("client/Scripts/GameRoot.Hud.cs", '''        experiencePacing.Text = overallLevel>=Progression.PlayerCap ? "Overall level cap reached" : $"Level progress {overallProgress:P0} · training credit {ChallengeProgression.OverallRate(overallLevel):P0}";
        experiencePacing.TooltipText = "Successful skill practice advances overall level. Trivial practice is strongly reduced but no longer enters a permanent zero-XP dead zone.";
        if(characterExperienceBar is not null)
        {
            characterExperienceBar.MaxValue=100; characterExperienceBar.Value=overallProgress*100;
            characterExperienceBar.TooltipText=overallLevel>=Progression.PlayerCap?"Overall level 200 · maximum":$"Overall level {overallLevel} → {overallLevel+1} · {overallProgress:P1}";
        }
''', '''        experiencePacing.Text = overallLevel>=Progression.PlayerCap ? "Character XP · Level 200" : $"Character XP · Level {overallLevel} → {overallLevel+1}";
        experiencePacing.TooltipText = "Every awarded skill XP point contributes directly to character level.";
        characterExperienceBar.MaxValue=100; characterExperienceBar.Value=overallProgress*100;
        characterExperienceBar.TooltipText=overallLevel>=Progression.PlayerCap?"Character level 200 · maximum":$"Character level {overallLevel} → {overallLevel+1} · {overallProgress:P1}";
        string displaySkill=lastExperienceSkill;
        if(displaySkill==""||!Data.Skills.Any(x=>x.Id==displaySkill))
            displaySkill=Data.Skills.OrderByDescending(x=>self.SkillXp.GetValueOrDefault(x.Id)).ThenBy(x=>x.Id).First().Id;
        long displayedXp=self.SkillXp.GetValueOrDefault(displaySkill);
        int displayedLevel=Progression.SkillLevel(displayedXp);
        double displayedProgress=Progression.SkillLevelProgress(displayedXp);
        string displayedName=Data.Skill(displaySkill).Name;
        skillExperienceText.Text=displayedLevel>=Progression.SkillCap?$"{displayedName} XP · Level 100":$"{displayedName} XP · Level {displayedLevel} → {displayedLevel+1}";
        skillExperienceBar.MaxValue=100; skillExperienceBar.Value=displayedProgress*100;
        skillExperienceBar.TooltipText=displayedLevel>=Progression.SkillCap?displayedName+" mastered":$"{displayedProgress:P1} toward {displayedName} level {displayedLevel+1}";
''')

replace("client/Scripts/GameRoot.cs", '''        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear(); skillExperienceNotes.Clear();
        chatLog.Text = ""; RenderPickupFeed(); RenderSkillExperience(); ShowLogin();
''', '''        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear(); lastExperienceSkill = "";
        chatLog.Text = ""; RenderPickupFeed(); ShowLogin();
''')

replace("tests/Kairnfall.Tests/Program.cs", '''Test("Overall level derives from skill XP and respects cap",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); Check(Progression.PlayerLevel(p)==1,"New character level.");
    Progression.Train(p,"mining",1000,1,data); Check(Progression.PlayerLevel(p)>1,"Noncombat skill did not raise overall level.");
    foreach(var skill in data.Skills) p.SkillXp[skill.Id]=Progression.Threshold(100);
    Check(Progression.PlayerLevel(p)==200,"Overall cap mismatch.");
});
''', '''Test("Overall level derives directly from awarded skill XP and respects cap",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); Check(Progression.PlayerLevel(p)==1,"New character level.");
    Progression.Train(p,"mining",1000,1,data);
    int trainedLevel=Progression.PlayerLevel(p); double trainedProgress=Progression.PlayerLevelProgress(p);
    Check(trainedLevel>1,"Noncombat skill did not raise character level.");
    p.PracticeOnlyXp=Progression.Total(p); p.OverallCreditRemainder=0;
    Check(Progression.PlayerLevel(p)==trainedLevel&&Math.Abs(Progression.PlayerLevelProgress(p)-trainedProgress)<.000001,"Hidden credit metadata changed character XP.");
    foreach(var skill in data.Skills) p.SkillXp[skill.Id]=Progression.Threshold(100);
    Check(Progression.PlayerLevel(p)==200,"Overall cap mismatch.");
});
Test("Expired ground loot is hidden and removed",()=>
{
    var r=NewRealm(); var p=NewPlayer(r);
    var expired=new LootPile{Zone=p.Zone,Position=p.Position,Expires=r.State.Time-1}; r.Loot[expired.Id]=expired;
    Check(!r.VisibleLoot(p.Id).Any(x=>x.Id==expired.Id),"Expired loot was still visible.");
    var fresh=new LootPile{Zone=p.Zone,Position=p.Position,Expires=r.State.Time+.2}; r.Loot[fresh.Id]=fresh;
    Check(r.VisibleLoot(p.Id).Any(x=>x.Id==fresh.Id),"Fresh loot was hidden early.");
    r.Tick(.1); r.Tick(.1); r.Tick(.1);
    Check(!r.Loot.ContainsKey(fresh.Id),"Expired loot remained in the realm.");
    Check(LootPile.LifetimeSeconds==180,"Ground-loot lifetime must stay at three minutes.");
});
''')
