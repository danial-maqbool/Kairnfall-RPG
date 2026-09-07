#!/usr/bin/env python3
"""Apply the reviewed transaction repair to exact, pinned source files.

This one-time source migration does not run in the game. The isolated repair
workflow tests the resulting C# files before committing them. Unexpected source
versions stop the migration instead of overwriting concurrent changes.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    'src/Kairnfall.Core/RealmEngine.cs': 'c19e7783366ab8b82f43cdd36c33b0ace63954ca',
    'src/Kairnfall.Core/RealmSocial.cs': '1d1506a9d8fe2d9dcebce2c9c755ebc3de28aa8d',
    'src/Kairnfall.Core/Models.cs': 'dd7f2bac3b03498b747b0512746ecee2b0a7983b',
    'tests/Kairnfall.SecurityTests/Program.cs': 'b85c0fdbfcb464d4dda76433d77ed5fc58a430d0',
}

TRANSACTIONS = r'''using System.Security.Cryptography;
using System.Text.Json;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private string SplitStack(Character player, string itemId, int amount)
    {
        var source = Items.Owned(player, itemId);
        var definition = Data.Item(source.Template);
        Need(definition.StackMax > 1 && !Items.Equipped(player, itemId),
            "Only unequipped, stackable items can be split.");
        Need(source.Affixes.Count == 0 && source.Runes.Count == 0 && source.Sockets == 0,
            "Modified equipment cannot be split.");
        Need(amount > 0 && amount < source.Quantity,
            "Split at least one item and leave at least one in the original stack.");
        Need(player.Inventory.Count < Items.InventoryCapacity,
            "A free inventory slot is required to split a stack.");

        // Do not call Items.Add: it deliberately merges compatible stacks.
        var separated = Wire.Copy(source);
        separated.Id = Guid.NewGuid().ToString("N");
        separated.Quantity = amount;
        source.Quantity -= amount;
        player.Inventory.Add(separated);
        return $"Split {amount} {definition.Name}.";
    }

    private bool CanFulfillTradeOffer(TradeOffer offer)
    {
        if (!State.Characters.TryGetValue(offer.Character, out var owner) ||
            offer.Gold < 0 || offer.Gold > owner.Gold || offer.Items.Count > 12)
            return false;
        foreach (var pair in offer.Items)
        {
            var item = owner.Inventory.FirstOrDefault(x => x.Id == pair.Key);
            if (item is null || pair.Value < 1 || pair.Value > item.Quantity ||
                Items.Equipped(owner, item.Id) || Data.Item(item.Template).Type == "quest")
                return false;
        }
        return true;
    }

    private string TradeContentFingerprint(Trade trade)
    {
        object Describe(TradeOffer offer)
        {
            var owner = Player(offer.Character);
            return new
            {
                offer.Character,
                offer.Gold,
                Funded = offer.Gold >= 0 && offer.Gold <= owner.Gold,
                Items = offer.Items.OrderBy(x => x.Key, StringComparer.Ordinal)
                    .Select(x => new
                    {
                        Id = x.Key,
                        Offered = x.Value,
                        Instance = owner.Inventory.FirstOrDefault(i => i.Id == x.Key),
                        Equipped = Items.Equipped(owner, x.Key)
                    }).ToArray()
            };
        }
        var content = JsonSerializer.SerializeToUtf8Bytes(
            new { A = Describe(trade.A), B = Describe(trade.B) }, Wire.Json);
        return Convert.ToHexString(SHA256.HashData(content));
    }

    private bool InvalidateTradeConsent(Trade trade)
    {
        if (!trade.A.Ready && !trade.B.Ready && !trade.A.Confirmed && !trade.B.Confirmed)
            return false;
        string current = TradeContentFingerprint(trade);
        bool changed = ((trade.A.Ready || trade.A.Confirmed) && trade.A.ApprovedFingerprint != current) ||
                       ((trade.B.Ready || trade.B.Confirmed) && trade.B.ApprovedFingerprint != current);
        if (!changed) return false;
        trade.A.Ready = trade.B.Ready = false;
        trade.A.Confirmed = trade.B.Confirmed = false;
        trade.A.ApprovedFingerprint = trade.B.ApprovedFingerprint = "";
        trade.Revision = checked(trade.Revision + 1);
        EconomicDirty = true;
        return true;
    }

    private void InvalidateTradeConsents()
    {
        foreach (var trade in State.Trades.Values) InvalidateTradeConsent(trade);
    }
}
'''

TRADE_READY = r'''    private string TradeReady(Character p,string id,int revision,bool confirm)
    {
        var trade = GetTrade(p, id);
        // Persist the reset as an acknowledged state change. Throwing here would
        // restore the stale consent through Execute's transaction rollback.
        if (InvalidateTradeConsent(trade))
            return "The trade contents changed. Both players must review the new offer.";
        Need(trade.Revision == revision, "The offer changed. Review the current revision.");
        Need(CanFulfillTradeOffer(trade.A) && CanFulfillTradeOffer(trade.B),
            "An offered item or the offered gold is no longer available.");
        var offer = trade.A.Character == p.Id ? trade.A : trade.B;
        if (!confirm)
        {
            offer.Ready = true;
            offer.Confirmed = false;
            // Each player approves BOTH offers, including the full item instance.
            offer.ApprovedFingerprint = TradeContentFingerprint(trade);
            return "Offer marked ready. Confirm after both players are ready.";
        }
        Need(trade.A.Ready && trade.B.Ready, "Both players must first mark their offers ready.");
        offer.Confirmed = true;
        if (!trade.A.Confirmed || !trade.B.Confirmed) return "Confirmed. Waiting for the other player.";
        var a=Player(trade.A.Character); var b=Player(trade.B.Character);
        var aItems=trade.A.Items.Select(x=>Items.Take(a.Inventory,x.Key,x.Value,a)).ToList();
        var bItems=trade.B.Items.Select(x=>Items.Take(b.Inventory,x.Key,x.Value,b)).ToList();
        Items.Spend(a,trade.A.Gold); Items.Spend(b,trade.B.Gold);
        foreach(var item in aItems) Items.Add(b.Inventory,item,Data);
        foreach(var item in bItems) Items.Add(a.Inventory,item,Data);
        Items.Grant(a,trade.B.Gold); Items.Grant(b,trade.A.Gold);
        State.Trades.Remove(id); Progress(a,"trade","*"); Progress(b,"trade","*");
        return "Trade completed.";
    }
'''

EXTRA_TESTS = r'''
void ReadyBoth(RealmEngine engine, string alice, string bob, string id)
{
    int revision = engine.State.Trades[id].Revision;
    Check(Act(engine, alice, "trade_ready", id, amount: revision).Ok, "Alice could not ready.");
    Check(Act(engine, bob, "trade_ready", id, amount: revision).Ok, "Bob could not ready.");
}

Test("full item state changes invalidate consent during the server tick", () =>
{
    Action<Item>[] mutations = [
        i => i.Durability--,
        i => i.Rarity = Rarity.Epic,
        i => i.Sockets++,
        i => i.Affixes.Add(new Affix { Name = "test", Stat = "strength", Value = 1 }),
        i => i.Template = "iron_sword"
    ];
    foreach (var mutate in mutations)
    {
        var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
        ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
        int old = f.Engine.State.Trades[offered.Trade].Revision;
        mutate(Items.Owned(f.Engine.Player(f.Alice), offered.Item));
        f.Engine.Tick(0.05);
        var trade = f.Engine.State.Trades[offered.Trade];
        Check(trade.Revision > old && !trade.A.Ready && !trade.B.Ready &&
            !trade.A.Confirmed && !trade.B.Confirmed, "Tick preserved approval of changed item contents.");
    }
});

Test("one ready player approves both offers, not only their own", () =>
{
    var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
    int old = f.Engine.State.Trades[offered.Trade].Revision;
    Check(Act(f.Engine, f.Bob, "trade_ready", offered.Trade, amount: old).Ok, "Bob ready failed.");
    var rune = f.Engine.Player(f.Alice).Inventory.First(x => catalog.Item(x.Template).Type == "rune");
    Check(Act(f.Engine, f.Alice, "socket", offered.Item, rune.Id).Ok, "Valid socket action failed.");
    var trade = f.Engine.State.Trades[offered.Trade];
    Check(!trade.B.Ready && trade.Revision > old, "Bob's approval survived a change to Alice's item.");
});

Test("unchanged offers retain consent after an unrelated item change", () =>
{
    var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
    ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
    int old = f.Engine.State.Trades[offered.Trade].Revision;
    var potion = f.Engine.Player(f.Alice).Inventory.First(x => x.Template == "healing_potion");
    Check(Act(f.Engine, f.Alice, "split", item: potion.Id, amount: 1).Ok, "Unrelated split failed.");
    var trade = f.Engine.State.Trades[offered.Trade];
    Check(trade.Revision == old && trade.A.Ready && trade.B.Ready, "Unrelated inventory changes cancelled consent.");
});

Test("stack splitting invalidates approval of the affected offered stack", () =>
{
    var f = Fixture();
    Check(Act(f.Engine, f.Alice, "trade_invite", f.Bob).Ok, "Invite failed.");
    string id = f.Engine.State.Trades.Values.Single().Id;
    var potion = f.Engine.Player(f.Alice).Inventory.First(x => x.Template == "healing_potion");
    Check(Act(f.Engine, f.Alice, "trade_offer", id, potion.Id, 2).Ok, "Offer failed.");
    ReadyBoth(f.Engine, f.Alice, f.Bob, id);
    int old = f.Engine.State.Trades[id].Revision;
    Check(Act(f.Engine, f.Alice, "split", item: potion.Id, amount: 1).Ok, "Valid split failed.");
    var trade = f.Engine.State.Trades[id];
    Check(trade.Revision > old && !trade.A.Ready && !trade.B.Ready, "Changed stack retained consent.");
});

Test("insufficient funds invalidate approved gold without a transfer", () =>
{
    var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
    Check(Act(f.Engine, f.Alice, "trade_offer", offered.Trade, arg: "500").Ok, "Gold offer failed.");
    ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
    f.Engine.Player(f.Alice).Gold = 100;
    f.Engine.Tick(0.05);
    var trade = f.Engine.State.Trades[offered.Trade];
    Check(!trade.A.Ready && !trade.B.Ready, "Unfunded offer retained consent.");
    Check(f.Engine.Player(f.Bob).Gold == 1000, "Invalidation transferred gold.");
});

Test("reviewing the changed offer permits a later correct trade", () =>
{
    var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
    ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
    var rune = f.Engine.Player(f.Alice).Inventory.First(x => catalog.Item(x.Template).Type == "rune");
    Check(Act(f.Engine, f.Alice, "socket", offered.Item, rune.Id).Ok, "Socket failed.");
    ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
    int revision = f.Engine.State.Trades[offered.Trade].Revision;
    Check(Act(f.Engine, f.Alice, "trade_confirm", offered.Trade, amount: revision).Ok, "First confirmation failed.");
    Check(Act(f.Engine, f.Bob, "trade_confirm", offered.Trade, amount: revision).Ok, "Final confirmation failed.");
    Check(!f.Engine.State.Trades.ContainsKey(offered.Trade), "Completed trade remained active.");
    Check(Items.Owned(f.Engine.Player(f.Bob), offered.Item).Runes.Count == 1, "Receiver did not get the reviewed item.");
    Check(!f.Engine.Player(f.Alice).Inventory.Any(x => x.Id == offered.Item), "Trade duplicated the item.");
});

Test("nonstackable and equipped items cannot be split", () =>
{
    var f = Fixture(); var weapon = f.Engine.Player(f.Alice).Equipment["weapon"];
    Check(!Act(f.Engine, f.Alice, "split", item: weapon, amount: 1).Ok, "Equipped weapon was split.");
    var extra = Items.Create(catalog, "copper_sword");
    Items.Add(f.Engine.Player(f.Alice).Inventory, extra, catalog);
    Check(!Act(f.Engine, f.Alice, "split", item: extra.Id, amount: 1).Ok, "Nonstackable item was split.");
});

Test("readiness fingerprints survive state serialization", () =>
{
    var f = Fixture(); var offered = Offer(f.Engine, f.Alice, f.Bob);
    ReadyBoth(f.Engine, f.Alice, f.Bob, offered.Trade);
    var saved = Wire.Copy(f.Engine.State);
    var trade = saved.Trades[offered.Trade];
    Check(trade.A.ApprovedFingerprint.Length == 64 && trade.A.ApprovedFingerprint == trade.B.ApprovedFingerprint,
        "State serialization lost the approval content fingerprint.");
});

'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f'{label}: expected one exact replacement anchor')
    return text.replace(old, new, 1)


def main() -> None:
    staged = {}
    for name, expected in EXPECTED.items():
        raw = (ROOT / name).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if actual != expected:
            raise RuntimeError(f'{name}: source changed; review before applying this migration')
        staged[name] = raw.decode('utf-8')
    engine = staged['src/Kairnfall.Core/RealmEngine.cs']
    engine = replace_once(engine, '            string message=Dispatch(p,command);',
        '            string message=Dispatch(p,command);\n            InvalidateTradeConsents();', 'post-command consent check')
    engine = replace_once(engine, '            case "gather": return Gather(p,c.Target);',
        '            case "split": return SplitStack(p,c.Item,c.Amount);\n            case "gather": return Gather(p,c.Target);', 'split dispatch')
    engine = replace_once(engine, '        TickEvents();\n    }',
        '        TickEvents();\n        InvalidateTradeConsents();\n    }', 'post-tick consent check')
    staged['src/Kairnfall.Core/RealmEngine.cs'] = engine
    models = staged['src/Kairnfall.Core/Models.cs']
    models = replace_once(models, '    public bool Confirmed { get; set; }\n}',
        '    public bool Confirmed { get; set; }\n    public string ApprovedFingerprint { get; set; } = "";\n}', 'approval model')
    staged['src/Kairnfall.Core/Models.cs'] = models
    social = staged['src/Kairnfall.Core/RealmSocial.cs']
    social = replace_once(social,
        'trade.B.Confirmed=false; trade.Expires=State.Time+120;',
        'trade.B.Confirmed=false; trade.A.ApprovedFingerprint=""; trade.B.ApprovedFingerprint=""; trade.Expires=State.Time+120;', 'explicit offer change')
    start = social.index('    private string TradeReady(')
    end = social.index('    private string TradeCancel(', start)
    social = social[:start] + TRADE_READY + social[end:]
    staged['src/Kairnfall.Core/RealmSocial.cs'] = social
    staged['src/Kairnfall.Core/RealmTransactions.cs'] = TRANSACTIONS
    program = staged['tests/Kairnfall.SecurityTests/Program.cs']
    program = replace_once(program, 'Console.WriteLine($"SECURITY_RESULTS', EXTRA_TESTS + 'Console.WriteLine($"SECURITY_RESULTS', 'extra regressions')
    staged['tests/Kairnfall.SecurityTests/Program.cs'] = program
    for name, text in staged.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')
        print('REPAIRED', name, hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main()
