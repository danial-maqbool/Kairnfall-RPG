namespace Kairnfall.Core;

/// <summary>Server-owned learning and overall progression. Monster statistics never scale with player level.</summary>
public static class ChallengeProgression
{
    public static double OverallRate(int level)
    {
        int band=(Math.Clamp(level,1,Progression.PlayerCap)-1)/10;
        return .25/(1+.14*band+.035*band*band);
    }
    public static double SkillPractice(int playerLevel,int enemyLevel)
    {
        double gap=Math.Max(0,Math.Clamp(playerLevel,1,200)-Math.Clamp(enemyLevel,1,100)-3);
        return Math.Max(.04,1/(1+Math.Pow(gap/8,3)));
    }
    public static double EnemyCredit(int playerLevel,int enemyLevel)
    {
        double gap=Math.Max(0,Math.Clamp(playerLevel,1,200)-Math.Clamp(enemyLevel,1,100)-3);
        return Math.Max(.005,Math.Exp(-.24*gap));
    }
    public static long OverallTraining(Character p)
    {
        long total=Progression.Total(p);
        return total-Math.Clamp(p.PracticeOnlyXp,0,total);
    }
    public static void Credit(Character p,long actual,int levelBefore,double enemyFactor=1)
    {
        if(actual<=0)return;
        if(!double.IsFinite(enemyFactor)||enemyFactor<0||enemyFactor>1)throw new RuleException("Invalid overall training factor.");
        double remainder=double.IsFinite(p.OverallCreditRemainder)?Math.Clamp(p.OverallCreditRemainder,0,.999999999):0;
        double equivalent=actual*OverallRate(levelBefore)*enemyFactor+remainder;
        long credited=Math.Clamp((long)Math.Floor(equivalent),0,actual);
        p.OverallCreditRemainder=equivalent-credited;
        long total=Progression.Total(p);
        p.PracticeOnlyXp=Math.Clamp(Math.Clamp(p.PracticeOnlyXp,0,total)+actual-credited,0,total);
    }
    public static long TrainCombat(Character p,string skill,int xp,int enemyLevel,Catalog data)
    {
        data.Skill(skill);
        if(xp<0||xp>100000||enemyLevel<1||enemyLevel>100)throw new RuleException("Invalid combat training award.");
        if(xp==0)return 0;
        int level=Progression.PlayerLevel(p), over=Progression.Level(p,skill)-enemyLevel;
        // Trivial combat retains small practice, not a free whole XP point per hit.
        double mastery=Math.Clamp((30.0-over)/30,.05,1);
        double affinity=data.Class(p.Class).Affinity.Contains(skill)?1.10:1;
        double carry=p.CombatPracticeRemainders.GetValueOrDefault(skill);
        if(!double.IsFinite(carry)||carry<0||carry>=1)carry=0;
        double pending=xp*mastery*affinity*SkillPractice(level,enemyLevel)+carry;
        long whole=(long)Math.Floor(pending), old=p.SkillXp.GetValueOrDefault(skill);
        long actual=Math.Max(0,Math.Min(Progression.Threshold(Progression.SkillCap)-old,whole));
        p.SkillXp[skill]=old+actual;
        p.CombatPracticeRemainders[skill]=p.SkillXp[skill]>=Progression.Threshold(Progression.SkillCap)?0:pending-whole;
        Credit(p,actual,level,EnemyCredit(level,enemyLevel));
        return actual;
    }
    public static string ChallengeName(int level,int enemy)
    {
        int gap=level-enemy;
        return gap>=20?"Trivial hunt":gap>=10?"Low challenge":gap>=4?"Light challenge":enemy-level>=8?"Dangerous hunt":"Matched hunt";
    }
}

/// <summary>Bounded diminishing returns for trained attacks. Armor and resistance retain their existing curves.</summary>
public static class CombatTrainingCurve
{
    public static double Physical(int skill)
    {
        double s=Math.Clamp(skill,1,Progression.SkillCap);
        return 1+.9*s/(s+75);
    }
    public static double Spell(int skill)
    {
        double s=Math.Clamp(skill,1,Progression.SkillCap);
        return 1+.75*s/(s+100);
    }
}
