

from pydantic import BaseModel
from typing import List
from string import Template
meta_prompt = '''Please read given document which includes tables and academic paper.
Then answer the following questions using only concise text directly extracted from the document.
Do not use any information that is not present in the text.
Do not use your own knowledge or external sources.
If the document does not provide enough information to answer a question, reply with 'nan'.

Notes:
Biochar: Stable, carbon-rich solid material produced by pyrolysis (thermal decomposition without oxygen) of feedstock or biomass.
Biochar-integrated construction materials: Construction materials (such as concrete, mortar, bricks, or composites) that are mixed with biochar. The biochar-integrated construction materials not include aggregate produced with biochar.
The types / components of the raw material of biochar-integrated construction materials include: cement, cementitious materials, aggregate, gypsum, asphalt, admixtures/additives, fiber, water, biochar, and others.
Cement: Cement is a binder, a substance used in construction that hardens and sets to adhere materials together. Ordinary Portland Cement (OPC) is a type of cement
Cementitious materials: Substances that act as cement (bind and harden with water), such as fly ash, slag, silica fume, and natural pozzolans (include cement).
Aggregates: Granular materials (sand, gravel, crushed stone, recycled/artificial aggregates) used in concrete or brick.
Fine aggregate: aggregate with a size less than 4.75 millimeters (mm).
Coarse aggregate: aggregate with a size greater than 4.75 millimeters (mm).
Admixtures/additives: Substances added to construction materials to improve properties (e.g., workability, strength, durability).

Questions: 
1.1. What categories of mixtures design or formulations design are used to produce biochar-integrated construction materials in this document?
1.2. What is the particle size range (just from minimum value to maximum value) of the biochar before it is applied or mixed into any mixtures?
1.3. What is the moisture content of the biochar before it is applied or mixed into any mixtures?

2.1. Is modulus property of biochar-integrated construction materials included in the given document?
2.2. Is durability of biochar-integrated construction materials included in the given document?
2.3. Is fire resistance performance of biochar-integrated construction materials included in the given document?
2.4. Is carbon footprint of biochar-integrated construction materials analyzed in the given document?

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


class QuestionPromptPDF1WithoutFormat:
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