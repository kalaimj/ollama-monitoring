from flask import Flask, request, jsonify
import requests
import os
import traceback
import re
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama-agent:11434")
MODEL = "codellama:instruct"

def ask_ollama(prompt):
    try:
        logging.debug("Sending prompt to Ollama...")
        res = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=60)
        res.raise_for_status()
        data = res.json()
        logging.debug(f"Ollama raw response: {data}")
        return data.get("response", "").strip()
    except Exception as e:
        logging.error("Error calling Ollama:", exc_info=True)
        return None

def extract_logql(text):
    """
    Extract the first valid-looking LogQL expression from the model output.
    """
    match = re.search(r'(\{.*\}.*|\(.*\).*)', text, re.DOTALL)
    if match:
        query = match.group(1).strip()
        logging.debug(f"Extracted Loki query: {query}")
        return query
    return ""

def query_loki(loki_query):
    try:
        params = {"query": loki_query, "limit": 20}
        logging.debug(f"Querying Loki: {loki_query}")
        res = requests.get(f"{LOKI_URL}/loki/api/v1/query", params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        logging.debug(f"Loki raw response: {data}")
        return data
    except Exception as e:
        logging.error("Error calling Loki:", exc_info=True)
        return None

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        question = data.get("question")
        if not question:
            return jsonify({"error": "Missing 'question'"}), 400

        logging.debug(f"Received question: {question}")

        # Strict instruction to Codellama
        prompt = f"""
You are a Loki LogQL query generator.
Given a request, output ONLY a single valid Loki LogQL query.
Do NOT write explanations, SQL, text, or markdown formatting.
Output only the raw query, starting with '{{' or '('.

Request: {question}
Query:
"""
        raw_output = ask_ollama(prompt)
        loki_query = extract_logql(raw_output)

        if not loki_query:
            logging.warning("Codellama output invalid, using fallback query")
            loki_query = '{container="loki"} |= "ERROR"'

        loki_result = query_loki(loki_query)
        if loki_result is None:
            return jsonify({"error": "Failed to query Loki"}), 500

        return jsonify({
            "question": question,
            "generated_query": loki_query,
            "logs": loki_result
        })

    except Exception as e:
        logging.error("Unexpected error:", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Enable unbuffered output in Python
    os.environ["PYTHONUNBUFFERED"] = "1"
    app.run(host="0.0.0.0", port=11435)
