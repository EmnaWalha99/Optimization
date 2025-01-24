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
        
        # Total resources and number of resources
        num_resources = st.number_input("Nombre de Ressources", min_value=1, max_value=5, value=2, step=1)
        resource_names = []
        resource_availabilities = []
        resource_priorities = []
        
        for i in range(num_resources):
            st.subheader(f"Ressource {i + 1}")
            name = st.text_input(f"Nom de la Ressource {i + 1}", value=f"Ressource {i + 1}", key=f"res_name_{i}")
            availability = st.number_input(f"Quantité Totale de {name}", min_value=1, value=100, step=10, key=f"res_avail_{i}")
            priority = st.number_input(f"Priorité pour {name} (1 = plus élevée)", min_value=1, max_value=10, value=5, key=f"res_priority_{i}")
            resource_names.append(name)
            resource_availabilities.append(availability)
            resource_priorities.append(priority)

        # Number of projects
        num_projects = st.number_input("Nombre de Projets", min_value=2, max_value=10, value=3, step=1)
        
        st.header("🔧 Coûts, Rendements et Contraintes")
        project_costs = []
        project_returns = []
        project_min_units = []
        project_max_units = []
        project_resource_needs = []

        # Create tabs for project-specific inputs
        tabs = st.tabs([f"Projet {i + 1}" for i in range(num_projects)])
        for i in range(num_projects):
            with tabs[i]:
                st.subheader(f"Configuration pour Projet {i + 1}")
                ret = st.number_input(f"Retour par unité pour Projet {i + 1}", min_value=1, value=10, step=1, key=f"return_{i}")
                min_units = st.number_input(f"investissement minimales pour Projet {i + 1}", min_value=0, value=0, step=1, key=f"min_units_{i}")
                max_units = st.number_input(f"investissement maximales pour Projet {i + 1}", min_value=1, value=10, step=1, key=f"max_units_{i}")
                project_returns.append(ret)
                project_min_units.append(min_units)
                project_max_units.append(max_units)

                # Per-resource needs
                resource_needs = []
                for j in range(num_resources):
                    need = st.number_input(
                        f"Besoins de {resource_names[j]} pour Projet {i + 1}",
                        min_value=0, value=1, step=1, key=f"proj_{i}_res_{j}"
                    )
                    resource_needs.append(need)
                project_resource_needs.append(resource_needs)

    # Interface Layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📈 Résultats d'Optimisation")
        if st.button("Optimiser 🚀"):
            try:
                # Model Initialization
                model = Model("Resource_Allocation_Multi")

                # Decision Variables: units allocated to each project
                x = [model.addVar(vtype=GRB.CONTINUOUS, name=f"Project_{i+1}") for i in range(num_projects)]

                # Add resource priority weights
                resource_weights = [1 if priority == 1 else 0.8 if priority == 2 else 0.5 for priority in resource_priorities]

                # Objective Function: Maximize Returns
                model.setObjective(
                    sum(project_returns[i] * x[i] for i in range(num_projects)), GRB.MAXIMIZE
                )

                # Constraint: Total Resources for each resource
                for j in range(num_resources):
                    model.addConstr(
                        sum(project_resource_needs[i][j] * x[i] for i in range(num_projects)) <= resource_availabilities[j],
                        name=f"Resource_Limit_{resource_names[j]}"
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
                        res_allocations = [
                            f"{project_resource_needs[i][j] * x[i].x:.2f}" for j in range(num_resources)
                        ]
                        allocation.append(
                            {"Projet": f"Projet {i+1}", 
                             
                             **{resource_names[j]: res_allocations[j] for j in range(num_resources)}}
                        )
                    
                    st.table(allocation)

                    # Visualization
                    fig = go.Figure()
                    for j in range(num_resources):
                        fig.add_trace(go.Bar(
                            x=[f"Projet {i+1}" for i in range(num_projects)],
                            y=[project_resource_needs[i][j] * x[i].x for i in range(num_projects)],
                            name=f"Allocation de {resource_names[j]}"
                        ))
                    fig.update_layout(
                        title="📊 Allocation Optimale des Ressources",
                        xaxis_title="Projets",
                        yaxis_title="Quantité de Ressources",
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
            - **Nombre de Ressources** : Indiquez combien de ressources sont disponibles.
            - **Contraintes des Projets** : Définissez les coûts, rendements et limites des unités par projet.
            - **Besoins de Ressources** : Saisissez les besoins spécifiques de chaque projet pour chaque ressource.
            - Cliquez sur **'Optimiser'** pour voir les résultats.
            """)

if __name__ == "__main__":
    main()



