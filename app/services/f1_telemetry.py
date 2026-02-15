"""F1 Race Telemetry Service"""
import os
import orjson
import fastf1
import fastf1.plotting
import numpy as np
from datetime import timedelta
from typing import Dict, Any, Optional, Callable
from app.utils.tyres import get_tyre_compound_int
from app.services.f1_s3_bucket import  upload_telemetry_to_s3
from app.services.mongo_logger import mongo_logger


FPS = 25
DT = 1 / FPS

# Precision settings for data reduction
POSITION_PRECISION = 1  # 1 decimal place for x, y coordinates
DISTANCE_PRECISION = 1  # 1 decimal place for distances
SPEED_PRECISION = 0  # 0 decimal places for speed (integers)


def enable_cache():
    """Enable FastF1 cache"""
    # Check if running on Vercel
    if os.environ.get("VERCEL"):
        cache_dir = "/tmp/fastf1-cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
    else:
        if not os.path.exists('.fastf1-cache'):
            os.makedirs('.fastf1-cache')
        fastf1.Cache.enable_cache('.fastf1-cache')


def load_race_session(year: int, round_number: int):
    """Load F1 race session"""
    session = fastf1.get_session(year, round_number, 'R')
    session.load(telemetry=True)
    return session


def get_driver_colors(session) -> Dict[str, list]:
    """Get driver color mapping"""
    color_mapping = fastf1.plotting.get_driver_color_mapping(session)
    
    # Convert hex colors to RGB lists
    rgb_colors = {}
    for driver, hex_color in color_mapping.items():
        hex_color = hex_color.lstrip('#')
        rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        rgb_colors[driver] = rgb
    return rgb_colors


