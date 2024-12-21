import streamlit as st
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import numpy as np

# Function to check if a facility is within a customer's zone (coverage criterion)
def is_within_coverage(facility, customer, radius):
    return np.sqrt((facility[0] - customer[0])**2 + (facility[1] - customer[1])**2) <= radius

# Function to solve the coverage optimization problem
def solve_coverage_optimization(customers, facilities, radii):
    num_facilities = len(facilities)
    num_customers = len(customers)

    # MIP Model formulation
    m = gp.Model('coverage_optimization')

    # Decision Variables
    select = m.addVars(num_facilities, vtype=GRB.BINARY, name='Select')
    cover = m.addVars(num_customers, num_facilities, vtype=GRB.BINARY, name='Cover')

    # Constraints
    # Each customer must be covered by at least one facility
    m.addConstrs((gp.quicksum(cover[c, f] for f in range(num_facilities)) == 1 for c in range(num_customers)), name="Coverage")

    # A facility can only cover a customer if it's selected
    m.addConstrs((cover[c, f] <= select[f] for c in range(num_customers) for f in range(num_facilities)), name="FacilitySetup")

    # Objective Function: Minimize the number of selected facilities
    m.setObjective(gp.quicksum(select[f] for f in range(num_facilities)), GRB.MINIMIZE)

    # Optimize model
    m.optimize()

    # Process results
    selected_facilities = [f for f in range(num_facilities) if select[f].x > 0.5]
    coverage = {(c, f): cover[c, f].x for c in range(num_customers) for f in selected_facilities if cover[c, f].x > 0.5}

    return selected_facilities, coverage

# Function to plot facilities and coverage areas with color-coded zones
def plot_facilities_and_zones(customers, facilities, selected_facilities, coverage, radii):
    plt.figure(figsize=(10, 6))

    # Plot customers with coverage circles in different colors
    colors = plt.cm.get_cmap('tab10', len(customers))  # Get a colormap for multiple colors
    for i, (x, y) in enumerate(customers):
        radius = radii[i]
        circle = plt.Circle((x, y), radius, color=colors(i), alpha=0.3, label=f"Zone {i+1}" if i == 0 else "")
        plt.gca().add_artist(circle)
    customer_x, customer_y = zip(*customers)
    plt.scatter(customer_x, customer_y, c='blue', label='Zones Cibles', s=100, edgecolors='black')

    # Plot facilities
    facility_x, facility_y = zip(*facilities)
    plt.scatter(facility_x, facility_y, c='red', label='Installations Candidats', s=150, marker='^', edgecolors='black')

    # Highlight selected facilities
    selected_x = [facilities[f][0] for f in selected_facilities]
    selected_y = [facilities[f][1] for f in selected_facilities]
    plt.scatter(selected_x, selected_y, c='green', s=200, marker='^', edgecolors='black', label='Installations Sélectionnées')

    # Draw lines for coverage
    for c in range(len(customers)):
        for f in selected_facilities:
            if coverage.get((c, f), 0) > 0:
                plt.plot(
                    [customers[c][0], facilities[f][0]],
                    [customers[c][1], facilities[f][1]],
                    c='gray', linestyle='--', linewidth=0.7
                )

    plt.title("Optimisation de la Couverture des Zones")
    plt.xlabel("Coordonnée X")
    plt.ylabel("Coordonnée Y")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(plt)

