import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# Page config
st.set_page_config(
    page_title="MCA Insights Engine",
    page_icon="🏢",
    layout="wide"
)

# Title
st.title("🏢 MCA Insights Engine")
st.markdown("AI-Powered Company Master Data Tracker")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Search Companies", "Change Analysis", "AI Chat"])

# Helper functions
@st.cache_data
def load_master_data():
    """Load master dataset with error handling"""
    try:
        return pd.read_csv('data/processed/master_dataset.csv')
    except Exception as e:
        st.error(f"Error loading master dataset: {e}")
        return pd.DataFrame()

@st.cache_data
def load_changes(day):
    """Load change data with error handling"""
    try:
        return pd.read_csv(f'data/changes/day{day}_changes.csv')
    except Exception as e:
        return pd.DataFrame()

def get_available_change_days():
    """Get list of available change log days"""
    change_dir = Path('data/changes')
    if not change_dir.exists():
        return []
    
    days = []
    for file in change_dir.glob('day*_changes.csv'):
        try:
            day_num = int(file.stem.replace('day', '').replace('_changes', ''))
            days.append(day_num)
        except:
            pass
    
    return sorted(days)

def process_query(query, master_df):
    """Simple query processor"""
    query_lower = query.lower()
    
    try:
        # Statistics query
        if "statistics" in query_lower or "stats" in query_lower:
            stats = f"""
**Dataset Statistics:**

- Total Companies: {len(master_df):,}
- Columns Available: {', '.join(master_df.columns)}
"""
            if 'STATE' in master_df.columns:
                stats += f"\n\n**State Distribution:**\n"
                for state, count in master_df['STATE'].value_counts().items():
                    stats += f"- {state}: {count:,}\n"
            
            if 'COMPANY_STATUS' in master_df.columns:
                stats += f"\n**Top Statuses:**\n"
                for status, count in master_df['COMPANY_STATUS'].value_counts().head(5).items():
                    stats += f"- {status}: {count:,}\n"
            
            return stats
        
        # Active companies
        elif "active" in query_lower and "how many" in query_lower:
            if 'COMPANY_STATUS' in master_df.columns:
                active = len(master_df[master_df['COMPANY_STATUS'] == 'ACTIVE'])
                return f"There are **{active:,}** active companies in the dataset."
            else:
                return "Company status information is not available in the dataset."
        
        # By status
        elif "by status" in query_lower or "status" in query_lower:
            if 'COMPANY_STATUS' in master_df.columns:
                status_counts = master_df['COMPANY_STATUS'].value_counts()
                result = "**Companies by Status:**\n\n"
                for status, count in status_counts.items():
                    result += f"- {status}: {count:,}\n"
                return result
            else:
                return "Company status information is not available."
        
        # Date range
        elif "date range" in query_lower:
            if 'DATE_OF_INCORPORATION' in master_df.columns:
                dates = pd.to_datetime(master_df['DATE_OF_INCORPORATION'], errors='coerce')
                min_date = dates.min()
                max_date = dates.max()
                return f"Incorporation dates range from **{min_date.strftime('%Y-%m-%d')}** to **{max_date.strftime('%Y-%m-%d')}**"
            else:
                return "Date information is not available."
        
        # Top companies
        elif "top" in query_lower:
            cols_to_show = [col for col in ['COMPANY_NAME', 'STATE', 'COMPANY_STATUS'] if col in master_df.columns]
            if cols_to_show:
                return master_df[cols_to_show].head(10).to_string()
            else:
                return "Unable to display companies with available columns."
        
        else:
            return "I can help you with:\n- Statistics for all states\n- Count of active companies\n- Companies by status\n- Date ranges\n- Top companies\n\nTry one of the sample queries above!"
    
    except Exception as e:
        return f"Error processing query: {e}"

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    
    # Load data
    master_df = load_master_data()
    
    if master_df.empty:
        st.warning("⚠️ No data loaded. Please run the processing script first.")
        st.code("python process.py", language="bash")
        st.stop()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_companies = len(master_df)
    active_companies = len(master_df[master_df['COMPANY_STATUS'] == 'ACTIVE']) if 'COMPANY_STATUS' in master_df.columns else 0
    
    with col1:
        st.metric("Total Companies", f"{total_companies:,}")
    
    with col2:
        # Try to get today's changes
        available_days = get_available_change_days()
        if available_days:
            latest_day = max(available_days)
            changes = load_changes(latest_day)
            new_today = len(changes[changes['Change_Type'] == 'NEW_INCORPORATION']) if not changes.empty and 'Change_Type' in changes.columns else 0
            st.metric("New (Latest)", new_today)
        else:
            st.metric("New (Latest)", "N/A")
    
    with col3:
        if available_days:
            latest_day = max(available_days)
            changes = load_changes(latest_day)
            status_changes = len(changes[changes['Change_Type'] == 'STATUS_CHANGE']) if not changes.empty and 'Change_Type' in changes.columns else 0
            st.metric("Status Changes", status_changes)
        else:
            st.metric("Status Changes", "N/A")
    
    with col4:
        st.metric("Active Companies", f"{active_companies:,}")
    
    # State-wise distribution
    st.subheader("State-wise Company Distribution")
    
    if 'STATE' in master_df.columns:
        state_counts = master_df['STATE'].value_counts().reset_index()
        state_counts.columns = ['State', 'Count']
        
        fig = px.bar(
            state_counts, 
            x='State', 
            y='Count',
            title="Companies by State",
            color='Count',
            color_continuous_scale='Blues',
            labels={'Count': 'Number of Companies', 'State': 'State'}
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="State",
            yaxis_title="Number of Companies",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("State information not available in dataset")
    
    # Recent changes timeline
    st.subheader("Recent Changes Timeline")
    
    available_days = get_available_change_days()
    
    if available_days:
        all_changes = []
        for day in available_days:
            changes = load_changes(day)
            if not changes.empty:
                all_changes.append(changes)
        
        if all_changes:
            changes_df = pd.concat(all_changes, ignore_index=True)
            
            if 'Date' in changes_df.columns and 'Change_Type' in changes_df.columns:
                # Convert Date to proper datetime format
                changes_df['Date'] = pd.to_datetime(changes_df['Date'], errors='coerce')
                
                # Group by date and change type
                change_timeline = changes_df.groupby(['Date', 'Change_Type']).size().reset_index(name='Count')
                
                # Sort by date
                change_timeline = change_timeline.sort_values('Date')
                
                # Format date for better display
                change_timeline['Date_Display'] = change_timeline['Date'].dt.strftime('%b %d, %Y')
                
                fig = px.line(
                    change_timeline,
                    x='Date_Display',
                    y='Count',
                    color='Change_Type',
                    title="Change Types Over Time",
                    labels={'Date_Display': 'Date', 'Count': 'Number of Changes', 'Change_Type': 'Change Type'},
                    markers=True
                )
                
                # Update layout for better appearance
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Changes",
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Change type information not available")
        else:
            st.info("No change data available yet")
    else:
        st.info("No change logs generated yet. Changes will appear here after running multiple snapshots.")

# ============================================================================
# SEARCH COMPANIES PAGE
# ============================================================================

elif page == "Search Companies":
    st.header("🔍 Search Companies")
    
    master_df = load_master_data()
    
    if master_df.empty:
        st.warning("⚠️ No data loaded. Please run the processing script first.")
        st.stop()
    
    search_type = st.radio("Search by:", ["CIN", "Company Name"])
    
    if search_type == "CIN":
        cin_input = st.text_input("Enter CIN:", placeholder="U12345MH2020PTC123456")
        
        if st.button("Search") and cin_input:
            if 'CIN' in master_df.columns:
                result = master_df[master_df['CIN'].str.contains(cin_input, case=False, na=False)]
                
                if not result.empty:
                    st.success(f"Found {len(result)} company(ies)")
                    st.dataframe(result, width='stretch')
                else:
                    st.warning("No company found with this CIN")
            else:
                st.error("CIN column not found in dataset")
    
    else:
        name_input = st.text_input("Enter Company Name:", placeholder="ABC Private Limited")
        
        if st.button("Search") and name_input:
            if 'COMPANY_NAME' in master_df.columns:
                result = master_df[master_df['COMPANY_NAME'].str.contains(name_input, case=False, na=False)]
                
                if not result.empty:
                    st.success(f"Found {len(result)} companies")
                    
                    # Show relevant columns
                    display_cols = ['CIN', 'COMPANY_NAME', 'STATE', 'COMPANY_STATUS', 'DATE_OF_INCORPORATION']
                    available_cols = [col for col in display_cols if col in result.columns]
                    
                    st.dataframe(result[available_cols].head(100), width='stretch')
                    
                    if len(result) > 100:
                        st.info(f"Showing first 100 of {len(result)} results")
                else:
                    st.warning("No companies found")
            else:
                st.error("COMPANY_NAME column not found in dataset")
    
    # Filters
    st.subheader("Filter Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'STATE' in master_df.columns:
            states = master_df['STATE'].dropna().unique().tolist()
            state_filter = st.multiselect("State", states)
        else:
            st.info("State filter not available")
            state_filter = []
    
    with col2:
        if 'COMPANY_STATUS' in master_df.columns:
            statuses = master_df['COMPANY_STATUS'].dropna().unique().tolist()
            status_filter = st.multiselect("Status", statuses[:10])  # Limit to 10
        else:
            st.info("Status filter not available")
            status_filter = []
    
    with col3:
        if 'DATE_OF_INCORPORATION' in master_df.columns:
            try:
                master_df['DATE_OF_INCORPORATION'] = pd.to_datetime(master_df['DATE_OF_INCORPORATION'], errors='coerce')
                min_year = int(master_df['DATE_OF_INCORPORATION'].dt.year.min())
                max_year = int(master_df['DATE_OF_INCORPORATION'].dt.year.max())
                year_filter = st.slider("Incorporation Year", min_year, max_year, (min_year, max_year))
            except:
                st.info("Year filter not available")
                year_filter = None
        else:
            year_filter = None
    
    if st.button("Apply Filters"):
        filtered_df = master_df.copy()
        
        if state_filter and 'STATE' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['STATE'].isin(state_filter)]
        
        if status_filter and 'COMPANY_STATUS' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['COMPANY_STATUS'].isin(status_filter)]
        
        if year_filter and 'DATE_OF_INCORPORATION' in filtered_df.columns:
            filtered_df['year'] = pd.to_datetime(filtered_df['DATE_OF_INCORPORATION'], errors='coerce').dt.year
            filtered_df = filtered_df[(filtered_df['year'] >= year_filter[0]) & (filtered_df['year'] <= year_filter[1])]
        
        st.success(f"Found {len(filtered_df):,} companies")
        
        display_cols = ['CIN', 'COMPANY_NAME', 'STATE', 'COMPANY_STATUS', 'DATE_OF_INCORPORATION']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        st.dataframe(filtered_df[available_cols].head(100), width='stretch')