def get_race_telemetry(
    session, 
    refresh_data: bool = False,
    cache_dir: str = "computed_data",
    frame_skip: int = 1,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Get race telemetry data for all drivers.
    
    Args:
        session: FastF1 session object
        refresh_data: If True, recompute data even if cached
        cache_dir: Directory to store cached data
        frame_skip: Only include every Nth frame
        progress_callback: Function to report progress (message, percentage)
    
    Returns:
        Dictionary containing frames, driver_colors, and track_statuses
    """
    # Override cache_dir if on Vercel (read-only filesystem except /tmp)
    if os.environ.get("VERCEL"):
        cache_dir = "/tmp/computed_data"
    event_name = str(session).replace(' ', '_')
    
    # Check if this data has already been computed
    if not refresh_data:
        try:
            cache_file = f"{cache_dir}/{event_name}_race_telemetry.json"
            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    data = orjson.loads(f.read())
                    print("Loaded precomputed race telemetry data.")
                    mongo_logger.info(f"Cache hit for {event_name}", context={"frame_skip": frame_skip})
                    # Apply frame skipping if needed (cache always has full resolution)
                    if frame_skip > 1:
                        data["frames"] = data["frames"][::frame_skip]
                        print(f"Applied frame skipping: {frame_skip} (reduced to {len(data['frames'])} frames)")
                    return data
        except (FileNotFoundError, orjson.JSONDecodeError, KeyError) as e:
            print(f"Cache load failed: {e}, recomputing...")
            mongo_logger.warning(f"Cache load failed or missing for {event_name}, recomputing...", error=e)
            pass  # Need to compute from scratch
    
    drivers = session.drivers
    driver_codes = {
        num: session.get_driver(num)["Abbreviation"]
        for num in drivers
    }
    
    driver_data = {}
    global_t_min = None
    global_t_max = None
    
    # 1. Get all of the drivers telemetry data
    total_drivers = len(drivers)
    for i, driver_no in enumerate(drivers):
        # Progress update (30% to 70% range for data fetching)
        if progress_callback:
            progress = 30.0 + (i / total_drivers * 40.0)
            progress_callback(f"Processing driver {i+1}/{total_drivers}...", progress)
            
    for driver_no in drivers:
        code = driver_codes[driver_no]
        print("Getting telemetry for driver:", code)
        mongo_logger.debug(f"Processing telemetry for driver {code}")
        laps_driver = session.laps.pick_drivers(driver_no)
        
        if laps_driver.empty:
            continue
        
        t_all = []
        x_all = []
        y_all = []
        race_dist_all = []
        rel_dist_all = []
        lap_numbers = []
        tyre_compounds = []
        speed_all = []
        gear_all = []
        drs_all = []
        total_dist_so_far = 0.0
        
        # iterate laps in order
        for _, lap in laps_driver.iterlaps():
            # get telemetry for THIS lap only
            lap_tel = lap.get_telemetry()
            lap_number = lap.LapNumber
            tyre_compund_as_int = get_tyre_compound_int(lap.Compound)
            
            if lap_tel.empty:
                continue
            
            t_lap = lap_tel["SessionTime"].dt.total_seconds().to_numpy()
            x_lap = lap_tel["X"].to_numpy()
            y_lap = lap_tel["Y"].to_numpy()
            d_lap = lap_tel["Distance"].to_numpy()
            rd_lap = lap_tel["RelativeDistance"].to_numpy()
            speed_kph_lap = lap_tel["Speed"].to_numpy()
            gear_lap = lap_tel["nGear"].to_numpy()
            drs_lap = lap_tel["DRS"].to_numpy()
            
            # normalise lap distance to start at 0
            d_lap = d_lap - d_lap.min()
            lap_length = d_lap.max()  # approx. circuit length for this lap
            
            # race distance = distance before this lap + distance within this lap
            race_d_lap = total_dist_so_far + d_lap
            total_dist_so_far += lap_length
            
            t_all.append(t_lap)
            x_all.append(x_lap)
            y_all.append(y_lap)
            race_dist_all.append(race_d_lap)
            rel_dist_all.append(rd_lap)
            lap_numbers.append(np.full_like(t_lap, lap_number))
            tyre_compounds.append(np.full_like(t_lap, tyre_compund_as_int))
            speed_all.append(speed_kph_lap)
            gear_all.append(gear_lap)
            drs_all.append(drs_lap)
        
        if not t_all:
            continue
        
        t_all = np.concatenate(t_all)
        x_all = np.concatenate(x_all)
        y_all = np.concatenate(y_all)
        race_dist_all = np.concatenate(race_dist_all)
        rel_dist_all = np.concatenate(rel_dist_all)
        lap_numbers = np.concatenate(lap_numbers)
        tyre_compounds = np.concatenate(tyre_compounds)
        speed_all = np.concatenate(speed_all)
        gear_all = np.concatenate(gear_all)
        drs_all = np.concatenate(drs_all)
        
        order = np.argsort(t_all)
        t_all = t_all[order]
        x_all = x_all[order]
        y_all = y_all[order]
        race_dist_all = race_dist_all[order]
        rel_dist_all = rel_dist_all[order]
        lap_numbers = lap_numbers[order]
        tyre_compounds = tyre_compounds[order]
        speed_all = speed_all[order]
        gear_all = gear_all[order]
        drs_all = drs_all[order]
        
        driver_data[code] = {
            "t": t_all,
            "x": x_all,
            "y": y_all,
            "dist": race_dist_all,
            "rel_dist": rel_dist_all,
            "lap": lap_numbers,
            "tyre": tyre_compounds,
            "speed": speed_all,
            "gear": gear_all,
            "drs": drs_all,
        }
        
        t_min = t_all.min()
        t_max = t_all.max()
        global_t_min = t_min if global_t_min is None else min(global_t_min, t_min)
        global_t_max = t_max if global_t_max is None else max(global_t_max, t_max)
    
    # 2. Create a timeline (start from zero)
    if progress_callback:
        progress_callback("Building race timeline...", 75.0)
        
    timeline = np.arange(global_t_min, global_t_max, DT) - global_t_min
    
    # 3. Resample each driver's telemetry (x, y, gap) onto the common timeline
    resampled_data = {}
    for code, data in driver_data.items():
        t = data["t"] - global_t_min  # Shift
        x = data["x"]
        y = data["y"]
        dist = data["dist"]
        rel_dist = data["rel_dist"]
        tyre = data["tyre"]
        speed = data['speed']
        gear = data['gear']
        drs = data['drs']
        
        # ensure sorted by time
        order = np.argsort(t)
        t_sorted = t[order]
        x_sorted = x[order]
        y_sorted = y[order]
        dist_sorted = dist[order]
        rel_dist_sorted = rel_dist[order]
        lap_sorted = data["lap"][order]
        tyre_sorted = tyre[order]
        speed_sorted = speed[order]
        gear_sorted = gear[order]
        drs_sorted = drs[order]
        
        x_resampled = np.interp(timeline, t_sorted, x_sorted)
        y_resampled = np.interp(timeline, t_sorted, y_sorted)
        dist_resampled = np.interp(timeline, t_sorted, dist_sorted)
        rel_dist_resampled = np.interp(timeline, t_sorted, rel_dist_sorted)
        lap_resampled = np.interp(timeline, t_sorted, lap_sorted)
        tyre_resampled = np.interp(timeline, t_sorted, tyre_sorted)
        speed_resampled = np.interp(timeline, t_sorted, speed_sorted)
        gear_resampled = np.interp(timeline, t_sorted, gear_sorted)
        drs_resampled = np.interp(timeline, t_sorted, drs_sorted)
        
        resampled_data[code] = {
            "t": timeline,
            "x": x_resampled,
            "y": y_resampled,
            "dist": dist_resampled,   # race distance (metres since Lap 1 start)
            "rel_dist": rel_dist_resampled,
            "lap": lap_resampled,
            "tyre": tyre_resampled,
            "speed": speed_resampled,
            "gear": gear_resampled,
            "drs": drs_resampled,
        }
    
    # 4. Incorporate track status data into the timeline (for safety car, VSC, etc.)
    track_status = session.track_status
    formatted_track_statuses = []
    for status in track_status.to_dict('records'):
        seconds = timedelta.total_seconds(status['Time'])
        start_time = seconds - global_t_min  # Shift to match timeline
        end_time = None
        
        # Set the end time of the previous status
        if formatted_track_statuses:
            formatted_track_statuses[-1]['end_time'] = start_time
        
        formatted_track_statuses.append({
            'status': status['Status'],
            'start_time': start_time,
            'end_time': end_time,
        })
    
    # 5. Build the frames + LIVE LEADERBOARD
    if progress_callback:
        progress_callback("Generating leaderboard frames...", 80.0)
        
    # Always compute all frames for cache, apply frame_skip when returning
    frames = []
    for i, t in enumerate(timeline):
        snapshot = []
        for code, d in resampled_data.items():
            snapshot.append({
                "code": code,
                "dist": round(float(d["dist"][i]), DISTANCE_PRECISION),
                "x": round(float(d["x"][i]), POSITION_PRECISION),
                "y": round(float(d["y"][i]), POSITION_PRECISION),
                "lap": int(round(d["lap"][i])),
                "rel_dist": round(float(d["rel_dist"][i]), DISTANCE_PRECISION),
                "tyre": int(round(d["tyre"][i])),
                "speed": int(round(d['speed'][i])) if SPEED_PRECISION == 0 else round(float(d['speed'][i]), SPEED_PRECISION),
                "gear": int(d['gear'][i]),
                "drs": int(d['drs'][i]),
            })
        
        # If for some reason we have no drivers at this instant
        if not snapshot:
            continue
        
        # 5b. Sort by race distance to get POSITIONS (1–20)
        # Leader = largest race distance covered
        snapshot.sort(key=lambda r: r["dist"], reverse=True)
        leader = snapshot[0]
        leader_lap = leader["lap"]
        
        # 5c. Compute gap to car in front in SECONDS
        frame_data = {}
        for idx, car in enumerate(snapshot):
            code = car["code"]
            position = idx + 1
            
            # include speed, gear, drs_active in frame driver dict
            frame_data[code] = {
                "x": car["x"],
                "y": car["y"],
                "dist": car["dist"],
                "lap": car["lap"],
                "rel_dist": car["rel_dist"],
                "tyre": car["tyre"],
                "position": position,
                "speed": car['speed'],
                "gear": car['gear'],
                "drs": car['drs'],
            }
        
        frames.append({
            "t": round(float(t), 2),  # Round time to 2 decimal places
            "lap": leader_lap,   # leader's lap at this time
            "drivers": frame_data,
        })
    
    print("completed telemetry extraction...")
    print("Saving to JSON file...")
    
    # If computed_data/ directory doesn't exist, create it
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Prepare full resolution result for cache
    full_result = {
        "frames": frames,
        "driver_colors": get_driver_colors(session),
        "track_statuses": formatted_track_statuses,
    }

    # Extract year and round from session
    year = session.event.EventDate.year
    round_number = session.event.RoundNumber

    # save the file to s3 
    if progress_callback:
        progress_callback("Uploading to S3...", 95.0)
        
    s3_success = upload_telemetry_to_s3(full_result, year, round_number, frame_skip)
    if s3_success:
        mongo_logger.info(f"Uploaded telemetry to S3 for {event_name}")
    else:
        mongo_logger.error(f"Failed to upload telemetry to S3 for {event_name}")
    
    # Save full resolution to cache with orjson (faster and more compact)
    cache_file = f"{cache_dir}/{event_name}_race_telemetry.json"
    with open(cache_file, "wb") as f:
        f.write(orjson.dumps(full_result, option=orjson.OPT_SERIALIZE_NUMPY))
    
    print(f"Saved Successfully! ({len(frames)} frames)")
    
    # Apply frame skipping for return value
    if frame_skip > 1:
        full_result["frames"] = full_result["frames"][::frame_skip]
        print(f"Applied frame skipping: {frame_skip} (reduced to {len(full_result['frames'])} frames)")
    
    return full_result

