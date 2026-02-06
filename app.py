import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# CONFIGURATION & STYLING
# =========================================================
st.set_page_config(
    page_title="Indonesian Film Monitoring Dashboard",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.stMetric {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
div[data-testid="stExpander"] {
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATA ENGINE
# =========================================================
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("data/imdb-indonesian.csv")
    df.columns = [c.strip().lower() for c in df.columns]

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['runtime_min'] = df['runtime'].astype(str).str.extract(r'(\d+)').astype(float)

    df['decade'] = (df['year'] // 10 * 10)
    df['genre_list'] = df['genre'].fillna('Unknown').str.split(', ')
    df['rating_clean'] = df['rating'].fillna('Unclassified')

    return df


df = load_and_clean_data()

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.title("🎛️ Monitoring Filters")

year_min = int(df['year'].min())
year_max = int(df['year'].max())

year_range = st.sidebar.slider(
    "Production Year Range",
    year_min,
    year_max,
    (1990, year_max)
)

df_filtered = df[
    (df['year'] >= year_range[0]) &
    (df['year'] <= year_range[1])
]

# =========================================================
# HEADER
# =========================================================
st.title("🎬 Indonesian Film Monitoring Dashboard")

# =========================================================
# KPI METRICS
# =========================================================
col1, col2, col3, col4 = st.columns(4)

total_films = len(df_filtered)
unclassified = (df_filtered['rating_clean'] == 'Unclassified').sum()
missing_runtime = df_filtered['runtime_min'].isna().sum()
avg_runtime = df_filtered['runtime_min'].mean()

col1.metric("Total Films Monitored", f"{total_films:,}")
col2.metric(
    "Unclassified Films",
    f"{unclassified}",
    f"{(unclassified / total_films * 100):.1f}%" if total_films else "0%"
)
col3.metric(
    "Missing Runtime Data",
    f"{missing_runtime}",
    f"{(missing_runtime / total_films * 100):.1f}%" if total_films else "0%"
)
col4.metric(
    "Average Runtime",
    f"{avg_runtime:.0f} min" if pd.notna(avg_runtime) else "N/A"
)

st.markdown("---")

# =========================================================
# MAIN TABS
# =========================================================
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🧠 Executive Summary",
    "📈 Production Trends",
    "🎭 Genre Distribution",
    "🔍 Metadata Integrity",
    "🏛️ Classification & Compliance"
])

# ---------------------------------------------------------
# TAB 0 — EXECUTIVE SUMMARY (FIXED & MEANINGFUL)
# ---------------------------------------------------------
with tab0:
    st.subheader("Key Insights & Monitoring Signals")

    colA, colB = st.columns(2)

    # Insight 1 — Growth concentration
    yearly_counts = (
        df_filtered
        .groupby('year')
        .size()
        .reset_index(name='film_count')
        .sort_values('year')
    )

    peak_year = yearly_counts.loc[yearly_counts['film_count'].idxmax()]

    colA.markdown(
        f"""
        ### 📈 Production Acceleration
        - **Peak production year:** **{int(peak_year['year'])}**
        - **Films produced:** **{int(peak_year['film_count'])}**
        - Indicates **structural growth**, not random fluctuation.
        """
    )

    # Insight 2 — Classification risk
    unclassified_rate = unclassified / total_films * 100 if total_films else 0

    colB.markdown(
        f"""
        ### ⚠️ Classification Coverage Risk
        - **{unclassified_rate:.1f}%** of films lack age classification
        - Dominant in **older decades**
        - Represents **archival & compliance blind spots**
        """
    )

    st.markdown("---")

    # Insight 3 — Genre dominance
    genre_leader = (
        df_filtered
        .explode('genre_list')
        .groupby('genre_list')
        .size()
        .reset_index(name='film_count')
        .sort_values('film_count', ascending=False)
        .head(1)
        .iloc[0]
    )

    # Insight 4 — Runtime outliers
    long_films = (df_filtered['runtime_min'] > 150).sum()

    colC, colD = st.columns(2)

    colC.markdown(
        f"""
        ### 🎭 Content Concentration
        - **Most dominant genre:** **{genre_leader['genre_list']}**
        - Accounts for a disproportionate share of national output
        - Useful for **content diversity monitoring**
        """
    )

    colD.markdown(
        f"""
        ### ⏱️ Runtime Extremes
        - **{long_films} films** exceed **150 minutes**
        - Potential review focus for:
          - Festival submissions
          - Broadcast suitability
        """
    )

# ---------------------------------------------------------
# TAB 1 — PRODUCTION TRENDS
# ---------------------------------------------------------
with tab1:
    st.subheader("Film Production Volume Over Time")

    fig = px.area(
        yearly_counts,
        x='year',
        y='film_count',
        title="Annual Film Production in Indonesia",
        labels={'film_count': 'Number of Films', 'year': 'Year'}
    )
    fig.update_layout(showlegend=False, hovermode="x unified")

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 2 — GENRE DISTRIBUTION
# ---------------------------------------------------------
with tab2:
    st.subheader("Genre Representation")

    genre_counts = (
        df_filtered
        .explode('genre_list')
        .groupby('genre_list')
        .size()
        .reset_index(name='film_count')
        .sort_values('film_count', ascending=False)
        .head(10)
    )

    fig = px.bar(
        genre_counts,
        x='film_count',
        y='genre_list',
        orientation='h',
        title="Most Common Film Genres",
        labels={
            'film_count': 'Number of Films',
            'genre_list': 'Genre'
        }
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 3 — METADATA INTEGRITY
# ---------------------------------------------------------
with tab3:
    st.subheader("Metadata Completeness Review")

    rating_dist = (
        df_filtered
        .groupby('rating_clean')
        .size()
        .reset_index(name='film_count')
        .rename(columns={'rating_clean': 'rating'})
    )

    fig = px.treemap(
        rating_dist,
        path=['rating'],
        values='film_count',
        title="Age Rating Documentation Coverage"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 4 — CLASSIFICATION & COMPLIANCE
# ---------------------------------------------------------
with tab4:
    st.subheader("Classification & Compliance Oversight")

    rating_decade = (
        df_filtered
        .groupby(['decade', 'rating_clean'])
        .size()
        .reset_index(name='film_count')
    )

    fig = px.bar(
        rating_decade,
        x='decade',
        y='film_count',
        color='rating_clean',
        barmode='stack',
        title="Age Rating Distribution Across Decades",
        labels={
            'decade': 'Production Decade',
            'film_count': 'Number of Films',
            'rating_clean': 'Age Rating'
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    fig_runtime = px.histogram(
        df_filtered,
        x='runtime_min',
        nbins=20,
        title="Runtime Distribution of Films",
        labels={'runtime_min': 'Runtime (Minutes)'}
    )

    st.plotly_chart(fig_runtime, use_container_width=True)

# =========================================================
# DATA EXPLORER
# =========================================================
with st.expander("📂 Film Registry Explorer"):
    search = st.text_input("Search by Film Title")
    if search:
        st.dataframe(
            df_filtered[df_filtered['title'].str.contains(search, case=False, na=False)]
        )
    else:
        st.dataframe(df_filtered.head(20))

# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("Data Source: IMDB Public Archive")