# ============================================================================
# CHANGE ANALYSIS PAGE
# ============================================================================

elif page == "Change Analysis":
    st.header("📈 Change Analysis")
    
    # Get available days
    available_days = get_available_change_days()
    
    if not available_days:
        st.warning("⚠️ No change logs found. Run the processing script to generate change logs.")
        st.info("Change logs will be created when you process data on multiple dates.")
        st.stop()
    
    day_select = st.selectbox("Select Day", available_days)
    
    changes_df = load_changes(day_select)
    
    if changes_df.empty:
        st.warning(f"No change data available for Day {day_select}")
        st.stop()
    
    st.subheader(f"Day {day_select} Summary")
    
    # Check if required columns exist
    has_change_type = 'Change_Type' in changes_df.columns
    
    col1, col2, col3, col4 = st.columns(4)
    
    if has_change_type:
        with col1:
            new_inc = len(changes_df[changes_df['Change_Type'] == 'NEW_INCORPORATION'])
            st.metric("New Incorporations", new_inc)
        
        with col2:
            dereg = len(changes_df[changes_df['Change_Type'] == 'DEREGISTRATION'])
            st.metric("Deregistrations", dereg)
        
        with col3:
            status_ch = len(changes_df[changes_df['Change_Type'] == 'STATUS_CHANGE'])
            st.metric("Status Changes", status_ch)
        
        with col4:
            capital_ch = len(changes_df[changes_df['Change_Type'] == 'CAPITAL_CHANGE'])
            st.metric("Capital Changes", capital_ch)
        
        # Change type distribution
        st.subheader("Change Type Distribution")
        change_dist = changes_df['Change_Type'].value_counts()
        
        fig = px.pie(
            values=change_dist.values,
            names=change_dist.index,
            title="Distribution of Change Types"
        )
        st.plotly_chart(fig, width='stretch')
    else:
        with col1:
            st.metric("Total Changes", len(changes_df))
    
    # Recent changes table
    st.subheader("Recent Changes")
    st.dataframe(changes_df.head(50), width='stretch')
    
    # Download option
    csv = changes_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Change Log",
        data=csv,
        file_name=f"day{day_select}_changes.csv",
        mime="text/csv"
    )

# ============================================================================
# AI CHAT PAGE
# ============================================================================

elif page == "AI Chat":
    st.header("💬 Chat with MCA Data")
    
    st.info("Ask questions about company data in natural language")
    
    master_df = load_master_data()
    
    if master_df.empty:
        st.warning("⚠️ No data loaded. Please run the processing script first.")
        st.stop()
    
    # Sample queries
    st.subheader("Sample Queries:")
    
    sample_queries = [
        "Show statistics for all states",
        "How many companies are active?",
        "Show companies by status",
        "What is the date range of incorporations?",
        "Show top 10 companies"
    ]
    
    for query in sample_queries:
        if st.button(query, key=query):
            st.session_state['user_query'] = query
    
    # Chat interface
    user_input = st.text_input(
        "Your question:",
        value=st.session_state.get('user_query', ''),
        placeholder="Ask about companies, statistics, trends..."
    )
    
    if st.button("Ask"):
        if user_input:
            with st.spinner("Analyzing..."):
                response = process_query(user_input, master_df)
                st.success("Answer:")
                st.write(response)
        else:
            st.warning("Please enter a question")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("MCA Insights Engine v1.0")
st.sidebar.caption("Built for MCA data analysis")
