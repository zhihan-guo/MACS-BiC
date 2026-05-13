

from pydantic import BaseModel
from typing import List
from string import Template
meta_prompt = '''Please read given document which includes tables and academic paper.
Then answer the following questions using only concise text directly extracted from the document.
Do not use any information that is not present in the text.
Do not use your own knowledge or external sources.
If the document does not provide enough information to answer a question, reply with 'nan'.

Questions: 
1.1. What categories of mixtures design or formulations design are used to produce biochar-integrated construction materials in this document? Please respond with just comma-separated categories. Example format 1: 1BR500-1. Example format 2: 2BR700-2. 
1.2. What is the particle size range (just from minimum value to maximum value) of the biochar before it is applied or mixed into any mixtures? Provide the answer as just a range expressed in millimeters (mm) of float number, rounded to two decimal places. Example format: 1.18–2.36.
1.3. What is the moisture content of the biochar before it is applied or mixed into any mixtures? (Note: Moisture content of biochar: The proportion of water present in the biochar, usually expressed as a percentage of the dry biochar mass.) Convert the unit to wt.%. Provide the answer as just a float number, rounded to two decimal places. If the original text mentions standard deviation, include it afterward. Answer format example: 5.60 ± 0.58 or 0.57.

2.1. Is modulus property of biochar-integrated construction materials included in the given document? The answer should be "yes" or "no". 
2.2. Is durability of biochar-integrated construction materials included in the given document? The answer should be "yes" or "no". 
2.3. Is fire resistance performance of biochar-integrated construction materials included in the given document? The answer should be "yes" or "no".
2.4. Is carbon footprint of biochar-integrated construction materials analyzed in the given document? The answer should be "yes" or "no".

Please provide your responses in the following format:
If there are multiple values for the category of mixture design or formulation design (1.1) please separate them with commas. Ensure that the values in the two lists correspond in order.

1.1: a comma-separated categories list of mixtures design or formulations design (question 1.1)
1.2: a range of particle size (question 1.2)
1.3: a float number of moisture content (question 1.3)
2.1: "yes" or "no" (question 2.1)
2.2: "yes" or "no" (question 2.2)
2.3: "yes" or "no" (question 2.3)
2.4: "yes" or "no" (question 2.4)
'''


class QuestionPromptPDF1WithoutNotes:
    def __init__(self):
        self.chat_history = []

    @staticmethod
    def get_prompted_input():
        return Template(meta_prompt).substitute()

    def get_history(self):
        self.chat_history = self.chat_history.append({'role': 'user', 'content': self.get_prompted_input()})
        return self.chat_history

class QuestionOutput1WithoutNotes(BaseModel):
    question_1_1: List[str]
    question_1_2: str
    question_1_3: List[float]
    question_2_1: str
    question_2_2: str
    question_2_3: str
    question_2_4: str