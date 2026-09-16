using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private string OpeningDialogue(NpcDef npc)
    {
        if (Snapshot is not { } snapshot || !OpeningJourney.Eligible(snapshot.Self)
            || npc.Id != OpeningJourney.Giver(Data).Id) return npc.Dialogue;
        var p = snapshot.Self;
        if (OpeningJourney.Finished(p))
            return "You made the medicine path safe, improved your kit and brewed your own supplies. The workshop needs a hand next. Or meet the other travelers through Social; the village is a shared home.";
        if (OpeningJourney.Crafted(p) && OpeningJourney.Equipped(p))
            return "Ready for the road? Keep the potions you brewed. Tell me you are finished, then choose your next journey.";
        if (p.CompletedQuests.Contains(OpeningJourney.FightQuest))
            return "Your Rare weapon and all the potion ingredients are already in your backpack. Equip the upgrade, then use the village alchemy table. Come back when you have brewed your medicine.";
        if (OpeningJourney.Kills(p) >= OpeningJourney.KillGoal)
            return "The nearby path is safer. Your weapon and medicine supplies are waiting here. Choose Claim reward; there is no special loot drop to search for.";
        return "Welcome to Wayfarer's Rest. Field rats have spoiled our medicine stores. Clear two from the nearby path, then return. I will fit you out and show you how to make fresh medicine.";
    }

    private void ReviewOpeningItem(string id)
    {
        // Re-read the current authoritative snapshot, not the card's captured item.
        // The ordinary inventory panel owns focus, comparison, Equip/Use and errors.
        if (Snapshot is not { } current) return;
        selectedBag = "inventory";
        selectedItem = current.Self.Inventory.Any(x => x.Id == id) ? id : "";
        OpenPage("Inventory");
    }

    private void AddOpeningQuestDetails(Node parent, QuestDef quest)
    {
        if (Snapshot is not { } snapshot || !OpeningJourney.Eligible(snapshot.Self)
            || !OpeningJourney.IsOpeningQuest(quest.Id)) return;
        var p = snapshot.Self;
        if (quest.Id == OpeningJourney.FightQuest)
        {
            parent.AddChild(Ui.Label(OpeningJourney.RewardDescription(Data, p), 14, Ui.Text, true));
            return;
        }
        string rewardId = OpeningJourney.RewardId(p);
        if (!OpeningJourney.Equipped(p))
        {
            if (p.Inventory.Any(x => x.Id == rewardId))
            {
                var review = Ui.Button("Review your earned weapon", () => ReviewOpeningItem(rewardId));
                review.Name = "OpeningReviewReward";
                review.TooltipText = "Open this exact item and its comparison in the backpack. Choose Equip there; no equipment changes happen just by viewing it.";
                parent.AddChild(review);
            }
            if (p.Equipment.GetValueOrDefault("weapon", "") != rewardId && OpeningJourney.CurrentWeaponIsUpgrade(Data, p))
            {
                var keep = Ui.Button("Keep my stronger equipped weapon", () =>
                {
                    if (Snapshot?.Self.Equipment.TryGetValue("weapon", out var id) == true)
                        Send("equip", item: id);
                }, !Online || actionBusy || p.Health <= 0);
                keep.Name = "OpeningKeepStrongerWeapon";
                keep.TooltipText = "Send a normal Equip request for your current weapon. The server checks that it is stronger than your class's starting weapon; you do not have to downgrade.";
                parent.AddChild(keep);
            }
            parent.AddChild(Ui.Label("Your opening reward stays yours until this equip step is complete. You may bank it, but equip it once before selling or trading it.", 13, Ui.Muted, true));
        }
        if (OpeningJourney.Crafted(p))
        {
            var potion = p.Inventory.FirstOrDefault(x => x.Template == "healing_potion");
            parent.AddChild(Ui.Label("Medicine brewed. Each Healing Potion restores 60 health. Keep it for your next fight; you do not need to waste a potion at full health.", 14, Ui.Text, true));
            if (potion is not null)
            {
                string id = potion.Id;
                var view = Ui.Button("Find my Healing Potions", () => ReviewOpeningItem(id));
                view.Name = "OpeningFindPotions";
                parent.AddChild(view);
            }
        }
    }

    private void AddOpeningJournalRecap(Node parent)
    {
        if (Snapshot is not { } snapshot || !OpeningJourney.Eligible(snapshot.Self)) return;
        var p = snapshot.Self;
        string Done(bool value) => value ? "Done" : "Pending";
        parent.AddChild(Ui.Label(OpeningJourney.Finished(p) ? "Your first journey · complete" : "Your first journey · Medicine for the Road", 19, Ui.Gold));
        parent.AddChild(Ui.Label($"{Done(p.CompletedQuests.Contains(OpeningJourney.FightQuest))}: clear two Field Rats and claim your class weapon.\n"
            + $"{Done(OpeningJourney.Equipped(p))}: review and equip the earned upgrade.\n"
            + $"{Done(OpeningJourney.Crafted(p))}: brew two Healing Potions at the village alchemy table.", 14, Ui.Text, true));
        parent.AddChild(Ui.Label("These are saved milestones, not a restart button. Death, reconnecting and closing guidance do not reset them. Reopening this journal never grants another reward.", 13, Ui.Muted, true));
        if (OpeningJourney.Finished(p))
        {
            parent.AddChild(Ui.Label("Next: follow A Place by the Fire for the workshop story, or open Social to meet nearby travelers and find a party. Neither choice needs another tutorial reward.", 14, Ui.Text, true));
            parent.AddChild(Ui.Button("Meet nearby travelers", () => OpenPage("Social")));
        }
    }
}
