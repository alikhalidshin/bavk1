from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# -------------------------
# إعدادات OpenAI
# -------------------------
API_KEY = os.getenv("spi")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# -------------------------
# قالب البرومبت
# -------------------------
PROMPT_TEMPLATE = """
أنت خبير في مقياس بصمة التفكير المطور بواسطة د. سلطان العتيبي. يقيس هذا المقياس تفضيلات التفكير (وليس القدرات). يمكن أن تكون للمستخدم أكثر من سمة/وجه مرتفع في الوقت نفسه.

مخرجات الأوجه (للتفسير):
استدلال=حُجّة/حكم منطقي | قياس=مؤشر/اتجاه | نظم=إطار/نظام | تنفيذ=إنجاز/تسليم | ابتكار=فكرة/بديل | تجريب=تعلم مُثبت | تأثير=التزام/اتفاق | تعاطف=طمأنة/اتزان نفسي

المستخدم حقق هذه المقاييس (من 0 إلى 100):
{metrics_text}

يجب أن تقوم بإرجاع الرد بتنسيق JSON حصراً لتسهيل عملية قراءته برمجياً. 
لا تضف أي نص خارج كائن JSON النهائي ولا تستخدم Markdown blocks (مثل ```json).

هيكل الـ JSON المطلوب بدقة:
{{
    "metrics": {{ "الاستدلال": int, "القياس": int, "النظم": int, "التنفيذ": int, "التأثير": int, "التعاطف": int, "الابتكار": int, "التجريب": int }},
    "dominant_quadrant": {{ "الربع المهيمن": "اسم الربع", "color": "#xxx" }},
    "headline_description": {{ "وصف العنوان": "نص قصير جذاب" }},
    "mind_mechanism": {{ "آلية التفكير": "شرح موجز لا يتعدى سطر واحد" }},
    "key_capabilities": ["ميزة 1", "ميزة 2", "ميزة 3"],
    "unique_fingerprint": ["بصمة 1", "بصمة 2"],
    "detailed_personality_profile": {{ "الملف الشخصي المفصل": "شرح موجز لا يتعدى سطرين" }},
    "unsuitable_environments": [{{"name": "بيئة", "reason": "سبب مختصر"}}],
    "recommended_careers": [{{"title": "وظيفة", "description": "سبب مختصر"}}],
    "core_strengths": {{ "نقاط القوة الأساسية": ["نقطة 1", "نقطة 2"], "quote": "مقولة قصيرة ملهمة" }}
}}

- استخدم القيم المعطاة لتحديد الربع المهيمن.
- املأ كل الحقول بناءً على الربع المهيمن وفق نموذج د. سلطان العتيبي بأسلوب موجز وسريع.
- لا تذكر اسم "HBDI" أو "هيرمان" في الرد، استخدم "بصمة التفكير".
- جميع النصوص بالعربية الفصحى وبأسلوب احترافي وجذاب.
"""

@app.route("/api/generate_hbdi_json", methods=["POST", "OPTIONS"])
def generate_hbdi_json():
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
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
            "temperature": 0.7,
            "max_tokens": 800,
            "stream": True # Enable streaming
        }
        
        def generate():
            # Send streaming POST request to OpenAI
            response = requests.post(OPENAI_URL, headers=headers, json=payload, stream=True, timeout=60)
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            # Parse out the delta text (token)
                            data_json = json.loads(data_str)
                            delta = data_json["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            pass
                            
        # Return the generator string as an SSE/raw stream
        return app.response_class(generate(), mimetype='text/plain')
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e), "hbdi_json": None}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))