"""Authored class kits. Rows select different targeting and effect contracts."""
import re

# name, skill, requirement, behavior, element, tactical purpose
KITS = {
'vanguard': [
 ('Shield Breaker','swordsmanship',1,'strike','Physical','A close strike against one foe.'),
 ('Brace','shield_mastery',1,'shield','Physical','Absorb the next incoming damage.'),
 ('Challenge','shield_mastery',1,'taunt','Physical','Force nearby enemies to focus on you and reduce incoming damage.'),
 ('Measured Advance','swordsmanship',5,'dash','Physical','Move through a clear lane and strike at its end.'),
 ('Sweeping Guard','swordsmanship',10,'cone','Physical','Sweep a forward cone without hitting enemies behind you.'),
 ('Shield Bell','shield_mastery',15,'interrupt','Physical','Interrupt a nearby creature before its telegraph resolves.'),
 ('Iron Resolve','heavy_armor',20,'buff','Physical','Temporarily reduce incoming damage.'),
 ('Linebreaker','spear_mastery',25,'line','Physical','Strike along a narrow forward lane.'),
 ('Rallying Breath','restoration',30,'heal','Radiant','Restore health to yourself or an injured party member.'),
 ('Stone Circle','geomancy',35,'area','Physical','Strike a chosen area after a short warning.'),
 ('Unbroken Wall','shield_mastery',40,'shield','Physical','Create a larger, longer-lived absorption shield.'),
 ('Sentinel Pursuit','swordsmanship',50,'dash','Physical','Close a longer gap without crossing solid terrain.'),
 ('King\'s Rebuke','mace_mastery',60,'interrupt','Physical','Interrupt an enemy attack at greater range.'),
 ('Hold the Gate','shield_mastery',75,'taunt','Physical','Draw a wider group of enemies into defensive combat.'),
 ('Last Bastion','heavy_armor',90,'shield','Radiant','Create an emergency barrier with a long recovery time.')],
'berserker': [
 ('Rending Chop','axe_mastery',1,'dot','Physical','Wound one target and apply bleeding.'),
 ('Reckless Roar','endurance',1,'buff','Physical','Increase outgoing damage for a short burst.'),
 ('Crushing Blow','mace_mastery',1,'strike','Physical','Deliver a slow heavy strike.'),
 ('Wild Leap','axe_mastery',5,'dash','Physical','Leap along a clear path and strike the landing area.'),
 ('Butcher\'s Arc','axe_mastery',10,'cone','Physical','Cleave a forward arc.'),
 ('Blood Draught','shadow_magic',15,'drain','Shadow','Steal a portion of the damage dealt as health.'),
 ('Defiant Hide','medium_armor',20,'shield','Physical','Absorb damage while preparing another attack.'),
 ('Groundsplitter','mace_mastery',25,'line','Physical','Slam a narrow line through a pack.'),
 ('Howling Challenge','endurance',30,'taunt','Physical','Pull nearby threats away from allies.'),
 ('Hamstring','axe_mastery',35,'dot','Physical','Apply a bleeding wound and stop a short advance.'),
 ('War Tempo','axe_mastery',40,'buff','Physical','Sustain an offensive burst.'),
 ('Tremor','geomancy',50,'area','Physical','Break up enemies gathered at a selected point.'),
 ('Skull Rattle','mace_mastery',60,'interrupt','Physical','Stop a creature\'s wind-up.'),
 ('Crimson Reaping','shadow_magic',75,'drain','Shadow','Recover health through a high-cost draining strike.'),
 ('Ruinous Wake','axe_mastery',90,'field','Physical','Leave repeated damaging pulses at a chosen point.')],
'ranger': [
 ('Aimed Arrow','archery',1,'projectile','Physical','Fire a delayed projectile at a target position.'),
 ('Bramble Snare','nature_magic',1,'dot','Nature','Root a target briefly.'),
 ('Hunter\'s Step','hunting',1,'dash','Physical','Move through a clear escape lane.'),
 ('Fan of Arrows','archery',5,'cone','Physical','Cover a forward firing arc.'),
 ('Pinning Bolt','crossbow_mastery',10,'projectile','Physical','Deliver a slow, high-impact ranged shot.'),
 ('Field Dressing','restoration',15,'heal','Nature','Treat an injured ally or yourself.'),
 ('Camouflage','hunting',20,'stealth','Nature','Hide from new enemy detection until attacking or taking damage.'),
 ('Splinter Line','archery',25,'line','Physical','Fire along a narrow lane through clustered creatures.'),
 ('Venom Shot','shadow_magic',30,'dot','Poison','Apply stacking poison to a selected foe.'),
 ('Windward Guard','light_armor',35,'shield','Nature','Absorb an approaching hit.'),
 ('Hawk Cry','hunting',40,'interrupt','Physical','Interrupt a distant creature.'),
 ('Stormfletch','stormcalling',50,'projectile','Lightning','Send a lightning projectile into wet or stormy terrain.'),
 ('Wild Companion','summoning',60,'summon','Nature','Call an animal companion that follows your attacks.'),
 ('Arrowfall','archery',75,'field','Physical','Sustain a targeted area barrage.'),
 ('Heartwood Refuge','nature_magic',90,'shield','Nature','Raise a large defensive barrier.')],
'rogue': [
 ('Backcut','dagger_mastery',1,'strike','Physical','Deliver a fast close-range attack.'),
 ('Venom Edge','shadow_magic',1,'dot','Poison','Apply poison that continues after the strike.'),
 ('Slip Away','evasion',1,'dash','Physical','Move quickly along an unobstructed escape path.'),
 ('Smoke Veil','shadow_magic',5,'stealth','Shadow','Break visual detection before choosing another target.'),
 ('Throat Tap','dagger_mastery',10,'interrupt','Physical','Stop a hostile cast at close range.'),
 ('Knife Fan','dagger_mastery',15,'cone','Physical','Strike several creatures in a forward cone.'),
 ('Leeching Cut','shadow_magic',20,'drain','Shadow','Recover some health from damage dealt.'),
 ('Quick Guard','light_armor',25,'shield','Physical','Absorb a hit without wearing heavy armor.'),
 ('Needle Cast','dagger_mastery',30,'projectile','Poison','Throw a poisoned blade toward a selected enemy.'),
 ('Opening Mark','dagger_mastery',35,'dot','Arcane','Expose an enemy to additional damage.'),
 ('Night Crossing','shadow_magic',40,'dash','Shadow','Cross a longer clear gap.'),
 ('Black Lotus','shadow_magic',50,'field','Poison','Poison creatures that remain in the selected area.'),
 ('Stolen Breath','shadow_magic',60,'drain','Shadow','Drain a large amount of life at a high mana cost.'),
 ('Silencing Needle','dagger_mastery',75,'interrupt','Poison','Interrupt a dangerous ranged attacker.'),
 ('Master\'s Disappearance','evasion',90,'stealth','Shadow','Maintain a long concealment window without attacking.')],
'arcanist': [
 ('Ember Lance','pyromancy',1,'projectile','Fire','Launch fire at a target position and apply burning on impact.'),
 ('Frost Needle','cryomancy',1,'projectile','Frost','Chill an enemy to slow movement.'),
 ('Arcane Ward','arcane_magic',1,'shield','Arcane','Absorb damage while maintaining distance.'),
 ('Forked Spark','stormcalling',5,'line','Lightning','Strike along a narrow lightning lane.'),
 ('Cinder Ring','pyromancy',10,'area','Fire','Burn an area after a short casting warning.'),
 ('Icebound','cryomancy',15,'dot','Frost','Root a creature within casting range.'),
 ('Stone Pulse','geomancy',20,'cone','Physical','Push damage through a short earthen cone.'),
 ('Blink Step','arcane_magic',25,'dash','Arcane','Move through clear terrain without passing through walls.'),
 ('Null Word','arcane_magic',30,'interrupt','Arcane','Cancel a hostile telegraph before it resolves.'),
 ('Static Mantle','stormcalling',35,'shield','Lightning','Create a lightning absorption barrier.'),
 ('Searing Ground','pyromancy',40,'field','Fire','Maintain repeated damage in a selected area.'),
 ('Winter Front','cryomancy',50,'cone','Frost','Chill enemies in a broad forward arc.'),
 ('Prismatic Focus','arcane_magic',60,'buff','Arcane','Temporarily increase outgoing spell damage.'),
 ('Thunderfall','stormcalling',75,'area','Lightning','Call a high-cost lightning burst at range.'),
 ('Rift Collapse','arcane_magic',90,'field','Arcane','Create several pulses around a selected fracture point.')],
'warden': [
 ('Thorn Dart','nature_magic',1,'projectile','Nature','Strike from range with a chance to entangle.'),
 ('Mending Leaf','restoration',1,'heal','Nature','Restore an injured target and add regeneration.'),
 ('Call Companion','summoning',1,'summon','Nature','Call one companion that follows and attacks with you.'),
 ('Root Grasp','nature_magic',5,'dot','Nature','Stop one creature from advancing.'),
 ('Barkskin','medium_armor',10,'shield','Nature','Absorb damage with a living barrier.'),
 ('Briar Fan','nature_magic',15,'cone','Nature','Strike a forward spread of creatures.'),
 ('Spring Cleanse','restoration',20,'purge','Nature','Remove harmful poison, burning, curses, and roots.'),
 ('Deerbound','animal_handling',25,'dash','Nature','Reposition along a clear path.'),
 ('Predator\'s Focus','hunting',30,'buff','Nature','Increase damage for a short hunting window.'),
 ('Vine Circle','nature_magic',35,'area','Nature','Strike enemies at a chosen gathering point.'),
 ('Ancient Shelter','nature_magic',40,'shield','Nature','Raise a long-lived protective barrier.'),
 ('Feral Rebuke','animal_handling',50,'interrupt','Nature','Interrupt a creature before its attack completes.'),
 ('Renewal','restoration',60,'heal','Nature','Provide a strong heal and continued regeneration.'),
 ('Overgrowth','nature_magic',75,'field','Nature','Punish enemies that remain among repeated root eruptions.'),
 ('Guardian of the Bough','summoning',90,'summon','Nature','Call the strongest companion allowed by your Summoning skill.')],
'templar': [
 ('Oath Strike','mace_mastery',1,'strike','Radiant','Strike one creature with radiant force.'),
 ('Merciful Light','restoration',1,'heal','Radiant','Restore health to an injured target.'),
 ('Sanctuary Guard','shield_mastery',1,'shield','Radiant','Absorb incoming damage.'),
 ('Radiant Rebuke','radiance',5,'interrupt','Radiant','Interrupt an enemy attack.'),
 ('Consecrated Ground','radiance',10,'field','Radiant','Damage foes that remain in a sanctified area.'),
 ('Purifying Word','restoration',15,'purge','Radiant','Remove harmful conditions from yourself.'),
 ('Pilgrim\'s Advance','mace_mastery',20,'dash','Radiant','Advance along a clear lane and strike at the end.'),
 ('Beacon Arc','radiance',25,'cone','Radiant','Strike an arc of enemies with light.'),
 ('Take the Burden','shield_mastery',30,'taunt','Radiant','Draw nearby threats and gain temporary protection.'),
 ('Mending Prayer','restoration',35,'heal','Radiant','Combine direct healing with regeneration.'),
 ('Dawn Spear','radiance',40,'projectile','Radiant','Launch a ranged ray of light.'),
 ('Stone Oath','geomancy',50,'shield','Physical','Create a high-capacity defensive ward.'),
 ('Unyielding Verdict','mace_mastery',60,'line','Physical','Deliver a straight-lane weapon judgment.'),
 ('Great Benediction','restoration',75,'heal','Radiant','Deliver a high-cost emergency heal.'),
 ('Sunward Citadel','radiance',90,'shield','Radiant','Protect yourself with a large final ward.')],
'spellblade': [
 ('Runic Cut','swordsmanship',1,'strike','Arcane','Combine close weapon damage with arcane vulnerability.'),
 ('Elemental Edge','runecasting',1,'buff','Arcane','Empower outgoing attacks for a brief window.'),
 ('Phase Step','arcane_magic',1,'dash','Arcane','Reposition along a clear lane.'),
 ('Flame Trace','pyromancy',5,'line','Fire','Leave a straight line of fire damage.'),
 ('Frostguard','cryomancy',10,'shield','Frost','Absorb damage while holding your ground.'),
 ('Spell Sever','swordsmanship',15,'interrupt','Arcane','Cancel a creature\'s attack with a close strike.'),
 ('Storm Arc','stormcalling',20,'cone','Lightning','Strike a forward arc with lightning.'),
 ('Runic Siphon','runecasting',25,'drain','Arcane','Convert part of the strike into healing.'),
 ('Aether Javelin','arcane_magic',30,'projectile','Arcane','Launch an arcane projectile at range.'),
 ('Wardbreaker','runecasting',35,'dot','Arcane','Apply vulnerability to a durable target.'),
 ('Flame Landing','pyromancy',40,'dash','Fire','Dash into a small impact burst.'),
 ('Rune Field','runecasting',50,'field','Arcane','Create repeated pulses at a selected location.'),
 ('Mirror Guard','arcane_magic',60,'shield','Arcane','Absorb a large amount of incoming damage.'),
 ('Judgment of Elements','runecasting',75,'area','Lightning','Strike a selected area with a long-cooldown burst.'),
 ('Aetherwind Passage','swordsmanship',90,'line','Arcane','Cut through a long, narrow lane of enemies.')]
}

