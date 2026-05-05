"""
Orbit Wars - Agent v4.0
Key improvements over v3:
- Dynamic keep_needed: binary search for minimum garrison to survive (frees more ships for offense)
- Proactive defense: pre-emptively reserve vs nearby enemy threats
- Reaction time map: detect safe vs contested neutrals
- Indirect features: neighborhood production density in scoring
- Recapture missions: plan recaptures of planets about to fall
- Rear staging: forward excess ships from rear planets to front-line planets
- Doomed evacuation: use ships from doomed planets for captures or retreats
- Crash exploit: swoop in after enemy fleets cancel each other
- Opening filter: avoid wasting ships on distant rotating neutrals early
"""

import math
from collections import defaultdict

SUN_XY = (50.0, 50.0)
SUN_RADIUS = 10.0
SUN_SAFETY = 1.5
ROTATION_LIMIT = 50.0
MAX_SPEED = 6.0
TOTAL_STEPS = 500
HORIZON = 110
ROUTE_SEARCH = 60

LATE_TURNS = 60
VERY_LATE_TURNS = 25
OPENING_TURNS = 80
EARLY_TURNS = 40

DEFENSE_LOOKAHEAD = 28
PROACTIVE_HORIZON = 14
PROACTIVE_RATIO = 0.20
MULTI_ENEMY_HORIZON = 14
MULTI_ENEMY_RATIO = 0.22

ATTACK_TURN_WEIGHT = 0.55
SNIPE_TURN_WEIGHT = 0.45
INDIRECT_SCALE = 0.15
INDIRECT_FRIENDLY = 0.35
INDIRECT_NEUTRAL = 0.9
INDIRECT_ENEMY = 1.25

REAR_MIN_SHIPS = 16
REAR_SEND_RATIO = 0.62
REAR_MIN_SEND = 10
REAR_MAX_TURNS = 40
REAR_DISTANCE_RATIO = 1.25
REAR_STAGE_PROGRESS = 0.78

CRASH_ETA_WINDOW = 2
CRASH_MIN_SHIPS = 10
CRASH_POST_DELAY = 1

OPENING_MAX_ROTATING_TURNS = 13
OPENING_HIGH_PROD = 4
OPENING_MAX_SAFE_TURNS = 10

DOOMED_LIMIT = 24
DOOMED_MIN = 8


# --- PHYSICS ---

