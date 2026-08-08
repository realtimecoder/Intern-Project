import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Logistics Route Efficiency Tracker",
    page_icon="🚚",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("delivery_data.csv", parse_dates=["Order_Date"])
    return df

df = load_data()

st.title("🚚 Logistics & Delivery Route Efficiency Tracker")
st.caption("Data Analytics Dashboard | Delivery Operations Performance")

# Sidebar filters
st.sidebar.header("Filters")

cities = st.sidebar.multiselect(
    "City", sorted(df["City"].unique()), default=sorted(df["City"].unique())
)
vehicles = st.sidebar.multiselect(
    "Vehicle Type", sorted(df["Vehicle_Type"].unique()),
    default=sorted(df["Vehicle_Type"].unique())
)
traffic = st.sidebar.multiselect(
    "Traffic Level", sorted(df["Traffic_Level"].unique()),
    default=sorted(df["Traffic_Level"].unique())
)

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()
date_range = st.sidebar.date_input("Order Date", (min_date, max_date))

filtered = df[
    df["City"].isin(cities)
    & df["Vehicle_Type"].isin(vehicles)
    & df["Traffic_Level"].isin(traffic)
]

if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[
        (filtered["Order_Date"].dt.date >= date_range[0])
        & (filtered["Order_Date"].dt.date <= date_range[1])
    ]

# KPIs
total_orders = int(filtered["Orders"].sum())
delivered = int(filtered["Delivered"].sum())
on_time = int(filtered["On_Time"].sum())
completion_rate = delivered / total_orders * 100 if total_orders else 0
on_time_rate = on_time / delivered * 100 if delivered else 0
avg_delay = filtered["Delay_min"].mean() if len(filtered) else 0
total_distance = filtered["Distance_km"].sum()
fuel_cost = filtered["Fuel_Cost_INR"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Orders", f"{total_orders:,}")
c2.metric("Delivered", f"{delivered:,}")
c3.metric("Completion Rate", f"{completion_rate:.1f}%")
c4.metric("On-Time Rate", f"{on_time_rate:.1f}%")
c5.metric("Avg Delay", f"{avg_delay:.1f} min")
c6.metric("Fuel Cost", f"₹{fuel_cost:,.0f}")

st.divider()

# Daily trend
daily = filtered.groupby("Order_Date", as_index=False).agg(
    Orders=("Orders", "sum"),
    Delivered=("Delivered", "sum"),
    On_Time=("On_Time", "sum"),
    Delay=("Delay_min", "mean")
)

fig = px.line(
    daily, x="Order_Date", y=["Orders", "Delivered"],
    markers=True, title="Daily Order & Delivery Trend"
)
st.plotly_chart(fig, use_container_width=True)

# Route analysis
route = filtered.groupby("Route_ID", as_index=False).agg(
    Distance_km=("Distance_km", "mean"),
    Avg_Delay_min=("Delay_min", "mean"),
    Fuel_Cost_INR=("Fuel_Cost_INR", "sum"),
    On_Time_Rate=("On_Time_Rate", "mean"),
    Efficiency_km_per_hr=("Route_Efficiency", "mean")
).sort_values("Avg_Delay_min", ascending=False)

left, right = st.columns(2)

with left:
    fig_route = px.bar(
        route.head(10),
        x="Avg_Delay_min", y="Route_ID",
        orientation="h",
        title="Top 10 Routes by Average Delay"
    )
    st.plotly_chart(fig_route, use_container_width=True)

with right:
    fig_eff = px.bar(
        route.sort_values("Efficiency_km_per_hr", ascending=False).head(10),
        x="Efficiency_km_per_hr", y="Route_ID",
        orientation="h",
        title="Top 10 Most Efficient Routes"
    )
    st.plotly_chart(fig_eff, use_container_width=True)

# Driver & vehicle analysis
driver = filtered.groupby("Driver_ID", as_index=False).agg(
    Deliveries=("Delivered", "sum"),
    On_Time_Rate=("On_Time_Rate", "mean"),
    Avg_Delay=("Delay_min", "mean")
).sort_values("On_Time_Rate", ascending=False)

vehicle = filtered.groupby("Vehicle_Type", as_index=False).agg(
    Distance_km=("Distance_km", "sum"),
    Fuel_Cost_INR=("Fuel_Cost_INR", "sum"),
    Avg_Delay=("Delay_min", "mean"),
    On_Time_Rate=("On_Time_Rate", "mean")
)

left, right = st.columns(2)

with left:
    fig_driver = px.bar(
        driver.head(10), x="On_Time_Rate", y="Driver_ID",
        orientation="h", title="Top Drivers by On-Time Rate"
    )
    st.plotly_chart(fig_driver, use_container_width=True)

with right:
    fig_vehicle = px.bar(
        vehicle, x="Vehicle_Type", y="Fuel_Cost_INR",
        title="Fuel Cost by Vehicle Type"
    )
    st.plotly_chart(fig_vehicle, use_container_width=True)

# Traffic & weather impact
traffic_df = filtered.groupby("Traffic_Level", as_index=False).agg(
    Avg_Delay=("Delay_min", "mean"),
    On_Time_Rate=("On_Time_Rate", "mean")
)

weather_df = filtered.groupby("Weather", as_index=False).agg(
    Avg_Delay=("Delay_min", "mean"),
    On_Time_Rate=("On_Time_Rate", "mean")
)

left, right = st.columns(2)

with left:
    fig_t = px.bar(
        traffic_df, x="Traffic_Level", y="Avg_Delay",
        title="Traffic Impact on Delay"
    )
    st.plotly_chart(fig_t, use_container_width=True)

with right:
    fig_w = px.bar(
        weather_df, x="Weather", y="Avg_Delay",
        title="Weather Impact on Delay"
    )
    st.plotly_chart(fig_w, use_container_width=True)

# Scatter relationship
fig_scatter = px.scatter(
    filtered,
    x="Distance_km",
    y="Actual_Time_min",
    size="Orders",
    color="Traffic_Level",
    hover_data=["Route_ID", "City", "Vehicle_Type"],
    title="Distance vs Actual Delivery Time"
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Recommendations
st.subheader("💡 Automated Business Insights")

worst_route = route.iloc[0] if not route.empty else None
best_route = route.sort_values("Efficiency_km_per_hr", ascending=False).iloc[0] if not route.empty else None

if worst_route is not None:
    st.write(
        f"• **Delay hotspot:** {worst_route['Route_ID']} has the highest average delay "
        f"({worst_route['Avg_Delay_min']:.1f} minutes)."
    )

if best_route is not None:
    st.write(
        f"• **Efficient route:** {best_route['Route_ID']} has the highest route efficiency "
        f"({best_route['Efficiency_km_per_hr']:.1f} km/hour)."
    )

high_traffic_delay = traffic_df.loc[
    traffic_df["Avg_Delay"].idxmax(), "Traffic_Level"
] if not traffic_df.empty else "N/A"

st.write(
    f"• **Traffic insight:** {high_traffic_delay} traffic currently shows the highest "
    "average delay in the selected data."
)

st.subheader("📋 Route Performance Table")
st.dataframe(route.round(2), use_container_width=True)

st.download_button(
    "Download Filtered Data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_delivery_data.csv",
    mime="text/csv"
)
