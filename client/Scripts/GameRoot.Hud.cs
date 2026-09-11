using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private HudPanel targetFrame = null!, chatFrame = null!;
    private ProgressBar targetHealth = null!;
    private Label targetDetail = null!, objectiveText = null!, experiencePacing = null!;
    private VBoxContainer chatBody = null!;
    private Button chatToggle = null!, objectiveToggle = null!;
    private bool chatExpanded = true;

    private void BuildHud()
    {
        hud = new Control { Name = "GameHud", MouseFilter = MouseFilterEnum.Ignore };
        interfaceRoot.AddChild(hud); hud.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect); interfaceRoot.MoveChild(hud, 0);
        var leftHud = new VBoxContainer
        {
            Name = "VitalsAndObjectives", Position = new Vector2(16, 16),
            CustomMinimumSize = new Vector2(286, 0), MouseFilter = MouseFilterEnum.Ignore
        };
        leftHud.AddThemeConstantOverride("separation", 10); hud.AddChild(leftHud);
        var vitals = new HudPanel { Name = "Vitals", CustomMinimumSize = new Vector2(286, 0) };
        leftHud.AddChild(vitals);
        var column = Ui.Column(vitals); column.AddThemeConstantOverride("separation", 4);
        characterTitle = Ui.Label("", 17, Ui.Gold); column.AddChild(characterTitle);
        experiencePacing = Ui.Label("", 11, Ui.Muted, true); experiencePacing.Name = "ExperiencePacing"; column.AddChild(experiencePacing);
        characterExperienceBar = Ui.Bar(new Color("c2a55f"), 262); characterExperienceBar.Name = "CharacterExperienceBar";
        characterExperienceBar.CustomMinimumSize = new Vector2(262, 9); characterExperienceBar.MouseFilter = MouseFilterEnum.Ignore; column.AddChild(characterExperienceBar);
        skillExperienceText = Ui.Label("Skill XP · train any skill", 11, Ui.Muted, true); skillExperienceText.Name = "SkillExperienceText"; column.AddChild(skillExperienceText);
        skillExperienceBar = Ui.Bar(new Color("789b62"), 262); skillExperienceBar.Name = "SkillExperienceBar";
        skillExperienceBar.CustomMinimumSize = new Vector2(262, 9); skillExperienceBar.MouseFilter = MouseFilterEnum.Ignore; column.AddChild(skillExperienceBar);
        healthText = Ui.Label("", 13); column.AddChild(healthText); health = Ui.Bar(new Color("a94c46"), 262); column.AddChild(health);
        manaText = Ui.Label("", 13); column.AddChild(manaText); mana = Ui.Bar(new Color("587db7"), 262); column.AddChild(mana);
        staminaText = Ui.Label("", 13); column.AddChild(staminaText); stamina = Ui.Bar(new Color("899955"), 262); column.AddChild(stamina);
        var title = new VBoxContainer
        {
            AnchorLeft = .5f, AnchorRight = .5f, OffsetLeft = -260, OffsetRight = 260, OffsetTop = 16,
            MouseFilter = MouseFilterEnum.Ignore
        };
        hud.AddChild(title);
        location = Ui.Label("", 21, Ui.Gold); location.HorizontalAlignment = HorizontalAlignment.Center; title.AddChild(location);
        connectionText = Ui.Label("", 13, Ui.Danger, true); connectionText.HorizontalAlignment = HorizontalAlignment.Center; title.AddChild(connectionText);
        targetFrame = new HudPanel
        {
            Name = "SelectedTarget", AnchorLeft = .5f, AnchorRight = .5f,
            OffsetLeft = -173, OffsetRight = 173, OffsetTop = 70, Visible = false, MouseFilter = MouseFilterEnum.Ignore
        };
        hud.AddChild(targetFrame);
        var targetColumn = Ui.Column(targetFrame); targetColumn.MouseFilter = MouseFilterEnum.Ignore; targetColumn.AddThemeConstantOverride("separation", 3);
        targetText = Ui.Label("", 16, Ui.Text); targetText.HorizontalAlignment = HorizontalAlignment.Center; targetColumn.AddChild(targetText);
        targetHealth = Ui.Bar(new Color("a94c46"), 322); targetHealth.MouseFilter = MouseFilterEnum.Ignore; targetColumn.AddChild(targetHealth);
        targetDetail = Ui.Label("", 12, Ui.Muted, true); targetDetail.Name = "TargetChallenge"; targetDetail.HorizontalAlignment = HorizontalAlignment.Center; targetColumn.AddChild(targetDetail);
        var objectives = new HudPanel { Name = "QuestTracker", CustomMinimumSize = new Vector2(286, 0) };
        leftHud.AddChild(objectives);
        var objectiveColumn = Ui.Column(objectives); objectiveColumn.AddThemeConstantOverride("separation", 4);
        var objectiveHeader = Ui.Row(objectiveColumn);
        var heading = Ui.Label("CURRENT OBJECTIVE", 12, Ui.Gold); heading.SizeFlagsHorizontal = SizeFlags.ExpandFill; objectiveHeader.AddChild(heading);
        objectiveText = Ui.Label("", 14, Ui.Text, true); objectiveText.CustomMinimumSize = new Vector2(264, 0);
        bool expanded = settings.GetValue("hud", "objectives", true).AsBool();
        objectiveText.Visible = expanded;
        objectiveToggle = Ui.Button(expanded ? "−" : "+", () =>
        {
            objectiveText.Visible = !objectiveText.Visible;
            objectiveToggle.Text = objectiveText.Visible ? "−" : "+";
            settings.SetValue("hud", "objectives", objectiveText.Visible); settings.Save("user://settings.cfg");
        });
        objectiveToggle.Name = "ToggleObjectives"; objectiveToggle.FocusMode = FocusModeEnum.None;
        objectiveToggle.CustomMinimumSize = new Vector2(26, 26); objectiveHeader.AddChild(objectiveToggle);
        objectiveColumn.AddChild(objectiveText);
        var minimapPanel = new HudPanel
        {
            Name = "MinimapPanel", AnchorLeft = 1, AnchorRight = 1,
            OffsetLeft = -210, OffsetRight = -16, OffsetTop = 16, OffsetBottom = 193
        };
        hud.AddChild(minimapPanel);
        var mini = Ui.Column(minimapPanel); mini.AddThemeConstantOverride("separation", 4);
        mini.AddChild(new MinimapView { World = World, Data = Data, CustomMinimumSize = new Vector2(172, 122) });
        var mapButton = Ui.Button("World map [M]", () => OpenPage("Map")); mapButton.FocusMode = FocusModeEnum.None; mini.AddChild(mapButton);
        var hotbarPanel = new HudPanel
        {
            Name = "AbilityBar", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -353, OffsetRight = 353, OffsetTop = -88, OffsetBottom = -10
        };
        hud.AddChild(hotbarPanel);
        var bar = Ui.Row(hotbarPanel); bar.AddThemeConstantOverride("separation", 6);
        for (int i = 0; i < hotbar.Length; i++)
        {
            int slot = i;
            var button = new AbilitySlot
            {
                Name = "Hotbar_" + (i == 9 ? 0 : i + 1), PressedAction = () => UseHotbar(slot),
                FocusMode = FocusModeEnum.None, CustomMinimumSize = new Vector2(60, 54),
                TextureFilter = TextureFilterEnum.Nearest, SizeFlagsHorizontal = SizeFlags.ExpandFill,
                MouseDefaultCursorShape = CursorShape.PointingHand
            };
            hotbarButtons[i] = button; bar.AddChild(button);
        }
        chatFrame = new HudPanel
        {
            Name = "ChatPanel", AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = 16, OffsetRight = 316, OffsetTop = -258, OffsetBottom = -106
        };
        hud.AddChild(chatFrame);
        var chat = Ui.Column(chatFrame); chat.AddThemeConstantOverride("separation", 4);
        var chatHeader = Ui.Row(chat);
        var chatTitle = Ui.Label("CHAT", 12, Ui.Gold); chatTitle.SizeFlagsHorizontal = SizeFlags.ExpandFill; chatHeader.AddChild(chatTitle);
        chatToggle = Ui.Button("−", () => ShowChat(!chatExpanded)); chatToggle.Name = "ToggleChat";
        chatToggle.FocusMode = FocusModeEnum.None; chatToggle.CustomMinimumSize = new Vector2(26, 26); chatHeader.AddChild(chatToggle);
        chatBody = Ui.Column(chat); chatBody.AddThemeConstantOverride("separation", 4);
        chatLog = new RichTextLabel
        {
            BbcodeEnabled = false, ScrollFollowing = true, CustomMinimumSize = new Vector2(278, 48),
            SizeFlagsVertical = SizeFlags.ExpandFill
        };
        chatLog.AddThemeFontSizeOverride("normal_font_size", 13); chatBody.AddChild(chatLog);
        var sendRow = Ui.Row(chatBody); sendRow.AddThemeConstantOverride("separation", 4);
        chatChannel = new OptionButton { CustomMinimumSize = new Vector2(70, 30) };
        foreach (string channel in new[] { "local", "global", "party", "guild", "whisper" }) chatChannel.AddItem(channel);
        sendRow.AddChild(chatChannel);
        chatInput = Ui.Edit("Enter to chat"); chatInput.MaxLength = 300; sendRow.AddChild(chatInput);
        chatInput.TextSubmitted += text =>
        {
            if (text.Trim() != "") Send("chat", chatChannel.GetItemText(chatChannel.Selected), selectedTargetKind == "player" ? selectedTarget : "", arg: text.Trim());
            chatInput.Text = ""; chatInput.ReleaseFocus();
        };
        ShowChat(settings.GetValue("hud", "chat", true).AsBool());
        var navigation = new HudPanel
        {
            Name = "Navigation", AnchorLeft = 1, AnchorRight = 1, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -346, OffsetRight = -16, OffsetTop = -211, OffsetBottom = -106
        };
        hud.AddChild(navigation);
        var grid = new GridContainer { Columns = 4 }; grid.AddThemeConstantOverride("h_separation", 4); grid.AddThemeConstantOverride("v_separation", 4); navigation.AddChild(grid);
        foreach (var entry in new[] { ("Bag [I]", "Inventory"), ("Gear [C]", "Character"), ("Skills [K]", "Skills"), ("Arts [B]", "Abilities"), ("Quest [J]", "Quests"), ("Hunt [H]", "Hunting"), ("Craft [F]", "Crafting"), ("Social [P]", "Social"), ("Menu", "Settings") })
        {
            var button = Ui.Button(entry.Item1, () => OpenPage(entry.Item2));
            button.FocusMode = FocusModeEnum.None; button.AddThemeFontSizeOverride("font_size", 12); grid.AddChild(button);
        }
        notice = Ui.Label("", 16, Ui.Text, true);
        notice.AnchorLeft = notice.AnchorRight = .5f; notice.AnchorTop = notice.AnchorBottom = 1;
        notice.OffsetLeft = -300; notice.OffsetRight = 300; notice.OffsetTop = -250; notice.OffsetBottom = -215;
        notice.HorizontalAlignment = HorizontalAlignment.Center; notice.AddThemeConstantOverride("outline_size", 4); notice.AddThemeColorOverride("font_outline_color", Ui.Ink); hud.AddChild(notice);
        deathPanel = new HudPanel
        {
            Name = "RespawnPanel", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = .5f, AnchorBottom = .5f,
            OffsetLeft = -240, OffsetRight = 240, OffsetTop = -90, OffsetBottom = 100, Visible = false
        };
        hud.AddChild(deathPanel);
        var death = Ui.Column(deathPanel); death.AddChild(Ui.Label("Your journey continues", 24, Ui.Gold));
        deathText = Ui.Label("", 16, Ui.Text, true); death.AddChild(deathText);
        respawnButton = Ui.Button("Return to safety", () => Send("respawn")); death.AddChild(respawnButton);
    }

    private void ShowChat(bool expanded)
    {
        chatExpanded = expanded; chatBody.Visible = expanded; chatToggle.Text = expanded ? "−" : "+";
        chatFrame.OffsetTop = expanded ? -258 : -155;
        if (!expanded && chatInput.HasFocus()) chatInput.ReleaseFocus();
        settings.SetValue("hud", "chat", expanded); settings.Save("user://settings.cfg");
    }

    private string AbilityTooltip(Character self, AbilityDef ability)
    {
        return ability.Name + "\n" + Ui.Words(ability.Kind) + " · " + ability.Element
            + "\n" + ability.Description
            + $"\nMana {ability.Mana:0.#} · Stamina {ability.Stamina:0.#}"
            + $"\nCooldown {ability.Cooldown:0.#} s · Range {ability.Range:0.#} tiles"
            + "\nRequires " + Data.Skill(ability.Skill).Name + " " + ExperienceRules.AbilityRequirement(self, ability)
            + (ability.Status == "" ? "" : "\nEffect: " + Ui.Words(ability.Status) + $" · {ability.Duration:0.#} s");
    }

    private void UpdateHud()
    {
        if (hud is null) return;
        hud.Visible = Snapshot is not null;
        if (Snapshot is not { } snap) return;
        var self = snap.Self; var stats = CombatMath.Stats(self, Data);
        characterTitle.Text = self.Name + " · Level " + Progression.PlayerLevel(self);
        characterTitle.TooltipText = Data.Class(self.Class).Name + " · " + self.Gold + " gold";
        int overallLevel = Progression.PlayerLevel(self);
        double overallProgress=Progression.PlayerLevelProgress(self);long characterXp=Progression.Total(self);
        long nextCharacterXp=overallLevel>=Progression.PlayerCap?characterXp:Progression.PlayerThreshold(overallLevel+1);
        long remainingCharacterXp=Math.Max(0,nextCharacterXp-characterXp);
        experiencePacing.Text = overallLevel>=Progression.PlayerCap ? "Character XP · Level 200" : $"Character XP · Level {overallLevel} → {overallLevel+1} · {remainingCharacterXp:N0} XP";
        experiencePacing.TooltipText = "Every awarded skill XP point contributes directly to character level. Levels 1-20 are deliberately quick; later bands require progressively more XP.";
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
        health.MaxValue = stats.Health; health.Value = self.Health; healthText.Text = $"Health  {Math.Ceiling(self.Health):0} / {stats.Health:0}";
        mana.MaxValue = stats.Mana; mana.Value = self.Mana; manaText.Text = $"Mana  {Math.Ceiling(self.Mana):0} / {stats.Mana:0}";
        stamina.MaxValue = stats.Stamina; stamina.Value = self.Stamina; staminaText.Text = $"Stamina  {Math.Ceiling(self.Stamina):0} / {stats.Stamina:0}";
        var zone = Data.Zone(self.Zone); location.Text = zone.Name;
        location.TooltipText = zone.Layer + " · " + WorldTime.Weather(zone, snap.Time);
        var target = selectedTargetKind == "creature" ? snap.Creatures.FirstOrDefault(x => x.Id == selectedTarget && x.Health > 0) : null;
        targetFrame.Visible = target is not null;
        if (target is not null)
        {
            var definition = Data.Mob(target.Template);
            double distance = self.Position.Distance(target.Position);
            targetText.Text = (definition.Boss ? "BOSS · " : definition.Elite ? "ELITE · " : "") + definition.Name + " · Level " + definition.Level;
            targetHealth.MaxValue = definition.Health; targetHealth.Value = target.Health;
            bool reachable = ExperienceRules.CanTarget(self, target, Data, ExperienceRules.WeaponRange(self, Data), true);
            targetDetail.Text = $"{Math.Ceiling(target.Health):0} / {definition.Health:0} health · {distance:0.0} tiles · " + (reachable ? "In weapon range" : "Out of range or blocked");
            double practice = ChallengeProgression.SkillPractice(overallLevel, definition.Level);
            double credit = ChallengeProgression.EnemyCredit(overallLevel, definition.Level) * ChallengeProgression.OverallRate(overallLevel);
            targetDetail.Text += $"\n{ChallengeProgression.ChallengeName(overallLevel, definition.Level)} · {practice:P0} practice · {credit:P1} overall credit";
            targetDetail.Text += "\n" + EnemyCombatRules.TacticLabel(definition);
            if(definition.Boss) targetDetail.Text += " · Phase " + (target.Phase+1) + "/3 · " + string.Join(" / ",EnemyCombatRules.AvailableBossAttacks(definition,target.Phase).Select(EnemyCombatRules.AttackLabel));
            targetDetail.TooltipText = "Practice scales the base combat skill award before skill mastery and affinity. Enemy tactic and boss attack cues describe authoritative server behavior; move out of telegraphs and interrupt long casts when possible.";
            var effects = target.Statuses.Where(x => x.Until > snap.Time).Select(x => Ui.Words(x.Kind)).Distinct().Take(3).ToArray();
            if (effects.Length > 0) targetDetail.Text += "\n" + string.Join(" · ", effects);
        }
        connectionText.Text = Connection?.Connected == true ? "" : "Disconnected. Open Menu to reconnect.";
        deathPanel.Visible = self.Health <= 0;
        if (deathPanel.Visible)
        {
            deathText.Text = "Your equipment remains yours. Repair damaged equipment after returning to a settlement.\nRespawn in " + Math.Max(0, Math.Ceiling(self.DeadUntil - snap.Time)) + " seconds.";
            respawnButton.Disabled = self.DeadUntil > snap.Time;
        }
        var tracked = self.Quests.OrderBy(x=>JourneyProgression.QuestPriority(Data.Quest(x.Key))).ThenBy(x=>x.Key,StringComparer.Ordinal).FirstOrDefault();
        if (tracked.Value is null)
        {
            var lead=JourneyProgression.LocalQuest(Data,self);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);
            if(lead is not null)objectiveText.Text=$"NEW LEAD · {lead.QuestName}\nTalk to {lead.GiverName} here.\nOpen Quest [J] or Hunt [H] for direction.";
            else if(zone.Kind=="interior"&&zone.Exits.FirstOrDefault() is { } wayOut)
                objectiveText.Text=$"Return outside\nExit toward {Data.Zone(wayOut.Target).Name}\nInteract: E";
            else if(next is not null&&next.Locked)
                objectiveText.Text=$"NEXT FRONTIER · {next.ZoneName}\nUnlocks at Level {next.EntryLevel} · {next.LevelsNeeded} to go\nTrain {activity?.Name??"skills"}, craft, gather or quest · Hunt [H]";
            else if(next is not null)
                objectiveText.Text=$"NEXT FRONTIER · {next.ZoneName}\nThreat {next.ThreatLevel} · Entry {next.EntryLevel}+ · READY\nOpen Hunt [H] and select the exit.";
            else objectiveText.Text=activity is null?"Explore, quest, craft and hunt to advance.":$"BUILD {activity.Name.ToUpperInvariant()} · Level {Progression.BaseLevel(self,activity.Id)}\n{activity.Action}\nHunt [H] shows local routes.";
        }
        else
        {
            var quest = Data.Quest(tracked.Key);
            int next = Enumerable.Range(0, quest.Objectives.Count).FirstOrDefault(i => tracked.Value.Counts.ElementAtOrDefault(i) < quest.Objectives[i].Count, -1);
            string guidance=next<0?"":JourneyProgression.ObjectiveGuidance(Data,quest,quest.Objectives[next]);
            objectiveText.Text = quest.Name + "\n" + (next < 0 ? "Return to " + Data.Npcs.First(x => x.Id == quest.Giver).Name + " to claim the reward."
                : quest.Objectives[next].Description + "\n" + tracked.Value.Counts.ElementAtOrDefault(next) + " / " + quest.Objectives[next].Count + (guidance==""?"":" · "+guidance));
        }
        for (int i = 0; i < hotbar.Length; i++)
        {
            string id = hotbar[i]; var button = (AbilitySlot)hotbarButtons[i]; string key = (i == 9 ? 0 : i + 1).ToString();
            if (string.IsNullOrEmpty(id))
            {
                button.Present(null, key, 0, 1, Element.Physical, "", "Assign an ability from Arts [B].", Online); continue;
            }
            var ability = Data.Ability(id);
            double cooldown = Math.Max(self.Cooldowns.GetValueOrDefault("ability:" + id), self.Cooldowns.GetValueOrDefault("global_ability")) - snap.Time;
            string problem = ExperienceRules.AbilityProblem(self, ability, Data, snap.Time);
            button.Present(Assets.AbilityIcon(id), key, cooldown, ability.Cooldown, ability.Element, problem,
                AbilityTooltip(self, ability) + (problem == "" ? "" : "\n" + problem), Online && gameWindow is null && !Typing && applicationFocused);
        }
    }
}
