import streamlit as st
import plotly.graph_objects as go
from gurobipy import Model, GRB
import time

# Streamlit App for Budget Allocation Problem
def main():
    st.set_page_config(
        page_title="Optimisation de l'Allocation du Budget",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Optimisation de l'Allocation du Budget")

    # Sidebar Inputs
    with st.sidebar:
        st.header("📋 Paramètres d'Entrée")
        
        # Budget input
        total_budget = st.number_input("Budget Total (€)", min_value=1000, value=10000, step=500)
        
        # Number of projects
        num_projects = st.number_input("Nombre de Projets", min_value=2, max_value=10, value=3, step=1)
        
        st.header("🔧 Coûts et Rendements")
        project_costs = []
        project_returns = []
        project_min_units = []

        # Create tabs for project-specific inputs
        tabs = st.tabs([f"Projet {i + 1}" for i in range(num_projects)])
        for i in range(num_projects):
            with tabs[i]:
                st.subheader(f"Configuration pour Projet {i + 1}")
                cost = st.number_input(f"Coût par unité pour Projet {i + 1} (€)", min_value=10, value=500, step=50, key=f"cost_{i}")
                ret = st.number_input(f"Retour par unité pour Projet {i + 1} (€)", min_value=10, value=800, step=50, key=f"return_{i}")
                min_units = st.number_input(f"Unités minimales pour Projet {i + 1}", min_value=0, value=0, step=1, key=f"min_units_{i}")
                project_costs.append(cost)
                project_returns.append(ret)
                project_min_units.append(min_units)

    # Interface Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📈 Résultats d'Optimisation")
        if st.button("Optimiser 🚀"):
            try:
                # Model Initialization
                model = Model("Budget_Optimization")
                
                # Decision Variables: units allocated to each project
                x = [model.addVar(vtype=GRB.CONTINUOUS, name=f"Project_{i+1}") for i in range(num_projects)]
                
                # Objective Function: Maximize Returns
                model.setObjective(sum(project_returns[i] * x[i] for i in range(num_projects)), GRB.MAXIMIZE)
                
                # Constraint: Total Budget
                model.addConstr(sum(project_costs[i] * x[i] for i in range(num_projects)) <= total_budget, name="Budget_Constraint")
                
                # Per-Project Minimum Units Constraint
                for i in range(num_projects):
                    model.addConstr(x[i] >= project_min_units[i], name=f"Min_Units_Constraint_Project_{i+1}")

                # Solve Model
                with st.spinner("Optimisation en cours..."):
                    start_time = time.time()
                    model.optimize()
                    end_time = time.time()

                # Display Results
                if model.status == GRB.OPTIMAL:
                    st.success("✅ Solution Optimale Trouvée !")
                    st.metric("Temps de Résolution (s)", f"{end_time - start_time:.2f}")
                    
                    # Table for allocation
                    allocation = []
                    for i in range(num_projects):
                        allocation.append(
                            {"Projet": f"Projet {i+1}", 
                             "Coût par Unité (€)": project_costs[i], 
                             "Retour par Unité (€)": project_returns[i],
                             "Unités Allouées": f"{x[i].x:.2f}",
                             "Unités Min. Requises": project_min_units[i]}
                        )
                    
                    st.table(allocation)

                    # Visualization
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[f"Projet {i+1}" for i in range(num_projects)],
                        y=[x[i].x for i in range(num_projects)],
                        text=[f"{x[i].x:.2f}" for i in range(num_projects)],
                        textposition='outside',
                        name="Unités Allouées"
                    ))
                    fig.update_layout(
                        title="📊 Allocation Optimale du Budget",
                        xaxis_title="Projets",
                        yaxis_title="Unités Allouées",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Aucune solution optimale trouvée.")

            except Exception as e:
                st.error(f"Erreur : {str(e)}")

    with col2:
        st.header("ℹ️ Instructions")
        with st.expander("📃 Guide d'Utilisation"):
            st.write("""
            - **Budget Total** : Définissez le montant total disponible pour l'allocation.
            - **Nombre de Projets** : Indiquez le nombre de projets à optimiser.
            - **Coûts et Rendements** : Saisissez les coûts et rendements par unité pour chaque projet.
            - Définissez les **unités minimales** pour chaque projet dans les onglets.
            - Cliquez sur **'Optimiser'** pour trouver l'allocation optimale du budget.
            """)
        with st.expander("🧮 Méthodologie"):
            st.write("""
            - Le problème est formulé comme un **programme linéaire**.
            - L'objectif est de **maximiser les rendements** tout en respectant les contraintes budgétaires et minimales.
            - La résolution est effectuée à l'aide du solveur **Gurobi**.
            """)
        with st.expander("🔧 Notes Techniques"):
            st.write("- Le solveur Gurobi est requis pour exécuter cette application.")
            st.write("- Les unités allouées sont affichées avec des graphiques interactifs.")

if __name__ == "__main__":
    main()
