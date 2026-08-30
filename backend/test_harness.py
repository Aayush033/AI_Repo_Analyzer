import asyncio
import sys

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.graph import run_workflow

class TerminalWS:
    async def send_json(self, data: dict):
        if data.get("type") == "log":
            print(f"[GRAPH LOG] {data.get('msg')}")

async def test_my_agents():
    test_url = "https://github.com/pallets/flask" 
    ws = TerminalWS()
    
    print("🧪 Commencing Core Agent Verification Test on https://github.com/pallets/flask...")
    
    try:
        response = await run_workflow("Senior Python Backend Engineer with Flask and Docker", test_url, ws)
        
        print("\n" + "="*50)
        print("📊 FINAL RESULTS MATRIX RECEIVED FROM CORE")
        print("="*50)
        print(f"🏆 TOTAL CALCULATED SCORE: {response['score']}/100")
        print(f"⏱️  TOTAL GRAPH RUNTIME  : {response['runtime']} seconds")
        print("="*50)
        
        print("\n📋 DETAILED AGENT VERIFICATION LEDGER:")
        for idx, result in enumerate(response["results"], 1):
            print(f"\n[{idx}] Agent: {result.get('agent')}")
            print(f"    Status: {result.get('status', '').upper()}")
            print(f"    Output: {result.get('output', '')[:180]}...")
            
    except Exception as e:
        print(f"💥 TEST CRASHED! Error in orchestrator loop: {e}")

if __name__ == "__main__":
    asyncio.run(test_my_agents())