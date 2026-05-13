

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

Given the following conditions: $category

Notes:
Biochar: Stable, carbon-rich solid material produced by pyrolysis (thermal decomposition without oxygen) of feedstock or biomass.
Biochar-integrated construction materials: Construction materials (such as concrete, mortar, bricks, or composites) that are mixed with biochar. Biochar-integrated construction materials do not include aggregate produced with biochar.
The types or components of the raw material of biochar-integrated construction materials include cement, slag, fly ash, silica fume, biochar, fiber, water, sand/fine aggregate, gravel/coarse aggregate, biochar-developed aggregate, admixtures, and other materials.
Cement: Cement is a binder, a substance used in construction that hardens and sets to adhere materials together. Ordinary Portland cement (OPC) is a type of cement. There are generally three grades of cement: 32.5, 42.5, and 52.5.
Cementitious materials: Substances that act as cement (bind and harden with water), such as fly ash, slag, and silica fume.
Binder: a substance used in construction that hardens and sets to adhere materials together, including cement and cementitious materials. 
Aggregates: Granular materials (sand, gravel, crushed stone, recycled/artificial aggregates) used in concrete or brick.
Fine aggregate: aggregate with a size less than 4.75 millimeters (mm). Sand is a fine aggregate.
Coarse aggregate: aggregate with a size greater than 4.75 millimeters (mm). Gravel is a coarse aggregate.
Admixtures/additives: Materials other than water, aggregates, and cement that are added to concrete mixtures to modify and improve specific properties of the concrete, such as workability, setting time, strength, durability, or resistance to environmental conditions. Common types include water reducers, superplasticizers, accelerators, retarders, air-entraining agents, etc.
Other materials: Materials used to develop biochar-integrated construction materials, but not cement, slag, fly ash, silica fume, biochar, fiber, water, sand/fine aggregate, gravel/coarse aggregate, aggregates for biochar development, and admixtures. 

1. Please identify or calculate the component ratios of the biochar-integrated construction materials in the provided document. Respond to the 17 questions below. 
Note 1: The total mass of the mixture refers to the sum of the masses of all types or components of raw materials used to produce the biochar-integrated construction material, including
cement, slag, fly ash, silica fume, biochar, fiber, water, sand/fine aggregate, gravel/coarse aggregate, biochar-developed aggregate, and admixtures. 
Note 2: binder mass means the sum of cement, slag, fly ash, and silica fume masses; cementitious materials mass means the sum of slag, fly ash, and silica fume masses; aggregate mass means the sum of fina aggregate, coarse aggregate, and biochar developed aggregate.)
Note 3: If the document does not provide sufficient information about one or more types or components of raw materials used to produce the biochar-integrated construction material, its content should be considered "0", and the mass ratio of the relevant component should be answered as "0".