PROFILES = {
 'strike':dict(power=1.35,range=2.0,radius=0,mana=0,stamina=12,cooldown=3,duration=0,status=''),
 'dot':dict(power=0.8,range=6,radius=0,mana=10,stamina=3,cooldown=5,duration=5,status='bleed'),
 'drain':dict(power=1.3,range=5,radius=0,mana=16,stamina=0,cooldown=7,duration=0,status=''),
 'shield':dict(power=2.2,range=0,radius=0,mana=12,stamina=8,cooldown=12,duration=7,status='shield'),
 'taunt':dict(power=0,range=0,radius=5,mana=0,stamina=20,cooldown=12,duration=5,status='guard'),
 'buff':dict(power=0.25,range=0,radius=0,mana=12,stamina=5,cooldown=16,duration=8,status='empower'),
 'dash':dict(power=0.65,range=5,radius=1.4,mana=4,stamina=18,cooldown=8,duration=0,status=''),
 'cone':dict(power=1.2,range=5,radius=5,mana=12,stamina=8,cooldown=6,duration=0,status=''),
 'line':dict(power=1.55,range=7,radius=7,mana=15,stamina=10,cooldown=7,duration=0,status=''),
 'area':dict(power=1.65,range=7,radius=2.5,mana=20,stamina=0,cooldown=8,duration=0,status=''),
 'field':dict(power=0.9,range=7,radius=2.8,mana=26,stamina=0,cooldown=14,duration=5,status=''),
 'heal':dict(power=2.6,range=6,radius=0,mana=18,stamina=0,cooldown=6,duration=0,status=''),
 'projectile':dict(power=1.25,range=8,radius=0.9,mana=7,stamina=2,cooldown=2,duration=0,status=''),
 'interrupt':dict(power=0.6,range=3,radius=0,mana=8,stamina=12,cooldown=9,duration=2,status=''),
 'stealth':dict(power=0,range=0,radius=0,mana=8,stamina=10,cooldown=20,duration=10,status='stealth'),
 'purge':dict(power=0,range=0,radius=0,mana=18,stamina=0,cooldown=12,duration=0,status=''),
 'summon':dict(power=1,range=0,radius=0,mana=30,stamina=0,cooldown=30,duration=0,status='')
}

