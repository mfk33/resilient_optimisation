"""
Transport Network Optimization Solver - Gurobi Implementation

This module implements a mixed-integer linear programming (MILP) model for maritime 
transport network optimization under disruption scenarios. The model considers 
container shipping, bulk shipping, and rail transport modes with capacity, time, 
and cost constraints.

Author: Mohammed Faisal Khan
Institution: University of Cambridge
Date: 28/07/2025

Mathematical Formulation:
- Objective: Minimize total transportation cost
- Decision Variables: Shipment quantities, vessel counts, route selection
- Constraints: Demand fulfillment, capacity limits, time thresholds, vessel availability

Dependencies:
- gurobipy: Commercial optimization solver
- itertools: Efficient iteration utilities

For research replication:
1. Ensure Gurobi license is properly configured
2. Verify all data parameters are correctly defined in scenario modules
3. Check constraint formulations match the mathematical model specification
"""

import gurobipy as gp
from gurobipy import GRB
import itertools

def solve_transport_model(data):
    """
    Constructs and solves the transportation optimization model for a given scenario.
    
    Parameters:
    -----------
    data : module
        Scenario-specific data module containing all model parameters
        
    Returns:
    --------
    dict
        Optimization results including status, total cost, computation time, 
        and total tonnage shipped
        
    Mathematical Components:
    - Decision variables for container, bulk, and rail transport
    - Cost components: shipping, vessel, toll, time, charter, fuel
    - Constraints: demand fulfillment, capacity, time thresholds, vessel availability
    """
    try:
        # Initialize Gurobi optimization environment with license
        env = gp.Env(empty=True)
        env.setParam('WLSACCESSID', '####')
        env.setParam('WLSSECRET', '####')
        env.setParam('LICENSEID', '####')
        env.start()
        model = gp.Model(f"TransportationOptimization_{data.__name__}", env=env)
        print(f"Gurobi model initialized for scenario {data.__name__}.")

        # Define index sets for mathematical formulation
        # Container routes: (sink, path) combinations
        container_sea_routes = [(s, p) for s in data.sinks for p in data.paths]
        # Bulk routes: (sink, path, fuel_stops) combinations  
        bulk_sea_routes = [(s, p, k) for s in data.sinks for p in data.paths for k in data.fuel_stops]
        # Rail routes: (origin_sink, destination_sink) pairs
        rail_routes = [(s_i, s_j) for s_i in data.sinks for s_j in data.sinks if s_i != s_j]

        # Define decision variables for the mathematical model
        # Container shipping variables
        QC = model.addVars(container_sea_routes, vtype=GRB.CONTINUOUS, name="QC")  # Quantity shipped
        NC = model.addVars(container_sea_routes, vtype=GRB.INTEGER, name="NC")     # Number of vessels
        yC = model.addVars(container_sea_routes, vtype=GRB.BINARY, name="yC")      # Route selection

        # Bulk shipping variables
        QB = model.addVars(bulk_sea_routes, vtype=GRB.CONTINUOUS, name="QB")       # Quantity shipped
        NB = model.addVars(bulk_sea_routes, vtype=GRB.INTEGER, name="NB")          # Number of vessels
        yB = model.addVars(bulk_sea_routes, vtype=GRB.BINARY, name="yB")           # Route selection

        # Rail transport variables
        QR = model.addVars(rail_routes, vtype=GRB.CONTINUOUS, name="QR")           # Quantity shipped
        yR = model.addVars(rail_routes, vtype=GRB.BINARY, name="yR")               # Route selection
        
        model.update()

        # Construct objective function: minimize total transportation cost
        # Container shipping cost component
        cost_container_shipping = gp.quicksum(
            QC[s, p] * data.container_shipping_cost.get((s, p), 0)
            for s, p in container_sea_routes
        )
        # Container vessel operating cost
        cost_container_vessel = gp.quicksum(
            NC[s, p] * data.CostPerContainerShipVoyage
            for s, p in container_sea_routes
        )
        # Suez Canal toll charges for container and bulk vessels
        suez_path_identifier = 'Suez'
        cost_suez_toll_container = gp.quicksum(NC[s, suez_path_identifier] for s in data.sinks) * data.Toll_Suez_Container
        cost_suez_toll_bulk = gp.quicksum(NB[s, suez_path_identifier, k] for s in data.sinks for k in data.fuel_stops) * data.Toll_Suez_Bulk
        cost_suez_toll = cost_suez_toll_container + cost_suez_toll_bulk
        
        # Cape route time cost (opportunity cost of extended transit time)
        cape_path_identifier = 'Cape'
        cost_time_cape = (
            gp.quicksum(
                QC[s, cape_path_identifier] * data.add_days_cape_container.get((s, cape_path_identifier), 0) * data.R_interest * data.CostScrapMetal
                for s in data.sinks if (s, cape_path_identifier) in QC
            ) +
            gp.quicksum(
                QB[s, cape_path_identifier, k] * data.add_days_cape_bulk_0_stops.get((s, cape_path_identifier), 0) * data.R_interest * data.CostScrapMetal
                for s in data.sinks for k in data.fuel_stops if (s, cape_path_identifier, k) in QB
            )
        )
        # Bulk vessel charter costs
        cost_charter_bulk = gp.quicksum(
            NB[s, p, k] * (data.base_bulk_travel_time_0_stops.get((s,p), 0) + k * data.AddedDays_stop) * data.DailyCharterRateB
            for s, p, k in bulk_sea_routes
        )
        # Bulk vessel fuel costs
        cost_fuel_bulk = gp.quicksum(
            NB[s, p, k] * (data.base_bulk_fuel_cost.get((s, p), 0) + k * data.CostFuel_stop)
            for s, p, k in bulk_sea_routes
        )
        
        # Time cost for fuel stops (opportunity cost of additional transit time)
        cost_time_fuel_stops_bulk = gp.quicksum(
            QB[s, p, k] * k * data.AddedDays_stop * data.R_interest * data.CostScrapMetal
            for s, p, k in bulk_sea_routes
        )
        
        # Rail transport costs
        cost_rail_transport = gp.quicksum(
            QR[s_i, s_j] * data.rail_cost.get((s_i, s_j), 0)
            for s_i, s_j in rail_routes
        )
        
        # Total objective function: sum of all cost components
        total_transportation_cost = (
            cost_container_shipping + cost_container_vessel + cost_suez_toll +
            cost_time_cape + cost_charter_bulk + cost_fuel_bulk +
            cost_time_fuel_stops_bulk + cost_rail_transport
        )
        model.setObjective(total_transportation_cost, GRB.MINIMIZE)

        # Implement mathematical constraints for the optimization model
        
        # Demand fulfillment constraints: ensure all demand at each sink is satisfied
        for s_j in data.sinks:
            inflow_sea_to_sj = (gp.quicksum(QC.get((s_j, p), 0) for p in data.paths) +
                                gp.quicksum(QB.get((s_j, p, k), 0) for p in data.paths for k in data.fuel_stops))
            inflow_rail_to_sj = gp.quicksum(QR.get((s_i, s_j), 0) for s_i in data.sinks if s_i != s_j)
            outflow_rail_from_sj = gp.quicksum(QR.get((s_j, s_k), 0) for s_k in data.sinks if s_k != s_j)
            model.addConstr(inflow_sea_to_sj + inflow_rail_to_sj - outflow_rail_from_sj == data.demands.get(s_j, 0),
                            name=f"DemandFulfillment[{s_j}]")
        
        # Vessel capacity constraints for container ships
        for s, p in container_sea_routes:
            model.addConstr(NC[s, p] * data.CapC_ship >= QC[s, p], name=f"ContainerShipCapacity[{s},{p}]")
        
        # Vessel capacity constraints for bulk ships (with fuel stop adjustments)
        for s, p, k_stops in bulk_sea_routes:
            effective_bulk_capacity = data.base_bulk_capacity.get((s, p), 0) + k_stops * data.DeltaCapB_stop.get((s, p), 0)
            if effective_bulk_capacity > 0:
                model.addConstr(NB[s, p, k_stops] * effective_bulk_capacity >= QB[s, p, k_stops],
                                name=f"BulkShipCapacity[{s},{p},{k_stops}]")
            else:
                model.addConstr(QB[s, p, k_stops] == 0, name=f"ZeroCapBulkForceOff[{s},{p},{k_stops}]")
        
        # Logical constraints linking continuous and binary variables
        for s, p in container_sea_routes:
            model.addConstr(QC[s, p] <= data.M * yC[s, p], name=f"Link_QC_yC[{s},{p}]")
            model.addConstr(NC[s, p] <= data.M * yC[s, p], name=f"Link_NC_yC[{s},{p}]")
        for s, p, k in bulk_sea_routes:
            model.addConstr(QB[s, p, k] <= data.M * yB[s, p, k], name=f"Link_QB_yB[{s},{p},{k}]")
            model.addConstr(NB[s, p, k] <= data.M * yB[s, p, k], name=f"Link_NB_yB[{s},{p},{k}]")
        for s_i, s_j in rail_routes:
            model.addConstr(QR[s_i, s_j] <= data.M * yR[s_i, s_j], name=f"Link_QR_yR[{s_i},{s_j}]")
        
        # Fuel stop selection constraints: only one fuel stop configuration per route
        for s in data.sinks:
            for p in data.paths:
                model.addConstr(gp.quicksum(yB[s, p, k_stops] for k_stops in data.fuel_stops) <= 1, name=f"UniqueFuelStopChoice[{s},{p}]")
        
        # Route capacity constraints for container shipping
        for s, p in container_sea_routes:
            model.addConstr(QC[s, p] <= data.max_container_tonnage_route.get((s, p), 0), name=f"ContainerRouteCapacity[{s},{p}]")
        
        # Time threshold constraints: exclude routes exceeding maximum acceptable transit time
        for s, p in container_sea_routes:
            if data.container_travel_time.get((s, p), float('inf')) > data.TimeThreshold:
                model.addConstr(yC[s, p] == 0, name=f"TravelTime_Leg_Container_ForceOff[{s},{p}]")
        for s, p, k in bulk_sea_routes:
            if (data.base_bulk_travel_time_0_stops.get((s, p), float('inf')) + k * data.AddedDays_stop) > data.TimeThreshold:
                 model.addConstr(yB[s, p, k] == 0, name=f"TravelTime_Leg_Bulk_ForceOff[{s},{p},{k}]")
        for s_i, s_j in rail_routes:
            if data.rail_time.get((s_i, s_j), float('inf')) > data.TimeThreshold:
                model.addConstr(yR[s_i, s_j] == 0, name=f"TravelTime_Leg_Rail_ForceOff[{s_i},{s_j}]")
        
        # Port handling capacity constraints
        for s in data.sinks:
            model.addConstr(gp.quicksum(QC[s, p] for p in data.paths) <= data.container_handling_capacity.get(s, 0), name=f"SinkContainerHandling[{s}]")
            model.addConstr(gp.quicksum(QB[s, p, k] for p in data.paths for k in data.fuel_stops) <= data.bulk_handling_capacity.get(s, 0), name=f"SinkBulkHandling[{s}]")
        
        # Global vessel availability constraint for bulk ships
        if hasattr(data, 'N_ships_availB') and data.N_ships_availB is not None and data.N_ships_availB > 0 :
            model.addConstr(gp.quicksum(NB[s,p,k] for s,p,k in bulk_sea_routes) <= data.N_ships_availB, name="GlobalBulkShipAvailability")
        
        model.update()

        # Execute optimization using Gurobi solver
        print("Executing optimization algorithm...")
        model.optimize()

        # Extract and compile optimization results for analysis
        results = {'scenario': data.__name__}
        if model.status == GRB.OPTIMAL:
            results['status'] = 'Optimal'
            results['total_cost'] = model.objVal
            
            # Record computational performance metrics
            results['computation_time_sec'] = model.Runtime
            
            # Calculate total tonnage shipped across all transport modes
            total_sea_tonnage = sum(QC[s, p].X for s, p in container_sea_routes) + \
                                sum(QB[s, p, k].X for s, p, k in bulk_sea_routes)
            results['total_tonnage_shipped'] = total_sea_tonnage
            
        else:
            results['status'] = f'Status {model.status}'
            results['total_cost'] = None
            results['computation_time_sec'] = model.Runtime
            results['total_tonnage_shipped'] = 0

        return results

    except gp.GurobiError as e:
        print(f"Gurobi optimization error in {data.__name__}: {e}")
        return {'scenario': data.__name__, 'status': 'Gurobi Error', 'total_cost': None}
    except Exception as e:
        print(f"Computational error in {data.__name__}: {e}")
        return {'scenario': data.__name__, 'status': 'Python Error', 'total_cost': None}
