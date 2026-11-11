#!/usr/bin/env python3
"""Generate the No Intrusive Scopes BLCMM patch from the vendored BL2 dumps."""

import argparse
import lzma
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT = ROOT / "NoIntrusiveScopes.txt"

VERSION = "1.1.0"
CREDIT = "ancent"

DUMP_FILES = {
    "parts": "WeaponPartDefinition.dump.xz",
    "lists": "WeaponPartListCollectionDefinition.dump.xz",
    "balances": "WeaponBalanceDefinition.dump.xz",
}

BLOCK_RE = re.compile(r"^\*\*\* Property dump for object '([^ ']+) (.+)' \*\*\*$")
SIGHT_RE = re.compile(r"^\(bEnabled=(True|False),WeightedParts=(?:\((.*)\))?\)$")
PART_RE = re.compile(r"^WeaponPartDefinition'([^']+)'$")
CAID_RE = re.compile(r"^ConsolidatedAttributeInitData\((\d+)\)$")
RUNTIME_RE = re.compile(r"WeaponPartListCollectionDefinition'([^']+)'")

# Launchers are edited when their pools contain scoped sights, but they have no
# stock no-sight part; every launcher pool keeps the non-scoped RL_Sight_Torgue.
FAMILY_STOCK = {
    "Pistol": "GD_Weap_Pistol.Sight.Pistol_Sight_None",
    "AR": "GD_Weap_AssaultRifle.Sight.AR_Sight_None",
    "SG": "GD_Weap_Shotgun.Sight.SG_Sight_None",
    "SMG": "GD_Weap_SMG.Sight.SMG_Sight_None",
    "Sniper": "GD_Weap_SniperRifles.Sight.Sniper_Sight_None_Buffalo",
}
STOCK_NO_SIGHT = set(FAMILY_STOCK.values()) | {
    "GD_Weap_SniperRifles.Sight.Sniper_Sight_None_Longbow",
}
FAMILY_NAMES = {
    "Pistol": "Pistols",
    "AR": "Assault Rifles",
    "SG": "Shotguns",
    "SMG": "SMGs",
    "Sniper": "Sniper Rifles",
    "RL": "Launchers",
}
# Category order follows the insertion order of FAMILY_NAMES.
FAMILY_ORDER = list(FAMILY_NAMES)

# Fremington's Edge's 25x scope is the weapon's identity.
EXEMPT = "FremingtonsEdge"

# The game cannot resolve these objects when text mods execute, so `set` only
# prints "Unrecognized class or object". Skip them instead of warning.
UNRESOLVABLE = {
    "GD_Aster_Weapons.Snipers.SR_Maliwan_4_Aquamarine:WeaponPartListCollectionDefinition_327",
    "GD_Iris_MotorMama.Weapons.LauncherCustom:PartList",
}


def fail(message):
    raise SystemExit(f"error: {message}")


# --- dumps -----------------------------------------------------------------


def _read_dump_lines(path):
    try:
        with lzma.open(path, "rt", encoding="utf-8") as handle:
            yield from handle
    except UnicodeDecodeError as exc:
        fail(f"{path}: not valid UTF-8 ({exc})")


def load_dump(path):
    """Read one property dump. Fail on anything that would silently lose data."""
    path = Path(path)
    if not path.is_file():
        fail(f"missing vendored dump {path}")
    blocks = {}
    current = None
    current_name = ""
    for number, line in enumerate(_read_dump_lines(path), 1):
        line = line.rstrip("\n")
        match = BLOCK_RE.match(line)
        if match:
            current_name = match.group(2)
            if current_name in blocks:
                fail(f"{path}:{number}: duplicate block {current_name}")
            current = {}
            blocks[current_name] = current
            continue
        if current is None or not line.strip():
            continue
        if line.strip().startswith("==="):
            continue
        if not line.startswith("  ") or "=" not in line:
            fail(f"{path}:{number}: unsupported dump line in {current_name}")
        key, _, value = line.strip().partition("=")
        if key in current:
            fail(f"{path}:{number}: duplicate property {key} in {current_name}")
        if value.count("(") != value.count(")"):
            fail(f"{path}:{number}: truncated value for {key} in {current_name}")
        current[key] = value
    return blocks


