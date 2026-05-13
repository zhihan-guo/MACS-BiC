import random
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import json
from pathlib import Path
from prompts.prompt1 import QuestionPromptPDF1, QuestionOutput1
from prompts.prompt2 import QuestionPrompt2, QuestionOutput2
question_prompt1 = QuestionPromptPDF1()
question_prompt2 = QuestionPrompt2()


from prompts.prompt1_without_notes import QuestionPromptPDF1WithoutNotes
from prompts.prompt2_without_notes import QuestionPrompt2WithoutNotes
question_prompt1_without_notes = QuestionPromptPDF1WithoutNotes()
question_prompt2_without_notes = QuestionPrompt2WithoutNotes()

from prompts.prompt1_without_format import QuestionPromptPDF1WithoutFormat
from prompts.prompt2_without_format import QuestionPrompt2WithoutFormat
question_prompt1_without_format = QuestionPromptPDF1WithoutFormat()
question_prompt2_without_format = QuestionPrompt2WithoutFormat()


from prompts.prompt1_200 import QuestionPromptPDF1200
from prompts.prompt2_200_20250918 import QuestionPrompt2200
question_prompt1200 = QuestionPromptPDF1200()
question_prompt2200 = QuestionPrompt2200()

from prompts.prompt2_without_image_translator import QuestionPromptMultiPDF2_without_image_translator, QuestionOutputMultiPDF2
question_prompt2_without_image_translator = QuestionPromptMultiPDF2_without_image_translator()

import base64
from pathlib import Path
import pandas as pd
import time

import re

import openai
from openai import OpenAI
import httpx
import concurrent.futures


import os


chart_to_table_prompt = '''Convert given chart or table to a markdown format table.
If given image is not a table or chart, use a short phrase to describe it.
For each chart: 1. Extract only the main value (ignore error sticks/text annotations like '% change')
2. Identify axis units: Convert units when mismatched (e.g., from m to mm: multiply by 1,000); Keep original values if units match requirements
3. Validate against context: Cross-check extracted values with textual results in the paper.
Your output format should be markdown text. Provide the answer as float numbers, rounded to two decimal places.
Your answers should show difference between values.
Then generate a one-sentence table captain.
'''

def get_question_name(num, sub_num):
    qa = {
        'query_1':{
            '1.1': '1.1. What category of mixtures design or formulation design is used to produce biochar-integrated construction materials?',
            '1.2': '1.2.What is the particle size range of the biochar before it is applied or mixed into any mixtures?',
            '1.3': '1.3.What is the moisture content of the biochar before it is applied or mixed into any mixtures?',
            "2.1": "2.1.Is modulus property of biochar-integrated construction materials included in the given document?",
            "2.2": "2.2.Is durability of biochar-integrated construction materials included in the given document?",
            "2.3": "2.3.Is fire resistance performance of biochar-integrated construction materials included in the given document?",
            "2.4": "2.4.Is carbon footprint of biochar-integrated construction materials analyzed in the given document?"
        },
        'query_2':{
            "1.1": "3.1.What is the density of the biochar-integrated construction materials in the hardened state?",
            "1.2": "3.2.What is the compressive strength of the biochar-integrated construction materials after 28 days of curing?",
            "1.3": "3.3.What is the flow table or slump test value of the biochar-integrated construction materials in the fresh state?",
            "1.4": "3.4.What is the thermal conductivity of the biochar-integrated construction materials after 28 days of curing?",
            "1.5": "3.5.What is the life cycle analysis carbon footprint of biochar-integrated construction materials",
            "1.6": "3.6.What is the mass ratio of biochar to total mixtures in biochar-integrated construction materials?",
            "1.7": "3.7.What is the type of biochar-integrated construction material?",
            "1.8": "3.8.What is the classifications of the feedstock or biomass used to produce biochar?",
            "1.9": "3.9.What type of feedstock or biomass is used to produce biochar?",
            "1.10": "3.10.What temperature is used in the pyrolysis process from feedstock or biomass to biochar?",
            '1.11': '3.11.What is the role or function of biochar in the biochar-integrated construction material?',
            '1.12': '3.12.What is the mass ratio of biochar to cementitious materials in biochar-integrated construction material?',
            '1.13': '3.13.What is the mass ratio of biochar to aggregate in biochar-integrated construction material?',
            '1.14': '3.14.What is the mass or volume ratio of biochar aggregate to total aggregate in biochar-integrated construction material?',
        },
    }
    return qa[num][sub_num]



