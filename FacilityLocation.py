import streamlit as st
import gurobipy as gp
from gurobipy import GRB
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
from itertools import product

# Function to compute Euclidean distance
def compute_distance(loc1, loc2):
    dx = loc1[0] - loc2[0]
    dy = loc1[1] - loc2[1]
    return sqrt(dx * dx + dy * dy)

# Function to solve the Facility Location Problem
def solve_facility_location(customers, facilities, setup_cost, cost_per_mile):
    num_facilities = len(facilities)
    num_customers = len(customers)
    cartesian_prod = list(product(range(num_customers), range(num_facilities)))

    # Compute shipping costs
    shipping_cost = {(c, f): cost_per_mile * compute_distance(customers[c], facilities[f]) for c, f in cartesian_prod}

    # MIP Model formulation
    m = gp.Model('facility_location')

    # Decision Variables
    select = m.addVars(num_facilities, vtype=GRB.BINARY, name='Select')
    assign = m.addVars(cartesian_prod, ub=1, vtype=GRB.CONTINUOUS, name='Assign')

    # Constraints
    m.addConstrs((assign[(c, f)] <= select[f] for c, f in cartesian_prod), name='Setup2ship')
    m.addConstrs((gp.quicksum(assign[(c, f)] for f in range(num_facilities)) == 1 for c in range(num_customers)), name='Demand')

    # Objective Function: Minimize total costs
    m.setObjective(select.prod(setup_cost) + assign.prod(shipping_cost), GRB.MINIMIZE)

    # Optimize model
    m.optimize()

    # Process results
    selected_facilities = [f for f in range(num_facilities) if abs(select[f].x) > 1e-6]
    shipments = {(c, f): assign[c, f].x for c, f in cartesian_prod if abs(assign[c, f].x) > 1e-6}

    return selected_facilities, shipments

# Function to plot facilities and supermarkets
def plot_facilities_and_supermarkets(customers, facilities, selected_facilities, shipments):
    plt.figure(figsize=(10, 6))

    # Plot supermarkets
    customer_x, customer_y = zip(*customers)
    plt.scatter(customer_x, customer_y, c='blue', label='Supermarkets', s=100, edgecolors='black')

    # Plot facilities
    facility_x, facility_y = zip(*facilities)
    plt.scatter(facility_x, facility_y, c='red', label='Candidate Facilities', s=150, marker='^', edgecolors='black')

    # Highlight selected facilities
    for idx in selected_facilities:
        plt.scatter(facility_x[idx], facility_y[idx], c='green', s=200, marker='^', edgecolors='black', label='Selected Facility')

    # Draw lines for shipments
    for (customer, facility), fraction in shipments.items():
        if fraction > 0:
            plt.plot(
                [customer_x[customer], facility_x[facility]],
                [customer_y[customer], facility_y[facility]],
                c='gray', linestyle='--', linewidth=0.7
            )

    plt.title("Facility Location Optimization")
    plt.xlabel("X-coordinate")
    plt.ylabel("Y-coordinate")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(plt)

# Main Streamlit app
def main():
    st.set_page_config(page_title="Facility Location Optimization", layout="wide")

    st.markdown("<h1 style='text-align: center;'>Facility Location Optimization</h1>", unsafe_allow_html=True)

    # Add instructions and methodology sections
    st.header("ℹ️ Instructions")
    with st.expander("📃 Guide d'Utilisation"):
        st.write("""
        - *Number of Customers*: Define how many customers you want to optimize for.
        - *Number of Facilities*: Set the number of facilities to choose from.
        - *Facility Setup Costs*: Define the setup cost for each facility.
        - *Cost Per Mile*: Define the transportation cost between a customer and facility.
        - *Solve*: Click 'Solve' to compute the optimal facility selection and shipment distribution.
        """)

    with st.expander("🧮 Méthodologie"):
        st.write("""
        - This problem is modeled as a *Mixed-Integer Programming* (MIP) problem.
        - The objective is to *minimize total costs* by optimizing facility selection and customer allocation.
        - The solution is computed using the *Gurobi solver* to find the optimal facility locations and shipment plans.
        """)

    with st.expander("🔧 Notes Techniques"):
        st.write("- The Gurobi solver is required to run this application.")
        st.write("- The results are displayed graphically for better visualization.")
        st.write("- Click on the 'Solve' button after providing the input parameters.")

    # Sidebar inputs for number of customers and facilities
    st.sidebar.header("Input Parameters")

    # Number of customers
    num_customers = st.sidebar.number_input("Number of Customers", min_value=1, value=2, step=1)
    customers = []
    for i in range(num_customers):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            customer_x = st.number_input(f"Customer {i+1} X-coordinate", value=np.random.uniform(-50, 50))
        with col2:
            customer_y = st.number_input(f"Customer {i+1} Y-coordinate", value=np.random.uniform(-50, 50))
        customers.append((customer_x, customer_y))

    # Number of facilities
    num_facilities = st.sidebar.number_input("Number of Facilities", min_value=1, value=5, step=1)
    facilities = []
    setup_cost = []
    for i in range(num_facilities):
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            facility_x = st.number_input(f"Facility {i+1} X-coordinate", value=np.random.uniform(-50, 50))
        with col2:
            facility_y = st.number_input(f"Facility {i+1} Y-coordinate", value=np.random.uniform(-50, 50))
        with col3:
            facility_cost = st.number_input(f"Facility {i+1} Setup Cost", value=10)
        facilities.append((facility_x, facility_y))
        setup_cost.append(facility_cost)

    # Cost per mile
    cost_per_mile = st.sidebar.number_input("Cost Per Mile", min_value=0.0, value=1.0)

    # Solve the problem when the button is pressed
    if st.sidebar.button("Solve"):
        selected_facilities, shipments = solve_facility_location(customers, facilities, setup_cost, cost_per_mile)

        st.subheader("Optimization Results")
        st.write("### Selected Facilities:")
        for facility in selected_facilities:
            st.write(f"Facility {facility + 1}")

        st.write("### Shipment Plan:")
        for (customer, facility), fraction in shipments.items():
            st.write(f"Customer {customer + 1} is served {round(100 * fraction, 2)}% by Facility {facility + 1}")

        # Visualization
        plot_facilities_and_supermarkets(customers, facilities, selected_facilities, shipments)

if __name__ == "__main__":
    main()
