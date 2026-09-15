"""
Random per-level modifiers, drawn from config.MODIFIERS. Each entry is
a (name, effect_dict) pair; this module is where that raw effect_dict
gets turned into concrete numbers the rest of the game actually reads.

Picking uses the maze's own seeded RNG (not Python's global random),
so a given (seed, level) always draws the same modifier — consistent
with everything else in this project being seed-reproducible.

How each effect key is interpreted (these are judgment calls the
original config data didn't spell out, since it only gave names +
raw numbers):
  - "step"  (Short Fuse)   -> shaves that many seconds off a trap's
                              safe window, making traps arm more often.
  - "push"  (Heavy World)  -> multiplies the pusher's speed (things
                              feel heavier / harder to shove around).
  - "slide" (Slippery)     -> lowers how quickly velocity snaps to the
                              input direction, giving an icy feel.
  - "dash"  (Rush)         -> multiplies the runner's sprint speed.
  - "swap"  (Panic)        -> swaps which control scheme (WASD vs
                              arrow keys) drives which player.
"""

from config import SPRINT_MULTIPLIER, TRAP_SAFE_SECONDS


class ModifierState:
    """Resolved, ready-to-use numbers for whichever modifier is active this level."""

    def __init__(self, name=None, effect=None):
        self.name = name or "None"
        effect = effect or {}

        self.sprint_multiplier = SPRINT_MULTIPLIER * effect.get("dash", 1.0)
        self.push_speed_multiplier = effect.get("push", 1.0)

        # 1.0 = instant response (no modifier); lower = more skating around.
        self.slide_factor = max(0.05, 1.0 - effect.get("slide", 0.0))

        self.trap_safe_seconds = max(0.5, TRAP_SAFE_SECONDS - effect.get("step", 0))
        self.swapped_controls = bool(effect.get("swap", False))

    def __repr__(self):
        return f"<Modifier {self.name}>"


def pick_modifier(rng, modifiers):
    """rng: the maze's own random.Random instance, for determinism per (seed, level)."""
    name, effect = rng.choice(modifiers)
    return ModifierState(name, effect)
