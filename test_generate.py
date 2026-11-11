#!/usr/bin/env python3
"""Static end-to-end test and seam tests for the No Intrusive Scopes generator."""

import lzma
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import generate as gen

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT / "generate.py"
PATCH = ROOT / "NoIntrusiveScopes.txt"
DATA_DIR = ROOT / "data"

DUMP_FILES = gen.DUMP_FILES
STOCK = gen.FAMILY_STOCK

AMIGO = "GD_Anemone_Weapons.A_Weapons_Unique.Sniper_Jakobs_3_Morde_Lt:WeaponPartListCollectionDefinition_236"
OVERCOMP = "GD_Anemone_Weapons.Shotgun.Overcompensator.SG_Hyperion_6_Overcompensator:WeaponPartListCollectionDefinition_237"
CHAUD = "GD_Anemone_Weapons.sniper.Sniper_Jakobs_6_Chaude_Mama:WeaponPartListCollectionDefinition_234"
ODD = "GD_Aster_Weapons.SMGs.SMG_Maliwan_3_Crit:WeaponPartListCollectionDefinition_244"
FREM = "GD_Weap_SniperRifles.A_Weapons_Unique.Sniper_Hyperion_3_FremingtonsEdge:WeaponPartListCollectionDefinition_209"
MISSING = [
    "GD_Anemone_Weapons.A_Weapons.AR_Bandit_3_Rare_Alien_Shock:WeaponPartListCollectionDefinition_337",
    "GD_Anemone_Weapons.A_Weapons.AR_Bandit_3_Rare_Alien_Slag:WeaponPartListCollectionDefinition_338",
    "GD_Flynt.Weapons.AR_Flynt:WeaponPartListCollectionDefinition_328",
    "GD_Leprechaun.Weapons.SG_Leprechaun:WeaponPartListCollectionDefinition_330",
    "GD_Orchid_BossWeapons.AssaultRifle.AR_Jakobs_3_Stinkpot_Nodrop:WeaponPartListCollectionDefinition_335",
    "GD_Weap_SniperRifles.A_Weapons.Sniper_Maliwan_4_Mordecai:WeaponPartListCollectionDefinition_329",
]
SKIPPED = [
    "GD_Aster_Weapons.Snipers.SR_Maliwan_4_Aquamarine:WeaponPartListCollectionDefinition_327",
    "GD_Iris_MotorMama.Weapons.LauncherCustom:PartList",
]
NO_SIGHT = [
    "GD_Anemone_Weapons.A_Weapons_Unique.Pistol_The_Gremlins:PartList",
    "GD_Lilac_SkillsBase.Buzzaxe.Buzzaxe:PartList",
    "GD_Orchid_BossWeapons.Pistol.Pistol_Jakobs_ScarletsGreed:WeaponPartListCollectionDefinition_298",
    "GD_Orchid_BossWeapons.RPG.Ahab.Orchid_Boss_Ahab_Balance_NODROP:WeaponPartListCollectionDefinition_309",
    "GD_Sage_HarpoonGun.Balance.Sage_HarpoonGun_Balance:WeaponPartListCollectionDefinition_315",
    "GD_Sage_RaidWeapons.Shotgun.Sage_Seraph_Interfacer_Balance:WeaponPartListCollectionDefinition_318",
    "GD_Weap_Scorpio.A_Weapon.WeapBalance_Scorpio:PartList",
]
UNSCOPED_POOLS = [
    "GD_Orchid_BossWeapons.AssaultRifle.AR_Vladof_3_Rapier:WeaponPartListCollectionDefinition_310",
    "GD_Weap_AssaultRifle.A_Weapons_Unique.AR_Vladof_3_Hail:WeaponPartListCollectionDefinition_44",
]
FAMILY_COUNTS = {"Pistol": 75, "AR": 45, "SG": 49, "SMG": 47, "Sniper": 51, "RL": 39}
ADDED_STOCK_COUNTS = {"Sniper": 51, "SG": 1}

SCOPED_PART = "GD_Weap_Pistol.Sight.Pistol_Sight_A"
IRON_PART = "GD_Weap_Pistol.Sight.Pistol_Sight_Iron"
STOCK_PART = STOCK["Pistol"]


def entry(part, minimum, maximum, weight=4):
    return (
        f"(Part=WeaponPartDefinition'{part}',"
        "Manufacturers=((Manufacturer=None,DefaultWeightIndex=1)),"
        f"MinGameStageIndex={minimum},MaxGameStageIndex={maximum},"
        f"DefaultWeightIndex={weight})"
    )


def sight(*entries, enabled=True):
    return f"(bEnabled={enabled},WeightedParts=({','.join(entries)}))"


