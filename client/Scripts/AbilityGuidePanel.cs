using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Stable ability browser. Selection never rebuilds the pressed control.</summary>
public partial class AbilityGuidePanel : VBoxContainer
{
    public Catalog Data { get; set; } = null!;
    public PixelAssets Assets { get; set; } = null!;
    public Func<Character?> ReadCharacter { get; set; } = () => null;
    public Func<double> ReadTime { get; set; } = () => 0;
    public Func<IReadOnlyList<string>> ReadHotbar { get; set; } = () => Array.Empty<string>();
    public Action<string, int>? AssignToHotbar { get; set; }
    public string SelectedAbility { get; private set; } = "";
    public IReadOnlyList<string> VisibleAbilityIds => visible.AsReadOnly();
    private readonly List<string> visible = [];
    private readonly Dictionary<string, Button> choices = [];
    private LineEdit search = null!;
    private OptionButton scope = null!, availability = null!, element = null!, hotbarSlot = null!;
    private VBoxContainer rows = null!;
    private Label resultCount = null!, title = null!, classification = null!, description = null!, numbers = null!, effect = null!, requirement = null!, readiness = null!, assigned = null!;
    private TextureRect icon = null!;
    private Button assign = null!;
    private string signature = "";

    public override void _Ready()
    {
        Name = "AbilityGuide";
        SizeFlagsHorizontal = SizeFlags.ExpandFill; SizeFlagsVertical = SizeFlags.ExpandFill;
        var filters = Ui.Row(this);
        search = Ui.Edit("Find an ability, skill, or effect"); search.Name = "AbilitySearch"; filters.AddChild(search);
        scope = new OptionButton { Name = "AbilityScope" };
        foreach (string text in new[] { "My class + shared", "Equipped weapon", "Magic", "All classes" }) scope.AddItem(text);
        filters.AddChild(scope);
        availability = new OptionButton { Name = "AbilityAvailability" };
        foreach (string text in new[] { "All levels", "Unlocked", "Locked" }) availability.AddItem(text);
        availability.Select(1); filters.AddChild(availability);
        element = new OptionButton { Name = "AbilityElement" }; element.AddItem("All elements");
        foreach (string text in Enum.GetNames<Element>()) element.AddItem(text);
        filters.AddChild(element);
        resultCount = Ui.Label("", 13, Ui.Muted, true); AddChild(resultCount);
        var body = Ui.Row(this); body.SizeFlagsVertical = SizeFlags.ExpandFill;
        var list = Ui.Scroll(body, new Vector2(280, 120)); list.Name = "AbilityList";
        list.SizeFlagsStretchRatio = 1; rows = Ui.Column(list);
        var detail = new PanelContainer { Name = "AbilityDetails", SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill, SizeFlagsStretchRatio = 1.35f };
        body.AddChild(detail);
        var detailColumn = Ui.Column(detail, true);
        var header = Ui.Row(detailColumn); icon = Ui.Image(null, 56); header.AddChild(icon);
        var names = Ui.Column(header); title = Ui.Label("Choose an ability", 21, Ui.Gold, true); names.AddChild(title);
        classification = Ui.Label("", 13, Ui.Muted, true); names.AddChild(classification);
        var scroll = Ui.Scroll(detailColumn, new Vector2(0, 80));
        var information = Ui.Column(scroll);
        description = Ui.Label("", 16, Ui.Text, true); information.AddChild(description);
        numbers = Ui.Label("", 14, Ui.Gold, true); numbers.Name = "AbilityCosts"; information.AddChild(numbers);
        effect = Ui.Label("", 14, Ui.Text, true); effect.Name = "AbilityEffect"; information.AddChild(effect);
        requirement = Ui.Label("", 14, Ui.Muted, true); requirement.Name = "AbilityRequirement"; information.AddChild(requirement);
        readiness = Ui.Label("", 14, Ui.Danger, true); readiness.Name = "AbilityReadiness"; information.AddChild(readiness);
        // The assignment controls stay outside the scrolling information area.
        assigned = Ui.Label("", 13, Ui.Success, true); assigned.Name = "AbilityAssignedSlots"; detailColumn.AddChild(assigned);
        var actions = Ui.Row(detailColumn);
        hotbarSlot = new OptionButton { Name = "AbilityHotbarSlot" };
        for (int i = 0; i < 10; i++) hotbarSlot.AddItem("Key " + (i == 9 ? "0" : (i + 1).ToString()));
        actions.AddChild(hotbarSlot);
        assign = Ui.Button("Assign to hotbar", () => TryAssignSelected()); assign.Name = "AssignAbility";
        assign.SizeFlagsHorizontal = SizeFlags.ExpandFill; actions.AddChild(assign);
        search.TextChanged += SearchChanged;
        scope.ItemSelected += FilterChanged; availability.ItemSelected += FilterChanged; element.ItemSelected += FilterChanged;
        RefreshSnapshot();
    }

