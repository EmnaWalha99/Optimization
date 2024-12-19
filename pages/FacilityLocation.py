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
    m.setObjective(
        gp.quicksum(setup_cost[f] * select[f] for f in range(num_facilities)) +
        gp.quicksum(shipping_cost[c, f] * assign[c, f] for c, f in cartesian_prod),
        GRB.MINIMIZE
    )

    # Optimize model
    m.optimize()

    # Process results
    selected_facilities = [f for f in range(num_facilities) if abs(select[f].x) > 1e-6]
    shipments = {(c, f): assign[c, f].x for c, f in cartesian_prod if abs(assign[c, f].x) > 1e-6}

    return selected_facilities, shipments

# Function to plot facilities and supermarkets
def plot_facilities_and_supermarkets(customers, facilities, selected_facilities, shipments):
    plt.figure(figsize=(10, 6))

    # Plot customers
    customer_x, customer_y = zip(*customers)
    plt.scatter(customer_x, customer_y, c='blue', label='Clients', s=100, edgecolors='black')

    # Plot facilities
    facility_x, facility_y = zip(*facilities)
    plt.scatter(facility_x, facility_y, c='red', label='Installations Candidats', s=150, marker='^', edgecolors='black')

    # Highlight selected facilities
    selected_x = [facilities[f][0] for f in selected_facilities]
    selected_y = [facilities[f][1] for f in selected_facilities]
    plt.scatter(selected_x, selected_y, c='green', s=200, marker='^', edgecolors='black', label='Installations Sélectionnées')

    # Draw lines for shipments
    for (customer, facility), fraction in shipments.items():
        if fraction > 0:
            plt.plot(
                [customers[customer][0], facilities[facility][0]],
                [customers[customer][1], facilities[facility][1]],
                c='gray', linestyle='--', linewidth=0.7
            )

    plt.title("Optimisation de l'Allocation des Installations")
    plt.xlabel("Coordonnée X")
    plt.ylabel("Coordonnée Y")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(plt)

# Main Streamlit app
def main():
    st.set_page_config(page_title="Optimisation de l'Allocation des Installations", layout="wide")

    st.markdown("<h1 style='text-align: center;'>Optimisation de l'Allocation des Installations</h1>", unsafe_allow_html=True)

    # Add instructions and methodology sections
    st.header("ℹ️ Instructions")
    with st.expander("📃 Guide d'Utilisation"):
        st.write("""
        - **Nombre de Clients** : Définissez le nombre de clients à optimiser.
        - **Nombre d'Installations** : Définissez le nombre d'installations parmi lesquelles choisir.
        - **Coûts de Mise en Place des Installations** : Définissez le coût fixe pour ouvrir chaque installation.
        - **Coût par Mile** : Définissez le coût de transport par unité de distance.
        - **Résoudre** : Cliquez sur 'Résoudre' pour calculer la sélection optimale des installations et la distribution des expéditions.
        """)

    with st.expander("🧮 Méthodologie"):
        st.write("""
        - Ce problème est modélisé comme un *Programmation Mixte en Nombres Entiers* (MIP).
        - L'objectif est de *minimiser les coûts totaux* en optimisant la sélection des installations et l'allocation des clients.
        - La solution est calculée en utilisant le *solveur Gurobi* pour trouver les emplacements optimaux des installations et les plans d'expédition.
        """)

    with st.expander("🔧 Notes Techniques"):
        st.write("- Le solveur Gurobi est requis pour exécuter cette application.")
        st.write("- Les résultats sont affichés graphiquement pour une meilleure visualisation.")
        st.write("- Cliquez sur le bouton 'Résoudre' après avoir fourni les paramètres d'entrée.")

    # Sidebar inputs for number of customers and facilities
    st.sidebar.header("Paramètres d'Entrée")

    # Nombre de clients
    if 'num_customers' not in st.session_state:
        st.session_state.num_customers = 2
    num_customers = st.sidebar.number_input("Nombre de Clients", min_value=1, value=st.session_state.num_customers, step=1)
    st.session_state.num_customers = num_customers

    # Initialiser les coordonnées des clients si non définies
    if 'customers' not in st.session_state or len(st.session_state.customers) != num_customers:
        st.session_state.customers = [(np.random.uniform(-50, 50), np.random.uniform(-50, 50)) for _ in range(num_customers)]

    customers = []
    for i in range(num_customers):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            customer_x = st.number_input(f"Client {i+1} Coordonnée X", value=st.session_state.customers[i][0], key=f"customer_x_{i}")
        with col2:
            customer_y = st.number_input(f"Client {i+1} Coordonnée Y", value=st.session_state.customers[i][1], key=f"customer_y_{i}")
        customers.append((customer_x, customer_y))
        st.session_state.customers[i] = (customer_x, customer_y)  # Mettre à jour les coordonnées des clients

    # Nombre d'installations
    if 'num_facilities' not in st.session_state:
        st.session_state.num_facilities = 5
    num_facilities = st.sidebar.number_input("Nombre d'Installations", min_value=1, value=st.session_state.num_facilities, step=1)
    st.session_state.num_facilities = num_facilities

    # Initialiser les coordonnées et coûts des installations si non définis
    if 'facilities' not in st.session_state or len(st.session_state.facilities) != num_facilities:
        st.session_state.facilities = [(np.random.uniform(-50, 50), np.random.uniform(-50, 50), 10) for _ in range(num_facilities)]

    facilities = []
    setup_cost = []
    for i in range(num_facilities):
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            facility_x = st.number_input(f"Installation {i+1} Coordonnée X", value=st.session_state.facilities[i][0], key=f"facility_x_{i}")
        with col2:
            facility_y = st.number_input(f"Installation {i+1} Coordonnée Y", value=st.session_state.facilities[i][1], key=f"facility_y_{i}")
        with col3:
            facility_cost = st.number_input(f"Installation {i+1} Coût de Mise en Place", value=st.session_state.facilities[i][2], key=f"facility_cost_{i}")
        facilities.append((facility_x, facility_y))
        setup_cost.append(facility_cost)
        st.session_state.facilities[i] = (facility_x, facility_y, facility_cost)  # Mettre à jour les données des installations

    # Coût par mile
    cost_per_mile = st.sidebar.number_input("Coût par Mile", min_value=0.0, value=1.0, step=0.1)

    # Bouton pour résoudre le problème
    if st.sidebar.button("Résoudre 🚀"):
        selected_facilities, shipments = solve_facility_location(customers, facilities, setup_cost, cost_per_mile)

        st.subheader("Résultats de l'Optimisation")
        st.write("### Installations Sélectionnées:")
        for facility in selected_facilities:
            st.write(f"Installation {facility + 1}")

        st.write("### Plan d'Expédition:")
        for (customer, facility), fraction in shipments.items():
            st.write(f"Client {customer + 1} est servi à {round(100 * fraction, 2)}% par Installation {facility + 1}")

        # Visualisation
        plot_facilities_and_supermarkets(customers, facilities, selected_facilities, shipments)

if __name__ == "__main__":
    main()
