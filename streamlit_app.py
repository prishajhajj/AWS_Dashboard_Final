import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="AWS EC2 & S3 Exploratory Dashboard",
    layout="wide"
)

st.title("AWS EC2 & S3 Exploratory Dashboard")

# -----------------------------
# Load data (with caching)
# -----------------------------
@st.cache_data
def load_data():
    ec2 = pd.read_csv("aws_resources_compute.csv")
    s3 = pd.read_csv("aws_resources_S3.csv")
    return ec2, s3

ec2_df, s3_df = load_data()

# Basic cleaning
ec2_df = ec2_df.dropna(subset=["CostUSD", "CPUUtilization"])
s3_df = s3_df.fillna({"CostUSD": 0})

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.title("Filters")

# EC2 region filter
ec2_regions = sorted(ec2_df["Region"].dropna().unique())
selected_ec2_regions = st.sidebar.multiselect(
    "EC2 Regions",
    options=ec2_regions,
    default=ec2_regions
)

# S3 region filter
s3_regions = sorted(s3_df["Region"].dropna().unique())
selected_s3_regions = st.sidebar.multiselect(
    "S3 Regions",
    options=s3_regions,
    default=s3_regions
)

# EC2 cost filter
ec2_min_cost = float(ec2_df["CostUSD"].min())
ec2_max_cost = float(ec2_df["CostUSD"].max())
ec2_cost_range = st.sidebar.slider(
    "EC2 Cost (USD/hr)",
    min_value=ec2_min_cost,
    max_value=ec2_max_cost,
    value=(ec2_min_cost, ec2_max_cost)
)

# EC2 CPU filter
ec2_min_cpu = float(ec2_df["CPUUtilization"].min())
ec2_max_cpu = float(ec2_df["CPUUtilization"].max())
ec2_cpu_range = st.sidebar.slider(
    "EC2 CPU Utilization (%)",
    min_value=ec2_min_cpu,
    max_value=ec2_max_cpu,
    value=(ec2_min_cpu, ec2_max_cpu)
)

# Raw data checkbox
show_raw_data = st.sidebar.checkbox("Show raw tables", value=False)

# -----------------------------
# Apply filters
# -----------------------------
ec2_filtered = ec2_df[
    (ec2_df["Region"].isin(selected_ec2_regions)) &
    (ec2_df["CostUSD"].between(ec2_cost_range[0], ec2_cost_range[1])) &
    (ec2_df["CPUUtilization"].between(ec2_cpu_range[0], ec2_cpu_range[1]))
]

s3_filtered = s3_df[s3_df["Region"].isin(selected_s3_regions)]

# -----------------------------
# High-level KPIs
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("EC2 Instances", len(ec2_filtered))
col2.metric(
    "Avg EC2 Cost (USD/hr)",
    f"{ec2_filtered['CostUSD'].mean():.2f}" if not ec2_filtered.empty else "0.00"
)
col3.metric("S3 Buckets", len(s3_filtered))
col4.metric(
    "Total S3 Storage (GB)",
    f"{s3_filtered['TotalSizeGB'].sum():,.0f}" if not s3_filtered.empty else "0"
)

# -----------------------------
# Tabs for dashboard sections
# -----------------------------
tab_overview, tab_ec2, tab_s3, tab_top, tab_opt, tab_data = st.tabs(
    [
        "Overview / Compute Visualizations",
        "EC2 Analysis",
        "S3 Analysis",
        "Top Resources",
        "Optimization Strategies",
        "Raw Data",
    ]
)

# =============================
# Overview / Compute Tab
# =============================
with tab_overview:
    st.subheader("Compute Visualizations")

    col_left, col_right = st.columns(2)

    # Left: Average EC2 Cost per Region (Filtered)
    with col_left:
        st.markdown("**Average EC2 Cost per Region (Filtered)**")
        avg_cost_region = (
            ec2_filtered
            .groupby("Region")["CostUSD"]
            .mean()
            .sort_values(ascending=False)
        )

        if not avg_cost_region.empty:
            fig, ax = plt.subplots()
            avg_cost_region.plot(kind="bar", ax=ax)
            ax.set_xlabel("AWS Region")
            ax.set_ylabel("Avg Cost (USD/hr)")
            ax.set_title("Average EC2 Cost per Region")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig)
        else:
            st.info("No EC2 data available for the selected filters.")

    # Right: S3 Total Storage by Region (Filtered)
    with col_right:
        st.markdown("**S3 Total Storage by Region (Filtered)**")
        storage_by_region = (
            s3_filtered
            .groupby("Region")["TotalSizeGB"]
            .sum()
            .sort_values(ascending=False)
        )

        if not storage_by_region.empty:
            fig, ax = plt.subplots()
            storage_by_region.plot(kind="bar", ax=ax)
            ax.set_xlabel("Region")
            ax.set_ylabel("Total Size (GB)")
            ax.set_title("S3 Total Storage by Region")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig)
        else:
            st.info("No S3 data available for the selected filters.")

