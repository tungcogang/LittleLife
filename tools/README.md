# LittleLife Asset Previewer

A standalone, visual inspection and validation utility built in Pygame for previewing all game assets in `assets_pack/`.

---

## 1. Features

- **Categorized Inspection**: Browse through all 4 asset categories (`icons/stats`, `icons/items`, `icons/ui`, `sprites/pet`).
- **Transparency Visualization**: Built-in checkerboard pattern revealing alpha transparency in 32-bit PNG assets.
- **Dynamic Zoom & Scaling**: Scale pixel art and UI icons smoothly between `1x`, `2x`, `3x`, `4x`, `6x`, and `8x`.
- **Keyboard & Mouse Navigation**: Seamless arrow-key cycling across assets and categories, with quick-jump number keys.
- **Dedicated Pet Comparison View**: Side-by-side inspection of all 5 pet mood/animation states (`idle`, `happy`, `sad`, `eating`, `sleeping`) for art consistency validation.
- **Error Handling & Diagnostics**: Detects missing or corrupted PNG files and surfaces clear error notices with path information.
- **Cozy LittleLife Theme**: Styled with the game's pastel cream and sage green aesthetic.

---

## 2. How to Run

Ensure your virtual environment is active, then run:

```powershell
# From the project root
.\.venv\Scripts\python.exe tools\asset_previewer.py
```

Or using module execution:
```powershell
.\.venv\Scripts\python.exe -m tools.asset_previewer
```

---

## 3. Keyboard & Mouse Controls

| Control | Action |
| :--- | :--- |
| `◀` / `▶` (Left / Right Arrow) | Cycle to Previous / Next asset in current category |
| `▲` / `▼` (Up / Down Arrow) | Cycle to Previous / Next category |
| `1`, `2`, `3`, `4` | Quick-jump directly to category 1 through 4 |
| `+` / `=` | Zoom In (increase scaling factor up to 8x) |
| `-` | Zoom Out (decrease scaling factor down to 1x) |
| `TAB` or `P` | Toggle **Pet 5-State Comparison View** |
| `G` | Toggle checkerboard background on/off |
| `ESC` | Exit the previewer |
| `Mouse Click` | Click sidebar tabs, zoom buttons, or carousel thumbnails |

---

## 4. Asset Verification Status

The tool scans and validates all 23 assets in `assets_pack/`:
- `icons/stats`: 6 items (`coin.png`, `energy.png`, `exp.png`, `happiness.png`, `heart.png`, `hunger.png`)
- `icons/items`: 6 items (`food_biscuit.png`, `food_salmon.png`, `medicine_tonic.png`, `potion_energy.png`, `toy_ball.png`, `toy_mouse.png`)
- `icons/ui`: 6 items (`checkmark.png`, `icon_habit.png`, `icon_inventory.png`, `icon_pet.png`, `icon_reward.png`, `icon_shop.png`)
- `sprites/pet`: 5 items (`pet_idle.png`, `pet_happy.png`, `pet_sad.png`, `pet_eating.png`, `pet_sleeping.png`)
