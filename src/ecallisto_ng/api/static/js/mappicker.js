// Offline map picker (F16): an equirectangular graticule with a draggable
// marker, two-way synced to lat/lon number inputs. No CDN/tiles -> CSP-safe.
(function () {
  "use strict";
  const canvas = document.getElementById("map-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const latIn = document.getElementById("latitude_deg");
  const lonIn = document.getElementById("longitude_deg");
  const W = canvas.width, H = canvas.height;

  function themed(name, fallback) {
    return (
      getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim() || fallback
    );
  }

  const clampLat = (v) => Math.max(-90, Math.min(90, v));
  const clampLon = (v) => Math.max(-180, Math.min(180, v));
  const toX = (lon) => ((lon + 180) / 360) * W;
  const toY = (lat) => ((90 - lat) / 180) * H;
  const toLon = (x) => clampLon((x / W) * 360 - 180);
  const toLat = (y) => clampLat(90 - (y / H) * 180);

  function curLat() { return clampLat(parseFloat(latIn.value) || 0); }
  function curLon() { return clampLon(parseFloat(lonIn.value) || 0); }

  function draw() {
    ctx.fillStyle = themed("--bg-hover", "#1a1d2a");
    ctx.fillRect(0, 0, W, H);
    // graticule every 30 deg
    ctx.strokeStyle = themed("--border", "#333");
    ctx.fillStyle = themed("--fg-muted", "#9aa");
    ctx.font = "10px sans-serif";
    ctx.lineWidth = 1;
    for (let lon = -180; lon <= 180; lon += 30) {
      const x = toX(lon);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let lat = -90; lat <= 90; lat += 30) {
      const y = toY(lat);
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    // equator + prime meridian emphasis
    ctx.strokeStyle = themed("--fg-muted", "#9aa");
    ctx.beginPath(); ctx.moveTo(0, toY(0)); ctx.lineTo(W, toY(0)); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(toX(0), 0); ctx.lineTo(toX(0), H); ctx.stroke();
    // marker
    const mx = toX(curLon()), my = toY(curLat());
    ctx.strokeStyle = themed("--accent", "#7bd");
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(mx, my, 6, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(mx - 10, my); ctx.lineTo(mx + 10, my);
    ctx.moveTo(mx, my - 10); ctx.lineTo(mx, my + 10);
    ctx.stroke();
    ctx.fillStyle = themed("--fg", "#dde");
    ctx.fillText(
      `${curLat().toFixed(2)}, ${curLon().toFixed(2)}`, mx + 9, my - 8
    );
  }

  function setFromEvent(ev) {
    const rect = canvas.getBoundingClientRect();
    const x = ((ev.clientX - rect.left) / rect.width) * W;
    const y = ((ev.clientY - rect.top) / rect.height) * H;
    latIn.value = toLat(y).toFixed(4);
    lonIn.value = toLon(x).toFixed(4);
    draw();
  }

  let dragging = false;
  canvas.addEventListener("mousedown", (e) => { dragging = true; setFromEvent(e); });
  canvas.addEventListener("mousemove", (e) => { if (dragging) setFromEvent(e); });
  window.addEventListener("mouseup", () => { dragging = false; });
  latIn.addEventListener("input", draw);
  lonIn.addEventListener("input", draw);
  draw();
})();