# =============================
# EC2 Analysis Tab
# =============================
with tab_ec2:
    st.subheader("EC2 Analysis")

    col1, col2 = st.columns(2)

    # Histogram of CPU utilization
    with col1:
        st.markdown("**CPU Utilization Distribution**")
        if not ec2_filtered.empty:
            fig, ax = plt.subplots()
            ax.hist(ec2_filtered["CPUUtilization"], bins=20)
            ax.set_xlabel("CPU Utilization (%)")
            ax.set_ylabel("Frequency")
            ax.set_title("EC2 CPU Utilization Distribution")
            st.pyplot(fig)
        else:
            st.info("No EC2 data available for the selected filters.")

    # Scatter: CPU vs Cost
    with col2:
        st.markdown("**CPU vs Cost**")
        if not ec2_filtered.empty:
            fig, ax = plt.subplots()
            ax.scatter(ec2_filtered["CPUUtilization"], ec2_filtered["CostUSD"])
            ax.set_xlabel("CPU Utilization (%)")
            ax.set_ylabel("Cost (USD/hr)")
            ax.set_title("EC2 CPU vs Cost")
            ax.grid(True, linestyle="--", alpha=0.6)
            st.pyplot(fig)
        else:
            st.info("No EC2 data available for the selected filters.")

# =============================
# S3 Analysis Tab
# =============================
with tab_s3:
    st.subheader("S3 Analysis")

    col1, col2 = st.columns(2)

    # S3: Cost vs Storage scatter
    with col1:
        st.markdown("**S3 Cost vs Storage Size**")
        if not s3_filtered.empty:
            fig, ax = plt.subplots()
            ax.scatter(s3_filtered["TotalSizeGB"], s3_filtered["CostUSD"])
            ax.set_xlabel("Total Size (GB)")
            ax.set_ylabel("Cost (USD)")
            ax.set_title("S3 Cost vs Storage Size")
            ax.grid(True, linestyle="--", alpha=0.6)
            st.pyplot(fig)
        else:
            st.info("No S3 data available for the selected filters.")

    # S3: Total storage by region
    with col2:
        st.markdown("**Total S3 Storage per Region (Filtered)**")
        total_storage_region = (
            s3_filtered
            .groupby("Region")["TotalSizeGB"]
            .sum()
            .sort_values(ascending=False)
        )
        if not total_storage_region.empty:
            fig, ax = plt.subplots()
            total_storage_region.plot(kind="bar", ax=ax)
            ax.set_xlabel("AWS Region")
            ax.set_ylabel("Total Storage (GB)")
            ax.set_title("Total S3 Storage per Region")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig)
        else:
            st.info("No S3 data available for the selected filters.")

# =============================
# Top Resources Tab
# =============================
with tab_top:
    st.subheader("Top Resources")

    col1, col2 = st.columns(2)

    # Top 5 EC2 by cost
    with col1:
        st.markdown("**Top 5 Most Expensive EC2 Instances (Filtered)**")
        if not ec2_filtered.empty:
            top_ec2 = (
                ec2_filtered
                .nlargest(5, "CostUSD")
                .sort_values("CostUSD", ascending=True)
            )

            fig, ax = plt.subplots()
            ax.barh(top_ec2["ResourceId"], top_ec2["CostUSD"])
            ax.set_xlabel("Cost (USD/hr)")
            ax.set_ylabel("ResourceId")
            ax.set_title("Top 5 EC2 Instances by Cost")
            st.pyplot(fig)

            st.dataframe(
                top_ec2[["ResourceId", "Region", "CostUSD"]],
                use_container_width=True
            )
        else:
            st.info("No EC2 data available for the selected filters.")

    # Top 5 S3 by size
    with col2:
        st.markdown("**Top 5 Largest S3 Buckets (Filtered)**")
        if not s3_filtered.empty:
            top_s3 = (
                s3_filtered
                .nlargest(5, "TotalSizeGB")
                .sort_values("TotalSizeGB", ascending=True)
            )

            fig, ax = plt.subplots()
            ax.barh(top_s3["BucketName"], top_s3["TotalSizeGB"])
            ax.set_xlabel("Total Size (GB)")
            ax.set_ylabel("Bucket Name")
            ax.set_title("Top 5 S3 Buckets by Size")
            st.pyplot(fig)

            st.dataframe(
                top_s3[["BucketName", "Region", "TotalSizeGB", "CostUSD"]],
                use_container_width=True
            )
        else:
            st.info("No S3 data available for the selected filters.")