def slug(text): return re.sub('[^a-z0-9]+','_',text.lower()).strip('_')

def build(data):
    for cls,kit in KITS.items():
        entry=next(x for x in data['classes'] if x['id']==cls)
        for name,skill,level,kind,element,description in kit:
            ident=cls+'_'+slug(name); profile=PROFILES[kind].copy()
            if level>=75:
                if kind not in {'buff','stealth','taunt','purge','summon'}: profile['power']*=1.6
                profile['cooldown']*=2; profile['mana']*=1.6; profile['stamina']*=1.4
            if level>=40 and kind in {'dash','interrupt'}: profile['range']+=2
            if kind=='dot':
                profile['status']='poison' if element=='Poison' else 'root' if name in {'Bramble Snare','Icebound','Root Grasp','Hamstring'} else 'vulnerable' if element=='Arcane' else 'bleed'
                if profile['status']=='root': profile['duration']=2
            if name in {'Mending Leaf','Mending Prayer','Renewal','Great Benediction'}: profile['duration']=6
            if name=='Iron Resolve': profile['status']='guard'; profile['power']=0.3
            if cls in {'vanguard','berserker','rogue'} and kind=='projectile': profile['mana']=0; profile['stamina']=10
            if cls=='ranger' and element=='Physical': profile['mana']=0; profile['stamina']=12
            data['abilities'].append(dict(id=ident,name=name,**{'class':cls},skill=skill,requirement=level,kind=kind,element=element,description=description,**profile))
            entry['abilities'].append(ident)
    # Utility spells give the remaining magic and support skills valid actions.
    for name,skill,level,kind,element,description in [
      ('Runestone Spark','runecasting',1,'projectile','Arcane','Channel a small ranged rune bolt.'),
      ('Pebble Lance','geomancy',1,'line','Physical','Drive a narrow ridge of stone through a clear lane.'),
      ('Shared Mend','restoration',1,'heal','Radiant','Restore an injured party member or yourself.'),
      ('Kindled Palm','pyromancy',1,'cone','Fire','Project a short cone of flame.'),
      ('Cold Breath','cryomancy',1,'cone','Frost','Chill creatures in a short arc.'),
      ('Low Thunder','stormcalling',1,'area','Lightning','Strike a small selected area.'),
      ('Night Needle','shadow_magic',1,'projectile','Shadow','Curse a creature with a ranged strike.'),
      ('Dawn Thread','radiance',1,'projectile','Radiant','Launch a thread of radiant energy.'),
      ('Wild Thorn','nature_magic',1,'projectile','Nature','Attack from range with living thorns.'),
      ('Arcane Thread','arcane_magic',1,'projectile','Arcane','Expose a creature to arcane vulnerability.'),
      ('Call Familiar','summoning',1,'summon','Nature','Call a companion supported by your Summoning level.'),
      ('Slayer\'s Refusal','slayer',25,'interrupt','Physical','Interrupt a selected creature before its attack resolves.')]:
        data['abilities'].append(dict(id='shared_'+slug(name),name=name,**{'class':''},skill=skill,requirement=level,kind=kind,element=element,description=description,**PROFILES[kind]))
