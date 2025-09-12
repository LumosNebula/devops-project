from flask import Flask, request, jsonify, Response
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

APP_NAME = "myapp"

REQUEST_COUNT = Counter(
    'myapp_http_requests_total',
    'Total HTTP requests',
    ['app', 'method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'myapp_request_latency_seconds',
    'Request latency in seconds',
    ['app', 'endpoint']
)

@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def record_metrics(response):
    try:
        resp_time = time.time() - getattr(request, '_start_time', time.time())
        endpoint = request.path
        method = request.method
        status = response.status_code
        REQUEST_LATENCY.labels(app=APP_NAME, endpoint=endpoint).observe(resp_time)
        REQUEST_COUNT.labels(app=APP_NAME, method=method, endpoint=endpoint, http_status=str(status)).inc()
    except Exception:
        pass
    return response

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

@app.route("/metrics")
def metrics():
    data = generate_latest()
    return Response(data, mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
