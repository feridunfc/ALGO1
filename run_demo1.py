# run_discovery_check.py
from src.strategies.registry import bootstrap, discover_strategies, list_strategies

bootstrap("static")  # statik bağları ekle (AI + rule_based)
specs = discover_strategies()

print("discovered =", len(specs))
for i, (qn, s) in enumerate(specs.items()):
    if i >= 10: break
    print(f"- {s.display_name} | {s.family} | {qn}")

errs = getattr(discover_strategies, "errors", {})
if errs:
    print("\n[skipped modules]")
    for k, v in errs.items():
        print("*", k, "->", v.splitlines()[0])

print("\n[manual registry keys]")
print(list_strategies())
