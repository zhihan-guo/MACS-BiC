

from pydantic import BaseModel
from typing import List
from string import Template
meta_prompt = '''Please read given document which includes tables and academic paper.
Then answer the following questions using only concise text directly extracted from the document.
Do not use any information that is not present in the text.
Do not use your own knowledge or external sources.
If the document does not provide enough information to answer a question, reply with 'nan'.

Given the following conditions:
Categories of mixtures design or formulations design of biochar-integrated construction materials: $category

1.1. What is the density of the biochar-integrated construction materials in the hardened state? The answer should be expressed in kilograms per cubic meter (kg/m^3). Provide answers in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 2000 ± 36. Answer format example 2: 2000. 
1.2. What is the compressive strength of the biochar-integrated construction materials after 28 days of curing? The answer should be expressed in megapascals (MPa), rounded to one decimal place. If the original text mentions standard deviation, include it afterward. Answer format example 1: 52.1 ± 3.6. Answer format example 2: 8.9. If there are different curing methods, considering only water curing.
1.3. What is the flow table or slump test value of the biochar-integrated construction materials in the fresh state? Provide the answer as a numerical value expressed in millimeters (mm) in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 160 ± 5. Answer format example 2: 160.
1.4. What is the thermal conductivity of the biochar-integrated construction materials after 28 days of curing? The answer should be expressed in watts per meter-kelvin (W/(m·K)), rounded to two decimal places. If the original text mentions standard deviation, include it afterward. Answer format example 1: 1.02 ± 0.05. Answer format example 2: 0.83. 
1.5. What is the life cycle analysis carbon footprint of biochar-integrated construction materials? The answer should be expressed in kilograms of CO_2 emissions per cubic meter of biochar-integrated construction materials (kg CO_2e/m^3 or kg CO_2eq/m^3). Provide answers in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 300 ± 36. Answer format example 2: 250. If the value is given as tons of CO_2 emissions per cubic meter (t CO_2e/m^3 or t CO_2eq/m^3), please convert it to kilograms of CO_2 emissions per cubic meter by the relationship of 1 ton of CO_2 emissions per cubic meter = 1000 kilograms of CO_2 emissions per cubic meter. If the value is given as kilograms of CO_2 emissions per ton (kg CO_2e/t or kg CO_2eq/t), please convert it to kilograms of CO_2 emissions per cubic meter (kg CO_2e/m^3 or kg CO_2eq/m^3) by multiplying by the density value in 3.1 and dividing by 1000.
1.6. What are the mass ratios of biochar to total mixtures in biochar-integrated construction materials? Provide the answer as comma-separated values, rounded to three decimal places.
1.7. What is the type of biochar-integrated construction materials? Choose one option from (a-i) below. Please respond with just the letter of your choice.
a. Concrete
b. Mortar or paste
c. Paving brick, permeable brick, eco-brick or other bricks
d. Insulation board
e. Gypsum composites
f. Asphalt composites
g. 3D printing materials
h. Coating
i. Others
1.8. What is the classification of the feedstock or biomass used to produce biochar in this document? Choose one option from (a-h) below. Provide the answer as just comma-separated letter lists.
a. Agricultural residues, such as crop stalks/straw (e.g., corn stover, rice husks, wheat straw); Nut shells (e.g., coconut shells, almond shells, peanut shells); Fruit residues (e.g. olive pits, date palm waste, pineapple peels); Seed husks (e.g., sunflower husks, cotton gin trash)
b. Forestry and wood waste, such as logging residues (e.g. sawdust, wood chips, bark); Pruning waste (e.g. fruit tree branches, vineyard trimmings); Processed wood waste (e.g. sawmill by-products, plywood scraps)
c. Animal manure and by-products, such as poultry litter (chicken, turkey manure); Cattle dung Swine manure; Fish processing waste
d. Municipal and urban organic waste, such as food waste (e.g. kitchen scraps, spoiled produce); Yard waste (e.g. grass clippings, leaves, tree trimmings); Sewage sludge (bio-solids after treatment); Paper/cardboard waste
e. Industrial and processing by-products, such as bagasse (sugarcane processing waste); Brewery/spent grain; Coffee grounds; Pulp and paper mill sludge; Cotton gin trash
f. Energy Crops, such as switch-grass; Miscanthus; Willow; Bamboo
g. Aquatic and marine biomass, such as algae (macro-algae and micro-algae); Water hyacinth; Seaweed; Aquatic weeds
h. Other organic wastes, such as tea waste; Wine pomace (grape skins/seeds); Tobacco waste; Coconut coir. 
1.9. What type of feedstock or biomass is used to produce biochar in this document? Please respond with just comma-separated types. The type should be one word or a short phrase. Example format : wood sawdust. 
1.10. What temperature is used in the pyrolysis process from feedstock or biomass to biochar? Convert the unit to degrees Celsius (°C). Provide the answer as just comma-separated integer values. Example format: 300
1.11. What is the role or function of biochar in the biochar-integrated construction material? Choose one option from (a-c) below. Provide the answer as just comma-separated letter lists.
a. Cementitious materials
b. Admixture or additive
c. Aggregate
d. Developing aggregate
1.12. What is the mass ratio of biochar to cementitious materials in biochar-integrated construction material? Please calculating the mass of cementitious materials as the sum mass of biochar and cementitious materials. Provide the answer as "nan", if the answer of question 1.6 is not a or b. Provide the answer as comma-separated values, rounded to two decimal places. If there is a reference group without biochar, please answer as 0.00. Example format: 0.18
1.13. What is the mass ratio of biochar to aggregate in biochar-integrated construction material? Please calculating the mass of aggregate as the sum mass of biochar and aggregate. Provide the answer as "nan" if the answer of question 1.6 is not c. Provide the answer as comma-separated values, rounded to two decimal places. If there is a reference group without biochar, please answer as 0.00. Example format: 0.18
1.14. What is the mass or volume ratio of biochar aggregate to total aggregate in biochar-integrated construction material? Please calculating the mass or volume of total aggregate as the sum mass or volume of biochar aggregate and other aggregates. Provide the answer as "nan" if the answer of question 1.6 is not d. Provide the answer as comma-separated values, rounded to two decimal places. If there is a reference group without biochar, please answer as 0.00. Example format: 0.18

Please provide your responses in the following format.
1.1: an integer value of density (question 1.1)
1.2: a float number of compressive strength (question 1.2)
1.3: a float number of flow table or slump test value (question 1.3)
1.4: a float number of thermal conductivity (question 1.4)
1.5: a float number of carbon footprint (question 1.5)
1.6: a float number of the mass ratio of biochar to total mixtures (question 1.6)
1.7: a letter of the type of biochar-integrated construction materials (question 1.7)
1.8: a letter of the classifications of the feedstock or biomass (question 1.8)
1.9: a type of feedstock or biomass (question 1.9)
1.10: an integer value of temperature (question 1.10)
1.11: a letter of biochar role (question 1.11)
1.12: a float number of the mass ratio of biochar to cementitious materials (question 1.12)
1.13: a float number of the mass ratio of biochar to aggregate (question 1.13)
1.14: a float number of the mass or volume ratio of biochar aggregate to total aggregate (question 1.14)

Document:

Given tables:
$table_and_charts

Given paper:
$all_text
'''

class QuestionPrompt2WithoutNotes:
    def __init__(self):
        self.chat_history = []

    @staticmethod
    def get_prompted_input(user_input):
        category, table_and_charts, all_text = user_input
        return Template(meta_prompt).substitute(category = category, table_and_charts = table_and_charts, all_text = all_text)

    def get_history(self, user_input):
        self.chat_history = self.chat_history.append({'role': 'user', 'content': self.get_prompted_input(user_input)})
        return self.chat_history

class QuestionOutput2(BaseModel):
    question_1_1: int
    question_1_2: float
    question_1_3: float
    question_1_4: float
    question_1_5: float
    question_1_6: float
    question_1_7: str
    question_1_8: str
    question_1_9: str
    question_1_10: int
    question_1_11: str
    question_1_12: float
    question_1_13: float
    question_1_14: float
