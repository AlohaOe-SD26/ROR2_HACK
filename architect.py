# [Risk of Rain 2 Fun House] - v27.5 (The Git-Adaptive Release)
# Description: Dynamic Branch Detection, Robust Profile Sync, Master List Integration.

import sys
import os

# --- CRITICAL FIX: SILENCE STDOUT FOR PYTHONW ---
if sys.executable.endswith("pythonw.exe"):
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

import shutil
import json
import time
import threading
import logging
import re
import subprocess
import queue
import webbrowser
import winreg
import requests
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox

# --- 1. BOOTSTRAP ---
REQUIRED_LIBS = [
    ("customtkinter", "customtkinter"),
    ("keyboard", "keyboard"),
    ("pydirectinput", "pydirectinput"),
    ("PIL", "Pillow"),
    ("requests", "requests"),
    ("inputs", "inputs"),
    ("bs4", "beautifulsoup4"),
    ("lxml", "lxml")
]

def install_dependencies():
    missing = []
    for import_name, install_name in REQUIRED_LIBS:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(install_name)
    if missing:
        try:
            executable = sys.executable.replace("pythonw.exe", "python.exe")
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.check_call([executable, "-m", "pip", "install"] + missing, startupinfo=si)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except:
            sys.exit(1)

install_dependencies()

import customtkinter as ctk
import keyboard
import pydirectinput
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from inputs import get_gamepad

# --- 2. CONFIG ---
APP_NAME = "Risk of Rain 2 Fun House"
VERSION = "27.5.0"
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "ROR2_Data")
PROFILE_DIR = os.path.join(DATA_DIR, "Profiles")
CACHE_FILE = os.path.join(DATA_DIR, "master_cache.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")
# URLs
WIKI_BASE = "https://riskofrain2.wiki.gg"
WIKI_ITEMS_PAGE = "https://riskofrain2.wiki.gg/wiki/Items"
WIKI_API = "https://riskofrain2.wiki.gg/api.php"
HEADERS = {"User-Agent": "ROR2-FunHouse/27.5 (Adaptive)"}

# Repo Config
REPO_API_URL = "https://api.github.com/repos/AlohaOe-SD26/ROR2_HACK/contents/ROR2_Data/Profiles"
RAW_URL_BASE = "https://raw.githubusercontent.com/AlohaOe-SD26/ROR2_HACK/main/ROR2_Data/Profiles"

for d in [DATA_DIR, PROFILE_DIR, LOG_DIR]: os.makedirs(d, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, "runtime.log"), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# --- 3. DATABASE MAPPINGS ---

RARITY_VIBES = {
    "Common": "#FFFFFF",          
    "Uncommon": "#72B045",        
    "Legendary": "#E64843",       
    "Boss": "#E5C962",            
    "Lunar": "#3478C7",           
    "Void": "#884C9E",            
    "Equipment": "#FF8000",       
    "Lunar Equipment": "#3478C7", 
    "Meal": "#F38D33",            
    "Untiered": "#606060"         
}

