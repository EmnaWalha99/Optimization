import streamlit as st
import subprocess
import psutil
import time
import os
import plotly.graph_objects as go
from gurobipy import Model, GRB

# Streamlit interface
def main():
    st.set_page_config(
        page_title="Analyse et Optimisation de Scripts Python",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Updated to ensure proper Unicode handling for emojis in the title
    st.title("📞 Analyse et Optimisation de Scripts Python")

    # Sidebar for file upload and constraints
    with st.sidebar:
        st.header("📂 Charger un Script")
        uploaded_file = st.file_uploader("Uploader un fichier .py", type=["py"], help="Chargez votre script Python ici")

        st.header("🔒 Définir les Contraintes")
        time_limit = st.number_input(
            "Temps maximum d'exécution (secondes)", value=6, min_value=1, help="Temps maximum autorisé pour le script."
        )
        memory_limit = st.number_input(
            "Mémoire maximale (MB)", value=50, min_value=1, help="Limite de mémoire maximale autorisée pour le script."
        )
        cost_cpu = st.number_input("Coût par unité CPU", value=0.5, step=0.1, help="Coût associé à l'utilisation du CPU.")
        cost_memory = st.number_input(
            "Coût par MB de mémoire", value=0.2, step=0.1, help="Coût associé à la consommation de mémoire."
        )

    # Display sections dynamically
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🔍 Analyse des Performances")

        if st.button("Lancer l'Analyse 🚀"):
            if not uploaded_file:
                st.error("Veuillez télécharger un fichier .py d'abord.")
            else:
                try:
                    temp_file_path = f"./{uploaded_file.name}"
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.read())

                    cpu_usage = []
                    memory_usage = []
                    timestamps = []

                    process = subprocess.Popen([ 
                        "python", temp_file_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    fig = go.Figure()
                    st_plot = st.empty()

                    with st.spinner("Exécution en cours... Veuillez patienter."):
                        while process.poll() is None:
                            cpu = psutil.cpu_percent(interval=0.1)
                            memory = psutil.virtual_memory().used / (1024**3)  # Convert to MB
                            timestamp = time.time()

                            cpu_usage.append(cpu)
                            memory_usage.append(memory)
                            timestamps.append(timestamp)

                            # Update plot in real time
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(y=cpu_usage, mode='lines', name="CPU Usage (%)"))
                            fig.add_trace(go.Scatter(y=memory_usage, mode='lines', name="Memory Usage (MB)"))
                            fig.update_layout(
                                title="Utilisation des Ressources en Temps Réel",
                                xaxis_title="Points de Mesure",
                                yaxis_title="Utilisation",
                                legend=dict(x=0, y=1),
                            )
                            st_plot.plotly_chart(fig, use_container_width=True)

                    stdout, stderr = process.communicate()

                    execution_time = timestamps[-1] - timestamps[0] if timestamps else 0
                    max_cpu = max(cpu_usage, default=0)
                    max_memory = max(memory_usage, default=0)

                    # Display Performance Results
                    st.subheader("ℹ️ Statistiques de Performance")
                    st.metric("Temps d'exécution (s)", f"{execution_time:.2f}")
                    st.metric("Utilisation CPU max (%)", f"{max_cpu:.2f}")
                    st.metric("Utilisation mémoire max (MB)", f"{max_memory:.2f}")

                    # Optimization with Gurobi
                    st.subheader("🌐 Optimisation des Ressources")
                    model = Model("Script_Optimization")

                    # Decision variables
                    x_cpu = model.addVar(vtype=GRB.CONTINUOUS, name="CPU_Usage")
                    x_memory = model.addVar(vtype=GRB.CONTINUOUS, name="Memory_Usage")

                    # Objective function: Minimize cost
                    model.setObjective(cost_cpu * x_cpu + cost_memory * x_memory, GRB.MINIMIZE)

                    # Constraints
                    model.addConstr(x_cpu >= max_cpu*1.2, name="CPU_Constraint")
                    model.addConstr(x_memory >= max_memory*1.2, name="Memory_Constraint")
                    model.addConstr(execution_time <= time_limit, name="Time_Constraint")

                    # Solve
                    model.optimize()

                    if model.status == GRB.OPTIMAL:
                        st.success("Solution Optimale Trouvée !")
                        st.metric("Allocation optimale CPU (%)", f"{x_cpu.x:.2f}")
                        st.metric("Allocation optimale Mémoire (MB)", f"{x_memory.x:.2f}")
                        st.metric("Coût Total", f"{model.objVal:.2f}")
                    else:
                        st.error("Aucune solution optimale trouvée.")

                except Exception as e:
                    st.error(f"Une erreur est survenue : {str(e)}")

                finally:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

    with col2:
        st.header("💡 Guide Utilisateur")
        with st.expander("📃 Instructions"):
            st.write("1. Chargez un fichier Python (.py) contenant le script à analyser.")
            st.write("2. Définissez les contraintes d'exécution : temps, mémoire, et coût.")
            st.write("3. Cliquez sur 'Lancer l'Analyse' pour visualiser les résultats et l'optimisation.")
        with st.expander("🔧 Notes Techniques"):
            st.write("- La consommation CPU est mesurée en temps réel.")
            st.write("- Les graphiques montrent les tendances en direct pendant l'exécution.")

if __name__ == "__main__":
    main()
