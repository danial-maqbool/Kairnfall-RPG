using Godot;
using System.Diagnostics;
using System.Runtime.ExceptionServices;

namespace Kairnfall.Client.Tests;

/// <summary>Test-scene diagnostics. Never reads password fields or session tokens.</summary>
public partial class RegistrationDiagnostics : Node
{
    private double elapsed;
    private string previous = "";
    private int traces;

    public override void _EnterTree() => AppDomain.CurrentDomain.FirstChanceException += TraceClosedConnection;
    public override void _ExitTree() => AppDomain.CurrentDomain.FirstChanceException -= TraceClosedConnection;

    private void TraceClosedConnection(object? sender, FirstChanceExceptionEventArgs args)
    {
        if (args.Exception.Message != "The connection is closed." || Interlocked.Increment(ref traces) > 8) return;
        // Method names locate the failing code. Do not log exception Data,
        // arguments, request objects, URLs, credentials, or exception messages.
        string methods = string.Join(" <- ", new StackTrace(args.Exception, false).GetFrames()
            .Select(frame => frame.GetMethod())
            .Where(method => method is not null)
            .Select(method => method!.DeclaringType?.FullName + "." + method.Name)
            .Take(20));
        Console.WriteLine("AUTH_CLOSED_TRACE type=" + args.Exception.GetType().FullName + "; methods=" + methods);
    }

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
