import time
import pandas as pd
import numpy as np
from annoy import AnnoyIndex
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer


def load_file(file_name):
    return pd.read_excel(file_name)

def load_excel_files_threadpool(file_names, cores = 2): # slower(70 sec) but works on every architecture
    try:
        print('\nLoading Files...'); start1 = time.time()

        with ThreadPoolExecutor(max_workers = cores) as executor:
            data_frames = list(executor.map(load_file, file_names))

        read_data = data_frames[0]
        end1 = time.time(); print(f"Completed in {end1-start1} sec")
        return read_data
    except Exception as e:
        print(f"Error in worker process: {e}")
        return None
    
#---------------------------

def YAKE(product_title):
    import yake
    keyword_extractor = yake.KeywordExtractor()
    keywords = keyword_extractor.extract_keywords(product_title)
    keywords = [keyword for keyword, _ in keywords]
    return keywords

def RAKE(product_title):
    from rake_nltk import Rake
    r = Rake()
    r.extract_keywords_from_text(product_title)
    keywords = r.get_ranked_phrases()
    return keywords

#---------------------------

def relevant_kws_algorithm(used_kws):
    print('\nRelevant Keywords Finding Algorithm running...'); start = time.time()
    start = time.time()
    model = SentenceTransformer('stsb-roberta-large')
    result_embeddings = np.array(model.encode(used_kws))
    num_dimensions = len(result_embeddings[0])
    annoy_index = AnnoyIndex(num_dimensions, 'angular')

    for i, embedding in enumerate(result_embeddings):
        annoy_index.add_item(i, embedding)

    annoy_index.build(n_trees=100)

    def find_top4_similar_keywords_annoy(args):
        query_embedding, index, keywords, query_keyword = args
        similar_indices = index.get_nns_by_vector(query_embedding, 5)  # Get top 5 (including the query itself)
        top4_indices = [idx for idx in similar_indices if keywords[idx] != query_keyword][:4]
        top4_keywords = [keywords[idx] for idx in top4_indices]
        return query_keyword, top4_keywords

    grouped_keywords_annoy = {}

    with ThreadPoolExecutor() as executor:
        args_list = [(result_embeddings[i], annoy_index, used_kws, query_keyword) for i, query_keyword in enumerate(used_kws)]
        results = list(executor.map(find_top4_similar_keywords_annoy, args_list))

    for query_keyword, top4_similar_keywords in results:
        grouped_keywords_annoy[query_keyword] = top4_similar_keywords

    end = time.time(); print(f"Completed in {end - start} sec")
    return grouped_keywords_annoy

#---------------------------

def write_excel_file_threadpool(df_to_write, output_filename='output_file.xlsx', cores=2):
    print('\nWriting Output File...'); start4 = time.time()
    with pd.ExcelWriter(output_filename) as writer:
        def write_to_excel(df, sheet_name):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        with ThreadPoolExecutor(max_workers = cores) as executor:
            futures = [executor.submit(write_to_excel, df, sheet_name) for df, sheet_name in [(df_to_write, 'Result')]]
            for future in futures:
                future.result()
    end4 = time.time(); print(f"Completed in {end4-start4} sec")
    return True