def runtime_refs(balances):
    """Return every distinct runtime list reference, one per balance."""
    refs = set()
    for path, props in balances.items():
        found = RUNTIME_RE.findall(props.get("RuntimePartListCollection", ""))
        if len(found) > 1:
            fail(f"{path} has {len(found)} runtime list references")
        refs.update(found)
    return sorted(refs)


# --- sight data ------------------------------------------------------------


def _split_entries(text):
    """Split a WeightedParts value into top-level entry tuples."""
    entries = []
    outside = []
    depth = 0
    start = None
    segment_start = 0
    for index, char in enumerate(text):
        if char == "(":
            if depth == 0:
                outside.append(text[segment_start:index])
                start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                fail("unbalanced parentheses in SightPartData")
            if depth == 0:
                entries.append(text[start:index + 1])
                segment_start = index + 1
    if depth != 0:
        fail("unbalanced parentheses in SightPartData")
    outside.append(text[segment_start:])
    if any(part.strip(" \t\r\n,") for part in outside):
        fail("unexpected text outside SightPartData entries")
    return entries


def _split_fields(inner):
    """Split an entry's fields on top-level commas, preserving their order."""
    fields = []
    depth = 0
    start = 0
    for index, char in enumerate(inner):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            fields.append(inner[start:index])
            start = index + 1
    fields.append(inner[start:])
    result = []
    for field in fields:
        key, separator, value = field.partition("=")
        if not separator:
            fail(f"cannot parse SightPartData field {field!r}")
        result.append((key, value))
    return result


class SightEntry:
    """One WeightedParts entry. Field order is preserved because it is rendered."""

    __slots__ = ("fields",)

    def __init__(self, fields):
        self.fields = [(key, value) for key, value in fields]

    @classmethod
    def parse(cls, text):
        return cls(_split_fields(text[1:-1]))

    @property
    def part(self):
        match = PART_RE.match(self.get("Part"))
        if not match:
            fail("SightPartData contains a non-part entry")
        return match.group(1)

    def get(self, key):
        for name, value in self.fields:
            if name == key:
                return value
        fail(f"missing {key} in SightPartData entry")

    def set(self, key, value):
        for index, (name, _) in enumerate(self.fields):
            if name == key:
                self.fields[index] = (name, value)
                return
        fail(f"missing {key} in SightPartData entry")

    def stage_range(self):
        return (
            int(self.get("MinGameStageIndex")),
            int(self.get("MaxGameStageIndex")),
        )

    def set_stage_range(self, minimum, maximum):
        self.set("MinGameStageIndex", str(minimum))
        self.set("MaxGameStageIndex", str(maximum))

    def render(self):
        return "(" + ",".join(f"{key}={value}" for key, value in self.fields) + ")"


class SightData:
    """The SightPartData property of one runtime list."""

    def __init__(self, enabled, entries):
        self.enabled = enabled
        self.entries = entries

    @classmethod
    def parse(cls, value, path="?"):
        match = SIGHT_RE.match(value or "")
        if not match:
            fail(f"cannot parse SightPartData for {path}")
        entries = [
            SightEntry.parse(entry)
            for entry in (_split_entries(match.group(2)) if match.group(2) else [])
        ]
        return cls(match.group(1) == "True", entries)

    @property
    def parts(self):
        return [entry.part for entry in self.entries]

    def render(self):
        weighted = ",".join(entry.render() for entry in self.entries)
        return f"(bEnabled={self.enabled},WeightedParts=({weighted}))"

    def command(self, path):
        return f"set {path} SightPartData {self.render()}"


# --- planning --------------------------------------------------------------


def _caid_values(props):
    for key, raw in props.items():
        match = CAID_RE.match(key)
        if match:
            yield int(match.group(1)), raw


