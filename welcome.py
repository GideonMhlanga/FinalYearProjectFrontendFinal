import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Import database and utilities
from database import db
from data_generator import data_generator

# Create professional landing page
def show_landing_page():
    """Display the landing page content"""
    st.markdown(
        """
        <style>
        .hero {
            padding: 2rem;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
            text-align: center;
        }
        .feature-card {
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            background-color: white;
        }
        .dark-mode .feature-card {
            background-color: #2d2d2d;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        }
        .icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        .section-title {
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dark-mode .section-title {
            border-bottom: 2px solid #444;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Hero section
    st.markdown(
        """
        <div class="hero">
            <h1>Zimbabwe Hybrid Solar-Wind Monitoring System</h1>
            <p style="font-size: 1.2rem;">Comprehensive real-time monitoring and management for renewable energy systems</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Introduction
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>Welcome to the Next Generation of Energy Monitoring</h2>
            <p>Our advanced monitoring system provides complete visibility and control of your hybrid solar and wind installation. 
            Get real-time insights, optimize performance, and ensure reliable power generation.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Key features section
    st.markdown('<h2 class="section-title">Key Features</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">📊</div>
                <h3>Real-time Monitoring</h3>
                <p>Monitor power generation, consumption, and system performance in real-time with intuitive dashboards.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">🔋</div>
                <h3>Battery Management</h3>
                <p>Track battery state of charge, health, and performance metrics to maximize battery lifespan.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">🛠️</div>
                <h3>Predictive Maintenance</h3>
                <p>Anticipate system issues before they occur with AI-powered predictive maintenance and alerts.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">☁️</div>
                <h3>Weather Integration</h3>
                <p>Access local Zimbabwe weather forecasts to predict energy generation and optimize system operation.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">👥</div>
                <h3>User Management</h3>
                <p>Role-based access control ensures proper security and permission management for all system users.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="icon">⚙️</div>
                <h3>System Control</h3>
                <p>Adjust system parameters, manage power flow, and configure alerts from a centralized control panel.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # System overview section
    st.markdown('<h2 class="section-title">System Overview</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Create sample data for visualization
        energy_sources = ["Solar", "Wind", "Battery"]
        typical_values = [60, 30, 10]
        
        # Create a pie chart
        fig = px.pie(
            names=energy_sources,
            values=typical_values,
            color_discrete_sequence=["#FFD700", "#4682B4", "#32CD32"],
            hole=0.4,
            title="Typical Energy Distribution"
        )
        
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(
            """
            <div style="padding: 1rem;">
                <h3>System Benefits</h3>
                <ul>
                    <li><strong>Increased Efficiency</strong> - Optimize energy production and usage</li>
                    <li><strong>Reduced Downtime</strong> - Identify and address issues proactively</li>
                    <li><strong>Lower Costs</strong> - Maximize renewable energy utilization</li>
                    <li><strong>Extended Lifespan</strong> - Proper maintenance of all components</li>
                    <li><strong>Improved Reliability</strong> - Ensure consistent power availability</li>
                </ul>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Call to action
    st.markdown(
        """
        <div style="text-align: center; margin: 3rem 0; padding: 2rem; background-color: #f8f9fa; border-radius: 10px;">
            <h2>Ready to take control of your renewable energy system?</h2>
            <p style="font-size: 1.2rem; margin-bottom: 2rem;">Log in to access the full features of the Zimbabwe Hybrid Solar-Wind Monitoring System.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Login and registration section
    st.markdown('<h2 class="section-title">Account Access</h2>', unsafe_allow_html=True)
    
    # Create tabs for login and registration
    login_tab, register_tab = st.tabs(["Login", "Create Account"])
    
    # Login tab
    with login_tab:
        with st.form("login_form_welcome"):
            st.subheader("Log in to your account")
            
            # Add some space
            st.write("")
            
            username = st.text_input("Username", key="login_username_welcome")
            password = st.text_input("Password", type="password", key="login_password_welcome")
            
            # Add some space
            st.write("")
            
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                auth_result = data_generator.authenticate_user(username, password)
                if auth_result["authenticated"]:
                    st.session_state.user = username
                    st.session_state.role = auth_result["role"]
                    st.success(f"Welcome back, {username}! Redirecting to dashboard...")
                    time.sleep(1)  # Brief pause for user to see message
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    
    # Registration tab
    with register_tab:
        with st.form("register_form_welcome"):
            st.subheader("Create a new account")
            
            # Add some space
            st.write("")
            
            new_username = st.text_input("Username", key="reg_username_welcome")
            new_password = st.text_input("Password", type="password", key="reg_password_welcome")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password_welcome")
            
            # Additional profile fields
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="first_name_welcome")
            with col2:
                last_name = st.text_input("Last Name", key="last_name_welcome")
            
            col3, col4 = st.columns(2)
            with col3:
                email = st.text_input("Email", key="email_welcome")
            with col4:
                phone = st.text_input("Phone", key="phone_welcome")
            
            # User role selection
            st.subheader("User Type")
            role_options = {
                "administrator": "Administrator - Full system access and control",
                "owner": "Owner - Full access to all features",
                "maintenance": "Maintenance Team - System management and maintenance access",
                "operator": "Operator - Daily operations and monitoring",
                "readonly": "Viewer - View-only access to dashboards"
            }
            
            new_role = st.selectbox(
                "Select user type",
                options=list(role_options.keys()),
                format_func=lambda x: role_options[x],
                index=4,  # Default to readonly
                key="role_select_welcome"
            )
            
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
                <h4 style="margin-top: 0;">Selected Role: {role_options[new_role].split(' - ')[0]}</h4>
                <p style="margin-bottom: 0;">{role_options[new_role].split(' - ')[1]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Password requirements
            st.markdown(
                """
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 5px; margin: 1rem 0;">
                    <h4 style="margin-top: 0;">Password Requirements</h4>
                    <ul style="margin-bottom: 0;">
                        <li>At least 8 characters long</li>
                        <li>Include letters and numbers</li>
                    </ul>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif new_username in data_generator.get_users():
                    st.error(f"Username '{new_username}' is already taken")
                else:
                    # Create user account
                    result = data_generator.add_user(new_username, new_password, new_role)
                    
                    if result:
                        # Update user profile with additional information
                        profile_data = {
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "phone": phone
                        }
                        
                        db.update_user_profile(new_username, profile_data)
                        
                        st.success(f"Account created successfully! You can now login.")
                    else:
                        st.error("Failed to create account. Please try again.")
    
    # Footer
    st.markdown(
        """
        <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #f0f0f0;">
            <p>© 2025 Zimbabwe Renewable Energy</p>
            <p style="font-size: 0.8rem; color: #6c757d;">Empowering Zimbabwe with sustainable energy solutions</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Show landing page if not logged in
def main():
    # Check dark mode for styling
    if st.session_state.theme == "dark":
        st.markdown('<style>body { background-color: #1e1e1e; color: #ffffff; } .dark-mode-true { display: block; } .dark-mode-false { display: none; }</style>', unsafe_allow_html=True)
    
    # Show landing page if not logged in
    if "user" not in st.session_state or st.session_state.user is None:
        show_landing_page()

if __name__ == "__main__":
    main()