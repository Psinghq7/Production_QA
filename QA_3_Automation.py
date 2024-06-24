import pandas as pd
import streamlit as st
import altair as alt
import os

# Predefined file paths
file_path_1 = 'Z:/Roster_QA_3_persons_raw_data.txt'
file_path_2 = 'C:/Users/psingh/Documents/Comscore Documents/Investigation/Automation/Roster_3.2_excluding_THP.xlsx'
file_path_3 = 'Z:/Roster_QA_1_raw_data.txt'

# Sidebar for file selection
st.sidebar.title("File Selection")
selected_file = st.sidebar.radio("Select the file to analyze:", ("QA_3.2", "QA_3.2_Excluding_THP", "Roster_QA_1"))

# Sidebar for file upload as a fallback
uploaded_file_1 = st.sidebar.file_uploader("Upload QA_3.2 File", type=["txt"])
uploaded_file_2 = st.sidebar.file_uploader("Upload QA_3.2 Excluding THP File", type=["xlsx"])
uploaded_file_3 = st.sidebar.file_uploader("Upload Roster_QA_1 File", type=["txt"])

def load_file(file_path, delimiter=None):
    try:
        if delimiter:
            df = pd.read_csv(file_path, delimiter=delimiter)
        else:
            df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None

# Load the selected file into a pandas DataFrame
df = None
if selected_file == "QA_3.2":
    if os.path.exists(file_path_1):
        df = load_file(file_path_1, delimiter='\t')
    elif uploaded_file_1:
        df = load_file(uploaded_file_1, delimiter='\t')
elif selected_file == "QA_3.2_Excluding_THP":
    if os.path.exists(file_path_2):
        df = load_file(file_path_2)
    elif uploaded_file_2:
        df = load_file(uploaded_file_2)
elif selected_file == "Roster_QA_1":
    if os.path.exists(file_path_3):
        df = load_file(file_path_3, delimiter='\t')
    elif uploaded_file_3:
        df = load_file(uploaded_file_3, delimiter='\t')

if df is not None:
    if selected_file == "QA_3.2" or selected_file == "QA_3.2_Excluding_THP":
        filtered_df = df[(df['MACHINE_STATUS'] == 'machine_still_present') & 
                         (df['PERSON_TYPE'] == 'Regular_SAT_persons')]
        pivot_table = filtered_df.pivot_table(index=['PERSON_STATUS', 'DEMO_CHANGE'], 
                                              columns='WEEK', values='CNT_PERSONS', 
                                              aggfunc='sum')
        pivot_table = pivot_table[sorted(pivot_table.columns, reverse=True)]
        
        # Get the last 10 weeks
        last_10_weeks = sorted(filtered_df['WEEK'].unique(), reverse=True)[:10]

        # Filter data for the last 10 weeks
        filtered_df_last_10_weeks = filtered_df[filtered_df['WEEK'].isin(last_10_weeks)]

        # Calculate persons added and lost for the last 10 weeks
        persons_added = filtered_df_last_10_weeks[filtered_df_last_10_weeks['PERSON_STATUS'] == 'Person_added'].pivot_table(
            index='WEEK', 
            values='CNT_PERSONS', 
            aggfunc='sum'
        ).sort_index(ascending=False)

        persons_lost = filtered_df_last_10_weeks[filtered_df_last_10_weeks['PERSON_STATUS'] == 'Person_lost'].pivot_table(
            index='WEEK', 
            values='CNT_PERSONS', 
            aggfunc='sum'
        ).sort_index(ascending=False)

    elif selected_file == "Roster_QA_1":
        filtered_df = df[(df['COMPLETE_AGE_GEN_FLAG'] == 'Machines_w_complete_age_gen') & 
                         (df['MACHINE_GROUP'] == 'Added_in_last_90_days')]
        
        # Convert WEEK_ID to numerical for sorting
        filtered_df['WEEK_ID_NUM'] = filtered_df['WEEK_ID'].str.extract('(\d+)').astype(int)
        
        # Create the pivot table
        pivot_table = filtered_df.pivot_table(index='WEEK_ID_NUM', columns='V_COUNTRY', values='PER_MACHINES', aggfunc='sum')
        
        # Sort the pivot table index (weeks) from latest to earliest
        pivot_table = pivot_table.sort_index(ascending=False)
        
        # Sort the pivot table columns (countries) in descending alphabetical order
        pivot_table = pivot_table[sorted(pivot_table.columns, reverse=True)]
        
        # Convert index back to original WEEK_ID format
        pivot_table.index = pivot_table.index.astype(str) + 'w'
        # Multiply values by 100 and add % sign
        pivot_table = pivot_table.applymap(lambda x: f"{x*100:.2f}%")

    # Define functions to highlight the data (for QA_3.2 and QA_3.2_Excluding_THP)
    def highlight_added(data):
        colors = []
        for i in range(len(data)):
            if i < len(data) - 1 and data.iloc[i] < data.iloc[i + 1]:
                colors.append('background-color: blue')
            else:
                colors.append('')
        return colors

    def highlight_lost(data):
        colors = []
        for i in range(len(data)):
            if i < len(data) - 1 and data.iloc[i] > data.iloc[i + 1]:
                colors.append('background-color: blue')
            else:
                colors.append('')
        return colors

    # Apply highlighting if applicable
    if selected_file in ["QA_3.2", "QA_3.2_Excluding_THP"]:
        persons_added_highlighted = persons_added.style.apply(highlight_added, subset=['CNT_PERSONS'])
        persons_lost_highlighted = persons_lost.style.apply(highlight_lost, subset=['CNT_PERSONS'])

    # Display title
    if selected_file == "QA_3.2":
        st.markdown("<h1 style='text-align: center;'>QA_3.2</h1>", unsafe_allow_html=True)
    elif selected_file == "QA_3.2_Excluding_THP":
        st.markdown("<h1 style='text-align: center;'>QA_3.2_Excluding_THP</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center;'>Roster_QA_1</h1>", unsafe_allow_html=True)

    # Display company logo (ensure the image is available in the deployment)
    st.image(r"C:\Users\psingh\Desktop\Comscore_Logo_Color_Logo.jpg", width=100) 

    # Create line charts with labels using Altair
    def create_chart(data, title):
        chart = alt.Chart(data.reset_index()).mark_line(point=True).encode(
            x=alt.X('WEEK:O', title='Week'),
            y=alt.Y('CNT_PERSONS:Q', title='Number of Persons'),
            tooltip=['WEEK', 'CNT_PERSONS']
        ).properties(
            title=title
        )
        return chart

    # Display line charts for the last 10 weeks with labels (if applicable)
    if selected_file in ["QA_3.2", "QA_3.2_Excluding_THP"]:
        st.write("Number of Persons Added by Week (Last 10 Weeks)")
        added_chart = create_chart(persons_added, "''")
        st.altair_chart(added_chart, use_container_width=True)

        st.write("Number of Persons Lost by Week (Last 10 Weeks)")
        lost_chart = create_chart(persons_lost, "''")
        st.altair_chart(lost_chart, use_container_width=True)

        # Display persons added and lost data side by side
        col1, col2 = st.columns(2)

        with col1:
            st.write("Persons Added Data")
            st.dataframe(persons_added_highlighted)

        with col2:
            st.write("Persons Lost Data")
            st.dataframe(persons_lost_highlighted)

    # Display the pivot table
    st.write("Pivot Table:")
    st.dataframe(pivot_table)
else:
    st.error("Please upload the required file to proceed.")
