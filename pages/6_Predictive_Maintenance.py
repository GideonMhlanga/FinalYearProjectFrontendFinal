import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
from data_generator import data_generator
from utils import get_status_color

# Configure the page
st.set_page_config(
    page_title="Predictive Maintenance | Solar-Wind Hybrid Monitor",
    page_icon="🔧",
    layout="wide"
)

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Title and description
st.title("Predictive Maintenance")
st.write("AI-powered predictive analytics to monitor system health and prevent failures")

# Function to refresh data
def refresh_data():
    return {}  # No specific data needed for this page

# Initialize component selection
if "selected_component" not in st.session_state:
    st.session_state.selected_component = "solar_panel"

# Initialize analysis status
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False

# Generate random components for simulation
components = ["solar_panel", "wind_turbine", "battery", "inverter"]
component_names = {
    "solar_panel": "Solar Panel Array",
    "wind_turbine": "Wind Turbine",
    "battery": "Battery System",
    "inverter": "Power Inverter"
}

# Sidebar component selection
st.sidebar.subheader("Component Analysis")
selected_component = st.sidebar.selectbox(
    "Select Component to Analyze",
    components,
    format_func=lambda x: component_names.get(x, x),
    index=components.index(st.session_state.selected_component)
)
st.session_state.selected_component = selected_component

# Run analysis button
if st.sidebar.button("Run Predictive Analysis", key="run_analysis"):
    st.session_state.analysis_running = True
    with st.spinner(f"Running analysis for {component_names[selected_component]}..."):
        # Run the predictive analysis for the selected component
        data_generator.generate_predictive_analysis(selected_component)
        time.sleep(1)  # Small delay for better UX
    st.session_state.analysis_running = False
    st.success("Analysis completed!")
    time.sleep(1)
    st.rerun()  # Refresh to show the new analysis

# System Health Overview
st.subheader("System Health Overview")

# Get component health status
health_data = data_generator.get_component_health()

# Check if we have health data
if health_data:
    # Create columns for component health cards
    columns = st.columns(len(components))
    
    for i, component in enumerate(components):
        with columns[i]:
            # Get health data for component
            component_health = health_data.get(component)
            
            if component_health:
                health_score = component_health.get("health_score", 0)
                predicted_date = component_health.get("predicted_failure_date")
                
                # Format predicted failure date
                if predicted_date:
                    try:
                        date_obj = datetime.fromisoformat(predicted_date.replace('Z', '+00:00'))
                        days_until = (date_obj - datetime.now()).days
                        if days_until > 0:
                            failure_text = f"Predicted failure: {days_until} days"
                        else:
                            failure_text = "Immediate attention needed"
                    except:
                        failure_text = "Unknown"
                else:
                    failure_text = "No prediction available"
                
                # Determine status color
                status_color = get_status_color(health_score, 
                                             {"green": (85, 100), 
                                              "yellow": (70, 85), 
                                              "red": (0, 70)})
                
                # Create health gauge
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=health_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': component_names[component], 'font': {'size': 18}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "green" if status_color == "green" else "orange" if status_color == "yellow" else "red"},
                        'steps': [
                            {'range': [0, 70], 'color': "#ffcccc"},
                            {'range': [70, 85], 'color': "#ffffcc"},
                            {'range': [85, 100], 'color': "#ccffcc"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': health_score
                        }
                    }
                ))
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=10, r=10, t=60, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display prediction information
                st.caption(failure_text)
                
                # Maintenance recommendation
                if component_health.get("maintenance_recommended", False):
                    st.warning(component_health.get("recommendation", "Maintenance recommended"))
            else:
                # Display empty gauge with no data
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=0,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': component_names[component], 'font': {'size': 18}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "gray"},
                        'steps': [
                            {'range': [0, 70], 'color': "#f0f0f0"},
                            {'range': [70, 85], 'color': "#f5f5f5"},
                            {'range': [85, 100], 'color': "#fafafa"}
                        ]
                    }
                ))
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=10, r=10, t=60, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.caption("No data available")
                st.info("Run analysis to generate health data")
else:
    st.info("No component health data available. Run analysis for each component to generate health data.")

# Detailed component analysis
st.subheader(f"Detailed Analysis: {component_names.get(selected_component, selected_component)}")

# Get maintenance data for the selected component
maintenance_data = data_generator.get_predictive_maintenance(selected_component)