def _d(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def fleet_speed(ships):
    if ships <= 1:
        return 1.0
    r = max(0.0, min(1.0, math.log(ships) / math.log(1000.0)))
    return 1.0 + (MAX_SPEED - 1.0) * (r ** 1.5)


def is_static(planet, initial_by_id):
    init = initial_by_id.get(planet[0])
    if init is not None:
        return _d(init[2], init[3], *SUN_XY) + init[4] >= ROTATION_LIMIT
    return _d(planet[2], planet[3], *SUN_XY) + planet[4] >= ROTATION_LIMIT


def predict_pos(planet, ang_vel, turns, initial_by_id, comet_ids):
    pid, px, py = planet[0], planet[2], planet[3]
    if pid in comet_ids:
        return px, py
    init = initial_by_id.get(pid)
    if init is None:
        return px, py
    orbit_r = _d(init[2], init[3], *SUN_XY)
    if orbit_r + init[4] >= ROTATION_LIMIT:
        return px, py
    theta = math.atan2(py - SUN_XY[1], px - SUN_XY[0])
    new_theta = theta + ang_vel * turns
    return (SUN_XY[0] + orbit_r * math.cos(new_theta),
            SUN_XY[1] + orbit_r * math.sin(new_theta))


def _clears_sun(lx, ly, ex, ey):
    dx, dy = ex - lx, ey - ly
    sq = dx * dx + dy * dy
    if sq < 1e-9:
        return _d(lx, ly, *SUN_XY) > SUN_RADIUS + SUN_SAFETY
    t = max(0.0, min(1.0, ((SUN_XY[0] - lx) * dx + (SUN_XY[1] - ly) * dy) / sq))
    return _d(lx + t * dx, ly + t * dy, *SUN_XY) > SUN_RADIUS + SUN_SAFETY


def _aim_direct(src, tx, ty, tr, ships):
    sx, sy, sr = src[2], src[3], src[4]
    angle = math.atan2(ty - sy, tx - sx)
    lx = sx + math.cos(angle) * (sr + 0.1)
    ly = sy + math.sin(angle) * (sr + 0.1)
    hit_d = max(0.0, _d(sx, sy, tx, ty) - sr - 0.1 - tr)
    end_x = lx + math.cos(angle) * hit_d
    end_y = ly + math.sin(angle) * hit_d
    if not _clears_sun(lx, ly, end_x, end_y):
        return None
    turns = max(1, math.ceil(hit_d / fleet_speed(ships)))
    return angle, turns


def intercept(src, tgt, ships, ang_vel, initial_by_id, comet_ids, max_search=ROUTE_SEARCH):
    tr = tgt[4]
    tx, ty = tgt[2], tgt[3]
    result = None
    for _ in range(5):
        r = _aim_direct(src, tx, ty, tr, ships)
        if r is None:
            break
        result = r
        angle, turns = r
        ntx, nty = predict_pos(tgt, ang_vel, turns, initial_by_id, comet_ids)
        if abs(ntx - tx) < 0.2 and abs(nty - ty) < 0.2:
            return result
        tx, ty = ntx, nty
    if result is not None:
        return result
    for t_cand in range(1, max_search + 1):
        fx, fy = predict_pos(tgt, ang_vel, t_cand, initial_by_id, comet_ids)
        r = _aim_direct(src, fx, fy, tr, ships)
        if r is None:
            continue
        angle, fly_turns = r
        if abs(fly_turns - t_cand) <= 1:
            actual_t = max(fly_turns, t_cand)
            vx, vy = predict_pos(tgt, ang_vel, actual_t, initial_by_id, comet_ids)
            vr = _aim_direct(src, vx, vy, tr, ships)
            if vr is not None and abs(vr[1] - actual_t) <= 1:
                return vr
    return None


# --- FLEET TRACKING ---

def build_arrivals(raw_fleets, planets):
    arrivals = defaultdict(list)
    for f in raw_fleets:
        if len(f) < 7:
            continue
        fx, fy = float(f[2]), float(f[3])
        angle, ships, owner = float(f[4]), int(f[6]), int(f[1])
        dx, dy = math.cos(angle), math.sin(angle)
        speed = fleet_speed(max(1, ships))
        best_t, best_pid = 1e9, None
        for p in planets:
            px, py, pr = float(p[2]), float(p[3]), float(p[4])
            qx, qy = px - fx, py - fy
            proj = qx * dx + qy * dy
            if proj < 0:
                continue
            perp_sq = qx * qx + qy * qy - proj * proj
            if perp_sq >= pr * pr:
                continue
            hit_d = max(0.0, proj - math.sqrt(max(0.0, pr * pr - perp_sq)))
            t = hit_d / speed if speed > 0 else 1e9
            if t < best_t and t <= HORIZON:
                best_t, best_pid = t, p[0]
        if best_pid is not None:
            arrivals[best_pid].append((int(math.ceil(best_t)), owner, ships))
    return arrivals


# --- TIMELINE SIMULATION ---

def _resolve_combat(owner, garrison, group):
    by_owner = defaultdict(float)
    for _, att_owner, ships in group:
        by_owner[att_owner] += ships
    if not by_owner:
        return owner, garrison
    sorted_owners = sorted(by_owner.items(), key=lambda x: x[1], reverse=True)
    top_owner, top_ships = sorted_owners[0]
    if len(sorted_owners) > 1:
        second = sorted_owners[1][1]
        if top_ships == second:
            return owner, garrison
        top_ships -= second
    if owner == top_owner:
        return owner, garrison + top_ships
    garrison -= top_ships
    if garrison < 0:
        return top_owner, -garrison
    return owner, garrison


def simulate_timeline(planet, arrival_list, player_id, horizon=HORIZON):
    by_turn = defaultdict(list)
    for eta, owner, ships in arrival_list:
        eta = max(1, int(math.ceil(eta)))
        if eta <= horizon:
            by_turn[eta].append((eta, owner, ships))
    owner = int(planet[1])
    garrison = float(planet[5])
    owner_at = {0: owner}
    ships_at = {0: garrison}
    fall_turn = None
    for t in range(1, horizon + 1):
        if owner != -1:
            garrison += planet[6]
        if t in by_turn:
            prev_owner = owner
            owner, garrison = _resolve_combat(owner, garrison, by_turn[t])
            if prev_owner == player_id and owner != player_id and fall_turn is None:
                fall_turn = t
        garrison = max(0.0, garrison)
        owner_at[t] = owner
        ships_at[t] = garrison
    return {"owner_at": owner_at, "ships_at": ships_at, "fall_turn": fall_turn}


def _survives_with(planet, arrival_list, player_id, start_garrison, horizon=HORIZON):
    by_turn = defaultdict(list)
    for eta, owner, ships in arrival_list:
        eta = max(1, int(math.ceil(eta)))
        if 0 < eta <= horizon:
            by_turn[eta].append((eta, owner, ships))
    owner = int(planet[1])
    garrison = float(start_garrison)
    for t in range(1, horizon + 1):
        if owner != -1:
            garrison += planet[6]
        if t in by_turn:
            prev_owner = owner
            owner, garrison = _resolve_combat(owner, garrison, by_turn[t])
            if prev_owner == player_id and owner != player_id:
                return False
        garrison = max(0.0, garrison)
    return True


def compute_keep_needed(planet, arrival_list, player_id, horizon=HORIZON):
    full_ships = int(planet[5])
    if not _survives_with(planet, arrival_list, player_id, full_ships, horizon):
        return full_ships
    lo, hi = 0, full_ships
    for _ in range(12):
        mid = (lo + hi) // 2
        if _survives_with(planet, arrival_list, player_id, float(mid), horizon):
            hi = mid
        else:
            lo = mid + 1
    return hi


def ships_needed_at(planet, arrival_turn, tl, player_id):
    t = max(0, min(arrival_turn, HORIZON))
    if tl:
        owner = tl["owner_at"].get(t, int(planet[1]))
        ships = tl["ships_at"].get(t, float(planet[5]))
    else:
        owner = int(planet[1])
        ships = float(planet[5])
    if owner == player_id:
        return 0
    return max(1, int(math.ceil(ships)) + 1)


def min_reinforcement(planet, arrival_list, player_id, arrive_by):
    tl = simulate_timeline(planet, arrival_list, player_id)
    if tl["fall_turn"] is None:
        return 0
    lo, hi = 1, 400
    for _ in range(10):
        mid = (lo + hi) // 2
        augmented = arrival_list + [(arrive_by, player_id, mid)]
        tl2 = simulate_timeline(planet, augmented, player_id)
        if tl2["fall_turn"] is None:
            hi = mid
        else:
            lo = mid + 1
    return hi if hi <= 400 else 0


def indirect_score(planet, planets, player_id):
    score = 0.0
    for other in planets:
        if other[0] == planet[0]:
            continue
        d = _d(planet[2], planet[3], other[2], other[3])
        if d < 1:
            continue
        factor = float(other[6]) / (d + 12.0)
        if other[1] == player_id:
            score += factor * INDIRECT_FRIENDLY
        elif other[1] == -1:
            score += factor * INDIRECT_NEUTRAL
        else:
            score += factor * INDIRECT_ENEMY
    return score


# --- MAIN AGENT ---

def agent(obs, conf):
    actions = []

    def _get(key, default):
        if isinstance(obs, dict):
            return obs.get(key, default)
        return getattr(obs, key, default)

    player_id  = int(_get("player", 0))
    step       = int(_get("step", 0) or 0)
    ang_vel    = float(_get("angular_velocity", 0.03) or 0.03)
    planets    = _get("planets", []) or []
    raw_fleets = _get("fleets", []) or []
    raw_init   = _get("initial_planets", []) or []
    comet_ids  = set(_get("comet_planet_ids", []) or [])

    if not planets:
        return actions

    initial_by_id = {p[0]: p for p in raw_init}
    planet_by_id  = {p[0]: p for p in planets}

    my_planets = [p for p in planets if p[1] == player_id]
    enemy_ps   = [p for p in planets if p[1] not in (-1, player_id)]
    neutral_ps = [p for p in planets if p[1] == -1]
    other_ps   = enemy_ps + neutral_ps

    if not my_planets:
        return actions

    remaining    = TOTAL_STEPS - step
    is_early     = step < EARLY_TURNS
    is_opening   = step < OPENING_TURNS
    is_late      = remaining < LATE_TURNS
    is_very_late = remaining < VERY_LATE_TURNS

    my_strength = sum(p[5] for p in my_planets)
    enemy_strength = sum(p[5] for p in enemy_ps)
    for f in raw_fleets:
        if len(f) >= 7:
            owner, ships = int(f[1]), int(f[6])
            if owner == player_id:
                my_strength += ships
            elif owner != -1:
                enemy_strength += ships

    domination   = (my_strength - enemy_strength) / max(1, my_strength + enemy_strength)
    is_behind    = bool(enemy_ps) and domination < -0.20
    is_ahead     = bool(enemy_ps) and domination > 0.18
    is_finishing = (domination > 0.35 and step > 100 and
                    sum(p[6] for p in my_planets) > sum(p[6] for p in enemy_ps) * 1.25)

    arrivals  = build_arrivals(raw_fleets, planets)
    timelines = {p[0]: simulate_timeline(p, arrivals.get(p[0], []), player_id)
                 for p in planets}

    # Dynamic keep_needed (binary search) + proactive reserve
    keep_needed = {}
    for p in my_planets:
        if is_very_late:
            keep_needed[p[0]] = 0
            continue
        kn = compute_keep_needed(p, arrivals.get(p[0], []), player_id)
        proactive = 0
        for enemy in sorted(enemy_ps, key=lambda e: _d(e[2], e[3], p[2], p[3]))[:4]:
            result = intercept(enemy, p, max(1, int(enemy[5])), ang_vel, initial_by_id, comet_ids)
            if result is None:
                continue
            _, eta = result
            if eta <= PROACTIVE_HORIZON:
                proactive = max(proactive, int(enemy[5] * PROACTIVE_RATIO))
            if eta <= MULTI_ENEMY_HORIZON:
                proactive = max(proactive, int(enemy[5] * MULTI_ENEMY_RATIO))
        keep_needed[p[0]] = min(int(p[5]), max(kn, proactive))

    attack_budget = {p[0]: max(0, int(p[5]) - keep_needed.get(p[0], 0)) for p in my_planets}
    spent = defaultdict(int)

    def attack_left(pid):
        return max(0, attack_budget.get(pid, 0) - spent[pid])

    def inventory_left(pid):
        p = planet_by_id.get(pid)
        return max(0, int(p[5]) - spent[pid]) if p else 0

    def do_move(pid, angle, send):
        send = min(int(send), inventory_left(pid))
        if send < 1:
            return 0
        actions.append([pid, float(angle), int(send)])
        spent[pid] += send
        return send

    # Indirect scores
    indirect = {p[0]: indirect_score(p, planets, player_id) for p in planets}

    # Reaction time map: for each neutral, (my_min_eta, enemy_min_eta)
    reaction_map = {}
    for tgt in neutral_ps:
        my_t = 1e9
        for src in sorted(my_planets, key=lambda p: _d(p[2], p[3], tgt[2], tgt[3]))[:4]:
            r = intercept(src, tgt, max(1, int(src[5])), ang_vel, initial_by_id, comet_ids)
            if r:
                my_t = min(my_t, r[1])
        en_t = 1e9
        for src in sorted(enemy_ps, key=lambda p: _d(p[2], p[3], tgt[2], tgt[3]))[:4]:
            r = intercept(src, tgt, max(1, int(src[5])), ang_vel, initial_by_id, comet_ids)
            if r:
                en_t = min(en_t, r[1])
        reaction_map[tgt[0]] = (my_t, en_t)

    def is_safe_neutral(tgt):
        my_t, en_t = reaction_map.get(tgt[0], (1e9, 1e9))
        return my_t <= en_t - 2

    def is_contested_neutral(tgt):
        my_t, en_t = reaction_map.get(tgt[0], (1e9, 1e9))
        return abs(my_t - en_t) <= 2

    def compute_value(tgt, arrival_turns, mission="capture"):
        turns_profit = max(1, remaining - arrival_turns)
        if tgt[0] in comet_ids:
            turns_profit = min(turns_profit, 35)
            if turns_profit <= 0:
                return -1.0
        value = float(tgt[6]) * turns_profit
        value += indirect.get(tgt[0], 0.0) * turns_profit * INDIRECT_SCALE
        if is_static(tgt, initial_by_id):
            value *= 1.55 if tgt[1] not in (-1, player_id) else 1.4
        elif is_opening:
            value *= 0.9
        if tgt[1] not in (-1, player_id):
            value *= 1.85 if not is_opening else 1.45
            if is_finishing:
                value *= 1.15
        elif tgt[1] == -1:
            if is_safe_neutral(tgt):
                value *= 1.2
            elif is_contested_neutral(tgt):
                value *= 0.7
            if is_early:
                value *= 1.2
        if tgt[0] in comet_ids:
            value *= 0.65
        if is_late:
            value += float(tgt[5]) * 0.6
            if tgt[1] not in (-1, player_id):
                if sum(p[5] for p in enemy_ps if p[1] == tgt[1]) <= 45:
                    value += 18.0
        if mission == "snipe":
            value *= 1.12
        elif mission == "recapture":
            value *= 0.88
        elif mission == "crash":
            value *= 1.18
        if is_behind and tgt[1] == -1:
            value *= 0.92
        if is_ahead and tgt[1] == -1 and is_contested_neutral(tgt):
            value *= 0.92
        return value

    def compute_margin(tgt, arrival_turns):
        if tgt[1] == -1:
            margin = min(8, 2 + tgt[6] * 2)
            if is_contested_neutral(tgt):
                margin += 5
        else:
            margin = min(12, 3 + tgt[6] * 2)
            if is_static(tgt, initial_by_id):
                margin += 4
            if is_finishing:
                margin += 3
        if arrival_turns > 18:
            margin += min(8, arrival_turns // 3)
        if tgt[0] in comet_ids:
            margin = max(0, margin - 6)
        return max(0, margin)

    def opening_filter(tgt, turns):
        if not is_opening or tgt[1] != -1:
            return False
        if tgt[0] in comet_ids:
            return True
        if is_static(tgt, initial_by_id):
            return False
        my_t, en_t = reaction_map.get(tgt[0], (1e9, 1e9))
        gap = en_t - my_t
        if tgt[6] >= OPENING_HIGH_PROD and turns <= OPENING_MAX_SAFE_TURNS and gap >= 2:
            return False
        return turns > OPENING_MAX_ROTATING_TURNS

    # =====================================================
    # PHASE 1 - RESCUE (defend friendly planets about to fall)
    # =====================================================
    defended = set()
    for tgt in sorted(my_planets, key=lambda p: timelines[p[0]].get("fall_turn") or 1e9):
        tl = timelines.get(tgt[0], {})
        fall_turn = tl.get("fall_turn")
        if fall_turn is None or fall_turn > DEFENSE_LOOKAHEAD or tgt[0] in defended:
            continue
        needed = min_reinforcement(tgt, arrivals.get(tgt[0], []), player_id, fall_turn - 1)
        if needed <= 0:
            continue
        best = None
        for src in sorted(my_planets, key=lambda p: _d(p[2], p[3], tgt[2], tgt[3])):
            if src[0] == tgt[0]:
                continue
            left = inventory_left(src[0])
            if left < needed:
                continue
            result = intercept(src, tgt, needed, ang_vel, initial_by_id, comet_ids)
            if result is None:
                continue
            angle, turns = result
            if turns > fall_turn:
                continue
            if best is None or turns < best[2]:
                send = min(left, needed + max(2, int(tgt[6])))
                best = (src[0], angle, turns, send)
        if best:
            src_id, angle, turns, send = best
            do_move(src_id, angle, send)
            defended.add(tgt[0])

    # =====================================================
    # PHASE 2 - BUILD ALL ATTACK OPTIONS then execute greedily
    # =====================================================
    # each entry: (score, src_id, tgt_id, angle, turns, send, needed)
    all_options = []
    opts_by_tgt = defaultdict(list)

    for src in my_planets:
        pid = src[0]
        left = attack_left(pid)
        if left < 4:
            continue

        for tgt in other_ps:
            tgt_tl = timelines.get(tgt[0], {})

            r_est = intercept(src, tgt, max(1, int(tgt[5]) + 1), ang_vel, initial_by_id, comet_ids)
            if r_est is None:
                continue
            _, turns_est = r_est

            max_turns = remaining - (3 if is_very_late else (5 if is_late else 7))
            if turns_est > max_turns or turns_est > HORIZON:
                continue
            if opening_filter(tgt, turns_est):
                continue

            owner_at_arr = tgt_tl.get("owner_at", {}).get(min(turns_est, HORIZON), int(tgt[1]))
            if owner_at_arr == player_id:
                continue

            needed = ships_needed_at(tgt, turns_est, tgt_tl, player_id)
            if needed == 0:
                continue

            r2 = intercept(src, tgt, needed, ang_vel, initial_by_id, comet_ids)
            if r2 is None:
                continue
            angle, turns = r2
            if turns > max_turns:
                continue

            margin = compute_margin(tgt, turns)
            send = min(left, needed + margin)
            value = compute_value(tgt, turns, "capture")
            if value <= 0:
                continue

            if send >= needed:
                score = value / (send + turns * ATTACK_TURN_WEIGHT + 1.0)
                if is_static(tgt, initial_by_id):
                    score *= 1.18
                if is_early and tgt[1] == -1 and is_static(tgt, initial_by_id):
                    score *= 1.25
                entry = (score, pid, tgt[0], angle, turns, send, needed)
                all_options.append(entry)
                opts_by_tgt[tgt[0]].append(entry)

            # Snipe: time our arrival to coincide with an incoming enemy fleet
            if tgt[1] == -1:
                enemy_etas = sorted({eta for eta, owner, _ in arrivals.get(tgt[0], [])
                                     if owner not in (-1, player_id)})
                for enemy_eta in enemy_etas[:2]:
                    if abs(turns - enemy_eta) > 1:
                        continue
                    sn_turn = max(turns, enemy_eta)
                    sn_needed = ships_needed_at(tgt, sn_turn, tgt_tl, player_id)
                    if sn_needed == 0 or sn_needed > left:
                        continue
                    sn_send = min(left, sn_needed + 2)
                    sn_value = compute_value(tgt, sn_turn, "snipe")
                    sn_score = sn_value / (sn_send + sn_turn * SNIPE_TURN_WEIGHT + 1.0) * 1.12
                    entry = (sn_score, pid, tgt[0], angle, turns, sn_send, sn_needed)
                    all_options.append(entry)
                    opts_by_tgt[tgt[0]].append(entry)

    # Crash exploit: arrive after two enemy fleets cancel each other at a planet
    for pid_crash, arr_list in arrivals.items():
        tgt = planet_by_id.get(pid_crash)
        if tgt is None or int(tgt[1]) == player_id:
            continue
        enemy_ev = sorted([(eta, owner, ships) for eta, owner, ships in arr_list
                           if owner not in (-1, player_id) and ships > 0])
        for i in range(len(enemy_ev)):
            for j in range(i + 1, len(enemy_ev)):
                if enemy_ev[i][1] == enemy_ev[j][1]:
                    continue
                if abs(enemy_ev[i][0] - enemy_ev[j][0]) > CRASH_ETA_WINDOW:
                    break
                if enemy_ev[i][2] + enemy_ev[j][2] < CRASH_MIN_SHIPS:
                    continue
                crash_turn = max(enemy_ev[i][0], enemy_ev[j][0]) + CRASH_POST_DELAY
                tgt_tl = timelines.get(pid_crash, {})
                for src in my_planets:
                    left = attack_left(src[0])
                    if left < 4:
                        continue
                    result = intercept(src, tgt, left, ang_vel, initial_by_id, comet_ids)
                    if result is None:
                        continue
                    angle, turns = result
                    if abs(turns - crash_turn) > CRASH_ETA_WINDOW:
                        continue
                    needed = ships_needed_at(tgt, turns, tgt_tl, player_id)
                    if needed <= 0 or needed > left:
                        continue
                    send = min(left, needed + 3)
                    value = compute_value(tgt, turns, "crash")
                    if value <= 0:
                        continue
                    score = value / (send + turns * SNIPE_TURN_WEIGHT + 1.0) * 1.05
                    entry = (score, src[0], pid_crash, angle, turns, send, needed)
                    all_options.append(entry)
                    opts_by_tgt[pid_crash].append(entry)

    # Execute single-source missions greedily by score
    all_options.sort(key=lambda x: -x[0])
    used_targets = set()

    for score, src_id, tgt_id, angle, turns, send, needed in all_options:
        if tgt_id in used_targets:
            continue
        left = attack_left(src_id)
        if left < needed:
            continue
        actual = do_move(src_id, angle, min(left, send))
        if actual >= needed:
            used_targets.add(tgt_id)

    # =====================================================
    # PHASE 3 - SWARM: two-source attacks on still-untaken targets
    # =====================================================
    for tgt_id, opts in opts_by_tgt.items():
        if tgt_id in used_targets:
            continue
        tgt = planet_by_id.get(tgt_id)
        if tgt is None:
            continue
        tgt_tl = timelines.get(tgt_id, {})
        top = sorted(opts, key=lambda x: -x[0])[:6]
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                s1, s2 = top[i], top[j]
                if s1[1] == s2[1]:
                    continue
                if abs(s1[4] - s2[4]) > 2:
                    continue
                joint_turn = max(s1[4], s2[4])
                c1 = min(attack_left(s1[1]), s1[5])
                c2 = min(attack_left(s2[1]), s2[5])
                if c1 <= 0 or c2 <= 0:
                    continue
                needed_joint = ships_needed_at(tgt, joint_turn, tgt_tl, player_id)
                if needed_joint <= 0 or c1 + c2 < needed_joint:
                    continue
                if c1 >= needed_joint or c2 >= needed_joint:
                    continue
                value = compute_value(tgt, joint_turn, "capture")
                if value <= 0:
                    continue
                do_move(s1[1], s1[3], c1)
                do_move(s2[1], s2[3], c2)
                used_targets.add(tgt_id)
                break
            if tgt_id in used_targets:
                break

    # =====================================================
    # PHASE 4 - RECAPTURE (planets that will fall: plan retake shortly after)
    # =====================================================
    for tgt in my_planets:
        tl = timelines.get(tgt[0], {})
        fall_turn = tl.get("fall_turn")
        if fall_turn is None or fall_turn > DEFENSE_LOOKAHEAD or tgt[0] in defended:
            continue
        for src in sorted(my_planets, key=lambda p: _d(p[2], p[3], tgt[2], tgt[3])):
            if src[0] == tgt[0]:
                continue
            left = attack_left(src[0])
            if left < 6:
                continue
            result = intercept(src, tgt, left, ang_vel, initial_by_id, comet_ids)
            if result is None:
                continue
            angle, turns = result
            if turns <= fall_turn or turns - fall_turn > 10:
                continue
            needed = ships_needed_at(tgt, turns, tl, player_id)
            if needed <= 0 or needed > left:
                continue
            do_move(src[0], angle, min(left, needed + 3))
            break

    # =====================================================
    # PHASE 5 - REAR STAGING
    # =====================================================
    if my_planets and (enemy_ps or neutral_ps) and not is_late and len(my_planets) > 1:
        frontier_targets = enemy_ps if enemy_ps else (
            [p for p in neutral_ps if is_static(p, initial_by_id)] or neutral_ps
        )
        if frontier_targets:
            def dist_to_front(planet):
                return min(_d(planet[2], planet[3], t[2], t[3]) for t in frontier_targets)

            front_dist = {p[0]: dist_to_front(p) for p in my_planets}
            non_doomed = [p for p in my_planets if timelines[p[0]].get("fall_turn") is None]

            if non_doomed:
                front_anchor = min(non_doomed, key=lambda p: front_dist[p[0]])
                for rear in sorted(my_planets, key=lambda p: -front_dist[p[0]]):
                    if rear[0] == front_anchor[0]:
                        continue
                    if timelines[rear[0]].get("fall_turn") is not None:
                        continue
                    left = attack_left(rear[0])
                    if left < REAR_MIN_SHIPS:
                        continue
                    if front_dist[rear[0]] < front_dist[front_anchor[0]] * REAR_DISTANCE_RATIO:
                        continue
                    candidates = [p for p in non_doomed
                                  if p[0] != rear[0]
                                  and front_dist[p[0]] < front_dist[rear[0]] * REAR_STAGE_PROGRESS]
                    if not candidates:
                        continue
                    front = min(candidates, key=lambda p: _d(rear[2], rear[3], p[2], p[3]))
                    send = int(left * REAR_SEND_RATIO)
                    if send < REAR_MIN_SEND:
                        continue
                    result = intercept(rear, front, send, ang_vel, initial_by_id, comet_ids)
                    if result is None:
                        continue
                    angle, turns = result
                    if turns > REAR_MAX_TURNS:
                        continue
                    do_move(rear[0], angle, send)

    # =====================================================
    # PHASE 6 - DOOMED EVACUATION
    # =====================================================
    for planet in my_planets:
        tl = timelines.get(planet[0], {})
        fall_turn = tl.get("fall_turn")
        if fall_turn is None or fall_turn > DOOMED_LIMIT:
            continue
        left = inventory_left(planet[0])
        if left < DOOMED_MIN:
            continue
        best_cap = None
        for tgt in other_ps:
            result = intercept(planet, tgt, left, ang_vel, initial_by_id, comet_ids)
            if result is None:
                continue
            angle, turns = result
            if turns > remaining - 2:
                continue
            tgt_tl = timelines.get(tgt[0], {})
            needed = ships_needed_at(tgt, turns, tgt_tl, player_id)
            if needed <= 0 or needed > left:
                continue
            value = compute_value(tgt, turns, "capture")
            send = min(left, needed + 3)
            score = value / (send + turns + 1.0)
            if tgt[1] not in (-1, player_id):
                score *= 1.05
            if best_cap is None or score > best_cap[0]:
                best_cap = (score, angle, turns, send)
        if best_cap:
            _, angle, turns, send = best_cap
            do_move(planet[0], angle, send)
        else:
            safe_allies = [p for p in my_planets
                           if p[0] != planet[0]
                           and timelines[p[0]].get("fall_turn") is None]
            if safe_allies:
                retreat = min(safe_allies, key=lambda p: _d(planet[2], planet[3], p[2], p[3]))
                result = intercept(planet, retreat, left, ang_vel, initial_by_id, comet_ids)
                if result:
                    angle, _ = result
                    do_move(planet[0], angle, left)

    return actions

