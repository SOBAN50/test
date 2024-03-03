import streamlit as st
import os
import io
import time
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from multiprocessing import Pool
from utils import *
from collections import Counter

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
def execute_code(file1, output_directory):
    
    if file1 and output_directory:

        with st.spinner("Executing..."):

            start = time.time()

            print(f'File1: {file1}')
            title_data = load_excel_files_threadpool(file_names = [file1], cores = 2)

            print('\nExtracting keywords from Title (RAKE):'); start2 = time.time()
            title_data['Keywords'] = title_data['Title'].apply(lambda x: RAKE(x))
            end2 = time.time(); print(f"Completed in {end2-start2} sec")

            all_keywords = list([item for sublist in title_data['Keywords'] for item in sublist])
            
            value_counts = Counter(all_keywords)
            value_dict = dict(value_counts)
            used_kws = list(value_dict.keys())

            output_df = pd.DataFrame(list(value_dict.items()), columns=['Keyword', 'Frequency'])
            
            grouped_keywords_annoy = relevant_kws_algorithm(used_kws)#, Limit=500)

            output_df['Relevant_Kws'] = None
            output_df['Relevant_Kws'] = output_df.apply(
                lambda x: grouped_keywords_annoy[x['Keyword']] if x['Keyword'] in grouped_keywords_annoy else None, axis = 1)

            output_df['Relevant_Keyword1'] = output_df.apply(lambda x: x['Relevant_Kws'][0] if x['Relevant_Kws'] is not None else None, axis = 1)
            output_df['Relevant_Keyword2'] = output_df.apply(lambda x: x['Relevant_Kws'][1] if x['Relevant_Kws'] is not None else None, axis = 1)
            output_df['Relevant_Keyword3'] = output_df.apply(lambda x: x['Relevant_Kws'][2] if x['Relevant_Kws'] is not None else None, axis = 1)
            output_df['Relevant_Keyword4'] = output_df.apply(lambda x: x['Relevant_Kws'][3] if x['Relevant_Kws'] is not None else None, axis = 1)
            output_df.drop(columns=['Relevant_Kws'], inplace=True)


            final_output_directory = output_directory + '/Output_File_GUI.xlsx'
            success = write_excel_file_threadpool(output_df, output_filename = final_output_directory, cores = 2)

            print('\nPreparing File for Download...'); start3 = time.time()
            download_excel(final_output_directory)
            end3 = time.time(); print(f"Completed in {end3-start3} sec")

            end = time.time()
            print(f"\nProgram completed in {end-start} sec")

            st.success(f"Code execution successful. Result saved to: {final_output_directory}")

    else:
        st.warning("Please provide all information before executing.")



#------------------------------------------------------------------------------------

def main():
    init_session_state()

    st.title("KEEPA")

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

        file1 = st.file_uploader("Input File", type=["csv", "xlsx"])

        selected_folder_path = os.getcwd()
        if selected_folder_path:
           st.write("Selected root folder path on host machine")

        # Execute button
        execute_button = st.button("Execute")

        if execute_button:
            execute_code(file1, selected_folder_path)


# Run the app
if __name__ == "__main__":
    main()