"Example 1": If 1 unit (generally one cubic meter) of biochar-integrated construction material is produced with cement of 300 kg, slag of 100 kg, fly ash of 70 kg, silica fume of 50 kg, biochar of 20 kg, fiber of 5 kg, water of 150 kg, fine aggregate of 600 kg, coarse aggregate of 800 kg, biochar developed aggregate of 250 kg with biochar content of 10%, admixtures of 5 kg, and other materials of 50 kg: (1) the mass ratio of cement in biochar-integrated construction materials should be calculated to be 0.1250 by dividing the cement mass of 300 kg by the total mass of the mixtures of 2400 kg; (2) the mass ratio of slag in biochar-integrated construction materials should be calculated to be 0.0417 by dividing the slag mass of 100 kg by the total mass of the mixtures of 2400 kg; (3) the mass ratio of fly ash in biochar-integrated construction materials should be calculated to be 0.0292 by dividing the fly ash mass of 70 kg by the total mass of the mixtures of 2400 kg; (4) the mass ratio of silica fume in biochar-integrated construction materials should be calculated to be 0.0208 by dividing the silica fume mass of 50 kg by the total mass of the mixtures of 2400 kg; (5) the mass ratio of biochar in biochar-integrated construction materials should be calculated to be 0.0188 by dividing the total biochar mass of 45 kg (20 kg from directly utilized biochar and 25 kg from the biochar in the biochar developed aggregate) by the total mass of the mixtures of 2400 kg; (6) the mass ratio of fiber in biochar-integrated construction materials should be calculated to be 0.0021 by dividing the fiber mass of 5 kg by the total mass of the mixtures of 2400 kg; (7) the mass ratio of water in biochar-integrated construction materials should be calculated to be 0.0625 by dividing the water mass of 150 kg by the total mass of the mixtures of 2400 kg; (8) the mass ratio of fine aggregate in biochar-integrated construction materials should be calculated to be 0.2500 by dividing the fine aggregate mass of 600 kg by the total mass of the mixtures of 2400 kg; (9) the mass ratio of coarse aggregate in biochar-integrated construction materials should be calculated to be 0.3333 by dividing the coarse aggregate mass of 800 kg by the total mass of the mixtures of 2400 kg; (10) the mass ratio of biochar developed aggregate in biochar-integrated construction materials should be calculated to be 0.1042 by dividing the biochar developed aggregate mass of 250 kg by the total mass of the mixtures of 2400 kg; (11) the mass ratio of admixtures in biochar-integrated construction materials should be calculated to be 0.0021 by dividing the admixtures mass of 5 kg by the total mass of the mixtures of 2400 kg; (12) the mass ratio of other materials in biochar-integrated construction materials should be calculated to be 0.0208 by dividing the other materials mass of 50 kg by the total mass of the mixtures of 2400 kg; (13) the mass ratio of binder in biochar-integrated construction materials should be calculated to be 0.2167 by dividing the binder mass of 520 kg by the total mass of the mixtures of 2400 kg; (14) the mass ratio of water to binder should be calculated to be 0.2885 by dividing the water mass of 150 kg by the binder mass of 520 kg; (15) the mass ratio of supplementary cementitious materials to binder should be calculated to be 0.4231 by dividing the supplementary cementitious materials mass of 220 kg by the binder mass of 520 kg; (16) the mass ratio of aggregate to binder should be calculated to be 3.1731 by dividing the aggregate mass of 1650 kg by the binder mass of 520 kg; (17) the mass ratio of biochar to binder should be calculated to be 0.0865 by dividing the total biochar mass of 45 kg (20 kg from directly utilized biochar and 25 kg from the biochar in the biochar developed aggregate) by the binder mass of 520 kg.
"Example 2": If the biochar-integrated construction material is produced with slag-to-cement ratio of 0.4000, fly ash-to-cement ratio of 0.2333, silica fume-to-cement ratio of 0.1667, fiber-to-cement ratio of 0.0167, water-to-cement ratio of 0.5000, fine aggregate-to-cement ratio of 2.000, coarse aggregate-to-cement ratio of 2.6667, biochar developed aggregate-to-cement ratio of 0.8333, admixtures-to-cement ratio of 0.0167, and other materials-to-cement ratio of 0.1667, then the composition of the biochar-integrated construction material is cement of 1 unit, slag of 0.4000 unit, fly ash of 0.2333 unit, silica fume of 0.1667 unit, fiber of 0.0167 unit, water of 0.5000 unit, fine aggregate of 2.000 unit, coarse aggregate of 2.6667 unit, biochar developed aggregate of 0.8333 unit, admixtures of 0.0167 unit, and other materials of 0.1667 unit. With these compositions, the component ratios the biochar-integrated construction material can be calculated as the methods should in "Example 1". For example, the mass ratio of cement in biochar-integrated construction materials should be calculated to be 0.1250 by dividing the cement mass of 1 unit by the total mass of the mixtures of 8 unit. 
"Example 3": If (i) the basic or reference formulation (C0) of the biochar-integrated construction material is produced with slag-to-cement ratio of 0.4000, fly ash-to-cement ratio of 0.2333, silica fume-to-cement ratio of 0.1667, fiber-to-cement ratio of 0.0167, water-to-cement ratio of 0.5000, fine aggregate-to-cement ratio of 2.000, coarse aggregate-to-cement ratio of 2.6667, biochar developed aggregate-to-cement ratio of 0.8333, admixtures-to-cement ratio of 0.0167, and other materials-to-cement ratio of 0.1667, and (ii) 10% of cement is replaced with biochar for develop biochar-integrated construction material of C10, then the composition of C10 is cement of 0.9 unit, slag of 0.3600 unit, fly ash of 0.2100 unit, silica fume of 0.1500 unit, biochar of 0.1000 unit, fiber of 0.0150 unit, water of 0.4500 unit, fine aggregate of 1.800 unit, coarse aggregate of 2.400 unit, biochar developed aggregate of 0.7500 unit, admixtures of 0.0150 unit, and other materials of 0.1500 unit. With these compositions, the component ratios the biochar-integrated construction material can be calculated as the methods should in "Example 1". For example, the mass ratio of cement in biochar-integrated construction materials should be calculated to be 0.1233 by dividing the cement mass of 0.9000 unit by the total mass of the mixtures of 7.300 unit. 

