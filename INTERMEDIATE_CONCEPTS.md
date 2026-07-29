# Intermediate Concepts Used in Meteor Dodge

This document explains the intermediate-level structures that appear in the code.

---

## 1. List Comprehension

### Basic Syntax

```python
[new_expression for item in original_list if condition]
```

### Where it appears in the game

```python
self.bullets = [b for b in self.bullets if not b.is_off_screen()]
```

### What it does

Creates a **new list** by iterating over the original one, element by element:

1. Takes each `b` from `self.bullets`
2. Checks the condition: `not b.is_off_screen()` (the bullet is still on screen)
3. If the condition is `True`, includes `b` in the new list
4. If the condition is `False`, skips it

### Equivalent without comprehension

```python
new_list = []
for b in self.bullets:
    if not b.is_off_screen():
        new_list.append(b)
self.bullets = new_list
```

The comprehension does exactly the same thing in a single line.

### Variant: filtering with keep condition

```python
self.explosions = [e for e in self.explosions if e.is_alive()]
```

Filters: keeps only explosions whose `is_alive()` returns `True`.

---

## 2. Nested Dictionaries

### Basic Syntax

```python
level = {
    1: {
        "name": "Nebula",
        "speed": 5,
    },
    2: {
        "name": "Storm",
        "speed": 7,
    },
}
```

### Where it appears in the game

```python
LEVELS = {
    1: {
        "name": "Nebula",
        "background": "background_01.png",
        "meteor_min_speed": 3,
        "meteor_max_speed": 5,
        "spawn_rate": 30,
        "ammo_type": "normal",
    },
    2: {
        "name": "Storm",
        "background": "background_02.png",
        # ...
    },
}
```

### What it does

- The `LEVELS` dictionary has **5 keys** (1, 2, 3, 4, 5), one per level.
- Each value is **another dictionary** with that level's configuration.
- To access a specific value: `LEVELS[1]["name"]` returns `"Nebula"`.
- To get the current level: `LEVELS[self.current_level]`.

### Advantage

All five level configurations are centralized in a single data structure. This allows a level's speed to be modified in one place. An alternative approach without nested dictionaries would require five separate variables or five parallel lists to represent the same data.

---

## 3. Slicing with `[:]` for Safe Iteration

### Basic Syntax

```python
for item in list[:]:      # shallow copy of the list
    list.remove(item)     # modify the original while iterating
```

### Where it appears in the game

```python
for bullet in self.bullets[:]:
    for meteor in self.meteors[:]:
        if bullet_rect.colliderect(meteor.get_rect()):
            self.meteors.remove(meteor)
            self.bullets.remove(bullet)
```

### What it does

- `self.bullets[:]` creates a **copy** of the list (using the slice operator `[:]`).
- The `for` loop iterates over the **copy**.
- When a collision is found, elements are removed from the **original** with `.remove()`.
- Since the loop traverses the copy, removing elements from the original does not affect the iteration.

### Why it is necessary

Without the `[:]` copy, if you remove an element while iterating, the indices shift and the loop skips the next element. This causes intermittent bugs that are hard to detect.

### Example of the problem

```python
lst = [1, 2, 3, 4, 5]
for i, n in enumerate(lst):     # WRONG: iterating over the original
    if n == 2:
        lst.remove(n)
    print(i, n)
# Prints: 0 1, 1 2, 2 4, 3 5
# The 3 is skipped because when 2 was removed, 3 moved to index 2
# but the loop counter i already advanced to 2
```

---

## 4. Optional Parameters with Default Values

### Basic Syntax

```python
def function(param1, param2=None):
    if param2 is None:
        param2 = "default value"
```

### Where it appears in the game

```python
def spawn_meteor(self, speed=None, speed_range=None):
    if len(self.meteors) < MAX_METEORS:
        if speed is not None:
            meteor = Meteor(self.meteor_images, (speed, speed))
        elif speed_range is not None:
            meteor = Meteor(self.meteor_images, speed_range)
        else:
            data = self.get_level_data()
            meteor = Meteor(self.meteor_images,
                (data["meteor_min_speed"], data["meteor_max_speed"]))
        self.meteors.append(meteor)
```

### What it does

- `speed=None` means: if the caller does not pass this argument, use `None`.
- The function checks: if they passed an exact speed, use it; if they passed a range, use it; if they passed nothing, use the current level's defaults.
- This allows calling `spawn_meteor()` in 3 different ways depending on context.

---

## 5. The `if __name__ == "__main__"` Block

```python
if __name__ == "__main__":
    game = Game()
    game.run()
```

- `__name__` is a special variable that Python assigns to every file.
- When you run `python meteor_dodge.py` directly, `__name__` is `"__main__"`.
- When you import the file from another script (`from meteor_dodge import Game`), `__name__` is `"meteor_dodge"` and the block does not execute.
- This lets you reuse the game's classes from other scripts without the game starting on its own.

---

## 6. The `break` Statement in Collision Loops

### Where it appears

```python
for meteor in self.meteors[:]:
    if player_rect.colliderect(meteor.get_rect()):
        # ... handle collision ...
        break
```

### What it does

- `break` immediately exits the innermost loop.
- In collision detection, after a meteor hits the player, we call `break` so the player is not hit by multiple meteors in the same frame (which would cost multiple lives at once).

---

## Summary

| Concept                  | Where it is used                   | What to study                                    |
| ------------------------ | ---------------------------------- | ------------------------------------------------ |
| List comprehension       | Filtering lists (bullets, meteors) | `[x for x in lista if cond]` structure           |
| Nested dictionaries      | `LEVELS`, `self.backgrounds`       | Access with `dict[key][subkey]`                  |
| Slicing `[:]`            | `for x in list[:]`                 | List copy, difference between `[:]` and `list()` |
| Optional parameters      | `spawn_meteor(speed=None)`         | Default values, `is None` check                  |
| `__name__ == "__main__"` | Game entry point                   | Direct execution vs import                       |
| `break`                  | Collision loops                    | Exiting loops early                              |
