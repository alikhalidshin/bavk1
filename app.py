from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # السماح بـ CORS لجميع النطاقات

# -------------------------
# إعدادات OpenAI
# -------------------------
API_KEY = os.getenv("spi")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# -------------------------
# قالب البرومبت
# -------------------------
PROMPT_TEMPLATE = """
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

@app.route("/api/generate_hbdi_json", methods=["POST"])
def generate_hbdi_json():
    try:
        # قراءة البيانات الخام من الطلب
        body = request.get_json()
        metrics = body.get("metrics", {})
        metrics_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])
        
        # تجهيز البرومبت النهائي
        final_prompt = PROMPT_TEMPLATE.format(metrics_text=metrics_text)
        
        # استدعاء OpenAI مباشرة عبر requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a personality analysis expert."},
                {"role": "user", "content": final_prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=30)
        response_data = response.json()
        
        if "choices" not in response_data:
            return jsonify({"error": "OpenAI API Error", "details": response_data}), 500
            
        output_text = response_data["choices"][0]["message"]["content"].strip()
        
        # تنظيف النص من علامات الـ Markdown إذا وُجدت
        if output_text.startswith("```"):
            lines = output_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            output_text = "\n".join(lines).strip()
            
        json_data = json.loads(output_text)
        
        return jsonify({"hbdi_json": json_data})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e), "hbdi_json": None}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))