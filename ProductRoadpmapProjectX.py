import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Product Roadmap 2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the roadmap data structure
quarters = {
    "Q1 2025": {
        "title": "Foundation Phase",
        "subtitle": "Dirty Prototype Development",
        "months": {
            "January": {
                "objectives": [
                    "Component Procurement & Manufacturing",
                    "Complete frame design and fabrication",
                    "Setup testing infrastructure"
                ],
                "deliverables": [
                    "Procured COTS components",
                    "Custom manufactured parts",
                    "Testing protocols document",
                    "Quality control checklist"
                ],
                "milestones": [
                    "Frame assembly completion",
                    "Component validation",
                    "Testing rig setup"
                ]
            },
            "February": {
                "objectives": [
                    "Core system assembly",
                    "Basic control implementation",
                    "Power system integration"
                ],
                "deliverables": [
                    "Assembled hybrid platform",
                    "Integrated propulsion system",
                    "Basic control architecture",
                    "Power management system"
                ],
                "milestones": [
                    "Successful power-up test",
                    "Basic movement validation",
                    "Initial system integration"
                ]
            },
            "March": {
                "objectives": [
                    "Comprehensive testing",
                    "System optimization",
                    "Documentation"
                ],
                "deliverables": [
                    "Test results documentation",
                    "Performance metrics report",
                    "IP documentation",
                    "Technical specifications"
                ],
                "milestones": [
                    "Mode transition validation",
                    "Hover stability achievement",
                    "Power efficiency validation"
                ]
            }
        }
    },
    "Q2 2025": {
        "title": "MVP Development",
        "subtitle": "First Market-Ready Version",
        "months": {
            "April": {
                "objectives": [
                    "Advanced system integration",
                    "AI/ML implementation",
                    "Navigation system setup"
                ],
                "deliverables": [
                    "AI/ML system integration",
                    "Advanced navigation module",
                    "Modular interface design",
                    "System architecture document"
                ],
                "milestones": [
                    "AI system validation",
                    "Navigation testing completion",
                    "Interface standardization"
                ]
            },
            "May": {
                "objectives": [
                    "Cleaning mechanism development",
                    "Autonomous features implementation",
                    "Cloud integration"
                ],
                "deliverables": [
                    "Working cleaning mechanism",
                    "Autonomous control system",
                    "Cloud connectivity setup",
                    "System monitoring dashboard"
                ],
                "milestones": [
                    "Cleaning efficiency validation",
                    "Autonomous operation testing",
                    "Cloud system integration"
                ]
            },
            "June": {
                "objectives": [
                    "Field testing program",
                    "Customer demonstration",
                    "Documentation completion"
                ],
                "deliverables": [
                    "Field test reports",
                    "Customer demo unit",
                    "Complete technical documentation",
                    "User manuals"
                ],
                "milestones": [
                    "Successful field trials",
                    "Customer feedback collection",
                    "MVP completion"
                ]
            }
        }
    },
    "Q3 2025": {
        "title": "Scale & Enhance",
        "subtitle": "Production & Feature Enhancement",
        "months": {
            "July": {
                "objectives": [
                    "Production setup",
                    "Feature enhancement planning",
                    "Supply chain establishment"
                ],
                "deliverables": [
                    "Production line setup",
                    "Enhanced feature list",
                    "Supply chain documentation",
                    "Quality control processes"
                ],
                "milestones": [
                    "Production line validation",
                    "Component supplier agreements",
                    "Process optimization"
                ]
            },
            "August": {
                "objectives": [
                    "Swarm technology development",
                    "Docking system implementation",
                    "Production scaling"
                ],
                "deliverables": [
                    "Swarm control system",
                    "Automated docking mechanism",
                    "Production metrics dashboard",
                    "Batch testing protocols"
                ],
                "milestones": [
                    "Swarm operation validation",
                    "Docking system testing",
                    "Production target achievement"
                ]
            },
            "September": {
                "objectives": [
                    "Multi-unit production",
                    "System optimization",
                    "Market preparation"
                ],
                "deliverables": [
                    "10-unit production batch",
                    "Optimization reports",
                    "Market launch plan",
                    "Support infrastructure"
                ],
                "milestones": [
                    "Production milestone (10 units)",
                    "System reliability validation",
                    "Market readiness assessment"
                ]
            }
        }
    },
    "Q4 2025": {
        "title": "Market Launch",
        "subtitle": "Full Scale Production & PMF",
        "months": {
            "October": {
                "objectives": [
                    "Production acceleration",
                    "Market testing",
                    "Support system establishment"
                ],
                "deliverables": [
                    "Increased production capacity",
                    "Market testing reports",
                    "Support system setup",
                    "Service protocols"
                ],
                "milestones": [
                    "Production scaling validation",
                    "Market response analysis",
                    "Support system validation"
                ]
            },
            "November": {
                "objectives": [
                    "PMF validation",
                    "Production optimization",
                    "Service network expansion"
                ],
                "deliverables": [
                    "PMF metrics report",
                    "Optimized production system",
                    "Extended service network",
                    "Customer success stories"
                ],
                "milestones": [
                    "PMF achievement",
                    "Production efficiency targets",
                    "Service coverage goals"
                ]
            },
            "December": {
                "objectives": [
                    "Full scale production",
                    "Market expansion planning",
                    "2026 strategy development"
                ],
                "deliverables": [
                    "25-unit inventory",
                    "Market expansion roadmap",
                    "2026 strategic plan",
                    "Annual performance report"
                ],
                "milestones": [
                    "Production target (25 units)",
                    "Market expansion readiness",
                    "2026 planning completion"
                ]
            }
        }
    }
}
def create_timeline():
    """Create a timeline visualization using Plotly"""
    df = pd.DataFrame([
        dict(Task="Q1: Foundation", Start='2025-01-01', Finish='2025-03-31', Type='quarter'),
        dict(Task="Q2: MVP", Start='2025-04-01', Finish='2025-06-30', Type='quarter'),
        dict(Task="Q3: Scale", Start='2025-07-01', Finish='2025-09-30', Type='quarter'),
        dict(Task="Q4: Launch", Start='2025-10-01', Finish='2025-12-31', Type='quarter'),
    ])
    
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Type")
    fig.update_layout(
        showlegend=False,
        height=200,
        title="2025 Product Development Timeline"
    )
    return fig

