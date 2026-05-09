import math
import os
import time
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field

DEBUG_LOG = os.environ.get("ORBIT_DEBUG") == "1"
_INFERRED_STEP = -1

# ============================================================
# Shared Configuration
# ============================================================

BOARD = 100.0
CENTER_X = 50.0
CENTER_Y = 50.0
SUN_R = 10.0
MAX_SPEED = 6.0
SUN_SAFETY = 1.5
ROTATION_LIMIT = 50.0
TOTAL_STEPS = 500
SIM_HORIZON = 110
ROUTE_SEARCH_HORIZON = 60
HORIZON = SIM_HORIZON
LAUNCH_CLEARANCE = 0.1

EARLY_TURN_LIMIT = 40
OPENING_TURN_LIMIT = 55
LATE_REMAINING_TURNS = 60
VERY_LATE_REMAINING_TURNS = 25

SAFE_NEUTRAL_MARGIN = 2
CONTESTED_NEUTRAL_MARGIN = 2
INTERCEPT_TOLERANCE = 1

SAFE_OPENING_PROD_THRESHOLD = 4
SAFE_OPENING_TURN_LIMIT = 10
ROTATING_OPENING_MAX_TURNS = 16
ROTATING_OPENING_LOW_PROD = 2
FOUR_PLAYER_ROTATING_REACTION_GAP = 3
FOUR_PLAYER_ROTATING_SEND_RATIO = 0.62
FOUR_PLAYER_ROTATING_TURN_LIMIT = 10

COMET_MAX_CHASE_TURNS = 10

ATTACK_COST_TURN_WEIGHT = 0.55
SNIPE_COST_TURN_WEIGHT = 0.45
INDIRECT_VALUE_SCALE = 0.15
INDIRECT_FRIENDLY_WEIGHT = 0.35
INDIRECT_NEUTRAL_WEIGHT = 0.9
INDIRECT_ENEMY_WEIGHT = 1.25

STATIC_NEUTRAL_VALUE_MULT = 1.4
STATIC_HOSTILE_VALUE_MULT = 1.55
ROTATING_OPENING_VALUE_MULT = 0.9
HOSTILE_TARGET_VALUE_MULT = 1.85
OPENING_HOSTILE_TARGET_VALUE_MULT = 1.45
SAFE_NEUTRAL_VALUE_MULT = 1.2
CONTESTED_NEUTRAL_VALUE_MULT = 0.7
EARLY_NEUTRAL_VALUE_MULT = 1.2
COMET_VALUE_MULT = 0.65
SNIPE_VALUE_MULT = 1.12
SWARM_VALUE_MULT = 1.05
REINFORCE_VALUE_MULT = 1.35
CRASH_EXPLOIT_VALUE_MULT = 1.18
FINISHING_HOSTILE_VALUE_MULT = 1.15
BEHIND_ROTATING_NEUTRAL_VALUE_MULT = 0.92

NEUTRAL_MARGIN_BASE = 2
NEUTRAL_MARGIN_PROD_WEIGHT = 2
NEUTRAL_MARGIN_CAP = 8
HOSTILE_MARGIN_BASE = 3
HOSTILE_MARGIN_PROD_WEIGHT = 2
HOSTILE_MARGIN_CAP = 12
STATIC_TARGET_MARGIN = 4
CONTESTED_TARGET_MARGIN = 5
FOUR_PLAYER_TARGET_MARGIN = 3
LONG_TRAVEL_MARGIN_START = 18
LONG_TRAVEL_MARGIN_DIVISOR = 3
LONG_TRAVEL_MARGIN_CAP = 8
COMET_MARGIN_RELIEF = 6
FINISHING_HOSTILE_SEND_BONUS = 3

STATIC_TARGET_SCORE_MULT = 1.18
EARLY_STATIC_NEUTRAL_SCORE_MULT = 1.25
FOUR_PLAYER_ROTATING_NEUTRAL_SCORE_MULT = 0.84
DENSE_STATIC_NEUTRAL_COUNT = 4
DENSE_ROTATING_NEUTRAL_SCORE_MULT = 0.86
SNIPE_SCORE_MULT = 1.12
SWARM_SCORE_MULT = 1.06
CRASH_EXPLOIT_SCORE_MULT = 1.05

FOLLOWUP_MIN_SHIPS = 8
FALLBACK_MIN_ATTACK_LEFT = 18
FALLBACK_MIN_STEP = 35
FALLBACK_TOP_TARGETS = 3
FALLBACK_SCORE_MULT = 0.82
PRESSURE_MIN_STEP = 45
PRESSURE_MIN_TOTAL_BUDGET = 180
PRESSURE_MIN_SOURCE_BUDGET = 28
PRESSURE_SOURCE_TOP_K = 6
PRESSURE_TARGET_TOP_K = 8
PRESSURE_MAX_MOVES = 5
PRESSURE_SEND_FRACTION = 0.62
PRESSURE_TIME_FLOOR = 0.05
ROUTE_TARGET_TOP_K = 18
ROUTE_TARGET_FOUR_PLAYER_BONUS = 4
ROUTE_TARGET_FINISHING_BONUS = 4
ROUTE_TARGET_LOW_TIME_TOP_K = 10
ROUTE_LOW_TIME_THRESHOLD = 0.28
FOLLOWUP_TARGET_TOP_K = 14
FALLBACK_CHEAP_TARGET_TOP_K = 12
DOOMED_TARGET_TOP_K = 10
LOW_VALUE_COMET_PRODUCTION = 1
LATE_CAPTURE_BUFFER = 5
VERY_LATE_CAPTURE_BUFFER = 3

DEFENSE_LOOKAHEAD_TURNS = 28
DEFENSE_COST_TURN_WEIGHT = 0.4
DEFENSE_FRONTIER_SCORE_MULT = 1.12
DEFENSE_SEND_MARGIN_BASE = 1
DEFENSE_SEND_MARGIN_PROD_WEIGHT = 1
DEFENSE_SHIP_VALUE = 0.55

REINFORCE_ENABLED = True
REINFORCE_MIN_PRODUCTION = 2
REINFORCE_MAX_TRAVEL_TURNS = 22
REINFORCE_SAFETY_MARGIN = 2
REINFORCE_MAX_SOURCE_FRACTION = 0.75
REINFORCE_MIN_FUTURE_TURNS = 40
REINFORCE_HOLD_LOOKAHEAD = 20
REINFORCE_COST_TURN_WEIGHT = 0.35

RECAPTURE_LOOKAHEAD_TURNS = 10
RECAPTURE_COST_TURN_WEIGHT = 0.52
RECAPTURE_VALUE_MULT = 0.88
RECAPTURE_FRONTIER_MULT = 1.08
RECAPTURE_PRODUCTION_WEIGHT = 0.6
RECAPTURE_IMMEDIATE_WEIGHT = 0.4

REAR_SOURCE_MIN_SHIPS = 16
REAR_DISTANCE_RATIO = 1.25
REAR_STAGE_PROGRESS = 0.78
REAR_SEND_RATIO_TWO_PLAYER = 0.62
REAR_SEND_RATIO_FOUR_PLAYER = 0.7
REAR_SEND_MIN_SHIPS = 10
REAR_MAX_TRAVEL_TURNS = 40

FRONTIER_DISTANCE = 24.0
FRONTIER_SEND_FRACTION = 0.58
BURST_SEND_FRACTION = 0.72
BURST_SEND_ABSOLUTE = 115
BURST_DEBUG_SHIPS = 180
STALL_DEBUG_BUDGET = 120

PARTIAL_SOURCE_MIN_SHIPS = 6
MULTI_SOURCE_TOP_K = 5
MULTI_SOURCE_ETA_TOLERANCE = 2
MULTI_SOURCE_PLAN_PENALTY = 0.95
HOSTILE_SWARM_ETA_TOLERANCE = 2
THREE_SOURCE_SWARM_ENABLED = True
THREE_SOURCE_MIN_TARGET_SHIPS = 20
THREE_SOURCE_ETA_TOLERANCE = 1
THREE_SOURCE_PLAN_PENALTY = 0.93

PROACTIVE_DEFENSE_HORIZON = 12
PROACTIVE_DEFENSE_RATIO = 0.18
MULTI_ENEMY_PROACTIVE_HORIZON = 14
MULTI_ENEMY_PROACTIVE_RATIO = 0.22
MULTI_ENEMY_STACK_WINDOW = 3
REACTION_SOURCE_TOP_K_MY = 4
REACTION_SOURCE_TOP_K_ENEMY = 4
PROACTIVE_ENEMY_TOP_K = 3

CRASH_EXPLOIT_ENABLED = True
CRASH_EXPLOIT_MIN_TOTAL_SHIPS = 10
CRASH_EXPLOIT_ETA_WINDOW = 2
CRASH_EXPLOIT_POST_CRASH_DELAY = 1

SLINGSHOT_ENABLED = True
SLINGSHOT_LOOK_AHEAD = 60
SLINGSHOT_PROXIMITY_THRESHOLD = 30.0
SLINGSHOT_LAUNCH_PROXIMITY = 28.0
SLINGSHOT_CAPTURE_VALUE_MULT = 1.5
SLINGSHOT_VALUE_MULT = 1.25
SLINGSHOT_SCORE_MULT = 1.18
SLINGSHOT_MIN_SHIPS = 6
SLINGSHOT_COST_TURN_WEIGHT = 0.42

LATE_IMMEDIATE_SHIP_VALUE = 0.6
WEAK_ENEMY_THRESHOLD = 45
ELIMINATION_BONUS = 18.0

BEHIND_DOMINATION = -0.20
AHEAD_DOMINATION = 0.18
FINISHING_DOMINATION = 0.35
FINISHING_PROD_RATIO = 1.25
AHEAD_ATTACK_MARGIN_BONUS = 0.08
BEHIND_ATTACK_MARGIN_PENALTY = 0.05
FINISHING_ATTACK_MARGIN_BONUS = 0.08

DOOMED_EVAC_TURN_LIMIT = 24
DOOMED_MIN_SHIPS = 8

# Comet evacuation: trigger when comet has this many turns of life left
COMET_EVAC_LIFE_THRESHOLD = 22
COMET_EVAC_MIN_SHIPS = 5

# Endgame drain: in final N turns drain every garrison to any reachable target
ENDGAME_DRAIN_TURNS = 15
ENDGAME_DRAIN_MIN_SHIPS = 3

SOFT_ACT_DEADLINE = 0.82
HEAVY_PHASE_MIN_TIME = 0.16
OPTIONAL_PHASE_MIN_TIME = 0.08
HEAVY_ROUTE_PLANET_LIMIT = 32

# --- Improvement 1: Sun-bypass routing ---
SUN_BYPASS_ENABLED = True

# --- Improvement 2: Production-rate-aware scoring ---
SCORING_TIME_DISCOUNT = 0.20   # fraction of value lost per full game length of delay
PROD_DENSITY_WEIGHT = 0.8      # bonus per (production / radius) unit

# --- Improvement 3: Hold-safety budget (production credit) ---
PROACTIVE_DEFENSE_PROD_CREDIT = 0.8  # fraction of accumulated prod to credit against threat

# --- Improvement 4: Endgame denial missions ---
DENIAL_MISSION_ENABLED = True
DENIAL_SHIP_WEIGHT = 1.8       # value per ship denied + production denied

# --- Improvement 5: Enemy-attacking-enemy snipe ---
ENEMY_ATTACK_SNIPE_ENABLED = True
ENEMY_ATTACK_SNIPE_RATIO = 1.2  # attacker must be >= RATIO * garrison to trigger

# --- Improvement 8: Intercept iteration count ---
AIM_MAX_ITERATIONS = 8

# --- Improvement 10: Opening static neutral distance filter ---
OPENING_STATIC_MAX_DIRECT_TURNS = 8   # nearby statics always allowed
OPENING_STATIC_MIN_REACTION_GAP = 4   # far statics need this advantage


# ============================================================
# Shared Types
# ============================================================

Planet = namedtuple(
    "Planet", ["id", "owner", "x", "y", "radius", "ships", "production"]
)
Fleet = namedtuple(
    "Fleet", ["id", "owner", "x", "y", "angle", "from_planet_id", "ships"]
)


@dataclass(frozen=True)
class ShotOption:
    score: float
    src_id: int
    target_id: int
    angle: float
    turns: int
    needed: int
    send_cap: int
    mission: str = "capture"
    anchor_turn: int | None = None


@dataclass
class Mission:
    kind: str
    score: float
    target_id: int
    turns: int
    options: list[ShotOption] = field(default_factory=list)


# ============================================================
# Physics
# ============================================================

def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def orbital_radius(planet):
    return dist(planet.x, planet.y, CENTER_X, CENTER_Y)


def is_static_planet(planet):
    return orbital_radius(planet) + planet.radius >= ROTATION_LIMIT


def fleet_speed(ships):
    if ships <= 1:
        return 1.0
    ratio = math.log(ships) / math.log(1000.0)
    ratio = max(0.0, min(1.0, ratio))
    return 1.0 + (MAX_SPEED - 1.0) * (ratio**1.5)


