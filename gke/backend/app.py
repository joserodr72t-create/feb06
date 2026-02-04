from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

from crypto_tools import get_crypto_price, get_top_cryptos, search_crypto

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

tools = [get_crypto_price, get_top_cryptos, search_crypto]

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are a helpful crypto assistant that provides real-time cryptocurrency market data. Use the available tools to fetch accurate price information. When users ask about a coin, use get_crypto_price with the coin ID (e.g., 'bitcoin', 'ethereum'). If unsure about the ID, use search_crypto first.",

)

# Apply recursion_limit when invoking the agent:
RECURSION_LIMIT = 2 * 3 + 1  # Equivalent to 3 iterations

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    @app.route("/ask", methods=['POST'])
    def talkToGemini():
        try:
            user_input = request.json['input']
            print(f"Received: {user_input}")
            
            result = agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                {"recursion_limit": RECURSION_LIMIT}
            )
    
            
            last_message = result["messages"][-1]
            
            # Handle different content formats (Gemini returns list)
            if isinstance(last_message.content, list):
                response_content = ""
                for block in last_message.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_content += block.get("text", "")
                    elif isinstance(block, str):
                        response_content += block
            else:
                response_content = last_message.content
            
            print(f"Response: {response_content}")
            return response_content
        except Exception as e:
            print(f"Error: {e}")
            return str(e), 500
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=80)
