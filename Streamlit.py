import os
import pandas as pd
import streamlit as st
import base64  

DATA_FOLDER = "data_movies"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Load and concatenate all CSV files from the folder
@st.cache_data
def load_and_concatenate_data(folder_path):
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    all_data = []

    for file in all_files:
        file_path = os.path.join(folder_path, file)
        try:
            df = pd.read_csv(file_path)
            df['cinema'] = os.path.splitext(file)[0]  # Add cinema name from filename
            all_data.append(df)
        except Exception as e:
            st.warning(f"Could not read {file}: {e}")

    if not all_data:
        return pd.DataFrame()  # Return empty DataFrame if nothing is loaded

    combined_df = pd.concat(all_data, ignore_index=True)

    # Normalize genre column: remove spaces, uppercase, remove duplicates within each row
    combined_df['genre'] = combined_df['genre'].fillna("UNKNOWN").apply(
        lambda x: ', '.join(sorted(set(g.strip().upper() for g in str(x).split(','))))
    )

    # Add date_dt column to sort dates properly
    combined_df["date_dt"] = pd.to_datetime(combined_df["date"], format="%d/%m/%Y", errors='coerce')

    return combined_df

# Set background image using CSS
def set_background(image_file):
    with open(image_file, "rb") as f:
        base64_img = base64.b64encode(f.read()).decode()
    page_bg_img = f"""
    <style>
    [data-testid="stApp"] {{
        background-image: url("data:image/jpg;base64,{base64_img}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Load the data
st.title("🎬 Cinémas de Strasbourg")
st.markdown("Regroupez et explorez les horaires des films de plusieurs cinémas.")
set_background("data_movies/cinema_background.jpg") # Replace with your actual image path

folder_path = "data_movies"
df = load_and_concatenate_data(folder_path)

if df.empty:
    st.error("❌ Aucune donnée trouvée dans le dossier. Vérifiez que les fichiers CSV existent dans le dossier `data_movies/`.")
else:
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filtres")

        selected_cinema = st.multiselect(
            "Cinéma",
            sorted(df["cinema"].dropna().unique()),
            default=df["cinema"].unique()
        )

        selected_titre = st.multiselect(
            "Film",
            sorted(df["titre"].dropna().unique())
        )

        selected_genre = st.multiselect(
            "Genre contient...",
            sorted(set(g.strip().upper() for val in df['genre'].dropna() for g in val.split(',')))
        )

        # Sort jours by natural weekday order
        weekday_order = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        unique_jours = df["jour"].dropna().unique().tolist()
        sorted_jours = [j for j in weekday_order if j in unique_jours]

        selected_jour = st.multiselect(
            "Jour",
            options=sorted_jours
        )

        # Sort dates chronologically
        sorted_dates = df.dropna(subset=["date_dt"]).sort_values("date_dt")["date"].drop_duplicates()

        selected_date = st.multiselect(
            "Date",
            options=sorted_dates.tolist()
        )

    # Filtering logic
    filtered_df = df.copy()

    if selected_cinema:
        filtered_df = filtered_df[filtered_df["cinema"].isin(selected_cinema)]
    if selected_titre:
        filtered_df = filtered_df[filtered_df["titre"].isin(selected_titre)]
    if selected_genre:
        genre_pattern = '|'.join([f'\\b{g.strip()}\\b' for g in selected_genre])
        filtered_df = filtered_df[filtered_df["genre"].str.contains(genre_pattern, case=False, na=False, regex=True)]
    if selected_jour:
        filtered_df = filtered_df[filtered_df["jour"].isin(selected_jour)]
    if selected_date:
        filtered_df = filtered_df[filtered_df["date"].isin(selected_date)]

    # Sort and reset index
    filtered_df = filtered_df.sort_values(by=["date_dt", "horaire"]).reset_index(drop=True)

    # Drop date_dt column before display/export
    filtered_df = filtered_df.drop(columns=["date_dt"], errors='ignore')
    filtered_df.columns = [col.upper() for col in filtered_df.columns]

    # Show results
    st.subheader(f"🎞️ {filtered_df.shape[0]} séances trouvées")
    styled_df = filtered_df.style.set_table_styles([
        {'selector': 'thead tr th',
         'props': [('background-color', '#343a40'),
                   ('color', 'white'),
                   ('font-weight', 'bold')]}
    ]).set_properties(**{
        'background-color': '#fffde7',
        'color': '#000000',
        'border-color': '#dddddd'
    })

    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Télécharger les données filtrées",
        filtered_df.to_csv(index=False),
        file_name="films_filtrés.csv",
        mime="text/csv"
    )
