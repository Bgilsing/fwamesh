// Event announcement: a popup on the first visit plus a slim banner at the top of every page.
// Both disappear on their own once the event ends. To announce a new event, edit EVENT and change its id
// (a new id shows the popup again to people who dismissed the last one). Set EVENT to null to turn it off.
(function () {
  var EVENT = {
    id: "hamfest-2026",
    title: "Meet the Fort Wayne mesh at Hamfest",
    when: "Saturday, November 21 · 9 AM – 5 PM",
    whenShort: "Sat, Nov 21",
    start: "2026-11-21T09:00:00-05:00",
    end: "2026-11-21T17:00:00-05:00",
    event: "2026 Fort Wayne Hamfest & Computer Expo",
    eventUrl: "https://www.fortwaynehamfest.com/",
    venue: "Allen County War Memorial Coliseum – Expo Center",
    address: "4000 Parnell Ave., Fort Wayne, IN 46805",
    booth: "", // e.g. "Booth 42". Shown when set.
  };
  if (!EVENT || Date.now() > Date.parse(EVENT.end)) return;

  var KEY = "fwamesh-announce-dismissed:" + EVENT.id;
  var store = {
    get: function () { try { return localStorage.getItem(KEY); } catch (e) { return null; } },
    set: function () { try { localStorage.setItem(KEY, "1"); } catch (e) { /* private mode */ } },
  };
  var esc = function (t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; };
  var maps = "https://www.google.com/maps/search/?api=1&query=" +
    encodeURIComponent(EVENT.venue + ", " + EVENT.address);

  function icsHref() {
    var z = function (iso) { return new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, ""); };
    var text = function (t) { return t.replace(/[\\,;]/g, "\\$&"); };
    var ics = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FWA Mesh//Events//EN", "BEGIN:VEVENT",
      "UID:" + EVENT.id + "@fwamesh.net", "DTSTAMP:" + z(new Date().toISOString()),
      "DTSTART:" + z(EVENT.start), "DTEND:" + z(EVENT.end),
      "SUMMARY:" + text("FWA Mesh at the " + EVENT.event),
      "LOCATION:" + text(EVENT.venue + ", " + EVENT.address),
      "DESCRIPTION:" + text("Local MeshCore users with mesh nodes on display. Come ask questions and get started. https://fwamesh.net"),
      "URL:" + EVENT.eventUrl, "END:VEVENT", "END:VCALENDAR",
    ].join("\r\n");
    return "data:text/calendar;charset=utf-8," + encodeURIComponent(ics);
  }

  function build() {
    // Slim banner at the very top; it reopens the popup.
    var bar = document.createElement("div");
    bar.className = "event-bar";
    bar.innerHTML = '<div class="wrap"><span class="event-dot" aria-hidden="true"></span>' +
      '<span class="event-bar-text"><strong>See us at the Fort Wayne Hamfest</strong> · ' + esc(EVENT.whenShort) +
      '<span class="event-bar-venue"> · Memorial Coliseum</span></span> <button type="button" class="event-bar-btn">Details</button></div>';
    document.body.insertBefore(bar, document.body.firstChild);

    var dlg = document.createElement("div");
    dlg.className = "event-modal";
    dlg.hidden = true;
    dlg.innerHTML =
      '<div class="event-backdrop" data-close></div>' +
      '<div class="event-card" role="dialog" aria-modal="true" aria-labelledby="event-title" aria-describedby="event-desc">' +
        '<button type="button" class="event-x" aria-label="Close" data-close>×</button>' +
        '<p class="kicker">' + esc(EVENT.when) + "</p>" +
        '<h2 id="event-title">' + esc(EVENT.title) + "</h2>" +
        '<p id="event-desc">Local MeshCore users will be at the <a href="' + EVENT.eventUrl + '">' + esc(EVENT.event) +
          "</a>. Stop by to see a range of mesh nodes up close, ask questions, and get help getting started with " +
          "MeshCore. Whether you're already on the mesh or just curious, come say hi.</p>" +
        '<dl class="event-facts">' +
          "<div><dt>When</dt><dd>" + esc(EVENT.when) + "</dd></div>" +
          "<div><dt>Where</dt><dd>" + esc(EVENT.venue) + "<br>" + esc(EVENT.address) + "</dd></div>" +
          (EVENT.booth ? "<div><dt>Find us</dt><dd>" + esc(EVENT.booth) + "</dd></div>" : "") +
        "</dl>" +
        '<div class="event-actions">' +
          '<a class="btn primary" href="' + maps + '" target="_blank" rel="noopener">Get directions</a>' +
          '<a class="btn ghost" href="' + icsHref() + '" download="fwamesh-hamfest.ics">Add to calendar</a>' +
          '<button type="button" class="btn ghost" data-close>Maybe later</button>' +
        "</div>" +
      "</div>";
    document.body.appendChild(dlg);

    var last = null;
    function open() {
      last = document.activeElement;
      dlg.hidden = false;
      document.documentElement.classList.add("event-open");
      dlg.querySelector(".event-x").focus();
    }
    function close() {
      dlg.hidden = true;
      document.documentElement.classList.remove("event-open");
      store.set();
      if (last && last.focus) last.focus();
    }
    dlg.addEventListener("click", function (e) { if (e.target.closest("[data-close]")) close(); });
    document.addEventListener("keydown", function (e) {
      if (dlg.hidden) return;
      if (e.key === "Escape") close();
      if (e.key === "Tab") { // keep focus inside the dialog
        var f = dlg.querySelectorAll("a, button");
        var first = f[0], end = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); end.focus(); }
        else if (!e.shiftKey && document.activeElement === end) { e.preventDefault(); first.focus(); }
      }
    });
    bar.querySelector(".event-bar-btn").addEventListener("click", open);

    if (!store.get()) setTimeout(open, 800);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