def get_question_name_200(num, sub_num):
    qa = {
        'query_1':{
            '1.1': '1.1. What category of mixtures design or formulation design is used to produce biochar-integrated construction materials?',
        },
        'query_2':{
            "1.1": "2.1. What is the mass ratio of cement in biochar-integrated construction materials?",
            "1.2": "2.2. What is the mass ratio of slag in biochar-integrated construction materials?",
            "1.3": "2.3. What is the mass ratio of fly ash in biochar-integrated construction materials?",
            "1.4": "2.4. What is the mass ratio of silica fume in biochar-integrated construction materials?",
            "1.5": "2.5. What is the mass ratio of biochar in biochar-integrated construction materials?",
            "1.6": "2.6. What is the mass ratio of fiber in biochar-integrated construction materials?",
            "1.7": "2.7. What is the mass ratio of water in biochar-integrated construction materials?",
            "1.8": "2.8. What is the mass ratio of sand/fine aggregate in biochar-integrated construction materials?",
            "1.9": "2.9. What is the mass ratio of gravel/coarse aggregate in biochar-integrated construction materials?",
            "1.10": "2.10. What is the mass ratio of biochar developed aggregate in biochar-integrated construction materials?",
            '1.11': "2.11. What is the mass ratio of admixtures in biochar-integrated construction materials?",
            '1.12': "2.12. What is the mass ratio of other materials in biochar-integrated construction materials?",
            '1.13': "2.13. What is the mass ratio of binder in biochar-integrated construction materials?",
            '1.14': "2.14. What is the mass ratio of water to binder in biochar-integrated construction materials?",
            '1.15': "2.15. What is the mass ratio of supplementary cementitious materials to binder in biochar-integrated construction materials?",
            '1.16': "2.16. What is the mass ratio of aggregate to binder in biochar-integrated construction materials?",
            '1.17': "2.17. What is the mass ratio of biochar to binder in biochar-integrated construction materials?",
            '2.1': "2.18. What grade of cement is used in this category?",
            '2.2': "2.19. What is the particle size range of biochar?",
            '2.3': "2.20. What is the porosity of biochar?",
            '2.4': "2.21. What is the fixed carbon content of biochar?",
            '2.5': "2.22. What is the carbon (C) content of the biochar?",
            '3.1': "2.23. What is the compressive strength of the biochar-integrated construction material?",
            '3.2': "2.24. What is the density of the biochar-integrated construction material?",
            '3.3': "2.25. What is the workability or flowability of the biochar-integrated construction material?",
            '3.4': "2.26. What is the thermal conductivity of the biochar-integrated construction material?",
        },
    }
    return qa[num][sub_num]


def interact_with_api_mp_biochar_1(all_text, model, prompt, response_format, table_and_charts):
    msg = prompt.get_prompted_input((all_text, table_and_charts))
    parsed_data = get_response_from_parsed_text(msg, model, response_format)
    if (isinstance(parsed_data, dict)):
        parsed_data['1.1'] = parsed_data['1.1'].split(',')
        for tem in parsed_data['1.1']:
            if tem == 'nan':
                parsed_data['1.1'].remove(tem)
        if len(parsed_data['1.1']) == 0:
            parsed_data['1.1'].append("")
        
    return parsed_data

def interact_with_api_mp_biochar_2(model, prompt, category,  table_and_charts, all_text: str):
    msg = prompt.get_prompted_input((category, table_and_charts, all_text))
    # 转换为 JSON 格式
    parsed_data = get_response_from_parsed_text(msg, model)
    return parsed_data