# =============================
# Optimization Strategies Tab
# =============================
with tab_opt:
    st.header("Optimization Strategies")

    # --- Dynamic insights from filtered data ---

    # EC2: region with highest average cost
    if not ec2_filtered.empty:
        avg_cost_region_opt = (
            ec2_filtered
            .groupby("Region")["CostUSD"]
            .mean()
            .sort_values(ascending=False)
        )
        ec2_expensive_region = avg_cost_region_opt.idxmax()
        ec2_expensive_value = avg_cost_region_opt.max()
    else:
        ec2_expensive_region = None
        ec2_expensive_value = None

    # S3: region with highest total storage
    if not s3_filtered.empty:
        storage_by_region_opt = (
            s3_filtered
            .groupby("Region")["TotalSizeGB"]
            .sum()
            .sort_values(ascending=False)
        )
        s3_heaviest_region = storage_by_region_opt.idxmax()
        s3_heaviest_value = storage_by_region_opt.max()
    else:
        s3_heaviest_region = None
        s3_heaviest_value = None

    # --- Build strategy matrix ---
    strategies = []

    strategies.append({
        "Area": "EC2",
        "Pattern Observed": (
            f"Highest avg hourly cost in region {ec2_expensive_region} (~{ec2_expensive_value:.2f} USD/hr)"
            if ec2_expensive_region else "No EC2 data for current filters"
        ),
        "Optimization Action": "Rightsize instances or move flexible workloads to cheaper regions.",
        "Expected Impact": "Lower compute spend while keeping performance acceptable."
    })

    strategies.append({
        "Area": "EC2",
        "Pattern Observed": "Under-utilized instances with low CPU but non-trivial cost.",
        "Optimization Action": "Downsize instance types or schedule shutdown outside business hours.",
        "Expected Impact": "Avoid paying for idle capacity."
    })

    strategies.append({
        "Area": "S3",
        "Pattern Observed": (
            f"Largest total storage in region {s3_heaviest_region} (~{s3_heaviest_value:,.0f} GB)"
            if s3_heaviest_region else "No S3 data for current filters"
        ),
        "Optimization Action": "Use lifecycle rules to move cold data to STANDARD_IA/GLACIER and expire old objects.",
        "Expected Impact": "Reduce monthly storage cost, especially for archival data."
    })

    strategies.append({
        "Area": "S3",
        "Pattern Observed": "Potential growth from versioning and duplicate copies.",
        "Optimization Action": "Review versioning; clean up non-current versions and unnecessary replicas.",
        "Expected Impact": "Control long-term storage growth and cost."
    })

    strategies_df = pd.DataFrame(strategies)

    st.subheader("Optimization Strategy Matrix")
    st.dataframe(strategies_df, use_container_width=True)

    # ==========================================
    # Visualization for Optimization Strategies
    # ==========================================
    st.subheader("Optimization Visualizations")

    # Bar chart: Estimated Impact by Action
    impact_scores = {
        "Rightsizing EC2 / Region Move": 35,
        "EC2 Scheduling Idle Instances": 20,
        "S3 Lifecycle Tiering": 30,
        "S3 Versioning Cleanup": 15
    }
    impact_df = pd.DataFrame(
        list(impact_scores.items()),
        columns=["Optimization Action", "Estimated % Cost Reduction Potential"]
    )

    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.barh(
        impact_df["Optimization Action"],
        impact_df["Estimated % Cost Reduction Potential"]
    )
    ax1.set_xlabel("Estimated % Cost Reduction Potential")
    ax1.set_ylabel("Optimization Action")
    ax1.set_title("Estimated Cost Reduction by Optimization Action")
    ax1.grid(axis="x", linestyle="--", alpha=0.6)
    st.pyplot(fig1)

    # Pie chart: Focus distribution (EC2 vs S3)
    focus_data = {"EC2": 2, "S3": 2}
    fig2, ax2 = plt.subplots()
    ax2.pie(
        focus_data.values(),
        labels=focus_data.keys(),
        autopct="%1.0f%%",
        startangle=140,
    )
    ax2.set_title("Optimization Focus Areas (EC2 vs S3)")
    st.pyplot(fig2)

    st.markdown("""
**Interpretation:**
- **Rightsizing EC2** and **S3 Lifecycle Tiering** are the two highest-impact actions, each capable of yielding large percentage savings.
- EC2 and S3 both present significant optimization opportunities.
- Combining all strategies can provide substantial overall cost efficiency improvements for the analyzed workloads.
""")

# =============================
# Raw Data Tab
# =============================
with tab_data:
    st.subheader("Raw Data")

    if show_raw_data:
        st.markdown("### EC2 Data (Filtered)")
        st.dataframe(ec2_filtered, use_container_width=True)

        st.markdown("### S3 Data (Filtered)")
        st.dataframe(s3_filtered, use_container_width=True)
    else:
        st.info("Enable **'Show raw tables'** in the sidebar to view raw data.")