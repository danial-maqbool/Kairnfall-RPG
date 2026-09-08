using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private void ClosePage()
    {
        refreshPage = null; page = null; currentPage = ""; lastPageStamp = "";
        if (gameWindow is not null) { gameWindow.QueueFree(); gameWindow = null; }
    }
    private void OpenPage(string name)
    {
        if (Snapshot is null && name != "Settings") return;
        ClosePage(); currentPage = name;
        gameWindow = new PanelContainer { Size = new Vector2(Math.Min(1100, Size.X - 80), Math.Min(670, Size.Y - 140)) };
        interfaceRoot.AddChild(gameWindow); gameWindow.Position = (Size - gameWindow.Size) / 2;
        var contents = Ui.Column(gameWindow, true); var header = Ui.Row(contents); header.MouseFilter = MouseFilterEnum.Stop;
        var title = Ui.Label(name, 26, Ui.Gold); title.SizeFlagsHorizontal = SizeFlags.ExpandFill; header.AddChild(title);
        header.AddChild(Ui.Button("Close  [Esc]", ClosePage));
        header.GuiInput += e =>
        {
            if (e is InputEventMouseMotion motion && (motion.ButtonMask & MouseButtonMask.Left) != 0 && gameWindow is not null)
            {
                var position = gameWindow.Position + motion.Relative;
                gameWindow.Position = new Vector2(Math.Clamp(position.X, 0, Math.Max(0, Size.X - gameWindow.Size.X)), Math.Clamp(position.Y, 0, Math.Max(0, Size.Y - gameWindow.Size.Y)));
            }
        };
        contents.AddChild(new HSeparator()); page = Ui.Column(contents, true);
        switch (name)
        {
            case "Inventory": BuildInventoryPage(false); break;
            case "Bank": BuildInventoryPage(true); break;
            case "Character": BuildCharacterPage(); break;
            case "Equipment Guide": BuildEquipmentGuidePage(); break;
            case "Shop": BuildShopPage(); break;
            case "Skills": BuildSkillsPage(); break;
            case "Abilities": BuildAbilitiesPage(); break;
            case "Quests": BuildQuestsPage(); break;
            case "Dialogue": BuildDialoguePage(); break;
            case "Crafting": BuildCraftingPage(); break;
            case "Social": BuildSocialPage(); break;
            case "Trade": BuildTradePage(); break;
            case "Auction": BuildAuctionPage(); break;
            case "Map": BuildMapPage(); break;
            case "Bestiary": BuildBestiaryPage(); break;
            case "Achievements": BuildAchievementsPage(); break;
            case "Settings": BuildSettingsPage(); break;
            default: throw new InvalidOperationException("Unknown client page: " + name);
        }
    }

    private void BuildSkillsPage()
    {
        if (page is null || Snapshot is null) return;
        var guide = new SkillGuidePanel
        {
            Data = Data, Assets = Assets, ReadCharacter = () => Snapshot?.Self
        };
        page.AddChild(guide);
        refreshPage = guide.RefreshSnapshot;
        guide.RefreshSnapshot();
    }

    private void BuildAbilitiesPage()
    {
        if (page is null || Snapshot is null) return;
        var guide = new AbilityGuidePanel
        {
            Data = Data, Assets = Assets, ReadCharacter = () => Snapshot?.Self,
            ReadTime = () => Snapshot?.Time ?? 0, ReadHotbar = () => hotbar,
            AssignToHotbar = (id, index) =>
            {
                if (Snapshot is not { } snapshot || index < 0 || index >= hotbar.Length) return;
                var ability = Data.Abilities.FirstOrDefault(a => a.Id == id);
                if (ability is null || Progression.Level(snapshot.Self, ability.Skill) < ExperienceRules.AbilityRequirement(snapshot.Self, ability)) return;
                hotbar[index] = id;
                settings.SetValue("hotbar_" + snapshot.Self.Id, index.ToString(), id); settings.Save("user://settings.cfg");
                Notify(ability.Name + " assigned to key " + (index == 9 ? "0" : (index + 1).ToString()) + ".");
            }
        };
        page.AddChild(guide); refreshPage = guide.RefreshSnapshot;
    }

    private void BuildDialoguePage()
    {
        if (page is null || Snapshot is null) return;
        var npc = Data.Npcs.FirstOrDefault(x => x.Id == selectedNpc);
        if (npc is null) return;
        var row = Ui.Row(page); row.AddChild(Ui.Image(Assets.Frame("npcs/" + npc.Role, 0, 0, 0), 110)); var text = Ui.Column(row);
        text.AddChild(Ui.Label(npc.Name, 25, Ui.Gold)); text.AddChild(Ui.Label(Ui.Words(npc.Role) + " · " + Ui.Words(npc.Faction), 14, Ui.Muted)); text.AddChild(Ui.Label(npc.Dialogue, 17, Ui.Text, true));
        var services = Ui.Row(page);
        if (npc.Stock.Length > 0) services.AddChild(Ui.Button("Trade goods", () => OpenPage("Shop")));
        if (npc.Role == "banker") services.AddChild(Ui.Button("Open bank", () => { selectedBag = "bank"; OpenPage("Bank"); }));
        if (npc.Role == "auctioneer") services.AddChild(Ui.Button("Auction house", () => OpenPage("Auction")));
        if (npc.Station != "") services.AddChild(Ui.Button("Use " + Ui.Words(npc.Station), () => OpenPage("Crafting")));
        if (npc.Role == "blacksmith") services.AddChild(Ui.Button("Repair equipment", () => OpenPage("Inventory")));
        if (npc.Role == "enchanter") services.AddChild(Ui.Button("Work with runes", () => OpenPage("Inventory")));
        if (npc.Role == "innkeeper") services.AddChild(Ui.Button("Rest · 5 gold", () => Send("rest")));
        if (npc.Role is "trainer" or "scholar") services.AddChild(Ui.Button("Skills and abilities", () => OpenPage("Skills")));
        if (npc.Role == "guild_registrar") services.AddChild(Ui.Button("Guild services", () => OpenPage("Social")));
        services.AddChild(Ui.Button("Waystone travel", () => OpenPage("Map")));
        var scroll = Ui.Scroll(page, new Vector2(840, 310)); var offers = Ui.Column(scroll);
        void Render()
        {
            if (Snapshot is null) return; Ui.Clear(offers);
            foreach (var quest in Data.Quests.Where(x => x.Giver == npc.Id))
            {
                bool active = Snapshot.Self.Quests.TryGetValue(quest.Id, out var progress);
                bool complete = Snapshot.Self.CompletedQuests.Contains(quest.Id);
                bool unlocked = quest.Prerequisite == "" || Snapshot.Self.CompletedQuests.Contains(quest.Prerequisite);
                bool cooldown = Snapshot.Self.Cooldowns.GetValueOrDefault("quest:" + quest.Id) > Snapshot.Time;
                if (!active && ((!quest.Repeatable && complete) || !unlocked || cooldown)) continue;
                var card = new PanelContainer(); offers.AddChild(card); var body = Ui.Column(card);
                body.AddChild(Ui.Label(quest.Name + (quest.Repeatable ? " · Repeatable" : ""), 20, Ui.Gold)); body.AddChild(Ui.Label(quest.Story, 15, Ui.Text, true));
                foreach (var objective in quest.Objectives) body.AddChild(Ui.Label("• " + objective.Description, 14, Ui.Muted, true));
                body.AddChild(Ui.Label($"Reward: {quest.Gold} gold" + (quest.Reward != "" ? " · " + Data.Item(quest.Reward).Name : ""), 14, Ui.Success));
                if (!active) body.AddChild(Ui.Button("Accept quest", () => Send("accept_quest", item: quest.Id), !NearNpc(npc)));
                else if (progress!.Complete) body.AddChild(Ui.Button("Claim reward", () => Send("claim_quest", item: quest.Id), !NearNpc(npc)));
                else body.AddChild(Ui.Button("Track objectives", () => { selectedQuest = quest.Id; OpenPage("Quests"); }));
            }
            if (offers.GetChildCount() == 0) offers.AddChild(Ui.Label("No further work is available here at present.", 16, Ui.Muted, true));
        }
        refreshPage = Render; Render();
    }

    private void BuildQuestsPage()
    {
        if (page is null || Snapshot is null) return;
        var top = Ui.Row(page); top.AddChild(Ui.Button("Bestiary", () => OpenPage("Bestiary"))); top.AddChild(Ui.Button("Achievements and factions", () => OpenPage("Achievements")));
        var body = Ui.Row(page); body.SizeFlagsVertical = SizeFlags.ExpandFill;
        var listing = Ui.Column(Ui.Scroll(body, new Vector2(300, 440))); var detail = Ui.Column(Ui.Scroll(body, new Vector2(520, 440)));
        void Render()
        {
            if (Snapshot is null) return; Ui.Clear(listing); Ui.Clear(detail);
            foreach (var entry in Snapshot.Self.Quests)
            {
                var quest = Data.Quest(entry.Key); listing.AddChild(Ui.Button((entry.Value.Complete ? "✓ " : "") + quest.Name, () => { selectedQuest = quest.Id; refreshPage?.Invoke(); }));
            }
            if (Snapshot.Self.Quests.Count == 0) listing.AddChild(Ui.Label("Speak with people in Wayfarer's Rest to find work.", 16, Ui.Muted, true));
            var selected = Data.Quests.FirstOrDefault(x => x.Id == selectedQuest && Snapshot.Self.Quests.ContainsKey(x.Id));
            selected ??= Snapshot.Self.Quests.Count > 0 ? Data.Quest(Snapshot.Self.Quests.Keys.First()) : null;
            if (selected is null) return;
            var progress = Snapshot.Self.Quests[selected.Id]; var giver = Data.Npc(selected.Giver);
            detail.AddChild(Ui.Label(selected.Name, 25, Ui.Gold)); detail.AddChild(Ui.Label(selected.Story, 17, Ui.Text, true));
            for (int i = 0; i < selected.Objectives.Count; i++)
            {
                var objective = selected.Objectives[i]; int count = i < progress.Counts.Count ? progress.Counts[i] : 0;
                detail.AddChild(Ui.Label($"{Math.Min(count, objective.Count)}/{objective.Count}  {objective.Description}", 16, count >= objective.Count ? Ui.Success : Ui.Text, true));
            }
            detail.AddChild(Ui.Label($"Reward: {selected.Gold} gold" + (selected.Reward == "" ? "" : " · " + Data.Item(selected.Reward).Name), 16, Ui.Success));
            detail.AddChild(Ui.Label("Return to " + giver.Name + " in " + Data.Zone(giver.Zone).Name + ".", 15, Ui.Muted, true));
            var questId = selected.Id;
            detail.AddChild(Ui.Button("Mark quest giver", () => MarkDestination(giver.Zone, giver.Position)));
            if (progress.Complete) detail.AddChild(Ui.Button("Claim reward", () => Send("claim_quest", item: questId), !NearNpc(giver)));
        }
        refreshPage = Render; Render();
    }

    private bool ClientAtStation(string station)
    {
        if (Snapshot is null) return false;
        return station == "hand" || Data.Npcs.Any(x => x.Station == station && NearNpc(x)) || Snapshot.Nodes.Any(x => x.Zone == Snapshot.Self.Zone && x.Owner == Snapshot.Self.Id && x.Template == "structure_" + station && x.Position.Distance(Snapshot.Self.Position) <= 3 && WorldMap.LineOfSight(Data.Zone(Snapshot.Self.Zone), Snapshot.Self.Position, x.Position));
    }
    private void BuildCraftingPage()
    {
        if (page is null || Snapshot is null) return;
        var guide=new CraftingGuidePanel
        {
            Data=Data, Assets=Assets, ReadCharacter=()=>Snapshot?.Self, ReadTime=()=>Snapshot?.Time??0,
            AtStation=ClientAtStation, CanSubmit=()=>Online&&!actionBusy,
            InitialRecipe=selectedRecipe, InitialSearch=equipmentRecipeSearch, RecipeSelected=id=>selectedRecipe=id,
            CraftRequested=(id,batches)=>Send("craft",item:id,amount:batches),
            PlaceRequested=id=> { structureRecipe=id; placement="build"; ClosePage(); Notify("Select clear wilderness within three tiles. Materials are consumed only after the server accepts placement."); },
            PlantRequested=()=> { placement="plant"; structureRecipe=""; ClosePage(); Notify("Select clear soil within two tiles. One wheat seed is required."); }
        };
        equipmentRecipeSearch=""; page.AddChild(guide); refreshPage=guide.RefreshSnapshot;
    }

    private void BuildBestiaryPage()
    {
        if (page is null || Snapshot is null) return;
        page.AddChild(Ui.Label("Defeated creatures are recorded here. Unknown creatures remain undiscovered.", 16, Ui.Muted, true));
        var rows = Ui.Column(Ui.Scroll(page, new Vector2(850, 440)));
        foreach (var entry in Snapshot.Self.Bestiary.OrderBy(x => Data.Mob(x.Key).Level))
        {
            var creature = Data.Mob(entry.Key); var card = new PanelContainer(); rows.AddChild(card); var row = Ui.Row(card);
            row.AddChild(Ui.Image(Assets.Frame("mobs/" + creature.Id, 0, 0, 0), 100)); var text = Ui.Column(row);
            text.AddChild(Ui.Label(creature.Name + " · Level " + creature.Level, 22, creature.Boss ? Ui.Gold : Ui.Text)); text.AddChild(Ui.Label(creature.Lore, 15, Ui.Muted, true));
            text.AddChild(Ui.Label($"Defeated: {entry.Value} · {Ui.Words(creature.Biome)} · {creature.Element}\n" + string.Join(" · ", creature.Resistances.Select(x => x.Key + " " + (x.Value * 100).ToString("0") + "%")), 14, Ui.Muted, true));
        }
        if (Snapshot.Self.Bestiary.Count == 0) rows.AddChild(Ui.Label("No creatures recorded yet.", 18, Ui.Gold));
    }
    private void BuildAchievementsPage()
    {
        if (page is null || Snapshot is null) return;
        var rows = Ui.Column(Ui.Scroll(page, new Vector2(840, 460)));
        rows.AddChild(Ui.Label("Achievements", 24, Ui.Gold));
        foreach (string achievement in Snapshot.Self.Achievements) rows.AddChild(Ui.Label("✓ " + Ui.Words(achievement), 18, Ui.Success));
        if (Snapshot.Self.Achievements.Count == 0) rows.AddChild(Ui.Label("Explore, help settlements, and overcome encounters to earn achievements.", 16, Ui.Muted, true));
        rows.AddChild(Ui.Label("Faction reputation", 24, Ui.Gold));
        foreach (string faction in Data.Npcs.Select(x => x.Faction).Where(x => x != "").Distinct().Order())
        {
            int reputation = Snapshot.Self.Reputation.GetValueOrDefault(faction); rows.AddChild(Ui.Label(Ui.Words(faction) + " · " + reputation + "/1000", 17)); var bar = Ui.Bar(new Color("94aa7b"), 650); bar.MaxValue = 1000; bar.Value = reputation; rows.AddChild(bar);
        }
        rows.AddChild(Ui.Label($"Completed quests: {Snapshot.Self.CompletedQuests.Count}\nDiscovered waystones: {Snapshot.Self.Waypoints.Count}", 17, Ui.Muted));
    }

    private void BuildSettingsPage()
    {
        if (page is null) return;
        var rows = Ui.Column(Ui.Scroll(page, new Vector2(800, 450)));
        rows.AddChild(Ui.Label("Display and sound", 22, Ui.Gold));
        AddToggle(rows, "Weather effects", World.WeatherEnabled, value => { World.WeatherEnabled = value; settings.SetValue("display", "weather", value); });
        AddToggle(rows, "NPC and player names", World.ShowNames, value => { World.ShowNames = value; settings.SetValue("display", "names", value); });
        AddToggle(rows, "Fullscreen", DisplayServer.WindowGetMode() == DisplayServer.WindowMode.Fullscreen, value => DisplayServer.WindowSetMode(value ? DisplayServer.WindowMode.Fullscreen : DisplayServer.WindowMode.Windowed));
        var volume = Ui.Row(rows); volume.AddChild(Ui.Label("Music", 15, Ui.Muted));
        var music = new HSlider { MinValue = 0, MaxValue = 1, Step = .05, Value = settings.GetValue("audio", "music", .35).AsDouble(), CustomMinimumSize = new Vector2(260, 26) }; volume.AddChild(music);
        var sounds = Ui.Row(rows); sounds.AddChild(Ui.Label("Effects", 15, Ui.Muted));
        var effects = new HSlider { MinValue = 0, MaxValue = 1, Step = .05, Value = settings.GetValue("audio", "effects", .65).AsDouble(), CustomMinimumSize = new Vector2(260, 26) }; sounds.AddChild(effects);
        music.ValueChanged += value => { settings.SetValue("audio", "music", value); settings.Save("user://settings.cfg"); audio?.SetVolumes((float)value, (float)effects.Value); };
        effects.ValueChanged += value => { settings.SetValue("audio", "effects", value); settings.Save("user://settings.cfg"); audio?.SetVolumes((float)music.Value, (float)value); };
        rows.AddChild(Ui.Label("Key bindings", 22, Ui.Gold)); rows.AddChild(Ui.Label("Select a key, then press its replacement. Press Escape to cancel. Arrow keys also move the character.", 15, Ui.Muted, true));
        foreach (var entry in bindings)
        {
            var row = Ui.Row(rows); var title = Ui.Label(Ui.Words(entry.Key), 16); title.CustomMinimumSize = new Vector2(220, 0); row.AddChild(title);
            var button = Ui.Button(entry.Value.ToString(), () => { awaitingBinding = entry.Key; Notify("Press a key for " + Ui.Words(entry.Key) + ". Escape cancels."); }); button.CustomMinimumSize = new Vector2(180, 34); row.AddChild(button);
        }
        var actions = Ui.Row(rows);
        if (Connection is not null)
        {
            actions.AddChild(Ui.Button("Reconnect", async () => { try { if (Connection is not null && Connection.CharacterId != "") { await Connection.ConnectAsync(Connection.CharacterId); ClosePage(); Notify("Connection restored."); } } catch (Exception e) { ShowLogin(e.Message); } }));
            actions.AddChild(Ui.Button("Sign out", Logout));
        }
        actions.AddChild(Ui.Button("Exit game", () => _ = ShutdownAsync()));
    }
    private void AddToggle(Node parent, string text, bool value, Action<bool> changed)
    {
        var button = new CheckButton { Text = text, ButtonPressed = value }; parent.AddChild(button);
        button.Toggled += on => { changed(on); settings.Save("user://settings.cfg"); };
    }
}