if maintenance_data:
    # Get the most recent analysis
    latest_analysis = maintenance_data[0]
    
    # Extract data
    health_score = latest_analysis.get("health_score", 0)
    prediction_date = latest_analysis.get("timestamps", "")
    failure_date = latest_analysis.get("predicted_failure_date")
    recommendation = latest_analysis.get("recommendation", "No specific recommendations")
    confidence = latest_analysis.get("confidence", 0) * 100  # Convert to percentage
    maintenance_cost = latest_analysis.get("maintenance_cost", 0)
    failure_cost = latest_analysis.get("failure_cost", 0)
    
    # Create two columns for information display
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display recommendation and insights
        st.subheader("Insights & Recommendations")
        
        # Health status
        if health_score >= 85:
            st.success(f"Component Health Score: {health_score:.1f}% (Good)")
            st.write("The component is in good condition and operating within expected parameters.")
        elif health_score >= 70:
            st.warning(f"Component Health Score: {health_score:.1f}% (Fair)")
            st.write("The component is showing signs of wear but still operational. Consider scheduling maintenance.")
        else:
            st.error(f"Component Health Score: {health_score:.1f}% (Poor)")
            st.write("The component requires immediate attention to prevent failure.")
        
        # Display failure prediction if available
        if failure_date:
            try:
                date_obj = datetime.fromisoformat(failure_date.replace('Z', '+00:00'))
                days_until = (date_obj - datetime.now()).days
                
                if days_until > 365:
                    st.info(f"Estimated time to failure: {days_until // 365} years, {days_until % 365} days")
                elif days_until > 0:
                    st.info(f"Estimated time to failure: {days_until} days")
                else:
                    st.error("Component has reached end of life and requires replacement")
            except:
                st.info("Failure prediction unavailable")
        
        # Specific recommendations
        st.subheader("Maintenance Recommendations")
        st.write(recommendation)
        
        # Cost Analysis
        st.subheader("Cost Analysis")
        
        # Calculate the cost of maintenance vs failure
        cost_difference = failure_cost - maintenance_cost
        savings_pct = (cost_difference / failure_cost * 100) if failure_cost > 0 else 0
        
        cost_data = {
            "Type": ["Preventive Maintenance", "Failure Replacement"],
            "Cost": [maintenance_cost, failure_cost]
        }
        
        cost_df = pd.DataFrame(cost_data)
        
        # Create bar chart for cost comparison
        fig = px.bar(
            cost_df, 
            x="Type", 
            y="Cost", 
            color="Type",
            color_discrete_map={
                "Preventive Maintenance": "#4CAF50", 
                "Failure Replacement": "#F44336"
            },
            text_auto=True
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if cost_difference > 0:
            st.success(f"Potential savings: ${cost_difference:.2f} ({savings_pct:.1f}%)")
    
    with col2:
        # Confidence score
        st.subheader("Prediction Confidence")
        
        # Create gauge for confidence
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={'suffix': "%"},
            title={'text': "Confidence Score"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [0, 40], 'color': "#ffcccc"},
                    {'range': [40, 70], 'color': "#ffffcc"},
                    {'range': [70, 100], 'color': "#ccffcc"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': confidence
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display confidence interpretation
        if confidence >= 70:
            st.success("High confidence prediction based on robust data analysis")
        elif confidence >= 40:
            st.info("Moderate confidence prediction - consider collecting more data")
        else:
            st.warning("Low confidence prediction - limited data available")
        
        # Display when the analysis was done
        try:
            analysis_time = datetime.fromisoformat(prediction_date.replace('Z', '+00:00'))
            st.caption(f"Analysis performed: {analysis_time.strftime('%Y-%m-%d %H:%M')}")
        except:
            st.caption("Analysis time unknown")
        
        # Display technical details expandable section
        with st.expander("Technical Analysis Details"):
            # Extract analysis data
            analysis_data = latest_analysis.get("analysis_data", {})
            
            if analysis_data:
                # Convert analysis data to DataFrame for display
                analysis_df = pd.DataFrame(list(analysis_data.items()), columns=["Metric", "Value"])
                st.dataframe(analysis_df, use_container_width=True)
            else:
                st.write("No detailed analysis data available")
    
    # Historical data section
    if len(maintenance_data) > 1:
        st.subheader("Health Trend Analysis")
        
        # Create DataFrame from historical data
        history_df = pd.DataFrame([
            {
                "date": item.get("timestamps"),
                "health_score": item.get("health_score"),
                "recommendation": item.get("recommendation"),
                "confidence": item.get("confidence") * 100 if item.get("confidence") else 0
            }
            for item in maintenance_data
        ])
        
        # Convert dates
        history_df["date"] = pd.to_datetime(history_df["date"])
        history_df = history_df.sort_values("date")
        
        # Plot health score trend
        fig = px.line(
            history_df, 
            x="date", 
            y="health_score",
            markers=True,
            title="Component Health Score Over Time",
            labels={"date": "Date", "health_score": "Health Score (%)"}
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Health Score (%)",
            yaxis=dict(range=[0, 100]),
            hovermode="x unified",
            margin=dict(l=60, r=20, t=50, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        # Add horizontal lines for threshold zones
        fig.add_shape(
            type="line",
            x0=history_df["date"].min(),
            y0=85,
            x1=history_df["date"].max(),
            y1=85,
            line=dict(color="green", width=2, dash="dash")
        )
        
        fig.add_shape(
            type="line",
            x0=history_df["date"].min(),
            y0=70,
            x1=history_df["date"].max(),
            y1=70,
            line=dict(color="red", width=2, dash="dash")
        )
        
        # Add annotations
        fig.add_annotation(
            x=history_df["date"].min(),
            y=92,
            text="Good",
            showarrow=False,
            font=dict(color="green")
        )
        
        fig.add_annotation(
            x=history_df["date"].min(),
            y=77,
            text="Fair",
            showarrow=False,
            font=dict(color="orange")
        )
        
        fig.add_annotation(
            x=history_df["date"].min(),
            y=60,
            text="Poor",
            showarrow=False,
            font=dict(color="red")
        )
        
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"No analysis data available for {component_names.get(selected_component, selected_component)}. Run analysis to generate data.")

# Maintenance Schedule
st.subheader("Maintenance Schedule")

# Create mock maintenance schedule based on component health
if health_data:
    # Create schedule data
    schedule_data = []
    
    for component, data in health_data.items():
        if data and data.get("maintenance_recommended", False):
            health_score = data.get("health_score", 0)
            
            # Determine urgency based on health score
            if health_score < 50:
                due_date = datetime.now() + timedelta(days=7)  # 1 week
                priority = "High"
            elif health_score < 70:
                due_date = datetime.now() + timedelta(days=30)  # 1 month
                priority = "Medium"
            else:
                due_date = datetime.now() + timedelta(days=90)  # 3 months
                priority = "Low"
            
            schedule_data.append({
                "Component": component_names.get(component, component),
                "Task": data.get("recommendation", "Perform inspection"),
                "Due Date": due_date.strftime("%Y-%m-%d"),
                "Priority": priority,
                "Status": "Scheduled"
            })
    
    if schedule_data:
        # Create DataFrame for display
        schedule_df = pd.DataFrame(schedule_data)
        
        # Apply conditional formatting
        def color_priority(val):
            if val == "High":
                return 'background-color: #ffcccc'
            elif val == "Medium":
                return 'background-color: #ffffcc'
            elif val == "Low":
                return 'background-color: #ccffcc'
            return ''
        
        # Display styled DataFrame
        st.dataframe(
            schedule_df.style.applymap(color_priority, subset=["Priority"]),
            use_container_width=True
        )
    else:
        st.info("No maintenance tasks currently scheduled")
else:
    st.info("Run component analysis to generate maintenance schedule recommendations")

# Initialize learned assignments in session state if not exists
if 'learned_assignments' not in st.session_state:
    st.session_state.learned_assignments = {}

# Add New Task (outside expander)
st.subheader("Add New Maintenance Task")
with st.expander("Create New Task"):
    col1, col2 = st.columns(2)
    
    with col1:
        new_component = st.selectbox(
            "Component", 
            ["Solar Panels", "Wind Turbine", "Battery Bank", "Inverter", "Control System"],
            key="new_component_main"  # Unique key
        )
        new_task = st.text_input("Task Description", key="task_desc_main")  # Unique key
        new_priority = st.selectbox(
            "Priority", 
            ["High", "Medium", "Low"],
            key="priority_main"  # Unique key
        )
    
    with col2:
        new_due_date = st.date_input("Due Date", key="due_date_main")  # Unique key
        new_assigned = st.selectbox(
            "Assign To", 
            ["Tech Team A", "Tech Team B", "Tech Team C"],
            key="assign_to_main"  # Unique key
        )
    
    if st.button("Add Task", key="add_task_main"):  # Unique key
        st.success("New maintenance task added successfully!")

        # Get learned assignments for the selected component
        component_assignments = st.session_state.learned_assignments.get(new_component, [])
        default_assignments = ["Tech Team A", "Tech Team B", "Tech Team C"]
        all_assignments = list(set(default_assignments + component_assignments))

        # Add option for custom assignment
        all_assignments.append("+ Add Custom Assignment")

        new_assigned = st.selectbox(
            "Assign To",
            all_assignments,
            help="Select from previous assignments or add a new one"
        )

        # Show text input if custom assignment selected
        if new_assigned == "+ Add Custom Assignment":
            custom_assigned = st.text_input("Enter Custom Assignment")
            new_assigned = custom_assigned if custom_assigned else None

            st.success("New maintenance task added successfully!")
            # Show learned assignments for this component
            if new_component in st.session_state.learned_assignments:
                st.info(f"Learned assignments for {new_component}: {', '.join(st.session_state.learned_assignments[new_component])}")
        else:
            st.error("Please specify an assignment")

# Maintenance Tasks Management
st.subheader("Maintenance Tasks")

# Create tabs for different task views
task_tab1, task_tab2, task_tab3 = st.tabs(["Pending Tasks", "Completed Tasks", "All Tasks"])

# Sample maintenance tasks
maintenance_tasks = [
    {"id": 1, "component": "Solar Panels", "task": "Clean solar panels", "due_date": "2024-02-15", "status": "Pending", "priority": "High", "assigned_to": "Tech Team A"},
    {"id": 2, "component": "Wind Turbine", "task": "Bearing lubrication", "due_date": "2024-02-20", "status": "Completed", "completion_date": "2024-01-20", "priority": "Medium"},
    {"id": 3, "component": "Battery Bank", "task": "Cell inspection", "due_date": "2024-03-01", "status": "Pending", "priority": "High", "assigned_to": "Tech Team B"},
    {"id": 4, "component": "Inverter", "task": "Firmware update", "due_date": "2024-02-28", "status": "Pending", "priority": "Medium", "assigned_to": "Tech Team A"},
    {"id": 5, "component": "Solar Panels", "task": "Connection check", "due_date": "2024-01-15", "status": "Completed", "completion_date": "2024-01-14", "priority": "Low"}
]

# Pending Tasks Tab
with task_tab1:
    st.markdown("### Pending Maintenance Tasks")
    pending_tasks = [task for task in maintenance_tasks if task["status"] == "Pending"]
    
    if pending_tasks:
        for task in pending_tasks:
            with st.expander(f"{task['component']} - {task['task']} (Due: {task['due_date']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Priority:** {task['priority']}")
                    st.markdown(f"**Assigned to:** {task['assigned_to']}")
                with col2:
                    if st.button("Mark Complete", key=f"complete_{task['id']}"):
                        st.success("Task marked as complete!")
    else:
        st.info("No pending tasks")

# Completed Tasks Tab
with task_tab2:
    st.markdown("### Completed Maintenance Tasks")
    completed_tasks = [task for task in maintenance_tasks if task["status"] == "Completed"]
    
    if completed_tasks:
        for task in completed_tasks:
            with st.expander(f"{task['component']} - {task['task']} (Completed: {task['completion_date']})"):
                st.markdown(f"**Priority:** {task['priority']}")
                st.markdown(f"**Due Date:** {task['due_date']}")
    else:
        st.info("No completed tasks")

# All Tasks Tab
with task_tab3:
    st.markdown("### All Maintenance Tasks")
    
    # Create DataFrame for better display
    df_tasks = pd.DataFrame(maintenance_tasks)
    
    # Add status indicator
    def color_status(val):
        color = "red" if val == "Pending" else "green"
        return f'color: {color}'
    
    # Display styled DataFrame
    st.dataframe(
        df_tasks.style.map(color_status, subset=["status"]),
        use_container_width=True
    )


# Footer
st.divider()
st.caption("The predictive maintenance system uses machine learning algorithms to analyze system performance and predict potential failures before they occur.")