using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool authenticationBusy;
    private Control hud = null!;
    private PanelContainer deathPanel = null!;
    private Button respawnButton = null!;
    private Label deathText = null!;
    private Label connectionText = null!;

    private VBoxContainer FrontPage(string title)
    {
        Ui.Clear(frontend); frontend.Visible = true;
        var shade = new ColorRect { Color = new Color(.035f, .055f, .07f, .64f), MouseFilter = MouseFilterEnum.Stop };
        frontend.AddChild(shade); shade.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        var center = new CenterContainer(); frontend.AddChild(center); center.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        var panel = new PanelContainer { CustomMinimumSize = new Vector2(600, 0) }; center.AddChild(panel);
        var column = Ui.Column(panel);
        var gameName = Ui.Label("K A I R N F A L L", 36, Ui.Gold); gameName.HorizontalAlignment = HorizontalAlignment.Center; column.AddChild(gameName);
        var subtitle = Ui.Label(title, 18, Ui.Muted); subtitle.HorizontalAlignment = HorizontalAlignment.Center; column.AddChild(subtitle);
        column.AddChild(new HSeparator());
        return column;
    }

    private void ShowLogin(string message = "")
    {
        authenticationBusy = false;
        var column = FrontPage("Enter a persistent realm");
        column.AddChild(Ui.Label("Server", 14, Ui.Muted));
        var address = Ui.Edit("https://your-realm.example", settings.GetValue("connection", "address", "http://127.0.0.1:5077").AsString()); column.AddChild(address);
        column.AddChild(Ui.Label("Account name", 14, Ui.Muted));
        var username = Ui.Edit("Account name", settings.GetValue("connection", "username", "").AsString()); column.AddChild(username);
        column.AddChild(Ui.Label("Password", 14, Ui.Muted));
        var password = Ui.Edit("Password", secret: true); column.AddChild(password);
        var repeat = Ui.Edit("Repeat password for a new account", secret: true); column.AddChild(repeat);
        var status = Ui.Label(message, 14, Ui.Danger, true); status.CustomMinimumSize = new Vector2(540, 38); column.AddChild(status);
        var buttons = Ui.Row(column);
        Button login = null!, register = null!;
        async void Authenticate(bool create)
        {
            if (authenticationBusy) return;
            if (create && password.Text != repeat.Text) { status.Text = "The passwords do not match."; return; }
            authenticationBusy = true; login.Disabled = true; register.Disabled = true; status.Text = "Connecting to the realm…";
            try
            {
                if (Connection is not null) await Connection.DisposeAsync();
                Connection = new GameConnection(address.Text.Trim());
                await Connection.SignInAsync(username.Text.Trim(), password.Text, create, lifetime.Token);
                var catalog = await Connection.CatalogAsync(lifetime.Token);
                var errors = catalog.Validate();
                if (errors.Count != 0) throw new InvalidDataException("The server content pack is invalid.");
                Data = catalog; World.Data = Data;
                settings.SetValue("connection", "address", address.Text.Trim()); settings.SetValue("connection", "username", username.Text.Trim()); settings.Save("user://settings.cfg");
                password.Text = ""; repeat.Text = "";
                await ShowCharactersAsync();
            }
            catch (Exception error)
            {
                if (GodotObject.IsInstanceValid(status)) { status.Text = error.Message; login.Disabled = false; register.Disabled = false; }
            }
            finally { authenticationBusy = false; }
        }
        login = Ui.Button("Sign in", () => Authenticate(false)); login.SizeFlagsHorizontal = SizeFlags.ExpandFill; buttons.AddChild(login);
        register = Ui.Button("Create account", () => Authenticate(true)); register.SizeFlagsHorizontal = SizeFlags.ExpandFill; buttons.AddChild(register);
        password.TextSubmitted += _ => Authenticate(false);
        repeat.TextSubmitted += _ => Authenticate(true);
        column.AddChild(Ui.Label("A realm server must be running. For a local realm, run Run-Kairnfall-Dev.ps1. Remote connections require HTTPS.", 14, Ui.Muted, true));
        column.AddChild(Ui.Label("Passwords and session tokens are not saved in client settings.", 13, Ui.Muted, true));
        var footer = Ui.Row(column); footer.AddChild(Ui.Button("Settings", () => OpenPage("Settings"))); footer.AddChild(Ui.Button("Exit", () => _ = ShutdownAsync()));
    }

    private async Task ShowCharactersAsync()
    {
        if (Connection is null) return;
        var characters = await Connection.CharactersAsync(lifetime.Token);
        var column = FrontPage("Choose your traveler");
        foreach (var character in characters)
        {
            var card = Ui.Row(column);
            var cls = Data.Class(character.Class);
            var preview = new AvatarPreview { Assets = Assets, Appearance = character.Appearance, CustomMinimumSize = new Vector2(70, 92), Equipment = StarterEquipment(cls) };
            card.AddChild(preview);
            var details = Ui.Column(card);
            details.AddChild(Ui.Label(character.Name, 22, Ui.Gold));
            details.AddChild(Ui.Label(cls.Name + "  ·  Level " + character.Level + "  ·  " + Data.Zone(character.Zone).Name, 14, Ui.Muted));
            var enter = Ui.Button("Enter world", () => EnterWorld(character.Id)); card.AddChild(enter);
        }
        if (characters.Count == 0) column.AddChild(Ui.Label("Create a character to begin at Wayfarer's Rest.", 17, Ui.Text, true));
        var buttons = Ui.Row(column);
        buttons.AddChild(Ui.Button("Create character", ShowCharacterCreation, characters.Count >= 4));
        buttons.AddChild(Ui.Button("Sign out", Logout));
    }
    private Dictionary<string, string> StarterEquipment(ClassDef cls)
        => new() { ["weapon"] = cls.Weapon, [Data.Item(cls.Armor).Slot] = cls.Armor };

    private async void EnterWorld(string characterId)
    {
        if (Connection is null || authenticationBusy) return;
        authenticationBusy = true;
        try
        {
            await Connection.ConnectAsync(characterId, lifetime.Token);
            int read = 0;
            while (read++ < 150 && Connection.TryRead(out var packet)) if (packet?.Snapshot is not null) { World.Accept(packet); invitations = packet.Invitations ?? []; }
            frontend.Visible = false; SetInitialHotbar(); ClosePage();
            Notify("WASD or arrows to move. E to interact. Right-click to walk. Select a creature to attack.");
        }
        catch (Exception error) { Notify(error.Message, true); ShowLogin(error.Message); }
        finally { authenticationBusy = false; }
    }

    private void ShowCharacterCreation()
    {
        var column = FrontPage("Create your traveler");
        var name = Ui.Edit("Character name: 3–20 characters"); name.MaxLength = 20; column.AddChild(name);
        var cls = new OptionButton(); foreach (var definition in Data.Classes) cls.AddItem(definition.Name + " — " + definition.Role); column.AddChild(cls);
        var description = Ui.Label("", 14, Ui.Muted, true); description.CustomMinimumSize = new Vector2(540, 52); column.AddChild(description);
        var row = Ui.Row(column);
        var appearance = new Appearance();
        var avatar = new AvatarPreview { Assets = Assets, Appearance = appearance, CustomMinimumSize = new Vector2(180, 210) }; row.AddChild(avatar);
        var options = Ui.Column(row);
        AddChoice(options, "Body", ["Broad frame", "Narrow frame"], 0, value => appearance.Body = value);
        AddChoice(options, "Skin", ["Ivory", "Warm sand", "Ochre", "Copper", "Umber", "Deep brown"], 0, value => appearance.Skin = value);
        AddChoice(options, "Hair", ["Short", "Long", "Braid", "Crest", "Ponytail", "Bun"], 0, value => appearance.Hair = value);
        AddChoice(options, "Hair color", ["Dark brown", "Chestnut", "Golden brown", "Blond", "Auburn", "Black", "Silver", "Plum"], 0, value => appearance.HairColor = value);
        var rotate = Ui.Row(column); rotate.AddChild(Ui.Button("View left", () => avatar.Direction = (avatar.Direction + 3) % 4)); rotate.AddChild(Ui.Button("View right", () => avatar.Direction = (avatar.Direction + 1) % 4));
        void RefreshClass()
        {
            var selected = Data.Classes[cls.Selected]; description.Text = selected.Passive + "\nAll professions remain trainable. Class affinity improves selected skills."; avatar.Equipment = StarterEquipment(selected);
        }
        cls.ItemSelected += _ => RefreshClass(); RefreshClass();
        var status = Ui.Label("", 14, Ui.Danger, true); column.AddChild(status);
        var buttons = Ui.Row(column);
        buttons.AddChild(Ui.Button("Begin at Wayfarer's Rest", async () =>
        {
            if (Connection is null || authenticationBusy) return;
            authenticationBusy = true;
            try
            {
                var created = await Connection.CreateCharacterAsync(new CharacterRequest { Name = name.Text.Trim(), Class = Data.Classes[cls.Selected].Id, Appearance = appearance }, lifetime.Token);
                authenticationBusy = false; EnterWorld(created.Id);
            }
            catch (Exception error) { status.Text = error.Message; authenticationBusy = false; }
        }));
        buttons.AddChild(Ui.Button("Back", () => _ = ShowCharactersAsync()));
    }

    private OptionButton AddChoice(Node parent, string label, string[] values, int selected, Action<int> changed)
    {
        var row = Ui.Row(parent); var title = Ui.Label(label, 14, Ui.Muted); title.CustomMinimumSize = new Vector2(85, 0); row.AddChild(title);
        var choice = new OptionButton { SizeFlagsHorizontal = SizeFlags.ExpandFill, CustomMinimumSize = new Vector2(140, 30) };
        foreach (var value in values) choice.AddItem(value);
        choice.Selected = Math.Clamp(selected, 0, Math.Max(0, values.Length - 1)); choice.ItemSelected += index => changed((int)index); row.AddChild(choice); return choice;
    }

    private void BuildHud()
    {
        hud = new Control { MouseFilter = MouseFilterEnum.Ignore }; interfaceRoot.AddChild(hud); hud.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect); interfaceRoot.MoveChild(hud, 0);
        var stats = new PanelContainer { Position = new Vector2(18, 18), CustomMinimumSize = new Vector2(300, 0) }; hud.AddChild(stats);
        var column = Ui.Column(stats); characterTitle = Ui.Label("", 18, Ui.Gold); column.AddChild(characterTitle);
        healthText = Ui.Label("", 13); column.AddChild(healthText); health = Ui.Bar(new Color("a65759"), 270); column.AddChild(health);
        manaText = Ui.Label("", 13); column.AddChild(manaText); mana = Ui.Bar(new Color("5b87a8"), 270); column.AddChild(mana);
        staminaText = Ui.Label("", 13); column.AddChild(staminaText); stamina = Ui.Bar(new Color("94a86e"), 270); column.AddChild(stamina);
        var titlePanel = new VBoxContainer { AnchorLeft = .5f, AnchorRight = .5f, OffsetLeft = -280, OffsetRight = 280, OffsetTop = 23, MouseFilter = MouseFilterEnum.Ignore }; hud.AddChild(titlePanel);
        location = Ui.Label("", 23, Ui.Gold); location.HorizontalAlignment = HorizontalAlignment.Center; titlePanel.AddChild(location);
        targetText = Ui.Label("", 15, Ui.Text); targetText.HorizontalAlignment = HorizontalAlignment.Center; titlePanel.AddChild(targetText);
        connectionText = Ui.Label("", 14, Ui.Danger); connectionText.HorizontalAlignment = HorizontalAlignment.Center; titlePanel.AddChild(connectionText);
        var minimapPanel = new PanelContainer { AnchorLeft = 1, AnchorRight = 1, OffsetLeft = -234, OffsetRight = -18, OffsetTop = 18, OffsetBottom = 246 }; hud.AddChild(minimapPanel);
        var miniColumn = Ui.Column(minimapPanel); miniColumn.AddChild(new MinimapView { World = World, Data = Data, CustomMinimumSize = new Vector2(184, 166) }); miniColumn.AddChild(Ui.Button("World map  [M]", () => OpenPage("Map")));
        var bottom = new PanelContainer { AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1, OffsetLeft = -355, OffsetRight = 355, OffsetTop = -89, OffsetBottom = -18 }; hud.AddChild(bottom);
        var bar = Ui.Row(bottom);
        for (int i = 0; i < hotbar.Length; i++)
        {
            int slot = i; var button = Ui.Button((i == 9 ? 0 : i + 1).ToString(), () => UseHotbar(slot)); button.CustomMinimumSize = new Vector2(58, 44); button.ExpandIcon = true; button.AddThemeConstantOverride("icon_max_width", 28); button.SizeFlagsHorizontal = SizeFlags.ExpandFill; hotbarButtons[i] = button; bar.AddChild(button);
        }
        var chatPanel = new PanelContainer { AnchorTop = 1, AnchorBottom = 1, OffsetLeft = 18, OffsetRight = 352, OffsetTop = -247, OffsetBottom = -18 }; hud.AddChild(chatPanel);
        var chat = Ui.Column(chatPanel); chatLog = new RichTextLabel { BbcodeEnabled = false, ScrollFollowing = true, CustomMinimumSize = new Vector2(295, 135), SizeFlagsVertical = SizeFlags.ExpandFill }; chatLog.AddThemeFontSizeOverride("normal_font_size", 13); chat.AddChild(chatLog);
        var sendRow = Ui.Row(chat); chatChannel = new OptionButton(); foreach (string channel in new[] { "local", "global", "party", "guild", "whisper" }) chatChannel.AddItem(channel); sendRow.AddChild(chatChannel);
        chatInput = Ui.Edit("Enter to chat"); chatInput.MaxLength = 300; sendRow.AddChild(chatInput);
        chatInput.TextSubmitted += text =>
        {
            if (text.Trim() != "") Send("chat", chatChannel.GetItemText(chatChannel.Selected), selectedTargetKind == "player" ? selectedTarget : "", arg: text.Trim());
            chatInput.Text = ""; chatInput.ReleaseFocus();
        };
        var menu = new PanelContainer { AnchorLeft = 1, AnchorRight = 1, AnchorTop = 1, AnchorBottom = 1, OffsetLeft = -300, OffsetRight = -18, OffsetTop = -229, OffsetBottom = -18 }; hud.AddChild(menu);
        var grid = new GridContainer { Columns = 2 }; menu.AddChild(grid);
        foreach (string entry in new[] { "Inventory", "Character", "Skills", "Abilities", "Quests", "Crafting", "Social", "Settings" }) grid.AddChild(Ui.Button(entry, () => OpenPage(entry)));
        notice = Ui.Label("", 16, Ui.Text, true); notice.AnchorLeft = .5f; notice.AnchorRight = .5f; notice.AnchorTop = 1; notice.AnchorBottom = 1; notice.OffsetLeft = -360; notice.OffsetRight = 360; notice.OffsetTop = -153; notice.OffsetBottom = -98; notice.HorizontalAlignment = HorizontalAlignment.Center; notice.AddThemeConstantOverride("outline_size", 5); notice.AddThemeColorOverride("font_outline_color", Ui.Ink); hud.AddChild(notice);
        deathPanel = new PanelContainer { AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = .5f, AnchorBottom = .5f, OffsetLeft = -240, OffsetRight = 240, OffsetTop = -90, OffsetBottom = 100, Visible = false }; hud.AddChild(deathPanel);
        var death = Ui.Column(deathPanel); death.AddChild(Ui.Label("Your journey continues", 24, Ui.Gold)); deathText = Ui.Label("", 16, Ui.Text, true); death.AddChild(deathText); respawnButton = Ui.Button("Return to safety", () => Send("respawn")); death.AddChild(respawnButton);
    }

    private void UpdateHud()
    {
        if (hud is null) return;
        hud.Visible = Snapshot is not null;
        if (Snapshot is not { } snap) return;
        var self = snap.Self; var stats = CombatMath.Stats(self, Data);
        characterTitle.Text = self.Name + "  ·  " + Progression.PlayerLevel(self) + "  ·  " + self.Gold + " gold";
        health.MaxValue = stats.Health; health.Value = self.Health; healthText.Text = $"Health  {Math.Ceiling(self.Health):0} / {stats.Health:0}";
        mana.MaxValue = stats.Mana; mana.Value = self.Mana; manaText.Text = $"Mana  {Math.Ceiling(self.Mana):0} / {stats.Mana:0}";
        stamina.MaxValue = stats.Stamina; stamina.Value = self.Stamina; staminaText.Text = $"Stamina  {Math.Ceiling(self.Stamina):0} / {stats.Stamina:0}";
        var zone = Data.Zone(self.Zone); location.Text = zone.Name + "  ·  " + zone.Layer;
        var target = snap.Creatures.FirstOrDefault(x => x.Id == selectedTarget && x.Health > 0);
        targetText.Text = target is null ? WorldTime.Weather(zone, snap.Time) + "  ·  " + (autoAttack ? "Auto-attack" : "E: interact") : Data.Mob(target.Template).Name + "  ·  " + Math.Ceiling(target.Health) + " health";
        connectionText.Text = Connection?.Connected == true ? "" : "Disconnected. Open Settings to reconnect or sign in again.";
        deathPanel.Visible = self.Health <= 0;
        if (deathPanel.Visible) { deathText.Text = "Your equipment remains yours. Repair damaged equipment after returning to a settlement.\nRespawn in " + Math.Max(0, Math.Ceiling(self.DeadUntil - snap.Time)) + " seconds."; respawnButton.Disabled = self.DeadUntil > snap.Time; }
        for (int i = 0; i < hotbar.Length; i++)
        {
            string id = hotbar[i]; var button = hotbarButtons[i];
            if (string.IsNullOrEmpty(id)) { button.Icon = null; button.Text = (i == 9 ? 0 : i + 1) + "\n—"; button.TooltipText = "Assign an ability from the Abilities window."; continue; }
            var ability = Data.Ability(id); double cooldown = self.Cooldowns.GetValueOrDefault(id) - snap.Time;
            button.Icon = Assets.AbilityIcon(id); button.Text = (i == 9 ? 0 : i + 1).ToString() + (cooldown > 0 ? "\n" + Math.Ceiling(cooldown) : "");
            button.TooltipText = ability.Name + "\n" + ability.Description + $"\nMana {ability.Mana} · Stamina {ability.Stamina} · Cooldown {ability.Cooldown}s";
            button.Disabled = cooldown > 0 || self.Health <= 0;
        }
    }
}