def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq <= 1e-9:
        return dist(px, py, x1, y1)
    t = ((px - x1) * dx + (py - y1) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return dist(px, py, proj_x, proj_y)


def segment_hits_sun(x1, y1, x2, y2, safety=SUN_SAFETY):
    return point_to_segment_distance(CENTER_X, CENTER_Y, x1, y1, x2, y2) < SUN_R + safety


def launch_point(sx, sy, sr, angle):
    clearance = sr + LAUNCH_CLEARANCE
    return sx + math.cos(angle) * clearance, sy + math.sin(angle) * clearance


def actual_path_geometry(sx, sy, sr, tx, ty, tr):
    angle = math.atan2(ty - sy, tx - sx)
    start_x, start_y = launch_point(sx, sy, sr, angle)
    hit_distance = max(0.0, dist(sx, sy, tx, ty) - (sr + LAUNCH_CLEARANCE) - tr)
    end_x = start_x + math.cos(angle) * hit_distance
    end_y = start_y + math.sin(angle) * hit_distance
    return angle, start_x, start_y, end_x, end_y, hit_distance


def sun_tangent_bypass(sx, sy, sr, tx, ty, tr):
    """Find a path that goes around the sun tangentially and still hits the target circle.

    Returns (angle, hit_distance) from source center, or None if no bypass exists.
    Used when the direct route is blocked by the sun.
    """
    if not SUN_BYPASS_ENABLED:
        return None
    dx = CENTER_X - sx
    dy = CENTER_Y - sy
    sun_dist = math.hypot(dx, dy)
    if sun_dist <= SUN_R + SUN_SAFETY + 0.1:
        return None  # source is inside the exclusion zone
    sin_half = min(1.0, (SUN_R + SUN_SAFETY) / sun_dist)
    half_angle = math.asin(sin_half)
    sun_dir = math.atan2(dy, dx)

    best = None
    for sign in (1.0, -1.0):
        bypass_angle = sun_dir + sign * half_angle
        ray_dx = math.cos(bypass_angle)
        ray_dy = math.sin(bypass_angle)
        # Ray-circle intersection: ray from (sx,sy), circle at (tx,ty) radius tr
        ox = sx - tx
        oy = sy - ty
        b = 2.0 * (ox * ray_dx + oy * ray_dy)
        c = ox * ox + oy * oy - tr * tr
        disc = b * b - 4.0 * c
        if disc < 0:
            continue
        sqrt_disc = math.sqrt(disc)
        t = (-b - sqrt_disc) / 2.0
        if t <= 0:
            t = (-b + sqrt_disc) / 2.0
        if t <= 0:
            continue
        # Verify that the path from the launch point clears the sun
        launch_x = sx + ray_dx * (sr + LAUNCH_CLEARANCE)
        launch_y = sy + ray_dy * (sr + LAUNCH_CLEARANCE)
        end_x = sx + ray_dx * t
        end_y = sy + ray_dy * t
        if segment_hits_sun(launch_x, launch_y, end_x, end_y):
            continue
        hit_dist = max(0.0, t - (sr + LAUNCH_CLEARANCE))
        if best is None or hit_dist < best[1]:
            best = (bypass_angle, hit_dist)
    return best


def safe_angle_and_distance(sx, sy, sr, tx, ty, tr):
    # Launch from the source boundary and time the route to the first hit on
    # the target circle.
    angle, start_x, start_y, end_x, end_y, hit_distance = actual_path_geometry(
        sx,
        sy,
        sr,
        tx,
        ty,
        tr,
    )
    if segment_hits_sun(start_x, start_y, end_x, end_y):
        return sun_tangent_bypass(sx, sy, sr, tx, ty, tr)
    return angle, hit_distance


def predict_planet_position(planet, initial_by_id, angular_velocity, turns):
    init = initial_by_id.get(planet.id)
    if init is None:
        return planet.x, planet.y
    r = dist(init.x, init.y, CENTER_X, CENTER_Y)
    if r + init.radius >= ROTATION_LIMIT:
        return planet.x, planet.y
    cur_ang = math.atan2(planet.y - CENTER_Y, planet.x - CENTER_X)
    new_ang = cur_ang + angular_velocity * turns
    return (
        CENTER_X + r * math.cos(new_ang),
        CENTER_Y + r * math.sin(new_ang),
    )


def predict_comet_position(planet_id, comets, turns):
    for group in comets:
        pids = group.get("planet_ids", [])
        if planet_id not in pids:
            continue
        idx = pids.index(planet_id)
        paths = group.get("paths", [])
        path_index = group.get("path_index", 0)
        if idx >= len(paths):
            return None
        path = paths[idx]
        future_idx = path_index + int(turns)
        if 0 <= future_idx < len(path):
            return path[future_idx][0], path[future_idx][1]
        return None
    return None


def comet_remaining_life(planet_id, comets):
    for group in comets:
        pids = group.get("planet_ids", [])
        if planet_id not in pids:
            continue
        idx = pids.index(planet_id)
        paths = group.get("paths", [])
        path_index = group.get("path_index", 0)
        if idx < len(paths):
            return max(0, len(paths[idx]) - path_index)
    return 0


def comet_slingshot_mult(comet_id: int, comets: list, enemy_planets: list) -> float:
    """Return a capture-value boost when the comet trajectory passes near enemy planets."""
    if not SLINGSHOT_ENABLED or not enemy_planets:
        return 1.0
    look = min(SLINGSHOT_LOOK_AHEAD, comet_remaining_life(comet_id, comets))
    for t in range(look + 1):
        pos = predict_comet_position(comet_id, comets, t)
        if pos is None:
            break
        for ep in enemy_planets:
            if math.hypot(pos[0] - ep.x, pos[1] - ep.y) < SLINGSHOT_PROXIMITY_THRESHOLD:
                return SLINGSHOT_CAPTURE_VALUE_MULT
    return 1.0


def path_hits_comet(start_x, start_y, angle, speed, turns, comets):
    if not comets:
        return False
    for t in range(1, int(turns) + 1):
        fx = start_x + math.cos(angle) * speed * t
        fy = start_y + math.sin(angle) * speed * t
        for group in comets:
            path_index = group.get("path_index", 0) + t
            for path in group.get("paths", []):
                if 0 <= path_index < len(path):
                    cx, cy = path[path_index]
                    if dist(fx, fy, cx, cy) < SUN_R:
                        return True
    return False


def estimate_arrival(sx, sy, sr, tx, ty, tr, ships, comets=None):
    # Use one boundary-aware ETA model for routing, ranking, reserve, and
    # launch decisions.
    safe = safe_angle_and_distance(sx, sy, sr, tx, ty, tr)
    if safe is None:
        return None
    angle, total_d = safe
    speed = fleet_speed(max(1, ships))
    turns = max(1, int(math.ceil(total_d / speed)))
    
    # Check mid-flight comet collision
    angle_geo, start_x, start_y, _, _, _ = actual_path_geometry(sx, sy, sr, tx, ty, tr)
    if comets and path_hits_comet(start_x, start_y, angle_geo, speed, turns, comets):
        return None
        
    return angle, turns


def travel_time(sx, sy, sr, tx, ty, tr, ships, comets=None):
    est = estimate_arrival(sx, sy, sr, tx, ty, tr, ships, comets=comets)
    if est is None:
        return 10**9
    return est[1]


def predict_target_position(target, turns, initial_by_id, ang_vel, comets, comet_ids):
    if target.id in comet_ids:
        return predict_comet_position(target.id, comets, turns)
    return predict_planet_position(target, initial_by_id, ang_vel, turns)


def target_can_move(target, initial_by_id, comet_ids):
    if target.id in comet_ids:
        return True
    init = initial_by_id.get(target.id)
    if init is None:
        return False
    r = dist(init.x, init.y, CENTER_X, CENTER_Y)
    return r + init.radius < ROTATION_LIMIT


def search_safe_intercept(src, target, ships, initial_by_id, ang_vel, comets, comet_ids):
    # If the direct line is unsafe, scan future positions and keep the earliest
    # viable intercept window.
    best = None
    best_score = None
    max_turns = min(HORIZON, ROUTE_SEARCH_HORIZON)
    if target.id in comet_ids:
        max_turns = min(max_turns, max(0, comet_remaining_life(target.id, comets) - 1))

    for candidate_turns in range(1, max_turns + 1):
        pos = predict_target_position(
            target,
            candidate_turns,
            initial_by_id,
            ang_vel,
            comets,
            comet_ids,
        )
        if pos is None:
            continue
        est = estimate_arrival(src.x, src.y, src.radius, pos[0], pos[1], target.radius, ships, comets=comets)
        if est is None:
            continue
        _, turns = est
        if abs(turns - candidate_turns) > INTERCEPT_TOLERANCE:
            continue

        actual_turns = max(turns, candidate_turns)
        actual_pos = predict_target_position(
            target,
            actual_turns,
            initial_by_id,
            ang_vel,
            comets,
            comet_ids,
        )
        if actual_pos is None:
            continue

        confirm = estimate_arrival(
            src.x,
            src.y,
            src.radius,
            actual_pos[0],
            actual_pos[1],
            target.radius,
            ships,
            comets=comets,
        )
        if confirm is None:
            continue

        delta = abs(confirm[1] - actual_turns)
        if delta > INTERCEPT_TOLERANCE:
            continue

        score = (delta, confirm[1], candidate_turns)
        if best is None or score < best_score:
            best_score = score
            best = (confirm[0], confirm[1], actual_pos[0], actual_pos[1])

    return best


def aim_with_prediction(src, target, ships, initial_by_id, ang_vel, comets, comet_ids):
    # Iterate toward a self-consistent moving-target intercept, then fall back
    # to a later safe window if needed.
    est = estimate_arrival(src.x, src.y, src.radius, target.x, target.y, target.radius, ships, comets=comets)
    if est is None:
        if not target_can_move(target, initial_by_id, comet_ids):
            return None
        return search_safe_intercept(
            src,
            target,
            ships,
            initial_by_id,
            ang_vel,
            comets,
            comet_ids,
        )

    tx, ty = target.x, target.y
    for _ in range(AIM_MAX_ITERATIONS):
        _, turns = est
        pos = predict_target_position(target, turns, initial_by_id, ang_vel, comets, comet_ids)
        if pos is None:
            return None
        ntx, nty = pos
        next_est = estimate_arrival(src.x, src.y, src.radius, ntx, nty, target.radius, ships, comets=comets)
        if next_est is None:
            if not target_can_move(target, initial_by_id, comet_ids):
                return None
            return search_safe_intercept(
                src,
                target,
                ships,
                initial_by_id,
                ang_vel,
                comets,
                comet_ids,
            )
        if (
            abs(ntx - tx) < 0.3
            and abs(nty - ty) < 0.3
            and abs(next_est[1] - turns) <= INTERCEPT_TOLERANCE
        ):
            return next_est[0], next_est[1], ntx, nty
        tx, ty = ntx, nty
        est = next_est

    final_est = estimate_arrival(src.x, src.y, src.radius, tx, ty, target.radius, ships, comets=comets)
    if final_est is None:
        return search_safe_intercept(
            src,
            target,
            ships,
            initial_by_id,
            ang_vel,
            comets,
            comet_ids,
        )
    return final_est[0], final_est[1], tx, ty


# ============================================================
# World Model
# ============================================================

def fleet_target_planet(fleet, planets, initial_by_id=None, ang_vel=0.0):
    # Project in-flight fleets by ray-circle hit timing to build a usable
    # arrival ledger. For rotating planets, test future orbital positions so
    # that fleets aimed via aim_with_prediction are correctly matched.
    best_planet = None
    best_time = 1e9
    dir_x = math.cos(fleet.angle)
    dir_y = math.sin(fleet.angle)
    speed = fleet_speed(fleet.ships)
    # Tolerance (turns) between predicted ETA and turn index for rotating match
    _ROTATE_ETA_TOL = 2

    for planet in planets:
        if (
            initial_by_id is not None
            and ang_vel != 0.0
            and not is_static_planet(planet)
        ):
            # Rotating planet: the fleet was aimed at a future orbital position.
            # Try each future turn to find the one where the fleet's direction
            # aligns with the planet's orbit AND ETA is consistent.
            for t in range(1, HORIZON + 1):
                px, py = predict_planet_position(planet, initial_by_id, ang_vel, t)
                dx = px - fleet.x
                dy = py - fleet.y
                proj = dx * dir_x + dy * dir_y
                if proj < 0:
                    continue
                perp_sq = dx * dx + dy * dy - proj * proj
                radius_sq = planet.radius * planet.radius
                if perp_sq >= radius_sq:
                    continue
                hit_d = max(0.0, proj - math.sqrt(max(0.0, radius_sq - perp_sq)))
                ray_eta = hit_d / speed
                if abs(ray_eta - t) <= _ROTATE_ETA_TOL:
                    if t < best_time:
                        best_time = t
                        best_planet = planet
                    break
        else:
            # Static planet: standard ray-circle test against current position.
            dx = planet.x - fleet.x
            dy = planet.y - fleet.y
            proj = dx * dir_x + dy * dir_y
            if proj < 0:
                continue
            perp_sq = dx * dx + dy * dy - proj * proj
            radius_sq = planet.radius * planet.radius
            if perp_sq >= radius_sq:
                continue
            hit_d = max(0.0, proj - math.sqrt(max(0.0, radius_sq - perp_sq)))
            turns = hit_d / speed
            if turns <= HORIZON and turns < best_time:
                best_time = turns
                best_planet = planet

    if best_planet is None:
        return None, None
    return best_planet, int(math.ceil(best_time))


def build_arrival_ledger(fleets, planets, initial_by_id=None, ang_vel=0.0):
    arrivals_by_planet = {planet.id: [] for planet in planets}
    for fleet in fleets:
        target, eta = fleet_target_planet(fleet, planets, initial_by_id, ang_vel)
        if target is None:
            continue
        arrivals_by_planet[target.id].append((eta, fleet.owner, int(fleet.ships)))
    return arrivals_by_planet


def resolve_arrival_event(owner, garrison, arrivals):
    # Match the environment's same-turn combat order: aggregate by owner, let
    # the top two attackers cancel, then resolve the survivor against garrison.
    by_owner = {}
    for _, attacker_owner, ships in arrivals:
        by_owner[attacker_owner] = by_owner.get(attacker_owner, 0) + ships

    if not by_owner:
        return owner, max(0.0, garrison)

    sorted_players = sorted(by_owner.items(), key=lambda item: item[1], reverse=True)
    top_owner, top_ships = sorted_players[0]

    if len(sorted_players) > 1:
        second_ships = sorted_players[1][1]
        if top_ships == second_ships:
            survivor_owner = -1
            survivor_ships = 0
        else:
            survivor_owner = top_owner
            survivor_ships = top_ships - second_ships
    else:
        survivor_owner = top_owner
        survivor_ships = top_ships

    if survivor_ships <= 0:
        return owner, max(0.0, garrison)

    if owner == survivor_owner:
        return owner, garrison + survivor_ships

    garrison -= survivor_ships
    if garrison < 0:
        return survivor_owner, -garrison
    return owner, garrison


def normalize_arrivals(arrivals, horizon):
    events = []
    for turns, owner, ships in arrivals:
        if ships <= 0:
            continue
        eta = max(1, int(math.ceil(turns)))
        if eta > horizon:
            continue
        events.append((eta, owner, int(ships)))
    events.sort(key=lambda item: item[0])
    return events


def simulate_planet_timeline(planet, arrivals, player, horizon):
    # Build one reusable future timeline so defense, capture, and evacuation
    # all query the same state model.
    horizon = max(0, int(math.ceil(horizon)))
    events = normalize_arrivals(arrivals, horizon)
    by_turn = defaultdict(list)
    for item in events:
        by_turn[item[0]].append(item)

    owner = planet.owner
    garrison = float(planet.ships)
    owner_at = {0: owner}
    ships_at = {0: max(0.0, garrison)}
    min_owned = garrison if owner == player else 0.0
    first_enemy = None
    fall_turn = None

    for turn in range(1, horizon + 1):
        if owner != -1:
            garrison += planet.production

        group = by_turn.get(turn, [])
        prev_owner = owner
        if group:
            if prev_owner == player and first_enemy is None:
                if any(item[1] not in (-1, player) for item in group):
                    first_enemy = turn
            owner, garrison = resolve_arrival_event(owner, garrison, group)
            if prev_owner == player and owner != player and fall_turn is None:
                fall_turn = turn

        owner_at[turn] = owner
        ships_at[turn] = max(0.0, garrison)
        if owner == player:
            min_owned = min(min_owned, garrison)

    keep_needed = 0
    holds_full = True

    if planet.owner == player:
        # Binary-search keep_needed: find the minimum initial garrison that
        # keeps the planet through the horizon. The analytical shortcut was
        # incorrect for multi-wave scenarios (resets between falls ignored
        # inter-wave production accumulation).
        def survives(initial_extra):
            s_owner = planet.owner
            s_garrison = float(initial_extra)
            for turn in range(1, horizon + 1):
                if s_owner != -1:
                    s_garrison += planet.production
                group = by_turn.get(turn, [])
                if group:
                    s_owner, s_garrison = resolve_arrival_event(s_owner, s_garrison, group)
                    if s_owner != player:
                        return False
            return True

        if not survives(planet.ships):
            holds_full = False
            keep_needed = int(planet.ships)
        elif survives(0):
            keep_needed = 0
        else:
            lo, hi = 0, int(planet.ships)
            while lo < hi:
                mid = (lo + hi) // 2
                if survives(mid):
                    hi = mid
                else:
                    lo = mid + 1
            keep_needed = lo
            holds_full = keep_needed <= int(planet.ships)

    return {
        "owner_at": owner_at,
        "ships_at": ships_at,
        "keep_needed": keep_needed,
        "min_owned": max(0, int(math.floor(min_owned))) if planet.owner == player else 0,
        "first_enemy": first_enemy,
        "fall_turn": fall_turn,
        "holds_full": holds_full,
        "horizon": horizon,
    }


def state_at_timeline(timeline, arrival_turn):
    turn = max(0, int(math.ceil(arrival_turn)))
    turn = min(turn, timeline["horizon"])
    owner = timeline["owner_at"].get(turn, timeline["owner_at"][timeline["horizon"]])
    ships = timeline["ships_at"].get(turn, timeline["ships_at"][timeline["horizon"]])
    return owner, max(0.0, ships)


def count_players(planets, fleets):
    owners = set()
    for planet in planets:
        if planet.owner != -1:
            owners.add(planet.owner)
    for fleet in fleets:
        owners.add(fleet.owner)
    return max(2, len(owners))


def nearest_distance_to_set(px, py, planets):
    if not planets:
        return 10**9
    return min(dist(px, py, planet.x, planet.y) for planet in planets)


def indirect_features(planet, planets, player):
    friendly = 0.0
    neutral = 0.0
    enemy = 0.0
    for other in planets:
        if other.id == planet.id:
            continue
        d = dist(planet.x, planet.y, other.x, other.y)
        if d < 1:
            continue
        factor = other.production / (d + 12.0)
        if other.owner == player:
            friendly += factor
        elif other.owner == -1:
            neutral += factor
        else:
            enemy += factor
    return friendly, neutral, enemy


class WorldModel:
    def __init__(self, player, step, planets, fleets, initial_by_id, ang_vel, comets, comet_ids):
        self.player = player
        self.step = step
        self.planets = planets
        self.fleets = fleets
        self.initial_by_id = initial_by_id
        self.ang_vel = ang_vel
        self.comets = comets
        self.comet_ids = set(comet_ids)

        self.planet_by_id = {planet.id: planet for planet in planets}
        self.my_planets = [planet for planet in planets if planet.owner == player]
        self.enemy_planets = [planet for planet in planets if planet.owner not in (-1, player)]
        self.neutral_planets = [planet for planet in planets if planet.owner == -1]
        self.static_neutral_planets = [
            planet for planet in self.neutral_planets if is_static_planet(planet)
        ]

        self.num_players = count_players(planets, fleets)
        self.remaining_steps = max(1, TOTAL_STEPS - step)
        self.is_early = step < EARLY_TURN_LIMIT
        self.is_opening = step < OPENING_TURN_LIMIT
        self.is_late = self.remaining_steps < LATE_REMAINING_TURNS
        self.is_very_late = self.remaining_steps < VERY_LATE_REMAINING_TURNS

        self.alive_players = set()
        for planet in planets:
            if planet.owner != -1:
                self.alive_players.add(planet.owner)
        self.num_active_players = max(2, len(self.alive_players))
        self.is_four_player = self.num_active_players >= 4
        self.is_three_player = self.num_active_players >= 3

        self.owner_strength = defaultdict(int)
        self.owner_production = defaultdict(int)
        for planet in planets:
            if planet.owner != -1:
                self.owner_strength[planet.owner] += int(planet.ships)
                self.owner_production[planet.owner] += int(planet.production)
        for fleet in fleets:
            self.owner_strength[fleet.owner] += int(fleet.ships)

        self.my_total = self.owner_strength.get(player, 0)
        self.enemy_total = sum(
            strength for owner, strength in self.owner_strength.items() if owner != player
        )
        self.max_enemy_strength = max(
            (strength for owner, strength in self.owner_strength.items() if owner != player),
            default=0,
        )
        self.my_prod = self.owner_production.get(player, 0)
        self.enemy_prod = sum(
            production
            for owner, production in self.owner_production.items()
            if owner != player
        )

        self.per_enemy_strength = {}
        for owner_id in self.owner_strength:
            if owner_id != player:
                self.per_enemy_strength[owner_id] = (
                    self.owner_strength[owner_id]
                    + self.owner_production.get(owner_id, 0) * 2
                )
        self.weak_enemies = set(
            oid
            for oid, strength in self.per_enemy_strength.items()
            if strength <= WEAK_ENEMY_THRESHOLD
        )
        self.strongest_enemy = max(
            self.per_enemy_strength.keys(),
            key=lambda oid: self.per_enemy_strength[oid],
            default=None,
        )

        self.arrivals_by_planet = build_arrival_ledger(fleets, planets, initial_by_id, ang_vel)
        self.base_timeline = {
            planet.id: simulate_planet_timeline(
                planet,
                self.arrivals_by_planet[planet.id],
                player,
                HORIZON,
            )
            for planet in planets
        }
        self.keep_needed_map = {
            planet.id: self.base_timeline[planet.id]["keep_needed"] for planet in planets
        }
        self.min_owned_map = {
            planet.id: self.base_timeline[planet.id]["min_owned"] for planet in planets
        }
        self.first_enemy_map = {
            planet.id: self.base_timeline[planet.id]["first_enemy"] for planet in planets
        }
        self.fall_turn_map = {
            planet.id: self.base_timeline[planet.id]["fall_turn"] for planet in planets
        }
        self.holds_full_map = {
            planet.id: self.base_timeline[planet.id]["holds_full"] for planet in planets
        }
        self.indirect_feature_map = {
            planet.id: indirect_features(planet, planets, player) for planet in planets
        }
        self.shot_cache = {}
        self.probe_candidate_cache = {}
        self.best_probe_cache = {}
        self.reaction_cache = {}
        self.exact_need_cache = {}

        self.total_visible_ships = sum(int(planet.ships) for planet in planets) + sum(
            int(fleet.ships) for fleet in fleets
        )
        self.total_production = sum(int(planet.production) for planet in planets)

    def is_static(self, planet_id):
        return is_static_planet(self.planet_by_id[planet_id])

    def comet_life(self, planet_id):
        return comet_remaining_life(planet_id, self.comets)

    def source_inventory_left(self, source_id, spent_total):
        return max(0, int(self.planet_by_id[source_id].ships) - spent_total[source_id])

    def plan_shot(self, src_id, target_id, ships):
        ships = int(ships)
        key = (src_id, target_id, ships)
        cached = self.shot_cache.get(key)
        if key in self.shot_cache:
            return cached
        src = self.planet_by_id[src_id]
        target = self.planet_by_id[target_id]
        result = aim_with_prediction(
            src,
            target,
            ships,
            self.initial_by_id,
            self.ang_vel,
            self.comets,
            self.comet_ids,
        )
        self.shot_cache[key] = result
        return result

    def probe_ship_candidates(self, src_id, target_id, source_cap, hints=()):
        cache = getattr(self, "probe_candidate_cache", None)
        if cache is None:
            cache = {}
            self.probe_candidate_cache = cache
        source_cap = max(1, int(source_cap))
        normalized_hints = tuple(
            int(math.ceil(hint))
            for hint in hints
            if hint is not None
        )
        cache_key = (src_id, target_id, source_cap, normalized_hints)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        target = self.planet_by_id[target_id]
        target_ships = max(1, int(math.ceil(target.ships)))

        values = set(range(1, min(6, source_cap) + 1))
        values.update(
            {
                source_cap,
                max(1, source_cap // 2),
                max(1, source_cap // 3),
                min(source_cap, PARTIAL_SOURCE_MIN_SHIPS),
                min(source_cap, target_ships + 1),
                min(source_cap, target_ships + 2),
                min(source_cap, target_ships + 4),
                min(source_cap, target_ships + 8),
            }
        )

        for hint in normalized_hints:
            base = max(1, min(source_cap, hint))
            for delta in (-2, -1, 0, 1, 2):
                candidate = base + delta
                if 1 <= candidate <= source_cap:
                    values.add(candidate)

        result = sorted(values)
        cache[cache_key] = result
        return result

    def best_probe_aim(
        self,
        src_id,
        target_id,
        source_cap,
        hints=(),
        min_turn=None,
        max_turn=None,
        anchor_turn=None,
        max_anchor_diff=None,
    ):
        cache_key = (
            src_id,
            target_id,
            max(1, int(source_cap)),
            tuple(hints),
            min_turn,
            max_turn,
            anchor_turn,
            max_anchor_diff,
        )
        cache = getattr(self, "best_probe_cache", None)
        if cache is None:
            cache = {}
            self.best_probe_cache = cache
        if cache_key in cache:
            return cache[cache_key]

        best = None
        best_key = None

        for ships in self.probe_ship_candidates(src_id, target_id, source_cap, hints=hints):
            aim = self.plan_shot(src_id, target_id, ships)
            if aim is None:
                continue

            angle, turns, dist_to_target, path_target = aim
            if min_turn is not None and turns < min_turn:
                continue
            if max_turn is not None and turns > max_turn:
                continue
            if (
                anchor_turn is not None
                and max_anchor_diff is not None
                and abs(turns - anchor_turn) > max_anchor_diff
            ):
                continue

            if anchor_turn is None:
                key = (turns, ships)
            else:
                key = (abs(turns - anchor_turn), turns, ships)

            if best_key is None or key < best_key:
                best_key = key
                best = (ships, (angle, turns, dist_to_target, path_target))

        cache[cache_key] = best
        return best

    def reaction_times(self, target_id):
        cached = self.reaction_cache.get(target_id)
        if cached is not None:
            return cached

        target = self.planet_by_id[target_id]
        my_t = 10**9
        for planet in self.my_planets:
            seeded = self.best_probe_aim(planet.id, target.id, max(1, int(planet.ships)))
            if seeded is None:
                continue
            _, aim = seeded
            my_t = min(my_t, aim[1])

        enemy_t = 10**9
        for planet in self.enemy_planets:
            seeded = self.best_probe_aim(planet.id, target.id, max(1, int(planet.ships)))
            if seeded is None:
                continue
            _, aim = seeded
            enemy_t = min(enemy_t, aim[1])

        cached = (my_t, enemy_t)
        self.reaction_cache[target_id] = cached
        return cached

    def projected_state(self, target_id, arrival_turn, planned_commitments=None, extra_arrivals=()):
        planned_commitments = planned_commitments or {}
        cutoff = max(1, int(math.ceil(arrival_turn)))
        if not planned_commitments.get(target_id) and not extra_arrivals:
            return state_at_timeline(self.base_timeline[target_id], cutoff)

        arrivals = [
            item
            for item in self.arrivals_by_planet.get(target_id, [])
            if item[0] <= cutoff
        ]
        arrivals.extend(
            item
            for item in planned_commitments.get(target_id, [])
            if item[0] <= cutoff
        )
        arrivals.extend(item for item in extra_arrivals if item[0] <= cutoff)

        target = self.planet_by_id[target_id]
        dyn = simulate_planet_timeline(target, arrivals, self.player, cutoff)
        return state_at_timeline(dyn, cutoff)

    def projected_timeline(self, target_id, horizon, planned_commitments=None, extra_arrivals=()):
        planned_commitments = planned_commitments or {}
        horizon = max(1, int(math.ceil(horizon)))
        arrivals = [
            item for item in self.arrivals_by_planet.get(target_id, []) if item[0] <= horizon
        ]
        arrivals.extend(
            item for item in planned_commitments.get(target_id, []) if item[0] <= horizon
        )
        arrivals.extend(item for item in extra_arrivals if item[0] <= horizon)
        target = self.planet_by_id[target_id]
        return simulate_planet_timeline(target, arrivals, self.player, horizon)

    def hold_status(self, target_id, planned_commitments=None, horizon=HORIZON):
        planned_commitments = planned_commitments or {}
        if planned_commitments.get(target_id):
            tl = self.projected_timeline(
                target_id,
                horizon,
                planned_commitments=planned_commitments,
            )
        else:
            tl = self.base_timeline[target_id]
        return {
            "keep_needed": tl["keep_needed"],
            "min_owned": tl["min_owned"],
            "first_enemy": tl["first_enemy"],
            "fall_turn": tl["fall_turn"],
            "holds_full": tl["holds_full"],
        }

    def _ownership_search_cap(self, eval_turn):
        productive_cap = self.total_production * max(2, eval_turn + 2)
        return max(32, int(self.total_visible_ships + productive_cap + 32))

    def min_ships_to_own_by(
        self,
        target_id,
        eval_turn,
        attacker_owner,
        arrival_turn=None,
        planned_commitments=None,
        extra_arrivals=(),
        upper_bound=None,
    ):
        planned_commitments = planned_commitments or {}
        eval_turn = max(1, int(math.ceil(eval_turn)))
        arrival_turn = eval_turn if arrival_turn is None else max(1, int(math.ceil(arrival_turn)))
        if arrival_turn > eval_turn:
            if upper_bound is not None:
                return max(1, int(upper_bound)) + 1
            return self._ownership_search_cap(eval_turn) + 1

        normalized_extra = tuple(
            (
                max(1, int(math.ceil(turns))),
                owner,
                int(ships),
            )
            for turns, owner, ships in extra_arrivals
            if ships > 0 and max(1, int(math.ceil(turns))) <= eval_turn
        )

        cache_key = None
        if (
            arrival_turn == eval_turn
            and not planned_commitments.get(target_id)
            and not normalized_extra
        ):
            cache_key = (target_id, eval_turn, attacker_owner)
            cached = self.exact_need_cache.get(cache_key)
            if cached is not None:
                return cached

        owner_before, ships_before = self.projected_state(
            target_id,
            eval_turn,
            planned_commitments=planned_commitments,
            extra_arrivals=normalized_extra,
        )
        if owner_before == attacker_owner:
            if cache_key is not None:
                self.exact_need_cache[cache_key] = 0
            return 0

        def owns_at(ships):
            owner_after, _ = self.projected_state(
                target_id,
                eval_turn,
                planned_commitments=planned_commitments,
                extra_arrivals=normalized_extra + ((arrival_turn, attacker_owner, int(ships)),),
            )
            return owner_after == attacker_owner

        if upper_bound is not None:
            hi = max(1, int(upper_bound))
            if not owns_at(hi):
                return hi + 1
        else:
            hi = max(1, int(math.ceil(ships_before)) + 1)
            search_cap = self._ownership_search_cap(eval_turn)
            while hi <= search_cap and not owns_at(hi):
                hi *= 2
            if hi > search_cap:
                hi = search_cap
                if not owns_at(hi):
                    return hi + 1

        lo = 1
        while lo < hi:
            mid = (lo + hi) // 2
            if owns_at(mid):
                hi = mid
            else:
                lo = mid + 1

        if cache_key is not None:
            self.exact_need_cache[cache_key] = lo
        return lo

    def min_ships_to_own_at(
        self,
        target_id,
        arrival_turn,
        attacker_owner,
        planned_commitments=None,
        extra_arrivals=(),
        upper_bound=None,
    ):
        return self.min_ships_to_own_by(
            target_id,
            arrival_turn,
            attacker_owner,
            arrival_turn=arrival_turn,
            planned_commitments=planned_commitments,
            extra_arrivals=extra_arrivals,
            upper_bound=upper_bound,
        )

    def reinforcement_needed_to_hold_until(
        self,
        planet_id,
        arrival_turn,
        hold_until,
        planned_commitments=None,
        upper_bound=None,
    ):
        planned_commitments = planned_commitments or {}
        target = self.planet_by_id[planet_id]
        arrival_turn = max(1, int(math.ceil(arrival_turn)))
        hold_until = max(arrival_turn, int(math.ceil(hold_until)))

        if target.owner != self.player:
            return self.min_ships_to_own_by(
                planet_id,
                hold_until,
                self.player,
                arrival_turn=arrival_turn,
                planned_commitments=planned_commitments,
                upper_bound=upper_bound,
            )

        def holds_with_reinforcement(ships):
            timeline = self.projected_timeline(
                planet_id,
                hold_until,
                planned_commitments=planned_commitments,
                extra_arrivals=((arrival_turn, self.player, int(ships)),),
            )
            for turn in range(arrival_turn, hold_until + 1):
                if timeline["owner_at"].get(turn) != self.player:
                    return False
            return True

        if upper_bound is not None:
            hi = max(1, int(upper_bound))
            if not holds_with_reinforcement(hi):
                return hi + 1
        else:
            hi = 1
            search_cap = self._ownership_search_cap(hold_until)
            while hi <= search_cap and not holds_with_reinforcement(hi):
                hi *= 2
            if hi > search_cap:
                hi = search_cap
                if not holds_with_reinforcement(hi):
                    return hi + 1

        lo = 1
        while lo < hi:
            mid = (lo + hi) // 2
            if holds_with_reinforcement(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def ships_needed_to_capture(
        self,
        target_id,
        arrival_turn,
        planned_commitments=None,
        extra_arrivals=(),
    ):
        return self.min_ships_to_own_at(
            target_id,
            arrival_turn,
            self.player,
            planned_commitments=planned_commitments,
            extra_arrivals=extra_arrivals,
        )


# ============================================================
# Strategy
# ============================================================

def planet_distance(first, second):
    return math.hypot(first.x - second.x, first.y - second.y)


def nearest_sources_to_target(target, sources, top_k):
    if top_k <= 0 or len(sources) <= top_k:
        return sources
    return sorted(
        sources,
        key=lambda src: (planet_distance(src, target), -int(src.ships), src.id),
    )[:top_k]


def min_legal_reaction_time(target, sources, world):
    best = 10**9
    for src in sources:
        seeded = world.best_probe_aim(src.id, target.id, max(1, int(src.ships)))
        if seeded is None:
            continue
        _, aim = seeded
        best = min(best, aim[1])
    return best


def policy_reaction_times(target_id, policy):
    return policy["reaction_time_map"].get(target_id, (10**9, 10**9))


def candidate_time_valid(target, turns, world, remaining_buffer):
    if turns > world.remaining_steps - remaining_buffer:
        return False
    if target.id in world.comet_ids:
        life = world.comet_life(target.id)
        if turns >= life or turns > COMET_MAX_CHASE_TURNS:
            return False
    return True


def stacked_enemy_proactive_keep(planet, world):
    threats = []
    for enemy in world.enemy_planets:
        seeded = world.best_probe_aim(
            enemy.id,
            planet.id,
            max(1, int(enemy.ships)),
        )
        if seeded is None:
            continue
        _, aim = seeded
        eta = aim[1]
        if eta > MULTI_ENEMY_PROACTIVE_HORIZON:
            continue
        threats.append((eta, int(enemy.ships)))

    if not threats:
        return 0

    threats.sort()
    best_stacked = 0
    left = 0
    running = 0
    for right in range(len(threats)):
        running += threats[right][1]
        while threats[right][0] - threats[left][0] > MULTI_ENEMY_STACK_WINDOW:
            running -= threats[left][1]
            left += 1
        best_stacked = max(best_stacked, running)

    return int(best_stacked * MULTI_ENEMY_PROACTIVE_RATIO)


def swarm_eta_tolerance(options, target, world):
    if len(options) >= 3:
        return THREE_SOURCE_ETA_TOLERANCE
    if target.owner not in (-1, world.player):
        return HOSTILE_SWARM_ETA_TOLERANCE
    return MULTI_SOURCE_ETA_TOLERANCE


def detect_enemy_crashes(world):
    crashes = []
    for target_id, arrivals in world.arrivals_by_planet.items():
        enemy_events = [
            (int(math.ceil(eta)), owner, int(ships))
            for eta, owner, ships in arrivals
            if owner not in (-1, world.player) and ships > 0
        ]
        enemy_events.sort()
        for i in range(len(enemy_events)):
            eta_a, owner_a, ships_a = enemy_events[i]
            for j in range(i + 1, len(enemy_events)):
                eta_b, owner_b, ships_b = enemy_events[j]
                if owner_a == owner_b:
                    continue
                if abs(eta_a - eta_b) > CRASH_EXPLOIT_ETA_WINDOW:
                    break
                if ships_a + ships_b < CRASH_EXPLOIT_MIN_TOTAL_SHIPS:
                    continue
                crashes.append(
                    {
                        "target_id": target_id,
                        "crash_turn": max(eta_a, eta_b),
                        "owners": (owner_a, owner_b),
                        "ships": (ships_a, ships_b),
                    }
                )
    return crashes


def build_policy_state(world, deadline=None):
    def expired():
        return deadline is not None and time.perf_counter() > deadline

    indirect_wealth_map = {}
    for target_id, features in world.indirect_feature_map.items():
        friendly, neutral, enemy = features
        indirect_wealth_map[target_id] = (
            friendly * INDIRECT_FRIENDLY_WEIGHT
            + neutral * INDIRECT_NEUTRAL_WEIGHT
            + enemy * INDIRECT_ENEMY_WEIGHT
        )

    reserve = {}
    attack_budget = {}
    reaction_time_map = {}

    for target in world.planets:
        if expired():
            break
        if target.owner == world.player:
            continue
        my_sources = nearest_sources_to_target(target, world.my_planets, REACTION_SOURCE_TOP_K_MY)
        enemy_sources = nearest_sources_to_target(target, world.enemy_planets, REACTION_SOURCE_TOP_K_ENEMY)
        my_t = min_legal_reaction_time(target, my_sources, world)
        enemy_t = min_legal_reaction_time(target, enemy_sources, world)
        reaction_time_map[target.id] = (my_t, enemy_t)

    for planet in world.my_planets:
        if expired():
            break
        exact_keep = world.keep_needed_map.get(planet.id, 0)

        proactive_keep = 0
        for enemy in nearest_sources_to_target(planet, world.enemy_planets, PROACTIVE_ENEMY_TOP_K):
            enemy_aim = world.plan_shot(enemy.id, planet.id, max(1, int(enemy.ships)))
            if enemy_aim is None:
                continue
            enemy_eta = enemy_aim[1]
            if enemy_eta > PROACTIVE_DEFENSE_HORIZON:
                continue
            # Credit the ships our planet will produce before the threat arrives:
            # a threat arriving in 10 turns against a planet producing 3/turn is
            # effectively 30 ships weaker from our perspective.
            prod_credit = planet.production * enemy_eta * PROACTIVE_DEFENSE_PROD_CREDIT
            threat_adjusted = max(0, enemy.ships - prod_credit)
            proactive_keep = max(
                proactive_keep,
                int(threat_adjusted * PROACTIVE_DEFENSE_RATIO),
            )
        proactive_keep = max(proactive_keep, stacked_enemy_proactive_keep(planet, world))

        reserve[planet.id] = min(int(planet.ships), max(exact_keep, proactive_keep))
        attack_budget[planet.id] = max(0, int(planet.ships) - reserve[planet.id])

    return {
        "indirect_wealth_map": indirect_wealth_map,
        "reserve": reserve,
        "attack_budget": attack_budget,
        "reaction_time_map": reaction_time_map,
    }


def build_modes(world):
    if world.num_active_players >= 3:
        effective_enemy = world.max_enemy_strength
    else:
        effective_enemy = world.enemy_total
    domination = (world.my_total - effective_enemy) / max(1, world.my_total + effective_enemy)
    is_behind = domination < BEHIND_DOMINATION
    is_ahead = domination > AHEAD_DOMINATION
    is_dominating = is_ahead or (
        world.max_enemy_strength > 0 and world.my_total > world.max_enemy_strength * 1.25
    )
    is_finishing = (
        domination > FINISHING_DOMINATION
        and world.my_prod > world.enemy_prod * FINISHING_PROD_RATIO
        and world.step > 100
    )
    target_leader = (
        world.num_active_players >= 3
        and not is_dominating
        and world.strongest_enemy is not None
        and world.my_total < world.per_enemy_strength.get(world.strongest_enemy, 0) * 1.1
    )

    attack_margin_mult = 1.0
    if is_ahead:
        attack_margin_mult += AHEAD_ATTACK_MARGIN_BONUS
    if is_behind:
        attack_margin_mult -= BEHIND_ATTACK_MARGIN_PENALTY
    if is_finishing:
        attack_margin_mult += FINISHING_ATTACK_MARGIN_BONUS

    return {
        "domination": domination,
        "is_behind": is_behind,
        "is_ahead": is_ahead,
        "is_dominating": is_dominating,
        "is_finishing": is_finishing,
        "attack_margin_mult": attack_margin_mult,
        "target_leader": target_leader,
    }


def is_safe_neutral(target, policy):
    if target.owner != -1:
        return False
    my_t, enemy_t = policy_reaction_times(target.id, policy)
    return my_t <= enemy_t - SAFE_NEUTRAL_MARGIN


def is_contested_neutral(target, policy):
    if target.owner != -1:
        return False
    my_t, enemy_t = policy_reaction_times(target.id, policy)
    return abs(my_t - enemy_t) <= CONTESTED_NEUTRAL_MARGIN


def opening_filter(target, arrival_turns, needed, src_available, world, policy):
    if not world.is_opening or target.owner != -1:
        return False
    if target.id in world.comet_ids:
        return False
    if world.is_static(target.id):
        # Close statics are always allowed; far statics need a strong reaction advantage.
        my_t, enemy_t = policy_reaction_times(target.id, policy)
        reaction_gap = enemy_t - my_t
        if arrival_turns <= OPENING_STATIC_MAX_DIRECT_TURNS:
            return False  # nearby — always allow
        if reaction_gap >= OPENING_STATIC_MIN_REACTION_GAP:
            return False  # strong advantage even if far — allow
        return True  # distant with weak advantage → block

    my_t, enemy_t = policy_reaction_times(target.id, policy)
    reaction_gap = enemy_t - my_t
    if (
        target.production >= SAFE_OPENING_PROD_THRESHOLD
        and arrival_turns <= SAFE_OPENING_TURN_LIMIT
        and reaction_gap >= SAFE_NEUTRAL_MARGIN
    ):
        return False

    if world.is_four_player:
        affordable = needed <= max(
            PARTIAL_SOURCE_MIN_SHIPS,
            int(src_available * FOUR_PLAYER_ROTATING_SEND_RATIO),
        )
        if (
            affordable
            and arrival_turns <= FOUR_PLAYER_ROTATING_TURN_LIMIT
            and reaction_gap >= FOUR_PLAYER_ROTATING_REACTION_GAP
        ):
            return False
        return True

    return arrival_turns > ROTATING_OPENING_MAX_TURNS or target.production <= ROTATING_OPENING_LOW_PROD


def target_value(target, arrival_turns, mission, world, modes, policy):
    turns_profit = max(1, world.remaining_steps - arrival_turns)
    if target.id in world.comet_ids:
        life = world.comet_life(target.id)
        turns_profit = max(0, min(turns_profit, life - arrival_turns))
        if turns_profit <= 0:
            return -1.0
    else:
        # Later captures are worth proportionally less: a planet grabbed in the last
        # 10% of the game contributes far less than one captured early.
        time_discount = 1.0 - (arrival_turns / max(1, world.remaining_steps)) * SCORING_TIME_DISCOUNT
        turns_profit = max(0.5, turns_profit * time_discount)

    value = target.production * turns_profit
    value += policy["indirect_wealth_map"][target.id] * turns_profit * INDIRECT_VALUE_SCALE
    # Bonus for high production-per-unit-radius: more ships produced per area defended.
    prod_density = target.production / max(1.0, target.radius)
    value += prod_density * PROD_DENSITY_WEIGHT * turns_profit

    if world.is_static(target.id):
        value *= STATIC_NEUTRAL_VALUE_MULT if target.owner == -1 else STATIC_HOSTILE_VALUE_MULT
    else:
        value *= ROTATING_OPENING_VALUE_MULT if world.is_opening else 1.0

    if target.owner not in (-1, world.player):
        value *= OPENING_HOSTILE_TARGET_VALUE_MULT if world.is_opening else HOSTILE_TARGET_VALUE_MULT

    if target.owner == -1:
        if is_safe_neutral(target, policy):
            value *= SAFE_NEUTRAL_VALUE_MULT
        elif is_contested_neutral(target, policy):
            value *= CONTESTED_NEUTRAL_VALUE_MULT
        if world.is_early:
            value *= EARLY_NEUTRAL_VALUE_MULT

    if target.id in world.comet_ids:
        enemy_ps = [p for p in world.planets if p.owner not in (-1, world.player)]
        value *= COMET_VALUE_MULT * comet_slingshot_mult(target.id, world.comets, enemy_ps)

    if mission == "snipe":
        value *= SNIPE_VALUE_MULT
    elif mission == "swarm":
        value *= SWARM_VALUE_MULT
    elif mission == "reinforce":
        value *= REINFORCE_VALUE_MULT
    elif mission == "crash_exploit":
        value *= CRASH_EXPLOIT_VALUE_MULT
    elif mission == "slingshot":
        value *= SLINGSHOT_VALUE_MULT

    if target.owner not in (-1, world.player):
        enemy_strength = world.owner_strength.get(target.owner, 0)
        if enemy_strength <= WEAK_ENEMY_THRESHOLD:
            value += ELIMINATION_BONUS
            if world.is_late:
                value += ELIMINATION_BONUS * 0.5
    if world.is_late:
        value += max(0, target.ships) * LATE_IMMEDIATE_SHIP_VALUE

    if modes.get("target_leader") and target.owner == world.strongest_enemy:
        value *= HOSTILE_TARGET_VALUE_MULT * 1.08
    if modes["is_finishing"] and target.owner not in (-1, world.player):
        value *= FINISHING_HOSTILE_VALUE_MULT
    if modes["is_behind"] and target.owner == -1 and not world.is_static(target.id):
        value *= BEHIND_ROTATING_NEUTRAL_VALUE_MULT
    if modes["is_behind"] and target.owner == -1 and is_safe_neutral(target, policy):
        value *= 1.08
    if modes["is_dominating"] and target.owner == -1 and is_contested_neutral(target, policy):
        value *= 0.92

    return value


def reinforce_value(target, hold_until, world, policy):
    saved_turns = max(1, world.remaining_steps - hold_until)
    value = target.production * saved_turns + max(0, target.ships) * DEFENSE_SHIP_VALUE
    if world.enemy_planets and nearest_distance_to_set(target.x, target.y, world.enemy_planets) < 22:
        value *= DEFENSE_FRONTIER_SCORE_MULT
    value += policy["indirect_wealth_map"][target.id] * saved_turns * INDIRECT_VALUE_SCALE * 0.35
    return value * REINFORCE_VALUE_MULT


def preferred_send(target, base_needed, arrival_turns, src_available, world, modes, policy):
    send = max(base_needed, int(math.ceil(base_needed * modes["attack_margin_mult"])))
    margin = 0
    if target.owner == -1:
        margin += min(
            NEUTRAL_MARGIN_CAP,
            NEUTRAL_MARGIN_BASE + target.production * NEUTRAL_MARGIN_PROD_WEIGHT,
        )
    else:
        margin += min(
            HOSTILE_MARGIN_CAP,
            HOSTILE_MARGIN_BASE + target.production * HOSTILE_MARGIN_PROD_WEIGHT,
        )
    if world.is_static(target.id):
        margin += STATIC_TARGET_MARGIN
    if is_contested_neutral(target, policy):
        margin += CONTESTED_TARGET_MARGIN
    if world.is_four_player:
        margin += FOUR_PLAYER_TARGET_MARGIN
    if arrival_turns > LONG_TRAVEL_MARGIN_START:
        margin += min(LONG_TRAVEL_MARGIN_CAP, arrival_turns // LONG_TRAVEL_MARGIN_DIVISOR)
    if target.id in world.comet_ids:
        margin = max(0, margin - COMET_MARGIN_RELIEF)
    if modes["is_finishing"] and target.owner not in (-1, world.player):
        margin += FINISHING_HOSTILE_SEND_BONUS
    if target.owner not in (-1, world.player) and target.owner in world.weak_enemies:
        margin = max(0, margin - 3)
    return min(src_available, send + margin)


def apply_score_modifiers(base_score, target, mission, world):
    score = base_score
    if world.is_static(target.id):
        score *= STATIC_TARGET_SCORE_MULT
    if world.is_early and target.owner == -1 and world.is_static(target.id):
        score *= EARLY_STATIC_NEUTRAL_SCORE_MULT
    if world.is_four_player and target.owner == -1 and not world.is_static(target.id):
        score *= FOUR_PLAYER_ROTATING_NEUTRAL_SCORE_MULT
    if (
        len(world.static_neutral_planets) >= DENSE_STATIC_NEUTRAL_COUNT
        and target.owner == -1
        and not world.is_static(target.id)
    ):
        score *= DENSE_ROTATING_NEUTRAL_SCORE_MULT
    if mission == "snipe":
        score *= SNIPE_SCORE_MULT
    elif mission == "swarm":
        score *= SWARM_SCORE_MULT
    elif mission == "crash_exploit":
        score *= CRASH_EXPLOIT_SCORE_MULT
    elif mission == "slingshot":
        score *= SLINGSHOT_SCORE_MULT
    return score


def settle_plan(
    src,
    target,
    src_cap,
    send_guess,
    world,
    planned_commitments,
    modes,
    policy,
    mission="capture",
    eval_turn_fn=None,
    anchor_turn=None,
    anchor_tolerance=None,
    max_iter=4,
):
    if src_cap < 1:
        return None

    seed_hint = max(1, min(src_cap, int(send_guess)))
    eval_turn_fn = eval_turn_fn or (lambda turns: turns)
    anchor_tolerance = (
        anchor_tolerance
        if anchor_tolerance is not None
        else (1 if mission == "snipe" else None)
    )
    tested = {}
    tested_order = []

    def evaluate(send):
        send = max(1, min(src_cap, int(send)))
        cached = tested.get(send)
        if cached is not None or send in tested:
            return cached

        aim = world.plan_shot(src.id, target.id, send)
        if aim is None:
            tested[send] = None
            return None

        angle, turns, _, _ = aim
        if mission == "crash_exploit" and anchor_turn is not None and turns < anchor_turn:
            tested[send] = None
            return None
        raw_eval_turn = int(math.ceil(eval_turn_fn(turns)))
        if raw_eval_turn < turns:
            tested[send] = None
            return None
        eval_turn = raw_eval_turn
        need = world.min_ships_to_own_by(
            target.id,
            eval_turn,
            world.player,
            arrival_turn=turns,
            planned_commitments=planned_commitments,
            upper_bound=src_cap,
        )
        if need <= 0 or need > src_cap:
            tested[send] = None
            return None

        if mission in ("snipe", "crash_exploit"):
            desired = need
        elif mission == "rescue":
            desired = min(
                src_cap,
                max(
                    need,
                    need + DEFENSE_SEND_MARGIN_BASE + target.production * DEFENSE_SEND_MARGIN_PROD_WEIGHT,
                ),
            )
        else:
            desired = min(
                src_cap,
                max(need, preferred_send(target, need, turns, src_cap, world, modes, policy)),
            )

        result = (angle, turns, eval_turn, need, send, desired)
        tested[send] = result
        tested_order.append(send)
        return result

    initial_candidates = sorted(
        world.probe_ship_candidates(
            src.id,
            target.id,
            src_cap,
            hints=(seed_hint,),
        ),
        key=lambda send: (abs(send - seed_hint), send),
    )

    current_send = None
    for seed in initial_candidates:
        result = evaluate(seed)
        if result is None:
            continue
        if (
            anchor_turn is not None
            and anchor_tolerance is not None
            and abs(result[1] - anchor_turn) > anchor_tolerance
        ):
            continue
        current_send = seed
        break

    if current_send is None:
        return None

    for _ in range(max_iter):
        result = evaluate(current_send)
        if result is None:
            break

        angle, turns, eval_turn, need, actual_send, desired = result
        if desired == actual_send:
            if (
                anchor_turn is not None
                and anchor_tolerance is not None
                and abs(turns - anchor_turn) > anchor_tolerance
            ):
                return None
            if mission == "rescue" and turns > eval_turn:
                return None
            return angle, turns, eval_turn, need, actual_send

        next_send = max(1, min(src_cap, int(desired)))
        if next_send in tested:
            current_send = next_send
            break
        current_send = next_send

    candidate_sends = sorted(
        [send for send in tested_order if tested.get(send) is not None],
        key=lambda send: (
            0
            if mission != "snipe" or anchor_turn is None
            else abs(tested[send][1] - anchor_turn),
            abs(send - seed_hint),
            tested[send][1],
            send,
        ),
    )

    seen = set()
    for send in candidate_sends:
        if send in seen:
            continue
        seen.add(send)
        result = tested.get(send)
        if result is None:
            continue
        angle, turns, eval_turn, need, actual_send, _ = result
        if actual_send < need:
            continue
        if (
            anchor_turn is not None
            and anchor_tolerance is not None
            and abs(turns - anchor_turn) > anchor_tolerance
        ):
            continue
        if mission == "rescue" and turns > eval_turn:
            continue
        return angle, turns, eval_turn, need, actual_send

    return None


def settle_reinforce_plan(
    src,
    target,
    src_cap,
    send_guess,
    world,
    planned_commitments,
    hold_until,
    max_arrival_turn,
    max_iter=4,
):
    if src_cap < 1:
        return None

    seed_hint = max(1, min(src_cap, int(send_guess)))
    tested = {}
    tested_order = []

    def evaluate(send):
        send = max(1, min(src_cap, int(send)))
        cached = tested.get(send)
        if cached is not None or send in tested:
            return cached

        aim = world.plan_shot(src.id, target.id, send)
        if aim is None:
            tested[send] = None
            return None

        angle, turns, _, _ = aim
        if turns > max_arrival_turn:
            tested[send] = None
            return None

        need = world.reinforcement_needed_to_hold_until(
            target.id,
            turns,
            hold_until,
            planned_commitments=planned_commitments,
            upper_bound=src_cap,
        )
        if need <= 0 or need > src_cap:
            tested[send] = None
            return None

        desired = min(src_cap, need + REINFORCE_SAFETY_MARGIN)
        result = (angle, turns, hold_until, need, send, desired)
        tested[send] = result
        tested_order.append(send)
        return result

    initial_candidates = sorted(
        world.probe_ship_candidates(
            src.id,
            target.id,
            src_cap,
            hints=(seed_hint,),
        ),
        key=lambda send: (abs(send - seed_hint), send),
    )

    current_send = None
    for seed in initial_candidates:
        result = evaluate(seed)
        if result is None:
            continue
        current_send = seed
        break

    if current_send is None:
        return None

    for _ in range(max_iter):
        result = evaluate(current_send)
        if result is None:
            break

        angle, turns, eval_turn, need, actual_send, desired = result
        if desired == actual_send:
            return angle, turns, eval_turn, need, actual_send

        next_send = max(1, min(src_cap, int(desired)))
        if next_send in tested:
            current_send = next_send
            break
        current_send = next_send

    candidate_sends = sorted(
        [send for send in tested_order if tested.get(send) is not None],
        key=lambda send: (abs(send - seed_hint), tested[send][1], send),
    )
    for send in candidate_sends:
        result = tested.get(send)
        if result is None:
            continue
        angle, turns, eval_turn, need, actual_send, _ = result
        if actual_send < need or turns > max_arrival_turn:
            continue
        return angle, turns, eval_turn, need, actual_send

    return None


def build_snipe_mission(src, target, src_available, world, planned_commitments, modes, policy):
    if target.owner != -1:
        return None

    enemy_etas = sorted(
        {
            int(math.ceil(eta))
            for eta, owner, ships in world.arrivals_by_planet.get(target.id, [])
            if owner not in (-1, world.player) and ships > 0
        }
    )
    if not enemy_etas:
        return None

    best = None
    for enemy_eta in enemy_etas[:3]:
        seeded = world.best_probe_aim(
            src.id,
            target.id,
            src_available,
            hints=(int(target.ships) + 1, int(target.ships) + 8),
            anchor_turn=enemy_eta,
            max_anchor_diff=1,
        )
        if seeded is None:
            continue

        probe, rough = seeded
        sync_turn = max(rough[1], enemy_eta)
        if target.id in world.comet_ids:
            life = world.comet_life(target.id)
            if sync_turn >= life or sync_turn > COMET_MAX_CHASE_TURNS:
                continue

        plan = settle_plan(
            src,
            target,
            src_available,
            probe,
            world,
            planned_commitments,
            modes,
            policy,
            mission="snipe",
            eval_turn_fn=lambda turns, enemy_eta=enemy_eta: max(turns, enemy_eta),
            anchor_turn=enemy_eta,
        )
        if plan is None:
            continue

        angle, turns, sync_turn, need, send_pref = plan
        if target.id in world.comet_ids:
            life = world.comet_life(target.id)
            if sync_turn >= life or sync_turn > COMET_MAX_CHASE_TURNS:
                continue

        value = target_value(target, sync_turn, "snipe", world, modes, policy)
        if value <= 0:
            continue

        score = apply_score_modifiers(
            value / (send_pref + sync_turn * SNIPE_COST_TURN_WEIGHT + 1.0),
            target,
            "snipe",
            world,
        )
        option = ShotOption(
            score=score,
            src_id=src.id,
            target_id=target.id,
            angle=angle,
            turns=turns,
            needed=need,
            send_cap=send_pref,
            mission="snipe",
            anchor_turn=enemy_eta,
        )
        mission_obj = Mission(
            kind="snipe",
            score=score,
            target_id=target.id,
            turns=sync_turn,
            options=[option],
        )
        if best is None or mission_obj.score > best.score:
            best = mission_obj

    return best


def build_rescue_missions(world, policy, planned_commitments, modes):
    missions = []

    for target in world.my_planets:
        fall_turn = world.fall_turn_map.get(target.id)
        if fall_turn is None or fall_turn > DEFENSE_LOOKAHEAD_TURNS:
            continue

        for src in world.my_planets:
            if src.id == target.id:
                continue

            src_available = policy["attack_budget"].get(src.id, 0)
            if src_available < PARTIAL_SOURCE_MIN_SHIPS:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                src_available,
                hints=(target.production + DEFENSE_SEND_MARGIN_BASE + 2,),
                max_turn=fall_turn,
            )
            if seeded is None:
                continue
            probe, probe_aim = seeded
            plan = settle_plan(
                src,
                target,
                src_available,
                probe,
                world,
                planned_commitments,
                modes,
                policy,
                mission="rescue",
                eval_turn_fn=lambda _turns, fall_turn=fall_turn: fall_turn,
                anchor_turn=fall_turn,
            )
            if plan is None:
                continue

            angle, turns, _, need, send_pref = plan
            saved_turns = max(1, world.remaining_steps - fall_turn)
            value = target.production * saved_turns + max(0, target.ships) * DEFENSE_SHIP_VALUE
            if world.enemy_planets and nearest_distance_to_set(target.x, target.y, world.enemy_planets) < 22:
                value *= DEFENSE_FRONTIER_SCORE_MULT
            score = value / (send_pref + turns * DEFENSE_COST_TURN_WEIGHT + 1.0)

            option = ShotOption(
                score=score,
                src_id=src.id,
                target_id=target.id,
                angle=angle,
                turns=turns,
                needed=need,
                send_cap=send_pref,
                mission="rescue",
                anchor_turn=fall_turn,
            )
            missions.append(
                Mission(
                    kind="rescue",
                    score=score,
                    target_id=target.id,
                    turns=fall_turn,
                    options=[option],
                )
            )

    return missions


def build_recapture_missions(world, policy, planned_commitments, modes):
    missions = []

    for target in world.my_planets:
        fall_turn = world.fall_turn_map.get(target.id)
        if fall_turn is None or fall_turn > DEFENSE_LOOKAHEAD_TURNS:
            continue

        for src in world.my_planets:
            if src.id == target.id:
                continue

            src_available = policy["attack_budget"].get(src.id, 0)
            if src_available < PARTIAL_SOURCE_MIN_SHIPS:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                src_available,
                hints=(target.production + DEFENSE_SEND_MARGIN_BASE + 2,),
                min_turn=fall_turn + 1,
                max_turn=fall_turn + RECAPTURE_LOOKAHEAD_TURNS,
            )
            if seeded is None:
                continue
            probe, probe_aim = seeded
            probe_turns = probe_aim[1]

            plan = settle_plan(
                src,
                target,
                src_available,
                probe,
                world,
                planned_commitments,
                modes,
                policy,
                mission="capture",
            )
            if plan is None:
                continue

            angle, turns, _, need, send_pref = plan
            if turns <= fall_turn or turns - fall_turn > RECAPTURE_LOOKAHEAD_TURNS:
                continue

            saved_turns = max(1, world.remaining_steps - turns)
            value = (
                RECAPTURE_PRODUCTION_WEIGHT * target.production * saved_turns
                + RECAPTURE_IMMEDIATE_WEIGHT * max(0, target.ships)
            )
            if world.enemy_planets and nearest_distance_to_set(target.x, target.y, world.enemy_planets) < 22:
                value *= RECAPTURE_FRONTIER_MULT
            value *= RECAPTURE_VALUE_MULT
            score = value / (send_pref + turns * RECAPTURE_COST_TURN_WEIGHT + 1.0)

            option = ShotOption(
                score=score,
                src_id=src.id,
                target_id=target.id,
                angle=angle,
                turns=turns,
                needed=need,
                send_cap=send_pref,
                mission="recapture",
                anchor_turn=fall_turn,
            )
            missions.append(
                Mission(
                    kind="recapture",
                    score=score,
                    target_id=target.id,
                    turns=turns,
                    options=[option],
                )
            )

    return missions


def build_reinforce_missions(world, policy, planned_commitments, modes, inventory_left_fn):
    if not REINFORCE_ENABLED:
        return []

    missions = []
    if world.remaining_steps < REINFORCE_MIN_FUTURE_TURNS:
        return missions

    for target in world.my_planets:
        fall_turn = world.fall_turn_map.get(target.id)
        if fall_turn is None:
            continue
        if target.production < REINFORCE_MIN_PRODUCTION:
            continue

        hold_until = min(HORIZON, fall_turn + REINFORCE_HOLD_LOOKAHEAD)
        max_arrival_turn = min(fall_turn, REINFORCE_MAX_TRAVEL_TURNS)

        for src in world.my_planets:
            if src.id == target.id:
                continue

            budget = inventory_left_fn(src.id)
            source_cap = min(budget, int(src.ships * REINFORCE_MAX_SOURCE_FRACTION))
            if source_cap < PARTIAL_SOURCE_MIN_SHIPS:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                source_cap,
                hints=(target.production + REINFORCE_SAFETY_MARGIN + 2,),
                max_turn=max_arrival_turn,
            )
            if seeded is None:
                continue
            probe, _ = seeded

            plan = settle_reinforce_plan(
                src,
                target,
                source_cap,
                probe,
                world,
                planned_commitments,
                hold_until,
                max_arrival_turn,
            )
            if plan is None:
                continue

            angle, turns, _, need, send_pref = plan
            value = reinforce_value(target, hold_until, world, policy)
            score = value / (send_pref + turns * REINFORCE_COST_TURN_WEIGHT + 1.0)

            option = ShotOption(
                score=score,
                src_id=src.id,
                target_id=target.id,
                angle=angle,
                turns=turns,
                needed=need,
                send_cap=send_pref,
                mission="reinforce",
                anchor_turn=hold_until,
            )
            missions.append(
                Mission(
                    kind="reinforce",
                    score=score,
                    target_id=target.id,
                    turns=fall_turn,
                    options=[option],
                )
            )

    return missions


def build_crash_exploit_missions(world, policy, planned_commitments, modes):
    if not CRASH_EXPLOIT_ENABLED:
        return []

    missions = []
    for crash in detect_enemy_crashes(world):
        target = world.planet_by_id[crash["target_id"]]
        if target.owner == world.player:
            continue
        desired_arrival = crash["crash_turn"] + CRASH_EXPLOIT_POST_CRASH_DELAY

        for src in world.my_planets:
            src_available = policy["attack_budget"].get(src.id, 0)
            if src_available < PARTIAL_SOURCE_MIN_SHIPS:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                src_available,
                hints=(12, int(target.ships) + 1),
                anchor_turn=desired_arrival,
                max_anchor_diff=CRASH_EXPLOIT_ETA_WINDOW,
            )
            if seeded is None:
                continue
            probe, _ = seeded

            plan = settle_plan(
                src,
                target,
                src_available,
                probe,
                world,
                planned_commitments,
                modes,
                policy,
                mission="crash_exploit",
                eval_turn_fn=lambda turns, desired_arrival=desired_arrival: max(turns, desired_arrival),
                anchor_turn=desired_arrival,
                anchor_tolerance=CRASH_EXPLOIT_ETA_WINDOW,
            )
            if plan is None:
                continue

            angle, turns, _, need, send_pref = plan
            if not candidate_time_valid(target, turns, world, LATE_CAPTURE_BUFFER):
                continue
            value = target_value(target, turns, "crash_exploit", world, modes, policy)
            if value <= 0:
                continue

            score = apply_score_modifiers(
                value / (send_pref + turns * SNIPE_COST_TURN_WEIGHT + 1.0),
                target,
                "crash_exploit",
                world,
            )
            option = ShotOption(
                score=score,
                src_id=src.id,
                target_id=target.id,
                angle=angle,
                turns=turns,
                needed=need,
                send_cap=send_pref,
                mission="crash_exploit",
                anchor_turn=desired_arrival,
            )
            missions.append(
                Mission(
                    kind="crash_exploit",
                    score=score,
                    target_id=target.id,
                    turns=turns,
                    options=[option],
                )
            )

    return missions


def build_comet_slingshot_missions(world, policy, planned_commitments, modes):
    """Generate attack missions when an owned comet is within striking range of an enemy/neutral planet."""
    if not SLINGSHOT_ENABLED:
        return []

    missions = []
    for src in world.my_planets:
        if src.id not in world.comet_ids:
            continue

        src_available = policy["attack_budget"].get(src.id, 0)
        if src_available < SLINGSHOT_MIN_SHIPS:
            continue

        life = world.comet_life(src.id)

        for target in world.planets:
            if target.id == src.id or target.owner == world.player:
                continue
            if dist(src.x, src.y, target.x, target.y) > SLINGSHOT_LAUNCH_PROXIMITY:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                src_available,
                hints=(int(target.ships) + 1,),
            )
            if seeded is None:
                continue
            _, rough_aim = seeded
            rough_turns = rough_aim[1]

            if rough_turns >= life:
                continue
            if not candidate_time_valid(target, rough_turns, world, LATE_CAPTURE_BUFFER):
                continue

            global_needed = world.min_ships_to_own_at(
                target.id,
                rough_turns,
                world.player,
                planned_commitments=planned_commitments,
            )
            if global_needed <= 0 or global_needed > src_available:
                continue

            plan = settle_plan(
                src,
                target,
                src_available,
                preferred_send(target, global_needed, rough_turns, src_available, world, modes, policy),
                world,
                planned_commitments,
                modes,
                policy,
                mission="slingshot",
            )
            if plan is None:
                continue

            angle, turns, _, needed, send_cap = plan
            if turns >= life:
                continue
            if not candidate_time_valid(target, turns, world, LATE_CAPTURE_BUFFER):
                continue

            value = target_value(target, turns, "slingshot", world, modes, policy)
            if value <= 0:
                continue

            score = apply_score_modifiers(
                value / (send_cap + turns * SLINGSHOT_COST_TURN_WEIGHT + 1.0),
                target,
                "slingshot",
                world,
            )
            option = ShotOption(
                score=score,
                src_id=src.id,
                target_id=target.id,
                angle=angle,
                turns=turns,
                needed=needed,
                send_cap=send_cap,
                mission="slingshot",
            )
            missions.append(Mission(
                kind="slingshot",
                score=score,
                target_id=target.id,
                turns=turns,
                options=[option],
            ))

    return missions


