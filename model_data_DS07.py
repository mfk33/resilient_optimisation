
# model_data.py
# Input parameters for the maritime supply chain optimization model

# 1. Defining the Sets ---
sinks = ['Mundra', 'Mumbai', 'Chennai']
paths = ['Suez', 'Cape'] # Primary sea paths
fuel_stops = [0, 1, 2, 3] # k = 0 means no stops

# 2. Global Parameters ---

TimeThreshold = 60  # days, maximum allowable travel time for any single leg
Toll_Suez_Container = 8500 # monetary units, cost for one container ship transit via Suez
Toll_Suez_Bulk = 224000      # monetary units, cost for one bulk ship transit via Suez
DailyCharterRateB = 33000 # monetary units, cost per day to charter one bulk ship
CostScrapMetal = 300 # MOnetary units per metric ton 
AddedDays_stop = 2 # days, time added to journey per fuel stop for bulk ships
CostFuel_stop = 35000 # monetary units, extra fuel cost per fuel stop for bulk ships
R_interest = 0.00032 # daily interest rate for commodity value (e.g., 0.032%)
CostPerContainerShipVoyage = 100 # monetary units, cost per ton of scrap in container ship voyage
N_ships_availB = 5 # Optional: Maximum number of bulk ships available from Immingham

# Container ship capacity (assuming one type for simplicity)
CapC_ship = 10000 # tons, weight capacity of one container ship

# Generic Big M value (refine this based on specific constraint needs if possible)
M = 1000000 # A sufficiently large number

# --- 3. Parameters Indexed by Sink Node (s) ---

# D_s: Monthly demand at sink port s (metric tons)
demands = {
    'Mundra': 30000,
    'Mumbai': 30000,
    'Chennai': 40000
}

# HandleCap_C_s: Container handling capacity at sink s (metric tons/month)
container_handling_capacity = {
    'Mundra': 300000,
    'Mumbai': 300000,
    'Chennai': 300000
}

# HandleCap_B_s: Bulk handling capacity at sink s (metric tons/month)
bulk_handling_capacity = {
    'Mundra': 20000,
    'Mumbai': 20000,
    'Chennai': 20000
}

# --- 4. Parameters for Container Mode (London Gateway to s via p) ---
# Keys are tuples (sink, path)

# TcostM_s_p: Shipping cost per metric ton for container mode
container_shipping_cost = {
    ('Mundra', 'Suez'): 100, ('Mundra', 'Cape'): 110,
    ('Mumbai', 'Suez'): 110, ('Mumbai', 'Cape'): 120,
    ('Chennai', 'Suez'): 130, ('Chennai', 'Cape'): 140
}

# MaxTonC_s_p: Max container tonnage per month on route (s,p)
max_container_tonnage_route = {
    ('Mundra', 'Suez'): 50000, ('Mundra', 'Cape'): 50000,
    ('Mumbai', 'Suez'): 40000, ('Mumbai', 'Cape'): 40000,
    ('Chennai', 'Suez'): 20000, ('Chennai', 'Cape'): 20000
}

# TimeC_s_p: Container travel time in days
container_travel_time = {
    ('Mundra', 'Suez'): 30, ('Mundra', 'Cape'): 50,
    ('Mumbai', 'Suez'): 32, ('Mumbai', 'Cape'): 52,
    ('Chennai', 'Suez'): 35, ('Chennai', 'Cape'): 55
}

# AddDaysC_s_Cape: Additional days for Cape route (Container) vs Suez
# Calculated for consistency, or can be provided directly
add_days_cape_container = {}
for s_node in sinks:
    if (s_node, 'Cape') in container_travel_time and (s_node, 'Suez') in container_travel_time:
        add_days_cape_container[(s_node, 'Cape')] = container_travel_time[(s_node, 'Cape')] - container_travel_time[(s_node, 'Suez')]
    else: # Should not happen if data is complete
        add_days_cape_container[(s_node, 'Cape')] = 0


# --- 5. Parameters for Bulk Mode (Immingham to s via p, with k stops) ---
# Keys are tuples (sink, path) for route-specific base values

