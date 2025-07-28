# resilient_optimisation
Code and models from my MPhil thesis at the University of Cambridge on optimising UK–India scrap metal supply chains using a MILP framework. Focuses on routing, mode selection (bulk vs container), fuel stops, and intermodal transfers. Built with Python and Gurobi.
# Resilient Optimisation of UK–India Scrap Metal Supply Chains

This repository contains the code, mathematical model, and data used in my MPhil dissertation submitted to the University of Cambridge as part of the Industrial Systems, Manufacture and Management programme (2024–25 cohort).

## 📘 Project Overview

The research focuses on modelling the monthly transportation of scrap metal from 8 UK ports to 3 Indian ports using bulk and container shipping modes. The model minimises total logistics cost while accounting for:

- Mode and route selection (bulk vs container)
- Optional fuel stops for bulk shipping
- Time-based interest costs
- Handling and port fees for container modes (via Suez or Cape routes)
- Inter-port rail transfer within India

The model is implemented as a Mixed-Integer Linear Program (MILP) using Python and Gurobi.

## 🧠 Research Objectives

- Optimise total transportation and interest costs over a multi-modal network
- Test the model’s response to disruptions (fuel cost spikes, port closures, etc.)
- Explore how different routing strategies impact resilience and delivery time

## 🧰 Tech Stack

- **Language:** Python 3.11
- **Solver:** Gurobi Optimizer
- **Libraries:** `pandas`, `numpy`, `gurobipy`, `matplotlib`

## 📁 Repository Structure

```bash
├── data/                   # Raw and cleaned data files of the baseline and disruption scenarios
├── optimization_solver/    # Converts the MILP model to python code which uses Gurobi to solve it
├── wrapper function/       # Resilience evaluation function
├── README.md

