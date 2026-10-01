using System.Text.Json;
using Kairnfall.Core;

public static class ClassicTutorialCatalogCases
{
    public static void Run(Action<string,Action> test,Catalog normal)
    {
        void Check(bool value,string message) { if(!value)throw new InvalidOperationException(message); }
        string Bytes<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        void Reject<T>(Action action) where T:Exception
        {
            try { action(); } catch(T) { return; }
            throw new InvalidOperationException("Expected "+typeof(T).Name);
        }
        Catalog Tutorial()
        {
            var data=Wire.Copy(normal);ClassicTutorialContent.Enable(data);return data;
        }
        test("Classic catalog activation stages validated content without changing ordinary definitions",()=>
        {
            var data=Wire.Copy(normal);string before=Bytes(normal);
            var city=data.Zone("wayfarers_rest");string oldCity=Bytes(city);
            var tuning=new ClassicTutorialTuning{StartingFood=61,ResourceRecoverySeconds=4,MilestoneXp=137};
            ClassicTutorialContent.Enable(data,tuning);
            Check(data.Validate().Count==0,"The staged tutorial catalog is invalid.");
            Check(Bytes(normal)==before&&Bytes(city)==oldCity,"Activation changed an existing catalog or retained city object.");
            foreach(var item in normal.Items)Check(Bytes(data.Item(item.Id))==Bytes(item),"Ordinary item definition changed.");
            var appliedTuning=data.ClassicTutorial??throw new InvalidOperationException("Tutorial tuning was not applied.");
            Check(appliedTuning is {StartingFood:61,MilestoneXp:137},"Explicit local tuning changed.");
            Check(data.Resource("classic_tree").Respawn==4,"Resource tuning did not reach the new definitions.");
            Check(data.Recipe("classic_make_pickaxe").Ingredients["classic_stone"]==10
                &&data.Recipe("classic_make_pickaxe").Ingredients["classic_wood"]==5
                &&data.Recipe("classic_make_fire").Ingredients["classic_tinder"]==3
                &&data.Recipe("classic_make_fire").Ingredients["classic_flint"]==1
                &&data.Recipe("classic_make_fire").Ingredients["classic_wood"]==5,"Recipe costs changed.");
            tuning.StartingFood=0;tuning.MilestoneXp=10000;
            Check(appliedTuning.StartingFood==61&&appliedTuning.MilestoneXp==137,"Caller tuning remained aliased to authority data.");
        });
        test("Classic invalid tuning rejects before any catalog or city mutation",()=>
        {
            foreach(var tuning in new[]{new ClassicTutorialTuning{FoodDrainPerSecond=double.NaN},
                new ClassicTutorialTuning{ResourceRecoverySeconds=double.PositiveInfinity},
                new ClassicTutorialTuning{MilestoneXp=0},new ClassicTutorialTuning{AvatarScale=2}})
            {
                var data=Wire.Copy(normal);string before=Bytes(data);var items=data.Items;var zones=data.Zones;
                Reject<InvalidDataException>(()=>ClassicTutorialContent.Enable(data,tuning));
                Check(Bytes(data)==before&&ReferenceEquals(items,data.Items)&&ReferenceEquals(zones,data.Zones),"Failed tuning partly changed the caller's catalog.");
            }
        });
        test("Classic partial catalogs cannot be accepted or silently completed",()=>
        {
            foreach(Action<Catalog> mutate in new Action<Catalog>[] {
                data=>data.ClassicTutorial=new(),
                data=>data.Items.Add(new(){Id="classic_wood",Name="Partial",Type="material",Icon="oak_log"}),
                data=>data.Zones.RemoveAll(zone=>zone.Id=="wayfarers_rest")})
            {
                var data=Wire.Copy(normal);mutate(data);string before=Bytes(data);
                Check(data.Validate().Count>0,"Partial tutorial/base catalog was accepted.");
                Reject<InvalidDataException>(()=>ClassicTutorialContent.Enable(data));
                Check(Bytes(data)==before,"Rejected catalog was mutated.");
            }
        });
        test("Classic catalog validation reports tuning and missing runtime references as errors",()=>
        {
            foreach(Action<Catalog> mutate in new Action<Catalog>[] {
                data=>data.ClassicTutorial!.FoodRestore=double.NaN,
                data=>data.Items.RemoveAll(item=>item.Id=="classic_berries"),
                data=>data.Skills.RemoveAll(skill=>skill.Id==ClassicTutorialContent.Questing),
                data=>data.Resources.RemoveAll(node=>node.Id=="classic_tinder_node"),
                data=>data.Resource("classic_tree").Item="classic_stone",
                data=>data.Resource("classic_tree").Respawn=9,
                data=>data.Mobs.RemoveAll(mob=>mob.Id=="field_rat"),
                data=>data.Recipes.RemoveAll(recipe=>recipe.Id=="classic_make_fire"),
                data=>data.Recipe("classic_make_pickaxe").Output="bread",
                data=>data.Zone(ClassicTutorialContent.ZoneId).Furnishings.Clear(),
                data=>data.Zone(ClassicTutorialContent.ZoneId).Furnishings.First(x=>x.Id=="classic_first_sign").Rise=0,
                data=>data.Zone(ClassicTutorialContent.ZoneId).Furnishings.First(x=>x.Id=="classic_first_sign").Rise=25,
                data=>data.Zone(ClassicTutorialContent.ZoneId).Furnishings.First(x=>x.Id=="classic_fountain").Rise=96,
                data=>data.Zone("wayfarers_rest").Exits.RemoveAll(exit=>exit.Target==ClassicTutorialContent.ZoneId),
                data=>data.Zones.RemoveAll(zone=>zone.Id==ClassicTutorialContent.ZoneId)})
            {
                var data=Tutorial();mutate(data);
                string? before=double.IsFinite(data.ClassicTutorial!.FoodRestore)?Bytes(data):null;
                Check(data.Validate().Count>0,"Malformed tutorial did not return validation errors.");
                Reject<InvalidDataException>(()=>ClassicTutorialContent.Enable(data));
                Check(before is null||Bytes(data)==before,"Rejected runtime reference partly changed the catalog.");
            }
        });
        test("Classic malformed nested collections return errors without escaping validation",()=>
        {
            foreach(Action<Catalog> mutate in new Action<Catalog>[] {
                data=>data.Resources=null!,data=>data.Items.Add(null!),
                data=>data.Recipe("classic_make_fire").Ingredients=null!,
                data=>data.Zone(ClassicTutorialContent.ZoneId).Furnishings=null!,
                data=>data.Item("classic_stone_pickaxe").Tags=null!})
            {
                var data=Tutorial();mutate(data);
                Check(data.Validate().Count>0,"Missing tutorial collections were accepted.");
                Reject<InvalidDataException>(()=>ClassicTutorialContent.Enable(data));
            }
        });
        test("Classic pre-overlaid activation is idempotent and rejects implicit retuning",()=>
        {
            var data=Tutorial();string before=Bytes(data);var zones=data.Zones;var tuning=data.ClassicTutorial;
            ClassicTutorialContent.Enable(data);ClassicTutorialContent.Enable(data,Wire.Copy(tuning!));
            Check(Bytes(data)==before&&ReferenceEquals(zones,data.Zones)&&ReferenceEquals(tuning,data.ClassicTutorial),"Idempotent activation replaced validated content.");
            Reject<InvalidDataException>(()=>ClassicTutorialContent.Enable(data,new(){MilestoneXp=999}));
            Check(Bytes(data)==before,"Conflicting caller tuning overwrote an embedded catalog.");
        });
        test("Classic startup requires opt-in Testing permitted HTTP and every effective loopback binding",()=>
        {
            void Gate(bool requested=true,bool overlaid=true,bool testing=true,bool http=true,params string[] addresses)
                =>ClassicTutorialContent.RequireLocalStartup(requested,overlaid,testing,http,addresses);
            Gate(addresses:["http://127.0.0.1:5100","https://[::1]:5101","http://localhost:5102"]);
            Gate(overlaid:false,addresses:["http://127.0.0.1:5100"]);
            Reject<InvalidOperationException>(()=>Gate(requested:false,addresses:["http://127.0.0.1:5100"]));
            Reject<InvalidOperationException>(()=>Gate(testing:false,addresses:["http://127.0.0.1:5100"]));
            Reject<InvalidOperationException>(()=>Gate(http:false,addresses:["http://127.0.0.1:5100"]));
            foreach(var addresses in new[]{Array.Empty<string>(),new[]{""},new[]{"http://0.0.0.0:5100"},
                new[]{"http://*:5100"},new[]{"http://example.com:5100"},new[]{"ftp://127.0.0.1:5100"},
                new[]{"http://127.0.0.1:5100/other"},new[]{"http://user@127.0.0.1:5100"},
                new[]{"http://127.0.0.1:5100","http://0.0.0.0:5101"}})
                Reject<InvalidOperationException>(()=>Gate(addresses:addresses));
            // Ordinary catalogs retain normal production configuration behavior.
            Gate(requested:false,overlaid:false,testing:false,http:false,addresses:["https://game.example.com"]);
        });
        test("Classic world mode rejection never converts or mutates retained saves",()=>
        {
            var ordinary=new RealmEngine(normal);var player=ordinary.CreateCharacter("retained-normal","Retained Normal","vanguard",new());
            var tutorial=Tutorial();var saved=Wire.Copy(ordinary.State);string before=Bytes(saved);
            Reject<InvalidDataException>(()=>new RealmEngine(tutorial,saved));
            Check(Bytes(saved)==before&&player.ClassicTutorial is null,"A normal retained world was converted.");
            var local=new RealmEngine(tutorial);var localPlayer=local.CreateCharacter("retained-classic","Retained Classic","vanguard",new());
            localPlayer.ClassicTutorial!.Food=43;localPlayer.ClassicTutorial.Completed.Add("wood");
            localPlayer.ClassicTutorial.NoticeId=7;localPlayer.ClassicTutorial.Notice="Retained notice";
            var classicSave=Wire.Copy(local.State);string classicBefore=Bytes(classicSave);
            Reject<InvalidDataException>(()=>new RealmEngine(normal,classicSave));
            Check(Bytes(classicSave)==classicBefore,"A tutorial save was modified by cross-mode rejection.");
            var reloaded=new RealmEngine(tutorial,Wire.Copy(classicSave));
            Check(Bytes(reloaded.Player(localPlayer.Id))==Bytes(localPlayer),"Same-mode reload changed tutorial progress or possessions.");
            Check(new RealmEngine(normal,Wire.Copy(saved)).Player(player.Id).ClassicTutorial is null,"Ordinary save gained tutorial state on reload.");
        });
    }
}
