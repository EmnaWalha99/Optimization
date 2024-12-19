import streamlit as st
import matplotlib.pyplot as plt
from gurobipy import Model, GRB
import time

# Function to plot the Gantt chart
def plot_gantt_streamlit(jobs_data, schedule, num_machines):
    fig, ax = plt.subplots(figsize=(10, 6))

    for machine in range(num_machines):
        for job, task, start, duration in schedule[machine]:
            ax.barh(machine, duration, left=start, align='center', color=f"C{job}", edgecolor='black')
            ax.text(start + duration / 2, machine, f"J{job}T{task}",
                    ha='center', va='center', color='white')

    ax.set_yticks(range(num_machines))
    ax.set_yticklabels([f"Machine {i + 1}" for i in range(num_machines)])  # Adjust to start from 1
    ax.set_xlabel("Temps")
    ax.set_title("Diagramme de Gantt - Planification des Travaux")
    st.pyplot(fig)

# Streamlit App for Job Shop Scheduling
def main():
    st.set_page_config(page_title="Planification des Travaux", layout="wide", initial_sidebar_state="expanded")

    st.title("📊 Planification des Travaux")

    # Sidebar Inputs
    with st.sidebar:
        st.header("📋 Paramètres d'Entrée")

        # Number of jobs and machines
        num_jobs = st.number_input("Nombre de Travaux (à partir de 1)", min_value=1, value=2, step=1)
        num_machines = st.number_input("Nombre de Machines (à partir de 1)", min_value=1, value=3, step=1)

        # Job tasks input
        st.header("🔧 Tâches des Travaux")
        jobs_data = []
        for job_id in range(num_jobs):
            with st.expander(f"Travail {job_id + 1}"):  # Adjust to show 1-based indexing
                tasks = []
                num_tasks = st.number_input(f"Nombre de tâches pour le Travail {job_id + 1}", min_value=1, value=2, step=1, key=f"num_tasks_{job_id}")
                for task_id in range(num_tasks):
                    machine = st.number_input(f"Tâche {task_id + 1} Machine", min_value=1, max_value=num_machines, value=1, step=1, key=f"machine_{job_id}_{task_id}")
                    duration = st.number_input(f"Tâche {task_id + 1} Durée", min_value=1, value=1, step=1, key=f"duration_{job_id}_{task_id}")
                    tasks.append((machine - 1, duration))  # Convert to 0-based indexing
                jobs_data.append(tasks)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📈 Résultats de l'Optimisation")
        if st.button("Optimiser 🚀"):
            try:
                # Horizon calculation
                horizon = sum(task[1] for job in jobs_data for task in job)

                # Model initialization
                model = Model("JobShop")

                # Decision variables
                start_vars = {}
                for job_id, job in enumerate(jobs_data):
                    for task_id, (machine, duration) in enumerate(job):
                        start_vars[job_id, task_id] = model.addVar(vtype=GRB.INTEGER, name=f"start_{job_id}_{task_id}")

                # Makespan variable
                makespan = model.addVar(vtype=GRB.INTEGER, name="makespan")

                # Constraints
                # 1. Precedence constraints within jobs
                for job_id, job in enumerate(jobs_data):
                    for task_id in range(len(job) - 1):
                        model.addConstr(
                            start_vars[job_id, task_id + 1] >= start_vars[job_id, task_id] + job[task_id][1],
                            name=f"precedence_{job_id}_{task_id}"
                        )

                # 2. No overlap constraints on machines
                for machine in range(num_machines):
                    machine_tasks = []
                    for job_id, job in enumerate(jobs_data):
                        for task_id, (task_machine, duration) in enumerate(job):
                            if task_machine == machine:
                                machine_tasks.append((job_id, task_id, duration))

                    for i, (job1, task1, dur1) in enumerate(machine_tasks):
                        for j, (job2, task2, dur2) in enumerate(machine_tasks):
                            if i < j:
                                z = model.addVar(vtype=GRB.BINARY, name=f"order_{job1}_{task1}_{job2}_{task2}")
                                model.addConstr(
                                    start_vars[job1, task1] + dur1 <= start_vars[job2, task2] + horizon * (1 - z),
                                    name=f"no_overlap_1_{job1}_{task1}_{job2}_{task2}"
                                )
                                model.addConstr(
                                    start_vars[job2, task2] + dur2 <= start_vars[job1, task1] + horizon * z,
                                    name=f"no_overlap_2_{job1}_{task1}_{job2}_{task2}"
                                )

                # 3. Makespan constraints
                for job_id, job in enumerate(jobs_data):
                    model.addConstr(
                        makespan >= start_vars[job_id, len(job) - 1] + job[-1][1],
                        name=f"makespan_job_{job_id}"
                    )

                # Objective: Minimize the makespan
                model.setObjective(makespan, GRB.MINIMIZE)

                # Solve the model
                with st.spinner("Optimisation en cours..."):
                    start_time = time.time()
                    model.optimize()
                    end_time = time.time()

                if model.status == GRB.OPTIMAL:
                    st.success("✅ Solution optimale trouvée !")
                    st.metric("Makespan optimal", f"{makespan.X}")
                    st.metric("Temps de solution (s)", f"{end_time - start_time:.2f}")

                    # Extract schedule
                    schedule = {machine: [] for machine in range(num_machines)}
                    for job_id, job in enumerate(jobs_data):
                        for task_id, (machine, duration) in enumerate(job):
                            start_time = start_vars[job_id, task_id].X
                            schedule[machine].append((job_id, task_id, start_time, duration))

                    # Sort tasks by start time for each machine
                    for machine in schedule:
                        schedule[machine].sort(key=lambda x: x[2])

                    # Plot Gantt chart
                    plot_gantt_streamlit(jobs_data, schedule, num_machines)
                else:
                    st.error("❌ Aucune solution optimale trouvée.")

            except Exception as e:
                st.error(f"Erreur: {str(e)}")

    with col2:
        with st.expander("ℹ️ Instructions"):
            st.write("""
            - Utilisez la barre latérale pour entrer le nombre de travaux, de machines et les détails des tâches.
            - Cliquez sur le bouton 'Optimiser' pour résoudre le problème de planification.
            - Le programme affichera le planning optimal et le diagramme de Gantt.
            """)
        with st.expander("📜 Contraintes"):
            st.write(
                """
                - 🔗 **Exécution Consécutive des Tâches** : Deux tâches spécifiées doivent être exécutées consécutivement, c'est-à-dire que l'heure de début de la deuxième tâche doit immédiatement suivre la fin de la première tâche.
        
                - 🚫 **Tâches Non-Empiétant sur la Même Machine** : Aucune tâche affectée à une machine ne peut chevaucher une autre tâche. Les tâches sont programmées de manière séquentielle sur une machine.
        
                - ⏳ **Contraintes de Précédence** : Une tâche doit être terminée avant que la tâche suivante puisse commencer, si elle dépend du résultat de la première tâche.
        
                - ⚙️ **Disponibilité des Machines** : Chaque machine peut traiter une seule tâche à la fois.
        
                - ⏲️ **Durées de Traitement Fixes** : Les tâches ont des durées pré-définies qui ne peuvent pas être modifiées lors de la planification.
        
                - 🛠️ **Affectation des Tâches** : Chaque tâche est affectée à une machine spécifique, comme spécifié dans les entrées du problème.
        
                - 🕒 **Makespan Minimisé** : Le modèle minimise le temps total nécessaire pour accomplir toutes les tâches (makespan).
                """
            )

if __name__ == "__main__":
    main()
