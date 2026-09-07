using Godot;

namespace Kairnfall.Client.Tests;

/// <summary>Test-scene diagnostics. Never reads password fields or session tokens.</summary>
public partial class RegistrationDiagnostics : Node
{
    private double elapsed;
    private string previous = "";
    private IEnumerable<T> Walk<T>(Node node) where T : Node
    {
        if (node is T value) yield return value;
        foreach (Node child in node.GetChildren())
            foreach (var nested in Walk<T>(child)) yield return nested;
    }
    public override void _Process(double delta)
    {
        elapsed += delta;
        if (elapsed < 2) return;
        elapsed = 0;
        var root = Walk<GameRoot>(GetParent()).FirstOrDefault();
        if (root is null) return;
        // Labels contain public interface text and error messages. Input fields
        // and private Connection.Session members are deliberately excluded.
        string labels = string.Join(" | ", Walk<Label>(root)
            .Where(label => label.IsVisibleInTree() && !string.IsNullOrWhiteSpace(label.Text))
            .Select(label => label.Text.Replace('\n', ' ')).Take(24));
        string buttons = string.Join(" | ", Walk<Button>(root)
            .Where(button => button.IsVisibleInTree())
            .Select(button => button.Text + (button.Disabled ? " [disabled]" : " [enabled]")).Take(12));
        string state = $"sessionPresent={root.Connection?.Session is not null}; connected={root.Connection?.Connected == true}; labels={labels}; buttons={buttons}";
        if (state == previous) return;
        previous = state;
        GD.Print("UI_DIAGNOSTIC " + state);
    }
}
