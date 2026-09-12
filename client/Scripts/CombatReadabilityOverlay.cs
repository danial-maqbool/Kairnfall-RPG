using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

/// <summary>
/// Read-only presentation over authoritative snapshots. It never predicts damage,
/// cooldown completion, crowd control, phases, or revives.
/// </summary>
public partial class CombatReadabilityOverlay : Control
{
    public WorldView World { get; set; } = null!;
    public Catalog Data { get; set; } = null!;
    public string PrimaryCue { get; private set; } = "";
    public int VisibleStatusCount { get; private set; }
    public bool RevivePromptVisible { get; private set; }
    public int VisibleTelegraphCount { get; private set; }

    private Snapshot? snapshot;
    private string selectedTarget = "";
    private readonly List<Cue> cues = [];
    private sealed record Cue(Point Position,string Text,Color Color,double Until);

    public override void _Ready()
    {
        MouseFilter=MouseFilterEnum.Ignore;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
    }

    public void Accept(Snapshot current,string targetId)
    {
        selectedTarget=targetId;
        double local=Time.GetTicksMsec()/1000.0;
        if(snapshot is { } previous && !ReferenceEquals(previous,current) && previous.Self.Id==current.Self.Id)
        {
            if(current.Self.Health<previous.Self.Health-.5)
                CueAt(current.Self.Position,"DAMAGE  −"+Math.Ceiling(previous.Self.Health-current.Self.Health),Ui.Danger,local);

            if(targetId!="")
            {
                var before=previous.Creatures.FirstOrDefault(x=>x.Id==targetId);
                var after=current.Creatures.FirstOrDefault(x=>x.Id==targetId);
                if(before is not null&&after is not null)
                {
                    if(after.Health<before.Health-.5)
                        CueAt(after.Position,after.Health<=0?"DEFEATED":"HIT  "+Math.Ceiling(before.Health-after.Health),after.Health<=0?Ui.Gold:Ui.Text,local);
                    if(after.Phase>before.Phase&&Data.Mob(after.Template).Boss)
                        CueAt(after.Position,$"PHASE {after.Phase+1}/3",Ui.Gold,local,1.4);
                }
            }

            foreach(var old in previous.Telegraphs)
            {
                if(old.Resolves<=current.Time+.05||current.Telegraphs.Any(x=>x.Id==old.Id))continue;
                var source=current.Creatures.FirstOrDefault(x=>x.Id==old.Source&&x.Health>0);
                if(source is not null)CueAt(source.Position,"INTERRUPTED",Ui.Success,local,1.0);
            }
        }
        snapshot=current;
        VisibleTelegraphCount=current.Telegraphs.Count(x=>current.Creatures.Any(c=>c.Id==x.Source&&c.Health>0));
        VisibleStatusCount=current.Self.Statuses.Count(x=>x.Until>current.Time&&CombatReadabilityRules.IsCrowdControl(x.Kind));
        if(targetId!=""&&current.Creatures.FirstOrDefault(x=>x.Id==targetId) is { } target)
            VisibleStatusCount+=target.Statuses.Count(x=>x.Until>current.Time&&CombatReadabilityRules.IsCrowdControl(x.Kind));
        RevivePromptVisible=current.Players.Any(x=>CombatReadabilityRules.CanRevive(current.Self,x,current.Party,current.Time));
        cues.RemoveAll(x=>x.Until<=local);
        PrimaryCue=cues.LastOrDefault()?.Text??"";
        QueueRedraw();
    }

    public void Clear()
    {
        snapshot=null;selectedTarget="";cues.Clear();PrimaryCue="";VisibleStatusCount=0;RevivePromptVisible=false;VisibleTelegraphCount=0;QueueRedraw();
    }

    private void CueAt(Point position,string text,Color color,double local,double duration=.85)
    {
        if(!position.Finite||string.IsNullOrWhiteSpace(text))return;
        cues.Add(new(position,text,color,local+duration));
        if(cues.Count>12)cues.RemoveRange(0,cues.Count-12);
        PrimaryCue=text;
    }