def caid_index(props, value, path):
    matches = [
        index for index, raw in _caid_values(props)
        if (constant := re.search(r"BaseValueConstant=([\d.]+)", raw))
        and float(constant.group(1)) == value
    ]
    if len(matches) != 1:
        fail(f"{path} has {len(matches)} CAID entries for value {value}")
    return matches[0]


def plain_zero_index(props, path):
    matches = [
        index for index, raw in _caid_values(props)
        if (
            "BaseValueConstant=0.000000" in raw
            and "BaseValueAttribute=None" in raw
            and "InitializationDefinition=None" in raw
            and "BaseValueScaleConstant=1.000000" in raw
        )
    ]
    if len(matches) != 1:
        fail(f"{path} has {len(matches)} plain zero-weight CAID entries")
    return matches[0]


def family_of(parts, path):
    families = set()
    for part in parts:
        prefix = part.rsplit(".", 1)[-1].split("_", 1)[0]
        if prefix not in FAMILY_NAMES:
            fail(f"cannot classify sight part {part} in {path}")
        families.add(prefix)
    if len(families) != 1:
        fail(f"{path} mixes sight families: {sorted(families)}")
    return families.pop()


@dataclass(frozen=True)
class RangePolicy:
    """How a scoped sight's stage range is emptied."""

    name: str
    apply: Callable[[SightEntry, int, int], None]


STRICT = RangePolicy(
    "strict",
    lambda entry, one, hundred: entry.set_stage_range(hundred, one),
)
CONSERVATIVE = RangePolicy(
    "conservative",
    lambda entry, one, hundred: entry.set("MaxGameStageIndex", str(one)),
)
POLICIES = {policy.name: policy for policy in (STRICT, CONSERVATIVE)}


@dataclass(frozen=True)
class Override:
    path: str
    family: str
    sight_data: SightData
    added_stock: str | None


@dataclass(frozen=True)
class Outcome:
    override: Override | None = None
    reason: str = ""


@dataclass(frozen=True)
class Skip:
    path: str
    reason: str


@dataclass(frozen=True)
class Plan:
    runtime: list[str]
    overrides: dict[str, Override]
    skips: list[Skip]
    policy: RangePolicy


def plan_list(path, props, scoped, known_parts, policy=CONSERVATIVE):
    """Turn one runtime list into an override, or a named skip reason."""
    sight_data = SightData.parse(props.get("SightPartData"), path)
    parts = sight_data.parts
    missing = sorted({part for part in parts if part not in known_parts})
    if missing:
        fail(f"{path} references sight parts absent from the dump: {missing}")
    if not parts:
        return Outcome(reason="no sight data")
    if not any(part in scoped for part in parts):
        return Outcome(reason="no scoped sight")

    caid_one = caid_index(props, 1.0, path)
    caid_hundred = caid_index(props, 100.0, path)
    family = family_of(parts, path)

    for entry in sight_data.entries:
        if entry.part in scoped:
            policy.apply(entry, caid_one, caid_hundred)
        elif entry.part in STOCK_NO_SIGHT:
            # Existing stock no-sight: make sure it is always available.
            entry.set_stage_range(caid_one, caid_hundred)

    if any(
        entry.stage_range()[1] != caid_one
        for entry in sight_data.entries
        if entry.part in scoped
    ):
        fail(f"{path}: scoped sight was not level-limited")

    has_full_range_nonscoped = any(
        entry.part not in scoped and entry.stage_range() == (caid_one, caid_hundred)
        for entry in sight_data.entries
    )

    added_stock = None
    if not has_full_range_nonscoped:
        stock = FAMILY_STOCK.get(family)
        if stock is None:
            fail(f"no stock no-sight part for family {family} ({path})")
        sight_data.entries.append(SightEntry([
            ("Part", f"WeaponPartDefinition'{stock}'"),
            ("Manufacturers", ""),
            ("MinGameStageIndex", str(caid_one)),
            ("MaxGameStageIndex", str(caid_hundred)),
            ("DefaultWeightIndex", str(plain_zero_index(props, path))),
        ]))
        added_stock = stock

    sight_data.entries.sort(key=SightEntry.render)
    return Outcome(Override(path, family, sight_data, added_stock))


