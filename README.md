# No Intrusive Scopes

A standalone Borderlands 2 text mod that stops newly generated weapons from
rolling scoped sights. Iron sights, red dots, holograms, and no-sight options
remain. Existing guns keep the scopes they already have.

Version **1.2.0**. Credit: **ancent**. `NoIntrusiveScopes.txt` is a standard
BLCMM v1 file, grouped by weapon family so it can be opened and inspected.

## Install

1. Back up your saves (see [Save safety](#save-safety)).
2. Copy `NoIntrusiveScopes.txt` into Borderlands 2's `Binaries` directory, next
   to the game executable.
3. Enable it in the text mod loader's mods menu.

No game files are edited. To uninstall, disable the mod in the menu or remove
the file.

## Load order

- The mod is standalone and works without the Unofficial Community Patch (UCP).
- With UCP, load **UCP first, then No Intrusive Scopes**. The loader can enable
  both BLCMM files at the same time.
- UCP 5.0.4 contains one inactive sight override (the Emperor-to-Torrent
  alternative). It is not executed by default and does not conflict.

## Save safety

Back up `Documents/My Games/Borderlands 2/WillowGame/SaveData` before
installing.

The mod rewrites generation lists only:

- Every original sight entry stays listed, so the save sanity check still
  recognises saved guns.
- Scoped entries are disabled or level-limited, not removed.
- No part definitions (`bScoped`, scope meshes, zoom FOV, reticles) are changed,
  so existing guns keep their current scopes.
- Existing gear is not re-rolled or deleted.

If guns vanish or behave oddly after installing, restore the save backup, then
either disable the mod or try the conservative policy below.

## How it works

For every edited list, the whole `SightPartData` array is replaced. Every
original entry is kept. A scoped entry gets `MinGameStageIndex` pointing at the
list's CAID value 100 and `MaxGameStageIndex` pointing at the list's CAID value
1, producing an empty stage range at every level. If a list would have no
non-scoped option left, a stock no-sight part for that weapon family is added
with a full range.

### Strict policy (default, verified in-game)

The committed patch and `python3 generate.py` use the strict policy. It sets
`MinGameStageIndex` to the CAID value 100 and `MaxGameStageIndex` to the CAID
value 1, producing an empty stage range. Starting-gun and full-game play were
verified in-game with no scoped sights. Back up saves before installing.

### Conservative policy (UCP-proven fallback)

If the strict range causes problems, regenerate with the conservative policy:

```sh
python3 generate.py --policy conservative NoIntrusiveScopes-conservative.txt
```

Copy the result to `Binaries` as usual. For each scoped entry, the conservative
policy keeps the existing minimum and sets `MaxGameStageIndex` to the list's
CAID index for 1. This leaves a tiny level-1 loophole but is known to be
tolerated by the game. In these dumps, the index for 1 is `0` for every list
except
`GD_Aster_Weapons.SMGs.SMG_Maliwan_3_Crit:WeaponPartListCollectionDefinition_244`,
which uses `2`.

## Coverage

Weapon balances reference 360 runtime lists; 354 exist in the pinned dumps.
347 of those contain sight data: 40 fixed-sight lists and 307 random pools.

- **306 lists are edited**: 303 random pools containing scoped sights, plus 3
  fixed named weapons (Amigo Sincero, Overcompensator, Chaude Mama).
- **54 lists are untouched**: 6 absent from the dumps, 7 with no sight data (3
  disabled, 4 enabled but empty), 2 unresolvable at execution time, 2 pools with
  no scoped sights, 36 fixed single-sight lists with only non-scoped sights, and
  Fremington's Edge, which keeps its unique 25× scope.
- 52 edited lists gained a stock no-sight part: 51 sniper lists
  (`Sniper_Sight_None_Buffalo`) and 1 shotgun list (`SG_Sight_None`).
- 95 edited lists already had a stock `_None` entry; 159 already had iron or
  other non-scoped coverage.
- All weapon types are covered: pistols, assault rifles, shotguns, SMGs, sniper
  rifles, and launchers. Launcher pools are edited where they contain scoped
  sights; their non-scoped `RL_Sight_Torgue` remains, so no launcher stock
  no-sight part is needed.

The 36 untouched fixed lists include the Toothpick, SwordSplosion, Buffalo,
Longbow, and Elephant Gun. The 2 untouched pools are `AR_Vladof_3_Rapier` and
`AR_Vladof_3_Hail`, which already have no scoped sights.

## Known gaps

- Six runtime lists are absent from the 2019 dump and are left untouched:
  - `GD_Anemone_Weapons.A_Weapons.AR_Bandit_3_Rare_Alien_Shock:WeaponPartListCollectionDefinition_337`
  - `GD_Anemone_Weapons.A_Weapons.AR_Bandit_3_Rare_Alien_Slag:WeaponPartListCollectionDefinition_338`
  - `GD_Flynt.Weapons.AR_Flynt:WeaponPartListCollectionDefinition_328`
  - `GD_Leprechaun.Weapons.SG_Leprechaun:WeaponPartListCollectionDefinition_330`
  - `GD_Orchid_BossWeapons.AssaultRifle.AR_Jakobs_3_Stinkpot_Nodrop:WeaponPartListCollectionDefinition_335`
  - `GD_Weap_SniperRifles.A_Weapons.Sniper_Maliwan_4_Mordecai:WeaponPartListCollectionDefinition_329`
- Two runtime lists exist in the dump but the game cannot resolve them when
  text mods execute. Editing them only produces `Unrecognized class or object`
  warnings, so they are skipped:
  - `GD_Aster_Weapons.Snipers.SR_Maliwan_4_Aquamarine:WeaponPartListCollectionDefinition_327`
    — the Aquamarine gemstone sniper; new Aquamarines can still roll a scope.
  - `GD_Iris_MotorMama.Weapons.LauncherCustom:PartList` — Motor Momma's
    NPC-only launcher, not player-obtainable.
- In-game behaviour, including vendor restock and enemy respawn timing, has not
  been tested. The mod affects new generation only.
- Content added after the pinned 2019 dumps is not covered.
- Only Borderlands 2 is supported.

## Generator

`generate.py` requires Python 3.10+ and uses only the standard library. It reads
the xz-compressed dumps in `data/`, generates both the BLCMM XML entries and the
flat `#Commands:` section from the same data, and writes the patch.

```sh
python3 generate.py                                                     # strict (default)
python3 generate.py /tmp/patch.txt                                      # custom output path
python3 generate.py --policy conservative /tmp/conservative.txt         # UCP fallback
```

The dumps are vendored and pinned. See [`data/README.md`](data/README.md) for
their source and commit. Regeneration works offline.

## Testing

Run the static suite from the repository root:

```sh
python3 -m unittest -v test_generate.py
```

It needs no game install and checks:

- The committed `NoIntrusiveScopes.txt` is byte-identical to a fresh
  `python3 generate.py` run, and two runs produce the same bytes.
- The default output uses the strict policy and contains no CRLF bytes.
- Every original sight entry is kept, and every scoped entry is disabled.
- The known edited and untouched lists, per-family counts, and added stock parts.
- No cross-family or `Part=None` entries appear.
- The BLCMM XML and flat `#Commands:` section agree.
- The parser, dump reader, CAID lookup, and both policies.

To inspect the conservative fallback without touching the committed patch:

```sh
python3 generate.py --policy conservative /tmp/conservative.txt
```

In-game testing is manual and outside this suite. Back up saves, copy the patch
to `Binaries`, enable it in the mod menu, and check only newly generated guns
(drops, vendors, chests, mission rewards). Existing guns should keep their
scopes.
