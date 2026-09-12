namespace Kairnfall.Core;

/// <summary>Pure combat-presentation contracts derived only from authoritative snapshot state.</summary>
public static class CombatReadabilityRules
{
    public static double TelegraphRemaining(Telegraph telegraph,double serverTime)
        => !double.IsFinite(serverTime)||!double.IsFinite(telegraph.Resolves)?0:Math.Max(0,telegraph.Resolves-serverTime);

    public static double TelegraphUrgency(Telegraph telegraph,double serverTime)
    {
        double remaining=TelegraphRemaining(telegraph,serverTime);
        // Enemy casts are authored between roughly .45 and 1.6 seconds. A one-second
        // visibility window gives a deterministic pulse without inventing client timing.
        return Math.Clamp(1-remaining,0,1);
    }

    public static bool IsInterruptible(Telegraph telegraph)=>telegraph.Skill=="interruptible";

    public static bool IsCrowdControl(string kind)=>kind is "stun" or "silence" or "root" or "chill" or "slow" or "revive_sickness";

    public static string StatusLabel(string kind)=>kind switch
    {
        "stun"=>"STUNNED","silence"=>"SILENCED","root"=>"ROOTED","chill"=>"CHILLED","slow"=>"SLOWED",
        "revive_sickness"=>"REVIVE SICKNESS","bleed"=>"BLEEDING","burn"=>"BURNING","poison"=>"POISONED",
        "curse"=>"CURSED","vulnerable"=>"VULNERABLE","fortify"=>"FORTIFIED","shield"=>"SHIELDED",
        _=>Words(kind)
    };

    public static string EliteTraitLabel(MobDef definition)=>EnemyCombatRules.EliteTrait(definition) switch
    {
        "elite_bulwark"=>"BULWARK","elite_frenzy"=>"FRENZIED","elite_vampiric"=>"VAMPIRIC",
        "elite_tempest"=>"STORMMARKED","elite_skirmisher"=>"FLEET",_=>""
    };

    public static string EnemyBanner(MobDef definition,Creature creature)
    {
        if(definition.Boss)return $"BOSS · PHASE {Math.Clamp(creature.Phase+1,1,3)}/3";
        if(definition.Elite)
        {
            string trait=EliteTraitLabel(definition);
            return trait==""?"RARE":"RARE · "+trait;
        }
        return definition.Ai switch
        {
            "ranged_kiter"=>"KITER · KEEPS RANGE","caster"=>"CASTER · WATCH TELEGRAPHS","ambusher"=>"AMBUSHER · BURST",
            "healer"=>"SUPPORT · HEALS ALLIES","summoner"=>"SUMMONER · ADDS",_=>""
        };
    }

    public static string TelegraphLabel(Telegraph telegraph)
    {
        string label=EnemyCombatRules.IsKnownAttack(telegraph.Skill)?EnemyCombatRules.AttackLabel(telegraph.Skill):Words(telegraph.Skill);
        return IsInterruptible(telegraph)?label+" · INTERRUPT":label;
    }

    public static bool CanRevive(Character self,PublicPlayer other,SocialGroup? party,double serverTime)
        => self.Health>0&&other.Health<=0&&party is not null&&party.Members.Contains(self.Id)&&party.Members.Contains(other.Id)
            &&self.Zone!=""&&self.Position.Distance(other.Position)<=2.6&&self.Stamina>=20&&self.Cooldowns.GetValueOrDefault("revive")<=serverTime;

    private static string Words(string value)=>string.Join(' ',(value??"").Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]));
}
