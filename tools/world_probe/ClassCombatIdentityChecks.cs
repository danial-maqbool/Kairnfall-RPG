using Kairnfall.Core;

internal static class ClassCombatIdentityChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action body)
        {
            try{body();passed++;Console.WriteLine("PASS CLASS IDENTITY: "+name);}
            catch(Exception error){failures.Add("Class identity: "+name);Console.WriteLine("FAIL CLASS IDENTITY: "+name+": "+error.Message);}
        }
        Character Player(string cls,double resource=0)=>new(){Class=cls,ClassResource=resource,Health=100,Mana=100,Stamina=100,LastCombat=0};

        Test("all eight classes expose distinct visible combat resources",()=>
        {
            Need(data.Classes.Count==8,"Expected exactly eight classes.");
            var names=data.Classes.Select(x=>ClassCombatRules.ResourceName(x.Id)).ToArray();
            Need(names.Distinct(StringComparer.Ordinal).Count()==8,"Class resource names are not distinct.");
            foreach(var cls in data.Classes)
            {
                string resource=ClassCombatRules.ResourceName(cls.Id);
                Need(cls.Passive.Contains(resource,StringComparison.Ordinal),cls.Id+" character-creation passive does not explain "+resource+".");
                Need(ClassCombatRules.ReadyThreshold(cls.Id) is >=40 and <=60,cls.Id+" has an invalid empowered threshold.");
            }
        });

        Test("martial identities build resource from their intended combat behavior",()=>
        {
            var v=Player("vanguard");ClassCombatRules.RecordIncoming(v,20,8,true,false);Need(v.ClassResource>=20,"Vanguard did not build Resolve from a block.");
            var b=Player("berserker");ClassCombatRules.RecordDamage(b,20,Element.Physical,"axe_mastery",1.5);ClassCombatRules.RecordIncoming(b,10,5,false,false);Need(b.ClassResource>=14,"Berserker did not build Fury from trading damage.");
            var r=Player("ranger");ClassCombatRules.RecordDamage(r,20,Element.Physical,"archery",7.5);Need(r.ClassResource>=15,"Ranger did not build Focus at long range.");
            var q=Player("rogue");ClassCombatRules.RecordDamage(q,20,Element.Physical,"dagger_mastery",1.5);ClassCombatRules.RecordIncoming(q,0,0,false,true);Need(q.ClassResource>=24,"Rogue did not build Momentum from close pressure and an evade.");
        });

        Test("caster support and hybrid identities have distinct build-spend loops",()=>
        {
            var a=Player("arcanist");ClassCombatRules.RecordDamage(a,20,Element.Fire,"pyromancy",5);Need(a.ClassResource==12,"Arcanist Resonance gain changed.");
            var w=Player("warden");var heal=data.Abilities.First(x=>x.Class=="warden"&&x.Kind=="heal");ClassCombatRules.RecordCast(w,heal,true);Need(w.ClassResource==18,"Warden support did not build Bond.");
            var t=Player("templar");var ward=data.Abilities.First(x=>x.Class=="templar"&&x.Kind=="shield");ClassCombatRules.RecordCast(t,ward,true);ClassCombatRules.RecordDamage(t,10,Element.Radiant,"radiance",2);Need(t.ClassResource>=28,"Templar did not build Conviction through support plus Radiant pressure.");
            var s=Player("spellblade");ClassCombatRules.RecordDamage(s,10,Element.Arcane,"runecasting",2);double first=s.ClassResource;ClassCombatRules.RecordDamage(s,10,Element.Physical,"swordsmanship",2);Need(first==5&&s.ClassResource==30&&s.ClassState=="martial","Spellblade did not reward alternating forms.");
        });

        Test("native empowered techniques consume class resource without banning cross-class skills",()=>
        {
            foreach(var cls in data.Classes)
            {
                var p=Player(cls.Id,100); if(cls.Id=="spellblade")p.ClassState="magic";
                var ability=cls.Id switch
                {
                    "vanguard"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="shield"),
                    "berserker"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    "ranger"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="projectile"),
                    "rogue"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    "arcanist"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="projectile"),
                    "warden"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="shield"),
                    "templar"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    _=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike")
                };
                var bonus=ClassCombatRules.PrepareCast(p,ability,false);Need(bonus.Empowered&&p.ClassResource<100,cls.Id+" did not consume its ready resource.");
            }
            var cross=Player("vanguard",100);var foreign=data.Abilities.First(x=>x.Class=="arcanist"&&x.Kind=="projectile");var before=cross.ClassResource;
            var foreignBonus=ClassCombatRules.PrepareCast(cross,foreign,false);Need(!foreignBonus.Empowered&&cross.ClassResource==before,"Using trained off-class magic consumed Vanguard Resolve.");
        });

        Test("real RealmEngine casts exercise every class identity",()=>
        {
            string[] classes=["vanguard","berserker","ranger","rogue","arcanist","warden","templar","spellblade"];
            foreach(string cls in classes)
            {
                var realm=new RealmEngine(data);var p=realm.CreateCharacter("class-identity-"+cls,"Identity "+cls,cls,new());realm.Active.Add(p.Id);
                var zone=data.Zone(p.Zone);p.Position=zone.Spawn;p.ClassResource=100;if(cls=="spellblade")p.ClassState="magic";
                var ability=cls switch
                {
                    "vanguard"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="shield"),
                    "berserker"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    "ranger"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="projectile"),
                    "rogue"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    "arcanist"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="projectile"),
                    "warden"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="shield"),
                    "templar"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    _=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike")
                };
                p.SkillXp[ability.Skill]=Progression.Threshold(ability.Requirement);p.Mana=100000;p.Stamina=100000;
                string target="";Point aim=p.Position;
                if(ability.Kind is "strike" or "projectile" or "dot" or "drain" or "interrupt")
                {
                    var definition=data.Mob("field_rat");var at=WorldMap.FindFree(zone,new(p.Position.X+1,p.Position.Y));
                    target="identity-target-"+cls;realm.State.Creatures[target]=new(){Id=target,Template=definition.Id,Zone=p.Zone,Position=at,Home=at,Health=definition.Health};aim=at;
                }
                double before=p.ClassResource;
                var result=realm.Execute(p.Id,new GameCommand{Kind="cast",Item=ability.Id,Target=target,X=aim.X,Y=aim.Y,Sequence=p.LastAction+1});
                Need(result.Ok,cls+" representative technique failed: "+result.Message);Need(p.ClassResource<before,cls+" representative technique did not spend its ready resource.");
            }
        });

        Test("class resource is save-safe bounded and decays outside combat",()=>
        {
            var p=Player("spellblade",100);p.ClassState="magic";p.LastCombat=0;ClassCombatRules.Tick(p,1,20);Need(p.ClassResource==88,"Out-of-combat decay changed.");
            var copy=Wire.Copy(p);Need(copy.ClassResource==88&&copy.ClassState=="magic","Class identity state did not survive serialization.");
            copy.ClassResource=double.NaN;ClassCombatRules.Normalize(copy);Need(copy.ClassResource==0,"Non-finite class resource did not fail closed.");
            ClassCombatRules.Tick(copy,20,40);Need(copy.ClassResource==0&&copy.ClassState=="","Empty Spellweave did not clear its alternating-form state.");
        });

        Test("client exposes meter buffering and authoritative impact feedback",()=>
        {
            string root=Directory.GetCurrentDirectory();
            string experience=File.ReadAllText(Path.Combine(root,"client/Scripts/GameRoot.Experience.cs"));
            string game=File.ReadAllText(Path.Combine(root,"client/Scripts/GameRoot.cs"));
            string world=File.ReadAllText(Path.Combine(root,"client/Scripts/WorldView.cs"));
            string audio=File.ReadAllText(Path.Combine(root,"client/Scripts/ClientAudio.cs"));
            Need(experience.Contains("ClassResourceHud",StringComparison.Ordinal)&&experience.Contains("READY",StringComparison.Ordinal),"Class meter is not visible in the combat HUD.");
            Need(game.Contains("AbilityBufferSeconds = .35",StringComparison.Ordinal)&&game.Contains("TickAbilityBuffer",StringComparison.Ordinal),"Short ability input buffer is absent.");
            Need(world.Contains("CombatImpact",StringComparison.Ordinal)&&world.Contains("ClassBurst",StringComparison.Ordinal),"Impact shake/class burst presentation is absent.");
            Need(audio.Contains("class_ready",StringComparison.Ordinal)&&audio.Contains("class_release",StringComparison.Ordinal)&&audio.Contains("impact",StringComparison.Ordinal),"Combat feedback audio cues are absent.");
        });

        Console.WriteLine($"CLASS COMBAT IDENTITY: {passed} groups passed; total failures {failures.Count}.");
    }
}
