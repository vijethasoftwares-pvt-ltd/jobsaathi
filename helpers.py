from langchain.llms import OpenAI
from langchain import PromptTemplate, LLMChain
from db import resume_details_collection
import os
import json
OPENAIKEY=os.environ['OPENAIKEY']
llm = OpenAI(openai_api_key=OPENAIKEY,  max_tokens=-1)

template = """You are a chatbot who helps people to build their resume/portfolio. This is the HTML of the portfolio {html}. Analyze the HTML properly.The following statement "{statement}" would be an instruction or information related to skills, achievements, education, projects or any other section in the resume. Analyze the statement and update the HTML code according to statement. You are free to add or remove a section as per the scenario. Make the portfolio attractive in styling. Return me only the HTML Code.
"""

skills_analyze_template = """You are a chatbot who helps people to build their resume/portfolio. This is the HTML of the portfolio {html}. Analyze the HTML properly and find all the skills of the person from the resume and return me the data in the following format.
JSON(
"skills" : list of all the skills from the resume.
)
"""
prompt = PromptTemplate(template=template, input_variables=["html", "statement"])
llm_chain = LLMChain(prompt=prompt, llm=llm)

skills_analyze_prompt = PromptTemplate(template=skills_analyze_template, input_variables=["html"])
skills_analyze_llm_chain = LLMChain(prompt=skills_analyze_prompt, llm=llm)

def query_update_billbot(user_id, statement):
    resume_html = get_resume_html_db(user_id)
    html_code = llm_chain.run({"html": str(resume_html), "statement": statement}) 
    return html_code

def get_resume_html_db(user_id):
    if resume_data := resume_details_collection.find_one({"user_id": user_id}):
        resume_html = resume_data.get("resume_html")
        return str(resume_html)
    else:
        return ""

def add_html_to_db(user_id, html_code):
    resume_details_collection.update_one({"user_id": user_id},{"$set": {"resume_html": html_code}})

def analyze_resume(user_id):
    if resume_details := resume_details_collection.find_one({"user_id": user_id},{"_id": 0}):
        resume_html = resume_details.get("resume_html")
        skills = skills_analyze_llm_chain.run(resume_html) 
        skills = skills.strip()
        skills_list = json.loads(skills)
        resume_details_collection.update_one({"user_id": user_id},{"$set": skills_list})
        return skills_list
    else:
        []



resume_question_template = """I have asked a person whether he/she has a portfolio/resume or not.{statement} is the person's reponse. Analyse the statement and return me 'yes' if he has a resume and 'no' if he doesn't have one and if the response is something weird like not a clear cut yes or no return me 'weird'
"""

resume_question_prompt = PromptTemplate(template=resume_question_template, input_variables=["statement"])
resume_question_llm_chain = LLMChain(prompt=resume_question_prompt, llm=llm)


def query__billbot(statement):
    resp = resume_question_llm_chain.run(statement) 
    return str(resp).strip().lower()