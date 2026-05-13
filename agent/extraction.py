import os
import pandas as pd
from datetime import datetime
import argparse
from utils.utils import get_question_biochar_multi_200, get_question_biochar_multi_200_threadpool

parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--model', type=str, help='gpt-4o-2024-11-20')
parser.add_argument("--output_path", type=str, help='')
parser.add_argument("--dataset_name", type=str, help='jsonl')
parser.add_argument("--parsing_path", type=str, help='jsonl')
parser.add_argument("--image_output_path", type=str, help='jsonl')
parser.add_argument("--result1", type=str, help='jsonl')
args = parser.parse_args()

current_time = datetime.now()
curr_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")

# executor = ProcessPoolExecutor(max_workers = 256)


def get_data():
    # List to hold the data from all JSONL files
    all_data = []
    df = pd.read_excel(PATH) # change to your own path
    # Iterate over all files in the directory
    for _, line in df.iterrows():
        all_data.append(line['doi'].replace("/", "_"))
        
    # Create a DataFrame from the combined data
    df_2000 = all_data[:230]
    question_list = []
    doi_list = [
        '10.1016_j.cemconcomp.2024.105867',
        '10.1016_j.conbuildmat.2019.117338',
        '10.1016_j.conbuildmat.2020.120688',
        '10.1016_j.conbuildmat.2020.120723',
        '10.1617_s11527-025-02573-5',
        # '10.1002_ep.13440',
        # '10.1007_s11043-025-09789-6',
    ]
    for doi in df_2000:
        if doi not in doi_list:
            question_list.append({
                "doi": doi, 
                "pdf": os.path.join(args.dataset_name, f"{doi}.pdf"), 
                "images": os.path.join(args.parsing_path, doi, "auto", "images"), 
                "markdown": os.path.join(args.parsing_path, doi, 'auto', f"{doi}.md")
            })
    return question_list

def run():
    data_list = get_data()
    data_list = [data for data in data_list if not os.path.exists(
        os.path.join(args.output_path, f"{data['doi']}.jsonl")
    )]
    os.makedirs(args.result1, exist_ok=True)
    os.makedirs(args.output_path, exist_ok=True)
    print(f'job started, total {len(data_list)} tasks.')
    get_question_biochar_multi_200_threadpool(
        data_list,
        args.model, 
        args.output_path,
        args.image_output_path,
        args.result1
    )
    

if __name__ == '__main__':
    run()
