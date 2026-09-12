using System.Text.Json;
using Kairnfall.Core;

var catalogPath = args.Length > 0 ? args[0] : "content/catalog.json";
var catalog = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(catalogPath), Wire.Json)
    ?? throw new InvalidOperationException("Could not load generated content catalog.");
var failures = new List<string>();
ConcurrencyStressChecks.Run(catalog, failures);
foreach (var failure in failures) Console.WriteLine("FAIL " + failure);
return failures.Count == 0 ? 0 : 1;
