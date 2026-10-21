"""All thresholds and paths for Open in Time."""
from pathlib import Path

ROOT = Path(__file__).parent
# Data folder: "data/" or the cloned repo folder, whichever exists
DATA_DIR = next(
    (p for p in [ROOT / "data", ROOT / "nfl-big-data-bowl-regional-event-data" / "data"] if p.exists()),
    ROOT / "data",
)
CACHE_DIR = ROOT / "cache"

FPS = 10  # tracking frames per second

# Plays kept: complete, incomplete, interception, sack (scrambles excluded)
PASS_RESULTS = {"C", "I", "IN", "S"}
RECEIVER_POSITIONS = {"WR", "TE", "RB", "FB"}

SNAP_EVENTS = {"ball_snap", "autoevent_ballsnap"}
END_EVENTS = {"pass_forward", "autoevent_passforward", "qb_sack", "qb_strip_sack"}
EXTRA_FRAMES = 5  # frames kept after the end frame (animation + sustain check)

# Receiver "open": separation >= OPEN_DIST for OPEN_SUSTAIN frames, not before OPEN_MIN_TIME
OPEN_DIST = 2.5       # yards
OPEN_MIN_TIME = 0.5   # seconds after snap
OPEN_SUSTAIN = 3      # consecutive frames
OPEN_UNCOVERED_TIME = 1.5  # never covered: counts as open from this time (the snap cushion is gone)

# Pressure: a pass rusher within PRESSURE_DIST of the QB
PRESSURE_DIST = 2.0   # yards
PRESSURE_MIN_TIME = 0.5  # seconds after snap (earlier = tracking noise)
PRESSURE_CLEAR_DIST = 3.0  # the QB must first be this far from every rusher (under center fix)

MIN_ROUTES = 40       # min routes for a player to appear in the summary
N_DEMO_PLAYS = 30     # plays stored with full frames for the animation
DEMO_MAX_TIME = 4.5   # demo plays: ball out (or sack) within this time, to stay typical
