from fastapi import FastAPI, Request
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fastapi.middleware.cors import CORSMiddleware
import os
import json
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
# إعداد LangChain LLM
# -------------------------
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("spi")
)

# -------------------------
# قالب البرومبت
# -------------------------
prompt_template = """
أنت خبير في مقياس بصمة التفكير المطور بواسطة د. سلطان العتيبي. 

المستخدم حقق هذه المقاييس (من 0 إلى 100):
{metrics_text}

يجب أن تقوم بإرجاع الرد بتنسيق JSON حصراً لتسهيل عملية قراءته برمجياً. 
لا تضف أي نص خارج كائن JSON النهائي ولا تستخدم Markdown blocks (مثل ```json).

هيكل الـ JSON المطلوب بدقة:
{{
    "metrics": {{ "الاستدلال": int, "القياس": int, "النظم": int, "التنفيذ": int, "التأثير": int, "التعاطف": int, "الابتكار": int, "التجريب": int }},
    "dominant_quadrant": {{ "الربع المهيمن": "اسم الربع", "color": "#xxx" }},
    "headline_description": {{ "وصف العنوان": "نص قصير جذاب" }},
    "mind_mechanism": {{ "آلية التفكير": "شرح مفصل" }},
    "key_capabilities": ["ميزة 1", "ميزة 2", "ميزة 3", "ميزة 4"],
    "unique_fingerprint": ["بصمة 1", "بصمة 2", "بصمة 3"],
    "detailed_personality_profile": {{ "الملف الشخصي المفصل": "شرح مفصل وعميق" }},
    "unsuitable_environments": [{{ "name": "بيئة", "reason": "سبب" }}, ...],
    "recommended_careers": [{{ "title": "وظيفة", "description": "سبب" }}, ...],
    "core_strengths": {{ "نقاط القوة الأساسية": ["نقطة 1", "نقطة 2", "نقطة 3"], "quote": "مقولة ملهمة تلخص النمط" }}
}}

- استخدم القيم المعطاة لتحديد الربع المهيمن.
- املأ كل الحقول بناءً على الربع المهيمن وفق نموذج د. سلطان العتيبي.
- لا تذكر اسم "HBDI" أو "هيرمان" في الرد، استخدم "بصمة التفكير".
- جميع النصوص بالعربية الفصحى وبأسلوب احترافي وجذاب.
"""

prompt = ChatPromptTemplate.from_template(prompt_template)

# LangChain LCEL pipeline
chain = prompt | llm

# -------------------------
# Endpoint
# -------------------------
@app.post("/api/generate_hbdi_json")
async def generate_hbdi_json(request: Request):
    try:
        # قراءة البيانات الخام من الطلب بدون Pydantic
        body = await request.json()
        metrics = body.get("metrics", {})
        
        metrics_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
        
        # استدعاء السلسلة
        response = chain.invoke({
            "metrics_text": metrics_text
        })
        
        # استخراج النص وتنظيفه إذا كان يحتوي على ماردكاوان
        output_text = response.content.strip()
        if output_text.startswith("```"):
            # إزالة علامات ```json و ```
            lines = output_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            output_text = "\n".join(lines).strip()
            
        json_data = json.loads(output_text)
        
        return {"hbdi_json": json_data}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e), "hbdi_json": None}