# --- THE MASTER LIST (Wiki Name -> Internal ID) ---
INTERNAL_ID_MAP = {
    # --- SEEKERS OF THE STORM (DLC 2) ---
    "Antler Shield": "AntlerShield",
    "Bolstering Lantern": "AttackSpeedPerNearbyAllyOrEnemy",
    "Chance Doll": "ChanceDoll",
    "Knockback Fin": "KnockbackFin",
    "Warped Echo": "DelayedDamage",
    "Chronic Expansion": "StackDamageOnKill",
    "Luminous Shot": "LuminousShot",
    "Noxious Thorn": "NoxiousThorn",
    "Prayer Beads": "PrayerBeads",
    "Sale Star": "SaleStar",
    "Unstable Transmitter": "TeleportOnLowHealth",
    "Electric Boomerang": "ElectricBoomerang",
    "Growth Nectar": "GrowthNectar",
    "Runic Lens": "RunicLens",
    "Sonorous Whispers": "ItemDropChanceOnKill",
    "War Bonds": "WarBonds",
    "Longstanding Solitude": "LongstandingSolitude",
    "Seed of Life": "HealAndRevive",
    "Bison Steak Dinner": "SearedSteak",
    "The Ultimate Meal": "UltimateMeal",

    # --- SURVIVORS OF THE VOID (DLC 1) ---
    "Delicate Watch": "FragileDamageBonus",
    "Mocha": "AttackSpeedAndMoveSpeed",
    "Oddly-shaped Opal": "OutOfCombatArmor",
    "Power Elixir": "HealingPotion",
    "Roll of Pennies": "GoldOnHurt",
    "Hunter's Harpoon": "MoveSpeedOnKill",
    "Ignition Tank": "StrengthenBurn",
    "Regenerating Scrap": "RegeneratingScrap",
    "Shipping Request Form": "FreeChest",
    "Shuriken": "PrimarySkillShuriken",
    "Ben's Raincoat": "ImmuneToDebuff",
    "Bottled Chaos": "RandomEquipmentTrigger",
    "Laser Scope": "CritDamage",
    "Pocket I.C.B.M.": "MoreMissile",
    "Spare Drone Parts": "DroneWeapons",
    "Symbiotic Scorpion": "PermanentDebuffOnHit",
    "Benthic Bloom": "CloverVoid",
    "Encrusted Key": "TreasureCacheVoid",
    "Lost Seer's Lenses": "CritGlassesVoid",
    "Lysate Cell": "EquipmentMagazineVoid",
    "Needletick": "BleedOnHitVoid",
    "Newly Hatched Zoea": "VoidMegaCrabItem",
    "Plasma Shrimp": "MissileVoid",
    "Pluripotent Larva": "ExtraLifeVoid",
    "Polylute": "ChainLightningVoid",
    "Safer Spaces": "BearVoid",
    "Singularity Band": "ElementalRingVoid",
    "Tentabauble": "SlowOnHitVoid",
    "Voidsent Flame": "ExplodeOnDeathVoid",
    "Weeping Fungus": "MushroomVoid",
    "Executive Card": "MultiShopCard",
    "Goobo Jr.": "GummyClone",
    "Molotov (6-Pack)": "Molotov",
    "Trophy Hunter's Tricorn": "BossHunter",

    # --- BASE GAME (Standardized) ---
    # Common
    "Armor-Piercing Rounds": "BossDamageBonus",
    "Backup Magazine": "SecondarySkillMagazine",
    "Bison Steak": "FlatHealth", 
    "Bundle of Fireworks": "Firework",
    "Bustling Fungus": "Mushroom",
    "Cautious Slug": "HealWhileSafe",
    "Crowbar": "Crowbar",
    "Energy Drink": "SprintBonus",
    "Focus Crystal": "NearbyDamageBonus",
    "Gasoline": "IgniteOnKill",
    "Lens-Maker's Glasses": "CritGlasses",
    "Medkit": "Medkit",
    "Monster Tooth": "Tooth",
    "Paul's Goat Hoof": "Hoof",
    "Personal Shield Generator": "PersonalShield",
    "Repulsion Armor Plate": "ArmorPlate",
    "Rusted Key": "TreasureCache",
    "Soldier's Syringe": "Syringe",
    "Sticky Bomb": "StickyBomb",
    "Stun Grenade": "StunChanceOnHit",
    "Topaz Brooch": "BarrierOnKill",
    "Tougher Times": "Bear",
    "Tri-Tip Dagger": "BleedOnHit",
    "Warbanner": "WardOnLevel",

    # Uncommon
    "AtG Missile Mk. 1": "Missile",
    "Bandolier": "Bandolier",
    "Berzerker's Pauldron": "WarCryOnMultiKill",
    "Chronobauble": "SlowOnHit",
    "Death Mark": "DeathMark",
    "Fuel Cell": "EquipmentMagazine",
    "Ghor's Tome": "BonusGoldPackOnKill",
    "Harvester's Scythe": "HealOnCrit",
    "Hopoo Feather": "Feather",
    "Infusion": "Infusion",
    "Kjaro's Band": "FireRing",
    "Leeching Seed": "Seed",
    "Lepton Daisy": "TPHealingNova",
    "Old Guillotine": "ExecuteLowHealthElite",
    "Old War Stealthkit": "Phasing",
    "Predatory Instincts": "AttackSpeedOnCrit",
    "Razorwire": "Thorns",
    "Red Whip": "SprintOutOfCombat",
    "Rose Buckler": "SprintArmor",
    "Runald's Band": "IceRing",
    "Squid Polyp": "Squid",
    "Ukulele": "ChainLightning",
    "War Horn": "EnergizedOnEquipmentUse",
    "Wax Quail": "JumpBoost",
    "Will-o'-the-wisp": "ExplodeOnDeath",

    # Legendary
    "57 Leaf Clover": "Clover",
    "Aegis": "BarrierOnOverHeal",
    "Alien Head": "AlienHead",
    "Brainstalks": "KillEliteFrenzy",
    "Brilliant Behemoth": "Behemoth",
    "Ceremonial Dagger": "Dagger",
    "Defensive Microbots": "CaptainDefenseMatrix",
    "Dio's Best Friend": "ExtraLife",
    "Frost Relic": "Icicle",
    "H3AD-5T v2": "FallBoots",
    "Happiest Mask": "GhostOnKill",
    "Hardlight Afterburner": "UtilitySkillMagazine",
    "Interstellar Desk Plant": "Plant",
    "N'kuhana's Opinion": "NovaOnHeal",
    "Rejuvenation Rack": "IncreaseHealing",
    "Resonance Disc": "LaserTurbine",
    "Sentient Meat Hook": "BounceNearby",
    "Shattering Justice": "ArmorReductionOnHit",
    "Soulbound Catalyst": "Talisman",
    "Unstable Tesla Coil": "ShockNearby",
    "Wake of Vultures": "HeadHunter",

    # Boss
    "Defense Nucleus": "MinorConstructOnKill",
    "Empathy Cores": "RoboBallBuddy",
    "Genesis Loop": "BleedOnHitAndExplode",
    "Halcyon Seed": "TitanGoldDuringTP",
    "Little Disciple": "SprintWisp",
    "Mired Urn": "SiphonOnLowHealth",
    "Molten Perforator": "FireballsOnHit",
    "Planula": "ParentEgg",
    "Queen's Gland": "BeetleGland",
    "Shatterspleen": "BleedOnHitAndExplode",
    "Titanic Knurl": "Knurl",
    "Charged Perforator": "LightningStrikeOnHit",

    # Lunar
    "Beads of Fealty": "LunarTrinket",
    "Brittle Crown": "GoldOnHit",
    "Corpsebloom": "RepeatHeal",
    "Defiant Gouge": "GlobalDeathMark", 
    "Egocentrism": "LunarSun",
    "Essence of Heresy": "LunarSpecialReplacement",
    "Eulogy Zero": "RandomlyLunar",
    "Focused Convergence": "FocusConvergence",
    "Gesture of the Drowned": "AutoCastEquipment",
    "Hooks of Heresy": "LunarSecondaryReplacement",
    "Light Flux Pauldron": "HalfAttackSpeedHalfCooldowns",
    "Mercurial Rachis": "RandomDamageZone",
    "Purity": "LunarBadLuck",
    "Radiant Pearl": "ShinyPearl",
    "Shaped Glass": "LunarDagger",
    "Stone Flux Pauldron": "HalfSpeedDoubleHealth",
    "Strides of Heresy": "LunarUtilityReplacement",
    "Transcendence": "ShieldOnly",
    "Visions of Heresy": "LunarPrimaryReplacement",

    # Equipment
    "Blast Shower": "Cleanse",
    "Disposable Missile Launcher": "CommandMissile",
    "Foreign Fruit": "Fruit",
    "Forgive Me Please": "DeathProjectile",
    "Gnarled Woodsprite": "PassiveHealing",
    "Jade Elephant": "GainArmor",
    "Milky Chrysalis": "Jetpack",
    "Ocular HUD": "CritOnUse",
    "Preon Accumulator": "BFG",
    "Primordial Cube": "Blackhole",
    "Radar Scanner": "Scanner",
    "Recycler": "Recycle",
    "Royal Capacitor": "Lightning",
    "Sawmerang": "Saw",
    "Super Massive Leech": "LifestealOnHit",
    "Gorag's Opus": "TeamWarCry",
    "The Back-up": "DroneBackup",
    "The Crowdfunder": "GoldGat",
    "Volcanic Egg": "FireBallDash",
    
    # Lunar Equipment
    "Effigy of Grief": "CripplingWard",
    "Glowing Meteorite": "Meteor",
    "Helfire Tincture": "BurnNearby",
    "Spinel Tonic": "Tonic",
    "Remote Caffeinator": "VendingMachine"
}

BOSS_DB = {
    "Beetle Queen": "BeetleQueen2Body", "Clay Dunestrider": "ClayBossBody", "Stone Titan": "TitanBody",
    "Wandering Vagrant": "VagrantBody", "Magma Worm": "MagmaWormBody", "Overloading Worm": "ElectricWormBody",
    "Imp Overlord": "ImpBossBody", "Grovetender": "GravekeeperBody", "Solus Control Unit": "RoboBallBossBody",
    "Alloy Worship Unit": "SuperRoboBallBossBody", "Scavenger": "ScavBody", "Grandparent": "GrandParentBody",
    "Mithrix": "BrotherBody", "Void Devastator": "VoidMegaCrabBody", "Xi Construct": "MegaConstructBody",
    "Voidling": "VoidRaidCrabBody"
}

MOB_DB = {
    "Lemurian": "LemurianMaster", "Beetle": "BeetleMaster", "Lesser Wisp": "WispMaster",
    "Jellyfish": "JellyfishMaster", "Imp": "ImpMaster", "Hermit Crab": "HermitCrabMaster",
    "Stone Golem": "GolemMaster", "Beetle Guard": "BeetleGuardMaster", "Elder Lemurian": "LemurianBruiserMaster",
    "Bison": "BisonMaster", "Brass Contraption": "BellMaster", "Greater Wisp": "GreaterWispMaster",
    "Clay Templar": "ClayBruiserMaster", "Parent": "ParentMaster", "Mini Mushrum": "MiniMushroomMaster",
    "Void Reaver": "NullifierMaster", "Void Jailer": "VoidJailerMaster", "Void Barnacle": "VoidBarnacleMaster",
    "Lunar Golem": "LunarGolemMaster", "Lunar Wisp": "LunarWispMaster"
}

ELITE_MODIFIERS = { "None": -1, "Blazing": 0, "Overloading": 1, "Glacial": 2, "Malachite": 3, "Celestine": 4, "Voidtouched": 5 }
TEAM_INDICES = {"Monster (Enemy)": 2, "Player (Ally)": 1, "Neutral (Chaos)": 0}

