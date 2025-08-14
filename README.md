The goal of this Proof-of-Concept (POC) is to automatically convert natural language questions about application logs into Loki LogQL queries using Codellama:instruct. This reduces manual query writing and allows teams to quickly explore logs.
Flask API: Exposes /ask endpoint for natural language log queries.

 docker exec -it ollama-agent ollama pull codellama:instruct

Codellama:instruct: Generates Loki LogQL queries from user requests.

Loki: Executes the generated LogQL query and returns logs.

ask_ollama(prompt): Sends prompt to Codellama and retrieves the response.

curl -X POST http://localhost:11435/ask \   -H "Content-Type: application/json" \   -d '{"question": "Show latest log from grafana container"}' 
