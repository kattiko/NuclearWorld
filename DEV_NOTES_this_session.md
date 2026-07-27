# NuclearWorld – dev session notes

This documents everything changed in this pass, why, and what's still left
for you to do (mostly art/mapping). A reusable audit script is included at
`dev-tools/audit_mod.py` — rerun it any time with:

```
python3 dev-tools/audit_mod.py .
```

from the mod's root folder. It requires only `pyyaml` (`pip install pyyaml`).
It checks for: items with no display name, UFOpaedia articles with no text,
items with no UFOpaedia article at all, weapon/armor items with no research
or purchase gate, and melee weapons using stun damage instead of melee damage.

---

## 1. Bugs fixed

### Melee weapons dealing stun damage instead of melee damage
`STR_WOODEN_CLUB` and `STR_STONE_HAMMER` had `damageType: 6` (Stun) instead of
`damageType: 7` (Melee), unlike `STR_SHIV` and `STR_SPEAR` which were already
correct. This is almost certainly why they felt "harmless" — Stun damage in
OpenXCOM doesn't kill, it only knocks out, and interacts very differently with
armor/overkill than a normal damage type.
- **File:** `Ruleset/items.rul`
- **Change:** both weapons now use `damageType: 7`. Their existing
  `damageAlter` blocks (`ToWound`/`ToStun` bonuses) were left untouched — the
  wooden club's `ToStun: 0.4` now reads as "also has a chance to knock the
  target out on top of the melee damage," which is a nice flavor side effect
  of a blunt weapon rather than its entire damage type.

### `STR_POWER_ARMOR_CORPSE` had no display name
Every other corpse item in the mod (29 of them) uses `name: STR_CORPSE` as an
override so it displays as "Corpse" in the UI. `STR_POWER_ARMOR_CORPSE` was
the one exception — it had no `name` override and no language entry of its
own, so it would have shown as a blank/raw string key in-game.
- **File:** `Ruleset/items.rul` — added `name: STR_CORPSE` to match its
  siblings (`STR_CORPSE_WASTELANDER_ARMOR`, `STR_CORPSE_LEATHER_ARMOR`, etc).

### `STR_CITIZEN` had no display name at all
Unlike its sibling recruitable/capturable civilians (`STR_PREPPER`,
`STR_CHURCH_FOLLOWER`, `STR_ORDER_RECRUIT`, etc.), `STR_CITIZEN` had no
language entry.
- **File:** `Language/en-US.yml` — added `STR_CITIZEN: "Wasteland Citizen"`.

### Two weapons had no UFOpaedia article
`STR_DMR` and `STR_BANDAGE` both have working research topics but no
UFOpaedia entry, so researching them would never produce an article to read.
- **Files:** `Ruleset/ufopaedia.rul` (new article entries), `Language/en-US.yml`
  (new `STR_DMR_UFOPAEDIA` / `STR_BANDAGE_UFOPAEDIA` text, written to match the
  existing in-universe tone).

All of the above were found with the audit script (see checks 1, 2, 3 and 5).
Everything is now clean except two armors flagged as having "no research/
purchase gate" — I checked those by hand and they're a **false positive**:
`STR_HAZMAT_ARMOR` and `STR_HAZMAT_ACID_ARMOR` can't be bought directly (no
`costBuy`), and their manufacture recipes in `manufacture.rul` already require
`STR_SPECIALIZED_ARMOR` research. So they are gated, just not through the
item's own `requires` field. No change needed; noted here so you don't
re-investigate it later.

---

## 2. The final battle now requires research (was: a blind 18-month timer)

This was the core bug behind "the final battle happens way too early."

`missionScript.rul`'s `finalOnslaught` entry had `firstMonth: 18` as its
**only** gate — the `researchTriggers` line existed but was commented out
(`#STR_ENEMY_MUTANTS: true`), and no `STR_FINAL_ONSLAUGHT` research topic even
existed anywhere in `research.rul`. So the ending fires automatically 18
months in, completely independent of how far the player has actually gotten
in the story.