def build_denial_missions(world, policy, planned_commitments, modes):
    """Endgame: attack enemy planets to destroy ships even without long-term holds.

    In the last ~25 turns, each enemy ship denied matters more than holding a
    planet for 3 more production ticks.  Score by ships+production denied rather
    than turns_profit.
    """
    if not DENIAL_MISSION_ENABLED or world.remaining_steps >= 50:
        return []
    missions = []
    for src in world.my_planets:
        src_available = policy["attack_budget"].get(src.id, 0)
        if src_available < PARTIAL_SOURCE_MIN_SHIPS:
            continue
        for target in world.enemy_planets:
            seeded = world.best_probe_aim(
                src.id, target.id, src_available,
                hints=(int(target.ships) + 1,),
            )
            if seeded is None:
                continue
            _, rough_aim = seeded
            rough_turns = rough_aim[1]
            if rough_turns > world.remaining_steps - 1:
                continue
            need = world.min_ships_to_own_at(
                target.id, rough_turns, world.player,
                planned_commitments=planned_commitments,
                upper_bound=src_available,
            )
            if need <= 0 or need > src_available:
                continue
            plan = settle_plan(
                src, target, src_available, need,
                world, planned_commitments, modes, policy,
                mission="capture",
            )
            if plan is None:
                continue
            angle, turns, _, plan_need, send = plan
            if turns > world.remaining_steps - 1:
                continue
            _, target_ships_at_arrival = world.projected_state(
                target.id, turns, planned_commitments=planned_commitments
            )
            denied_ships = min(send, target_ships_at_arrival)
            denied_prod = target.production * max(0, world.remaining_steps - turns)
            value = (denied_ships + denied_prod) * DENIAL_SHIP_WEIGHT
            score = value / (send + turns * ATTACK_COST_TURN_WEIGHT + 1.0)
            if target.owner in world.weak_enemies:
                score *= 1.15
            if modes.get("target_leader") and target.owner == world.strongest_enemy:
                score *= 1.08
            missions.append(Mission(
                kind="single",
                score=score,
                target_id=target.id,
                turns=turns,
                options=[ShotOption(
                    score=score, src_id=src.id, target_id=target.id,
                    angle=angle, turns=turns, needed=plan_need, send_cap=send,
                    mission="capture",
                )],
            ))
    return missions


