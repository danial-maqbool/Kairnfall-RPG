using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>One process in a two-process graphical multiplayer contract. Human multiplayer review remains separate.</summary>
public partial class LiveMultiplayerPresenceContract : Node
{
    private GameRoot game=null!;
    private int checks;
    private static double Now=>Time.GetTicksMsec()/1000.0;
    private static T Field<T>(GameRoot value,string name)=> (T)typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(value)!;
    private static void Attach(GameRoot value,GameConnection connection)=>typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(value,connection);
    private Character Self=>game.Snapshot?.Self??throw new InvalidOperationException("No authoritative snapshot.");
    private void Require(bool value,string message)
    {
        if(!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS GRAPHICAL MULTIPLAYER: "+message);
    }
    private async Task Frame()=>await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
    private async Task Delay(double seconds)=>await ToSignal(GetTree().CreateTimer(seconds),SceneTreeTimer.SignalName.Timeout);
    private async Task Until(Func<bool> condition,string failure,double timeout=15)
    {
        double deadline=Now+timeout;
        while(!condition()) { if(Now>=deadline) throw new TimeoutException(failure); await Frame(); }
    }
    private void KeyEvent(Key key,bool pressed)
    {
        using var input=new InputEventKey{PhysicalKeycode=key,Keycode=key,Pressed=pressed};
        Input.ParseInputEvent(input); Input.FlushBufferedEvents();
    }

    public override async void _Ready()
    {
        GameConnection? connection=null;
        try
        {
            if(DisplayServer.GetName()=="headless") throw new InvalidOperationException("This contract requires graphical rendering.");
            if(System.Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")!="Testing") throw new InvalidOperationException("Use the disposable Testing realm.");
            string address=System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL")??"http://127.0.0.1:5079";
            if(!Uri.TryCreate(address,UriKind.Absolute,out var uri)||!uri.IsLoopback) throw new InvalidOperationException("Graphical multiplayer QA must use a loopback realm.");
            string role=System.Environment.GetEnvironmentVariable("KAIRNFALL_GRAPHICAL_ROLE")??throw new InvalidOperationException("Set KAIRNFALL_GRAPHICAL_ROLE.");
            string peerRole=System.Environment.GetEnvironmentVariable("KAIRNFALL_GRAPHICAL_PEER_ROLE")??throw new InvalidOperationException("Set KAIRNFALL_GRAPHICAL_PEER_ROLE.");
            string suffix=Guid.NewGuid().ToString("N")[..8];
            connection=new GameConnection(address);
            await connection.SignInAsync("graphical_"+role.ToLowerInvariant()+"_"+suffix,"QA_"+Guid.NewGuid().ToString("N"),true);
            var created=await connection.CreateCharacterAsync(new CharacterRequest{Name="Graphical "+role+" "+suffix,Class=role=="A"?"vanguard":"ranger",Appearance=new()});
            await connection.ConnectAsync(created.Id);
            using(var scene=GD.Load<PackedScene>("res://Main.tscn")) game=scene.Instantiate<GameRoot>();
            AddChild(game); Attach(game,connection); Field<Control>(game,"frontend").Hide(); GetViewport().GuiReleaseFocus();
            await Until(()=>game.Snapshot is not null,"The graphical client did not receive its first snapshot.");
            await Until(()=>game.Snapshot!.Players.Any(p=>p.Id!=Self.Id),"The second graphical client did not appear in the shared world.",25);
            var peer=game.Snapshot!.Players.First(p=>p.Id!=Self.Id); string peerId=peer.Id;
            Require(peer.Position.Distance(Self.Position)<50,"The same-region snapshot contains the second graphical client near the starting point");

            string ownMessage="GRAPHICAL_MULTI:"+role; string peerMessage="GRAPHICAL_MULTI:"+peerRole;
            var chat=await connection.ActAsync(new GameCommand{Kind="chat",Target="local",Arg=ownMessage});
            Require(chat.Ok,"The graphical client can send shared chat");
            await Until(()=>Field<List<string>>(game,"history").Any(line=>line.Contains(peerMessage,StringComparison.Ordinal)),"The peer graphical chat message did not arrive.",20);
            Require(true,"The second graphical client message reaches the rendered client");

            peer=game.Snapshot!.Players.First(p=>p.Id==peerId); var peerStart=peer.Position; var selfStart=Self.Position;
            Key move=role=="A"?Key.D:Key.A; KeyEvent(move,true); await Delay(2.0); KeyEvent(move,false); await Delay(.4);
            Require(Self.Position.Distance(selfStart)>1.5,"Physical keyboard input moves this graphical client through the server");
            await Until(()=>game.Snapshot!.Players.FirstOrDefault(p=>p.Id==peerId)?.Position.Distance(peerStart)>.5,"Peer movement did not synchronize into this graphical client.",15);
            Require(true,"Peer movement synchronizes into the rendered shared world");
            await Delay(1.0);
            GD.Print($"GRAPHICAL_MULTIPLAYER_CONTRACT: role {role}; {checks} checks passed; independent process peer observed. Protocol party/trade/loot/reconnect/restart checks run in the same CI gate. Human multiplayer approval is not inferred.");
            GetTree().Quit(0);
        }
        catch(Exception error)
        {
            GD.PushError(error.ToString()); GetTree().Quit(1);
        }
        finally
        {
            if(connection is not null) await connection.DisposeAsync();
        }
    }
}
