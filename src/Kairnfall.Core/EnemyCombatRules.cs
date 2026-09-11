namespace Kairnfall.Core;

public static class EnemyCombatRules
{
    public static readonly string[] EliteTraits = ["elite_bulwark","elite_frenzy","elite_vampiric","elite_tempest","elite_skirmisher"];
    private static readonly HashSet<string> EnemyAttacks = new([
        "strike","lunge","slam","brace","frenzy","ambush","projectile","circle","charge","cone","stomp","line","ring",
        "interruptible","poison_field","summon","root","field","tempest"
    ],StringComparer.Ordinal);

    public static bool IsEliteTrait(string token)=>EliteTraits.Contains(token,StringComparer.Ordinal);
    public static bool IsKnownAttack(string token)=>EnemyAttacks.Contains(token);
    public static string EliteTrait(MobDef definition)=>definition.Attacks.FirstOrDefault(IsEliteTrait)??"";

    public static IReadOnlyList<string> AvailableBossAttacks(MobDef definition,int phase)
    {
        if(!definition.Boss||definition.Attacks.Length==0)return [];
        int count=Math.Clamp(phase+1,1,definition.Attacks.Length);
        return definition.Attacks.Take(count).ToArray();
    }

    public static string NextBossAttack(MobDef definition,Creature creature)
    {
        var choices=AvailableBossAttacks(definition,creature.Phase);
        if(choices.Count==0)return "strike";
        string attack=choices[creature.AttackStep%choices.Count];creature.AttackStep++;
        return attack;
    }

    public static string NextStandardAttack(MobDef definition,Creature creature)
    {
        var attacks=definition.Attacks.Where(x=>!IsEliteTrait(x)&&IsKnownAttack(x)).ToArray();
        if(attacks.Length==0)attacks=["strike"];
        int step=creature.AttackStep++;
        if(EliteTrait(definition)=="elite_tempest"&&step%3==2)return "tempest";
        return attacks[step%attacks.Length];
    }

    public static double AttackInterval(MobDef definition,Creature creature)
    {
        double interval=definition.Boss?2.8-creature.Phase*.3:definition.Ai switch
        {
            "pack_hunter"=>1.55,"ambusher"=>2.1,"ranged_kiter"=>2.0,"caster"=>2.2,"healer"=>2.25,"guard"=>2.2,"summoner"=>2.4,_=>1.8
        };
        if(EliteTrait(definition)=="elite_frenzy")interval*=.72;
        return Math.Max(.8,interval);
    }

    public static double MoveSpeedMultiplier(MobDef definition)=>EliteTrait(definition)=="elite_skirmisher"?1.28:1;
    public static double IncomingDamageMultiplier(MobDef definition)=>EliteTrait(definition)=="elite_bulwark"?.78:1;
    public static double PowerMultiplier(MobDef definition,Creature creature)
    {
        double result=1;
        if(definition.Ai=="berserker"&&creature.Health<definition.Health*.4)result*=1.6;
        if(EliteTrait(definition)=="elite_frenzy"&&creature.Health<definition.Health*.6)result*=1.3;
        return result;
    }

    public static string AttackLabel(string token)=>token switch
    {
        "strike"=>"Strike","lunge"=>"Lunge","slam"=>"Slam","brace"=>"Brace","frenzy"=>"Frenzy","ambush"=>"Ambush",
        "projectile"=>"Ranged Shot","circle"=>"Blast","charge"=>"Charge","cone"=>"Sweep","stomp"=>"Stomp","line"=>"Line Break",
        "ring"=>"Shock Ring","interruptible"=>"Interruptible Cast","poison_field"=>"Poison Field","summon"=>"Call Reinforcements",
        "root"=>"Binding Roots","field"=>"Hazard Field","tempest"=>"Tempest",_=>UiWords(token)
    };

    public static string TacticLabel(MobDef definition)
    {
        if(definition.Boss)return "Boss phases unlock authored attacks";
        string role=definition.Ai switch
        {
            "ranged_kiter"=>"Kiter · retreats when pressured","caster"=>"Caster · telegraphed area attacks","ambusher"=>"Ambusher · burst and bleed",
            "pack_hunter"=>"Pack hunter · shares threat","healer"=>"Support · heals wounded allies","summoner"=>"Summoner · calls reinforcements",
            "guard"=>"Guard · braces before heavy slams","berserker"=>"Berserker · stronger while wounded","fleeing"=>"Fleeing wildlife",
            "passive"=>"Passive wildlife","territorial"=>"Territorial bruiser",_=>"Aggressive skirmisher"
        };
        string elite=EliteTrait(definition) switch
        {
            "elite_bulwark"=>" · Bulwark","elite_frenzy"=>" · Frenzied","elite_vampiric"=>" · Vampiric","elite_tempest"=>" · Stormmarked","elite_skirmisher"=>" · Fleet",_=>""
        };
        return role+elite;
    }

    private static string UiWords(string value)=>string.Join(' ',value.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]));
}