def main():
    """Main application function"""
    st.title("Product Roadmap 2025: Hybrid Drone-Rover Platform")
    
    # Display timeline
    st.plotly_chart(create_timeline(), use_container_width=True)
    
    # Quarter selection
    selected_quarter = st.selectbox(
        "Select Quarter to View Details",
        list(quarters.keys())
    )
    
    # Display quarter information
    st.header(f"{selected_quarter}: {quarters[selected_quarter]['title']}")
    st.subheader(quarters[selected_quarter]['subtitle'])
    
    # Create three columns for months
    cols = st.columns(3)
    
    # Display month details
    for idx, (month, data) in enumerate(quarters[selected_quarter]['months'].items()):
        with cols[idx]:
            st.markdown(f"### {month}")
            
            # Objectives
            st.markdown("**Objectives:**")
            for obj in data['objectives']:
                st.markdown(f"- {obj}")
            
            # Deliverables
            st.markdown("**Deliverables:**")
            for deliv in data['deliverables']:
                st.markdown(f"- {deliv}")
            
            # Milestones
            st.markdown("**Milestones:**")
            for mile in data['milestones']:
                st.markdown(f"- {mile}")
    
    # Add metrics section
    st.header("Key Metrics")
    metric_cols = st.columns(4)
    
    # Example metrics - you can modify these
    with metric_cols[0]:
        st.metric(label="Development Progress", value="25%", delta="On Track")
    with metric_cols[1]:
        st.metric(label="Budget Utilization", value="30%", delta="-5%")
    with metric_cols[2]:
        st.metric(label="Milestones Completed", value="8/32", delta="2")
    with metric_cols[3]:
        st.metric(label="Risk Level", value="Low", delta="Stable")

if __name__ == "__main__":
    main()