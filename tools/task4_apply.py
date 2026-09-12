#!/usr/bin/env python3
"""One-shot Task #4 integration patch. Removed by its publication workflow."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace_once(rel,old,new):
    path=ROOT/rel
    text=path.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{rel}: expected one patch anchor, found {count}: {old[:90]!r}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

def replace_all(rel,old,new,minimum=1):
    path=ROOT/rel
    text=path.read_text(encoding='utf-8')
    count=text.count(old)
    if count<minimum:
        raise RuntimeError(f'{rel}: expected at least {minimum} patch anchors, found {count}: {old[:90]!r}')
    path.write_text(text.replace(old,new),encoding='utf-8')

# Generated content pass runs after equipment progression, so it can safely attach behavior
# metadata without weakening the existing base-tier identity contract.
replace_once('tools/build_content.py',
    'from content_src import skills, items, abilities, mobs, boss_uniques, world, exploration_rewards, quests, presentation, gear_progression',
    'from content_src import skills, items, abilities, mobs, boss_uniques, world, exploration_rewards, quests, presentation, gear_progression, build_defining_loot')
replace_once('tools/build_content.py',
    'for module in [skills,items,abilities,mobs,boss_uniques,world,exploration_rewards,quests,presentation,gear_progression]: module.build(data)',
    'for module in [skills,items,abilities,mobs,boss_uniques,world,exploration_rewards,quests,presentation,gear_progression,build_defining_loot]: module.build(data)')

# Core derived stats ignore effect identifiers as numeric rows and then apply their bounded,
# authored behavior. Rare+ ordinary equipment receives one conditional behavior roll.
replace_once('src/Kairnfall.Core/Mechanics.cs',
    '            foreach(var affix in item.Affixes) Add(affix.Stat,affix.Value);',
    '            foreach(var affix in item.Affixes) if(!BuildDefiningLoot.IsEffectAffix(affix)) Add(affix.Stat,affix.Value);')
replace_once('src/Kairnfall.Core/Mechanics.cs',
'''            foreach(var rune in item.Runes)
            {
                var rd=data.Item(rune.Template);
                foreach(var stat in rd.Stats) Add(stat.Key,stat.Value);
            }
        }
        double v=''',
'''            foreach(var rune in item.Runes)
            {
                var rd=data.Item(rune.Template);
                foreach(var stat in rd.Stats) Add(stat.Key,stat.Value);
            }
        }
        BuildDefiningLoot.ApplyDynamicStats(p,data,Add);
        double v=''')
replace_once('src/Kairnfall.Core/Mechanics.cs',
'''                item.Affixes.Add(new(){Name=key.Replace('_',' '),Stat=key,Value=1+Math.Round((def.Requirement/6.0+2)*CombatMath.RandomUnit(),1)});
            }
        }
        return item;''',
'''                item.Affixes.Add(new(){Name=key.Replace('_',' '),Stat=key,Value=1+Math.Round((def.Requirement/6.0+2)*CombatMath.RandomUnit(),1)});
            }
            if(BuildDefiningLoot.RollConditionalAffix(def,item.Rarity) is { } special) item.Affixes.Add(special);
        }
        return item;''')
replace_once('src/Kairnfall.Core/Mechanics.cs',
'''            if(def is null||i.Quantity<1||i.Quantity>def.StackMax||i.Sockets<0||i.Sockets>4||i.Runes.Count>i.Sockets||i.Durability<0||i.Durability>100) errors.Add("Invalid item: "+i.Id);
            if(i.SkillBonuses.Any''',
'''            if(def is null||i.Quantity<1||i.Quantity>def.StackMax||i.Sockets<0||i.Sockets>4||i.Runes.Count>i.Sockets||i.Durability<0||i.Durability>100) errors.Add("Invalid item: "+i.Id);
            if(def is not null) BuildDefiningLoot.ValidateItem(i,def,data,errors);
            if(i.SkillBonuses.Any''')

replace_once('src/Kairnfall.Core/EquipmentComparison.cs',
    '        foreach (var affix in item.Affixes) Add(affix.Stat, affix.Value);',
    '        foreach (var affix in item.Affixes) if (!BuildDefiningLoot.IsEffectAffix(affix)) Add(affix.Stat, affix.Value);')

# Rune conversion affects actual offensive damage element, while ClassCombatRules still receives
# the authored ability definition. Loot therefore cannot spoof or spend another class engine.
combat_path=ROOT/'src/Kairnfall.Core/RealmCombat.cs'
combat=combat_path.read_text(encoding='utf-8')
start=combat.index('    private string Cast(Character p,string abilityId,string target,Point location)')
end=combat.index('    private double HitCreature(Character p,Creature mob,double raw,Element element,string skill)')
segment=combat[start:end]
anchor='        var classBonus=ClassCombatRules.PrepareCast(p,ability,stealthed);\n'
if segment.count(anchor)!=1: raise RuntimeError('RealmCombat Cast class-bonus anchor changed')
segment=segment.replace(anchor,anchor+'        Element castElement=BuildDefiningLoot.AbilityElement(p,ability,Data);\n',1)
segment=segment.replace('ability.Element','castElement')
segment=segment.replace('double basePower=(castElement==Element.Physical?stats.Physical:stats.Spell)*ability.Power;',
                        'double basePower=(ability.Element==Element.Physical?stats.Physical:stats.Spell)*ability.Power;',1)
combat=combat[:start]+segment+combat[end:]
hit='        var def=Data.Mob(mob.Template); var stats=CombatMath.Stats(p,Data);\n'
if combat.count(hit)!=1: raise RuntimeError('RealmCombat HitCreature anchor changed')
combat=combat.replace(hit,hit+'        raw*=BuildDefiningLoot.TargetDamageMultiplier(p,mob,def,Data,State.Time);\n',1)
combat_path.write_text(combat,encoding='utf-8')

# Craft specialization uses the already-present GameCommand.Arg field. Reforge gets one explicit
# authoritative command and reuses existing request receipts for replay safety.
replace_once('src/Kairnfall.Core/RealmEngine.cs','            case "craft": return Craft(p,c.Item,c.Amount);','            case "craft": return Craft(p,c.Item,c.Amount,c.Arg);')
replace_once('src/Kairnfall.Core/RealmEngine.cs','            case "unsocket": return Unsocket(p,c.Target,c.Amount);','            case "unsocket": return Unsocket(p,c.Target,c.Amount);\n            case "reforge": return Reforge(p,c.Item,c.Amount);')

replace_once('src/Kairnfall.Core/RealmEconomy.cs','    private string Craft(Character p,string id,int quantity)','    private string Craft(Character p,string id,int quantity,string specialization)')
replace_once('src/Kairnfall.Core/RealmEconomy.cs',
'''        Need(Progression.Level(p,recipe.Skill)>=recipe.Requirement,"Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".");
        Need(AtStation(p,recipe.Station),"Use the "+recipe.Station+" station.");''',
'''        Need(Progression.Level(p,recipe.Skill)>=recipe.Requirement,"Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".");
        string specializationProblem=BuildDefiningLoot.CraftSpecializationProblem(p,recipe,specialization,Data);
        Need(specializationProblem=="",specializationProblem);
        Need(AtStation(p,recipe.Station),"Use the "+recipe.Station+" station.");''')
replace_once('src/Kairnfall.Core/RealmEconomy.cs',
'''                var rarity=Items.RollCraftRarity(Progression.Level(p,recipe.Skill),recipe.Requirement);
                Items.Add(p.Inventory,Items.Create(Data,output.Id,1,rarity,p),Data);''',
'''                var rarity=Items.RollCraftRarity(Progression.Level(p,recipe.Skill),recipe.Requirement);
                var crafted=Items.Create(Data,output.Id,1,rarity,p);
                BuildDefiningLoot.ApplyCraftSpecialization(crafted,p,recipe,specialization,Data);
                Items.Add(p.Inventory,crafted,Data);''')
replace_once('src/Kairnfall.Core/RealmEconomy.cs','    private string Salvage(Character p,string id)\n    {',
'''    private string Reforge(Character p,string id,int index)
    {
        var item=Items.Owned(p,id);var def=Data.Item(item.Template);
        Need(def.Slot!=""&&def.StackMax==1,"Only equipment affixes can be reforged.");
        Need(!Items.Equipped(p,id),"Unequip this item before reforging it.");
        Need(index>=0&&index<item.Affixes.Count&&BuildDefiningLoot.CanReforgeAffix(item.Affixes[index]),"Choose a reforgeable affix.");
        Need(NearService(p,"enchanter")||AtStation(p,"rune_table"),"Visit an enchanter or rune table to reforge equipment.");
        long gold=BuildDefiningLoot.ReforgeGoldCost(item,def);int dust=BuildDefiningLoot.ReforgeDustCost(item,def);
        Need(Items.Count(p,"rune_dust")>=dust,$"Reforging requires {dust} Rune Dust.");
        Ready(p,"reforge",0.8);Items.Spend(p,gold);Items.Consume(p,"rune_dust",dust);
        BuildDefiningLoot.RerollAffix(item,index,def);
        return $"Reforged one affix for {gold} gold and {dust} Rune Dust. All other affixes remained locked.";
    }
    private string Salvage(Character p,string id)
    {''')

# Item cards render build effects as first-class text rather than fake stat rows.
replace_once('client/Scripts/CompactItemCard.cs',
'''        var metadata = Centered(item.Rarity + " · " + Ui.Words(def.Type) + rolledMeta + (self is not null && Items.Equipped(self, item.Id) ? " · Equipped" : ""), metaSize, Ui.Muted);''',
'''        string identity=item.Rarity+(def.Tags.Contains("boss_unique",StringComparer.Ordinal)?" · Signature":def.Tags.Any(x=>x.StartsWith("set:",StringComparison.Ordinal))?" · Set piece":"");
        var metadata = Centered(identity + " · " + Ui.Words(def.Type) + rolledMeta + (self is not null && Items.Equipped(self, item.Id) ? " · Equipped" : ""), metaSize, Ui.Muted);''')
replace_once('client/Scripts/CompactItemCard.cs',
'''        foreach (string notice in notices)
        {
            var label = Centered(notice, metaSize, Ui.Gold);
            label.Name = "ItemNotice";
            box.AddChild(label);
        }

        if (def.Slot != "" || def.Type == "tool")''',
'''        foreach (string notice in notices)
        {
            var label = Centered(notice, metaSize, Ui.Gold);
            label.Name = "ItemNotice";
            box.AddChild(label);
        }

        var buildLines=BuildDefiningLoot.TooltipLines(item,def,data,self);
        foreach(string line in (compact?buildLines.Take(1):buildLines))
        {
            var effect=Centered(line,metaSize,Ui.Gold);
            effect.Name="ItemBuildEffect";box.AddChild(effect);
        }

        if (def.Slot != "" || def.Type == "tool")''')

# Crafting panel: one explicit finish selector, kept outside the scroll region with the existing
# primary action. Locked mastery choices remain visible and explain their skill gate.
replace_once('client/Scripts/CraftingGuidePanel.cs','    public Action<string,int>? CraftRequested { get; set; }','    public Action<string,int,string>? CraftRequested { get; set; }')
replace_once('client/Scripts/CraftingGuidePanel.cs','    private readonly List<string> professions=[];','    private readonly List<string> professions=[];\n    private readonly List<string> specializationIds=[];')
replace_once('client/Scripts/CraftingGuidePanel.cs','    private OptionButton profession=null!, learned=null!;','    private OptionButton profession=null!, learned=null!, specialization=null!;')
replace_once('client/Scripts/CraftingGuidePanel.cs',
'''        readiness=Ui.Label("",compactHeight?13:14,Ui.Danger,true); readiness.Name="CraftReadiness"; inspector.AddChild(readiness);
        var actions=Ui.Row(inspector); actions.AddChild(Ui.Label("Batches",compactHeight?13:14,Ui.Muted));''',
'''        readiness=Ui.Label("",compactHeight?13:14,Ui.Danger,true); readiness.Name="CraftReadiness"; inspector.AddChild(readiness);
        var finish=Ui.Row(inspector);finish.AddChild(Ui.Label("Finish",compactHeight?13:14,Ui.Muted));
        specialization=new OptionButton{Name="CraftSpecialization",SizeFlagsHorizontal=SizeFlags.ExpandFill};finish.AddChild(specialization);
        var actions=Ui.Row(inspector); actions.AddChild(Ui.Label("Batches",compactHeight?13:14,Ui.Muted));''')
replace_once('client/Scripts/CraftingGuidePanel.cs',
    'search.TextChanged-=SearchChanged; profession.ItemSelected-=FilterChanged; learned.ItemSelected-=FilterChanged; amount.ValueChanged-=AmountChanged; connected=false;',
    'search.TextChanged-=SearchChanged; profession.ItemSelected-=FilterChanged; learned.ItemSelected-=FilterChanged; specialization.ItemSelected-=SpecializationChanged; amount.ValueChanged-=AmountChanged; connected=false;')
replace_once('client/Scripts/CraftingGuidePanel.cs',
    'search.TextChanged+=SearchChanged; profession.ItemSelected+=FilterChanged; learned.ItemSelected+=FilterChanged; amount.ValueChanged+=AmountChanged; connected=true;',
    'search.TextChanged+=SearchChanged; profession.ItemSelected+=FilterChanged; learned.ItemSelected+=FilterChanged; specialization.ItemSelected+=SpecializationChanged; amount.ValueChanged+=AmountChanged; connected=true;')
replace_once('client/Scripts/CraftingGuidePanel.cs','    private void AmountChanged(double _) => RefreshDetails();','    private void AmountChanged(double _) => RefreshDetails();\n    private void SpecializationChanged(long _) => RefreshDetails();')
replace_once('client/Scripts/CraftingGuidePanel.cs','    private int Batches => Math.Clamp((int)amount.Value,1,20);',
'''    private int Batches => Math.Clamp((int)amount.Value,1,20);
    private string CurrentSpecialization => specializationIds.Count==0||specialization.Selected<0||specialization.Selected>=specializationIds.Count?"":specializationIds[specialization.Selected];
    private void RefreshSpecializations(Character? self,RecipeDef? recipe)
    {
        string prior=CurrentSpecialization;specialization.Clear();specializationIds.Clear();
        if(recipe is null){specialization.AddItem("Standard finish");specializationIds.Add("");return;}
        foreach(var choice in BuildDefiningLoot.CraftSpecializations(recipe,Data))
        {
            bool locked=self is not null&&Progression.Level(self,recipe.Skill)<choice.Requirement;
            specialization.AddItem(choice.Name+(locked?$" · skill {choice.Requirement}":""));specializationIds.Add(choice.Id);
        }
        int selected=Math.Max(0,specializationIds.IndexOf(prior));specialization.Select(selected);
    }''')
replace_once('client/Scripts/CraftingGuidePanel.cs',
'''        if(Progression.Level(self,recipe.Skill)<recipe.Requirement) return "Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".";
        bool structure=Data.Item(recipe.Output).Type=="structure";''',
'''        if(Progression.Level(self,recipe.Skill)<recipe.Requirement) return "Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".";
        string specializationProblem=BuildDefiningLoot.CraftSpecializationProblem(self,recipe,CurrentSpecialization,Data);
        if(specializationProblem!="") return specializationProblem;
        bool structure=Data.Item(recipe.Output).Type=="structure";''')
replace_once('client/Scripts/CraftingGuidePanel.cs','        var self=ReadCharacter(); var recipe=Data.Recipes.FirstOrDefault(r=>r.Id==SelectedRecipe);',
    '        var self=ReadCharacter(); var recipe=Data.Recipes.FirstOrDefault(r=>r.Id==SelectedRecipe);\n        RefreshSpecializations(self,recipe);')
replace_once('client/Scripts/CraftingGuidePanel.cs',
'''        requirement.Text=Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+" · "+Ui.Words(recipe.Station)+
            "\\nOutput: "+checked(recipe.Quantity*quantity)+" · Base skill XP per batch: "+recipe.Xp+''',
'''        var finishChoice=BuildDefiningLoot.CraftSpecializations(recipe,Data).First(x=>x.Id==CurrentSpecialization);
        requirement.Text=Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+" · "+Ui.Words(recipe.Station)+
            "\\nFinish: "+finishChoice.Name+" · "+finishChoice.Description+
            "\\nOutput: "+checked(recipe.Quantity*quantity)+" · Base skill XP per batch: "+recipe.Xp+''')
replace_once('client/Scripts/CraftingGuidePanel.cs','        else { if(CraftRequested is null) return false; CraftRequested(recipe.Id,Batches); }',
    '        else { if(CraftRequested is null) return false; CraftRequested(recipe.Id,Batches,CurrentSpecialization); }')
replace_once('client/Scripts/GameRoot.Panels.cs','            CraftRequested=(id,batches)=>Send("craft",item:id,amount:batches),','            CraftRequested=(id,batches,specialization)=>Send("craft",item:id,amount:batches,arg:specialization),')

# Reforge actions live alongside rune extraction/reclaim and require explicit confirmation.
replace_once('client/Scripts/GameRoot.Inventory.cs',
'''        foreach (var affix in item.Affixes) text.AppendLine($"{affix.Value:+0.0;-0.0;0} {Ui.Words(affix.Stat)}");''',
'''        foreach (var affix in item.Affixes)
            if(BuildDefiningLoot.IsEffectAffix(affix)) text.AppendLine((affix.Name.StartsWith("Crafted:",StringComparison.Ordinal)?"Crafted specialization: ":"Conditional affix: ")+BuildDefiningLoot.EffectDescription(BuildDefiningLoot.EffectId(affix)));
            else text.AppendLine($"{affix.Value:+0.0;-0.0;0} {Ui.Words(affix.Stat)}");''')
replace_once('client/Scripts/GameRoot.Inventory.cs',
'''        if(CraftEconomy.Reclaim(Data,item) is { } reclaim)
        {''',
'''        if(def.Slot!=""&&item.Affixes.Any(BuildDefiningLoot.CanReforgeAffix))
        {
            for(int i=0;i<item.Affixes.Count;i++)
            {
                int index=i;if(!BuildDefiningLoot.CanReforgeAffix(item.Affixes[index]))continue;
                long gold=BuildDefiningLoot.ReforgeGoldCost(item,def);int dust=BuildDefiningLoot.ReforgeDustCost(item,def);
                bool blocked=Items.Equipped(self,item.Id)||(!NearRole("enchanter")&&!ClientAtStation("rune_table"))||self.Gold<gold||Items.Count(self,"rune_dust")<dust;
                string affixName=item.Affixes[index].Name;
                parent.AddChild(Ui.Button($"Reforge {affixName} · {gold:N0} gold + {dust} Rune Dust",()=>Confirm("Reforge affix",$"Replace {affixName}? Every other affix stays locked. Cost: {gold:N0} gold and {dust} Rune Dust.",()=>Send("reforge",item:item.Id,amount:index)),blocked));
            }
        }
        if(CraftEconomy.Reclaim(Data,item) is { } reclaim)
        {''')

# Native crafting fixture records the specialization argument and keeps standard crafting exact.
replace_once('client/Tests/CraftingGuideChecks.cs',
    '            var requests=new List<(string Id,int Batches)>(); panel.CraftRequested=(id,batches)=>requests.Add((id,batches));',
    '            var requests=new List<(string Id,int Batches,string Specialization)>(); panel.CraftRequested=(id,batches,specialization)=>requests.Add((id,batches,specialization));')
replace_once('client/Tests/CraftingGuideChecks.cs',
    '            check(requests.Count==1 && requests[0]==(recipe.Id,2),"Native Craft requests the selected recipe and batch count exactly once");',
    '            check(requests.Count==1 && requests[0]==(recipe.Id,2,""),"Native Craft requests the selected recipe, batch count, and standard finish exactly once");')

# Native item-card contract explicitly verifies build-effect rendering for signatures and sets.
replace_once('client/Tests/CompactItemCardContract.cs','            var longData = Wire.Copy(data);',
'''            var signatureDef=data.Items.First(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal));
            var signatureItem=Items.Create(data,signatureDef.Id,1,Rarity.Relic);
            var signatureCard=CompactItemCard.Create(data,null,signatureItem,null,false,false);
            try
            {
                await Layout(signatureCard,new Vector2(8,8));
                var effects=signatureCard.FindChildren("ItemBuildEffect","Label",true,false).OfType<Label>().ToArray();
                Need(effects.Any(x=>x.Text.Contains("SIGNATURE EFFECT",StringComparison.Ordinal)),"Full signature item card renders its authored special effect");
                Need(effects.Any(x=>x.Text.Contains("TARGET FARM",StringComparison.Ordinal)),"Full signature item card renders its boss source");
            }
            finally { Release(signatureCard); }

            var longData = Wire.Copy(data);''')

# World probe owns the permanent Task #4 suite.
replace_once('tools/world_probe/Program.cs','SocialCooperationChecks.Run(catalog,failures);\nExplorationRewardChecks.Run(catalog,failures);',
    'SocialCooperationChecks.Run(catalog,failures);\nBuildDefiningLootChecks.Run(catalog,failures);\nExplorationRewardChecks.Run(catalog,failures);')

# Correct two intentionally strict source expressions before compilation.
replace_once('src/Kairnfall.Core/BuildDefiningLoot.cs',
    '        if(def.Effect!=""&&def.Type is "weapon" or "offhand" or "rune"&& !KnownEffect(def.Effect))',
    '        if(def.Effect!=""&&(def.Type is "weapon" or "offhand" or "rune")&&!KnownEffect(def.Effect))')
replace_once('tools/world_probe/BuildDefiningLootChecks.cs',
    '            var ability=data.Abilities.First(x=>x.Kind is "strike" or "projectile" or "area"&&x.Element!=Element.Physical);',
    '            var ability=data.Abilities.First(x=>(x.Kind is "strike" or "projectile" or "area")&&x.Element!=Element.Physical);')
replace_once('tools/world_probe/BuildDefiningLootChecks.cs','        Console.WriteLine($"BUILD DEFINING LOOT: {passed}/14 groups passed.");','        Console.WriteLine($"BUILD DEFINING LOOT: {passed}/15 groups passed.");')

print('Task #4 integration patch applied.')