def interact_with_api_mp_biochar_2_without_image_translator(model, prompt, pdf_id, category):
    msg = prompt.get_prompted_input(category)
    parsed_data = get_response_from_pdf(pdf_id, msg, model)
    mapping_question_1_7 = {
        'a': 'Concrete',
        'b': 'Mortar or Paste',
        'c': 'Brick',
        'd': 'Insulation Board',
        'e': 'Gypsum Composites',
        'f': 'Asphalt Composites',
        'g': '3D Printing Materials',
        'h': 'Coating',
        'i': 'Other'
    }

    parsed_data['1.7'] = mapping_question_1_7.get(parsed_data['1.7'], parsed_data['1.7'])
        
    mapping_question_1_8 = {
        'a': 'Agricultural Residues',
        'b': 'Forestry and Wood Waste',
        'c': 'Animal Manure and Byproducts',
        'd': 'Municipal and Urban Organic Waste',
        'e': 'Industrial and Processing Byproducts',
        'f': 'Energy Crops',
        'g': 'Aquatic and Marine Biomass',
        'h': 'Other Organic Wastes'
    }

    parsed_data['1.8'] = mapping_question_1_8.get(parsed_data['1.8'], parsed_data['1.8'])
    
    mapping_question_1_11 = {
        'a': 'Cementitious Materials',
        'b': 'Admixture or Additive',
        'c': 'Aggregate',
        'd': 'Developing Aggregate'
    }

    parsed_data['1.11'] = mapping_question_1_11.get(parsed_data['1.11'], parsed_data['1.11'])

    return parsed_data

def get_response_from_parsed_text(msg, model):
    client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
    msg = [{'role':'user', 'content': msg}]
    start_time = time.time()
    for i in range(5):
        try:
            response = client.responses.create(
                model=model,
                input=msg,
                reasoning={"effort": "medium"}
            )
        except Exception as e:
            time.sleep(random.randint(5, 10))
            print(msg)
            print(f" Occurred: {e}. Retrying...")
        except openai.error.APIerror:
            time.sleep(random.randint(5, 10))
            print(f"APIError")
        else:
            success = True
            # print(f"success")
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f'get response from parsed text elapsed time: {elapsed_time:.6f} secs')
            break
    try:
        parsed_data = parse_responses(response.output_text)
    except:
        parsed_data = response.output_text
    return parsed_data

def get_response_from_pdf(pdf_id, msg, model):
    client = OpenAI(http_client=httpx.Client(verify = False))
    msg = [
        {
            'role':'user', 
            'content': [
                {
                    "type": "input_file",
                    "file_id": pdf_id
                },
                {
                    "type": "input_text",
                    "text": msg
                }
            ]
        }
    ]
    start_time = time.time()
    for i in range(5):
        try:
            response = client.responses.create(
                model=model,
                input=msg,
                reasoning={"effort": "medium"}
            )
        except Exception as e:
            time.sleep(random.randint(5, 10))
            print(msg)
            print(f" Occurred: {e}. Retrying...")
        except openai.error.APIerror:
            time.sleep(random.randint(5, 10))
            print(f"APIError了。")
        else:
            success = True
            # print(f"success")
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f'get response from pdf elapsed time: {elapsed_time:.6f} secs')
            break

    try:
        parsed_data = parse_responses(response.output_text)
    except:
        parsed_data = response.output_text
    # json_data = json.dumps(parsed_data, ensure_ascii=False, indent=4)
    return parsed_data

def parse_responses(responses):
    responses = responses.replace("**", "")
    data = {}
    lines = responses.strip().split('\n')
    
    for line in lines:
        match = re.match(r'(\d+\.\d+):\s*(.+)', line)
        if match:
            question, answer = match.groups()
            data[question] = answer.strip()
    
    return data