    public override void _Process(double delta)
    {
        double local=Time.GetTicksMsec()/1000.0;
        if(cues.RemoveAll(x=>x.Until<=local)>0)PrimaryCue=cues.LastOrDefault()?.Text??"";
        QueueRedraw();
    }

    public override void _Draw()
    {
        if(snapshot is not { } snap||World is null||Data is null)return;
        double local=Time.GetTicksMsec()/1000.0;

        foreach(var telegraph in snap.Telegraphs)
        {
            if(!snap.Creatures.Any(x=>x.Id==telegraph.Source&&x.Health>0))continue;
            double remaining=CombatReadabilityRules.TelegraphRemaining(telegraph,snap.Time);
            string label=CombatReadabilityRules.TelegraphLabel(telegraph)+$"  {remaining:0.0}s";
            Label(World.WorldToScreen(telegraph.Position)+new Vector2(0,-30),label,
                CombatReadabilityRules.IsInterruptible(telegraph)?Ui.Gold:WorldView.ElementColor(telegraph.Element),10);
        }

        foreach(var mob in snap.Creatures.Where(x=>x.Health>0))
        {
            var definition=Data.Mob(mob.Template);
            string banner=CombatReadabilityRules.EnemyBanner(definition,mob);
            bool selected=mob.Id==selectedTarget;
            var statuses=mob.Statuses.Where(x=>x.Until>snap.Time&&CombatReadabilityRules.IsCrowdControl(x.Kind))
                .Select(x=>CombatReadabilityRules.StatusLabel(x.Kind)).Distinct(StringComparer.Ordinal).Take(2).ToArray();
            if(!selected&&banner==""&&statuses.Length==0)continue;
            string text=string.Join(" · ",new[]{selected?"TARGET":"",banner,string.Join(" · ",statuses)}.Where(x=>x!=""));
            if(text!="")Label(World.WorldToScreen(mob.Position)+new Vector2(0,-90),text,definition.Boss||definition.Elite?Ui.Gold:Ui.Text,9);
        }

        var selfStatuses=snap.Self.Statuses.Where(x=>x.Until>snap.Time&&CombatReadabilityRules.IsCrowdControl(x.Kind))
            .Select(x=>CombatReadabilityRules.StatusLabel(x.Kind)).Distinct(StringComparer.Ordinal).Take(3).ToArray();
        if(selfStatuses.Length>0)Label(World.WorldToScreen(snap.Self.Position)+new Vector2(0,-70),string.Join(" · ",selfStatuses),Ui.Danger,10);

        foreach(var player in snap.Players.Where(x=>CombatReadabilityRules.CanRevive(snap.Self,x,snap.Party,snap.Time)))
            Label(World.WorldToScreen(player.Position)+new Vector2(0,-77),"DOWNED · PARTY REVIVE AVAILABLE [P]",Ui.Success,10);

        foreach(var cue in cues.Where(x=>x.Until>local))
        {
            Color color=cue.Color;color.A=(float)Math.Clamp((cue.Until-local)/.85,0,1);
            Label(World.WorldToScreen(cue.Position)+new Vector2(0,-112),cue.Text,color,12);
        }
    }

    private void Label(Vector2 position,string text,Color color,int size)
    {
        var font=ThemeDB.FallbackFont;
        float width=Math.Min(300,font.GetStringSize(text,HorizontalAlignment.Left,-1,size).X);
        DrawRect(new Rect2(position-new Vector2(width/2+4,font.GetAscent(size)),new Vector2(width+8,font.GetHeight(size))),new Color(.03f,.025f,.02f,.78f));
        var at=position-new Vector2(150,0);
        DrawStringOutline(font,at,text,HorizontalAlignment.Center,300,size,3,new Color(0,0,0,.9f));
        DrawString(font,at,text,HorizontalAlignment.Center,300,size,color);
    }
}
