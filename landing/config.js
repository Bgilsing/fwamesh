// Site-wide settings for the landing pages. Edit these at go-live; no rebuild needed.
window.FWAMESH = {
  // Where the CoreScope analyzer lives.
  analyzerUrl: "https://map.fwamesh.net",
  // MQTT broker observers should publish to.
  mqttHost: "mqtt.fwamesh.net",
  mqttPort: 1883,
  iata: "FWA",
};

document.addEventListener("DOMContentLoaded", function () {
  var c = window.FWAMESH;
  document.querySelectorAll("[data-analyzer]").forEach(function (a) {
    a.href = c.analyzerUrl + (a.getAttribute("data-analyzer") || "");
  });
  document.querySelectorAll("[data-mqtt-host]").forEach(function (e) { e.textContent = c.mqttHost; });
  document.querySelectorAll("[data-mqtt-port]").forEach(function (e) { e.textContent = c.mqttPort; });
  document.querySelectorAll("[data-iata]").forEach(function (e) { e.textContent = c.iata; });
});