def get_final_output(model, QuestionPrompt2, results_1, output_path: str, data, category, table_and_charts: str, all_text):
    results_2 = interact_with_api_mp_biochar_2(model, QuestionPrompt2, category, table_and_charts, all_text)
    results_1_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_1.items():
            results_1_rename[get_question_name("query_1", key)] = value
            if value == 'nan':
                results_1_rename[get_question_name("query_1", key)] = ''

    results_1_rename['1.1. What category of mixtures design or formulation design is used to produce biochar-integrated construction materials?'] = category
    
    results_2_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_2.items():
            results_2_rename[get_question_name("query_2", key)] = value
            if value == 'nan':
                results_2_rename[get_question_name("query_2", key)] = ''

    if (isinstance(results_1, dict)) and (isinstance(results_2, dict)):
        merged_result = {k: v for d in (results_1_rename, results_2_rename) for k, v in d.items()}
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            'table_and_charts': table_and_charts,
            "text": all_text,
            "qa": merged_result,
            'model': model,
            "success": True
        }
    else:
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            'table_and_charts': table_and_charts,
            "text": all_text,
            "qa":{
                "results_1": results_1,
                "results_2": results_2,
            },
            'model': model,
            "success": False
        }
    with open(f'{output_path}/{data["doi"]}.jsonl', "a+") as wf:
        wf.write(json.dumps(responses) + '\n')


def get_final_output_200(model, QuestionPrompt2, results_1, output_path: str, data, category, table_and_charts: str, all_text):
    results_2 = interact_with_api_mp_biochar_2(model, QuestionPrompt2, category, table_and_charts, all_text)
    results_1_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_1.items():
            results_1_rename[get_question_name_200("query_1", key)] = value
            if value == 'nan':
                results_1_rename[get_question_name_200("query_1", key)] = ''

    results_1_rename['1.1. What category of mixtures design or formulation design is used to produce biochar-integrated construction materials?'] = category
    
    results_2_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_2.items():
            results_2_rename[get_question_name_200("query_2", key)] = value
            if value == 'nan':
                results_2_rename[get_question_name_200("query_2", key)] = ''

    if (isinstance(results_1, dict)) and (isinstance(results_2, dict)):
        merged_result = {k: v for d in (results_1_rename, results_2_rename) for k, v in d.items()}
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            'table_and_charts': table_and_charts,
            "text": all_text,
            "qa": merged_result,
            'model': model,
            "success": True
        }
    else:
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            'table_and_charts': table_and_charts,
            "text": all_text,
            "qa":{
                "results_1": results_1,
                "results_2": results_2,
            },
            'model': model,
            "success": False
        }
    with open(f'{output_path}/{data["doi"]}.jsonl', "a+") as wf:
        wf.write(json.dumps(responses) + '\n')


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
def get_question_biochar_multi(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    for data in data_list:
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    start_time = time.time()
                    results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, QuestionPromptPDF1)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'prompt 1 elapsed time: {elapsed_time:.6f} secs')
                    with open(result1_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
         

    
def interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, prompt, doi):
    msg = prompt.get_prompted_input()
    parsed_data = get_response_from_pdf(pdf_id, msg, model)
    if (isinstance(parsed_data, dict)):
        if len(parsed_data) == 0:
            with open(r"D:\projects\Biochar_for_Construction\output\error_doi.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({"error_doi": doi}, ensure_ascii=False) + "\n")
            return parsed_data
        parsed_data['1.1'] = parsed_data['1.1'].split(',')
        for tem in parsed_data['1.1']:
            if tem == 'nan':
                parsed_data['1.1'].remove(tem)
        
    return parsed_data

def get_question_biochar_multi_pdf_threadpool(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    with concurrent.futures.ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(get_question_biochar_multi_pdf_process_data, data, model, output_path, image_output_path, result1) for data in data_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

def get_question_biochar_multi_pdf_process_data(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
            if len(results_1['1.1']) == 0:
                results_1['1.1'].append("")
            
            try:
                total_iter = 0
                with open(data["markdown"], "r", encoding="utf-8") as f:
                    all_text = f.read()
                all_text = cut_before_section(all_text)
                for category in results_1['1.1']:
                    total_iter += 1
                    get_final_output(model, QuestionPrompt2, results_1, output_path, data, category, table_and_charts, all_text)
                    if total_iter >= 20:
                        return 0
            except Exception as e:
                time.sleep(random.randint(5, 10))
                # print(data['pdf'])
                print(f" Occurred: {e}. Retrying...")

        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    try:
                        results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, QuestionPromptPDF1)
                    except Exception as e:
                        time.sleep(random.randint(5, 10))
                        print(f" Occurred: {e}. Retrying...")
                    else:
                        with open(result1_path, "w", encoding="utf-8") as f:
                            f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            for category in results_1['1.1']:
                total_iter += 1
                get_final_output(model, QuestionPrompt2, results_1, output_path, data, category, table_and_charts, all_text)
                if total_iter >= 20:
                    return 0
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")

MAX_RETRIES = 5
BASE_SLEEP = 2.0 

def b64_data_url(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def sanitize_filename(name: str) -> str:
    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name

def get_text_from_response(resp) -> str:
    if hasattr(resp, "output_text") and isinstance(resp.output_text, str):
        return resp.output_text.strip()

    try:
        outputs = getattr(resp, "output", None)
        if outputs and len(outputs) > 0:
            contents = getattr(outputs[0], "content", None)
            if contents and len(contents) > 0:
                text = getattr(contents[0], "text", None)
                if isinstance(text, str):
                    return text.strip()
    except Exception:
        pass

    return str(resp)

def call_gpt_on_image(data_url: str, prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.responses.create(
                model=model,
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url}
                    ]
                }]
            )
            return get_text_from_response(resp)
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if ("429" in msg) or ("rate limit" in msg) or ("5" in msg and "error" in msg):
                sleep_s = BASE_SLEEP * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue
            else:
                raise

    raise RuntimeError(f"API request failed after {MAX_RETRIES} retries: {last_err}")

