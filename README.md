# Risk of Rain 2 Fun House
### v26.0 - "The Surgeon" Release

**Risk of Rain 2 Fun House** is an advanced, external automation dashboard for *Risk of Rain 2*. It functions as a "Dungeon Master" console, allowing players to build loadouts, spawn specific bosses, control mob flows, and synchronize their data across machines via GitHub.

Unlike standard mods, this tool runs externally (Python) and interacts with the game via the Developer Console (`cheats 1`) and the `Player.log` file, ensuring compatibility without modifying game binaries.

---

## 📂 Repository Structure & Architecture

The program follows a **Hybrid-Core Architecture**. It possesses a hardcoded "Skeleton" of essential game data to ensure it never crashes on load, but it relies on a sophisticated **Wiki Mining Engine** to populate its database with high-resolution assets and up-to-date stats.

### File System Layout
```text
ROR2_HACK/
│
├── architect.py                # THE CORE. Main application logic (GUI, Logic, Mining).
├── upload_data.py              # Data Uplink. Automates git operations for the Data folder.
├── README.md                   # This documentation.
│
├── ROR2_Data/                  # THE ARCHIVE. Contains mined assets.
│   ├── Common/                 # White Items
│   ├── Uncommon/               # Green Items
│   ├── Legendary/              # Red Items
│   ├── Boss/                   # Yellow Items
│   ├── Lunar/                  # Blue Items
│   ├── Lunar Equipment/        # Blue Active Items (Strictly separated from Orange)
│   ├── Void/                   # Purple Items
│   ├── Equipment/              # Orange Active Items
│   ├── Meal/                   # Chef Consumables (DLC)
│   └── master_cache.json       # The JSON index of all known items and their paths.
│
├── Profiles/                   # User Loadouts (.json)
│   ├── Default.json
│   └── [User_Created].json
│
└── logs/                       # Runtime diagnostics
    └── runtime.log
