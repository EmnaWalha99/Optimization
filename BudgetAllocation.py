import streamlit as st
import plotly.graph_objects as go
from gurobipy import Model, GRB
import time

# Streamlit App for Resource Allocation with Constraints
def main():
    st.set_page_config(
        page_title="Optimisation d'Allocation de Ressources",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Optimisation d'Allocation de Ressources ")

    # Sidebar Inputs
    with st.sidebar:
        st.header("📋 Paramètres d'Entrée")
        
        # Total resources input
        total_resources = st.number_input("Ressources Totales Disponibles", min_value=1, value=100, step=1)
        
        # Number of projects
        num_projects = st.number_input("Nombre de Projets", min_value=2, max_value=10, value=3, step=1)
        
        st.header("🔧 Coûts, Rendements et Contraintes")
        project_costs = []
        project_returns = []
        project_min_units = []
        project_max_units = []
        project_priorities = []

        # Create tabs for project-specific inputs
        tabs = st.tabs([f"Projet {i + 1}" for i in range(num_projects)])
        for i in range(num_projects):
            with tabs[i]:
                st.subheader(f"Configuration pour Projet {i + 1}")
                cost = st.number_input(f"Coût par unité pour Projet {i + 1}", min_value=1, value=5, step=1, key=f"cost_{i}")
                ret = st.number_input(f"Retour par unité pour Projet {i + 1}", min_value=1, value=10, step=1, key=f"return_{i}")
                min_units = st.number_input(f"Unités minimales pour Projet {i + 1}", min_value=0, value=0, step=1, key=f"min_units_{i}")
                max_units = st.number_input(f"Unités maximales pour Projet {i + 1}", min_value=1, value=10, step=1, key=f"max_units_{i}")
                priority = st.number_input(f"Priorité pour Projet {i + 1} (1 = plus élevée)", min_value=1, max_value=10, value=5, key=f"priority_{i}")
                project_costs.append(cost)
                project_returns.append(ret)
                project_min_units.append(min_units)
                project_max_units.append(max_units)
                project_priorities.append(priority)

    # Interface Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📈 Résultats d'Optimisation")
        if st.button("Optimiser 🚀"):
            try:
                # Model Initialization
                model = Model("Resource_Allocation")

                # Decision Variables: units allocated to each project
                x = [model.addVar(vtype=GRB.CONTINUOUS, name=f"Project_{i+1}") for i in range(num_projects)]
                

                # Add priority weights
                priority_weights = [1 if priority == 1 else 0.8 if priority == 2 else 0.5 for priority in project_priorities]

                # Objective Function: Maximize Returns (weighted by priorities)
                model.setObjective(
                    sum(project_returns[i] * priority_weights[i] * x[i] for i in range(num_projects)), GRB.MAXIMIZE
                )


                # Constraint: Total Resources
                model.addConstr(
                    sum(project_costs[i] * x[i] for i in range(num_projects)) <= total_resources,
                    name="Resource_Limit"
                )

                # Per-Project Minimum and Maximum Units Constraints
                for i in range(num_projects):
                    model.addConstr(x[i] >= project_min_units[i], name=f"Min_Units_Project_{i+1}")
                    model.addConstr(x[i] <= project_max_units[i], name=f"Max_Units_Project_{i+1}")

               

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
                             "Coût par Unité": project_costs[i], 
                             "Retour par Unité": project_returns[i],
                             "Unités Allouées": f"{x[i].x:.2f}",
                             "Unités Min. Requises": project_min_units[i],
                             "Unités Max. Requises": project_max_units[i]}
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
                        title="📊 Allocation Optimale des Ressources",
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
            - **Ressources Totales** : Entrez les ressources disponibles à distribuer.
            - **Nombre de Projets** : Indiquez le nombre de projets à optimiser.
            - **Contraintes** : Saisissez les coûts, rendements, unités minimales et maximales pour chaque projet.
            - Ajoutez les contraintes spécifiques dans le champ dédié.
            - Cliquez sur **'Optimiser'** pour trouver une allocation optimale.
            """)
        with st.expander("🧮 Méthodologie"):
            st.write("""
            - Formulation : Problème de programmation linéaire (maximisation).
            - Contraintes : Limitation des ressources, unités minimales/maximales, interdépendances, priorités.
            """)
        with st.expander("🔧 Notes Techniques"):
            st.write("- Le solveur **Gurobi** est utilisé pour résoudre le problème.")
            st.write("- Les solutions et graphiques sont interactifs et dynamiques.")

if __name__ == "__main__":
    main()
