# No Intrusive Scopes

A standalone Borderlands 2 text mod that stops newly generated weapons from
rolling scoped sights. Iron sights, red dots, holograms, and no-sight options
remain. Existing guns keep the scopes they already have.

Version **1.0.0**. Credit: **ancent**. The patch is a standard BLCMM v1 file
(`NoIntrusiveScopes.txt`) grouped by weapon family so it can be opened and
inspected.

## Install

1. Back up your saves (see [Save safety](#save-safety)).
2. Copy `NoIntrusiveScopes.txt` into Borderlands 2's `Binaries` directory, next
   to the game executable.
3. Enable it in the text mod loader's mods menu.

No game files are edited. Disable the mod in the menu, or remove the file, to
uninstall.

## Load order

- The mod is standalone and works without the Unofficial Community Patch.
- With UCP: load **UCP first, then No Intrusive Scopes**. The loader can enable
  both BLCMM files at the same time.
- UCP 5.0.4 contains one inactive sight override (the Emperor-to-Torrent
  alternative). It is not executed by default and does not conflict.

## Save safety

Back up `Documents/My Games/Borderlands 2/WillowGame/SaveData` before
installing.

The mod rewrites generation lists only:

- Every original sight entry stays listed, so the save sanity check still
  recognises saved guns.
- Scoped entries are disabled with an empty stage range, not removed.
- No part definitions (`bScoped`, scope meshes, zoom FOV, reticles) are changed,
  so existing guns keep their current scopes.
- Existing gear is not re-rolled or deleted.

If guns vanish or behave oddly after installing, restore the save backup, then
either disable the mod or switch to the conservative pattern below.

## How it works

For every edited list, the whole `SightPartData` array is replaced. Every
original entry is kept. A scoped entry gets `MinGameStageIndex` pointing at the
list's CAID value 100 and `MaxGameStageIndex` pointing at the list's CAID value
1, producing an empty stage range at every level. If a list would have no
non-scoped option left, a stock no-sight part for that weapon family is added
with a full range.

### Strict disable (untested)

The inverted range above is logically sound but has **not** been verified
in-game. The generator has only been checked statically.

### Conservative fallback (UCP-proven)

If the strict range causes problems, regenerate with the fallback:

```sh
python3 generate.py --policy conservative /tmp/NoIntrusiveScopes-conservative.txt
```

Copy the result to `Binaries` as usual. For each scoped entry, it keeps the
existing minimum and sets `MaxGameStageIndex` to the list's CAID index for 1.
This leaves a tiny level-1 loophole but is known to be tolerated by the game. In
these dumps the index for 1 is `0` for every list except
`GD_Aster_Weapons.SMGs.SMG_Maliwan_3_Crit:WeaponPartListCollectionDefinition_244`,
which uses `2`.

## Coverage

Weapon balances reference 360 runtime lists; 354 exist in the pinned dumps.

- 347 lists have at least one sight: 40 fixed single-sight lists and 307 random
  pools.
- **306 lists are changed**: 303 random pools containing scoped sights plus 3
  fixed named weapons (Amigo Sincero, Overcompensator, Chaude Mama).
- 52 lists gained a stock no-sight option: 51 sniper lists
  (`Sniper_Sight_None_Buffalo`) and 1 shotgun list (`SG_Sight_None`).
- 95 edited lists already had a stock `_None` entry; 159 already had iron or
  other non-scoped coverage.
- 7 lists have no sight data and are untouched (3 disabled, 4
  enabled-but-empty).
- 2 pools already had no scoped sights and are untouched: `AR_Vladof_3_Rapier`
  and `AR_Vladof_3_Hail`.
- 36 fixed single-sight lists contain only non-scoped sights and are untouched,
  including the Toothpick, SwordSplosion, Buffalo, Longbow, and Elephant Gun.
- Fremington's Edge is exempt and keeps its unique 25× scope.

All weapon types are covered: pistols, assault rifles, shotguns, SMGs, sniper
rifles, and launchers. Launcher pools are changed where they contain scoped
sights; their non-scoped `RL_Sight_Torgue` remains, so no launcher stock
no-sight part is needed.

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
- Seven lists have no sight data and are left alone.
- Existing guns keep their current scopes; the mod does not retroactively
  remove scopes from inventory.
- Fremington's Edge keeps its unique 25× scope.
- In-game behaviour, including vendor restock and enemy respawn timing, has not
  been tested. The mod affects new generation only.
- Content added after the pinned 2019 dumps is not covered.
- Only Borderlands 2 is supported.

## Generator

`generate.py` uses only the Python standard library. It reads the xz-compressed
dumps in `data/`, generates both the BLCMM XML entries and the flat
`#Commands:` section from the same data, and writes the patch.

```sh
python3 generate.py                 # writes NoIntrusiveScopes.txt
python3 generate.py /tmp/patch.txt  # optional output path
python3 generate.py --policy conservative /tmp/conservative.txt  # UCP fallback
python3 -m unittest -v test_generate.py
```

The dumps are vendored and pinned. See [`data/README.md`](data/README.md) for
the source and commit. Regeneration works offline. The test is static: it does
not launch the game, load a save, install the mod, or modify game files.