1.1. What is the mass ratio of cement in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the cement mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.1250. 
1.2. What is the mass ratio of slag in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the slag mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0417. 
1.3. What is the mass ratio of fly ash in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the fly ash mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0292. 
1.4. What is the mass ratio of silica fume in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the silica fume mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0208. 
1.5. What is the mass ratio of biochar in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the total biochar mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0188. 
1.6. What is the mass ratio of fiber in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the fiber mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0021. 
1.7. What is the mass ratio of water in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the water mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0625. 
1.8. What is the mass ratio of fine aggregate in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the fine aggregate mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.2500. 
1.9. What is the mass ratio of coarse aggregate in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the coarse aggregate mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.3333. 
1.10. What is the mass ratio of biochar developed aggregate in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the biochar developed aggregate mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.1042. 
1.11. What is the mass ratio of admixtures in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the admixtures mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0021.
1.12. What is the mass ratio of other materials in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the other materials mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0208. 
1.13. What is the mass ratio of binder in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the binder mass by the total mass of the mixture. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.2167. (Note: The binder mass refers to the sum of the masses of cement, slag, fly ash, and silica fume.) 
1.14. What is the mass ratio of water to binder in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the water mass by the binder mass. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.2885. (Note: The binder mass refers to the sum of the masses of cement, slag, fly ash, and silica fume.)
1.15. What is the mass ratio of supplementary cementitious materials to binder in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the supplementary cementitious materials mass by the binder mass. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.4231. (Note: The supplementary cementitious materials mass refers to the sum of the masses of slag, fly ash, and silica fume. The binder mass refers to the sum of the masses of cement, slag, fly ash, and silica fume.) 
1.16. What is the mass ratio of aggregate to binder in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the aggregate mass by the binder mass. Provide the answer of a floating number, rounded to four decimal places. Example format: 3.1731. (Note: The binder mass refers to the sum of the masses of cement, slag, fly ash, and silica fume. The aggregate mass refers to the sum of the masses of fine aggregate, coarse aggregate, and biochar developed aggregate.) 
1.17. What is the mass ratio of biochar to binder in biochar-integrated construction materials? If this value is not provided directly in the given text, it is calculated by dividing the biochar mass by the binder mass. Provide the answer of a floating number, rounded to four decimal places. Example format: 0.0385. (Note: The binder mass refers to the sum of the masses of cement, slag, fly ash, and silica fume.) 

2. Please identify the properties and characteristics of the cement and biochar utilized in the provided document. Respond to the 5 questions below. If the document does not provide enough information to answer a question, reply with 'nan'.
2.1. What grade of cement is used in this category? (Note: There are generally three grades of cement: 32.5, 42.5, and 52.5.) Please respond with C32.5 if the grade is 32.5. Please respond with C42.5 if the grade is 42.5. Please respond with C52.5 if the grade is 52.5. Example format C42.5.
2.2. What is the particle size range (just from the minimum value to the maximum value) of biochar before it is applied or mixed in the mixture of this category? (Note: Particle size range of biochar: The smallest and largest dimensions of the individual biochar particles. This range is typically reported in millimeters (mm) and reflects the physical size distribution of the biochar material.) Provide the answer in millimeters (mm) of a range of float numbers, rounded to three decimal places. Convert units when mismatched (e.g. from cm to mm: multiply by 10). Example format: 1.180–2.360.
2.3. What is the porosity of biochar used in this document?
(Note: Porosity of biochar: The ratio of the volume of pores (void spaces) within the biochar to the total volume of the biochar, typically expressed as a percentage. Porosity reflects the ability of biochar to retain water, nutrients, and gases.) Provide the answer as a percent (%), rounded to two decimal places. Example format: 67.42%.
2.4. What is the fixed carbon content of biochar used in this document? (Note: Fixed carbon content of biochar: The proportion of carbon that remains in the biochar after volatile substances have been removed during pyrolysis. It is an indicator of the stability and energy content of biochar, typically expressed as a percentage of the total mass.) If a range is provided, provide the answer as an average value. Provide the answer as a percent (%), rounded to two decimal places. Example format: 78.65%.
2.5. What is the carbon (C) content of the biochar used in this document? (Note: Carbon (C) content of biochar: The proportion of elemental carbon present in the biochar, usually determined by elemental analysis. This value reflects the amount of carbon retained in the biochar after pyrolysis and is typically expressed as a percentage of the total mass.) If a range is provided, provide the answer as an average value. Provide the answer as a percent (%), rounded to two decimal places. Example format: 65.23%.

