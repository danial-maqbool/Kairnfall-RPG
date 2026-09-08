using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Presentation categories and unlocks derived from the existing catalog.</summary>
public static class SkillGuideRules
{
    public static readonly string[] Categories = ["Combat", "Magic", "Defense", "Gathering", "Crafting", "Utility"];
    public sealed record Unlock(string Kind, string Id, string Name, int Level);

    public static string Group(SkillDef skill)
    {
        if (skill.Id is "shield_mastery" or "light_armor" or "medium_armor" or "heavy_armor" or "evasion" or "endurance") return "Defense";
        if (skill.Id is "hunting" or "slayer") return "Combat";
        if (skill.Id == "meditation") return "Magic";
        return skill.Category switch
        {
            "Weapons" => "Combat", "Magic" => "Magic", "Gathering" => "Gathering",
            "Crafting" => "Crafting", _ => "Utility"
        };
    }

    public static IReadOnlyList<SkillDef> Filter(Catalog data, string category, string query)
    {
        string text = query.Trim();
        return data.Skills.Where(skill => (category == "All" || Group(skill) == category)
                && (skill.Name + " " + skill.Action + " " + skill.Benefit).Contains(text, StringComparison.OrdinalIgnoreCase))
            .OrderBy(skill => skill.Name, StringComparer.Ordinal).ToArray();
    }

    public static IReadOnlyList<Unlock> FutureUnlocks(Catalog data, Character self, string skillId)
    {
        int current = Progression.Level(self, skillId);
        var items = data.Items.Where(item => item.Skill == skillId && item.Slot != "")
            .Select(item => new Unlock("Equipment", item.Id, item.Name, BeginnerProgression.EquipmentRequirement(item)));
        var recipes = data.Recipes.Where(recipe => recipe.Skill == skillId)
            .Select(recipe => new Unlock("Recipe", recipe.Id, recipe.Name, recipe.Requirement));
        var abilities = data.Abilities.Where(ability => ability.Skill == skillId)
            .Select(ability => new Unlock("Ability", ability.Id, ability.Name,
                ability.Requirement + (ability.Class != "" && ability.Class != self.Class ? 20 : 0)));
        return items.Concat(recipes).Concat(abilities)
            .Where(unlock => unlock.Level > current && unlock.Level <= 100)
            .DistinctBy(unlock => (unlock.Kind, unlock.Id))
            .OrderBy(unlock => unlock.Level).ThenBy(unlock => unlock.Kind, StringComparer.Ordinal)
            .ThenBy(unlock => unlock.Name, StringComparer.Ordinal).ToArray();
    }
}

/// <summary>Stable skill navigation. Snapshot updates do not rebuild the scroll list.</summary>
public partial class SkillGuidePanel : VBoxContainer
{
    public Catalog Data { get; set; } = null!;
    public PixelAssets Assets { get; set; } = null!;
    public Func<Character?> ReadCharacter { get; set; } = static () => null;
    public string ActiveCategory { get; private set; } = "All";
    public string SelectedSkillId { get; private set; } = "";
    public int VisibleSkillCount => skillButtons.Count;
    public LineEdit SearchBox { get; private set; } = null!;
    private readonly Dictionary<string, Button> skillButtons = [];
    private readonly Dictionary<string, Button> categoryButtons = [];
    private readonly Dictionary<string, long> seenXp = [];
    private VBoxContainer listing = null!, details = null!;
    private Label summary = null!;
    private ScrollContainer listScroll = null!;
    private string characterId = "";
    private bool prepared;