# CapB_base_s_p: Base bulk capacity (0 stops) for route (s,p) in tons
# This value accounts for fuel needed for this specific base journey
base_bulk_capacity = {
    ('Mundra', 'Suez'): 55000, ('Mundra', 'Cape'): 45000,
    ('Mumbai', 'Suez'): 54900, ('Mumbai', 'Cape'): 44900,
    ('Chennai', 'Suez'): 50000, ('Chennai', 'Cape'): 40000
}

# DeltaCapB_stop_s,p: Increase in bulk ship capacity per fuel stop for route (s,p)
DeltaCapB_stop = {
    ('Mundra', 'Suez'): 100, ('Mundra', 'Cape'): 200,
    ('Mumbai', 'Suez'): 90, ('Mumbai', 'Cape'): 190,
    ('Chennai', 'Suez'): 80, ('Chennai', 'Cape'): 180
}


# CostFuelB_s_p: Base fuel cost for bulk ship on route (s,p)
base_bulk_fuel_cost = {
    ('Mundra', 'Suez'): 100000, ('Mundra', 'Cape'): 110000,
    ('Mumbai', 'Suez'): 105000, ('Mumbai', 'Cape'): 115000,
    ('Chennai', 'Suez'): 110000, ('Chennai', 'Cape'): 120000
}

# TimeB_s_p_0: Base bulk travel time (0 stops) in days for route (s,p)
base_bulk_travel_time_0_stops = {
    ('Mundra', 'Suez'): 20, ('Mundra', 'Cape'): 35,
    ('Mumbai', 'Suez'): 22, ('Mumbai', 'Cape'): 37,
    ('Chennai', 'Suez'): 25, ('Chennai', 'Cape'): 40
}

# AddDaysB_s_Cape: Additional days for Cape route (Bulk, 0 stops) vs Suez (0 stops)
# Calculated for consistency
add_days_cape_bulk_0_stops = {}
for s_node in sinks:
    if (s_node, 'Cape') in base_bulk_travel_time_0_stops and (s_node, 'Suez') in base_bulk_travel_time_0_stops:
        add_days_cape_bulk_0_stops[(s_node, 'Cape')] = base_bulk_travel_time_0_stops[(s_node, 'Cape')] - base_bulk_travel_time_0_stops[(s_node, 'Suez')]
    else: # Should not happen
        add_days_cape_bulk_0_stops[(s_node, 'Cape')] = 0

# --- 6. Parameters for Rail Transport (between sink si and sink sj) ---
# Keys are tuples (sink_from, sink_to)

rail_cost = {} # Cost per metric ton
rail_time = {} # Time in days

# Populate rail data - ensure all si != sj combinations you want to allow are covered
# Example:
# Mundra <-> Mumbai
rail_cost[('Mundra', 'Mumbai')] = 4
rail_time[('Mundra', 'Mumbai')] = 2
rail_cost[('Mumbai', 'Mundra')] = 4 # Costs can be asymmetric
rail_time[('Mumbai', 'Mundra')] = 2

# Mundra <-> Chennai
rail_cost[('Mundra', 'Chennai')] = 20
rail_time[('Mundra', 'Chennai')] = 4
rail_cost[('Chennai', 'Mundra')] = 20
rail_time[('Chennai', 'Mundra')] = 4

# Mumbai <-> Chennai
rail_cost[('Mumbai', 'Chennai')] = 15
rail_time[('Mumbai', 'Chennai')] = 3
rail_cost[('Chennai', 'Mumbai')] = 15
rail_time[('Chennai', 'Mumbai')] = 3



print("model_data.py loaded successfully (example print statement)")
if __name__ == '__main__':
    # Example of accessing some data
    print(f"Demand at Mundra: {demands['Mundra']}")
    print(f"Container shipping cost Mundra to Suez: {container_shipping_cost[('Mundra', 'Suez')]}")
    print(f"Base bulk capacity Mundra to Suez: {base_bulk_capacity[('Mundra', 'Suez')]}")
    print(f"Rail cost Mundra to Mumbai: {rail_cost.get(('Mundra', 'Mumbai'), 'N/A')}")
    print(f"Additional days for Cape route (Container) to Mundra: {add_days_cape_container.get(('Mundra', 'Cape'), 'N/A')}")