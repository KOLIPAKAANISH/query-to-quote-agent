from flask import Flask, render_template, request, jsonify
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Build the agent graph once at startup
from agent.nodes import build_graph
agent_graph = build_graph()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    inquiry = data.get("inquiry", "")

    if not inquiry.strip():
        return jsonify({"status": "error", "message": "No inquiry provided"}), 400

    try:
        # Run the LangGraph agent
        result = agent_graph.invoke({
            "raw_inquiry": inquiry,
            "intent": None,
            "lead_quality": None,
            "quality_reason": None,
            "retrieved_rates": None,
            "supplier_request": None,
            "client_ack": None,
        })

        # Serialize for JSON response
        intent_data = result["intent"].model_dump() if result["intent"] else None

        return jsonify({
            "status": "ok",
            "steps": {
                "extract": intent_data,
                "classify": {
                    "quality": result["lead_quality"],
                    "reason": result["quality_reason"],
                },
                "retrieve": result["retrieved_rates"] or [],
                "draft": {
                    "supplier_request": result["supplier_request"],
                    "client_ack": result["client_ack"],
                },
            },
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
