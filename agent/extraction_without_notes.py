import os
import pandas as pd
from datetime import datetime
import argparse
from utils.utils import get_question_biochar_multi_without_notes, get_question_biochar_multi_without_notes_threadpool

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

    # Iterate over all files in the directory
    for filename in os.listdir(args.dataset_name):
        if filename.endswith('.pdf'):
            all_data.append(filename.replace(".pdf", ""))

    # Create a DataFrame from the combined data
    question_list = []
    for doi in all_data:
            question_list.append({
                "doi": doi, "pdf": os.path.join(args.dataset_name, f"{doi}.pdf"), 
                "images": os.path.join(args.parsing_path, doi, "auto", "images"), 
                "markdown": os.path.join(args.parsing_path, doi, 'auto', f"{doi}.md")
            })
    return question_list

def run():
    data_list = get_data()
    data_list = [data for data in data_list if not os.path.exists(
        os.path.join(args.output_path, f"{data['doi']}.jsonl")
    )]
    print(f'job started, total {len(data_list)} tasks.')
    get_question_biochar_multi_without_notes_threadpool(
        data_list,
        args.model, 
        args.output_path,
        args.image_output_path,
        args.result1
    )
    

if __name__ == '__main__':
    run()
