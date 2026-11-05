"""Freeze one 32-game training batch from a reviewed opponent registry."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

QUOTAS = {"anchor": 8, "sparring": 5, "history": 3}
MAX_PAIRS_PER_STYLE = 4


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def stable_order(seed, value):
    return sha256(f"{seed}:{value}".encode()).hexdigest()


def freeze(registry_path, map_manifest, map_dir, holdout, seed, matched=False):
    registry = json.loads(registry_path.read_text())
    opponents = {}
    for item in registry["opponents"]:
        name, role, style = (item[k] for k in ("name", "role", "style"))
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in opponents:
            raise ValueError(f"Invalid or duplicate opponent name: {name}")
        if role not in QUOTAS or not style:
            raise ValueError(f"Invalid league role or style: {name}")
        if role == "sparring" and not item.get("admission_evidence"):
            raise ValueError(f"Missing sparring admission review: {name}")
        binary = (registry_path.parent / item["wasm"]).resolve()
        if digest(binary) != item["sha256"]:
            raise ValueError(f"Opponent hash mismatch: {name}")
        opponents[name] = {**item, "wasm": str(binary)}
    if len({item["sha256"] for item in opponents.values()}) != len(opponents):
        raise ValueError("An opponent binary appears under multiple names")

    control_names = {name: name for name in opponents}
    if matched:
        for name, item in opponents.items():
            if item["role"] == "sparring":
                parent = item.get("control_parent")
                if parent not in opponents or opponents[parent]["role"] != "anchor":
                    raise ValueError(f"Matched sparring requires a registered anchor parent: {name}")
                control_names[name] = parent
    selected = Counter()
    style_counts = Counter()
    control_style_counts = Counter()

    def allocate(role, quota):
        for _ in range(quota):
            options = [name for name, item in opponents.items()
                       if item["role"] == role and style_counts[item["style"]] < MAX_PAIRS_PER_STYLE
                       and control_style_counts[opponents[control_names[name]]["style"]] < MAX_PAIRS_PER_STYLE]
            if not options:
                break
            name = min(options, key=lambda n: (style_counts[opponents[n]["style"]],
                                                selected[n], stable_order(seed, n)))
            selected[name] += 1
            style_counts[opponents[name]["style"]] += 1
            control_style_counts[opponents[control_names[name]]["style"]] += 1

    roles = ("sparring", "anchor", "history") if matched else QUOTAS
    for role in roles:
        allocate(role, QUOTAS[role])
    allocate("anchor", 16 - sum(selected.values()))
    if sum(selected.values()) != 16:
        raise ValueError("Need more anchor styles to fill 16 paired slots under the style cap")
    if matched and not any(opponents[name]["role"] == "sparring" for name in selected):
        raise ValueError("A matched trial requires at least one admitted sparring slot")

    held_out = json.loads(holdout.read_text())["maps"]
    excluded = {m["sha256"] for m in held_out}
    excluded_families = {m["family"] for m in held_out}
    candidates = json.loads(map_manifest.read_text())["maps"]
    families = {}
    for m in sorted(candidates, key=lambda m: stable_order(seed, m["sha256"])):
        if m["split"] == "training" and m["sha256"] not in excluded and m["family"] not in excluded_families:
            families.setdefault(m["family"], m)
    if len(families) < 8:
        raise ValueError("Need at least eight eligible training map families")
    maps = []
    groups = {}
    for name, count in selected.items():
        groups.setdefault(control_names[name], Counter())[name] = count
    for m in list(families.values())[:8]:
        parents = sorted((n for n, counts in groups.items() if sum(counts.values())),
                         key=lambda n: (-sum(groups[n].values()), stable_order(seed, n)))[:2]
        if len(parents) != 2 or digest(map_dir / m["file"]) != m["sha256"]:
            raise ValueError(f"Invalid map or opponent pair: {m['file']}")
        chosen = []
        for parent in parents:
            counts = groups[parent]
            name = min(counts, key=lambda n: (-counts[n], stable_order(seed, n)))
            counts[name] -= 1
            chosen.append(name)
        maps.append({**m, "opponents": chosen})
    provenance = {
        "schema": "sparring-batch-v1", "policy_seed": seed, "games": 32,
        "registry_sha256": digest(registry_path),
        "map_manifest_sha256": digest(map_manifest),
        "holdout_manifest_sha256": digest(holdout),
    }

    def batch(arm_maps):
        counts = Counter(n for m in arm_maps for n in m["opponents"])
        return {
            **provenance,
            "maps": arm_maps, "opponents": {name: opponents[name] for name in counts},
            "games_per_opponent": {name: 2 * count for name, count in counts.items()},
            "games_by_role": {role: 2 * sum(n for name, n in counts.items()
                                            if opponents[name]["role"] == role) for role in QUOTAS},
        }

    treatment = batch(maps)
    if not matched:
        return treatment
    control = batch([{**m, "opponents": [control_names[n] for n in m["opponents"]]} for m in maps])
    return {"schema": "sparring-matched-trial-v1", "treatment": treatment, "control": control}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("registry", "map-manifest", "map-dir", "holdout", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--matched", action="store_true",
                        help="Emit both arms, substituting each sparrer's registered control_parent")
    args = parser.parse_args()
    batch = freeze(args.registry, args.map_manifest, args.map_dir, args.holdout, args.seed, args.matched)
    with args.out.open("x") as stream:
        json.dump(batch, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