def props_for(sight_value):
    return {
        "ConsolidatedAttributeInitData(2)": (
            "BaseValueConstant=0.000000,BaseValueAttribute=None,"
            "InitializationDefinition=None,BaseValueScaleConstant=1.000000"
        ),
        "ConsolidatedAttributeInitData(5)": (
            "BaseValueConstant=1.000000,BaseValueAttribute=None,"
            "InitializationDefinition=None,BaseValueScaleConstant=1.000000"
        ),
        "ConsolidatedAttributeInitData(7)": (
            "BaseValueConstant=100.000000,BaseValueAttribute=None,"
            "InitializationDefinition=None,BaseValueScaleConstant=1.000000"
        ),
        "SightPartData": sight_value,
    }


def key_of(entry):
    return (entry.part, entry.get("Manufacturers"), entry.get("DefaultWeightIndex"))


def family_of(parts):
    return parts[0].rsplit(".", 1)[-1].split("_", 1)[0]


def parse_patch(text):
    start = text.index("<BLCMM")
    end = text.index("</BLCMM>") + len("</BLCMM>")
    xml_text = re.sub(r"^#<!!!.*\n", "", text[start:end], flags=re.MULTILINE)
    root = ElementTree.fromstring(xml_text)
    codes = [code.text for code in root.iter("code")]
    flat = [
        line for line in text[text.index("#Commands:"):].splitlines()[1:]
        if line.strip()
    ]
    commands = {}
    for command in codes:
        prefix = "set "
        suffix = " SightPartData "
        if not command.startswith(prefix) or suffix not in command:
            raise AssertionError(f"unexpected command: {command[:120]}")
        path, value = command[len(prefix):].split(suffix, 1)
        commands[path] = value
    return root, codes, flat, commands


class Expectation:
    def __init__(self):
        self.parts = gen.load_dump(DATA_DIR / DUMP_FILES["parts"])
        self.lists = gen.load_dump(DATA_DIR / DUMP_FILES["lists"])
        balances = gen.load_dump(DATA_DIR / DUMP_FILES["balances"])
        self.scoped = {
            path for path, props in self.parts.items()
            if props.get("bScoped") == "True"
        }
        self.runtime = gen.runtime_refs(balances)
        self.missing = [path for path in self.runtime if path not in self.lists]
        self.no_sight = []
        self.fixed = []
        self.pools = []
        self.sights = {}
        for path in self.runtime:
            if path in self.missing:
                continue
            sights = gen.SightData.parse(self.lists[path]["SightPartData"], path).parts
            self.sights[path] = sights
            if not sights:
                self.no_sight.append(path)
            elif len(set(sights)) == 1:
                self.fixed.append(path)
            else:
                self.pools.append(path)
        self.unscoped_pools = [
            path for path in self.pools
            if not any(part in self.scoped for part in self.sights[path])
        ]
        self.fixed_scoped = [
            path for path in self.fixed
            if any(part in self.scoped for part in self.sights[path])
        ]
        self.exempt = [path for path in self.fixed_scoped if "FremingtonsEdge" in path]
        self.skipped = [
            path for path in self.pools + self.fixed_scoped
            if path in SKIPPED
        ]
        self.edited = [
            path for path in self.pools + self.fixed_scoped
            if path not in self.unscoped_pools
            and path not in self.exempt
            and path not in SKIPPED
        ]


class NoIntrusiveScopesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.first = Path(cls.tmp.name) / "first.txt"
        cls.second = Path(cls.tmp.name) / "second.txt"
        subprocess.run([sys.executable, str(GENERATOR), str(cls.first)], check=True)
        subprocess.run([sys.executable, str(GENERATOR), str(cls.second)], check=True)
        cls.text = cls.first.read_text(encoding="utf-8")
        cls.root, cls.codes, cls.flat, cls.commands = parse_patch(cls.text)
        cls.expect = Expectation()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_output_is_current_and_deterministic(self):
        self.assertEqual(
            self.first.read_bytes(),
            PATCH.read_bytes(),
            "NoIntrusiveScopes.txt is stale; run generate.py",
        )
        self.assertEqual(self.first.read_bytes(), self.second.read_bytes())

    def test_counts_match_independent_expectation(self):
        expect = self.expect
        self.assertEqual(len(expect.runtime), 360)
        self.assertEqual(len(expect.missing), 6)
        self.assertEqual(len(expect.no_sight), 7)
        self.assertEqual(len(expect.fixed), 40)
        self.assertEqual(len(expect.pools), 307)
        self.assertEqual(len(expect.unscoped_pools), 2)
        self.assertEqual(len(expect.fixed_scoped), 4)
        self.assertEqual(len(expect.exempt), 1)
        self.assertEqual(len(expect.skipped), 2)
        self.assertEqual(len(expect.pools) - len(expect.unscoped_pools), 305)
        self.assertEqual(
            len(expect.pools) - len(expect.unscoped_pools) - len(expect.skipped),
            303,
        )
        self.assertEqual(len(expect.fixed_scoped) - len(expect.exempt), 3)
        self.assertEqual(len(expect.edited), 306)
        self.assertEqual(len(self.commands), 306)
        self.assertEqual(set(self.commands), set(expect.edited))

    def test_expected_lists_are_edited_or_untouched(self):
        expect = self.expect
        for path in [AMIGO, OVERCOMP, CHAUD, ODD]:
            self.assertIn(path, self.commands)
        for path in MISSING + NO_SIGHT + UNSCOPED_POOLS + SKIPPED + [FREM]:
            self.assertNotIn(path, self.commands)
        self.assertEqual(expect.missing, MISSING)
        self.assertEqual(expect.no_sight, NO_SIGHT)
        self.assertEqual(expect.unscoped_pools, UNSCOPED_POOLS)
        self.assertEqual(expect.exempt, [FREM])
        self.assertEqual(sorted(expect.skipped), sorted(SKIPPED))
        for path in SKIPPED:
            self.assertIn(path, expect.pools)
            self.assertTrue(
                any(part in expect.scoped for part in expect.sights[path]),
                path,
            )

    def test_family_coverage(self):
        families = Counter(family_of(self.expect.sights[path]) for path in self.expect.edited)
        self.assertEqual(dict(families), FAMILY_COUNTS)

    def test_original_entries_and_ranges(self):
        expect = self.expect
        added = Counter()
        for path in expect.edited:
            props = expect.lists[path]
            caid_one = gen.caid_index(props, 1.0, path)
            caid_hundred = gen.caid_index(props, 100.0, path)
            self.assertIsNotNone(caid_one, path)
            self.assertIsNotNone(caid_hundred, path)

            original = gen.SightData.parse(props["SightPartData"], path)
            output = gen.SightData.parse(self.commands[path], path)
            self.assertEqual(output.enabled, original.enabled, path)
            original_keys = Counter(key_of(entry) for entry in original.entries)
            output_keys = Counter(key_of(entry) for entry in output.entries)
            for key, count in original_keys.items():
                self.assertGreaterEqual(output_keys[key], count, path)
            self.assertNotIn("Part=None", self.commands[path])

            # Pair duplicate keys by occurrence, then check each written range.
            originals_by_key = {}
            for written in original.entries:
                originals_by_key.setdefault(key_of(written), []).append(written)
            outputs_by_key = {}
            for written in output.entries:
                outputs_by_key.setdefault(key_of(written), []).append(written)

            original_nonscoped = []
            for key, originals in originals_by_key.items():
                for source, written in zip(originals, outputs_by_key[key]):
                    part = source.part
                    if part in expect.scoped:
                        self.assertEqual(written.stage_range(), (caid_hundred, caid_one), path)
                    else:
                        original_nonscoped.append(written)
                        if part.rsplit(".", 1)[-1].endswith("_None"):
                            self.assertEqual(written.stage_range(), (caid_one, caid_hundred), path)
                        else:
                            self.assertEqual(written.stage_range(), source.stage_range(), path)

            self.assertEqual(
                [written.render() for written in output.entries],
                sorted(written.render() for written in output.entries),
                path,
            )

            if original_nonscoped:
                self.assertEqual(len(output.entries), len(original.entries), path)
            else:
                self.assertEqual(len(output.entries), len(original.entries) + 1, path)
                family = family_of(expect.sights[path])
                self.assertIn(STOCK[family], [written.part for written in output.entries], path)
                added[family] += 1

            full_range = [
                written for written in output.entries
                if written.part not in expect.scoped
                and written.stage_range() == (caid_one, caid_hundred)
            ]
            self.assertTrue(full_range, f"{path} has no full-range non-scoped sight")

        self.assertEqual(dict(added), ADDED_STOCK_COUNTS)

    def test_no_cross_family_or_none_entries(self):
        expect = self.expect
        for path, value in self.commands.items():
            family = family_of(expect.sights[path])
            for written in gen.SightData.parse(value, path).entries:
                part = written.part
                self.assertNotEqual(part, "None", path)
                self.assertIn(part, expect.parts, path)
                self.assertEqual(family_of([part]), family, f"{path}: {part}")

    def test_patch_is_blcmm_with_matching_flat_commands(self):
        self.assertEqual([code.text for code in self.root.iter("code")], self.codes)
        self.assertEqual(self.codes, self.flat)
        self.assertEqual(self.root.find("head/type").attrib, {"name": "BL2", "offline": "true"})
        self.assertEqual(list(self.root.iter("hotfix")), [])
        self.assertNotIn("#Hotfixes:", self.text)

    def test_caid_edge_case(self):
        props = self.expect.lists[ODD]
        self.assertEqual(gen.caid_index(props, 1.0, ODD), 2)
        self.assertEqual(gen.caid_index(props, 100.0, ODD), 3)
        for written in gen.SightData.parse(self.commands[ODD], ODD).entries:
            if written.part in self.expect.scoped:
                self.assertEqual(written.stage_range(), (3, 2))
            else:
                self.assertEqual(written.stage_range(), (2, 3))


