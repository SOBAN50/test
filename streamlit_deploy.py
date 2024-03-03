import streamlit as st
import os
import io
import time
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from multiprocessing import Pool
from utils import *

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

# Define a dictionary to store user credentials
user_credentials = {
    'username': 'soban',
    'password': 'soban'
}

# Function to check login credentials
def authenticate(username, password):
    return username == user_credentials['username'] and password == user_credentials['password']

#------------------------------------------------------------------------------------

def load_excel(file_name):
    return pd.read_excel(file_name)

def download_excel(file_path, button_label='Download Excel File'):
    excel_output = io.BytesIO()
    with pd.ExcelWriter(excel_output, engine='openpyxl', mode='w') as writer:
        # Read all sheets from the Excel file
        with pd.ExcelFile(file_path) as xls:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    excel_data = excel_output.getvalue()
    st.download_button(label=button_label, data=excel_data, key='download_button', file_name='Output_File.xlsx')

# Function to execute code on uploaded files
def execute_code(file1, file2, output_directory, growing_keyword_input, diminishing_keyword_input):
    
    if file1 and file2 and growing_keyword_input and diminishing_keyword_input and output_directory:

        with st.spinner("Executing..."):

            start = time.time()

            print(f'File1: {file1}, File2: {file2}')
            data_2022, data_2023 = load_excel_files_threadpool(file_names = [file1, file2], cores = 2)

            print('\nAnalyzing Data:'); start2 = time.time()
            merged_data = data_2022.merge(data_2023, on = 'Keyword', how = 'inner')        
            merged_data['Change_in_rank_percentage'] = merged_data.apply( lambda x: rank_percentage_function(x) , axis=1 )
            keyword_change_dict = dict(zip(merged_data['Keyword'], merged_data['Change_in_rank_percentage']))

            set2022 = set(data_2022['Keyword'].to_list())
            set2023 = set(data_2023['Keyword'].to_list())
            new_niches_list = list(set2023 - set2022)
            print(f'New Niches: {len(new_niches_list)}')

            missing_niches_list = list(set2022 - set2023)
            print(f'Missing Keywords: {len(missing_niches_list)}')
            end2 = time.time(); print(f"Completed in {end2-start2} sec")

            growing_kw_df, diminishing_kw_df, new_niches_df, missing_niches_df = finalize_dataframes(
                                    merged_data, data_2022, data_2023, new_niches_list, missing_niches_list,
                                    growing_keyword_input = growing_keyword_input, diminishing_keyword_input = diminishing_keyword_input)
            
            used_kws = get_used_kws(merged_data)#, limit = 5_000)

            grouped_keywords_annoy = relevant_kws_algorithm(used_kws)

            growing_kw_df = add_relevant_kws_to_growing_df("Growing", growing_kw_df, keyword_change_dict, grouped_keywords_annoy)
            diminishing_kw_df = add_relevant_kws_to_growing_df("Diminishing", diminishing_kw_df, keyword_change_dict, grouped_keywords_annoy)

            final_output_directory = output_directory + '/Output_File_GUI.xlsx'

            success = write_excel_file_threadpool(growing_kw_df, diminishing_kw_df, new_niches_df, missing_niches_df,
                                                output_filename = final_output_directory, cores = 2)

            print('\nPreparing File for Download...'); start3 = time.time()
            download_excel(final_output_directory)
            end3 = time.time(); print(f"Completed in {end3-start3} sec")

            end = time.time()
            print(f"\nProgram completed in {end-start} sec\nOutput Excel File is ready for Download.")

            st.success(f"Code execution successful.")

    else:
        st.warning("Please provide all information before executing.")

#------------------------------------------------------------------------------------

def select_folder():
   root = tk.Tk()
   root.withdraw()
   folder_path = filedialog.askdirectory(master=root)
   root.destroy()
   return folder_path

# Streamlit app
def main():
    init_session_state()

    st.title("Simple Streamlit App")

    if not st.session_state.logged_in:
        st.header("Login")

        # Input fields for username and password
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Login button
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Credentials")

    else:
        st.header("Upload Files")

        growing_keyword_input = st.number_input("Growing Keyword Threshold", value = 100)
        diminishing_keyword_input = st.number_input("Diminishing Keyword Threshold", value = 100)

        file1 = st.file_uploader("Previous Year Data", type=["csv", "xlsx"])

        file2 = st.file_uploader("Current Year Data", type=["csv", "xlsx"])

        selected_folder_path = os.getcwd()
        if selected_folder_path:
           st.write("Selected root folder path on host machine")

        # Execute button
        execute_button = st.button("Execute")

        if execute_button:
            execute_code(file1, file2, selected_folder_path, growing_keyword_input, diminishing_keyword_input)

# Run the app
if __name__ == "__main__":
    main()
