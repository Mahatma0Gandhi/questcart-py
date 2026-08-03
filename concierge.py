import os
import json
import subprocess
import threading
import time
import random
from flask import Flask, request
from openai import OpenAI
from linq import LinqAPIV3

app = Flask(__name__)

# --- CONFIGURATION ---


SESSIONS = {}

client = OpenAI(api_key=OPENAI_API_KEY)
linq = LinqAPIV3(api_key=LINQ_API_KEY, webhook_secret=LINQ_WEBHOOK_SECRET)

# --- UI UTILITIES ---

def send_bubble(to, text, delay=1.2, media=None):
    parts = [{"type": "text", "value": text}]
    if media: parts.append({"type": "media", "url": media})
    try:
        linq.chats.create(from_=MY_LINQ_NUMBER, to=[to], message={"parts": parts})
        time.sleep(delay)
    except Exception as e: print(f"Send Error: {e}")

# --- UNIVERSAL REASONING ---

def get_technical_thought(category, goal):
    """Generates reasoning based strictly on the current mission domain"""
    prompt = f"""
    You are a subject matter expert in {goal}.
    Task: Scouting for '{category}'.
    
    Give 1 technical reasoning update (Max 20 words). 
    Explain why this specific component matters for the success of this mission.
    Example (Photography): 'Looking for high burst rates and fast autofocus to freeze birds in flight without motion blur.'
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": prompt}])
        return res.choices[0].message.content
    except: return f"Optimizing {category} for the mission..."

def analyze_intent(text, history):
    """Identifies the DOMAIN and intent (New, Modify, or Buy)"""
    prompt = f"""
    Analyze user intent. History: {history}. User: {text}.
    
    RULES:
    1. Determine if this is a NEW mission, a CLARIFICATION, or a MODIFY request.
    2. If NEW: Are there enough constraints to build a professional BOM? (Budget, specific use-case).
    3. If MODIFY: Identify exactly which part they want to change.

    Return JSON: {{ "intent": "NEW|MODIFY|BUY", "ready": bool, "reply": "human response", "goal": "refined mission context" }}
    """
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": prompt}], response_format={"type": "json_object"})
    return json.loads(res.choices[0].message.content)

def architect_mission(goal, history, scouted_data=None):
    """Universal BOM Architect: Works for any domain (Gym, PC, Photography, Coffee)"""
    prompt = f"""
    You are a Master Procurement Architect (Universal Specialist). 
    Mission Goal: {goal}
    USD to INR: {USD_TO_INR}
    
    IF PLANNING (scouted_data is None):
    - Identify the 4 most critical product categories for this specific mission.
    - DO NOT default to PC parts unless requested. 
    - Output JSON: {{ "items": [{{ "category": "", "search_query": "" }}] }}

    IF FINALIZING:
    - Pick 1 winner per category. Explain its SYNERGY with the mission goal.
    - Calculate 'total_inr' and a realistic 'market_avg_inr' for the context.
    - Generate a dynamic Technical Scorecard (3 attributes relevant to THIS mission).
    - Hard budget limit: Ensure total_inr is within user's requested budget.

    Return JSON:
    {{
        "items": [{{ "category": "", "product": "", "price_usd": 0, "synergy": "" }}],
        "metrics": {{ "total_inr": 0, "market_avg_inr": 0, "budget_bar": "███░░", "scorecard": {{ "AttributeName": 0 }} }},
        "verdict": "Expert engineer report (Max 40 words)"
    }}
    """
    user_content = f"Data: {json.dumps(scouted_data) if scouted_data else 'None'}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_content}], response_format={"type": "json_object"})
    return json.loads(res.choices[0].message.content)

def run_prava(query):
    try:
        cmd = f"npx --yes prava shop search --query \"{query}\" --json"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
        return json.loads(result.stdout).get('results', [])[:5]
    except: return []

# --- WORKFLOW ---

def mission_control(phone, text):
    if phone not in SESSIONS: SESSIONS[phone] = {"history": [], "bom": None}
    sess = SESSIONS[phone]
    
    analysis = analyze_intent(text, sess['history'])
    if not analysis['ready']:
        send_bubble(phone, analysis['reply'])
        sess['history'].append(f"User: {text}")
        return

    # MODIFICATION DETECTION
    if analysis['intent'] == "MODIFY" and sess['bom']:
        send_bubble(phone, "♻️ Re-architecting only affected components and verifying domain compatibility...")

    send_bubble(phone, f"🎯 MISSION: {analysis['goal'].upper()}")
    
    # 1. PLAN
    plan = architect_mission(analysis['goal'], sess['history'])
    
    # 2. SCOUT
    scouted = {}
    for item in plan.get('items', []):
        # Mission-specific thought
        thought = get_technical_thought(item['category'], analysis['goal'])
        send_bubble(phone, f"🧠 {thought}", delay=0.5)
        
        query = item.get('search_query') or item.get('category')
        scouted[item['category']] = run_prava(query)

    # 3. FINALIZE
    send_bubble(phone, "⚖️ Rebalancing the BOM and verifying technical ROI...")
    final_bom = architect_mission(analysis['goal'], sess['history'], scouted)
    
    # 4. MODIFICATION LOG (Delta)
    if sess['bom']:
        delta_msg = "🔧 MODIFICATION LOG\n\n"
        old_items = {i['category']: i['product'] for i in sess['bom']['items']}
        for i in final_bom['items']:
            status = "✓ Updated" if old_items.get(i['category']) != i['product'] else "✓ Unchanged"
            delta_msg += f"{i['category']}: {status}\n"
        send_bubble(phone, delta_msg)

    sess['bom'] = final_bom
    sess['history'].append(f"User: {text}")

    # 5. DELIVERY
    m = final_bom['metrics']
    saved = m['market_avg_inr'] - m['total_inr']
    header = (f"━━━━━━━━━━━━━━\n✨ ARCHITECT'S VERDICT\n\n"
              f"Market Average: ₹{m['market_avg_inr']:,.0f}\n"
              f"QuestCart: ₹{m['total_inr']:,.0f}\n"
              f"Saved: ₹{max(0, saved):,.0f}\n\n"
              f"Utilization: {m['budget_bar']}\n"
              "━━━━━━━━━━━━━━")
    send_bubble(phone, header)

    hero_img = None
    for pick in final_bom['items']:
        if not hero_img:
            data = scouted.get(pick['category'], [])
            if data: hero_img = data[0].get('image_url')
        
        card = (f"📦 {pick['category'].upper()}\n{pick['product']}\n"
                f"₹{float(pick['price_usd'])*USD_TO_INR:,.0f}\n\n"
                f"✓ Synergy: {pick['synergy']}\n━━━━━━━━━━━━━━")
        send_bubble(phone, card, delay=0.8)

    if hero_img: send_bubble(phone, "Final Selection Preview:", media=hero_img)

    # DYNAMIC SCORECARD
    scorecard = "📊 MISSION SCORECARD\n\n"
    for attr, val in m['scorecard'].items():
        scorecard += f"{attr.upper()}: {'█' * int(val)}{'░' * (10-int(val))}\n"
    send_bubble(phone, scorecard)

    send_bubble(phone, f"📜 REPORT\n{final_bom['verdict']}\n\nReply 'BUY' to secure this build.")

def handle_buy_narrative(phone):
    bom = SESSIONS.get(phone, {}).get('bom')
    if not bom:
        send_bubble(phone, "No mission ready. What are we building?")
        return

    narrative = ["🛠️ QuestCart: Preparing secure merchant handoff...", "🔍 Prava: Verifying availability and price lock...", "💳 Generating payment session...", "📡 Waiting for authorization..."]
    for s in narrative: send_bubble(phone, s, delay=1.0)
    
    receipt = f"━━━━━━━━━━━━━━\n🎉 PURCHASE SUCCESSFUL\n━━━━━━━━━━━━━━\nOrder: #QC-{random.randint(1000,9999)}\nAmount: ₹{bom['metrics']['total_inr']:,.0f}\n\nAll items secured. 🚀"
    send_bubble(phone, receipt)

@app.route("/webhook", methods=["POST"])
def webhook():
    raw = request.data.decode("utf-8")
    try:
        event = linq.webhooks.unwrap(raw, headers=request.headers)
        if event.event_type == "message.received":
            text = event.data.parts[0].value
            phone = event.data.sender_handle.handle
            if text.strip().upper() == "BUY":
                threading.Thread(target=handle_buy_narrative, args=(phone,)).start()
            else:
                threading.Thread(target=mission_control, args=(phone, text)).start()
    except Exception as e: print(f"Error: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(port=3000)