# Main Streamlit app
def main():
    st.set_page_config(page_title="Optimisation de la Couverture des Zones", layout="wide")

    st.markdown("<h1 style='text-align: center;'>Optimisation de la Couverture des Zones</h1>", unsafe_allow_html=True)

    st.header("ℹ️ Instructions")
    with st.expander("📃 Guide d'Utilisation"):
        st.write("""
        - **Nombre de Zones Cibles** : Définissez le nombre de zones cibles à couvrir.
        - **Nombre d'Installations** : Définissez le nombre d'installations parmi lesquelles choisir.
        - **Rayon des Zones Cibles** : Définissez le rayon de couverture de chaque zone cible.
        - **Résoudre** : Cliquez sur 'Résoudre' pour calculer la couverture optimale des zones avec les installations.
        """)

    with st.expander("🧮 Méthodologie"):
        st.write("""
        - Ce problème est modélisé comme une **optimisation de couverture**.
        - L'objectif est de *minimiser le nombre d'installations* nécessaires pour couvrir toutes les zones cibles.
        - La solution est calculée en utilisant un **solveur Gurobi** pour trouver les emplacements optimaux des installations et la couverture des zones.
        """)

    # Sidebar inputs for number of customers and facilities
    st.sidebar.header("Paramètres d'Entrée")

    # Nombre de zones cibles
    if 'num_customers' not in st.session_state:
        st.session_state.num_customers = 2
    num_customers = st.sidebar.number_input("Nombre de Zones Cibles", min_value=1, value=st.session_state.num_customers, step=1)
    st.session_state.num_customers = num_customers

    # Initialiser les coordonnées des zones cibles et leurs rayons
    if 'customers' not in st.session_state or len(st.session_state.customers) != num_customers:
        st.session_state.customers = [(np.random.uniform(-50, 50), np.random.uniform(-50, 50)) for _ in range(num_customers)]
    if 'radii' not in st.session_state or len(st.session_state.radii) != num_customers:
        st.session_state.radii = [np.random.uniform(5, 20) for _ in range(num_customers)]

    customers = []
    radii = []
    for i in range(num_customers):
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            customer_x = st.number_input(f"Zone Cible {i+1} Coordonnée X", value=st.session_state.customers[i][0], key=f"customer_x_{i}")
        with col2:
            customer_y = st.number_input(f"Zone Cible {i+1} Coordonnée Y", value=st.session_state.customers[i][1], key=f"customer_y_{i}")
        with col3:
            radius = st.number_input(f"Zone Cible {i+1} Rayon", value=st.session_state.radii[i], key=f"radius_{i}")
        customers.append((customer_x, customer_y))
        radii.append(radius)
        st.session_state.customers[i] = (customer_x, customer_y)  # Mettre à jour les coordonnées
        st.session_state.radii[i] = radius  # Mettre à jour les rayons

    # Nombre d'installations
    if 'num_facilities' not in st.session_state:
        st.session_state.num_facilities = 5
    num_facilities = st.sidebar.number_input("Nombre d'Installations", min_value=1, value=st.session_state.num_facilities, step=1)
    st.session_state.num_facilities = num_facilities

    # Initialiser les coordonnées des installations
    if 'facilities' not in st.session_state or len(st.session_state.facilities) != num_facilities:
        st.session_state.facilities = [(np.random.uniform(-50, 50), np.random.uniform(-50, 50)) for _ in range(num_facilities)]

    facilities = []
    for i in range(num_facilities):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            facility_x = st.number_input(f"Installation {i+1} Coordonnée X", value=st.session_state.facilities[i][0], key=f"facility_x_{i}")
        with col2:
            facility_y = st.number_input(f"Installation {i+1} Coordonnée Y", value=st.session_state.facilities[i][1], key=f"facility_y_{i}")
        facilities.append((facility_x, facility_y))
        st.session_state.facilities[i] = (facility_x, facility_y)  # Mettre à jour les installations

    # Bouton pour résoudre le problème
    if st.sidebar.button("Résoudre 🚀"):
        selected_facilities, coverage = solve_coverage_optimization(customers, facilities, radii)

        st.subheader("Résultats de l'Optimisation")
        st.write("### Installations Sélectionnées:")
        for facility in selected_facilities:
            st.write(f"Installation {facility + 1}")

        # Visualisation
        plot_facilities_and_zones(customers, facilities, selected_facilities, coverage, radii)

if __name__ == "__main__":
    main()