    public override void _Ready()
    {
        Name = "SkillGuide";
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        SizeFlagsVertical = SizeFlags.ExpandFill;
        AddChild(Ui.Label("Train a skill by using it. All skill XP contributes to your overall level.", 15, Ui.Muted, true));
        var filters = new HFlowContainer { Name = "SkillCategories", SizeFlagsHorizontal = SizeFlags.ExpandFill };
        AddChild(filters);
        foreach (string category in new[] { "All" }.Concat(SkillGuideRules.Categories))
        {
            var button = Ui.Button(category, () => SelectCategory(category));
            button.Name = "SkillCategory_" + category;
            button.CustomMinimumSize = new Vector2(100, 38);
            button.ToggleMode = true;
            categoryButtons.Add(category, button);
            filters.AddChild(button);
        }
        SearchBox = Ui.Edit("Find a skill, training action, or benefit");
        SearchBox.Name = "SkillSearch";
        AddChild(SearchBox);
        SearchBox.TextChanged += SearchChanged;
        summary = Ui.Label("", 13, Ui.Muted);
        summary.Name = "SkillCount";
        AddChild(summary);
        var body = Ui.Row(this);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        listScroll = Ui.Scroll(body, new Vector2(280, 330));
        listScroll.SizeFlagsHorizontal = SizeFlags.Fill;
        listing = Ui.Column(listScroll);
        var detailScroll = Ui.Scroll(body, new Vector2(340, 330));
        details = Ui.Column(detailScroll);
        details.Name = "SkillDetails";
        prepared = true;
        RebuildListing();
    }

    public void SelectCategory(string category)
    {
        if (category != "All" && !SkillGuideRules.Categories.Contains(category, StringComparer.Ordinal))
            throw new ArgumentException("Unknown skill category.", nameof(category));
        ActiveCategory = category;
        if (prepared) RebuildListing();
    }

    private void SearchChanged(string _) => RebuildListing();

    private void RebuildListing()
    {
        if (!prepared) return;
        Ui.Clear(listing);
        skillButtons.Clear();
        var visible = SkillGuideRules.Filter(Data, ActiveCategory, SearchBox.Text);
        if (!visible.Any(skill => skill.Id == SelectedSkillId))
            SelectedSkillId = visible.FirstOrDefault()?.Id ?? "";
        foreach (var skill in visible)
        {
            string id = skill.Id;
            var button = Ui.Button(skill.Name, () => SelectSkill(id));
            button.Name = "SkillEntry_" + id;
            button.Icon = Assets.Texture("skills/" + id);
            button.ExpandIcon = true;
            button.AddThemeConstantOverride("icon_max_width", 26);
            button.CustomMinimumSize = new Vector2(258, 44);
            button.Alignment = HorizontalAlignment.Left;
            button.ToggleMode = true;
            button.TooltipText = skill.Action;
            listing.AddChild(button);
            skillButtons.Add(id, button);
        }
        if (visible.Count == 0)
            listing.AddChild(Ui.Label("No matching skills. Clear the search or select All.", 15, Ui.Muted, true));
        foreach (var (category, button) in categoryButtons)
            button.SetPressedNoSignal(category == ActiveCategory);
        listScroll.ScrollVertical = 0;
        RefreshSnapshot(forceDetails: true);
    }

    private void SelectSkill(string id)
    {
        if (!skillButtons.ContainsKey(id)) return;
        SelectedSkillId = id;
        RefreshSnapshot(forceDetails: true);
    }

    public void RefreshSnapshot() => RefreshSnapshot(forceDetails: false);

    private void RefreshSnapshot(bool forceDetails)
    {
        if (!prepared || ReadCharacter() is not { } self) return;
        bool changed = characterId != self.Id || Data.Skills.Any(skill =>
            !seenXp.TryGetValue(skill.Id, out long previous) || previous != self.SkillXp.GetValueOrDefault(skill.Id));
        characterId = self.Id;
        summary.Text = $"{VisibleSkillCount} of {Data.Skills.Count} skills  ·  Overall level {Progression.PlayerLevel(self)}  ·  Total XP {Progression.Total(self):N0}";
        var affinity = Data.Class(self.Class).Affinity;
        foreach (var (id, button) in skillButtons)
        {
            button.Text = Data.Skill(id).Name + "  ·  " + Progression.Level(self, id)
                + (affinity.Contains(id, StringComparer.Ordinal) ? "  +" : "");
            button.SetPressedNoSignal(id == SelectedSkillId);
        }
        foreach (var skill in Data.Skills) seenXp[skill.Id] = self.SkillXp.GetValueOrDefault(skill.Id);
        if (changed || forceDetails) RenderDetails(self);
    }

