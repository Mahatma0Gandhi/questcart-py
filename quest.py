import os
import json
import subprocess
from flask import Flask, request, jsonify
from openai import OpenAI
from linq import LinqAPIV3

app = Flask(__name__)

# --- CONFIGURATION (Reads from Environment Variables) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINQ_API_KEY = os.getenv("LINQ_API_KEY")
LINQ_WEBHOOK_SECRET = os.getenv("LINQ_WEBHOOK_SECRET")
MY_LINQ_NUMBER = os.getenv("MY_LINQ_NUMBER")
USD_TO_INR = 84

client = OpenAI(api_key=OPENAI_API_KEY)
linq = LinqAPIV3(api_key=LINQ_API_KEY)

# --- 1. REMOTE PRAVA MANAGEMENT ---

@app.route("/setup")
def remote_setup():
    """Visit this URL once to start the linking process on the server"""
    try:
        # We use process.env['PRAVA_STATE_DIR'] which is set in render.yaml
        cmd = "prava setup --name QuestRemote --platform custom"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        # This will return a URL for you to click and approve
        return f"<h3>Prava Remote Setup</h3><pre>{result.stdout}</pre><p>Copy the URL above to approve.</p>"
    except Exception as e:
        return str(e)

@app.route("/status")
def remote_status():
    """Check if the server is successfully linked to Prava"""
    try:
        result = subprocess.run("prava status", capture_output=True, text=True, shell=True)
        return f"<h3>Prava Server Status</h3><pre>{result.stdout}</pre>"
    except Exception as e:
        return str(e)

# --- 2. THE COMMERCE ENGINE (Original Logic) ---

def get_procurement_plan(goal):
    """OpenAI Stage: Planning"""
    system_prompt = """
    You are a technical procurement planner. Break the user goal into a list of required components.
    Return ONLY a JSON object with a key "items". 
    Example: {"items": [{"category": "CPU", "search_query": "AMD Ryzen 5 7600"}]}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": goal}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def run_prava_search(query):
    """Prava CLI Stage: Scouting"""
    try:
        # Running the global 'prava' command installed via render.yaml
        cmd = f"prava shop search --query \"{query}\" --json"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0: 
            print(f"CLI Error: {result.stderr}")
            return []
        return json.loads(result.stdout).get('results', [])
    except Exception as e:
        print(f"Search Execution Failed: {e}")
        return []

def refine_with_ai(original_goal, search_results):
    """OpenAI Stage: Architectural Refinement"""
    refiner_prompt = f"""
    You are a Professional Procurement Architect.
    Original Goal: {original_goal}
    Total Budget: Assume 1 Lakh INR (Approx $1,200 USD). 
    Conversion: 1 USD = {USD_TO_INR} INR.

    You will receive a JSON of live search results for various categories.
    Your job:
    1. Select the SINGLE BEST option for each category.
    2. Ensure the TOTAL cost stays within the budget.
    3. Ensure parts are compatible.

    Return ONLY a JSON object:
    {{
        "total_inr": 0,
        "selections": [
            {{ "category": "", "product": "", "price_usd": "", "merchant": "", "reason": "" }}
        ],
        "summary": "Explanation"
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": refiner_prompt},
            {"role": "user", "content": json.dumps(search_results)}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 3. THE WEBHOOK HANDLER (Messaging Layer) ---

@app.route("/webhook", methods=["POST"])
def linq_webhook():
    raw_body = request.data.decode("utf-8")
    headers = request.headers
    
    try:
        # Verify the signature and unwrap the Linq event
        event = linq.webhooks.unwrap(raw_body, headers=headers)
        
        if event.event_type == "message.received":
            user_msg = event.data.parts[0].get('value')
            user_phone = event.data.sender_handle.handle
            
            # Send immediate feedback to user
            linq.chats.create(
                from_=MY_LINQ_NUMBER, 
                to=[user_phone],
                message={"parts": [{"type": "text", "value": f"🚀 Mission: '{user_msg}'\nScouting live markets..."}]}
            )

            # --- EXECUTE PLAN-SCOUT-REFINE LOOP ---
            
            # A. Plan
            plan = get_procurement_plan(user_msg)
            items = plan.get("items", [])
            
            # B. Scout (Prava CLI)
            all_category_data = {}
            for item in items:
                cat = item['category']
                query = item['search_query']
                all_category_data[cat] = run_prava_search(query)[:5] # Top 5 results

            # C. Refine
            final_build = refine_with_ai(user_msg, all_category_data)

            # --- D. FORMAT RICH RESPONSE ---
            
            report = f"✨ ARCHITECTED BUILD COMPLETE ✨\n\n💰 Total: ₹{final_build.get('total_inr', 0):,.0f}\n\n"
            hero_image = None
            
            for pick in final_build.get('selections', []):
                # Build the item description line
                item_desc = f"📦 {pick['category'].upper()}\n🔹 {pick['product']}\n💰 ${pick['price_usd']} ({pick['merchant']})\n\n"
                report += item_desc
                
                # Pick the first available image as the hero image
                if not hero_image:
                    cat_res = all_category_data.get(pick['category'], [])
                    if cat_res: hero_image = cat_res[0].get('image_url')

            report += f"📝 Strategy: {final_build.get('summary')}"

            # Assemble multipart message for RCS
            reply_parts = [{"type": "text", "value": report}]
            if hero_image:
                reply_parts.append({"type": "media", "url": hero_image})

            # Send final response
            linq.chats.create(
                from_=MY_LINQ_NUMBER,
                to=[user_phone],
                message={"parts": reply_parts}
            )

    except Exception as e:
        print(f"Webhook Error: {e}")
        # We still return 200 to Linq to avoid excessive retries on logic failure
        return "Internal Processing Error", 200

    return "OK", 200

if __name__ == "__main__":
    # Local fallback
    app.run(port=3000)