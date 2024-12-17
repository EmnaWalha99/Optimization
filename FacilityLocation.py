import streamlit as st
import gurobipy as gp
from gurobipy import GRB
from math import sqrt
from itertools import product

# Function to compute Euclidean distance
def compute_distance(loc1, loc2):
    dx = loc1[0] - loc2[0]
    dy = loc1[1] - loc2[1]
    return sqrt(dx * dx + dy * dy)

# Function to solve Facility Location Problem
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

    # Display results
    selected_facilities = []
    shipments = []

    for facility in select.keys():
        if abs(select[facility].x) > 1e-6:
            selected_facilities.append(f"Build a warehouse at location {facility + 1}.")

    for customer, facility in assign.keys():
        if abs(assign[customer, facility].x) > 1e-6:
            shipments.append(f"Supermarket {customer + 1} receives {round(100 * assign[customer, facility].x, 2)}% of its demand from Warehouse {facility + 1}.")

    return selected_facilities, shipments

# Streamlit UI
def main():
    st.set_page_config(page_title="Facility Location Optimization", layout="wide")

    # Custom styling for the Streamlit app
    st.markdown("""
        <style>
        .header {
            text-align: center;
            font-size: 35px;
            font-weight: bold;
            color: #4CAF50;
        }
        .subheader {
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }
        .instruction-text {
            color: #777;
            font-size: 16px;
        }
        .input-box {
            padding: 10px;
            border-radius: 5px;
            border: 2px solid #ddd;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='header'>Facility Location Optimization</h1>", unsafe_allow_html=True)
    st.markdown("<p class='instruction-text'>Use this tool to find the optimal locations for warehouses to minimize delivery and setup costs. Enter the details below and click 'Solve' to see the result.</p>", unsafe_allow_html=True)

    # Sidebar for Input Parameters
    st.sidebar.header("Input Parameters")

    # Customers input (coordinates)
    num_customers = st.sidebar.number_input("Number of Customers", min_value=1, value=2, step=1, help="Number of supermarkets to be served.")
    customers = []
    for i in range(num_customers):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            customer_x = st.number_input(f"Customer {i+1} X-coordinate", min_value=-100.0, value=0.0, help="Enter the X-coordinate of the customer.")
        with col2:
            customer_y = st.number_input(f"Customer {i+1} Y-coordinate", min_value=-100.0, value=1.5, help="Enter the Y-coordinate of the customer.")
        customers.append((customer_x, customer_y))

    # Facilities input (coordinates and setup costs)
    num_facilities = st.sidebar.number_input("Number of Facility Locations", min_value=1, value=9, step=1, help="Number of candidate warehouse locations.")
    facilities = []
    setup_cost = []
    for i in range(num_facilities):
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            facility_x = st.number_input(f"Facility {i+1} X-coordinate", min_value=-100.0, value=0.0, help="Enter the X-coordinate of the facility.")
        with col2:
            facility_y = st.number_input(f"Facility {i+1} Y-coordinate", min_value=-100.0, value=0.0, help="Enter the Y-coordinate of the facility.")
        with col3:
            facility_cost = st.number_input(f"Facility {i+1} Setup Cost", min_value=0, value=3, help="Enter the setup cost of the facility.")
        facilities.append((facility_x, facility_y))
        setup_cost.append(facility_cost)

    # Cost per mile
    cost_per_mile = st.sidebar.number_input("Cost Per Mile", min_value=0.0, value=1.0, help="Enter the cost per mile for transportation.")

    # Solve the problem when the button is pressed
    if st.sidebar.button("Solve"):
        st.markdown("<hr>", unsafe_allow_html=True)
        selected_facilities, shipments = solve_facility_location(customers, facilities, setup_cost, cost_per_mile)

        # Display results in a clean format
        st.subheader("Optimization Results")
        st.write("### Selected Facilities:")
        if selected_facilities:
            for facility in selected_facilities:
                st.write(facility)
        else:
            st.write("No facility selected.")

        st.write("### Shipment Plan:")
        if shipments:
            for shipment in shipments:
                st.write(shipment)
        else:
            st.write("No shipments required.")

        st.markdown("<hr>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