    public override void _ExitTree()
    {
        if (search is null) return;
        search.TextChanged -= SearchChanged;
        scope.ItemSelected -= FilterChanged; availability.ItemSelected -= FilterChanged; element.ItemSelected -= FilterChanged;
    }
    private void SearchChanged(string _) { signature = ""; RefreshSnapshot(); }
    private void FilterChanged(long _) { signature = ""; RefreshSnapshot(); }
    private string WeaponSkill(Character self)
    {
        var item = self.Equipment.TryGetValue("weapon", out var id) ? self.Inventory.FirstOrDefault(x => x.Id == id) : null;
        return item is null ? "unarmed_combat" : Data.Item(item.Template).Skill;
    }
    private bool Includes(AbilityDef ability, Character self)
    {
        if (scope.Selected == 0 && ability.Class != "" && ability.Class != self.Class) return false;
        if (scope.Selected == 1 && ability.Skill != WeaponSkill(self)) return false;
        if (scope.Selected == 2 && ability.Element == Element.Physical) return false;
        bool learned = Progression.Level(self, ability.Skill) >= ExperienceRules.AbilityRequirement(self, ability);
        if (availability.Selected == 1 && !learned || availability.Selected == 2 && learned) return false;
        if (element.Selected > 0 && ability.Element.ToString() != element.GetItemText(element.Selected)) return false;
        string text = ability.Name + " " + Data.Skill(ability.Skill).Name + " " + ability.Description + " " + ability.Status;
        return text.Contains(search.Text.Trim(), StringComparison.OrdinalIgnoreCase);
    }
    public void RefreshSnapshot()
    {
        if (search is null || !IsInsideTree()) return;
        var self = ReadCharacter();
        if (self is null) { assign.Disabled = true; return; }
        // Mana, cooldowns, and XP within a level do not destroy the list or its scroll position.
        string next = self.Id + ":" + self.Class + ":" + WeaponSkill(self) + ":"
            + string.Join(",", Data.Skills.Select(x => Progression.Level(self, x.Id))) + ":"
            + search.Text + ":" + scope.Selected + ":" + availability.Selected + ":" + element.Selected;
        if (next != signature)
        {
            signature = next; Ui.Clear(rows); choices.Clear(); visible.Clear();
            foreach (var ability in Data.Abilities.Where(x => Includes(x, self))
                .OrderByDescending(x => x.Class == self.Class).ThenBy(x => ExperienceRules.AbilityRequirement(self, x))
                .ThenBy(x => x.Name, StringComparer.Ordinal))
            {
                string id = ability.Id;
                var button = Ui.Button("", () => SelectAbility(id));
                button.Name = "AbilityChoice_" + id; button.Icon = Assets.AbilityIcon(id); button.ExpandIcon = true;
                button.AddThemeConstantOverride("icon_max_width", 32); button.Alignment = HorizontalAlignment.Left;
                button.CustomMinimumSize = new Vector2(0, 58); button.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis; button.ClipText = true;
                button.Text = ability.Name + "\n" + Data.Skill(ability.Skill).Name + " " + ExperienceRules.AbilityRequirement(self, ability);
                button.TooltipText = ability.Name + "\n" + ability.Description;
                rows.AddChild(button); choices.Add(id, button); visible.Add(id);
            }
            if (!visible.Contains(SelectedAbility)) SelectedAbility = visible.FirstOrDefault() ?? "";
            resultCount.Text = visible.Count + " abilities shown. Select one to inspect its effect and assign a key.";
            if (visible.Count == 0) rows.AddChild(Ui.Label("No abilities match. Change the filters or clear the search.", 15, Ui.Muted, true));
        }
        RefreshDetails(self);
    }
    public void SelectAbility(string id)
    {
        if (!visible.Contains(id) || ReadCharacter() is not { } self) return;
        SelectedAbility = id; RefreshDetails(self);
    }
    private void RefreshDetails(Character self)
    {
        foreach (var entry in choices)
            entry.Value.AddThemeStyleboxOverride("normal", Ui.Box(entry.Key == SelectedAbility ? Ui.Raised.Lightened(.12f) : Ui.Ink,
                entry.Key == SelectedAbility ? Ui.Gold : new Color("665941"), 8));
        var ability = Data.Abilities.FirstOrDefault(x => x.Id == SelectedAbility);
        assign.Disabled = ability is null;
        if (ability is null)
        {
            icon.Texture = null; title.Text = "No ability selected";
            classification.Text = description.Text = numbers.Text = effect.Text = requirement.Text = readiness.Text = assigned.Text = "";
            return;
        }
        icon.Texture = Assets.AbilityIcon(ability.Id); title.Text = ability.Name;
        classification.Text = Ui.Words(ability.Kind) + " · " + ability.Element + " · " + (ability.Class == "" ? "Shared" : Data.Class(ability.Class).Name);
        description.Text = ability.Description;
        var stats = CombatMath.Stats(self, Data);
        numbers.Text = $"Mana {ability.Mana:0.#}   Stamina {ability.Stamina:0.#}\nCooldown {ability.Cooldown * (1 - stats.CooldownReduction):0.##} s   Range {ability.Range:0.#} tiles"
            + (ability.Radius > 0 ? $"\nEffect radius {ability.Radius:0.#} tiles" : "");
        effect.Text = AbilityGuideText.Effect(ability);
        int level = Progression.Level(self, ability.Skill), needed = ExperienceRules.AbilityRequirement(self, ability);
        requirement.Text = $"Requires {Data.Skill(ability.Skill).Name} {needed}. Your level: {level}."
            + (ability.Class != "" && ability.Class != self.Class ? "\nCross-class learning adds 20 skill levels." : "");
        assign.Disabled = level < needed || AssignToHotbar is null;
        string problem = ExperienceRules.AbilityProblem(self, ability, Data, ReadTime());
        readiness.Text = problem;
        var bar = ReadHotbar();
        var keys = Enumerable.Range(0, Math.Min(10, bar.Count)).Where(i => bar[i] == ability.Id).Select(i => i == 9 ? "0" : (i + 1).ToString());
        string existing = string.Join(", ", keys);
        assigned.Text = existing == "" ? "Choose a key below. Use that key after closing this window." : "Assigned to key " + existing + ".";
    }
    public bool TryAssignSelected()
    {
        if (!IsInsideTree() || ReadCharacter() is not { } self || AssignToHotbar is null) return false;
        var ability = Data.Abilities.FirstOrDefault(x => x.Id == SelectedAbility);
        if (ability is null || Progression.Level(self, ability.Skill) < ExperienceRules.AbilityRequirement(self, ability)) return false;
        if (hotbarSlot.Selected is < 0 or >= 10) return false;
        AssignToHotbar(ability.Id, hotbarSlot.Selected); RefreshDetails(self); return true;
    }
}

