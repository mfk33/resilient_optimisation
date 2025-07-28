"""
Transport Network Disruption Analysis - Main Execution Script

This script implements a comprehensive simulation framework to evaluate the impact of 
various disruption scenarios on maritime transport network optimization. The analysis 
examines cost implications and network resilience under different operational constraints.

Author: Mohammed Faisal Khan
Institution: University of Cambridge
Date: 28/07/2025

Methodology:
- Multi-scenario optimization using Gurobi solver
- Baseline cost comparison analysis
- Statistical deviation assessment
- Automated result visualization

For replication of this research:
1. Ensure all model_data_DS*.py files are present in the same directory
2. Install required dependencies: pandas, matplotlib, gurobipy
3. Execute this script to run all disruption scenarios
4. Results will be saved as CSV and PNG files for further analysis
"""

import importlib
import pandas as pd
import matplotlib.pyplot as plt
from optimization_solver import solve_transport_model

# Research Parameters
# Define the range of disruption scenarios to analyze
# Scenarios 1-15 represent different operational constraints and network disruptions
scenarios_to_run = range(1, 16)

# Data file naming convention for scenario modules
data_file_basename = "model_data_DS"

# Baseline reference value for cost deviation analysis
# This represents the optimal cost per ton under normal operating conditions found by running the optimisation function for mode_data (which contains the baseline parameters) 
baseline_cost_per_ton = 61.18

# Initialize results collection for statistical analysis
all_results = []

print("=== Transport Network Disruption Analysis Initiated ===")

# Execute simulation across all defined scenarios
for i in scenarios_to_run:
    # Generate scenario identifier following established naming convention
    scenario_name = f"{data_file_basename}{i:02d}"
    
    print(f"\n--- Executing Scenario {scenario_name} ---")

    try:
        # Dynamic module import for scenario-specific data
        scenario_data = importlib.import_module(scenario_name)
        print(f"Data module {scenario_name}.py loaded successfully.")

        # Execute optimization model for current scenario
        result = solve_transport_model(scenario_data)
        
        # Calculate cost efficiency metrics for comparative analysis
        total_cost = result.get('total_cost')
        total_tonnage = result.get('total_tonnage_shipped')
        
        if total_cost is not None and total_tonnage is not None and total_tonnage > 1e-6:
            result['cost_per_ton'] = total_cost / total_tonnage
        else:
            result['cost_per_ton'] = None  # Handle edge cases with minimal tonnage
        
        all_results.append(result)
        print(f"Scenario {scenario_name} completed. Status: {result.get('status')}, Total Cost: ${result.get('total_cost', 'N/A'):,.2f}")

    except ImportError:
        print(f"Data file not found: {scenario_name}.py - Scenario excluded from analysis.")
    except Exception as e:
        print(f"Error in scenario {scenario_name}: {e}")

# Compile and analyze simulation results
print("\n=== Simulation Analysis Complete ===")

if all_results:
    # Create structured dataset for statistical analysis
    results_df = pd.DataFrame(all_results)
    
    # Calculate percentage deviation from baseline for resilience assessment
    if 'cost_per_ton' in results_df.columns:
        results_df['deviation_pct'] = ((results_df['cost_per_ton'] - baseline_cost_per_ton) / baseline_cost_per_ton) * 100
    
    # Organize output columns for clarity and analysis
    desired_columns = [
        'scenario', 'status', 'total_cost', 
        'total_tonnage_shipped', 'cost_per_ton', 'deviation_pct', 'computation_time_sec'
    ]
    existing_columns = [col for col in desired_columns if col in results_df.columns]
    results_df = results_df[existing_columns]

    print("\n=== Comprehensive Results Summary ===")
    print(results_df.round(2))

    # Export results for external analysis and reproducibility
    try:
        results_df.to_csv("simulation_results_summary.csv", index=False, float_format='%.2f')
        print("\nResults exported to simulation_results_summary.csv for further analysis")
    except Exception as e:
        print(f"\nExport error: {e}")
        
    # Generate visualization outputs for research presentation
    print("\nGenerating analytical visualizations...")
    try:
        # Filter for valid optimization results
        plot_df = results_df.dropna(subset=['total_cost', 'cost_per_ton'])
        
        if not plot_df.empty:
            # Figure 1: Cost Analysis Across Scenarios
            fig1, ax1 = plt.subplots(figsize=(14, 8))
            ax1.set_title("Transport Cost Analysis: Total Cost and Unit Cost by Scenario", fontsize=16, fontweight='bold')
            ax1.set_xlabel("Disruption Scenario", fontsize=12)
            ax1.set_ylabel("Total Transportation Cost ($)", fontsize=12, color='tab:blue')
            ax1.bar(plot_df['scenario'], plot_df['total_cost'], color='tab:blue', alpha=0.7, label='Total Cost')
            ax1.tick_params(axis='y', labelcolor='tab:blue')
            ax1.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            plt.xticks(rotation=45, ha='right')
            ax2 = ax1.twinx()
            ax2.set_ylabel("Cost per Ton ($/ton)", fontsize=12, color='tab:red')
            ax2.plot(plot_df['scenario'], plot_df['cost_per_ton'], color='tab:red', marker='o', linestyle='--', label='Cost per Ton')
            ax2.tick_params(axis='y', labelcolor='tab:red')
            ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.2f}'))
            fig1.tight_layout()
            plot1_filename = "simulation_results_plot.png"
            plt.savefig(plot1_filename, dpi=300, bbox_inches='tight')
            print(f"Cost analysis visualization saved as {plot1_filename}")
            plt.close(fig1)

            # Figure 2: Baseline Deviation Analysis
            if 'deviation_pct' in plot_df.columns:
                fig2, ax = plt.subplots(figsize=(14, 8))
                
                # Color coding: red for cost increases, green for cost decreases
                colors = ['#d62728' if x > 0 else '#2ca02c' for x in plot_df['deviation_pct']]
                
                bars = ax.bar(plot_df['scenario'], plot_df['deviation_pct'], color=colors)
                
                # Reference line at baseline (0% deviation)
                ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
                
                ax.set_title(f"Cost Deviation from Baseline Optimal Solution (${baseline_cost_per_ton}/ton)", fontsize=16, fontweight='bold')
                ax.set_xlabel("Disruption Scenario", fontsize=12)
                ax.set_ylabel("Percentage Deviation from Baseline (%)", fontsize=12)
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
                
                # Annotate bars with exact deviation values
                for bar in bars:
                    yval = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.1f}%', 
                           va='bottom' if yval >=0 else 'top', ha='center')

                plt.xticks(rotation=45, ha='right')
                fig2.tight_layout()
                plot2_filename = "simulation_deviation_plot.png"
                plt.savefig(plot2_filename, dpi=300, bbox_inches='tight')
                print(f"Deviation analysis visualization saved as {plot2_filename}")
                plt.close(fig2)
            
        else:
            print("No valid optimization results available for visualization.")

    except Exception as e:
        print(f"Visualization generation error: {e}")
        
else:
    print("No scenarios completed successfully. Please check data files and model parameters.")