def build_plan(policy=CONSERVATIVE):
    parts = load_dump(DATA_DIR / DUMP_FILES["parts"])
    lists = load_dump(DATA_DIR / DUMP_FILES["lists"])
    balances = load_dump(DATA_DIR / DUMP_FILES["balances"])

    scoped = {
        path for path, props in parts.items() if props.get("bScoped") == "True"
    }
    for family, stock in FAMILY_STOCK.items():
        props = parts.get(stock)
        if props is None:
            fail(f"stock no-sight part {stock} for {family} is absent from the dump")
        if props.get("bScoped") != "False":
            fail(f"stock no-sight part {stock} for {family} is scoped")

    runtime = runtime_refs(balances)
    overrides = {}
    skips = []
    for path in runtime:
        if path not in lists:
            skips.append(Skip(path, "absent from dump"))
            continue
        if EXEMPT in path:
            skips.append(Skip(path, "exempt: unique scope is the weapon's identity"))
            continue
        if path in UNRESOLVABLE:
            skips.append(Skip(path, "unresolvable when text mods execute"))
            continue
        outcome = plan_list(path, lists[path], scoped, parts, policy)
        if outcome.override is None:
            skips.append(Skip(path, outcome.reason))
        else:
            overrides[path] = outcome.override
    return Plan(runtime, overrides, skips, policy)


# --- rendering -------------------------------------------------------------


def render_patch(plan):
    by_family = {family: [] for family in FAMILY_ORDER}
    for override in sorted(plan.overrides.values(), key=lambda item: item.path):
        by_family[override.family].append(override)

    range_comment = (
        "\t\t\t<comment>Strict inverted stage range is untested in-game. Back up saves first; see the README for the conservative fallback.</comment>"
        if plan.policy is STRICT
        else "\t\t\t<comment>Conservative stage range uses the UCP-proven level-1 pattern.</comment>"
    )
    lines = [
        '<BLCMM v="1">',
        '#<!!!You opened a file saved with BLCMM in FilterTool. Please update to BLCMM to properly open this file!!!>',
        '\t<head>',
        '\t\t<type name="BL2" offline="true"/>',
        '\t\t<profiles>',
        '\t\t\t<profile name="default" current="true"/>',
        '\t\t</profiles>',
        '\t</head>',
        '\t<body>',
        f'\t\t<category name="No Intrusive Scopes v{VERSION}">',
        f'\t\t\t<comment>Stops new BL2 weapons from generating with scoped sights. Credit: {CREDIT}</comment>',
        '\t\t\t<comment>Iron sights, red dots, holograms, and no-sight options remain. Existing guns keep their current scopes.</comment>',
        '\t\t\t<comment>Every original sight entry stays listed so the save sanity check cannot delete existing gear.</comment>',
        range_comment,
        "\t\t\t<comment>Load order: UCP first, then No Intrusive Scopes. Fremington's Edge is exempt.</comment>",
    ]

    flat = []
    for family in FAMILY_ORDER:
        lines.append(f'\t\t\t<category name="{FAMILY_NAMES[family]}">')
        for override in by_family[family]:
            value = override.sight_data.command(override.path)
            flat.append(value)
            lines.append(f'\t\t\t\t<code profiles="default">{escape(value, quote=False)}</code>')
        lines.append('\t\t\t</category>')

    lines.extend([
        '\t\t</category>',
        '\t</body>',
        '</BLCMM>',
        '',
        '#Commands:',
        *flat,
        '',
    ])

    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--policy", choices=sorted(POLICIES), default=CONSERVATIVE.name)
    args = parser.parse_args(argv)

    plan = build_plan(POLICIES[args.policy])
    patch = render_patch(plan)
    tmp = args.output.with_name(args.output.name + ".tmp")
    tmp.write_text(patch, encoding="utf-8", newline="\n")
    tmp.replace(args.output)
    print(
        f"wrote {args.output} "
        f"({len(plan.overrides)} of {len(plan.runtime)} runtime sight lists changed)"
    )


if __name__ == "__main__":
    main()
