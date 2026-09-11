#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def replace_once(path,old,new):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{path}: expected one match, found {count}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

# Internal entrances are directional thresholds, not proximity mines. A player must
# approach from the source-map side and actually move into the entrance. Border
# exits retain their dedicated outward-lane behavior.
replace_once('src/Kairnfall.Core/MapTransitionRules.cs',
'''        if (SegmentDistance(before, after, exit.Position) > WalkTriggerRadius
            && after.Distance(exit.Position) > WalkTriggerRadius) return false;
        var toward = before.Direction(exit.Position);
        return toward.Distance(new Point(0, 0)) > 0.01 && Dot(unit, toward) > 0.05;
''',
'''        if (SegmentDistance(before, after, exit.Position) > WalkTriggerRadius
            && after.Distance(exit.Position) > WalkTriggerRadius) return false;

        // Interior/cave/settlement entrances have a front side. The authored zone
        // spawn represents the playable side of that threshold, so crossing traffic
        // cannot trigger a doorway simply by brushing across its tile.
        var forward = zone.Spawn.Direction(exit.Position);
        if (forward.Distance(new Point(0, 0)) > 0.01)
        {
            if (Dot(unit, forward) < 0.55) return false;
            var fromExit = new Point(before.X - exit.Position.X, before.Y - exit.Position.Y);
            if (Dot(fromExit, forward) > 0.15) return false;
        }
        var toward = before.Direction(exit.Position);
        return toward.Distance(new Point(0, 0)) > 0.01 && Dot(unit, toward) > 0.20;
''')

# Make any future integration regression name the accidental source/destination and
# intended coordinate, instead of hiding the geometry behind a generic assertion.
replace_once('tests/Kairnfall.Integration/Program.cs',
'''        snapshot=await State(client); Check(snapshot.Self.Zone==zoneId,"Navigation crossed an unexpected zone.");
''',
'''        snapshot=await State(client); Check(snapshot.Self.Zone==zoneId,$"Navigation crossed an unexpected zone {zoneId} -> {snapshot.Self.Zone} while heading to {destination}.");
''')

# The network acceptance route must model what a player does at a visible entrance:
# reach the inside approach point first, then walk directly through the threshold.
replace_once('tests/Kairnfall.Integration/Program.cs',
'''    var exit=source.Exits.First(x=>x.Target==destination);
    var route=WorldMap.FindPath(source,snapshot.Self.Position,exit.Position,source.Width*source.Height);route.Add(exit.Position);
    int next=0;var watch=Stopwatch.StartNew();
    while(watch.Elapsed<TimeSpan.FromSeconds(100))
    {
        snapshot=await State(client);
        if(snapshot.Self.Zone==destination) { await client.MoveAsync(0,0,cancel);return; }
        Check(snapshot.Self.Zone==sourceId,"Walk-through navigation crossed an unexpected zone.");
        var position=snapshot.Self.Position;Point direction;
        var outward=MapTransitionRules.BorderOutward(source,exit);
        if(outward.Distance(new Point(0,0))>0.01&&position.Distance(exit.Position)<1.6) direction=outward;
        else
        {
            while(next<route.Count-1&&position.Distance(route[next])<0.7) next++;
            direction=position.Direction(route[Math.Min(next,route.Count-1)]);
        }
        await client.MoveAsync(direction.X,direction.Y,cancel);await Task.Delay(100,cancel);Pump(client);
    }
''',
'''    var exit=source.Exits.First(x=>x.Target==destination);
    var outward=MapTransitionRules.BorderOutward(source,exit);
    var forward=outward.Distance(new Point(0,0))>0.01 ? outward : source.Spawn.Direction(exit.Position);
    var approach=WorldMap.FindFree(source,exit.Position.Add(forward.Scale(-1.20)));
    var route=WorldMap.FindPath(source,snapshot.Self.Position,approach,source.Width*source.Height);route.Add(approach);
    int next=0;var watch=Stopwatch.StartNew();
    while(watch.Elapsed<TimeSpan.FromSeconds(100))
    {
        snapshot=await State(client);
        if(snapshot.Self.Zone==destination) { await client.MoveAsync(0,0,cancel);return; }
        Check(snapshot.Self.Zone==sourceId,$"Walk-through navigation crossed {sourceId} -> {snapshot.Self.Zone} while entering {destination}.");
        var position=snapshot.Self.Position;Point direction;
        if(position.Distance(approach)<0.80) direction=forward;
        else
        {
            while(next<route.Count-1&&position.Distance(route[next])<0.7) next++;
            direction=position.Direction(route[Math.Min(next,route.Count-1)]);
        }
        await client.MoveAsync(direction.X,direction.Y,cancel);await Task.Delay(100,cancel);Pump(client);
    }
''')

print('Refined directional walk-through entrance rules and network approach geometry.')