def collect_jpgs(folder: Path) -> List[Path]:
    return sorted([p for p in folder.glob("*.jpg")] + [p for p in folder.glob("*.jpeg")])

import re

def cut_before_section(all_text: str) -> str:
    patterns = [
        r"DISCUSSION",
        r"5\. Conclusions",
        r"CONCLUSIONS",
        r"REFERENCES",
        r"R E F E R E N C E S",
        r"C O N C L U S I O N S",
    ]
    
    regex = re.compile("|".join(patterns))

    match = regex.search(all_text)
    if match:
        return all_text[:match.start()].strip()
    else:
        return all_text  # 如果没找到，返回全文
    

def get_question_biochar_multi_pdf_threadpool_without_image_translator(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    for data in data_list:
        get_question_biochar_multi_pdf_process_data_without_image_translator(data, model, output_path, image_output_path, result1)
                
def get_question_biochar_multi_pdf_process_data_without_image_translator(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        sanitized = sanitize_filename(data['doi'])
    
        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
            if len(results_1['1.1']) == 0:
                results_1['1.1'].append("")
            
            try:
                total_iter = 0
                pdf_file = client_openai.files.create(
                    file=open(data['pdf'], "rb"),
                    purpose="assistants"
                #     purpose="user_data"
                )
                pdf_id = pdf_file.id
                for category in results_1['1.1']:
                    total_iter += 1
                    get_final_output_without_image_translator(model, question_prompt2_without_image_translator, results_1, output_path, data, category, pdf_id)
                    if total_iter >= 20:
                        return 0
            except Exception as e:
                time.sleep(random.randint(5, 10))
                # print(data['pdf'])
                print(f" Occurred: {e}. Retrying...")
        else:
            pdf_file = client_openai.files.create(
                file=open(data['pdf'], "rb"),
                purpose="assistants"
            #     purpose="user_data"
            )
            pdf_id = pdf_file.id
            results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, QuestionPromptPDF1)
            with open(result1_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
            if len(results_1['1.1']) == 0:
                results_1['1.1'].append("")
            
            try:
                total_iter = 0
                for category in results_1['1.1']:
                    total_iter += 1
                    get_final_output_without_image_translator(model, question_prompt2_without_image_translator, results_1, output_path, data, category, pdf_id)
                    if total_iter >= 20:
                        return 0
            except Exception as e:
                time.sleep(random.randint(5, 10))
                # print(data['pdf'])
                print(f" Occurred: {e}. Retrying...")
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    try:
                        results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, QuestionPromptPDF1)
                    except Exception as e:
                        time.sleep(random.randint(5, 10))
                        print(f" Occurred: {e}. Retrying...")
                    else:
                        with open(result1_path, "w", encoding="utf-8") as f:
                            f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            for category in results_1['1.1']:
                total_iter += 1
                get_final_output(model, QuestionPrompt2, results_1, output_path, data, category, table_and_charts, all_text)
                if total_iter >= 20:
                    return 0
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")
        
def get_final_output_without_image_translator(model, question_prompt2_without_image_translator, results_1, output_path: str, data, category, pdf_id):
    results_2 = interact_with_api_mp_biochar_2_without_image_translator(model, question_prompt2_without_image_translator, pdf_id, category)
    results_1_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_1.items():
            results_1_rename[get_question_name("query_1", key)] = value
            if value == 'nan':
                results_1_rename[get_question_name("query_1", key)] = ''

    results_1_rename['1.1. What category of mixtures design or formulation design is used to produce biochar-integrated construction materials?'] = category
    
    results_2_rename = {}
    if isinstance(results_1, dict):
        for key, value in results_2.items():
            results_2_rename[get_question_name("query_2", key)] = value
            if value == 'nan':
                results_2_rename[get_question_name("query_2", key)] = ''

    if (isinstance(results_1, dict)) and (isinstance(results_2, dict)):
        merged_result = {k: v for d in (results_1_rename, results_2_rename) for k, v in d.items()}
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            "text": '',
            "qa": merged_result,
            'model': model,
            "success": True
        }
    else:
        responses = {
            'doi': data['doi'],
            "pdf": data['pdf'],
            "text": '',
            "qa":{
                "results_1": results_1,
                "results_2": results_2,
            },
            'model': model,
            "success": False
        }
    with open(f'{output_path}/{data["doi"]}.jsonl', "a+") as wf:
        wf.write(json.dumps(responses) + '\n')