class SightDataTest(unittest.TestCase):
    def test_round_trip_preserves_field_order(self):
        value = sight(entry(SCOPED_PART, 0, 1))
        data = gen.SightData.parse(value, "fixture")
        self.assertTrue(data.enabled)
        self.assertEqual(data.parts, [SCOPED_PART])
        self.assertEqual(data.render(), value)

    def test_set_stage_range_keeps_order(self):
        data = gen.SightData.parse(sight(entry(SCOPED_PART, 0, 1)), "fixture")
        data.entries[0].set_stage_range(7, 5)
        self.assertEqual(data.entries[0].stage_range(), (7, 5))
        self.assertIn("MinGameStageIndex=7,MaxGameStageIndex=5", data.render())

    def test_unbalanced_entries_fail(self):
        with self.assertRaises(SystemExit):
            gen.SightData.parse("(bEnabled=True,WeightedParts=((Part=x)", "fixture")

    def test_non_property_value_fails(self):
        with self.assertRaises(SystemExit):
            gen.SightData.parse("garbage", "fixture")


class DumpReaderTest(unittest.TestCase):
    HEADER = "*** Property dump for object 'WillowGame.WeaponPartDefinition GD.X:Part' ***\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text):
        path = Path(self.tmp.name) / "fixture.dump.xz"
        with lzma.open(path, "wt", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_reads_properties_and_ignores_section_headers(self):
        path = self.write(self.HEADER + "=== properties ===\n  bScoped=True\n")
        self.assertEqual(gen.load_dump(path)["GD.X:Part"]["bScoped"], "True")

    def test_duplicate_block_fails(self):
        with self.assertRaises(SystemExit):
            gen.load_dump(self.write(self.HEADER + self.HEADER))

    def test_duplicate_property_fails(self):
        with self.assertRaises(SystemExit):
            gen.load_dump(self.write(self.HEADER + "  bScoped=True\n  bScoped=False\n"))

    def test_truncated_value_fails(self):
        with self.assertRaises(SystemExit):
            gen.load_dump(self.write(self.HEADER + "  SightPartData=(bEnabled=True,WeightedParts=((Part=x)\n"))

    def test_unsupported_line_fails(self):
        with self.assertRaises(SystemExit):
            gen.load_dump(self.write(self.HEADER + "  continuation without equals\n"))

    def test_missing_file_fails(self):
        with self.assertRaises(SystemExit):
            gen.load_dump(Path(self.tmp.name) / "absent.dump.xz")


class RuntimeRefsTest(unittest.TestCase):
    def test_returns_sorted_unique_refs(self):
        balances = {
            "B": {"RuntimePartListCollection": "(WeaponPartListCollectionDefinition'GD.X:Two')"},
            "A": {"RuntimePartListCollection": "(WeaponPartListCollectionDefinition'GD.X:One')"},
        }
        self.assertEqual(gen.runtime_refs(balances), ["GD.X:One", "GD.X:Two"])

    def test_ambiguous_reference_fails(self):
        balances = {
            "B": {"RuntimePartListCollection": (
                "(WeaponPartListCollectionDefinition'GD.X:One',"
                "WeaponPartListCollectionDefinition'GD.X:Two')"
            )},
        }
        with self.assertRaises(SystemExit):
            gen.runtime_refs(balances)


class PlanningTest(unittest.TestCase):
    known = {SCOPED_PART, IRON_PART, STOCK_PART}

    def test_strict_plan_empties_scoped_range_and_adds_stock(self):
        outcome = gen.plan_list(
            "GD.X:PartList",
            props_for(sight(entry(SCOPED_PART, 5, 7))),
            {SCOPED_PART},
            self.known,
        )
        override = outcome.override
        self.assertIsNotNone(override)
        self.assertEqual(override.family, "Pistol")
        self.assertEqual(override.added_stock, STOCK_PART)
        ranges = {written.part: written.stage_range() for written in override.sight_data.entries}
        self.assertEqual(ranges[SCOPED_PART], (7, 5))
        self.assertEqual(ranges[STOCK_PART], (5, 7))
        added = next(written for written in override.sight_data.entries if written.part == STOCK_PART)
        self.assertEqual(added.get("Manufacturers"), "")

    def test_conservative_plan_keeps_level_one_loophole(self):
        outcome = gen.plan_list(
            "GD.X:PartList",
            props_for(sight(entry(SCOPED_PART, 5, 7))),
            {SCOPED_PART},
            self.known,
            gen.CONSERVATIVE,
        )
        ranges = {written.part: written.stage_range() for written in outcome.override.sight_data.entries}
        self.assertEqual(ranges[SCOPED_PART], (5, 5))
        self.assertEqual(ranges[STOCK_PART], (5, 7))

    def test_full_range_non_scoped_entry_skips_stock(self):
        outcome = gen.plan_list(
            "GD.X:PartList",
            props_for(sight(entry(SCOPED_PART, 0, 1), entry(IRON_PART, 5, 7))),
            {SCOPED_PART},
            self.known,
        )
        self.assertIsNone(outcome.override.added_stock)
        self.assertNotIn(STOCK_PART, [written.part for written in outcome.override.sight_data.entries])

    def test_skip_reasons(self):
        no_scoped = gen.plan_list(
            "GD.X:PartList",
            props_for(sight(entry(IRON_PART, 5, 7))),
            {SCOPED_PART},
            self.known,
        )
        self.assertEqual(no_scoped.reason, "no scoped sight")
        empty = gen.plan_list(
            "GD.X:PartList",
            props_for(sight(enabled=False)),
            {SCOPED_PART},
            self.known,
        )
        self.assertEqual(empty.reason, "no sight data")

    def test_missing_part_fails(self):
        with self.assertRaises(SystemExit):
            gen.plan_list(
                "GD.X:PartList",
                props_for(sight(entry(SCOPED_PART, 0, 1))),
                {SCOPED_PART},
                set(),
            )

    def test_build_plan_exposes_skip_reasons(self):
        plan = gen.build_plan()
        self.assertEqual(len(plan.runtime), 360)
        self.assertEqual(len(plan.overrides), 306)
        reasons = {skip.path: skip.reason for skip in plan.skips}
        for path in MISSING:
            self.assertEqual(reasons[path], "absent from dump")
        self.assertIn("exempt", reasons[FREM])
        for path in SKIPPED:
            self.assertEqual(reasons[path], "unresolvable when text mods execute")
        self.assertEqual(reasons[UNSCOPED_POOLS[0]], "no scoped sight")
        self.assertEqual(reasons[NO_SIGHT[0]], "no sight data")


class PolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.strict_path = Path(cls.tmp.name) / "strict.txt"
        cls.conservative_path = Path(cls.tmp.name) / "conservative.txt"
        subprocess.run([sys.executable, str(GENERATOR), str(cls.strict_path)], check=True)
        subprocess.run(
            [sys.executable, str(GENERATOR), "--policy", "conservative", str(cls.conservative_path)],
            check=True,
        )
        cls.strict = parse_patch(cls.strict_path.read_text(encoding="utf-8"))[3]
        cls.conservative_text = cls.conservative_path.read_text(encoding="utf-8")
        cls.conservative = parse_patch(cls.conservative_text)[3]
        cls.expect = Expectation()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_conservative_header_does_not_warn_about_strict(self):
        self.assertIn("Conservative stage range", self.conservative_text)
        self.assertNotIn("Strict inverted stage range is untested", self.conservative_text)

    def test_conservative_policy_uses_level_one_range(self):
        self.assertEqual(set(self.strict), set(self.conservative))
        scoped_entries = 0
        for path, value in self.conservative.items():
            props = self.expect.lists[path]
            caid_one = gen.caid_index(props, 1.0, path)
            conservative = gen.SightData.parse(value, path)
            strict = gen.SightData.parse(self.strict[path], path)
            self.assertEqual(
                [entry.render() for entry in conservative.entries if entry.part not in self.expect.scoped],
                [entry.render() for entry in strict.entries if entry.part not in self.expect.scoped],
                path,
            )
            for entry in conservative.entries:
                if entry.part in self.expect.scoped:
                    self.assertEqual(entry.stage_range(), (caid_one, caid_one), path)
                    scoped_entries += 1
        self.assertGreater(scoped_entries, 0)


if __name__ == "__main__":
    unittest.main()
