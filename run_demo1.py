from src.strategies.registry import discover_strategies
specs = discover_strategies()
print("discovered =", len(specs))
for i, k in enumerate(sorted(specs.keys())[:10], 1):
    s = specs[k]
    print(i, k, "->", s.display_name, f"({s.family})")
