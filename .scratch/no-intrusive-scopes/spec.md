Status: ready-for-agent

# No Intrusive Scopes — Spec

## Problem Statement

Borderlands 2 weapons generate with scoped sights that put a full-screen scope overlay and heavy zoom on screen when aiming. The overlay blocks peripheral vision and makes aiming feel intrusive, and the game has no global setting to turn scopes off. Existing community fixes either only add an iron-sight option at equal odds (so scoped sights still appear) or target sniper rifles only.

The player wants every newly generated gun — all weapon types, rarities, sources, and DLCs, including named weapons — to spawn with non-intrusive sights only: iron sights, red dots, holograms, or no sight at all. Existing guns in saves must keep working and must not be deleted.

## Solution

A standalone BLCMM text mod named **No Intrusive Scopes**, loaded through the standard BL2 text mod loader. It rewrites the game's runtime sight part lists so scoped sights cannot spawn on new drops. It keeps every original sight entry listed (so the save sanity check does not delete existing guns), retains all non-scoped sights, and adds a stock no-sight option wherever a list would otherwise have no non-scoped roll.

The one named weapon whose unique scope is its identity — Fremington's Edge's 25× scope — is exempt. The mod affects new generation only; existing guns keep their current scopes because no sight part definitions are changed.

A deterministic generator produces the 300-plus overrides from a vendored, pinned set of BL2 object dumps. A static test at the generator seam verifies the generated patch. In-game testing is deliberately out of scope for this delivery.

## User Stories

1. As a BL2 player, I want newly generated guns to roll only non-scoped sights, so aiming does not put a full-screen scope overlay in front of me.
2. As a player, I want every weapon type covered — pistols, assault rifles, shotguns, SMGs, sniper rifles, and launchers — so no weapon class slips through.
3. As a player, I want sniper rifles included, so they also use non-intrusive sights.
4. As a player, I want iron sights, red dots, and holograms retained, so guns still have sight variety and remain usable.
5. As a player, I want a stock no-sight option added wherever a sight pool has only scoped sights, so every edited pool has a valid non-scoped roll.
6. As a player, I want all rarities and generation sources covered — drops, vendors, chests, enemy-held weapons, and mission rewards — so new gear behaves consistently.
7. As a player, I want DLC weapon types covered, so the mod applies across the full game, not just the base campaign.
8. As a player, I want named and unique weapons with fixed generic scopes to become scopeless too, so "all guns" is true.
9. As a player, I want Fremington's Edge to keep its unique 25× scope, so the weapon keeps the identity it was designed around.
10. As a player, I want weapons that are already scopeless left untouched, so they do not gain scopes or change behavior.
11. As a player, I want existing guns in my save to keep their current scopes, so the mod does not silently re-roll my inventory.
12. As a player, I want existing guns never to be deleted by the save sanity check, so installing the mod cannot destroy gear.
13. As a player, I want the mod to be standalone, so it works with or without the Unofficial Community Patch.
14. As a player, I want to load it alongside UCP through the text mod loader, so I do not have to merge files or give up UCP.
15. As a player, I want clear load-order guidance, so UCP and this mod coexist without surprise overrides.
16. As a player, I want a simple install and uninstall flow — copy the patch, enable or disable it in the mods menu — so I do not need to edit game files.
17. As a player, I want a README that explains the save-safety risk and recommends backing up saves, so I do not lose gear.
18. As a player, I want the README to name the untested strict disable method and the conservative fallback, so I can recover if something goes wrong.
19. As a player, I want the README to list known gaps — the six missing runtime lists, the two skipped runtime lists, existing guns, and Fremington's Edge — so there are no surprises.
20. As a player, I want the mod to be a standard BLCMM file I can open and inspect, so I can see exactly what it changes.
21. As a player, I want the patch grouped and labeled clearly in the BLCMM interface, so I can find and audit it.
22. As a player, I want a versioned patch with a clear name and credit, so I know what I am installing and who made it.
23. As a player, I want the mod to avoid unproven `Part=None` entries in sight slots, so it relies on stock parts the game already ships.
24. As a player, I want launchers left alone unless they actually contain scoped sights, so the patch makes no unnecessary changes.
25. As a player, I want already-scopeless pools untouched, so the patch stays minimal and focused.
26. As a player, I want the strict inverted-range disable documented as untested, so I understand the risk before installing.
27. As a player, I want a conservative fallback pattern documented, so I can switch methods if guns disappear or behave oddly.
28. As a player, I want no game launch or save modification as part of delivery, so my install and saves stay untouched.
29. As a player, I want the mod to affect only new generation, so my existing inventory remains stable.
30. As a player, I want old scoped parts to stay listed but disabled, so saved guns that reference them survive the sanity check.
31. As a player, I want the README to include coverage counts — lists changed, exemptions, gaps — so coverage is auditable.
32. As a player, I want all DLC content present in the dumps covered, so coverage is not base-game-only.
33. As a player, I want the text mod loader to allow enabling the mod through its normal interface, so installation stays simple.
34. As a player, I want the mod to work offline in single-player, so it does not depend on online services.
35. As a player, I want no external runtime dependencies, so the patch is self-contained.
36. As a player, I want the patch to be a single file, so sharing and installing are easy.
37. As a maintainer, I want a generator that produces the patch from pinned dumps, so 300-plus overrides are reproducible and less error-prone than hand-editing.
38. As a maintainer, I want the dumps vendored, so regeneration works offline and upstream changes cannot break the build.
39. As a maintainer, I want the pinned dump commit recorded, so the data source is traceable.
40. As a maintainer, I want the generator to preserve every existing sight entry, so the save sanity check continues to pass.
41. As a maintainer, I want the generator to verify that scoped entries are disabled and non-scoped coverage exists, so mistakes fail loudly.
42. As a maintainer, I want the generator to leave exempt and missing lists untouched, so safe gaps stay safe.
43. As a maintainer, I want the generator to determine CAID indices per list, so the strict range works even for lists with nonstandard index positions.
44. As a maintainer, I want the generator to add or normalize only the correct stock no-sight part for each weapon family, so no cross-family sights appear.
45. As a maintainer, I want the generator to handle the one odd list with CAID indices 2 and 3, so it does not assume 0 and 1.
46. As a maintainer, I want the generator's output deterministic, so regeneration produces stable diffs.
47. As a maintainer, I want the BLCMM XML metadata and the flat command section generated from one data source, so the GUI view and executed commands cannot drift.
48. As a maintainer, I want a static test at the generator seam, so regressions are caught without launching the game.
49. As a maintainer, I want the vendored data kept to the minimum needed, so the repository stays small.
50. As a maintainer, I want the generator to use only the Python standard library, so there is no dependency setup.

