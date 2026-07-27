#!/usr/bin/env python3
"""
NuclearWorld mod audit script (v2 - corrected for actual _UFOPAEDIA text-key convention).

Finds:
  1) Items missing a plain display name string.
  2) UFOpaedia articles (ufopaedia.rul) whose 'text' key has no matching
     language string -> these show a blank/placeholder page in-game.
  3) Items that exist in items.rul but have NO ufopaedia.rul article at all
     (so they can never be read about, even once researched).
  4) Weapon/armor items with no research topic (needItem) and no 'requires'
     gate -> they can never be "researched"/unlocked through story progress.
  5) Melee weapons using stun damage instead of melee damage.
"""
import sys, os, yaml

def load(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def main(root):
    rules = os.path.join(root, 'Ruleset')
    items = [x for x in load(os.path.join(rules, 'items.rul'))['items'] if 'delete' not in x]
    research = [x for x in load(os.path.join(rules, 'research.rul'))['research'] if 'delete' not in x]
    pedia = [x for x in load(os.path.join(rules, 'ufopaedia.rul'))['ufopaedia'] if 'delete' not in x]
    lang = load(os.path.join(root, 'Language', 'en-US.yml'))['en-US']

    item_types = {x['type'] for x in items}
    research_names = {x['name'] for x in research}
    needitem_names = {x['name'] for x in research if x.get('needItem')}
    lang_keys = set(lang.keys())

    print("="*70); print("1) ITEMS MISSING A PLAIN DISPLAY NAME STRING"); print("="*70)
    name_key_of = {x['type']: x.get('name', x['type']) for x in items}
    missing_name = sorted(t for t, key in name_key_of.items() if key not in lang_keys)
    print(f"Count: {len(missing_name)}")
    for t in missing_name:
        print(" ", t)

    print(); print("="*70); print("2) UFOPAEDIA ARTICLES WITH MISSING TEXT STRING"); print("="*70)
    missing_pedia_text = []
    for p in pedia:
        text_key = p.get('text')
        if text_key and text_key not in lang_keys:
            missing_pedia_text.append((p['id'], text_key))
    print(f"Count: {len(missing_pedia_text)}")
    for id_, key in missing_pedia_text:
        print(f"  {id_:35s} -> missing '{key}'")

    print(); print("="*70); print("3) ITEMS WITH NO UFOPAEDIA ARTICLE AT ALL"); print("="*70)
    pedia_ids = {p['id'] for p in pedia}
    # focus on items a player would expect an article for: weapons, armor, ammo, consumables
    interesting_bt = {1,2,3,4,5,6,8}
    no_pedia = []
    for it in items:
        t = it['type']
        bt = it.get('battleType')
        cats = it.get('categories') or []
        is_armor = 'STR_ARMORS' in cats
        if t in pedia_ids:
            continue
        if bt in interesting_bt or is_armor:
            no_pedia.append(t)
    print(f"Count: {len(no_pedia)}")
    for t in no_pedia:
        print(" ", t)

    print(); print("="*70); print("4) WEAPON/ARMOR ITEMS WITH NO RESEARCH/UNLOCK PATH"); print("="*70)
    relevant, unresearchable = [], []
    for it in items:
        t = it['type']; bt = it.get('battleType'); cats = it.get('categories') or []
        is_weapon_like = bt in (1,3,4,5,8)
        is_armor = 'STR_ARMORS' in cats
        if not (is_weapon_like or is_armor):
            continue
        unlocked = bool(it.get('requires')) or t in needitem_names
        relevant.append(t)
        if not unlocked:
            unresearchable.append((t, bt, is_armor))
    print(f"Checked {len(relevant)} weapon/armor items. Unresearchable: {len(unresearchable)}")
    for t, bt, is_armor in unresearchable:
        kind = 'ARMOR' if is_armor else f'battleType={bt}'
        print(f"  {t:35s} [{kind}]")

    print(); print("="*70); print("5) MELEE WEAPON DAMAGE TYPE CHECK (battleType=3)"); print("="*70)
    DT = {0:'NONE',1:'AP',2:'INCENDIARY',3:'HE',4:'LASER',5:'PLASMA',6:'STUN',7:'MELEE',8:'ACID',9:'SMOKE'}
    for it in items:
        if it.get('battleType') == 3:
            dt = it.get('damageType')
            flag = "  <-- STUN, LIKELY SHOULD BE MELEE(7)" if dt == 6 else ""
            print(f"  {it['type']:25s} damageType={dt} ({DT.get(dt,'?')}){flag}")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
