# No Intrusive Scopes

A standalone Borderlands 2 text mod that stops newly generated weapons from
rolling scoped sights. Iron sights, red dots, holograms, and no-sight options
remain. Existing guns keep their current scopes.

Version **1.2.0**. Credit: **Hunter1712**. `NoIntrusiveScopes.txt` is a standard
BLCMM v1 file grouped by weapon family.

## Install

1. Back up your saves (see [Save safety](#save-safety)).
2. Copy `NoIntrusiveScopes.txt` into Borderlands 2's `Binaries` directory.
3. Enable it in the text mod loader's mods menu.

No game files are edited. To uninstall, disable the mod or remove the file.

With the Unofficial Community Patch, load **UCP first, then this mod**. Without
UCP it works standalone.

## Save safety

Back up `Documents/My Games/Borderlands 2/WillowGame/SaveData` before installing.

The mod only rewrites generation lists. Every original sight entry stays listed
so the save sanity check still recognises saved guns; no part definitions are
changed, and existing gear is not re-rolled or deleted.

If guns vanish or behave oddly, restore the backup and either disable the mod or
regenerate with the conservative policy below.

## How it works

For each edited list, the `SightPartData` array is replaced but every original
entry is kept. Scoped entries get an empty stage range, so they cannot be
selected at any level. Lists left without a non-scoped option get a stock
no-sight part for their weapon family.

This is the **strict policy**, the default. Starting-gun and full-game play were
verified in-game with no scoped sights.

The conservative UCP-proven fallback instead keeps each scoped entry's minimum
and caps its maximum at level 1, leaving a tiny level-1 loophole:

```sh
python3 generate.py --policy conservative NoIntrusiveScopes-conservative.txt
```

Copy the result to `Binaries` as usual.

## Coverage

Weapon balances reference 360 runtime lists; 354 exist in the pinned dumps.

- **306 edited**: 303 random pools with scoped sights, plus Amigo Sincero,
  Overcompensator, and Chaude Mama.
- **54 untouched**: 6 absent from the dump, 7 with no sight data, 2 unresolvable
  at execution time, 2 pools with no scoped sights, 36 fixed lists with only
  non-scoped sights, and Fremington's Edge (keeps its unique 25× scope).
- 52 edited lists gained a stock no-sight part; the rest already had iron,
  hologram, or stock coverage.
- All weapon types are covered, including launchers where their pools contain
  scopes.

## Known gaps

- Six runtime lists are absent from the 2019 dump and are untouched.
- Two lists cannot be resolved when text mods execute and are skipped. The
  Aquamarine sniper is one, so new Aquamarines can still roll a scope; the other
  is Motor Momma's NPC-only launcher.
- The affected named exceptions (Toothpick, SwordSplosion, Buffalo, Longbow,
  Elephant Gun, Fremington's Edge) keep their intended sights.
- Vendor restock and enemy respawn timing are inferred, not verified.
- Content added after the 2019 dumps is not covered.

Borderlands 2 only.

## Generator and tests

`generate.py` needs Python 3.10+ and only the standard library. The dumps are
vendored and pinned in `data/`; regeneration works offline.

```sh
python3 generate.py                                             # strict (default)
python3 generate.py --policy conservative /tmp/conservative.txt # fallback
python3 -m unittest -v test_generate.py                         # static suite
```

The suite needs no game install. It checks that the committed patch matches a
fresh generation byte-for-byte, that every original sight entry is kept and
every scoped entry is disabled, and covers the parser, dump reader, CAID lookup,
and both policies. In-game testing is manual and outside the suite.
