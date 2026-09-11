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
            while (read++ < 150 && Connection.TryRead(out var packet)) if (packet?.Snapshot is not null)
            {
                World.Accept(packet); invitations = packet.Invitations ?? []; friendInvitations = packet.FriendInvitations ?? [];
                lfgListings = packet.Lfg ?? []; socialProfiles = packet.SocialProfiles ?? [];
            }
            frontend.Visible = false; SetInitialHotbar(); ClosePage();
            Notify("Move: WASD or arrows. Interact: E. Hold Space to attack. Use your first class ability with 1.");
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

}
