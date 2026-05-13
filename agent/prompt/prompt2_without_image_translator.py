

from pydantic import BaseModel
from typing import List
from string import Template
meta_prompt = '''Please read the attached academic paper (PDF) and answer the following questions using only concise text directly extracted from the document.
Then answer the following questions using only concise text directly extracted from the document.
Do not use any information that is not present in the text.
Do not use your own knowledge or external sources.
If the document does not provide enough information to answer a question, reply with 'nan'.

Given the following conditions:
Categories of mixtures design or formulations design of biochar-integrated construction materials: $category

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

1.1. What is the density of the biochar-integrated construction materials in the hardened state? The answer should be expressed in kilograms per cubic meter (kg/m^3). Provide answers in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 2000 ± 36. Answer format example 2: 2000. 
1.2. What is the compressive strength of the biochar-integrated construction materials after 28 days of curing? The answer should be expressed in megapascals (MPa), rounded to one decimal place. If the original text mentions standard deviation, include it afterward. Answer format example 1: 52.1 ± 3.6. Answer format example 2: 8.9. If there are different curing methods, considering only water curing.
1.3. What is the flow table or slump test value of the biochar-integrated construction materials in the fresh state? Provide the answer as a numerical value expressed in millimeters (mm) in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 160 ± 5. Answer format example 2: 160.
1.4. What is the thermal conductivity of the biochar-integrated construction materials after 28 days of curing? The answer should be expressed in watts per meter-kelvin (W/(m·K)), rounded to two decimal places. If the original text mentions standard deviation, include it afterward. Answer format example 1: 1.02 ± 0.05. Answer format example 2: 0.83. 
1.5. What is the life cycle analysis carbon footprint of biochar-integrated construction materials? The answer should be expressed in kilograms of CO_2 emissions per cubic meter of biochar-integrated construction materials (kg CO_2e/m^3 or kg CO_2eq/m^3). Provide answers in integer numerical form. If the original text mentions standard deviation, include it afterward. Answer format example 1: 300 ± 36. Answer format example 2: 250. If the value is given as tons of CO_2 emissions per cubic meter (t CO_2e/m^3 or t CO_2eq/m^3), please convert it to kilograms of CO_2 emissions per cubic meter by the relationship of 1 ton of CO_2 emissions per cubic meter = 1000 kilograms of CO_2 emissions per cubic meter. If the value is given as kilograms of CO_2 emissions per ton (kg CO_2e/t or kg CO_2eq/t), please convert it to kilograms of CO_2 emissions per cubic meter (kg CO_2e/m^3 or kg CO_2eq/m^3) by multiplying by the density value in 3.1 and dividing by 1000.
1.6. What are the mass ratios of biochar to total mixtures in biochar-integrated construction materials? Provide the answer as comma-separated values, rounded to three decimal places. (Note: total mixtures: sum of all the types or components of raw materials used to produce the biochar-integrated construction materials.) If this value is not provided directly in the given text, please calculate it by the incorporated biochar mass divided by the total mass of the mixture. If there is a reference group without biochar, please answer 0.000. Example format: 0.180
1.7. What is the type of biochar-integrated construction materials? Choose one option from (a-i) below. Please respond with just the letter of your choice.
a. Concrete (Note: Concrete: it refers to construction materials made from cementitious materials, fine aggregates, coarse aggregate, admixtures or additives, fiber, water, and others. Coarse aggregate must be included.)
b. Mortar or paste (Note: Mortar or paste: it refers to construction materials made from cementitious materials, admixtures or additives, fiber, water, and others. Coarse aggregate must not be included.)
c. Paving brick, permeable brick, eco-brick or other bricks (Note: Paving brick, permeable brick, eco-brick or other bricks: they are refer to bricks or blocks used for paving roads, walkways, or for building walls. This includes special types such as permeable bricks (which allow water to pass through), eco-bricks (environmentally friendly bricks), or any other brick types that incorporate biochar.)
d. Insulation board (Note: Insulation board: Boards or panels used for thermal or acoustic insulation in buildings. These can be made from various materials (e.g., foam, mineral wool, or natural fibers) and may include biochar to enhance insulation properties.)
e. Gypsum composites (Note: Gypsum composites: This phrase refers to building materials that are made by combining gypsum (a soft sulfate mineral composed of calcium sulfate dihydrate) with other substances such as fibers, polymers, aggregates or additives.)
f. Asphalt composites (Note: Asphalt composites: This phrase refers to engineered materials made by combining asphalt (a sticky, black, and highly viscous liquid or semi-solid form of petroleum) with other components such as aggregates (sand, gravel, or crushed stone), polymers, fibers, or other additives.)
g. 3D printing materials (Note: 3D printing materials: Materials specifically designed for use in 3D printing technologies for construction.)
h. Coating (Note: Coating: Surface coatings, paints or finishes that include biochar as an ingredient.)
i. Others (Note: Others: Any other type of construction material not covered by the above categories.)
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
a. Cementitious materials (Note: Use as or replace cementitious materials)
b. Admixture or additive (Note: Use as admixture or additive)
c. Aggregate (Note: Directly use as or replace aggregate)
d. Developing aggregate (Note: biochar is first used to produce aggregate and then is used as biochar aggregate to replace natural aggregate)
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
'''


class QuestionPromptMultiPDF2_without_image_translator:
    def __init__(self):
        self.chat_history = []

    @staticmethod
    def get_prompted_input(user_input):
        category = user_input
        return Template(meta_prompt).substitute(category = category)

    def get_history(self):
        self.chat_history = self.chat_history.append({'role': 'user', 'content': self.get_prompted_input()})
        return self.chat_history

class QuestionOutputMultiPDF2(BaseModel):
    type_list: List[str]
    classification_list: List[str]
    source: str
    pretreatments: str
    region_total_amount: str
    global_total_amount: str
    pyrolysis_system: str
    scale: str
    post_treatments_of_the_produced_biochar: str
    produced_biochar_will_be_used_for: str
    post_treatments_of_the_produced_syngas: str
    Is_the_generated_syngas_gas_used_for_this_pyrolysis_system: str
    post_treatments_of_the_produced_bio_oil: str
    Is_the_generated_bio_oil_used_for_this_pyrolysis_system: str
    region_total_amount: str
    global_total_amount: str
