# Survival Game: The Power Role

You are the hunter. Eliminate all **10 survivors** to win. Survivors fight back with roles, shields, bursts, and necromancer skeletons.

## Run

```bash
pip install -r requirements.txt
python3 main.py
```

## Controls

| Key | Action |
|-----|--------|
| W / A / S / D | Move |
| Space | Freeze projectile (3s trap on hit, 5s cooldown) |
| Up Arrow | Hazard zone in front of you (0.5s active, follows you, 2s cooldown) |
| Shift | **Dash** — 3s rush at speed 10, 100×100 kill box, 8s cooldown |

There is **no melee contact damage**. Kills come from hazards, dash, and traps.

## Hunter abilities

### Dash (Shift)
- Lasts **3 seconds** with **40%** normal steering
- **100×100** hitbox instantly kills anyone in your path (shields do not block)
- **End burst** knocks back survivors within range
- **8 second** cooldown after use
- You cannot be stunned while dashing

### Stun immunity
- After any stun ends, you gain **10 seconds** of stun immunity (yellow ring)
- Immunity blocks stuns from attacker bursts and skeletons

### Portals
- Blue edges wrap you to the opposite side (1 second cooldown between warps)
- Survivors use the same portal system

## Survivors (10 total)

| Role | Count | Color | Behavior |
|------|-------|-------|----------|
| **Attacker** | 4 | Cyan | 50% chance to wind up (0.5s), then **150×150 burst** — stuns you 3s + heavy knockback |
| **Lifesaver** | 2 | Light blue | Shield every 8s for 3s — blocks all hunter damage in radius |
| **Necromancer** | 2 | Purple | Collects **death marks** (X) and spawns a **skeleton** |
| **Healer** | 2 | Green | **3 hearts** — takes 3 hazard hits to die; sends heal orbs (+1 heart) |

### Death
- Dead survivors show a red **X**
- Necromancers path to marks and revive them as skeletons

### Skeleton (necromancer)
- Speed **10**, rushes the hunter
- **5 second** stun + heavy knockback on hit, then vanishes

## Win condition

Eliminate all 10 survivors (`Alive: 0/10`).

## Repo

https://github.com/eggo120/game1
