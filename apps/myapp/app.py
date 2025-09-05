from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "Welcome to MyApp!", 200

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/hello")
def hello():
    name = request.args.get("name", "world")
    return jsonify({"message": f"Hello, {name}!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

