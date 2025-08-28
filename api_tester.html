<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Triad Learning API Tester</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Arial; margin: 2rem; }
      button { margin: 0.25rem 0.5rem 1rem 0; padding: 0.6rem 1rem; }
      pre { background: #f5f5f5; padding: 1rem; border-radius: 6px; }
      input { width: 320px; padding: 0.5rem; }
    </style>
  </head>
  <body>
    <h1>Triad Learning API Tester</h1>
    <p>Status: <span id="status">checking...</span></p>

    <h3>Try a KNN prediction</h3>
    <p>Features (comma-separated): <br/>
      <input id="knnFeatures" value="5.1, 3.5, 1.4, 0.2"/>
    </p>
    <button onclick="predict('knn')">Predict (KNN)</button>

    <h3>Try a Random Forest prediction</h3>
    <p>Features (comma-separated): <br/>
      <input id="forestFeatures" value="6.2, 2.8, 4.8, 1.8"/>
    </p>
    <button onclick="predict('forest')">Predict (Forest)</button>

    <h3>Response</h3>
    <pre id="out"></pre>

    <script>
      const base = "http://127.0.0.1:8000";
      async function check() {
        try {
          const r = await fetch(base + "/");
          const j = await r.json();
          document.getElementById('status').textContent = j.ok ? "Online" : "Unexpected";
        } catch {
          document.getElementById('status').textContent = "Offline (start_api.py not running)";
        }
      }
      function parseFeatures(id) {
        const raw = document.getElementById(id).value;
        const arr = raw.split(",").map(s => parseFloat(s.trim())).filter(x => !isNaN(x));
        return arr;
      }
      async function predict(which) {
        const inputId = which === "knn" ? "knnFeatures" : "forestFeatures";
        const features = parseFeatures(inputId);
        const out = document.getElementById('out');
        out.textContent = "Sending...";
        try {
          const r = await fetch(base + "/predict/" + which, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ features })
          });
          const j = await r.json();
          out.textContent = JSON.stringify(j, null, 2);
        } catch (e) {
          out.textContent = "Error: " + e;
        }
      }
      check();
    </script>
  </body>
</html>
