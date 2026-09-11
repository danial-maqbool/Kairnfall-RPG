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

print('Refined directional walk-through entrance rules.')