## Implementation Decisions

- **Two user-facing deliverables:** the generated BLCMM v1 patch and a README. The patch is a single self-contained file; the README covers install, load order, save safety, coverage, gaps, and generator usage.
- **Tooling deliverables:** a deterministic generator and a vendored, compressed set of three BL2 object dumps. The generator uses only the Python standard library.
- **Pinned data source:** the ft-explorer BL2 dumps for `WeaponPartDefinition`, `WeaponPartListCollectionDefinition`, and `WeaponBalanceDefinition` at commit `29a24d28d464`, dated 2019-06-26. The compressed dumps total roughly 113 KB.
- **Target selection:** follow `WeaponBalanceDefinition.RuntimePartListCollection`, not the static `:PartList` objects. There are 360 distinct runtime references; 354 are present in the dumps; 6 are missing and left untouched. Two more are present but cannot be resolved when text mods execute, so they are also exempt.
- **Classification:** of the 354 present lists, 347 have at least one non-`None` sight. Forty are fixed single-sight lists; 307 are random pools. Seven have no non-`None` sight (three disabled, four enabled-but-empty) and are left alone.
- **Sight classification:** a sight is scoped when its `WeaponPartDefinition.bScoped` is true. The dumps contain 13 non-scoped `WP_Sight` parts, plus the anomalously typed `SMG_Sight_None` (`WP_Stock`), and 6 stock `_None` parts.
- **Transform:** for each runtime list containing at least one scoped sight, replace the whole `SightPartData` property with a new array that preserves every original entry. No entry is ever removed; this keeps the save sanity check satisfied for existing guns.
- **Strict disable:** every original scoped entry keeps its part, manufacturer, and weight fields but gets `MinGameStageIndex` pointing at the list's CAID value 100 and `MaxGameStageIndex` pointing at the list's CAID value 1, producing an empty stage range at every level. This is a deliberate, untested choice; the README documents the conservative alternative. The generator can emit that alternative with `--policy conservative`: it keeps each scoped entry's existing minimum and sets `MaxGameStageIndex` to the list's CAID value 1.
- **CAID handling:** indices are discovered per list by scanning `ConsolidatedAttributeInitData`. 353 lists use indices 0 and 1; one list uses 2 and 3. If either value is absent, generation fails loudly.
- **Non-scoped coverage:** every edited list must contain at least one non-scoped option with a full stage range. Existing non-scoped entries are kept unchanged. An existing stock `_None` entry is normalized to the full range. If absent, one is added using the correct family part: pistol, assault rifle, shotgun, or SMG `Sight_None`; `Sniper_Sight_None_Buffalo` for sniper rifles. `Part=None` is not used in sight slots because no stock list uses it there.
- **Fixed lists:** three fixed-scope named weapons are converted with the same transform — Amigo Sincero (generic Jakobs scope), Overcompensator (generic Hyperion scope), and Chaude Mama (generic Maliwan scope). Fremington's Edge is excluded because its 25× scope is a unique gimmick part.
- **Left untouched:** the six missing runtime lists, the two runtime lists that cannot be resolved at text-mod execution time, the seven no-sight lists, the two pools with no scoped sights, fixed non-scoped named sights (Toothpick, SwordSplosion), and the three already-scopeless sniper uniques (Buffalo, Longbow, Elephant Gun).
- **Part definitions are not edited.** No changes to `bScoped`, scope meshes, zoom FOV, reticles, or other part-property values. Therefore existing guns keep their scopes and other mods that touch part definitions are unaffected.
- **BLCMM format:** a v1 file with BL2/offline type, default profile, a clearly named category with explanatory comments, `<code>` entries for GUI inspection, and a flat `#Commands:` section that the text mod loader executes. Both representations are generated from the same data so they cannot drift. No `#Hotfixes:` section is produced.
- **Versioning and credit:** version 1.0.0; header credit "ancent".
- **Determinism:** target lists, entries, and output lines are emitted in stable sorted order.
- **No game interaction:** the delivery does not install into the game, launch it, or touch saves.
- **Test seams:** the generator command line for end-to-end patch behavior, plus the public interfaces of the sight-data, dump-reader and planning modules for format, validation and policy behavior. The generated patch's byte identity remains the end-to-end guard.

