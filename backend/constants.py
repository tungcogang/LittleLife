"""Hằng số gameplay dùng chung cho LittleLife.

Giữ các giá trị này ở một chỗ để đảm bảo Habit API, Pet API và logic
Store/Inventory đều dùng chung ngưỡng phần thưởng và cấp độ.
"""

# Phần thưởng chỉ được cộng một lần cho mỗi habit mỗi ngày.
HABIT_COINS_REWARD = 10
HABIT_EXP_REWARD = 20

# Ngưỡng kinh nghiệm cố định cho mỗi cấp (khớp thanh EXP của frontend).
EXP_PER_LEVEL = 100

# Tinh chỉnh các hành động chăm sóc. Mọi chỉ số đều bị kẹp trong khoảng 0..PET_STAT_MAX.
FEED_HUNGER_GAIN = 15

SLEEP_ENERGY_GAIN = 30
SLEEP_HEALTH_GAIN = 5

PLAY_HUNGER_COST = 10
PLAY_ENERGY_COST = 10
PLAY_HAPPINESS_GAIN = 15

# Chỉ áp dụng một lần ở lần tương tác pet đầu tiên của mỗi ngày mới.
DAILY_HAPPINESS_DECAY = 10
DAILY_HEALTH_DECAY = 5

# Mọi chỉ số của pet nằm trong khoảng 0..100 (xem ràng buộc check của model Pet).
PET_STAT_MAX = 100

PET_STAT_LABELS = {
    "hunger": "Hunger",
    "happiness": "Happiness",
    "energy": "Energy",
    "health": "Health",
}