# --- 4. ENGINES ---
class SteamManager:
    def __init__(self):
        self.path = self._find_steam_path()
        self.accounts = self._get_accounts()
    def _find_steam_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            return path.replace("/", "\\")
        except: return None
    def _get_accounts(self):
        accs = ["Default / Auto"]
        if not self.path: return accs
        config_path = os.path.join(self.path, "config", "loginusers.vdf")
        if not os.path.exists(config_path): return accs
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = f.read()
                matches = re.findall(r'"AccountName"\s+"([^"]+)"', data)
                accs.extend(sorted(list(set(matches))))
        except: pass
        return accs
    def launch_game(self, account=None):
        game_id = "632360"
        if not account or account == "Default / Auto":
            os.startfile(f"steam://run/{game_id}")
            return "Launching via Protocol..."
        if not self.path: return "Error: Steam path not found."
        exe = os.path.join(self.path, "steam.exe")
        if not os.path.exists(exe): return "Error: steam.exe not found."
        subprocess.Popen([exe, "-login", account, "-applaunch", game_id])
        return f"Switching to {account}..."

class LogWatcher:
    def __init__(self):
        self.path = os.path.expandvars(r"%userprofile%\AppData\LocalLow\Hopoo Games, LLC\Risk of Rain 2\Player.log")
        self.active = False
        self.enemy_count = 0
    def start_watching(self):
        self.active = True
        threading.Thread(target=self._monitor, daemon=True).start()
    def _monitor(self):
        while self.active:
            if os.path.exists(self.path):
                try:
                    with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(0, 2)
                        while self.active:
                            line = f.readline()
                            if not line: time.sleep(0.1); continue
                            if "Master(Clone)" in line: self.enemy_count += 1
                            if "list_ai" in line: self.enemy_count = 0 
                except: pass
            time.sleep(1)