def get_question_biochar_multi_without_loop_threadpool(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_question_biochar_multi_without_loop, data, model, output_path, image_output_path, result1) for data in data_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

def get_question_biochar_multi_without_loop(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
    # for data in data_list:
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    start_time = time.time()
                    results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, QuestionPromptPDF1)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'prompt 1 elapsed time: {elapsed_time:.6f} secs')
                    with open(result1_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            # total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            category = ",".join(results_1['1.1'])
            get_final_output(model, QuestionPrompt2, results_1, output_path, data, category, table_and_charts, all_text)
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")
            
def get_question_biochar_multi_without_notes_threadpool(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_question_biochar_multi_without_notes, data, model, output_path, image_output_path, result1) for data in data_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

def get_question_biochar_multi_without_notes(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            # 目标文件
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    start_time = time.time()
                    results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, question_prompt1_without_notes)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'prompt 1 elapsed time: {elapsed_time:.6f} secs')
                    with open(result1_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            for category in results_1['1.1']:
                total_iter += 1
                get_final_output(model, question_prompt2_without_notes, results_1, output_path, data, category, table_and_charts, all_text)
                if total_iter >= 20:
                    return 0
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")
            
            
def get_question_biochar_multi_without_format_threadpool(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_question_biochar_multi_without_format, data, model, output_path, image_output_path, result1) for data in data_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")

def get_question_biochar_multi_without_format(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            # 目标文件
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    start_time = time.time()
                    results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, question_prompt1_without_format)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'prompt 1 elapsed time: {elapsed_time:.6f} secs')
                    with open(result1_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            for category in results_1['1.1']:
                total_iter += 1
                get_final_output(model, question_prompt2_without_format, results_1, output_path, data, category, table_and_charts, all_text)
                if total_iter >= 20:
                    return 0
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")
            
def get_question_biochar_multi_200_threadpool(data_list: List[Dict], model: str, output_path: str, image_output_path: str, result1: str):
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(get_question_biochar_multi_200, data, model, output_path, image_output_path, result1) for data in data_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")
def get_question_biochar_multi_200(data: Dict, model: str, output_path: str, image_output_path: str, result1: str):
        client = OpenAI(
            base_url=YOUR_URL,
            api_key=YOUR_KEY
        )
        client_openai = OpenAI(http_client=httpx.Client(verify = False))
        start_time = time.time()
        for i in range(5):
            # 目标文件
            sanitized = sanitize_filename(data['doi'])
            convert_image_path = os.path.join(image_output_path, f"{sanitized}.jsonl")
            if os.path.exists(convert_image_path):
                record = pd.read_json(convert_image_path, lines = True)
                table_and_charts = record['table_and_charts'][0]
            else:
                jpgs = collect_jpgs(Path(data["images"]))
                if not jpgs:
                    raise FileNotFoundError(f"No .jpg/.jpeg files found in: {data['images']}")

                # print(f"Found {len(jpgs)} images. Sending to model {MODEL} ...")

                per_image_sections = []
                for idx, img_path in enumerate(jpgs, start=1):
                    try:
                        base64_image = encode_image(img_path)
                        response = client.chat.completions.create(
                            model="gemini-2.5-pro",
                            messages=[
                                {
                                "role": "user",
                                "content": [
                                    {
                                    "type": "text",
                                    "text": chart_to_table_prompt,
                                    },
                                    {
                                    "type": "image_url",
                                    "image_url": {
                                        "url":  f"data:image/jpeg;base64,{base64_image}"
                                    },
                                    },
                                ],
                                }
                            ],
                        )
                        section = (
                            f"### Image {idx}: {img_path.name}\n\n"
                            f"{response.choices[0].message.content.strip()}\n"
                        )
                        per_image_sections.append(section)
                        print(f"[OK] {img_path.name}")
                    except Exception as e:
                        err_section = f"### Image {idx}: {img_path.name}\n\n[ERROR] {e}\n"
                        per_image_sections.append(err_section)
                        print(f"[ERROR] {img_path.name}: {e}")

                table_and_charts = ("\n\n---\n\n").join(per_image_sections).strip()

                record = {
                    "doi": data['doi'],
                    "table_and_charts": table_and_charts,
                    "image_count": len(jpgs)
                }

                with open(convert_image_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f'converted file elapsed time: {elapsed_time:.6f} secs')
                break

        result1_path = os.path.join(result1, f"{sanitized}.jsonl")
        if os.path.exists(result1_path):
            with open(result1_path, "r", encoding="utf-8") as f:
                results_1_record = [json.loads(line) for line in f]
            results_1 = results_1_record[0]
        else:
            for i in range(5):
                try:
                    pdf_file = client_openai.files.create(
                        file=open(data['pdf'], "rb"),
                        purpose="assistants"
                    #     purpose="user_data"
                    )
                    pdf_id = pdf_file.id
                except Exception as e:
                    time.sleep(random.randint(5, 10))
                    # print(data['pdf'])
                    print(f" Occurred: {e}. Retrying...")
                except openai.error.APIerror:
                    time.sleep(random.randint(5, 10))
                    print(f"APIError了。")
                else:
                    success = True
                    # print(f"success")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'upload file elapsed time: {elapsed_time:.6f} secs')
                    start_time = time.time()
                    results_1 = interact_with_api_mp_biochar_multi_pdf_1(pdf_id, model, question_prompt1200, data['doi'])
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f'prompt 1 elapsed time: {elapsed_time:.6f} secs')
                    with open(result1_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(results_1, ensure_ascii=False) + "\n")
                    break
            
        try:
            total_iter = 0
            with open(data["markdown"], "r", encoding="utf-8") as f:
                all_text = f.read()
            all_text = cut_before_section(all_text)
            for category in results_1['1.1']:
                total_iter += 1
                get_final_output_200(model, question_prompt2200, results_1, output_path, data, category, table_and_charts, all_text)
                if total_iter >= 20:
                    return 0
        except Exception as e:
            time.sleep(random.randint(5, 10))
            # print(data['pdf'])
            print(f" Occurred: {e}. Retrying...")
