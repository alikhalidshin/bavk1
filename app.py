# app_langchain.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
load_dotenv()

# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(title="HBDI Personality JSON API with LangChain")

# السماح بـ CORS لتسهيل التواصل مع الفرونت أند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# مدخل البيانات من المستخدم
# -------------------------
class MetricsInput(BaseModel):
    metrics: Dict[str, int]  # 8 مقاييس

# -------------------------
# نموذج Pydantic للـ JSON النهائي
# -------------------------
class HBDIJson(BaseModel):
    metrics: Dict[str, int]
    dominant_quadrant: Dict[str, str]
    headline_description: Dict[str, str]
    mind_mechanism: Dict[str, str]
    key_capabilities: list
    unique_fingerprint: list
    detailed_personality_profile: Dict[str, str]
    unsuitable_environments: list
    recommended_careers: list
    core_strengths: Dict[str, list]

# -------------------------
# إعداد LangChain LLM
# -------------------------
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("spi")
)

# -------------------------
# إعداد Output Parser
# -------------------------
output_parser = PydanticOutputParser(pydantic_object=HBDIJson)

# -------------------------
# قالب البرومبت
# -------------------------
prompt_template = """
أنت خبير في تحليل الشخصية حسب HBDI. 

المستخدم حقق هذه المقاييس:
{metrics_text}

استخدم هذه التعليمات لتنسيق المخرجات:
{format_instructions}

- استخدم القيم لتحديد dominant_quadrant والربع المهيمن
- املأ كل الحقول الأخرى بناءً على dominant_quadrant
- JSON يجب أن يكون جاهز للعرض مباشرة على صفحة التقرير
- لا تخرج عن الهيكل، لا تكتب نصوص خارج JSON
- جميع النصوص بالعربية الفصحى وبأسلوب احترافي
"""

prompt = ChatPromptTemplate.from_template(prompt_template)

# LangChain LCEL pipeline
chain = prompt | llm | output_parser

# -------------------------
# Endpoint
# -------------------------
@app.post("/api/generate_hbdi_json")
async def generate_hbdi_json(input_data: MetricsInput):
    metrics_text = "\n".join([f"{k}: {v}" for k, v in input_data.metrics.items()])
    try:
        result = chain.invoke({
            "metrics_text": metrics_text,
            "format_instructions": output_parser.get_format_instructions()
        })
        return {"hbdi_json": result.model_dump()}
    except Exception as e:
        return {"error": str(e), "hbdi_json": None}