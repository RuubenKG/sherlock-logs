const BACKEND_URL = window.BACKEND_URL || "";

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

async function fetchMetrics() {
    try {
        // read the x-served-by header set by da loadbalancer
        const pageResponse = await fetch(window.location.origin, { method: "HEAD"});
        const servedBy = pageResponse.headers.get("X-Served-By") || window.location.hostname;

        setText("webserver-tag", `Served by: ${servedBy}`);

        // /metrics now belongs to Prometheus (text format); the human-facing
        // diagnostic JSON moved to /api/info. This is the only change here.
        const response = await fetch(`${BACKEND_URL}/api/info`);
        const data = await response.json();

        setText("val-hostname", data.hostname);
        setText("val-os-type", data.os_type);
        setText("val-os-release", data.os_release);
        setText("val-os-version", data.os_version.split(" ").slice(0, 4).join(" "));

        setText("val-cpu-cores", data.cpu_cores);
        setText("val-cpu-threads", data.cpu_threads);
        setText("val-cpu-freq", `${data.cpu_freq_mhz} MHz`);
        setText("val-cpu-usage", `${data.cpu_usage_percent}%`);

        setText("val-memory-total", `${data.memory_total_mb} MB`);
        setText("val-memory-used", `${data.memory_used_mb} MB`);
        setText("val-memory-free", `${data.memory_free_mb} MB`);
        setText("val-memory-usage", `${data.memory_used_percent}%`);

        const errorBanner = document.getElementById("error-banner");
        errorBanner.style.display = "none";
    }
    catch (err) {
        const errorBanner = document.getElementById("error-banner");
        errorBanner.textContent = `Failed to fetch metrics: ${err.message}`;

        errorBanner.style.display = "block";
    }
}

document.addEventListener(
  "click", () => {
    const audio = new Audio("Intermission.mp3");
    audio.loop = true;
    audio.play();
  },
  { once: true },
);

    fetchMetrics();
    setInterval(fetchMetrics, 5000);