# --- REWRITTEN CLOUD MANAGER (DYNAMIC GIT) ---
class CloudManager:
    @staticmethod
    def get_current_branch():
        try:
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return "main" # Fallback

    @staticmethod
    def run_git(args, error_msg):
        try:
            subprocess.run(args, cwd=BASE_DIR, check=True, capture_output=True, text=True)
            return True, "Success"
        except subprocess.CalledProcessError as e:
            err = e.stderr if e.stderr else str(e)
            return False, f"{error_msg}\n{err}"

    @staticmethod
    def push_profile(profile_name):
        target_file = os.path.join("ROR2_Data", "Profiles", f"{profile_name}.json")
        if not os.path.exists(os.path.join(BASE_DIR, target_file)): return False, "Profile not found."
        
        branch = CloudManager.get_current_branch()
        
        # 1. Pull (Sync)
        CloudManager.run_git(["git", "pull", "origin", branch], "Pull failed.")
        
        # 2. Add
        ok, msg = CloudManager.run_git(["git", "add", target_file], "Git Add failed.")
        if not ok: return False, msg
        
        # 3. Commit (Allow empty in case no changes)
        try:
            subprocess.run(["git", "commit", "-m", f"Sync Profile: {profile_name}"], cwd=BASE_DIR, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            pass # Nothing to commit is fine
        
        # 4. Push
        ok, msg = CloudManager.run_git(["git", "push", "origin", branch], "Git Push failed.")
        if not ok: return False, msg
        
        return True, "Profile Uploaded!"

    @staticmethod
    def pull_profiles():
        branch = CloudManager.get_current_branch()
        ok, msg = CloudManager.run_git(["git", "pull", "origin", branch], "Git Pull failed.")
        if ok: return True, "Profiles Synced."
        return False, msg

class WikiSyncEngine:
    def __init__(self, cb):
        self.cb = cb; self.stop_flag = False
        self.session = requests.Session(); self.session.headers.update(HEADERS)
    
    def safe_name(self, n): return re.sub(r'[^a-zA-Z0-9]', '_', n).strip('_')
    
    def save_image(self, url, folder, filename):
        path = os.path.join(folder, filename)
        if os.path.exists(path) and os.path.getsize(path) > 1024: return True
        try:
            clean_url = url
            if "/thumb/" in url:
                clean_url = url.replace("/thumb", "")
                if "/" in clean_url.split(".")[-1]: 
                    clean_url = "/".join(clean_url.split("/")[:-1])
            r = self.session.get(clean_url, timeout=5)
            if r.status_code == 200:
                with open(path, 'wb') as f: f.write(r.content); return True
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                with open(path, 'wb') as f: f.write(r.content); return True
        except: pass
        return False

    def fetch_full_text(self, item_name):
        params = { "action": "query", "titles": item_name, "prop": "extracts", "explaintext": 1, "format": "json", "redirects": 1 }
        try:
            r = self.session.get(WIKI_API, params=params, timeout=5)
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for pid in pages:
                if pid != "-1": return pages[pid].get("extract", "No additional details found.")
        except: pass
        return "No details available."

    def run_sync(self):
        try:
            collected = {k: [] for k in RARITY_VIBES.keys()}
            
            self.cb(0, 100, "Discovery", "Mapping Wiki Structure...", "#FFF")
            
            r = self.session.get(WIKI_ITEMS_PAGE, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            header_map = {
                "Lunar Equipment": "Lunar Equipment", 
                "Elite Equipment": "Equipment",
                "Common": "Common",
                "Uncommon": "Uncommon",
                "Legendary": "Legendary",
                "Boss": "Boss",
                "Lunar": "Lunar", 
                "Void": "Void",
                "Equipment": "Equipment",
                "Consumable": "Meal"
            }
            
            sorted_map_keys = sorted(header_map.keys(), key=len, reverse=True)
            
            headers = soup.find_all(['h2', 'h3'])
            total_items = sum([len(h.find_next("table").find_all("tr")) for h in headers if h.find_next("table")])
            current_idx = 0
            
            for h in headers:
                header_text = h.get_text(strip=True).replace(" items", "")
                
                target_rarity = None
                for key in sorted_map_keys:
                    if key in header_text:
                        target_rarity = header_map[key]
                        break
                
                if not target_rarity: continue
                if target_rarity not in collected: target_rarity = "Common" 
                
                tbl = h.find_next("table")
                if not tbl: continue
                
                for row in tbl.find_all("tr")[1:]:
                    try:
                        if self.stop_flag: break
                        current_idx += 1
                        
                        cols = row.find_all(['td', 'th'])
                        if len(cols) < 3: continue 
                        
                        link_tag = row.find("a")
                        if not link_tag: continue
                        name = link_tag.get('title', link_tag.text.strip())
                        href = link_tag['href']
                        if href.startswith("/"): href = WIKI_BASE + href
                        
                        # Smart Description
                        brief_desc = "No description."
                        candidates = []
                        for col in cols[1:]:
                            text = col.get_text(" ", strip=True)
                            lower_text = text.lower()
                            if lower_text in ["linear", "hyperbolic", "exponential", "none", "special", "standard"]: continue
                            if text in ["Common", "Uncommon", "Legendary", "Boss", "Lunar", "Void", "Equipment"]: continue
                            if text == name: continue
                            if len(text) < 10: continue
                            score = len(text)
                            if "%" in text: score += 50
                            if "damage" in lower_text: score += 20
                            if "heal" in lower_text: score += 20
                            if "cooldown" in lower_text: score += 20
                            candidates.append((score, text))
                        
                        if candidates:
                            candidates.sort(key=lambda x: x[0], reverse=True)
                            brief_desc = candidates[0][1]
                        
                        img_tag = row.find("img")
                        img_url = None
                        if img_tag:
                            img_url = img_tag.get("data-src") or img_tag.get("src")
                            if img_url and img_url.startswith("/"): img_url = WIKI_BASE + img_url
                        
                        vibe_color = RARITY_VIBES.get(target_rarity, "#FFF")
                        self.cb(current_idx, total_items, f"[{target_rarity}]", name, vibe_color)
                        
                        full_notes = self.fetch_full_text(name)
                        safe_n = self.safe_name(name)
                        
                        console_id = INTERNAL_ID_MAP.get(name, safe_n)
                        
                        item_dir = os.path.join(DATA_DIR, self.safe_name(target_rarity), safe_n)
                        if not os.path.exists(item_dir): os.makedirs(item_dir)
                        
                        item_data = {
                            "name": name,
                            "id": console_id, 
                            "desc": brief_desc, 
                            "notes": full_notes, 
                            "url": href,
                            "img_file": f"{safe_n}.png",
                            "local_path": item_dir,
                            "rarity_raw": target_rarity
                        }
                        
                        with open(os.path.join(item_dir, "meta.json"), 'w') as f: json.dump(item_data, f, indent=4)
                        if img_url: self.save_image(img_url, item_dir, f"{safe_n}.png")
                        
                        collected[target_rarity].append(item_data)
                        time.sleep(0.05)
                        
                    except Exception as e:
                        logging.error(f"Row Error: {e}")
                        continue

            if self.stop_flag: return False
            with open(CACHE_FILE, 'w') as f: json.dump(collected, f, indent=4)
            return True
            
        except Exception as e:
            logging.error(f"Sync Fatal: {e}")
            return False

# --- 5. DATA MANAGER ---
class DataManager:
    def __init__(self): self.db = {}; self.mem_cache = {}
    def load_db(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f: self.db = json.load(f); return True
            except: return False
        return False
    def get_image(self, item_data, size=(45, 45)):
        key = f"{item_data['id']}_{size}"
        if key in self.mem_cache: return self.mem_cache[key]
        try:
            path = os.path.join(item_data["local_path"], item_data["img_file"])
            if os.path.exists(path):
                img = ctk.CTkImage(light_image=Image.open(path), size=size); self.mem_cache[key] = img; return img
        except: pass
        return None

# --- 6. UTILS ---
def center_window(win, width, height):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - width) // 2, (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

# --- 7. POPUPS & DIALOGS ---
class DetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, item_data, data_mgr):
        super().__init__(parent); self.title(f"{item_data['name']}"); center_window(self, 600, 700); self.attributes("-topmost", True)
        head = ctk.CTkFrame(self, fg_color="transparent"); head.pack(fill="x", padx=20, pady=20)
        img = data_mgr.get_image(item_data, size=(100, 100))
        if img: ctk.CTkLabel(head, text="", image=img).pack(side="left", padx=(0, 20))
        else: ctk.CTkLabel(head, text="[No Image]", width=100, height=100, fg_color="#444").pack(side="left", padx=(0, 20))
        
        info = ctk.CTkFrame(head, fg_color="transparent"); info.pack(side="left", fill="both")
        ctk.CTkLabel(info, text=item_data['name'], font=("Impact", 24)).pack(anchor="w")
        ctk.CTkLabel(info, text=f"ID: {item_data['id']}", text_color="gray").pack(anchor="w")
        
        ctk.CTkLabel(self, text="Summary", font=("Arial", 14, "bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(self, text=item_data.get('desc', ''), font=("Arial", 12), text_color="#DDD", wraplength=550, justify="left").pack(anchor="w", padx=20, pady=5)

        ctk.CTkLabel(self, text="Full Stats & Notes", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(10,0))
        db = ctk.CTkTextbox(self, height=350, fg_color="#333"); db.pack(fill="both", expand=True, padx=20, pady=5)
        db.insert("0.0", item_data.get('notes',''))
        db.configure(state="disabled")
        
        btm = ctk.CTkFrame(self, fg_color="transparent"); btm.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btm, text="Wiki", command=lambda: webbrowser.open(item_data.get('url', WIKI_BASE))).pack(side="right")
        ctk.CTkButton(btm, text="Close", fg_color="#444", command=self.destroy).pack(side="left")

class SetupWindow(ctk.CTkToplevel):
    def __init__(self, parent, complete_cb):
        super().__init__(parent); self.title("Setup"); center_window(self, 700, 500); self.attributes("-topmost", True); self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
        self.complete_cb = complete_cb; self.start = datetime.now(); self.active = True; self.timer_id = None; self.engine = None
        ctk.CTkLabel(self, text="WIKI ARCHIVE MINER", font=("Impact", 36)).pack(pady=(30, 10))
        grid = ctk.CTkFrame(self, fg_color="transparent"); grid.pack(pady=5)
        self.l_start = ctk.CTkLabel(grid, text=f"Start: {self.start.strftime('%H:%M:%S')}", font=("Consolas", 12)); self.l_start.grid(row=0, column=0, padx=20)
        self.l_el = ctk.CTkLabel(grid, text="Elapsed: 00:00", font=("Consolas", 12)); self.l_el.grid(row=0, column=1, padx=20)
        self.l_eta = ctk.CTkLabel(grid, text="ETA: Calculating...", font=("Consolas", 12)); self.l_eta.grid(row=0, column=2, padx=20)
        stat = ctk.CTkFrame(self, fg_color="transparent", height=60); stat.pack(pady=(20, 10))
        self.l_cat = ctk.CTkLabel(stat, text="[Ready]", font=("Arial", 18, "bold"), text_color="gray"); self.l_cat.pack(side="top")
        self.l_itm = ctk.CTkLabel(stat, text="Preparing to build full Item Archive...", font=("Arial", 14), text_color="white"); self.l_itm.pack(side="bottom")
        self.pb = ctk.CTkProgressBar(self, width=500); self.pb.set(0); self.pb.pack(pady=5)
        self.l_cnt = ctk.CTkLabel(self, text="0 / 0"); self.l_cnt.pack()
        btn_row = ctk.CTkFrame(self, fg_color="transparent"); btn_row.pack(pady=30)
        self.btn = ctk.CTkButton(btn_row, text="START MINE", command=self.start_proc, height=50, width=200, font=("Arial", 14, "bold")); self.btn.pack(side="left", padx=10)
        self.btn_cancel = ctk.CTkButton(btn_row, text="SKIP", command=self.finish, height=50, width=120, fg_color="#880000", state="normal"); self.btn_cancel.pack(side="left", padx=10)
        self.update_timer()
    def update_timer(self):
        if not self.active: return
        self.l_el.configure(text=f"Elapsed: {str(datetime.now()-self.start).split('.')[0]}")
        self.timer_id = self.after(1000, self.update_timer)
    def start_proc(self): self.btn.configure(state="disabled", text="MINING..."); self.btn_cancel.configure(state="disabled"); self.engine = WikiSyncEngine(self.progress); threading.Thread(target=self.run_engine, daemon=True).start()
    def cancel_proc(self): os._exit(0)
    def on_close_attempt(self): os._exit(0)
    def progress(self, cur, tot, cat, name, col):
        if not self.active: return
        self.pb.set(cur/max(tot,1)); self.l_cat.configure(text=cat, text_color=col); self.l_itm.configure(text=name, text_color=col); self.l_cnt.configure(text=f"{cur} / {tot}")
        if cur > 0: rate = (datetime.now()-self.start).total_seconds()/cur; eta = datetime.now()+timedelta(seconds=(tot-cur)*rate); self.l_eta.configure(text=f"ETA: {eta.strftime('%H:%M:%S')}")
    def run_engine(self):
        if self.engine.run_sync(): self.after(0, self.finish)
        else: self.after(0, self.reset_ui)
    def reset_ui(self):
        if not self.active: return
        self.l_itm.configure(text="Download Stopped / Failed.", text_color="red"); self.btn.configure(state="normal", text="RETRY")
    def finish(self): self.active = False; self.after_cancel(self.timer_id) if self.timer_id else None; self.withdraw(); self.destroy(); self.complete_cb()

class ProfileManager:
    @staticmethod
    def get_profiles():
        files = [f.replace(".json", "") for f in os.listdir(PROFILE_DIR) if f.endswith(".json")]
        if "Default" not in files: files.insert(0, "Default")
        return sorted(files)
    @staticmethod
    def save(name, data, metadata=None):
        clean = {
            "items": {k: {"c": v["chk"].get(), "q": v["qty"].get()} for k,v in data.items() if v["chk"].get() or int(v["qty"].get())>0},
            "meta": metadata if metadata else {}
        }
        with open(os.path.join(PROFILE_DIR, f"{name}.json"), 'w') as f: json.dump(clean, f, indent=4)
    @staticmethod
    def load(name):
        p = os.path.join(PROFILE_DIR, f"{name}.json")
        if os.path.exists(p):
            with open(p, 'r') as f: 
                d = json.load(f)
                if "items" not in d: return {"items": d, "meta": {}}
                return d
        return {"items": {}, "meta": {}}

class ProfileConsole(ctk.CTkToplevel):
    def __init__(self, parent, cb_load, cb_save, curr):
        super().__init__(parent); self.title("Profiles"); center_window(self, 600, 500); self.attributes("-topmost", True)
        self.cb_l=cb_load; self.cb_s=cb_save; self.curr=curr
        ctk.CTkLabel(self, text="PROFILES", font=("Impact", 24)).pack(pady=10)
        panes = ctk.CTkFrame(self, fg_color="transparent"); panes.pack(fill="both", expand=True, padx=20)
        self.scr = ctk.CTkScrollableFrame(panes, width=300); self.scr.pack(side="left", fill="both", expand=True, padx=(0,10))
        ctrl = ctk.CTkFrame(panes); ctrl.pack(side="right", fill="y")
        ctk.CTkButton(ctrl, text="LOAD", fg_color="green", command=self._l).pack(fill="x", pady=5)
        ctk.CTkButton(ctrl, text="SAVE CURRENT", fg_color="#444", command=self._s).pack(fill="x", pady=5)
        ctk.CTkButton(ctrl, text="NEW", fg_color="#444", command=self._n).pack(fill="x", pady=5)
        ctk.CTkFrame(ctrl, height=2, fg_color="gray").pack(fill="x", pady=10)
        ctk.CTkLabel(ctrl, text="CLOUD SYNC", font=("Arial", 10, "bold")).pack()
        ctk.CTkButton(ctrl, text="PUSH (Upload)", fg_color="#0055AA", command=self._cloud_up).pack(fill="x", pady=5)
        ctk.CTkButton(ctrl, text="PULL (Download)", fg_color="#0055AA", command=self._cloud_down).pack(fill="x", pady=5)
        self.lbl = ctk.CTkLabel(self, text=f"Active: {curr}", text_color="cyan"); self.lbl.pack(pady=10); self.refresh()
    def refresh(self):
        for w in self.scr.winfo_children(): w.destroy()
        for p in ProfileManager.get_profiles():
            c = "green" if p == self.curr else "transparent"
            ctk.CTkButton(self.scr, text=p, fg_color=c, border_width=1, command=lambda n=p: self._sel(n)).pack(fill="x", pady=2)
    def _sel(self, n): self.sel=n; self.lbl.configure(text=f"Selected: {n}")
    def _l(self): 
        if hasattr(self,'sel'): self.cb_l(self.sel); self.curr=self.sel; self.refresh(); self.lbl.configure(text=f"Loaded: {self.curr}")
    def _s(self): self.cb_s(); self.lbl.configure(text="Saved!")
    def _n(self):
        n = ctk.CTkInputDialog(text="Name:", title="New").get_input()
        if n: self.cb_l(n); self.curr=n; self.cb_s(); self.refresh()
    def _cloud_up(self):
        if not hasattr(self, 'sel'): return messagebox.showerror("Error", "Select a profile first.")
        self.lbl.configure(text="Uploading...", text_color="yellow"); self.update()
        success, msg = CloudManager.push_profile(self.sel)
        color = "green" if success else "red"
        self.lbl.configure(text=msg, text_color=color)
        if not success: messagebox.showerror("Upload Failed", msg)
    def _cloud_down(self):
        self.lbl.configure(text="Checking GitHub...", text_color="yellow"); self.update()
        success, msg = CloudManager.pull_profiles()
        self.lbl.configure(text=msg, text_color="green" if success else "red")
        self.refresh()

class SafeCloseDialog(ctk.CTkToplevel):
    def __init__(self, parent, cb_yes):
        super().__init__(parent); self.title("Confirm Exit"); center_window(self, 300, 150); self.attributes("-topmost", True)
        ctk.CTkLabel(self, text="Close ROR2 Architect?", font=("Arial", 14, "bold")).pack(pady=30)
        row = ctk.CTkFrame(self, fg_color="transparent"); row.pack()
        ctk.CTkButton(row, text="YES", width=80, fg_color="red", command=cb_yes).pack(side="left", padx=10)
        ctk.CTkButton(row, text="NO", width=80, fg_color="gray", command=self.destroy).pack(side="left", padx=10)

# --- 10. MAIN APP ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = int(sw * 0.85), int(sh * 0.85); x, y = (sw - w) // 2, (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.protocol("WM_DELETE_WINDOW", self.request_close)
        
        ctk.set_appearance_mode("Dark")
        self.data = DataManager(); self.q = queue.Queue(); self.run = True
        self.prof = "Default"; self.sel_i = {}
        self.steam = SteamManager()
        self.log_watcher = LogWatcher()
        self.log_watcher.start_watching()
        self.steam_user = ctk.StringVar(value="Default / Auto")
        self.cat_f = {}; self.act_c = None
        
        # --- PER-TAB HOTKEY CONFIG ---
        self.hk_cfg = {
            "Architect": {"mode": ctk.StringVar(value="Keyboard"), "key": ctk.StringVar(value="f5")},
            "Boss": {"mode": ctk.StringVar(value="Keyboard"), "key": ctk.StringVar(value="f6")},
            "Mob": {"mode": ctk.StringVar(value="Keyboard"), "key": ctk.StringVar(value="f7")}
        }
        
        # --- DIRECTOR STATE ---
        self.queues = {"Boss": [], "Mob": []}
        self.ui_textboxes = {}
        self.active_loops = {"Boss": False, "Mob": False}
        self.loop_buttons = {}
        self.smart_chk_vars = {"Boss": ctk.BooleanVar(value=False), "Mob": ctk.BooleanVar(value=False)}
        self.interval_vars = {"Boss": ctk.StringVar(value="30"), "Mob": ctk.StringVar(value="5")}
        
        self.sel_boss = ctk.StringVar(value=list(BOSS_DB.keys())[0])
        self.sel_mob = ctk.StringVar(value=list(MOB_DB.keys())[0])
        self.ent_elite_boss = ctk.StringVar(value="None")
        self.ent_team_boss = ctk.StringVar(value="Monster (Enemy)")
        self.ent_count_boss = ctk.StringVar(value="1")
        self.ent_elite_mob = ctk.StringVar(value="None")
        self.ent_team_mob = ctk.StringVar(value="Monster (Enemy)")
        self.ent_count_mob = ctk.StringVar(value="1")
        self.dir_disabled = False

        self.withdraw()
        
        # Corrupt check
        corrupt = False
        if os.path.exists(CACHE_FILE):
            if os.path.getsize(CACHE_FILE) < 1024: corrupt = True
        
        if not os.path.exists(CACHE_FILE) or corrupt:
            # Fix GC Issue: Keep reference to window
            self.setup_window = SetupWindow(self, self.on_setup_complete)
        else:
            self._ask_upd()

    def on_setup_complete(self): self.deiconify(); self._init_main()
    
    def _ask_upd(self):
        d = ctk.CTkToplevel(self); d.title("Database Check"); center_window(d, 400, 250); d.attributes("-topmost", True); d.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        self.upd_window = d # Keep ref
        ctk.CTkLabel(d, text="ARCHIVE FOUND", font=("Impact", 24)).pack(pady=(20, 10))
        ctk.CTkLabel(d, text="Files detected. Validate updates from Wiki?", font=("Arial", 14, "bold")).pack(pady=5)
        row = ctk.CTkFrame(d, fg_color="transparent"); row.pack()
        def y(): d.destroy(); self.setup_window = SetupWindow(self, self.on_setup_complete)
        def n(): d.destroy(); self.on_setup_complete()
        ctk.CTkButton(row, text="YES, UPDATE", width=120, fg_color="green", command=y).pack(side="left", padx=10)
        ctk.CTkButton(row, text="NO, LAUNCH", width=120, fg_color="gray", command=n).pack(side="left", padx=10)

    def request_close(self): SafeCloseDialog(self, lambda: os._exit(0))

    def _init_main(self):
        if not self.data.load_db(): return
        # --- LEFT SIDEBAR ---
        sb = ctk.CTkFrame(self, width=280, corner_radius=0); sb.pack(side="left", fill="y")
        ctk.CTkLabel(sb, text="FUN HOUSE", font=("Impact", 30)).pack(pady=(30,0))
        ctk.CTkLabel(sb, text=f"v{VERSION}", text_color="gray").pack(pady=(0,20))
        ctk.CTkButton(sb, text="MANAGE PROFILES", fg_color="#333", command=lambda: ProfileConsole(self, self._lp, self._sp, self.prof)).pack(fill="x", padx=20)
        self.lp_lbl = ctk.CTkLabel(sb, text=f"Active: {self.prof}", text_color="cyan"); self.lp_lbl.pack(pady=5)
        
        # Hotkey Summary Panel
        ctk.CTkLabel(sb, text="ACTIVE HOTKEYS", font=("Arial", 12, "bold")).pack(pady=(20,5))
        self.hk_labels = {}
        for k in ["Architect", "Boss", "Mob"]:
            f = ctk.CTkFrame(sb, fg_color="transparent")
            f.pack(fill="x", padx=10)
            ctk.CTkLabel(f, text=f"{k}:", width=60, anchor="w").pack(side="left")
            l = ctk.CTkLabel(f, text="...", text_color="yellow", anchor="w")
            l.pack(side="left")
            self.hk_labels[k] = l
        self.conflict_lbl = ctk.CTkLabel(sb, text="", text_color="red", font=("Arial", 10, "bold"))
        self.conflict_lbl.pack(pady=5)
        
        ctk.CTkLabel(sb, text="GAME LAUNCH", font=("Arial", 12, "bold")).pack(pady=(20,5))
        self.stm_menu = ctk.CTkOptionMenu(sb, values=self.steam.accounts, variable=self.steam_user); self.stm_menu.pack(padx=20, pady=2, fill="x")
        self.launch_armed = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(sb, text="Armed", variable=self.launch_armed, command=self._tog_launch, progress_color="red").pack(pady=5)
        self.btn_launch = ctk.CTkButton(sb, text="LAUNCH ROR2", fg_color="darkred", state="disabled", command=self._launch_game); self.btn_launch.pack(pady=5, padx=20)
        
        ctk.CTkButton(sb, text="SAFE CLOSE", fg_color="#400", command=self.request_close).pack(side="bottom", pady=20, padx=20)
        self.stat = ctk.CTkLabel(sb, text="Ready", text_color="#00FF00"); self.stat.pack(side="bottom", pady=5)
        
        # --- RIGHT TABS ---
        self.main_tabs = ctk.CTkTabview(self); self.main_tabs.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # TAB 1: ARCHITECT
        self.main_tabs.add("Architect")
        t_arch = self.main_tabs.tab("Architect")
        self._build_hotkey_ui(t_arch, "Architect", "Inject Selected Items")
        
        self.item_tabs = ctk.CTkTabview(t_arch, command=self._tc); self.item_tabs.pack(fill="both", expand=True)
        # Sort tabs by Rarity Logic (Visual Order)
        rarity_order = ["Common", "Uncommon", "Legendary", "Boss", "Lunar", "Void", "Equipment", "Lunar Equipment", "Meal"]
        sorted_cats = sorted(self.data.db.keys(), key=lambda x: rarity_order.index(x) if x in rarity_order else 99)
        
        for c in sorted_cats:
            self.item_tabs.add(c)
            f = ctk.CTkScrollableFrame(self.item_tabs.tab(c))
            f.pack(fill="both", expand=True)
            self.cat_f[c] = f
            # Header Stripe
            ctk.CTkFrame(f, height=5, fg_color=RARITY_VIBES.get(c, "#333")).pack(fill="x", pady=(0,5))
            
        ctk.CTkButton(t_arch, text="Set All 10 (Selected)", fg_color="#555", command=self._s10).pack(pady=5)

        # TAB 2: DIRECTOR
        self.main_tabs.add("Director")
        t_dir = self.main_tabs.tab("Director")
        self.dir_tabs = ctk.CTkTabview(t_dir); self.dir_tabs.pack(fill="both", expand=True)
        self.dir_tabs.add("Boss Rush")
        self.dir_tabs.add("Mob Modifier")
        
        self._build_director_ui(self.dir_tabs.tab("Boss Rush"), BOSS_DB, "Boss")
        self._build_director_ui(self.dir_tabs.tab("Mob Modifier"), MOB_DB, "Mob")
        
        self._lp(self.prof)
        self.after(200, self._tc); self._sl(); self._update_hk_summary()

    def _build_hotkey_ui(self, parent, tab_key, action_desc):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(f, text=f"Hotkey ({action_desc}):", font=("Arial", 11, "bold")).pack(side="left")
        mode_var = self.hk_cfg[tab_key]["mode"]; key_var = self.hk_cfg[tab_key]["key"]
        seg = ctk.CTkSegmentedButton(f, values=["Keyboard", "Controller"], variable=mode_var, command=lambda x: self._update_hk_summary())
        seg.pack(side="left", padx=10)
        c = ctk.CTkFrame(f, fg_color="transparent"); c.pack(side="left")
        kb_entry = ctk.CTkEntry(c, textvariable=key_var, width=50)
        ctrl_menu = ctk.CTkOptionMenu(c, values=["BTN_NORTH", "BTN_SOUTH", "BTN_EAST", "BTN_WEST"], variable=key_var)
        def update_vis(*args):
            if mode_var.get() == "Keyboard": ctrl_menu.pack_forget(); kb_entry.pack()
            else: kb_entry.pack_forget(); ctrl_menu.pack()
            self._update_hk_summary()
        mode_var.trace_add("write", update_vis); update_vis()
        ctk.CTkButton(f, text="Set", width=40, fg_color="#444", command=self._update_hk_hooks).pack(side="left", padx=5)

    def _update_hk_summary(self):
        overlap = []; seen = {}
        for k, v in self.hk_cfg.items():
            m = v["mode"].get(); kv = v["key"].get()
            txt = f"{kv}" if m == "Keyboard" else f"🎮 {kv.replace('BTN_', '')}"
            self.hk_labels[k].configure(text=txt)
            combo = f"{m}:{kv}"
            if combo in seen: overlap.append(f"{seen[combo]} & {k}")
            seen[combo] = k
        if overlap: self.conflict_lbl.configure(text="Overlap Detected!")
        else: self.conflict_lbl.configure(text="")
        self._update_hk_hooks()

    def _update_hk_hooks(self):
        keyboard.unhook_all()
        for k, v in self.hk_cfg.items():
            if v["mode"].get() == "Keyboard":
                try: keyboard.add_hotkey(v["key"].get(), lambda t=k: self.q.put(t))
                except: pass

    def _build_director_ui(self, parent, db, type_name):
        self._build_hotkey_ui(parent, type_name, "Toggle Loop / Spawn")
        fc = ctk.CTkFrame(parent); fc.pack(fill="x", padx=10, pady=5)
        self.btn_stop_spawns = ctk.CTkButton(fc, text="DISABLE NATURAL SPAWNS", fg_color="orange", command=self._toggle_spawns)
        self.btn_stop_spawns.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        ctk.CTkButton(fc, text="NUKE ALL ENEMIES", fg_color="red", command=self._kill_all).pack(side="right", fill="x", expand=True, padx=5, pady=5)
        bi = ctk.CTkFrame(parent); bi.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(bi, text="Entity Injector", font=("Arial", 12, "bold")).pack(pady=5)
        grid = ctk.CTkFrame(bi, fg_color="transparent"); grid.pack(pady=5)
        ctk.CTkLabel(grid, text=f"{type_name}:").grid(row=0, column=0, padx=5)
        var_sel = self.sel_boss if type_name == "Boss" else self.sel_mob
        var_count = self.ent_count_boss if type_name == "Boss" else self.ent_count_mob
        var_elite = self.ent_elite_boss if type_name == "Boss" else self.ent_elite_mob
        var_team = self.ent_team_boss if type_name == "Boss" else self.ent_team_mob
        ctk.CTkOptionMenu(grid, values=list(db.keys()), variable=var_sel).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(grid, text="Count:").grid(row=0, column=2, padx=5)
        ctk.CTkEntry(grid, textvariable=var_count, width=40).grid(row=0, column=3, padx=5)
        grid2 = ctk.CTkFrame(bi, fg_color="transparent"); grid2.pack(pady=5)
        ctk.CTkLabel(grid2, text="Elite:").grid(row=0, column=0, padx=5)
        ctk.CTkOptionMenu(grid2, values=list(ELITE_MODIFIERS.keys()), variable=var_elite).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(grid2, text="Team:").grid(row=0, column=2, padx=5)
        ctk.CTkOptionMenu(grid2, values=list(TEAM_INDICES.keys()), variable=var_team).grid(row=0, column=3, padx=5)
        qf = ctk.CTkFrame(bi, fg_color="transparent"); qf.pack(fill="x", pady=10)
        ctk.CTkButton(qf, text="ADD TO QUEUE", width=120, command=lambda d=db, t=type_name, v=var_sel, c=var_count, e=var_elite, tm=var_team: self._add_queue(d, t, v, c, e, tm)).pack(side="left", padx=20)
        ctk.CTkButton(qf, text="SPAWN NOW", width=120, fg_color="#00AA00", command=lambda d=db, v=var_sel, c=var_count, e=var_elite, tm=var_team: self._spawn_one(d, v, c, e, tm)).pack(side="right", padx=20)
        tb = ctk.CTkTextbox(parent, height=100); tb.pack(fill="x", padx=10, pady=5)
        self.ui_textboxes[type_name] = tb
        pf = ctk.CTkFrame(parent); pf.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(pf, text="Persistence / Smart Spawn", font=("Arial", 12, "bold")).pack(pady=5)
        pr = ctk.CTkFrame(pf, fg_color="transparent"); pr.pack()
        ctk.CTkLabel(pr, text="Interval (s):").pack(side="left", padx=5)
        ctk.CTkEntry(pr, textvariable=self.interval_vars[type_name], width=40).pack(side="left", padx=5)
        btn = ctk.CTkButton(pf, text=f"START {type_name.upper()} LOOP", fg_color="#333", command=lambda t=type_name: self._toggle_persist(t))
        btn.pack(pady=5); self.loop_buttons[type_name] = btn
        ctk.CTkCheckBox(pf, text="Smart Spawn (Only when < 1 Enemy)", variable=self.smart_chk_vars[type_name]).pack(pady=5)

    def _add_queue(self, db, type_name, var_sel, var_count, var_elite, var_team):
        name = var_sel.get()
        self.queues[type_name].append({
            "id": db[name], "count": var_count.get(),
            "elite": ELITE_MODIFIERS[var_elite.get()],
            "team": TEAM_INDICES[var_team.get()],
            "name": name
        })
        self._update_q_ui(type_name)

    def _update_q_ui(self, type_name):
        tb = self.ui_textboxes[type_name]
        tb.delete("0.0", "end")
        for i, item in enumerate(self.queues[type_name]):
            tb.insert("end", f"{i+1}. {item['name']} (x{item['count']})\n")

    def _spawn_one(self, db, var_sel, var_count, var_elite, var_team):
        body = db[var_sel.get()]
        cmd = f"spawn_ai {body} {var_count.get()} {ELITE_MODIFIERS[var_elite.get()]} {TEAM_INDICES[var_team.get()]}"
        self._inj_cmd(cmd)

    def _toggle_persist(self, type_name):
        active = self.active_loops[type_name]
        self.active_loops[type_name] = not active
        if not active:
            self.loop_buttons[type_name].configure(text=f"STOP {type_name.upper()} LOOP", fg_color="red")
            threading.Thread(target=self._persist_loop, args=(type_name,), daemon=True).start()
        else:
            self.loop_buttons[type_name].configure(text=f"START {type_name.upper()} LOOP", fg_color="#333")

    def _persist_loop(self, type_name):
        idx = 0
        while self.active_loops[type_name] and self.queues[type_name]:
            if self.smart_chk_vars[type_name].get():
                self._inj_cmd("list_ai", silent=True); time.sleep(0.5) 
                if self.log_watcher.enemy_count > 0: time.sleep(1); continue
            item = self.queues[type_name][idx]
            cmd = f"spawn_ai {item['id']} {item['count']} {item['elite']} {item['team']}"
            self._inj_cmd(cmd)
            try: wait = int(self.interval_vars[type_name].get())
            except: wait = 5
            time.sleep(wait); idx = (idx + 1) % len(self.queues[type_name])

    def _inj_cmd(self, cmd, silent=False):
        def r():
            time.sleep(0.1); pydirectinput.press('f2'); time.sleep(0.1)
            keyboard.write(cmd); time.sleep(0.01); pydirectinput.press('enter'); time.sleep(0.01)
            pydirectinput.press('f2')
        threading.Thread(target=r, daemon=True).start()
        if not silent: self.stat.configure(text=f"Sent: {cmd}", text_color="cyan")

    def _toggle_spawns(self):
        self.dir_disabled = not self.dir_disabled
        val = "1" if self.dir_disabled else "0"
        txt = "ENABLE NATURAL SPAWNS" if self.dir_disabled else "DISABLE NATURAL SPAWNS"
        col = "green" if self.dir_disabled else "orange"
        self._inj_cmd(f"director_combat_disable {val}")
        self.btn_stop_spawns.configure(text=txt, fg_color=col)

    def _kill_all(self): self._inj_cmd("kill_all Monster")

    def _tog_launch(self):
        s = "normal" if self.launch_armed.get() else "disabled"
        c = "red" if self.launch_armed.get() else "darkred"
        self.btn_launch.configure(state=s, fg_color=c)
    def _launch_game(self):
        msg = self.steam.launch_game(self.steam_user.get())
        self.stat.configure(text=msg, text_color="orange")

    def _lp(self, n):
        self.prof = n; self.lp_lbl.configure(text=f"Active: {n}")
        d = ProfileManager.load(n)
        for v in self.sel_i.values(): v["chk"].set(False); v["qty"].set("0")
        items = d.get("items", {})
        for i, v in items.items():
            if i in self.sel_i: self.sel_i[i]["chk"].set(v["c"]); self.sel_i[i]["qty"].set(v["q"])
        meta = d.get("meta", {})
        saved_user = meta.get("steam_user", "Default / Auto")
        if saved_user in self.steam.accounts: self.steam_user.set(saved_user)
        else: self.steam_user.set("Default / Auto")
        hk_data = meta.get("hotkeys", {})
        for k, v in self.hk_cfg.items():
            if k in hk_data:
                v["mode"].set(hk_data[k].get("mode", "Keyboard"))
                v["key"].set(hk_data[k].get("key", "f5"))
        self._update_hk_summary()

    def _sp(self): 
        hk_data = {}
        for k, v in self.hk_cfg.items(): hk_data[k] = {"mode": v["mode"].get(), "key": v["key"].get()}
        meta = {"steam_user": self.steam_user.get(), "hotkeys": hk_data}
        ProfileManager.save(self.prof, self.sel_i, meta)
        
    def _mc(self, m): self.imode=m; self._bi(); self._hk()
    def _sct(self, t): self.ctrig=t
    def _togg_kb(self): self.kb_unlocked = self.uv.get(); self._build_input()
    def _set_ktrig(self, t): self.kb_trigger = t; self._hook_kb()
    def _upd_kb(self): self.kb_trigger = self.ke.get(); self._hook_kb()
    def _hk(self): self._update_hk_hooks()

    def _tc(self):
        try:
            c = self.item_tabs.get(); 
            if c == self.act_c: return
            self.act_c = c
            if len(self.cat_f[c].winfo_children()) == 1: self._lb(c)
        except: pass
    
    def _lb(self, c):
        items = self.data.db.get(c, [])
        current_loaded = len(self.cat_f[c].winfo_children()) - 1
        if current_loaded >= len(items): return
        end = min(current_loaded + 15, len(items))
        for i in items[current_loaded:end]: self._mk(self.cat_f[c], i)
        if self.cat_f[c]._parent_canvas.yview()[1] < 1.0: self.after(100, lambda: self._lb(c))

    def _mk(self, p, i):
        c = ctk.CTkFrame(p, fg_color="#2B2B2B", border_width=1, border_color="#3A3A3A"); c.pack(fill="x", pady=4, padx=5)
        img = self.data.get_image(i)
        l = ctk.CTkLabel(c, text="", image=img) if img else ctk.CTkFrame(c, width=45, height=45, fg_color="#444"); l.pack(side="left", padx=10, pady=5)
        l.bind("<Button-1>", lambda e: DetailsWindow(self, i, self.data))
        info = ctk.CTkFrame(c, fg_color="transparent"); info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text=i['name'], font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=i['desc'][:80]+"...", text_color="gray", font=("Arial", 11), anchor="w").pack(fill="x")
        ctrl = ctk.CTkFrame(c, fg_color="transparent"); ctrl.pack(side="right", padx=10)
        chk = ctk.BooleanVar(); qty = ctk.StringVar(value="0")
        ctk.CTkCheckBox(ctrl, text="", variable=chk, width=0).pack(side="top", pady=2)
        ctk.CTkEntry(ctrl, textvariable=qty, width=40).pack(side="bottom", pady=2)
        self.sel_i[i['id']] = {"chk": chk, "qty": qty}
        pd = ProfileManager.load(self.prof).get("items", {})
        if i['id'] in pd: chk.set(pd[i['id']]["c"]); qty.set(pd[i['id']]["q"])

    def _sl(self): threading.Thread(target=self._cl, daemon=True).start(); self._hk(); self._pl(); self._lpl()
    def _cl(self):
        while self.run:
            try:
                events = get_gamepad()
                for e in events:
                    if e.ev_type == "Key" and e.state == 1:
                        for k, v in self.hk_cfg.items():
                            if v["mode"].get() == "Controller" and e.code == v["key"].get(): self.q.put(k)
            except: time.sleep(0.1)
    def _pl(self):
        try:
            action = self.q.get_nowait()
            if action == "Architect": self._inj()
            elif action == "Boss": self._toggle_persist("Boss")
            elif action == "Mob": self._toggle_persist("Mob")
        except: pass
        if self.run: self.after(50, self._pl)
    def _lpl(self):
        try:
            if self.main_tabs.get() == "Architect" and self.act_c:
                if self.cat_f[self.act_c]._parent_canvas.yview()[1] > 0.9: self._lb(self.act_c)
        except: pass
        if self.run: self.after(200, self._lpl)
    def _s10(self): 
        for v in self.sel_i.values(): 
            if v["chk"].get(): v["qty"].set("10")
    def _inj(self):
        self.stat.configure(text="INJECTING...", text_color="orange"); cmds = []
        for i, v in self.sel_i.items():
            if v["chk"].get():
                try: 
                    # --- CRITICAL FIX: DISCRIMINATE ITEM VS EQUIPMENT ---
                    # The game command is 'give_equip' for orange/blue active items
                    # And 'give_item' for passives.
                    # We check the Rarity RAW stored in the meta.
                    rarity = v.get("rarity_raw", "Common") # Need to access this from self.data.db lookup
                    
                    # Look up rarity from DB since self.sel_i only stores qty/chk
                    rarity = "Common"
                    for cat_name, cat_items in self.data.db.items():
                        found = False
                        for it in cat_items:
                            if it["id"] == i:
                                rarity = cat_name
                                found = True
                                break
                        if found: break
                    
                    cmd_type = "give_item"
                    if "Equipment" in rarity: cmd_type = "give_equip"
                    
                    if int(v["qty"].get()) > 0: 
                        cmds.append(f"{cmd_type} {i} {v['qty'].get()}")
                except: pass
        if not cmds: self.stat.configure(text="No Items", text_color="yellow"); return
        def r():
            time.sleep(0.1); pydirectinput.press('f2'); time.sleep(0.1)
            keyboard.write("cheats 1"); time.sleep(0.01); pydirectinput.press('enter'); time.sleep(0.01)
            for c in cmds: keyboard.write(c); time.sleep(0.01); pydirectinput.press('enter'); time.sleep(0.01)
            pydirectinput.press('f2'); self.stat.configure(text="Done", text_color="green")
        threading.Thread(target=r, daemon=True).start()

if __name__ == "__main__":
    App().mainloop()
