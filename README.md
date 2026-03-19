# Rocket Duel — Architect vs Pilot

A fast-paced **two-player competitive game** built using **Python and Pygame**, combining **level design strategy** with **precision-based rocket navigation**.

---

## Game Overview

**Rocket Duel** is a unique dual-role game where players alternate between:

*  **Architect** — designs a challenging obstacle course
*  **Pilot** — navigates a rocket through the map

The game blends **creativity, physics, and skill**, making each match dynamic and unpredictable.

---

## Gameplay Flow

1. Enter player names
2. **Round 1**

   * Player 1 → Architect
   * Player 2 → Pilot
3. **Round 2 (Role Swap)**

   * Player 2 → Architect
   * Player 1 → Pilot
4. Final winner is determined based on:

   * Successful completion
   * Fastest time

---

##  Game Physics & Engine Design

Rocket Duel uses a **custom-built 2D physics engine** optimized for smooth and precise gameplay.

---

###  Rocket Dynamics

* Directional movement using trigonometry:

  * `x += cos(angle) * speed`
  * `y += sin(angle) * speed`
* Independent rotation and velocity control
* Speed clamped to ensure balanced gameplay

#### Key Mechanics

*  Rotation-based navigation (not grid-based)
*  Gradual acceleration & deceleration
*  Momentum preservation
*  Skill-based control (angle + velocity coordination)

---

###  Collision Detection System

Instead of simple bounding boxes, the game uses **geometry-based collision detection**.

#### Implementation

* Obstacles → stored as **line segments**
* Rocket → approximated using:

  * Bounding edges
  * Movement vector

#### Collision Checks

* Edge vs obstacle intersection
* Previous → current position (continuous detection)

- Prevents tunneling at high speed
- Ensures accurate collision handling

---

###  Goal Detection

* Uses **Euclidean distance**
* Win condition:

```text
distance(rocket, goal) < radius + threshold
```

Provides a balance between **precision and playability**.

---

###  Particle System

* Dynamic rocket exhaust particles
* Each particle has:

  * Position, velocity, lifetime
  * Color variation
* Behavior scales with speed

---

###  Performance Optimizations

* Cached trigonometric values (reduces computation)
* Rolling FPS calculation system
* Limited path tracking (`MAX_PATH`)
* Efficient in-place particle updates

---

## Features

---

###  Map Builder (Design Mode)

* Freehand obstacle drawing
* Preset shapes (L, T, Cross, Diagonal, etc.)
* Real-time placement feedback
* Undo functionality
* Save maps for reuse

---

###  Core Gameplay

* Real-time 60 FPS simulation
* Smooth rocket physics
* Accurate collision detection
* Goal-based navigation

---

###  Competitive System

* Two-round gameplay with role switching
* Time-based scoring system
* Fair comparison across players

---

###  Persistent Storage

* SQLite database integration
* Maps stored as JSON:

  * Start point
  * Goal point
  * Obstacles
* Leaderboard stores best times

---

###  Visual System

* Procedural cosmic background
* Animated galaxy with rotational motion
* Twinkling stars (sinusoidal brightness)
* Lightning effects for obstacles
* Smooth UI transitions

---

###  Transition System

* Flash transitions between states
* Lightning overlays for visual feedback

---

###  Multi-Round Gameplay

* Role swapping ensures fairness
* Final result based on:

  * Completion success
  * Performance time

---

##  Controls

###  Pilot Controls

| Key     | Action        |
| ------- | ------------- |
| `A / D` | Rotate rocket |
| `← / →` | Control speed |

---

###  Architect Controls

| Action        | Control        |
| ------------- | -------------- |
| Set Start     | Click          |
| Set Goal      | Click          |
| Draw Obstacle | Click + Drag   |
| Use Preset    | Select + Click |
| Undo          | Right Click    |
| Save Map      | `S`            |
| Start Game    | `Enter`        |

---

##  Project Structure

```bash
rocket-duel/
│
├── main.py                # Game entry point & state manager
├── rocket.py              # Rocket physics & movement
├── geometry.py            # Collision detection logic
├── play_mode.py           # Gameplay engine
├── design_mode.py         # Map builder system
├── dashboard.py           # UI screens & menus
├── sound_manager.py       # Audio system
├── database.sqlite        # Leaderboard & map storage
│
├── client/                # (Browser version - WIP)
├── server/                # Backend services
└── assets/                # Media files
```

---

##  Installation

### 1️. Clone the repository

```bash
git clone https://github.com/your-username/rocket-duel.git
cd rocket-duel
```

---

### 2️. Install dependencies

```bash
pip install pygame numpy
```

---

### 3️. Run the game

```bash
python main.py
```

---

##  Build Executable (.exe)

Create a standalone version:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name RocketDuel main.py
```

Output:

```bash
dist/RocketDuel.exe
```

---

##  Future Improvements

*  Browser version using Phaser.js
*  Online multiplayer mode
*  Mobile support
*  Cloud leaderboard
*  Advanced particle effects

---

##  Engineering Highlights

* Modular architecture (separation of concerns)
* Real-time simulation loop (60 FPS)
* Custom physics & collision system
* Efficient rendering pipeline
* Scalable design for web conversion

---

##  Author

Developed by **Sanjeev Raj**

---

##  Support

If you found this project interesting, consider ⭐ starring the repository!

---