    private void RenderDetails(Character self)
    {
        Ui.Clear(details);
        var skill = Data.Skills.FirstOrDefault(value => value.Id == SelectedSkillId);
        if (skill is null)
        {
            details.AddChild(Ui.Label("Choose a skill", 23, Ui.Gold));
            details.AddChild(Ui.Label("Select a category or clear your search to browse the skill guide.", 16, Ui.Muted, true));
            return;
        }
        int level = Progression.Level(self, skill.Id);
        long xp = self.SkillXp.GetValueOrDefault(skill.Id);
        var heading = Ui.Row(details);
        heading.AddChild(Ui.Image(Assets.Texture("skills/" + skill.Id), 48));
        var names = Ui.Column(heading);
        names.AddChild(Ui.Label(skill.Name, 24, Ui.Gold, true));
        names.AddChild(Ui.Label(SkillGuideRules.Group(skill) + "  ·  Level " + level + "/100", 14, Ui.Muted));
        if (Data.Class(self.Class).Affinity.Contains(skill.Id, StringComparer.Ordinal))
            details.AddChild(Ui.Label("Class affinity: +10% training XP", 14, Ui.Success, true));
        long start = Progression.Threshold(level);
        long needed = level >= 100 ? 1 : Progression.Threshold(level + 1) - start;
        var bar = Ui.Bar(Ui.Success, 260);
        bar.Name = "SelectedSkillProgress";
        bar.MaxValue = needed;
        bar.Value = level >= 100 ? 1 : Math.Clamp(xp - start, 0, needed);
        bar.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        details.AddChild(bar);
        details.AddChild(Ui.Label(level >= 100 ? "Mastered" : $"{Math.Clamp(xp - start, 0, needed):N0} / {needed:N0} XP to level {level + 1}", 14, Ui.Text, true));
        details.AddChild(Ui.Label("HOW TO TRAIN", 14, Ui.Gold));
        var training = Ui.Label(skill.Action, 17, Ui.Text, true);
        training.Name = "SkillTrainingAction";
        details.AddChild(training);
        details.AddChild(Ui.Label("BENEFIT", 14, Ui.Gold));
        details.AddChild(Ui.Label(skill.Benefit, 16, Ui.Text, true));
        details.AddChild(new HSeparator());
        details.AddChild(Ui.Label("NEXT CATALOG UNLOCKS", 14, Ui.Gold));
        var unlocks = SkillGuideRules.FutureUnlocks(Data, self, skill.Id);
        if (unlocks.Count == 0)
            details.AddChild(Ui.Label(level >= 100 ? "Maximum skill level reached." : "No later equipment, recipe, or ability unlock is listed for this skill.", 15, Ui.Muted, true));
        foreach (var unlock in unlocks.Take(5))
            details.AddChild(Ui.Label($"Level {unlock.Level} · {unlock.Name}\n{unlock.Kind}", 15, Ui.Text, true));
        if (unlocks.Count > 5)
            details.AddChild(Ui.Label($"{unlocks.Count - 5} later unlocks. Recipes and abilities show their full requirements in their own windows.", 13, Ui.Muted, true));
    }

    public override void _ExitTree()
    {
        if (SearchBox is not null && GodotObject.IsInstanceValid(SearchBox)) SearchBox.TextChanged -= SearchChanged;
        prepared = false;
        ReadCharacter = static () => null;
        skillButtons.Clear(); categoryButtons.Clear(); seenXp.Clear();
    }
}