def build_enemy_attack_snipe_missions(world, policy, planned_commitments, modes):
    """Snipe enemy-owned planets that another enemy is attacking.

    When enemy B sends a large fleet to attack enemy A's planet, the surviving
    garrison is weakened.  Arriving just after the fight lets us capture cheaply.
    """
    if not ENEMY_ATTACK_SNIPE_ENABLED:
        return []
    missions = []
    for target_id, arrivals in world.arrivals_by_planet.items():
        target = world.planet_by_id[target_id]
        if target.owner in (world.player, -1):
            continue  # only enemy-owned planets
        attacking = [
            (int(math.ceil(eta)), owner, int(ships))
            for eta, owner, ships in arrivals
            if owner not in (-1, world.player, target.owner) and ships > 0
        ]
        if not attacking:
            continue
        attacking.sort()
        first_eta, _, first_ships = attacking[0]
        if first_ships < target.ships * ENEMY_ATTACK_SNIPE_RATIO:
            continue  # attack too weak to significantly deplete the garrison
        desired_arrival = first_eta + CRASH_EXPLOIT_POST_CRASH_DELAY
        for src in world.my_planets:
            src_available = policy["attack_budget"].get(src.id, 0)
            if src_available < PARTIAL_SOURCE_MIN_SHIPS:
                continue
            seeded = world.best_probe_aim(
                src.id, target.id, src_available,
                hints=(int(target.ships) + 1,),
                anchor_turn=desired_arrival,
                max_anchor_diff=CRASH_EXPLOIT_ETA_WINDOW,
            )
            if seeded is None:
                continue
            probe, _ = seeded
            plan = settle_plan(
                src, target, src_available, probe,
                world, planned_commitments, modes, policy,
                mission="snipe",
                eval_turn_fn=lambda t, da=desired_arrival: max(t, da),
                anchor_turn=desired_arrival,
                anchor_tolerance=CRASH_EXPLOIT_ETA_WINDOW,
            )
            if plan is None:
                continue
            angle, turns, _, need, send_pref = plan
            if not candidate_time_valid(target, turns, world, LATE_CAPTURE_BUFFER):
                continue
            value = target_value(target, turns, "snipe", world, modes, policy)
            if value <= 0:
                continue
            score = apply_score_modifiers(
                value / (send_pref + turns * SNIPE_COST_TURN_WEIGHT + 1.0),
                target, "snipe", world,
            )
            if target.owner in world.weak_enemies:
                score *= 1.12
            if modes.get("target_leader") and target.owner == world.strongest_enemy:
                score *= 1.06
            missions.append(Mission(
                kind="snipe",
                score=score,
                target_id=target_id,
                turns=turns,
                options=[ShotOption(
                    score=score, src_id=src.id, target_id=target_id,
                    angle=angle, turns=turns, needed=need, send_cap=send_pref,
                    mission="snipe", anchor_turn=desired_arrival,
                )],
            ))
    return missions


