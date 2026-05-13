

from pydantic import BaseModel
from typing import List
from string import Template
meta_prompt = '''Please read the attached academic paper (PDF) and answer the following questions using only concise text directly extracted from the document.
Do not use any information that is not present in the text.
Do not use your own knowledge or external sources.
If the values are in charts, your answers should be:
1. Extract only the main value (ignore error sticks/text annotations like "% change")
2. Identify axis units: Convert units when mismatched (e.g. from m to mm: multiply by 1,000); Keep original values if units match requirements
3. Validate against context: Cross-check extracted values with the textual results in the paper.

Notes:
Biochar: Stable, carbon-rich solid material produced by pyrolysis (thermal decomposition without oxygen) of feedstock or biomass.
Biochar-integrated construction materials: Construction materials (such as concrete, mortar, bricks, or composites) that are mixed with biochar. Biochar-integrated construction materials do not include aggregate produced with biochar.
The types or components of the raw material of biochar-integrated construction materials include cement, slag, fly ash, silica fume, biochar, fiber, water, sand/fine aggregate, gravel/coarse aggregate, biochar-developed aggregate, admixtures, etc.
Cement: Cement is a binder, a substance used in construction that hardens and sets to adhere materials together. Ordinary Portland cement (OPC) is a type of cement. There are generally three grades of cement: 32.5, 42.5, and 52.5.
Cementitious materials: Substances that act as cement (bind and harden with water), such as fly ash, slag, and silica fume.
Binder: a substance used in construction that hardens and sets to adhere materials together, including cement and cementitious materials. 
Aggregates: Granular materials (sand, gravel, crushed stone, recycled/artificial aggregates) used in concrete or brick.
Fine aggregate: aggregate with a size less than 4.75 millimeters (mm). Sand is a fine aggregate.
Coarse aggregate: aggregate with a size greater than 4.75 millimeters (mm). Gravel is a coarse aggregate.
Admixtures/additives: Substances added to construction materials to improve properties (e.g., workability, strength, durability).

Questions: 
Note: If the document does not provide enough information to answer a question, reply with 'nan'.

1.1. What categories of mixtures design or formulations design are used to produce biochar-integrated construction materials in this document? Please respond with just comma-separated categories. Example format 1: 1BR500-1. Example format 2: 2BR700-2. 
Note 1: categories of mixtures design or formulations design refers to the unique alphanumeric identifiers assigned to distinct experimental batches of biochar-integrated construction materials. 
Note 2: The category should be alphanumeric identifiers and typically consist of different variables. For example, in the two examples given, 1BR and 2BR represent different biochar types; 500 and 700 represent different pyrolysis temperatures in biochar production; The last digits 1 and 2 represent different usage levels of biochar. This alphanumeric identifiers can have fewer or more variables combinations depending on the situation.
Note 3: If two or more formulations or mixtures are put toghther as one category, please seperate them with different categories. For example: 500-1 & 700-1. The example means that there are two different of biochar, one produced at 500 degrees Celsius and the other produced at 700 degrees Celsius, however, they used as same dosage of 1% in the mixture. Please seperate them into two categories with one of 500-1 and the other of 700-1.
Note 4: Please include the reference group or control group without biochar usage. Example format 1: BR0. 
Note 5: Please not include aggregate produced with biochar in the category.

Please provide your responses in the following format:
If there are multiple values for the category of mixture design or formulation design (1.1) please separate them with commas. Ensure that the values in the two lists correspond in order.

1.1: a comma-separated categories list of mixtures design or formulations design (question 1.1)
'''


class QuestionPromptPDF1200:
    def __init__(self):
        self.chat_history = []

    @staticmethod
    def get_prompted_input():
        return Template(meta_prompt).substitute()

    def get_history(self):
        self.chat_history = self.chat_history.append({'role': 'user', 'content': self.get_prompted_input()})
        return self.chat_history

class QuestionOutput1(BaseModel):
    question_1_1: List[str]
    question_1_2: str
    question_1_3: List[float]
    question_2_1: str
    question_2_2: str
    question_2_3: str
    question_2_4: str
