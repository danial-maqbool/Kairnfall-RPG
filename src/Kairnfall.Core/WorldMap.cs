namespace Kairnfall.Core;

public enum Terrain { Grass, Dirt, Stone, Sand, Snow, Water, Lava, Wall, Wood, Moss, Crystal, Marsh, Ash }

public static class WorldMap
{
    public const int TileSize = 32;
    public const double ActorRadius = 0.24;
    public static uint Hash(int x,int y,int seed)
    {
        unchecked
        {
            uint h=(uint)x*374761393u+(uint)y*668265263u+(uint)seed*2246822519u;
            h=(h^(h>>13))*1274126177u; return h^(h>>16);
        }
    }
    private static bool OnRoad(ZoneDef z,int x,int y,bool legacy=false)
    {
        int sx=(int)z.Spawn.X,sy=(int)z.Spawn.Y;
        if(Math.Abs(x-sx)<=2||Math.Abs(y-sy)<=2) return true;
        foreach(var e in z.Exits)
        {
            var ex=(int)e.Position.X; var ey=(int)e.Position.Y;
            if(legacy && z.Id=="thornhollow" && e.Id=="thornhollow_to_thornhollow_deepway") { ex=64; ey=88; }
            if(Math.Abs(y-ey)<=1 && x>=Math.Min(ex,sx)-1 && x<=Math.Max(ex,sx)+1) return true;
            if(Math.Abs(x-sx)<=1 && y>=Math.Min(ey,sy)-1 && y<=Math.Max(ey,sy)+1) return true;
        }
        // Keep physical door approaches connected even where rivers or rough terrain
        // border a building. Masonry still takes precedence over these paths below.
        if(legacy) return false;
        foreach(var b in z.Buildings)
        {
            int doorX=b.X+b.Width/2, approachY=b.Y+b.Height;
            if(Math.Abs(y-approachY)<=1 && x>=Math.Min(doorX,sx) && x<=Math.Max(doorX,sx)) return true;
        }
        return false;
    }
    public static Terrain TileAt(ZoneDef z,int x,int y)=>TileAt(z,x,y,false);
    private static Terrain TileAt(ZoneDef z,int x,int y,bool legacy)
    {
        if(x<1||y<1||x>=z.Width-1||y>=z.Height-1) return Terrain.Wall;
        if(legacy && OnRoad(z,x,y,true)) return z.Layer=="Surface" ? Terrain.Dirt : Terrain.Stone;
        foreach(var b in z.Buildings)
        {
            if(x>=b.X&&x<b.X+b.Width&&y>=b.Y+1&&y<b.Y+b.Height)
                return (x==b.X+b.Width/2&&y==b.Y+b.Height-1) ? Terrain.Wood : Terrain.Wall;
        }
        if(!legacy && OnRoad(z,x,y)) return z.Layer=="Surface" ? Terrain.Dirt : Terrain.Stone;
        uint h=Hash(x,y,z.Seed);
        if(z.Kind=="interior") return (x>2&&y>2&&x<z.Width-3&&y<z.Height-3)?Terrain.Wood:Terrain.Wall;
        if(z.Layer!="Surface")
        {
            int cx=z.Width/2,cy=z.Height/2;
            bool room=(Math.Abs(x-cx)<=8&&Math.Abs(y-cy)<=8);
            for(int i=0;i<8;i++)
            {
                int rx=8+(int)(Hash(i,0,z.Seed)%(uint)(z.Width-16));
                int ry=8+(int)(Hash(i,1,z.Seed)%(uint)(z.Height-16));
                room |= Math.Abs(x-rx)<=5&&Math.Abs(y-ry)<=4;
                room |= Math.Abs(x-rx)<=1&&y>=Math.Min(ry,cy)&&y<=Math.Max(ry,cy);
                room |= Math.Abs(y-cy)<=1&&x>=Math.Min(rx,cx)&&x<=Math.Max(rx,cx);
            }
            if(!room) return Terrain.Wall;
            return z.Biome=="fungal"?Terrain.Moss:z.Biome=="crystal"?Terrain.Crystal:Terrain.Stone;
        }
        double river=z.Width*0.72+Math.Sin(y*0.075+z.Seed%11)*7;
        if(Math.Abs(x-river)<2.5 && z.Biome is not ("volcanic" or "badlands" or "glacier")) return Terrain.Water;
        if(z.Kind is "city" or "settlement")
        {
            if(Math.Abs(x-z.Spawn.X)<19&&Math.Abs(y-z.Spawn.Y)<19) return Terrain.Stone;
        }
        return z.Biome switch
        {
            "tundra" or "glacier" => h%19==0?Terrain.Stone:Terrain.Snow,
            "volcanic" => h%47==0?Terrain.Lava:Terrain.Ash,
            "coast" or "archipelago" or "badlands" => Terrain.Sand,
            "swamp" or "wetlands" => h%13==0?Terrain.Water:Terrain.Marsh,
            "mountains" or "highlands" => h%29==0?Terrain.Wall:Terrain.Stone,
            "wasteland" => Terrain.Ash,
            "ancient_forest" or "pine_forest" => Terrain.Moss,
            _ => Terrain.Grass
        };
    }
    public static bool IsSolid(Terrain t) => t is Terrain.Wall or Terrain.Water or Terrain.Lava;
    public static bool Walkable(ZoneDef z,Point p)
    {
        if(!p.Finite) return false;
        return !IsSolid(TileAt(z,(int)Math.Floor(p.X),(int)Math.Floor(p.Y)));
    }
    public static bool Fits(ZoneDef z,Point p)
    {
        return Walkable(z,new(p.X-ActorRadius,p.Y-ActorRadius))&&Walkable(z,new(p.X+ActorRadius,p.Y-ActorRadius))&&Walkable(z,new(p.X-ActorRadius,p.Y+ActorRadius))&&Walkable(z,new(p.X+ActorRadius,p.Y+ActorRadius));
    }
    // Used only while loading saved state after the masonry-priority repair.
    // Never turn arbitrary corrupt coordinates into a spawn teleport.
    public static bool TryRecoverLegacyRoadPosition(ZoneDef z,Point saved,out Point recovered)
    {
        recovered=saved;
        if(!saved.Finite || saved.X<1 || saved.Y<1 || saved.X>=z.Width-1 || saved.Y>=z.Height-1 || Fits(z,saved)) return false;
        foreach(double dx in new[]{-ActorRadius,ActorRadius})
            foreach(double dy in new[]{-ActorRadius,ActorRadius})
            {
                double x=Math.Floor(saved.X+dx),y=Math.Floor(saved.Y+dy);
                if(x<1||y<1||x>=z.Width-1||y>=z.Height-1 || IsSolid(TileAt(z,(int)x,(int)y,true))) return false;
            }
        for(int radius=0;radius<=16;radius++)
            for(int dy=-radius;dy<=radius;dy++)
                for(int dx=-radius;dx<=radius;dx++)
                {
                    if(Math.Max(Math.Abs(dx),Math.Abs(dy))!=radius) continue;
                    var candidate=new Point(Math.Floor(saved.X)+dx+.5,Math.Floor(saved.Y)+dy+.5);
                    if(!Fits(z,candidate)) continue;
                    if(candidate.Distance(z.Spawn)>.01 && FindPath(z,z.Spawn,candidate,z.Width*z.Height).Count==0) continue;
                    recovered=candidate; return true;
                }
        return false;
    }
    public static Point Move(ZoneDef z,Point from,Point delta)
    {
        if(!from.Finite||!delta.Finite) return from;
        double length=Math.Sqrt(delta.X*delta.X+delta.Y*delta.Y);
        int steps=Math.Clamp((int)Math.Ceiling(length/0.2),1,128);
        var step=delta.Scale(1.0/steps); var p=from;
        for(int i=0;i<steps;i++)
        {
            var dx=new Point(p.X+step.X,p.Y); if(Fits(z,dx)) p=dx;
            var dy=new Point(p.X,p.Y+step.Y); if(Fits(z,dy)) p=dy;
        }
        return p;
    }
    public static bool LineOfSight(ZoneDef z,Point a,Point b)
    {
        if(!a.Finite||!b.Finite||a.Distance(b)>64) return false;
        int count=Math.Max(1,(int)Math.Ceiling(a.Distance(b)*4));
        for(int i=1;i<=count;i++) if(!Walkable(z,new(a.X+(b.X-a.X)*i/count,a.Y+(b.Y-a.Y)*i/count))) return false;
        return true;
    }
    public static Point FindFree(ZoneDef z,Point near)
    {
        for(int r=0;r<24;r++) for(int dy=-r;dy<=r;dy++) for(int dx=-r;dx<=r;dx++)
        {
            var p=new Point(Math.Floor(near.X)+dx+0.5,Math.Floor(near.Y)+dy+0.5);
            if(Fits(z,p)) return p;
        }
        return z.Spawn;
    }
    public static List<Point> FindPath(ZoneDef z,Point start,Point destination,int budget=4096)
    {
        var s=((int)start.X,(int)start.Y); var g=((int)destination.X,(int)destination.Y);
        var open=new PriorityQueue<(int,int),double>(); open.Enqueue(s,0);
        var cost=new Dictionary<(int,int),double>{{s,0}};
        var previous=new Dictionary<(int,int),(int,int)>();
        (int,int)[] directions=[(1,0),(-1,0),(0,1),(0,-1)];
        while(open.TryDequeue(out var current,out _)&&budget-->0)
        {
            if(current==g)
            {
                var path=new List<Point>(); var p=g;
                while(p!=s) { path.Add(new(p.Item1+0.5,p.Item2+0.5)); p=previous[p]; }
                path.Reverse(); return path;
            }
            foreach(var d in directions)
            {
                var next=(current.Item1+d.Item1,current.Item2+d.Item2);
                if(!Walkable(z,new(next.Item1+0.5,next.Item2+0.5))) continue;
                double c=cost[current]+1;
                if(cost.TryGetValue(next,out var old)&&old<=c) continue;
                cost[next]=c; previous[next]=current;
                open.Enqueue(next,c+Math.Abs(next.Item1-g.Item1)+Math.Abs(next.Item2-g.Item2));
            }
        }
        return [];
    }
}
