# LittleLife Game Asset Pack Catalog

This directory contains the standalone game asset pack for **LittleLife**, a cozy virtual pet, habit tracker, and mini-economy game.

All images are standard transparent PNGs (`RGBA` format) optimized for Pygame rendering via `pygame.image.load(...).convert_alpha()`.

---

## 1. Directory Structure

```
assets_pack/
├── CATALOG.md             # Detailed asset catalog and integration documentation
├── icons/
│   ├── stats/             # Currencies and pet vital meters (32x32)
│   ├── items/             # Store and backpack item icons (48x48)
│   └── ui/                # Navigation tabs and interactive badges (32x32)
└── sprites/
    └── pet/               # Pet character sprites for key states (64x64)
```

---

## 2. Complete Asset Catalog

### 2.1 Stats & Currency Icons (`assets_pack/icons/stats/`)
Dimensions: **32x32 px** | Format: **RGBA Transparent PNG**

| Filename | Dimensions | Description / Intended Usage |
| :--- | :--- | :--- |
| `coin.png` | 32x32 | Gold coin with shimmer star. Used in wallet display, shop prices, and habit rewards. |
| `exp.png` | 32x32 | Lavender star badge. Used in pet EXP progress bar and habit reward tags. |
| `heart.png` | 32x32 | Soft crimson heart. Used for Pet Health meter and health recovery indicators. |
| `hunger.png` | 32x32 | Drumstick / meat cutlet. Used for Pet Hunger meter and food action headers. |
| `happiness.png` | 32x32 | Joyful sunny smiley face. Used for Pet Happiness meter and mood rating. |
| `energy.png` | 32x32 | Sky-blue lightning bolt. Used for Pet Energy meter and stamina indicators. |

---

### 2.2 Item Icons (`assets_pack/icons/items/`)
Dimensions: **48x48 px** | Format: **RGBA Transparent PNG**

| Filename | Dimensions | Description / Intended Usage |
| :--- | :--- | :--- |
| `food_biscuit.png` | 48x48 | Golden baked cookie with chocolate chips. Used for Crispy Biscuit item. |
| `food_salmon.png` | 48x48 | Fresh salmon filet with grill texture. Used for Gourmet Salmon item. |
| `toy_ball.png` | 48x48 | Bright bouncy ball with yellow ribbon band. Used for Squeaky Ball item. |
| `toy_mouse.png` | 48x48 | Cute wind-up plush mouse with pink tail. Used for toy catalog items. |
| `medicine_tonic.png`| 48x48 | Green apothecary bottle with red cross badge. Used for Herbal Tonic item. |
| `potion_energy.png` | 48x48 | Round glass flask with glowing violet elixir. Used for Energy Elixir item. |

---

### 2.3 UI & Navigation Icons (`assets_pack/icons/ui/`)
Dimensions: **32x32 px** | Format: **RGBA Transparent PNG**

| Filename | Dimensions | Description / Intended Usage |
| :--- | :--- | :--- |
| `icon_pet.png` | 32x32 | Cozy green paw print. Used for the Pet Companion navigation tab. |
| `icon_habit.png` | 32x32 | Clipboard checklist with checkmark. Used for the Daily Habits navigation tab. |
| `icon_shop.png` | 32x32 | Warm woven shopping basket. Used for the General Store navigation tab. |
| `icon_inventory.png`| 32x32 | Adventurer's backpack. Used for the Backpack navigation tab. |
| `icon_reward.png` | 32x32 | Red gift box with golden ribbon bow. Used for reward claim buttons and bonus popups. |
| `checkmark.png` | 32x32 | Green circular check badge. Used to show habit completion status. |

---

### 2.4 Pet Sprites (`assets_pack/sprites/pet/`)
Dimensions: **64x64 px** | Format: **RGBA Transparent PNG**

| Filename | Dimensions | Description / Intended Usage |
| :--- | :--- | :--- |
| `pet_idle.png` | 64x64 | Base neutral/calm companion with sparkling round eyes, blush, and soft shadow. |
| `pet_happy.png` | 64x64 | Joyful companion with happy eyes (`^ ^`), open mouth smile, and heart accents. |
| `pet_sad.png` | 64x64 | Unhappy / lonely companion with droopy eyes, curved frown, and tear drop. |
| `pet_eating.png` | 64x64 | Cheerful companion holding and nibbling a cookie with paws. |
| `pet_sleeping.png`| 64x64 | Cozy companion taking a restful nap with closed eyes (`- -`) and floating "Zzz". |

---

## 3. How to Integrate Into Pygame

### Loading Assets
Always use `convert_alpha()` after initializing the display surface for fast blitting with transparent alpha:

```python
import pygame
from pathlib import Path

# Base asset directory
ASSETS_DIR = Path("assets_pack")

# Load stat icon
coin_icon = pygame.image.load(str(ASSETS_DIR / "icons" / "stats" / "coin.png")).convert_alpha()

# Load pet sprite
pet_idle = pygame.image.load(str(ASSETS_DIR / "sprites" / "pet" / "pet_idle.png")).convert_alpha()
```

### Scaling Sprites
Pygame allows easy scaling using `pygame.transform.smoothscale`:

```python
# Scale the 64x64 pet sprite up to 128x128 for a prominent profile avatar
pet_avatar_large = pygame.transform.smoothscale(pet_idle, (128, 128))
```

### Selecting Pet Sprite by State
You can map pet vitals and actions to the corresponding sprite:

```python
def get_pet_sprite(pet_state, action_status="none"):
    if action_status == "sleeping":
        return sprites["pet_sleeping"]
    elif action_status == "eating":
        return sprites["pet_eating"]
    elif pet_state.happiness < 40 or pet_state.hunger < 25:
        return sprites["pet_sad"]
    elif pet_state.happiness >= 75:
        return sprites["pet_happy"]
    return sprites["pet_idle"]
```
