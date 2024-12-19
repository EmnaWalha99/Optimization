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
    ax.set_xlabel("Time")
    ax.set_title("Job Shop Scheduling Gantt Chart")
    st.pyplot(fig)

# Streamlit App for Job Shop Scheduling
def main():
    st.set_page_config(page_title="Job Shop Scheduling", layout="wide", initial_sidebar_state="expanded")

    st.title("📊 Job Shop Scheduling")

    # Sidebar Inputs
    with st.sidebar:
        st.header("📋 Input Parameters")

        # Number of jobs and machines
        num_jobs = st.number_input("Number of Jobs (starting from 1)", min_value=1, value=2, step=1)
        num_machines = st.number_input("Number of Machines (starting from 1)", min_value=1, value=3, step=1)

        # Job tasks input
        st.header("🔧 Job Tasks")
        jobs_data = []
        for job_id in range(num_jobs):
            with st.expander(f"Job {job_id + 1}"):  # Adjust to show 1-based indexing
                tasks = []
                num_tasks = st.number_input(f"Number of tasks in Job {job_id + 1}", min_value=1, value=2, step=1, key=f"num_tasks_{job_id}")
                for task_id in range(num_tasks):
                    machine = st.number_input(f"Task {task_id + 1} Machine", min_value=1, max_value=num_machines, value=1, step=1, key=f"machine_{job_id}_{task_id}")
                    duration = st.number_input(f"Task {task_id + 1} Duration", min_value=1, value=1, step=1, key=f"duration_{job_id}_{task_id}")
                    tasks.append((machine - 1, duration))  # Convert to 0-based indexing
                jobs_data.append(tasks)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📈 Optimization Results")
        if st.button("Optimize 🚀"):
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
                with st.spinner("Optimization in progress..."):
                    start_time = time.time()
                    model.optimize()
                    end_time = time.time()

                if model.status == GRB.OPTIMAL:
                    st.success("✅ Optimal Solution Found!")
                    st.metric("Optimal Makespan", f"{makespan.X}")
                    st.metric("Solution Time (s)", f"{end_time - start_time:.2f}")

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
                    st.error("❌ No optimal solution found.")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        with st.expander("ℹ️ Instructions"):
            st.write("""
            - Use the sidebar to input the number of jobs, machines, and task details.
            - Click the 'Optimize' button to solve the scheduling problem.
            - The optimal schedule and Gantt chart will be displayed.
            """)
        with st.expander("📜Constraints"):
            st.write(
                """
                - 🔗 **Consecutive Task Execution**: Two specified tasks must run consecutively, i.e., the start time of the second task must immediately follow the end time of the first task. This ensures that no gap exists between these tasks.
        
                - 🚫 **Non-Overlapping Tasks**: No two tasks assigned to the same machine can overlap in time. Tasks are scheduled sequentially on a single machine.
        
                - ⏳ **Precedence Constraints**: A task must be completed before another task can start if it depends on the first task's outcome.
        
                - ⚙️ **Machine Availability**: Each machine can process only one task at a time.
        
                - ⏲️ **Fixed Processing Times**: Tasks have predefined durations that cannot be changed during scheduling.
        
                - 🛠️ **Task Assignment**: Each task is assigned to exactly one machine as specified in the problem input.
        
                - 🕒 **Minimized Makespan**: The model minimizes the total time required to complete all tasks (makespan).
                """
            )


if __name__ == "__main__":
    main()