3. Please identify the properties and characteristics of the biochar-integrated construction materials in the provided document. Respond to the 4 questions below. If the document does not provide enough information to answer a question, reply with 'nan'.
3.1. What is the compressive strength of the biochar-integrated construction material after 28 days of curing? The answer should be expressed in megapascals (MPa), rounded to two decimal place. If the original text mentions the standard deviation, delete the standard deviation. Answer format example 1: 52.13. If different curing methods are used, only answer with the value corresponding to the standard curing method. 
3.2. What is the density of the biochar-integrated construction material in the hardened state? The answer should be expressed in kilograms per cubic meter (kg/m^3). Provide answers in integer numerical form. If the original text mentions the standard deviation, delete the standard deviation. Answer format example 1: 2000. 
3.3. What is the workability or flowability (usually tested as a flow table or slump) of the biochar-integrated construction material in the fresh state? Provide the answer as a numerical value expressed in millimeters (mm) in integer numerical form. If the original text mentions the standard deviation, delete the standard deviation. Convert units when mismatched (e.g. from cm to mm: multiply by 10). Answer format example 1: 160.
3.4. What is the thermal conductivity of the biochar-integrated construction material after 28 days of curing? The answer should be expressed in watts per meter-kelvin (W/(m·K)), rounded to four decimal places. If the original text mentions the standard deviation, delete the standard deviation. Answer format example 1: 1.0255. 

Please provide your responses in the following format.
1.1: A floating number of cement mass ratio (question 1.1)
1.2: A floating number of slag mass ratio (question 1.2)
1.3: A floating number of fly ash mass ratio (question 1.3)
1.4: A floating number of silica fume mass ratio (question 1.4)
1.5: A floating number of biochar mass ratio (question 1.5)
1.6: A floating number of fiber mass ratio (question 1.6)
1.7: A floating number of water mass ratio (question 1.7)
1.8: A floating number of fine aggregate mass ratio (question 1.8)
1.9: A floating number of coarse aggregate mass ratio (question 1.9)
1.10: A floating number of biochar developed aggregate mass ratio (question 1.10)
1.11: A floating number of admixtures mass ratio (question 1.11)
1.12: A floating number of other materials mass ratio (question 1.12)
1.13: A floating number of binder mass ratio (question 1.13)
1.14: A floating number of water to binder mass ratio (question 1.14)
1.15: A floating number of supplementary cementitious materials to binder mass ratio (question 1.15)
1.16: A floating number of aggregate to binder mass ratio (question 1.16)
1.17: A floating number of biochar to binder mass ratio (question 1.17)
2.1: A string of cement grade (question 2.1) 
2.2: A floating number range of particle size (question 2.2) 
2.3: A floating number of biochar porosity (question 2.3) 
2.4: A floating number of fixed carbon content of biochar (question 2.4) 
2.5: A floating number of carbon (C) content of biochar (question 2.5) 
3.1: A floating number of compressive strength of the biochar-integrated construction material (question 3.1)
3.2: A floating number of density of the biochar-integrated construction material (question 3.2)
3.3: A floating number of flow table or slump test value of the biochar-integrated construction material (question 3.3)
3.4: A floating number of thermal conductivity of the biochar-integrated construction material (question 3.4)

Document:

Given tables:
$table_and_charts

Given paper:
$all_text
'''

class QuestionPrompt2200:
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