def plan_moves(world, deadline=None):
    def expired():
        return deadline is not None and time.perf_counter() > deadline

    def time_left():
        if deadline is None:
            return 10**9
        return deadline - time.perf_counter()

    def allow_heavy_phase():
        return time_left() > HEAVY_PHASE_MIN_TIME and len(world.planets) <= HEAVY_ROUTE_PLANET_LIMIT

    def allow_optional_phase():
        return time_left() > OPTIONAL_PHASE_MIN_TIME

    modes = build_modes(world)
    policy = build_policy_state(world, deadline=deadline)
    planned_commitments = defaultdict(list)
    source_options_by_target = defaultdict(list)
    missions = []
    moves = []
    spent_total = defaultdict(int)

    def source_inventory_left(source_id):
        return world.source_inventory_left(source_id, spent_total)

    def source_attack_left(source_id):
        budget = policy["attack_budget"].get(source_id, 0)
        return max(0, budget - spent_total[source_id])

    def append_move(src_id, angle, ships):
        send = min(int(ships), source_inventory_left(src_id))
        if send < 1:
            return 0
        moves.append([src_id, float(angle), int(send)])
        spent_total[src_id] += send
        return send

    def capped_attack_send(src, target, send, need, mission):
        if mission in ("reinforce", "rescue", "snipe", "crash_exploit"):
            return int(send)
        if need >= send:
            return int(send)

        src_left = source_attack_left(src.id)
        if src_left <= 0:
            return 0

        cap = min(int(send), int(src_left))
        if world.enemy_planets:
            nearest_enemy = nearest_distance_to_set(src.x, src.y, world.enemy_planets)
            if nearest_enemy <= FRONTIER_DISTANCE:
                cap = min(cap, max(int(need), int(src_left * FRONTIER_SEND_FRACTION)))
        if send >= BURST_SEND_ABSOLUTE:
            cap = min(cap, max(int(need), int(src_left * BURST_SEND_FRACTION)))
        if modes["is_behind"]:
            cap = min(cap, max(int(need), int(src_left * FRONTIER_SEND_FRACTION)))
        return max(int(need), int(cap))

    def verify_capped_capture(src, target, send, mission):
        aim = world.plan_shot(src.id, target.id, send)
        if aim is None:
            return None
        angle, turns, _, _ = aim
        if not time_filters_pass(target, turns, send, send):
            return None
        eval_turn = turns
        owner_after, _ = world.projected_state(
            target.id,
            eval_turn,
            planned_commitments=planned_commitments,
            extra_arrivals=((turns, world.player, int(send)),),
        )
        if owner_after != world.player:
            return None
        return angle, turns

    def finalize_moves():
        final_moves = []
        used_final = defaultdict(int)
        for src_id, angle, ships in moves:
            source = world.planet_by_id[src_id]
            max_allowed = int(source.ships) - used_final[src_id]
            send = min(int(ships), max_allowed)
            if send >= 1:
                final_moves.append([src_id, float(angle), int(send)])
                used_final[src_id] += send
        return final_moves

    def compute_live_doomed():
        doomed = set()
        for planet in world.my_planets:
            status = world.hold_status(
                planet.id,
                planned_commitments=planned_commitments,
                horizon=DOOMED_EVAC_TURN_LIMIT,
            )
            if (
                not status["holds_full"]
                and status["fall_turn"] is not None
                and status["fall_turn"] <= DOOMED_EVAC_TURN_LIMIT
                and source_inventory_left(planet.id) >= DOOMED_MIN_SHIPS
            ):
                doomed.add(planet.id)
        return doomed

    def time_filters_pass(target, turns, needed, src_cap):
        if not candidate_time_valid(target, turns, world, VERY_LATE_CAPTURE_BUFFER if world.is_very_late else LATE_CAPTURE_BUFFER):
            return False
        if opening_filter(target, turns, needed, src_cap, world, policy):
            return False
        return True

    def cheap_pressure_score(src, target):
        distance = planet_distance(src, target)
        owner_bonus = 95.0 if target.owner not in (-1, world.player) else 28.0
        if target.owner == -1 and world.enemy_planets:
            owner_bonus -= 14.0
        if world.is_static(target.id):
            owner_bonus += 18.0
        if target.id in world.comet_ids:
            owner_bonus -= 30.0
        return (
            owner_bonus
            + target.production * 42.0
            - target.ships * 0.45
            - distance * 1.15
        )

    def route_target_limit(default_limit):
        limit = int(default_limit)
        if world.is_four_player:
            limit += ROUTE_TARGET_FOUR_PLAYER_BONUS
        if modes["is_finishing"]:
            limit += ROUTE_TARGET_FINISHING_BONUS
        if time_left() <= ROUTE_LOW_TIME_THRESHOLD:
            limit = min(limit, ROUTE_TARGET_LOW_TIME_TOP_K)
        return max(1, limit)

    def ranked_attack_targets(src, limit, include_low_value_comets=False):
        scored = []
        for target in world.planets:
            if target.id == src.id or target.owner == world.player:
                continue
            if (
                not include_low_value_comets
                and target.id in world.comet_ids
                and target.production <= LOW_VALUE_COMET_PRODUCTION
            ):
                continue

            score = cheap_pressure_score(src, target)
            if target.owner == -1:
                my_t, enemy_t = policy_reaction_times(target.id, policy)
                if my_t < 10**8 and enemy_t < 10**8:
                    score += max(-30.0, min(24.0, (enemy_t - my_t) * 5.0))
                first_enemy = world.first_enemy_map.get(target.id)
                if first_enemy is not None and first_enemy <= 8:
                    score -= 18.0
            elif target.owner == world.strongest_enemy:
                score += 14.0

            scored.append((score, -planet_distance(src, target), -int(target.production), target.id, target))

        scored.sort(reverse=True)
        return [target for *_, target in scored[:route_target_limit(limit)]]

    def opening_block_relaxed(target, turns, needed, src_left):
        blocked = opening_filter(target, turns, needed, src_left, world, policy)
        if not blocked:
            return False
        if target.owner not in (-1, world.player):
            return False
        if target.production >= 3 and turns <= ROTATING_OPENING_MAX_TURNS + 4:
            return False
        return True

    def pressure_pass():
        pressure_budget = sum(policy["attack_budget"].values())
        if (
            world.is_very_late
            or world.step < PRESSURE_MIN_STEP
            or pressure_budget < PRESSURE_MIN_TOTAL_BUDGET
            or time_left() <= PRESSURE_TIME_FLOOR
        ):
            if DEBUG_LOG and pressure_budget >= PRESSURE_MIN_TOTAL_BUDGET:
                print(
                    f"[P skip step={world.step} budget={pressure_budget} tl={time_left():.3f}]",
                    flush=True,
                )
            return 0

        moved_sources = {src_id for src_id, _, _ in moves}
        launched = 0
        sources = sorted(
            world.my_planets,
            key=lambda planet: policy["attack_budget"].get(planet.id, 0),
            reverse=True,
        )[:PRESSURE_SOURCE_TOP_K]
        for src in sources:
            if launched >= PRESSURE_MAX_MOVES or time_left() <= PRESSURE_TIME_FLOOR:
                return launched
            if src.id in moved_sources:
                continue
            src_left = source_attack_left(src.id)
            if src_left < PRESSURE_MIN_SOURCE_BUDGET:
                continue

            candidates = [
                target
                for target in world.planets
                if target.id != src.id
                and target.owner != world.player
                and not (
                    target.id in world.comet_ids
                    and target.production <= LOW_VALUE_COMET_PRODUCTION
                )
            ]
            candidates.sort(key=lambda target: cheap_pressure_score(src, target), reverse=True)

            best = None
            for target in candidates[:PRESSURE_TARGET_TOP_K]:
                if time_left() <= PRESSURE_TIME_FLOOR:
                    break
                seeded = world.best_probe_aim(
                    src.id,
                    target.id,
                    src_left,
                    hints=(int(target.ships) + 1, max(1, int(src_left * PRESSURE_SEND_FRACTION))),
                )
                if seeded is None:
                    continue
                _, rough_aim = seeded
                rough_turns = rough_aim[1]
                if not candidate_time_valid(
                    target,
                    rough_turns,
                    world,
                    VERY_LATE_CAPTURE_BUFFER if world.is_very_late else LATE_CAPTURE_BUFFER,
                ):
                    continue

                rough_needed = world.min_ships_to_own_at(
                    target.id,
                    rough_turns,
                    world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=src_left,
                )
                if rough_needed <= 0 or rough_needed > src_left:
                    continue
                if opening_block_relaxed(target, rough_turns, rough_needed, src_left):
                    continue

                send_ceiling = max(rough_needed, int(src_left * PRESSURE_SEND_FRACTION))
                send_guess = min(
                    src_left,
                    send_ceiling,
                    preferred_send(target, rough_needed, rough_turns, src_left, world, modes, policy),
                )
                plan = settle_plan(
                    src,
                    target,
                    src_left,
                    send_guess,
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
                if plan is None:
                    continue

                angle, turns, _, need, send = plan
                if send < need or need > src_left:
                    continue

                capped_send = min(send, max(need, int(src_left * PRESSURE_SEND_FRACTION)))
                if capped_send < send:
                    capped_plan = verify_capped_capture(src, target, capped_send, "capture")
                    if capped_plan is None:
                        continue
                    angle, turns = capped_plan
                    send = capped_send

                value = target_value(target, turns, "capture", world, modes, policy)
                if value <= 0:
                    continue
                score = apply_score_modifiers(
                    value / (send + turns * ATTACK_COST_TURN_WEIGHT + 1.0),
                    target,
                    "capture",
                    world,
                )
                if best is None or score > best[0]:
                    best = (score, target.id, angle, turns, need, send)

            if best is None:
                continue

            _, target_id, angle, turns, need, send = best
            actual = append_move(src.id, angle, send)
            if actual < need:
                continue
            if DEBUG_LOG:
                print(
                    f"[P move step={world.step} src={src.id} tgt={target_id} need={need} send={actual} tl={time_left():.3f}]",
                    flush=True,
                )
            moved_sources.add(src.id)
            launched += 1
            planned_commitments[target_id].append((turns, world.player, int(actual)))
        return launched

    pressure_launched = pressure_pass()
    if pressure_launched:
        return finalize_moves()

    if allow_heavy_phase():
        missions.extend(
            build_reinforce_missions(
                world,
                policy,
                planned_commitments,
                modes,
                source_inventory_left,
            )
        )
    missions.extend(build_rescue_missions(world, policy, planned_commitments, modes))
    missions.extend(build_recapture_missions(world, policy, planned_commitments, modes))

    # Only build candidates after solving an intercept so timing decisions come
    # from a real route.
    for src in world.my_planets:
        if expired():
            return finalize_moves()
        src_available = source_attack_left(src.id)
        if src_available <= 0:
            continue

        for target in ranked_attack_targets(src, ROUTE_TARGET_TOP_K):
            if expired():
                return finalize_moves()
            if target.id == src.id or target.owner == world.player:
                continue

            seeded = world.best_probe_aim(
                src.id,
                target.id,
                src_available,
                hints=(int(target.ships) + 1,),
            )
            if seeded is None:
                continue
            _, rough_aim = seeded

            rough_turns = rough_aim[1]
            if not candidate_time_valid(
                target,
                rough_turns,
                world,
                VERY_LATE_CAPTURE_BUFFER if world.is_very_late else LATE_CAPTURE_BUFFER,
            ):
                continue

            global_needed = world.min_ships_to_own_at(
                target.id,
                rough_turns,
                world.player,
                planned_commitments=planned_commitments,
            )
            if global_needed <= 0:
                continue
            if opening_filter(target, rough_turns, global_needed, src_available, world, policy):
                continue

            partial_send_cap = min(
                src_available,
                preferred_send(
                    target,
                    global_needed,
                    rough_turns,
                    src_available,
                    world,
                    modes,
                    policy,
                ),
            )
            if partial_send_cap >= PARTIAL_SOURCE_MIN_SHIPS:
                partial_seed = world.best_probe_aim(
                    src.id,
                    target.id,
                    partial_send_cap,
                    hints=(partial_send_cap, global_needed, int(target.ships) + 1),
                )
                if partial_seed is not None:
                    _, partial_aim = partial_seed
                    p_angle, p_turns, _, _ = partial_aim
                    if time_filters_pass(target, p_turns, global_needed, src_available):
                        partial_value = target_value(target, p_turns, "swarm", world, modes, policy)
                        if partial_value > 0:
                            partial_score = apply_score_modifiers(
                                partial_value / (partial_send_cap + p_turns * ATTACK_COST_TURN_WEIGHT + 1.0),
                                target,
                                "swarm",
                                world,
                            )
                            source_options_by_target[target.id].append(
                                ShotOption(
                                    score=partial_score,
                                    src_id=src.id,
                                    target_id=target.id,
                                    angle=p_angle,
                                    turns=p_turns,
                                    needed=global_needed,
                                    send_cap=partial_send_cap,
                                    mission="swarm",
                                )
                            )

            if global_needed <= src_available:
                send_guess = preferred_send(
                    target,
                    global_needed,
                    rough_turns,
                    src_available,
                    world,
                    modes,
                    policy,
                )
                plan = settle_plan(
                    src,
                    target,
                    src_available,
                    send_guess,
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
                if plan is None:
                    continue

                angle, turns, _, needed, send_cap = plan
                if not time_filters_pass(target, turns, needed, src_available):
                    continue
                if send_cap < 1:
                    continue

                value = target_value(target, turns, "capture", world, modes, policy)
                if value <= 0:
                    continue

                score = apply_score_modifiers(
                    value / (send_cap + turns * ATTACK_COST_TURN_WEIGHT + 1.0),
                    target,
                    "capture",
                    world,
                )

                option = ShotOption(
                    score=score,
                    src_id=src.id,
                    target_id=target.id,
                    angle=angle,
                    turns=turns,
                    needed=needed,
                    send_cap=send_cap,
                    mission="capture",
                )

                if send_cap >= needed:
                    missions.append(
                        Mission(
                            kind="single",
                            score=score,
                            target_id=target.id,
                            turns=turns,
                            options=[option],
                        )
                    )

            snipe = build_snipe_mission(src, target, src_available, world, planned_commitments, modes, policy)
            if snipe is not None:
                missions.append(snipe)

    # Allow small synchronized two-source finishes when one source is not
    # enough on its own.
    for target_id, options in source_options_by_target.items():
        if expired():
            return finalize_moves()
        if len(options) < 2:
            continue

        target = world.planet_by_id[target_id]
        top_options = sorted(options, key=lambda item: -item.score)[:MULTI_SOURCE_TOP_K]
        for i in range(len(top_options)):
            for j in range(i + 1, len(top_options)):
                first = top_options[i]
                second = top_options[j]
                if first.src_id == second.src_id:
                    continue
                pair_tol = swarm_eta_tolerance((first, second), target, world)
                if abs(first.turns - second.turns) > pair_tol:
                    continue

                joint_turn = max(first.turns, second.turns)
                total_cap = first.send_cap + second.send_cap
                need = world.min_ships_to_own_at(
                    target_id,
                    joint_turn,
                    world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=total_cap,
                )
                if need <= 0:
                    continue
                if first.send_cap >= need or second.send_cap >= need:
                    continue
                if total_cap < need:
                    continue

                value = target_value(target, joint_turn, "swarm", world, modes, policy)
                if value <= 0:
                    continue

                pair_score = apply_score_modifiers(
                    value / (need + joint_turn * ATTACK_COST_TURN_WEIGHT + 1.0),
                    target,
                    "swarm",
                    world,
                )
                pair_score *= MULTI_SOURCE_PLAN_PENALTY
                missions.append(
                    Mission(
                        kind="swarm",
                        score=pair_score,
                        target_id=target_id,
                        turns=joint_turn,
                        options=[first, second],
                    )
                )

        if (
            THREE_SOURCE_SWARM_ENABLED
            and allow_heavy_phase()
            and target.owner not in (-1, world.player)
            and int(target.ships) >= THREE_SOURCE_MIN_TARGET_SHIPS
            and len(top_options) >= 3
        ):
            for i in range(len(top_options)):
                for j in range(i + 1, len(top_options)):
                    for k in range(j + 1, len(top_options)):
                        if expired():
                            return finalize_moves()
                        trio = [top_options[i], top_options[j], top_options[k]]
                        if len({option.src_id for option in trio}) < 3:
                            continue
                        trio_tol = swarm_eta_tolerance(tuple(trio), target, world)
                        turns = [option.turns for option in trio]
                        if max(turns) - min(turns) > trio_tol:
                            continue

                        joint_turn = max(turns)
                        total_cap = sum(option.send_cap for option in trio)
                        need = world.min_ships_to_own_at(
                            target_id,
                            joint_turn,
                            world.player,
                            planned_commitments=planned_commitments,
                            upper_bound=total_cap,
                        )
                        if need <= 0 or total_cap < need:
                            continue
                        if any(
                            trio[a].send_cap + trio[b].send_cap >= need
                            for a in range(3)
                            for b in range(a + 1, 3)
                        ):
                            continue

                        value = target_value(target, joint_turn, "swarm", world, modes, policy)
                        if value <= 0:
                            continue

                        trio_score = apply_score_modifiers(
                            value / (need + joint_turn * ATTACK_COST_TURN_WEIGHT + 1.0),
                            target,
                            "swarm",
                            world,
                        )
                        trio_score *= THREE_SOURCE_PLAN_PENALTY
                        missions.append(
                            Mission(
                                kind="swarm",
                                score=trio_score,
                                target_id=target_id,
                                turns=joint_turn,
                                options=trio,
                            )
                        )

    if allow_heavy_phase():
        missions.extend(build_crash_exploit_missions(world, policy, planned_commitments, modes))
        missions.extend(build_comet_slingshot_missions(world, policy, planned_commitments, modes))
        missions.extend(build_enemy_attack_snipe_missions(world, policy, planned_commitments, modes))
    missions.extend(build_denial_missions(world, policy, planned_commitments, modes))

    missions.sort(key=lambda item: -item.score)

    # Update commitments after every accepted launch so later plans see the
    # timing that is already spoken for.
    for mission in missions:
        if expired():
            return finalize_moves()
        target = world.planet_by_id[mission.target_id]

        if mission.kind in ("single", "snipe", "rescue", "recapture", "reinforce", "crash_exploit", "slingshot"):
            option = mission.options[0]
            src = world.planet_by_id[option.src_id]
            if mission.kind == "reinforce":
                left = min(
                    source_inventory_left(option.src_id),
                    int(src.ships * REINFORCE_MAX_SOURCE_FRACTION),
                )
            else:
                left = source_attack_left(option.src_id)
            if left <= 0:
                continue

            if mission.kind == "reinforce":
                plan = settle_reinforce_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    option.anchor_turn,
                    mission.turns,
                )
            elif mission.kind == "rescue":
                plan = settle_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="rescue",
                    eval_turn_fn=lambda _turns, hold_turn=mission.turns: hold_turn,
                    anchor_turn=option.anchor_turn,
                )
            elif mission.kind == "snipe":
                plan = settle_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="snipe",
                    eval_turn_fn=lambda turns, enemy_eta=option.anchor_turn: max(turns, enemy_eta),
                    anchor_turn=option.anchor_turn,
                )
            elif mission.kind == "crash_exploit":
                plan = settle_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="crash_exploit",
                    eval_turn_fn=lambda turns, desired_arrival=option.anchor_turn: max(turns, desired_arrival),
                    anchor_turn=option.anchor_turn,
                    anchor_tolerance=CRASH_EXPLOIT_ETA_WINDOW,
                )
            elif mission.kind == "slingshot":
                plan = settle_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="slingshot",
                )
            else:
                plan = settle_plan(
                    src,
                    target,
                    left,
                    min(left, option.send_cap),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
            if plan is None:
                continue

            angle, turns, _, need, send = plan
            if send < need or need > left:
                continue

            capped_send = capped_attack_send(src, target, send, need, mission.kind)
            if capped_send < send and capped_send >= need:
                capped_plan = verify_capped_capture(src, target, capped_send, mission.kind)
                if capped_plan is not None:
                    angle, turns = capped_plan
                    send = capped_send

            sent = append_move(option.src_id, angle, send)
            if sent < need:
                continue
            planned_commitments[target.id].append((turns, world.player, int(sent)))
            continue

        limits = []
        for option in mission.options:
            left = source_attack_left(option.src_id)
            limits.append(min(left, option.send_cap))
        if min(limits) <= 0:
            continue

        missing = world.min_ships_to_own_at(
            target.id,
            mission.turns,
            world.player,
            planned_commitments=planned_commitments,
            upper_bound=sum(limits),
        )
        if missing <= 0 or sum(limits) < missing:
            continue

        ordered = sorted(
            zip(mission.options, limits),
            key=lambda item: (item[0].turns, -item[1], item[0].src_id),
        )
        remaining = missing
        sends = {}
        for idx, (option, limit) in enumerate(ordered):
            remaining_other = sum(other_limit for _, other_limit in ordered[idx + 1 :])
            send = min(limit, max(0, remaining - remaining_other))
            sends[option.src_id] = send
            remaining -= send
        if remaining > 0:
            continue

        reaimed = []
        for option, _ in ordered:
            send = sends.get(option.src_id, 0)
            if send <= 0:
                continue
            src = world.planet_by_id[option.src_id]
            fixed_aim = world.plan_shot(src.id, target.id, send)
            if fixed_aim is None:
                reaimed = []
                break
            angle, turns, _, _ = fixed_aim
            reaimed.append((option.src_id, angle, turns, send))
        if not reaimed:
            continue

        turns_only = [item[2] for item in reaimed]
        eta_tol = swarm_eta_tolerance(mission.options, target, world)
        if max(turns_only) - min(turns_only) > eta_tol:
            continue

        actual_joint_turn = max(turns_only)
        owner_after, _ = world.projected_state(
            target.id,
            actual_joint_turn,
            planned_commitments=planned_commitments,
            extra_arrivals=[(turns, world.player, send) for _, _, turns, send in reaimed],
        )
        if owner_after != world.player:
            continue

        committed = []
        for src_id, angle, turns, send in reaimed:
            actual = append_move(src_id, angle, send)
            if actual <= 0:
                continue
            committed.append((turns, world.player, int(actual)))
        if sum(item[2] for item in committed) < missing:
            continue
        planned_commitments[target.id].extend(committed)

    # Use leftover attack budget for one more pass after the first commitment
    # wave is fixed.  In very-late game keep_needed==0 so all ships are in the
    # attack budget — always run to drain idle garrisons.
    if allow_optional_phase():
        for src in world.my_planets:
            if expired():
                return finalize_moves()
            src_left = source_attack_left(src.id)
            if src_left < FOLLOWUP_MIN_SHIPS:
                continue

            best = None
            for target in ranked_attack_targets(src, FOLLOWUP_TARGET_TOP_K):
                if expired():
                    return finalize_moves()
                if target.id == src.id or target.owner == world.player:
                    continue
                if target.id in world.comet_ids and target.production <= LOW_VALUE_COMET_PRODUCTION:
                    continue

                seeded = world.best_probe_aim(
                    src.id,
                    target.id,
                    src_left,
                    hints=(int(target.ships) + 1,),
                )
                if seeded is None:
                    continue
                rough_ships, rough_aim = seeded

                est_turns = rough_aim[1]
                if world.is_late and est_turns > world.remaining_steps - LATE_CAPTURE_BUFFER:
                    continue

                rough_needed = world.min_ships_to_own_at(
                    target.id,
                    est_turns,
                    world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=src_left,
                )
                if rough_needed <= 0 or rough_needed > src_left:
                    continue
                if opening_filter(target, est_turns, rough_needed, src_left, world, policy):
                    continue

                send = preferred_send(target, rough_needed, est_turns, src_left, world, modes, policy)
                if send < rough_needed:
                    continue

                plan = settle_plan(
                    src,
                    target,
                    src_left,
                    send,
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
                if plan is None:
                    continue

                _, turns, _, need, final_send = plan
                if world.is_late and turns > world.remaining_steps - LATE_CAPTURE_BUFFER:
                    continue
                if final_send < need:
                    continue

                value = target_value(target, turns, "capture", world, modes, policy)
                if value <= 0:
                    continue

                score = apply_score_modifiers(
                    value / (final_send + turns * ATTACK_COST_TURN_WEIGHT + 1.0),
                    target,
                    "capture",
                    world,
                )
                if best is None or score > best[0]:
                    best = (score, target, plan)

            if best is None:
                continue

            _, target, plan = best
            angle, turns, _, need, send = plan
            src_left = source_attack_left(src.id)
            if need > src_left:
                continue

            plan = settle_plan(
                src,
                target,
                src_left,
                min(src_left, send),
                world,
                planned_commitments,
                modes,
                policy,
                mission="capture",
            )
            if plan is None:
                continue

            angle, turns, _, need, send = plan
            if send < need:
                continue

            capped_send = capped_attack_send(src, target, send, need, "capture")
            if capped_send < send and capped_send >= need:
                capped_plan = verify_capped_capture(src, target, capped_send, "capture")
                if capped_plan is not None:
                    angle, turns = capped_plan
                    send = capped_send

            actual = append_move(src.id, angle, send)
            if actual < need:
                continue
            planned_commitments[target.id].append((turns, world.player, int(actual)))

    # If the global mission pass leaves a rich source idle, give that source a
    # small local top-N chance to act. This prevents midgame hoarding when broad
    # filters are too conservative for a specific planet.
    if (
        world.step >= FALLBACK_MIN_STEP
        and allow_optional_phase()
    ):
        moved_sources = {src_id for src_id, _, _ in moves}
        for src in sorted(world.my_planets, key=lambda planet: -source_attack_left(planet.id)):
            if expired():
                return finalize_moves()
            if src.id in moved_sources:
                continue
            src_left = source_attack_left(src.id)
            if src_left < FALLBACK_MIN_ATTACK_LEFT:
                continue

            ranked_targets = []
            for target in ranked_attack_targets(src, FALLBACK_CHEAP_TARGET_TOP_K):
                if expired():
                    return finalize_moves()
                if target.id == src.id or target.owner == world.player:
                    continue
                if target.id in world.comet_ids and target.production <= LOW_VALUE_COMET_PRODUCTION:
                    continue

                seeded = world.best_probe_aim(
                    src.id,
                    target.id,
                    src_left,
                    hints=(int(target.ships) + 1, src_left),
                )
                if seeded is None:
                    continue
                _, rough_aim = seeded
                rough_turns = rough_aim[1]
                if not candidate_time_valid(
                    target,
                    rough_turns,
                    world,
                    VERY_LATE_CAPTURE_BUFFER if world.is_very_late else LATE_CAPTURE_BUFFER,
                ):
                    continue

                rough_needed = world.min_ships_to_own_at(
                    target.id,
                    rough_turns,
                    world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=src_left,
                )
                if rough_needed <= 0 or rough_needed > src_left:
                    continue

                blocked_by_opening = opening_filter(
                    target, rough_turns, rough_needed, src_left, world, policy
                )
                if blocked_by_opening:
                    local_pressure_ok = (
                        target.owner not in (-1, world.player)
                        or (
                            target.production >= ROTATING_OPENING_LOW_PROD
                            and rough_turns <= ROTATING_OPENING_MAX_TURNS + 6
                        )
                    )
                    if not local_pressure_ok:
                        continue

                value = target_value(target, rough_turns, "capture", world, modes, policy)
                if value <= 0:
                    continue
                score = apply_score_modifiers(
                    value / (rough_needed + rough_turns * ATTACK_COST_TURN_WEIGHT + 1.0),
                    target,
                    "capture",
                    world,
                )
                if blocked_by_opening:
                    score *= FALLBACK_SCORE_MULT
                ranked_targets.append((score, target, rough_needed, rough_turns))

            best = None
            for _, target, rough_needed, rough_turns in sorted(
                ranked_targets, key=lambda item: -item[0]
            )[:FALLBACK_TOP_TARGETS]:
                if expired():
                    return finalize_moves()
                src_left = source_attack_left(src.id)
                if src_left < rough_needed:
                    continue
                send_guess = preferred_send(
                    target,
                    rough_needed,
                    rough_turns,
                    src_left,
                    world,
                    modes,
                    policy,
                )
                plan = settle_plan(
                    src,
                    target,
                    src_left,
                    send_guess,
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
                if plan is None:
                    continue
                angle, turns, _, need, send = plan
                if send < need or need > src_left:
                    continue
                capped_send = capped_attack_send(src, target, send, need, "capture")
                if capped_send < send and capped_send >= need:
                    capped_plan = verify_capped_capture(src, target, capped_send, "capture")
                    if capped_plan is not None:
                        angle, turns = capped_plan
                        send = capped_send
                score = target_value(target, turns, "capture", world, modes, policy) / (
                    send + turns * ATTACK_COST_TURN_WEIGHT + 1.0
                )
                if best is None or score > best[0]:
                    best = (score, target.id, angle, turns, need, send)

            if best is None:
                continue
            _, target_id, angle, turns, need, send = best
            actual = append_move(src.id, angle, send)
            if actual < need:
                continue
            moved_sources.add(src.id)
            planned_commitments[target_id].append((turns, world.player, int(actual)))

    # Comet evacuation: ships left on a comet that expires are permanently lost.
    # When a comet's remaining life falls below the threshold, send its surplus
    # ships to the best reachable target, or retreat to a safe ally.
    if not expired():
        for planet in world.my_planets:
            if expired():
                break
            if planet.id not in world.comet_ids:
                continue
            life = world.comet_life(planet.id)
            if life > COMET_EVAC_LIFE_THRESHOLD:
                continue
            available_now = source_inventory_left(planet.id)
            if available_now < COMET_EVAC_MIN_SHIPS:
                continue

            best_attack = None
            for target in world.planets:
                if target.id == planet.id or target.owner == world.player:
                    continue
                seeded = world.best_probe_aim(
                    planet.id, target.id, available_now,
                    hints=(available_now, int(target.ships) + 1),
                )
                if seeded is None:
                    continue
                _, probe_aim = seeded
                probe_turns = probe_aim[1]
                if probe_turns >= life or probe_turns > world.remaining_steps - 2:
                    continue
                need = world.min_ships_to_own_at(
                    target.id, probe_turns, world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=available_now,
                )
                if need <= 0 or need > available_now:
                    continue
                plan = settle_plan(
                    planet, target, available_now,
                    min(available_now, max(need, int(target.ships) + 1)),
                    world, planned_commitments, modes, policy, mission="capture",
                )
                if plan is None:
                    continue
                angle, act_turns, _, plan_need, send = plan
                if act_turns >= life or send < plan_need:
                    continue
                value = target_value(target, act_turns, "capture", world, modes, policy)
                if value <= 0:
                    continue
                score = value / (send + act_turns + 1.0)
                if target.owner not in (-1, world.player):
                    score *= 1.05
                if best_attack is None or score > best_attack[0]:
                    best_attack = (score, target.id, angle, act_turns, send, plan_need)

            if best_attack is not None:
                _, tgt_id, angle, act_turns, send, plan_need = best_attack
                actual = append_move(planet.id, angle, send)
                if actual >= plan_need:
                    planned_commitments[tgt_id].append((act_turns, world.player, int(actual)))
                continue

            # Retreat to nearest safe non-comet ally so ships survive
            safe_allies = [
                ally for ally in world.my_planets
                if ally.id != planet.id and ally.id not in world.comet_ids
            ]
            if not safe_allies:
                continue
            retreat = min(safe_allies, key=lambda a: planet_distance(planet, a))
            aim = world.plan_shot(planet.id, retreat.id, available_now)
            if aim is None:
                continue
            angle, r_turns, _, _ = aim
            if r_turns < life:
                append_move(planet.id, angle, available_now)

    # If a planet cannot hold soon, prefer reinforcement first. For stacks that
    # still look doomed after the main mission pass, prefer a last useful
    # capture; otherwise retreat the stack to a safer ally.
    if expired():
        return finalize_moves()
    live_doomed = compute_live_doomed()
    if live_doomed:
        frontier_targets = (
            world.enemy_planets
            if world.enemy_planets
            else (world.static_neutral_planets or world.neutral_planets)
        )
        if frontier_targets:
            frontier_distance = {
                planet.id: nearest_distance_to_set(planet.x, planet.y, frontier_targets)
                for planet in world.my_planets
            }
        else:
            frontier_distance = {planet.id: 10**9 for planet in world.my_planets}

        for planet in world.my_planets:
            if expired():
                return finalize_moves()
            if planet.id not in live_doomed:
                continue

            available_now = source_inventory_left(planet.id)
            if available_now < 1:
                continue

            best_capture = None
            for target in ranked_attack_targets(
                planet,
                DOOMED_TARGET_TOP_K,
                include_low_value_comets=True,
            ):
                if expired():
                    return finalize_moves()
                if target.id == planet.id or target.owner == world.player:
                    continue
                seeded = world.best_probe_aim(
                    planet.id,
                    target.id,
                    available_now,
                    hints=(available_now, int(target.ships) + 1),
                )
                if seeded is None:
                    continue
                _, probe_aim = seeded
                probe_turns = probe_aim[1]
                if probe_turns > world.remaining_steps - 2:
                    continue

                need = world.min_ships_to_own_at(
                    target.id,
                    probe_turns,
                    world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=available_now,
                )
                if need <= 0 or need > available_now:
                    continue

                plan = settle_plan(
                    planet,
                    target,
                    available_now,
                    min(available_now, max(need, int(target.ships) + 1)),
                    world,
                    planned_commitments,
                    modes,
                    policy,
                    mission="capture",
                )
                if plan is None:
                    continue
                angle, turns, _, plan_need, send = plan
                if send < plan_need:
                    continue
                score = target_value(target, turns, "capture", world, modes, policy) / (send + turns + 1.0)
                if target.owner not in (-1, world.player):
                    score *= 1.05
                if best_capture is None or score > best_capture[0]:
                    best_capture = (score, target.id, angle, turns, send)

            if best_capture is not None:
                _, target_id, angle, turns, need = best_capture
                actual = append_move(planet.id, angle, need)
                if actual >= 1:
                    planned_commitments[target_id].append((turns, world.player, int(actual)))
                continue

            safe_allies = [
                ally
                for ally in world.my_planets
                if ally.id != planet.id and ally.id not in live_doomed
            ]
            if not safe_allies:
                continue

            retreat_target = min(
                safe_allies,
                key=lambda ally: (
                    frontier_distance.get(ally.id, 10**9),
                    planet_distance(planet, ally),
                ),
            )
            aim = world.plan_shot(planet.id, retreat_target.id, available_now)
            if aim is None:
                continue
            angle, _, _, _ = aim
            append_move(planet.id, angle, available_now)

    # Rear planets feed the frontier through staging allies instead of acting
    # as slow solo attackers.
    if (
        (world.enemy_planets or world.neutral_planets)
        and len(world.my_planets) > 1
        and not world.is_late
        and allow_optional_phase()
    ):
        live_doomed = compute_live_doomed()
        frontier_targets = (
            world.enemy_planets
            if world.enemy_planets
            else (world.static_neutral_planets or world.neutral_planets)
        )
        frontier_distance = {
            planet.id: nearest_distance_to_set(planet.x, planet.y, frontier_targets)
            for planet in world.my_planets
        }
        safe_fronts = [
            planet for planet in world.my_planets if planet.id not in live_doomed
        ]
        if safe_fronts:
            front_anchor = min(safe_fronts, key=lambda planet: frontier_distance[planet.id])
            send_ratio = (
                REAR_SEND_RATIO_FOUR_PLAYER if world.is_four_player else REAR_SEND_RATIO_TWO_PLAYER
            )
            if modes["is_finishing"]:
                send_ratio = max(send_ratio, REAR_SEND_RATIO_FOUR_PLAYER)

            for rear in sorted(world.my_planets, key=lambda planet: -frontier_distance[planet.id]):
                if expired():
                    return finalize_moves()
                if rear.id == front_anchor.id or rear.id in live_doomed:
                    continue
                if source_attack_left(rear.id) < REAR_SOURCE_MIN_SHIPS:
                    continue
                if frontier_distance[rear.id] < frontier_distance[front_anchor.id] * REAR_DISTANCE_RATIO:
                    continue

                stage_candidates = [
                    planet
                    for planet in safe_fronts
                    if planet.id != rear.id
                    and frontier_distance[planet.id] < frontier_distance[rear.id] * REAR_STAGE_PROGRESS
                ]
                if stage_candidates:
                    # Prefer the staging planet that is closest to the frontier
                    # AND still has capacity for more ships (high attack budget).
                    front = min(
                        stage_candidates,
                        key=lambda planet: (
                            frontier_distance[planet.id],
                            -policy["attack_budget"].get(planet.id, 0),
                        ),
                    )
                else:
                    objective = min(
                        frontier_targets,
                        key=lambda target: planet_distance(rear, target),
                    )
                    remaining_fronts = [planet for planet in safe_fronts if planet.id != rear.id]
                    if not remaining_fronts:
                        continue
                    front = min(
                        remaining_fronts,
                        key=lambda planet: planet_distance(planet, objective),
                    )

                if front.id == rear.id:
                    continue

                send = int(source_attack_left(rear.id) * send_ratio)
                if send < REAR_SEND_MIN_SHIPS:
                    continue

                aim = world.plan_shot(rear.id, front.id, send)
                if aim is None:
                    continue

                angle, turns, _, _ = aim
                if turns > REAR_MAX_TRAVEL_TURNS:
                    continue
                # Skip if the staging planet will fall before ships arrive.
                front_timeline = world.base_timeline.get(front.id, {})
                front_fall = front_timeline.get("fall_turn")
                if front_fall is not None and front_fall <= turns:
                    continue
                append_move(rear.id, angle, send)

    # Endgame drain: in final turns, deplete every remaining garrison toward
    # any reachable target.  Fleets in flight count toward final score, so
    # sending beats hoarding.  keep_needed is already 0 when is_very_late.
    if world.remaining_steps <= ENDGAME_DRAIN_TURNS and not expired():
        drain_targets = [p for p in world.planets if p.owner != world.player]
        drain_targets.sort(key=lambda t: (
            0 if t.owner not in (-1, world.player) else 1,
            -int(t.production),
        ))
        for src in world.my_planets:
            if expired():
                break
            avail = source_inventory_left(src.id)
            if avail < ENDGAME_DRAIN_MIN_SHIPS:
                continue
            best_drain = None
            for target in drain_targets:
                if target.id == src.id:
                    continue
                seeded = world.best_probe_aim(src.id, target.id, avail,
                                             hints=(avail, int(target.ships) + 1))
                if seeded is None:
                    continue
                _, aim_info = seeded
                d_turns = aim_info[1]
                if d_turns > world.remaining_steps - 1:
                    continue
                need = world.min_ships_to_own_at(
                    target.id, d_turns, world.player,
                    planned_commitments=planned_commitments,
                    upper_bound=avail,
                )
                if need <= 0 or need > avail:
                    continue
                plan = settle_plan(
                    src, target, avail, min(avail, max(need, int(target.ships) + 1)),
                    world, planned_commitments, modes, policy, mission="capture",
                )
                if plan is None:
                    continue
                angle, d_turns2, _, plan_need, send = plan
                if send < plan_need or d_turns2 > world.remaining_steps - 1:
                    continue
                value = target_value(target, d_turns2, "capture", world, modes, policy)
                if value <= 0:
                    continue
                score = value / (send + d_turns2 + 1.0)
                if best_drain is None or score > best_drain[0]:
                    best_drain = (score, target.id, angle, d_turns2, send, plan_need)
            if best_drain is not None:
                _, tgt_id, angle, d_turns2, send, plan_need = best_drain
                avail_now = source_inventory_left(src.id)
                if plan_need > avail_now:
                    continue
                actual = append_move(src.id, angle, min(avail_now, send))
                if actual >= plan_need:
                    planned_commitments[tgt_id].append((d_turns2, world.player, int(actual)))

    final = finalize_moves()
    if DEBUG_LOG:
        total_budget = sum(policy["attack_budget"].values())
        total_reserve = sum(policy["reserve"].values())
        total_sent = sum(int(n) for _, _, n in final)
        should_log = (
            (not final and total_budget >= STALL_DEBUG_BUDGET)
            or total_sent >= BURST_DEBUG_SHIPS
            or world.step < 5
            or world.step % 25 == 0
        )
    else:
        should_log = False

    if should_log:
        top5 = sorted(missions, key=lambda m: -m.score)[:5]
        top5_str = " | ".join(
            f"{m.options[0].mission if m.options else m.kind}→{m.target_id} s={m.score:.3f}"
            for m in top5
        )
        moves_str = " ".join(f"{src}:{int(n)}" for src, _, n in final)
        print(
            f"[D step={world.step} me={len(world.my_planets)} en={len(world.enemy_planets)}"
            f" neu={len(world.neutral_planets)} prod={world.my_prod} ships={world.my_total}"
            f" budget={total_budget} reserve={total_reserve} missions={len(missions)}"
            f" sent={total_sent}] top:{top5_str} | moves:{moves_str}",
            flush=True,
        )
    return final


# ============================================================
# Agent Entry Point
# ============================================================

def _read(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def build_world(obs):
    player = _read(obs, "player", 0)
    step = _read(obs, "step", 0) or 0
    raw_planets = _read(obs, "planets", []) or []
    raw_fleets = _read(obs, "fleets", []) or []
    ang_vel = _read(obs, "angular_velocity", 0.0) or 0.0
    raw_init = _read(obs, "initial_planets", []) or []
    comets = _read(obs, "comets", []) or []
    comet_ids = set(_read(obs, "comet_planet_ids", []) or [])

    planets = [Planet(*planet) for planet in raw_planets]
    fleets = [Fleet(*fleet) for fleet in raw_fleets]
    initial_planets = [Planet(*planet) for planet in raw_init]
    initial_by_id = {planet.id: planet for planet in initial_planets}

    return WorldModel(
        player=player,
        step=step,
        planets=planets,
        fleets=fleets,
        initial_by_id=initial_by_id,
        ang_vel=ang_vel,
        comets=comets,
        comet_ids=comet_ids,
    )


def _looks_like_new_episode_without_step(obs):
    raw_planets = _read(obs, "planets", []) or []
    raw_fleets = _read(obs, "fleets", []) or []
    player = _read(obs, "player", 0)
    if raw_fleets:
        return False

    owned = [planet for planet in raw_planets if len(planet) > 5 and planet[1] == player]
    enemy_owned = [
        planet
        for planet in raw_planets
        if len(planet) > 5 and planet[1] not in (-1, player)
    ]
    if len(owned) != 1 or not enemy_owned:
        return False
    return int(owned[0][5]) <= 15 and all(int(planet[5]) <= 15 for planet in enemy_owned)


def agent(obs, config=None):
    global _INFERRED_STEP
    start_time = time.perf_counter()
    if _read(obs, "step", None) is None:
        if _INFERRED_STEP > 20 and _looks_like_new_episode_without_step(obs):
            _INFERRED_STEP = -1
        _INFERRED_STEP += 1
        if isinstance(obs, dict):
            obs = dict(obs)
            obs["step"] = _INFERRED_STEP
        else:
            try:
                setattr(obs, "step", _INFERRED_STEP)
            except Exception:
                pass
    else:
        _INFERRED_STEP = int(_read(obs, "step", 0) or 0)
    world = build_world(obs)
    if not world.my_planets:
        return []
    act_timeout = _read(config, "actTimeout", 1.0) if config is not None else 1.0
    soft_budget = min(SOFT_ACT_DEADLINE, max(0.55, act_timeout * 0.82))
    deadline = start_time + soft_budget
    return plan_moves(world, deadline=deadline)


__all__ = ["agent", "build_world"]