public static class AbilityGuideText
{
    // These descriptions follow RealmCombat.Cast, not inferred names or unused metadata.
    public static string Effect(AbilityDef a)
    {
        string text = a.Kind switch
        {
            "strike" or "dot" => "Select a living hostile creature. The hit resolves immediately within range.",
            "drain" => "Hit one hostile creature and recover health equal to 25% of damage dealt.",
            "projectile" => "Select a hostile creature. The projectile resolves at its target position after travel time.",
            "area" => "Aim at a position. Damage resolves in a circle after 0.35 seconds.",
            "cone" => "Aim forward. Damage resolves in a forward cone after 0.35 seconds.",
            "line" => "Aim forward. Damage resolves along a narrow line after 0.35 seconds.",
            "field" => "Aim at a position. An initial hit is followed by up to five weaker damage pulses.",
            "dash" => "Aim at a clear position. Move there and strike creatures near the destination. Walls block the move.",
            "heal" => "Heal yourself or an injured party member. This ability cannot resurrect a dead character.",
            "shield" => "Apply an absorption shield to yourself.",
            "buff" => "Apply " + Ui.Words(a.Status == "" ? "empower" : a.Status) + " to yourself.",
            "stealth" => "Apply stealth to yourself. Offensive actions end stealth.",
            "purge" => "Remove poison, burning, curses, and roots from yourself.",
            "taunt" => "Draw nearby hostile creatures toward you and gain a temporary guard effect.",
            "interrupt" => "Cancel a hostile creature's pending attacks, delay its next attack, and deal a hit.",
            "summon" => "Call one animal companion allowed by your Summoning level. Only one companion can be active.",
            _ => "This action needs an implementation review."
        };
        if (a.Kind is "strike" or "dot" or "drain" && a.Status != "") text += $"\nHit effect: {Ui.Words(a.Status)} for {a.Duration:0.#} s.";
        else if (a.Kind is "shield" or "buff" or "stealth" or "taunt") text += $"\nDuration: {a.Duration:0.#} s.";
        if (a.Kind == "heal" && a.Duration > 0) text += $"\nAlso applies regeneration for {a.Duration:0.#} s.";
        return text;
    }
}