Trimmed entry shape that encodes the strict-disable decision (from the dump format):

```
(Part=WeaponPartDefinition'...', Manufacturers=, MinGameStageIndex=<index of 100>, MaxGameStageIndex=<index of 1>, DefaultWeightIndex=...)
```

## Testing Decisions

- **Good test:** exercise external behavior through each module's public interface. Run the generator end to end against the vendored dumps and assert on the generated patch; use fixed-string fixtures for the sight format, dump validation and per-list planning.
- **Seams:** the generator command line guards the whole patch. The sight-data, dump-reader and planning modules each have one seam that callers and tests cross together; parser internals stay private.
- **No prior art:** the repository has no test suite; this is the first automated test.
- **Assertions:**
  - The generator exits successfully and writes the patch.
  - The number of edited runtime lists matches an independently derived expectation (303 random pools plus 3 fixed named weapons).
  - Every original sight entry in every edited list is still present.
  - Every original scoped entry is disabled with the inverted range, using the correct CAID indices for that list.
  - Every edited list has at least one full-range non-scoped option, using the correct family stock part.
  - No edit is emitted for the six missing lists, the two runtime lists that cannot be resolved at text-mod execution time, the seven no-sight lists, the two already-scopeless pools, or Fremington's Edge.
  - No `Part=None` appears inside any generated `SightPartData`.
  - The patch parses as BLCMM and the flat command section matches the XML entries.
  - Two consecutive runs produce byte-identical output.
- **Static only:** no game launch, no save loading, no runtime verification. The README states this explicitly.
- **Failure behavior:** the generator should fail with a clear message if a CAID value is missing, a target list is unclassified, or a stock no-sight part is unavailable for a family.

## Out of Scope

- Installing the mod into the game, launching the game, editing saves, or runtime verification.
- Retroactively removing scopes from guns already in saves.
- Editing sight part definitions: `bScoped`, scope meshes, zoom FOV, reticles, or related properties.
- Replacing or merging with UCP; the mod is standalone but coexistable.
- The six runtime lists absent from the 2019 dump.
- The two runtime lists the game cannot resolve when text mods execute.
- Fremington's Edge's unique 25× scope.
- Weapons and pools that are already scopeless.
- Non-BL2 games (The Pre-Sequel, Borderlands 3, Wonderlands).
- SDK-mod behavior, Python SDK hooks, or save editing.
- In-game toggles, configuration menus, or per-weapon user options.
- Fixing or validating the strict inverted range at runtime.
- DLC content not present in the pinned dumps.
- Launcher-specific sight replacement unless a launcher list is found to contain scoped sights.
- Cosmetic scope-model removal for existing guns.

## Further Notes

- The safe save pattern is the core constraint: old parts stay listed, so the game's part-list sanity check does not delete saved guns that reference them.
- The strict inverted range is logically sound but unverified in-game. The conservative fallback is the UCP-proven pattern: keep old scoped entries with `MaxGameStageIndex` set to the index of 1. It leaves a tiny level-1 loophole but is known-tolerated by the game.
- New drops only: vendor restock and enemy respawn timing are inferred, not verified.
- The `SMG_Sight_None` part is anomalously typed `WP_Stock` in the stock data; that anomaly is pre-existing and left unchanged.
- UCP 5.0.4 contains one inactive sight override (the Emperor-to-Torrent alternative). It is not executed by default and does not conflict with this mod.
- The text mod loader scans files directly in the game's `Binaries` directory and can enable multiple BLCMM files; UCP's entry has no hotfix service lock, so both can run. Load order is UCP first, then No Intrusive Scopes.
- The repository has no glossary or ADR covering this area; domain terms are defined inline in this spec.
- The mod is data-only; it does not add runtime code, menus, or external dependencies.
- The README should state that if guns vanish after install, the user should restore the save backup and switch to the conservative pattern or disable the mod.
