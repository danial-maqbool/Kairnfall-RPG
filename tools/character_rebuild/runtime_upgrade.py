"""Temporary exact-source runtime integration; the publishing workflow removes this module."""
from pathlib import Path
import hashlib, subprocess
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def replace(path, old, new, count=1):
    path=ROOT/path
    text=path.read_text(encoding='utf-8')
    if text.count(old)!=count:raise RuntimeError(f'Expected {count} guarded matches in {path.relative_to(ROOT)} for {old[:100]!r}; got {text.count(old)}')
    path.write_text(text.replace(old,new),encoding='utf-8')

def install(name,target):
    path=ROOT/target;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text((HERE/(name+'.in')).read_text(encoding='utf-8'),encoding='utf-8')

def apply():
    expected={
        'client/Scripts/WorldView.cs':'04143ba303f8b9742cc158b528ba42c4a948d258',
        'client/Scripts/PixelAssets.cs':'b39f7200ebf52ce554c7d158fee68e0d8c521750',
        'client/Scripts/GameRoot.cs':'cb781e6b134351a63f565a7523ffb90f9240a51f',
        'client/Scripts/SpritePoseRules.cs':'66e18353072d668960aaa910fbfb49eb0d928abc',
        'src/Kairnfall.Core/Models.cs':'d06afbbc6e81aa3c38fdb6376bfa2e2e6afe8af0',
        'src/Kairnfall.Core/RealmEngine.cs':'1a1ecc8981e52bbfffdacea0e104dba858b1b119'}
    for name,digest in expected.items():
        actual=subprocess.check_output(['git','hash-object',name],cwd=ROOT,text=True).strip()
        if actual!=digest:raise RuntimeError('Source changed since inspection; refusing to overwrite '+name)
    install('ActorPresentation.cs','src/Kairnfall.Core/ActorPresentation.cs')
    install('SpritePoseRules.cs','client/Scripts/SpritePoseRules.cs')
    install('PixelAssets.cs','client/Scripts/PixelAssets.cs')
    install('WorldView.CharacterMotion.cs','client/Scripts/WorldView.CharacterMotion.cs')
    install('CharacterProbe.cs','tools/character_probe/Program.cs')
    install('CharacterPresentationContract.cs','client/Tests/CharacterPresentationContract.cs')
    (ROOT/'tools/character_probe/CharacterProbe.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup>\n  <ItemGroup><ProjectReference Include="../../src/Kairnfall.Core/Kairnfall.Core.csproj" /></ItemGroup>\n</Project>\n')
    (ROOT/'client/Tests/CharacterPresentationContract.tscn').write_text('[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="res://Tests/CharacterPresentationContract.cs" id="1"]\n\n[node name="CharacterPresentationContract" type="Node"]\nscript = ExtResource("1")\n')
    replace('Kairnfall.slnx','</Solution>','  <Project Path="tools/character_probe/CharacterProbe.csproj" />\n</Solution>')
    replace('src/Kairnfall.Core/ActorPresentation.cs','state is 2 or 3 or 4 or 5 or 6 or 7 or 9','state is 2 or 3 or 4 or 5 or 6 or 7 or 9 or 10')
    replace('src/Kairnfall.Core/ActorPresentation.cs','if (state is 2 or 9)','if (state is 2 or 9 or 10)')
    replace('src/Kairnfall.Core/ActorPresentation.cs','if (incoming is < 0 or > 9)','if (incoming is < 0 or > 10)')
    replace('src/Kairnfall.Core/ActorPresentation.cs','cue.Sequence > 0 && cue.Actor.Length > 0 && cue.Actor.Length <= 128','cue is not null && cue.Sequence > 0 && cue.Actor is { Length: > 0 and <= 128 }')
    replace('src/Kairnfall.Core/ActorPresentation.cs','        (int state, double duration) = command.Kind switch','        if (command.Kind == "respawn") { presentationCues.Remove(player.Id); return; }\n        (int state, double duration) = command.Kind switch')
    replace('src/Kairnfall.Core/ActorPresentation.cs','|| !ActorMotion.CueIsCurrent(x.Value.Cue, State.Time)','|| !State.Characters.TryGetValue(x.Key, out var actor) || actor.Health <= 0 || actor.Zone != x.Value.Zone\n                     || !ActorMotion.CueIsCurrent(x.Value.Cue, State.Time)')
    replace('src/Kairnfall.Core/Models.cs','public sealed class Snapshot\n{','public sealed class Snapshot\n{\n    public List<ActorPresentationCue> ActorCues { get; set; } = [];')
    # Publishing only occurs after the complete candidate, including these guarded edits, passes.
    replace('src/Kairnfall.Core/RealmEngine.cs','            EconomicDirty=true; return result;','            ObservePresentation(p,command);\n            EconomicDirty=true; return result;')
    replace('src/Kairnfall.Core/RealmEngine.cs','        return snap;','        AppendPresentation(snap);\n        return snap;')
    replace('client/Scripts/SpritePoseRules.cs','if (human && state is >= 6 and <= 10) return ("motions/" + key, state - 6);\n        return (key, Math.Clamp(state, 0, key.StartsWith("motions/", StringComparison.Ordinal) ? 4 : 5));','if (human && state is >= 6 and <= 10)\n        {\n            string[] motions = ["interact", "craft", "run", "bow_attack", "crossbow_attack"];\n            return ("motions/" + motions[state - 6] + "/" + key, 0);\n        }\n        return (key, Math.Clamp(state, 0, key.StartsWith("motions/", StringComparison.Ordinal) ? 0 : 5));')
    replace('client/Scripts/WorldView.CharacterMotion.cs','            if (!tracks.TryGetValue(cue.Actor, out var track)','            if (cue is null || string.IsNullOrEmpty(cue.Actor)) continue;\n            if (!tracks.TryGetValue(cue.Actor, out var track)')
    replace('client/Scripts/WorldView.CharacterMotion.cs','if (cue.Npc.Length > 0 &&','if (!string.IsNullOrEmpty(cue.Npc) &&')
    replace('client/Scripts/WorldView.cs','        public double WalkPhase;','        public double WalkPhase;\n        public double RenderSpeed;\n        public double IdlePhase;\n        public bool Moving;\n        public bool Player;\n        public long CueSequence;\n        public int ActionDirection;')
    replace('client/Scripts/WorldView.cs','Snapshot = null; Loot.Clear(); tracks.Clear(); interactions.Clear(); numbers.Clear(); lastZone = ""; TargetId = ""; Waypoint = null;','Snapshot = null; Loot.Clear(); tracks.Clear(); interactions.Clear(); numbers.Clear(); npcGestures.Clear(); combatBursts.Clear(); impactUntil = 0; impactStrength = 0; lastZone = ""; TargetId = ""; Waypoint = null;')
    replace('client/Scripts/WorldView.cs','            tracks.Clear(); numbers.Clear(); TargetId = ""; Waypoint = null;','            tracks.Clear(); numbers.Clear(); npcGestures.Clear(); combatBursts.Clear(); impactUntil = 0; impactStrength = 0; TargetId = ""; Waypoint = null;')
    replace('client/Scripts/WorldView.cs','Track(snapshot.Self.Id, snapshot.Self.Position, snapshot.Self.Facing, snapshot.Self.Health);','Track(snapshot.Self.Id, snapshot.Self.Position, snapshot.Self.Facing, snapshot.Self.Health, true);')
    replace('client/Scripts/WorldView.cs','Track(player.Id, player.Position, player.Facing, player.Health);','Track(player.Id, player.Position, player.Facing, player.Health, true);')
    replace('client/Scripts/WorldView.cs','            var track = Track(creature.Id, creature.Position, creature.Facing, creature.Health);\n            if (creature.NextAttack > track.LastAttack + .01 && creature.Health > 0)','            bool existing = tracks.ContainsKey(creature.Id);\n            var track = Track(creature.Id, creature.Position, creature.Facing, creature.Health);\n            if (!existing) track.LastAttack = creature.NextAttack;\n            if (existing && creature.NextAttack > track.LastAttack + .01 && creature.Health > 0)')
    replace('client/Scripts/WorldView.cs','    private ActorTrack Track(string id, Point position, Point facing, double health)','    private ActorTrack Track(string id, Point position, Point facing, double health, bool player = false)')
    replace('client/Scripts/WorldView.cs','FacingDirection = SpritePoseRules.Direction(facing, 0), Health = health, LastMoved = -10','FacingDirection = SpritePoseRules.Direction(facing, 0), ActionDirection = SpritePoseRules.Direction(facing, 0), Health = health, LastMoved = -10, Player = player, IdlePhase = IdleOffset(id)')
    replace('client/Scripts/WorldView.cs','            tracks[id] = track;','            tracks[id] = track;\n            if (health <= 0) { track.State = 5; track.StateStart = Clock - ActorMotion.CorpseCollapseSeconds; track.StateUntil = Clock + 6; }')
    replace('client/Scripts/WorldView.cs','                Animate(creature.Id, 2, .6);\n            }\n        }\n    }','                Animate(creature.Id, 2, .6);\n            }\n        }\n        AcceptPresentation(snapshot);\n    }')
    replace('client/Scripts/WorldView.cs','        if (!tracks.TryGetValue(id, out var track)) return;\n        track.State = state; track.StateStart = Clock; track.StateUntil = Clock + duration;','        if (!tracks.TryGetValue(id, out var track) || !double.IsFinite(duration) || duration <= 0) return;\n        int current = Clock < track.StateUntil ? track.State : 0;\n        if (!ActorMotion.MayInterrupt(current, state, track.Health > 0)) return;\n        track.ActionDirection = track.FacingDirection;\n        track.State = state; track.StateStart = Clock; track.StateUntil = Clock + Math.Min(duration, 6);')
    replace('client/Scripts/WorldView.cs','''        foreach (var track in tracks.Values)
        {
            var previousPosition = track.Position;
            double weight = 1 - Math.Exp(-18 * delta);
            if (track.Position.Distance(track.Target) > 6) track.Position = track.Target;
            else track.Position = new Point(track.Position.X + (track.Target.X - track.Position.X) * weight, track.Position.Y + (track.Target.Y - track.Position.Y) * weight);
            double travelled = previousPosition.Distance(track.Position);
            track.WalkPhase = travelled > 6 ? 0 : SpritePoseRules.AdvanceWalk(track.WalkPhase, travelled);
        }''','        foreach (var track in tracks.Values) AdvanceTrack(track, delta);')
    replace('client/Scripts/WorldView.cs','''        if (!tracks.TryGetValue(id, out var t)) return (0, 0, (int)(Clock * 6) % 8, at);
        int state = t.Health <= 0 ? 5 : Clock < t.StateUntil ? t.State : Clock - t.LastMoved < .35 ? 1 : 0;
        int frame = state is 2 or 3 or 4 or 5
            ? SpritePoseRules.ActionFrame(state, Clock - t.StateStart, t.StateUntil - t.StateStart)
            : state == 1 ? (int)t.WalkPhase : (int)(Clock * 5) % 8;
        return (state, t.FacingDirection, frame, t.Position);''','''        if (!tracks.TryGetValue(id, out var t)) return (0, 0, (int)(Clock * 5 + IdleOffset(id)) % 8, at);
        int state = t.Health <= 0 ? 5 : Clock < t.StateUntil ? t.State : t.Moving ? Running(id) ? 8 : 1 : 0;
        int frame = ActorMotion.IsAction(state)
            ? SpritePoseRules.ActionFrame(state, Clock - t.StateStart, t.StateUntil - t.StateStart)
            : state is 1 or 8 ? (int)t.WalkPhase : (int)(Clock * 5 + t.IdlePhase) % 8;
        int direction = ActorMotion.IsAction(state) ? t.ActionDirection : t.FacingDirection;
        return (state, direction, frame, t.Position);''')
    replace('client/Scripts/WorldView.cs','Assets.DrawFrame(this, "npcs/" + npc.Role, feet, 0, npc.Position.X > Camera.X + 2 ? 1 : npc.Position.X < Camera.X - 2 ? 2 : 0, (int)(Clock * 5) % 8);','DrawNpc(npc, feet);')
    replace('client/Scripts/WorldView.cs','Assets.DrawPerson(this, player.Appearance, player.Equipment, feet, player.Health<=0?5:pp.State, pp.Direction, player.Health<=0?7:pp.Frame);','Assets.DrawPerson(this, player.Appearance, player.Equipment, feet, pp.State, pp.Direction, pp.Frame, LocomotionFrame(player.Id), Running(player.Id));')
    replace('client/Scripts/WorldView.cs','Assets.DrawPerson(this, character.Appearance, PixelAssets.VisibleEquipment(character), feet, self.State, self.Direction, self.Frame);','Assets.DrawPerson(this, character.Appearance, PixelAssets.VisibleEquipment(character), feet, self.State, self.Direction, self.Frame, LocomotionFrame(character.Id), Running(character.Id));')
    replace('client/Scripts/GameRoot.cs','                if (command.Kind is "attack" or "cast" or "gather") World.Animate(Snapshot!.Self.Id, command.Kind == "cast" ? 3 : 2, .6);','                // Accepted server cues drive both self and remote actions; receipts must not restart them.')
    print('Guarded character runtime integration applied.')