**Fix:** two new research topics were added, and I deliberately didn't just
uncomment the old trigger, because `STR_ENEMY_MUTANTS` is one half of a
mutually-exclusive branch (`STR_ALLY_MUTANTS` vs `STR_ENEMY_MUTANTS` disable
each other) — gating the ending on "enemy" specifically would make it
unreachable for anyone who chose to ally with the mutants.

- **`STR_ORIGIN_OF_THE_HORDE`** (new, capstone topic) — requires having made
  contact with **all five factions** (`STR_FACTION_CHURCH`,
  `STR_FACTION_RAIDERS`, `STR_FACTION_ORDER`, `STR_FACTION_MUTANTS`,
  `STR_FACTION_GHOULS` — the "faction" topics, not the ally/enemy branches, so
  it's reachable regardless of which side the player picked). Represents
  X-COM finally piecing together where the horde is massing and why.
- **`STR_FINAL_ONSLAUGHT`** (new) — depends on the topic above, cheap/fast on
  its own. Its name matches the `finalOnslaught` missionScript type by the
  same convention the mod already uses for `STR_BOUNTY_HUNTING`.
- `missionScript.rul` → `finalOnslaught` now has an active
  `researchTriggers: { STR_FINAL_ONSLAUGHT: true }`. `firstMonth` was lowered
  from 18 to 6 and kept only as a minimal safety floor, not the real gate.
- Both new topics got UFOpaedia journal entries + language text
  (`STR_ORIGIN_OF_THE_HORDE_UFOPAEDIA`, `STR_FINAL_ONSLAUGHT_UFOPAEDIA`)
  written in the same first-person-plural in-universe voice as the existing
  journal entries (`STR_WHAT_NOW_UFOPAEDIA`, etc).

**Net effect:** the player now has to actually explore the world (meet/decide
on every faction) before the capstone even becomes researchable, then do one
more short research project, before the final mission can start rolling at
all. This should meaningfully lengthen the mid/late game.

---

## 3. Bounty hunters can now actually raid your base

You were right about the root cause: `STR_BOUNTY_HUNTING` and `finalOnslaught`
both had `targetBaseOdds: 100` in `missionScript.rul`, but neither mission
spawned an actual UFO — they used `ufo: STR_BOUNTY_HUNTING_SITE` / `ufo:
STR_FINAL_ONSLAUGHT_SITE`, which (per OXCE's own mission logic) are **direct
mission-site spawns with no underlying craft object**. `targetBaseOdds` only
ever does anything when the engine has a real `Ufo` it can redirect toward a
discovered player base using its built-in retaliation trajectory — there's
nothing to redirect when it's just a site.

I found that the mod already has (unused/orphaned) proof that this pattern
works: `ufos.rul` defines three UFOs (`STR_CARAVAN_ORDER_UFO`,
`STR_CARAVAN_CHURCH_UFO`, `STR_CARAVAN_RAIDERS_UFO`) with their own
`battlescapeTerrainData` pointing at real maps that already ship with the mod
(`ORDER_CARAVAN.MAP`, `CHURCH_CARAVAN.MAP`, `RAIDER_CARAVAN.MAP` in `MAPS/`),
but none of them were ever referenced from `alienMissions.rul` — dead content.

**What I did for `STR_BOUNTY_HUNTING`:**
- Added a new, fully-statted UFO, **`STR_BOUNTY_HUNTER_TRANSPORT`**
  (`Ruleset/ufos.rul`), using the real field names OXCE expects for UFOs
  (`size`, `sprite`, `damageMax`, `speedMax`, `power`, `range`, `score`,
  `reload`, `breakOffTime`) — deliberately weak/slow so it's an easy, fair
  intercept. It reuses the existing `RAIDER_CARAVAN` map/terrain data (the
  orphaned raider caravan asset), so it has a working battlescape immediately
  with no new art needed.
- Added a matching **`alienDeployment`** of the same name
  (`Ruleset/alienDeployments.rul`) that defines the crew/loot table for when
  it's shot down or lands normally — cloned directly from the existing
  `STR_BOUNTY_HUNTING_SITE` table, so the fight itself feels unchanged.
- Added a new **`ufoTrajectory`**, `P_RAID` (`Ruleset/ufoTrajectories.rul`):
  enters at high altitude/full speed, then descends to land, with a
  `groundTimer` window during which it can be intercepted. Uses the mission's
  existing `spawnZone: 4` for both waypoints so it doesn't depend on guessing
  unfamiliar zone/region mappings.
- Updated the `STR_BOUNTY_HUNTING` alien mission (`Ruleset/alienMissions.rul`)
  to spawn `STR_BOUNTY_HUNTER_TRANSPORT` on trajectory `P_RAID` instead of the
  old direct site spawn.

With a real craft in play, `targetBaseOdds: 100` (already set on the
`bountyHunting` missionScript entry) can now actually fire: the engine can
redirect the transport toward a discovered player base and trigger a genuine
base-defense battle, using the mod's already-inherited (not deleted)
`STR_BASE_DEFENSE` alien deployment from the master ruleset. If it's *not*
redirected, it still lands and plays out as a normal ground fight with the
same enemies/loot as before.

**What I deliberately did *not* do the same way for the final battle:**
`STR_FINAL_ONSLAUGHT_SITE` has `finalDestination: true` plus
`winCutscene`/`loseCutscene`/`abortCutscene` — it's the scripted ending.
`STR_BASE_DEFENSE` is a single, shared deployment hard-coded into the engine
for *every* base attack, regardless of which mission triggered it. If I'd
made the final wave a real UFO with `targetBaseOdds` active, a successful
retaliation roll would silently reroute the ending into an ordinary,
non-scripted base-defense fight with no cutscenes and no win/loss handling —
at best a confusing anticlimax, at worst something that could repeat
indefinitely without ever giving you a real ending. I don't have a verified,
safe way to give just the *final* base attack its own special deployment
without either an OXCE feature I couldn't confirm exists or a C++ change,
so I left `STR_FINAL_ONSLAUGHT` as a guaranteed, direct-to-objective site
(no `targetBaseOdds`) so the ending reliably fires once
`STR_FINAL_ONSLAUGHT` research completes. It's already framed as a siege
(50×50 map, ruined-city terrains, friendly NPCs fighting alongside you), just
not literally your player-built base tileset.

If you want to push further on this (have the *actual* ending be a raid on
your literal base), the next step would be asking on the OXCE forum/Discord
whether current nightly builds support per-mission base-defense deployment
overrides — if so, I'm happy to wire it up once that's confirmed.

---

## 4. Base assembly system / post-apocalyptic base assets

This is the one item I could not meaningfully deliver, and I want to be
upfront about why rather than fake it: `facilities.rul` still points every
facility's `mapName` at the vanilla `XBASE_00`–`XBASE_16` tiles (Access Lift,
Living Quarters, Lab, Workshop, General Stores, Alien Containment, Psionic
Lab, Hangar). There are no matching `.MAP`/`.RMP` files or MCD tilesets for
those names inside this mod's own `MAPS`/`TERRAIN` folders, so the game falls
back to the stock sci-fi XCOM base graphics whenever a base-defense mission
happens.

Building the "your base assembled from post-apocalyptic shacks" look you
described requires actual new tile art: an MCD tileset (wall/floor/object
graphics) drawn in a shack/scavenged-shelter style, then new `.MAP`/`.RMP`
files built in the Map Editor for each facility footprint, replacing the
`mapName:` values in `facilities.rul`. That's pixel art and level-editor work
— outside what I can generate. What I *can* do once you (or an artist) have
produced the tileset and maps: wire up `facilities.rul`, `terrains.rul`, and
the `XBASE` map script to point at your new assets, and help iterate on the
map-script rules (block types, road/corridor requirements) once you have
something to test against. Let me know when you have art and I'll do that
part.

---

## 6. Follow-up pass: power armor restore chain + weapon distribution

### Power armor corpses couldn't be restored
`STR_POWER_ARMOR` (the base/mid-tier power armor) had `corpseBattle:
[STR_POWER_ARMOR_CORPSE]` in `armors.rul`, but the manufacture recipe that
turns a busted power armor corpse back into a wearable `STR_POWER_ARMOR`
required `STR_CORPSE_POWER_ARMOR` (word order swapped) — a *different*,
orphaned item that nothing in the game actually dropped. So the recipe could
never fire in practice, even though it existed. The other two power armor
tiers (`STR_HANDCRAFTED_POWER_ARMOR`, `STR_PROTOTYPE_POWER_ARMOR`) were
already wired correctly and didn't need changes.
- **Fix:** `Ruleset/armors.rul` — `STR_POWER_ARMOR`'s `corpseBattle` now points
  at `STR_CORPSE_POWER_ARMOR`, matching the naming convention every other
  armor in the mod already uses (`STR_CORPSE_<ARMOR_NAME>`) and matching the
  manufacture recipe that already existed for it. All three power armor tiers
  can now be restored via manufacture from their battlefield corpse.
- Note: `STR_POWER_ARMOR_CORPSE` (the old, now-unreferenced item) is left in
  `items.rul` — harmless, just unused. No need to delete it, but flagging it
  here in case you want to clean it up later.

### Stronger weapons were inconsistently missing before the finale
Checked every alien deployment's `itemSets` for Laser Rifle, Laser Gatling,
Gauss Rifle, Pulse Rifle, Plasma Gun, and Minigun. They *do* already show up
in a number of mid/late missions (medium patrols, caravans, terror sites,
faction-vs-faction battles, the military base/lab/prepper-shelter missions,
bounty hunting) — but coverage was inconsistent, and one whole faction had
none at all:
- Sibling mission variants were missing a strong-weapon option that their
  counterparts already had: `STR_MEDIUM_PATROL_CHURCH_SITE` had a Plasma Gun
  but `STR_MEDIUM_PATROL_RAIDERS_SITE`/`STR_MEDIUM_PATROL_ORDER_SITE` didn't;
  three of the four faction-battle sites had a strong weapon but
  `STR_CHURCH_VS_RAIDERS_BATTLE_SITE`/`STR_ORDER_VS_RAIDERS_BATTLE_SITE`
  didn't.
- More importantly: the **mutants** — your actual final antagonist —
  never carried anything stronger than a pre-war service rifle/bow/crossbow
  anywhere before the ending, even at `STR_RAID_MUTANT_SITE` (their toughest
  non-finale encounter). Ghoul caravans had the same problem. This is
  probably the main reason strong weapons felt endgame-only.

**Fix** — replaced one weak itemSet option with a strong-weapon one at the
toughest rank of each gap, mirroring the exact pattern/frequency their
already-correct siblings use (so drop rates and squad sizes are unchanged,
only the weapon variety):
- `STR_MEDIUM_PATROL_RAIDERS_SITE` → added Pulse Rifle (Raiders' established
  signature strong weapon)
- `STR_MEDIUM_PATROL_ORDER_SITE` → upgraded a Bozar slot to Laser Gatling
  (Order's signature)
- `STR_CHURCH_VS_RAIDERS_BATTLE_SITE` → added Plasma Gun (Church's signature)
- `STR_ORDER_VS_RAIDERS_BATTLE_SITE` → added Laser Rifle (Order's signature)
- `STR_RAID_MUTANT_SITE` (top rank) → added Laser Rifle
- `STR_CARAVAN_GHOUL_SITE` (top rank) → added Pulse Rifle

Small patrols were deliberately left weak-only — that tier reads as
intentional (every faction's small patrol is unarmed/basic), so I didn't
touch it. All edits were re-verified against a script scan afterward to
confirm every targeted deployment now actually contains the intended weapon.



- `Ruleset/items.rul` — melee damage type fix (2 items), corpse name fix (1 item)
- `Ruleset/ufopaedia.rul` — 2 missing item articles + 2 new story articles
- `Ruleset/research.rul` — 2 new research topics (endgame gate)
- `Ruleset/missionScript.rul` — finalOnslaught now research-gated
- `Ruleset/ufos.rul` — new `STR_BOUNTY_HUNTER_TRANSPORT` UFO
- `Ruleset/ufoTrajectories.rul` — new `P_RAID` trajectory
- `Ruleset/alienDeployments.rul` — new matching crew/loot deployment
- `Ruleset/alienMissions.rul` — `STR_BOUNTY_HUNTING` now spawns a real craft
- `Language/en-US.yml` — 5 new/changed strings (`STR_CITIZEN`,
  `STR_DMR_UFOPAEDIA`, `STR_BANDAGE_UFOPAEDIA`,
  `STR_ORIGIN_OF_THE_HORDE_UFOPAEDIA`, `STR_FINAL_ONSLAUGHT_UFOPAEDIA`)
- `dev-tools/audit_mod.py` — new, reusable

All files were round-tripped through a YAML parser after editing to confirm
they're still syntactically valid, and cross-referenced (UFO ↔ deployment ↔
trajectory ↔ mission ↔ research ↔ language) to make sure every new name
actually matches up everywhere it's used. I have not been able to launch
OpenXCOM Extended itself to playtest the base-attack behavior in a live
game — please test the bounty hunter encounter and the new research gate
in-game before you rely on them.
---

## 7. Files touched (across both passes)

- `Ruleset/items.rul` — melee damage type fix (2 items), corpse name fix (1 item)
- `Ruleset/armors.rul` — fixed STR_POWER_ARMOR's corpseBattle reference
- `Ruleset/ufopaedia.rul` — 2 missing item articles + 2 new story articles
- `Ruleset/research.rul` — 2 new research topics (endgame gate)
- `Ruleset/missionScript.rul` — finalOnslaught now research-gated
- `Ruleset/ufos.rul` — new `STR_BOUNTY_HUNTER_TRANSPORT` UFO
- `Ruleset/ufoTrajectories.rul` — new `P_RAID` trajectory
- `Ruleset/alienDeployments.rul` — new bounty-hunter crew/loot deployment,
  plus 6 deployments given a strong-weapon option they were missing
- `Ruleset/alienMissions.rul` — `STR_BOUNTY_HUNTING` now spawns a real craft
- `Language/en-US.yml` — 5 new/changed strings (`STR_CITIZEN`,
  `STR_DMR_UFOPAEDIA`, `STR_BANDAGE_UFOPAEDIA`,
  `STR_ORIGIN_OF_THE_HORDE_UFOPAEDIA`, `STR_FINAL_ONSLAUGHT_UFOPAEDIA`)
- `dev-tools/audit_mod.py` — new, reusable

All files were round-tripped through a YAML parser after every edit to
confirm they're still syntactically valid, and cross-referenced (UFO ↔
deployment ↔ trajectory ↔ mission ↔ research ↔ language, and armor ↔ corpse
↔ manufacture recipe) to make sure every name actually matches up everywhere
it's used. I have not been able to launch OpenXCOM Extended itself to
playtest any of this in a live game — please test in-game before relying on
it, especially the base-attack behavior and the new research gate.

---

## 8. Scientist pipeline: made rescue missions more common, training faster

Follow-up to the "hard to get scientists/engineers" investigation above.
Didn't touch the disabled `hireScientistsUnlockResearch` (that's a bigger
design decision to leave for you), but tightened the one working pipeline:

- `Ruleset/missionScript.rul` → `bloodForScientists`: `startDelay` dropped
  from 90 to 20 (now in line with almost every other mission script in the
  file, which all use 20 - this one was oddly the highest), and `randomDelay`
  cut from 43500 to 10000. Since each missionScript runs its own independent
  timer, this doesn't affect any other mission's frequency - it just lets
  `STR_RESCUEABLE_SCIENTISTS` come up roughly every ~7 days instead of ~30
  once unlocked.
- `Ruleset/manufacture.rul` → `STR_UNTRAINED_SCIENTIST` training recipe:
  `time` reduced from 128 to 94 hours, as requested.

Scientists are still one-at-a-time and still gated behind the
`STR_RESCUEABLE_SCIENTISTS` research chain, but the whole loop (find mission →
rescue → train) should now come around noticeably faster.
