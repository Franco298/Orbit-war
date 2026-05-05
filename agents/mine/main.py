"""
Orbit Wars - ROI Predictive Agent
A deterministic optimization engine featuring precise deflection shooting,
comet exploitation, and end-game garrison draining.
"""

import math

# Core Map Constants
SUN_XY = (50.0, 50.0)
SUN_RADIUS = 10.0

def predict_future_position(planet, angular_velocity: float, turns_ahead: int) -> tuple:
    """Calculates the exact (x, y) coordinates of a planet in the future."""
    cx, cy = SUN_XY
    x, y = planet[2], planet[3]
    radius = planet[4]
    
    dx, dy = x - cx, y - cy
    dist_from_sun = math.hypot(dx, dy)
    
    # --- IL FIX DELLA MIRA ---
    # Static planets logic: if distance + radius >= 50, they do not move.
    if dist_from_sun + radius >= 50.0:
        return x, y
        
    theta = math.atan2(dy, dx)
    theta_new = theta + angular_velocity * turns_ahead
    return (cx + dist_from_sun * math.cos(theta_new), cy + dist_from_sun * math.sin(theta_new))

def calculate_fleet_speed(num_ships: int) -> float:
    """Calculates fleet speed based on the logarithmic scaling rule."""
    if num_ships <= 0: return 1.0
    ratio = math.log(num_ships) / math.log(1000)
    return min(6.0, 1.0 + 5.0 * ratio ** 1.5)

def is_path_safe(x1, y1, x2, y2) -> bool:
    """Checks if the trajectory intersects the deadly radius of the Sun."""
    cx, cy = SUN_XY
    dx, dy = x2 - x1, y2 - y1
    seg_len_sq = dx*dx + dy*dy
    if seg_len_sq == 0: return False
    
    t = max(0.0, min(1.0, ((cx - x1) * dx + (cy - y1) * dy) / seg_len_sq))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(closest_x - cx, closest_y - cy) > SUN_RADIUS

def calculate_capture_cost(target_ships, target_production, travel_turns, is_neutral) -> int:
    """Calculates the exact number of ships needed to guarantee a capture."""
    if is_neutral:
        return target_ships + 1
    return max(0, target_ships + (target_production * travel_turns)) + 1

def calculate_exact_interception(src_x, src_y, target_p, angular_velocity, num_ships) -> tuple:
    """Simulates future turns to find the exact ballistic interception point."""
    speed = calculate_fleet_speed(num_ships)
    
    # Capped at 150 turns to strictly respect Kaggle's 1-second timeout rule
    for t in range(1, 150):
        fut_x, fut_y = predict_future_position(target_p, angular_velocity, t)
        dist = math.hypot(fut_x - src_x, fut_y - src_y)
        travel_turns = math.ceil(dist / speed)
        
        if travel_turns <= t:
            return fut_x, fut_y, t
            
    return target_p[2], target_p[3], 999 # Target unreachable in reasonable time

def evaluate_target_roi(source_p, target_p, angular_velocity, comet_ids) -> tuple:
    """Evaluates a target's Return On Investment (Score = Production / (Distance * Cost))."""
    src_x, src_y = source_p[2], source_p[3]
    tgt_ships = target_p[5]
    tgt_prod = target_p[6]
    is_neutral = (target_p[1] == -1)
    
    # 1. Initial cost estimation assuming a 10-turn travel time
    estimated_cost = calculate_capture_cost(tgt_ships, tgt_prod, 10, is_neutral)
    
    # 2. Deflection shooting calculation based on estimated speed
    fut_x, fut_y, travel_time = calculate_exact_interception(src_x, src_y, target_p, angular_velocity, estimated_cost)
    
    # 3. Exact cost recalculation using actual travel time
    actual_cost = calculate_capture_cost(tgt_ships, tgt_prod, travel_time, is_neutral)
    
    # 4. Final aim adjustment using exact fleet speed
    fut_x, fut_y, final_time = calculate_exact_interception(src_x, src_y, target_p, angular_velocity, actual_cost)
    
    # Abort if the final path crosses the Sun
    if not is_path_safe(src_x, src_y, fut_x, fut_y):
        return -1.0, actual_cost, fut_x, fut_y 
        
    actual_dist = math.hypot(fut_x - src_x, fut_y - src_y)
    if actual_dist == 0: actual_dist = 0.1
    
    # ROI Formula
    score = tgt_prod / (actual_dist * actual_cost)
    
    # Comet Slingshot Strategy: Give comets massive priority
    if target_p[0] in comet_ids:
        score *= 10.0 
        
    return score, actual_cost, fut_x, fut_y

def agent(obs, conf):
    """Main agent execution loop called by the Kaggle environment."""
    actions = []
    
    # Safe Extraction: Handles both dicts (local) and Structs (Kaggle servers)
    player_id = obs.get("player", 0) if isinstance(obs, dict) else getattr(obs, "player", 0)
    step = obs.get("step", 0) if isinstance(obs, dict) else getattr(obs, "step", 0)
    angular_velocity = obs.get("angular_velocity", 0.03) if isinstance(obs, dict) else getattr(obs, "angular_velocity", 0.03)
    planets = obs.get("planets", []) if isinstance(obs, dict) else getattr(obs, "planets", [])
    
    raw_comets = obs.get("comet_planet_ids", []) if isinstance(obs, dict) else getattr(obs, "comet_planet_ids", [])
    comet_ids = set(raw_comets)
    
    my_planets = [p for p in planets if p[1] == player_id]
    other_planets = [p for p in planets if p[1] != player_id]
    
    if not my_planets or not other_planets:
        return actions
        
    # Garrison Draining Strategy: Abandon defense in the last 50 turns
    FINAL_PUSH = (step >= 450) 
    
    # Prevent multiple friendly planets from launching redundant attacks at the same target
    targeted_enemies = set() 
    
    for my_p in my_planets:
        planet_id = my_p[0]
        ships = my_p[5]
        
        # Comet Evacuation: Flee before the comet is destroyed and ships are lost
        if planet_id in comet_ids and (step % 100) > 85:
            safe_allies = [p for p in my_planets if p[0] not in comet_ids]
            if safe_allies:
                escape_target = safe_allies[0]
                escape_angle = math.atan2(escape_target[3] - my_p[3], escape_target[2] - my_p[2])
                actions.append([planet_id, float(escape_angle), int(ships)])
            continue

        min_garrison = 0 if FINAL_PUSH else 5
        available_ships = ships - min_garrison
        
        if available_ships > 0:
            best_score = -1.0
            best_action = None
            chosen_target_id = None
            
            for target_p in other_planets:
                target_id = target_p[0]
                if target_id in targeted_enemies: 
                    continue 
                    
                score, cost, fut_x, fut_y = evaluate_target_roi(my_p, target_p, angular_velocity, comet_ids)
                
                # Attack only if the ROI is best and we can afford the exact cost
                if score > best_score and available_ships >= cost:
                    best_score = score
                    angle = math.atan2(fut_y - my_p[3], fut_x - my_p[2])
                    best_action = [planet_id, float(angle), int(cost)]
                    chosen_target_id = target_id
                    
            if best_action:
                actions.append(best_action)
                targeted_enemies.add(chosen_target_id)
                
    return actions
