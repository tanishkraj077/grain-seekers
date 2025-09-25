import json
import random
import copy
from datetime import date, timedelta, time

def generate_realistic_beach_data(num_runs, locations_per_run, grains_per_location, center_lat, center_lon, delta_max, beach_id="beachid_default", beach_name="Default Beach"):
    """
    Generates realistic beach data using a purely "chained" algorithm.
    Grain evolution depends only on its previous state and randomized global conditions for the day.
    All directional/zonal logic has been removed.
    """
    # Calculate the min/max latitude and longitude from the center point and delta
    min_lat, max_lat = center_lat - delta_max, center_lat + delta_max
    min_lon, max_lon = center_lon - delta_max, center_lon + delta_max

    # --- NEW: A single set of global tendencies for the entire beach ---
    # These parameters will be slightly randomized each day.
    global_tendency = {
        "mean": 1.0,      # Mean size change factor (1.0 = stable)
        "dev": 0.05,      # Deviation for size change, inducing randomness
        "add_chance": 0.05, # Base chance to add new grains
        "remove_chance": 0.05 # Base chance to remove an existing grain
    }

    # Increased grid resolution for finer tiles
    grid_size_x, grid_size_y = 20, 16
    cell_width = (max_lon - min_lon) / grid_size_x
    cell_height = (max_lat - min_lat) / grid_size_y
    
    print(f"\nGrid cell size: {cell_width:.6f}° x {cell_height:.6f}°")
    print(f"Total area: {(max_lon - min_lon):.6f}° x {(max_lat - min_lat):.6f}°")
    
    all_grid_cells = [(x, y) for x in range(grid_size_x) for y in range(grid_size_y)]

    # --- Step 1: Generate a single master list of locations (zone logic removed) ---
    print("\nGenerating master list of fixed locations...")
    master_locations = []
    num_locations = random.randint(locations_per_run[0], locations_per_run[1])
    locations_per_cell = max(1, num_locations // len(all_grid_cells))
    extra_locations = num_locations % len(all_grid_cells)
    
    random.shuffle(all_grid_cells)

    for cell_index, (cell_x, cell_y) in enumerate(all_grid_cells):
        cell_min_lon = min_lon + cell_x * cell_width
        cell_min_lat = min_lat + cell_y * cell_height
        
        current_cell_locations = locations_per_cell + (1 if cell_index < extra_locations else 0)
        
        for _ in range(current_cell_locations):
            lon = round(random.uniform(cell_min_lon, cell_min_lon + cell_width), 7)
            lat = round(random.uniform(cell_min_lat, cell_min_lat + cell_height), 7)
            # Removed zone assignment. All locations are treated equally.
            master_locations.append({"lat": lat, "lon": lon})

    print(f"Master list created with {len(master_locations)} locations.")
    
    beach_data = {"_id": beach_id, "name": beach_name, "runs": []}
    start_date = date(2025, 9, 21)

    # --- NEW ALGORITHM: Step 2 ---
    # Loop through each run, evolving grain data with randomized global parameters.
    for i in range(num_runs):
        current_date = start_date + timedelta(days=i)
        run_data = {
            "operation_id": f"run_{current_date.strftime('%Y%m%d')}",
            "date": current_date.strftime('%Y-%m-%d'),
            "time": time(random.randint(7, 18), random.randint(0, 59)).strftime('%H:%M'),
            "locations": []
        }
        
        # --- NEW: Daily Global Fluctuations ---
        # Create a unique set of parameters for this specific run (day).
        daily_params = copy.deepcopy(global_tendency)
        daily_params['mean'] += random.uniform(-0.02, 0.02) # e.g., slightly accretive or erosive day
        daily_params['add_chance'] += random.uniform(-0.03, 0.03)
        daily_params['remove_chance'] += random.uniform(-0.03, 0.03)
        
        print(f"Run {i+1}: Processing {len(master_locations)} locations with chained algorithm...")

        for location_index, loc_info in enumerate(master_locations):
            location_data = {"lat": loc_info["lat"], "lon": loc_info["lon"], "grains": []}
            
            if i == 0:
                # FIRST RUN: Create the initial set of grains from scratch.
                num_grains = random.randint(grains_per_location[0], grains_per_location[1])
                for _ in range(num_grains):
                    base_diameter = random.uniform(0.5, 1.5)
                    base_area = random.uniform(0.2, 2.0)
                    location_data["grains"].append({
                        "diameter": abs(round(base_diameter, 5)),
                        "area": abs(round(base_area, 5)),
                    })
            else:
                # SUBSEQUENT RUNS: Evolve grains from the previous day using the daily global params.
                previous_grains = beach_data["runs"][i-1]["locations"][location_index]["grains"]
                
                surviving_grains = []
                # 1. Resize and potentially remove existing grains
                for prev_grain in previous_grains:
                    # Use the single, daily remove_chance for all locations
                    if random.random() > max(0, daily_params["remove_chance"]): 
                        change_factor = random.uniform(daily_params["mean"] - daily_params["dev"], daily_params["mean"] + daily_params["dev"])
                        new_diameter = prev_grain["diameter"] * change_factor
                        new_area = prev_grain["area"] * change_factor
                        surviving_grains.append({
                            "diameter": abs(round(new_diameter, 5)),
                            "area": abs(round(new_area, 5)),
                        })
                
                # 2. Potentially add new grains (accretion)
                if random.random() < max(0, daily_params["add_chance"]):
                    num_new_grains = random.randint(1, 7) 
                    for _ in range(num_new_grains):
                        base_diameter = random.uniform(0.5, 1.5)
                        base_area = random.uniform(0.2, 2.0)
                        surviving_grains.append({
                            "diameter": abs(round(base_diameter, 5)),
                            "area": abs(round(base_area, 5)),
                        })

                location_data["grains"] = surviving_grains

            run_data["locations"].append(location_data)
        
        beach_data["runs"].append(run_data)

    return beach_data

if __name__ == "__main__":
    input_valid = False
    beach_info = {}

    print("Please paste the beach information in JSON format and press Enter twice.")
    print("Example:")
    print("""{
  "_id": "beachid444987",
  "name": "black orange",
  "lat": 12.35678,
  "lon": 77.13456
}""")
    print("-" * 20)

    # Loop until valid JSON input is received
    while not input_valid:
        try:
            # Read multi-line input from the user
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            json_input = "".join(lines)
            
            beach_info = json.loads(json_input)
            
            # Check for required keys
            if all(k in beach_info for k in ("_id", "name", "lat", "lon")):
                input_valid = True
            else:
                print("Invalid JSON: Missing one of the required keys (_id, name, lat, lon). Please try again.")

        except json.JSONDecodeError:
            print("Invalid JSON format. Please paste the JSON object correctly.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Please try again.")

    # Static configuration for the data generation process
    config = {
        "num_runs": 5,
        "locations_per_run": (2000, 3000),
        "grains_per_location": (5, 20),
        "delta_max": 0.0025, # Defines the geographic spread around the center point
    }

    # Combine user input with the static configuration
    generation_params = {
        "beach_id": beach_info["_id"],
        "beach_name": beach_info["name"],
        "center_lat": beach_info["lat"],
        "center_lon": beach_info["lon"],
        **config
    }

    print("\nStarting data generation with the following configuration:")
    print(json.dumps(generation_params, indent=2, sort_keys=True))

    # Generate the data
    generated_data = generate_realistic_beach_data(**generation_params)
    output_filename = f"{generation_params['beach_id']}_data.json"

    # Save the data to a file
    with open(output_filename, 'w') as f:
        json.dump(generated_data, f, indent=2)

    print(f"\nSuccessfully generated fine-grid data and saved it to '{output_filename}'")
    
    # Calculate and print final statistics
    total_locations = sum(len(run["locations"]) for run in generated_data["runs"])
    total_grains = sum(len(loc["grains"]) for run in generated_data["runs"] for loc in run["locations"])
    
    print("\n--- Summary ---")
    print(f"Total runs: {len(generated_data['runs'])}")
    print(f"Total locations generated: {total_locations}")
    print(f"Total grains generated: {total_grains}")
    if generated_data['runs']:
        print(f"Average locations per run: {total_locations / len(generated_data['runs']):.1f}")
    print("--- End of Summary ---")

