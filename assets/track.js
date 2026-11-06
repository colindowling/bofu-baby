/* bofubaby.com GA4 + conversion tracking. Pattern copied from rncld.com/assets/track.js.
   SINGLE PLACEHOLDER: set GA_ID to the real G- ID. While it is the placeholder,
   gtag is never loaded and no hit is sent (events only log to console with ?debug_track=1).
   Events: cta_click, book_call_click, book_call_scheduled, autopsy_request,
   contact_form_submit, outbound_email_click, outbound_phone_click.
   Key events (mark in GA4 Admin): book_call_scheduled, contact_form_submit, autopsy_request, book_call_click. */
(function () {
  var GA_ID = "G-XXXXXXXXXX"; // <-- the only value to change
  var LIVE = /^G-[A-Z0-9]{6,}$/.test(GA_ID) && GA_ID !== "G-XXXXXXXXXX";
  var CAL_CSS = "https://assets.calendly.com/assets/external/widget.css";
  var CAL_JS = "https://assets.calendly.com/assets/external/widget.js";
  var UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid", "li_fat_id"];
  var STORE = "bb_attr";
  var pending = null;

  /* ---- first-touch attribution (session) ---- */
  function readAttr() {
    try { return JSON.parse(sessionStorage.getItem(STORE) || "null"); } catch (e) { return null; }
  }
  var qs = new URLSearchParams(window.location.search);
  var attrib = readAttr();
  if (!attrib) {
    attrib = { landing_page: location.pathname, referrer: document.referrer || "(direct)" };
    UTM_KEYS.forEach(function (k) { if (qs.get(k)) attrib[k] = qs.get(k); });
    try { sessionStorage.setItem(STORE, JSON.stringify(attrib)); } catch (e) {}
  }
  var isTest = /^test/i.test(attrib.utm_source || qs.get("utm_source") || "");

  /* ---- gtag (only with a real ID) ---- */
  window.dataLayer = window.dataLayer || [];
  if (LIVE) {
    window.gtag = function () { window.dataLayer.push(arguments); };
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
    document.head.appendChild(s);
    window.gtag("js", new Date());
    var cfg = { page_template: document.body.getAttribute("data-page-template") || "" };
    if (isTest) { cfg.debug_mode = true; cfg.traffic_type = "internal_test"; }
    window.gtag("config", GA_ID, cfg);
  }

  function attr(el, n) { return (el && el.getAttribute && el.getAttribute(n)) || ""; }
  function payload(el) {
    var b = document.body;
    var p = {
      page_location: location.href,
      page_template: attr(el, "data-page-template") || attr(b, "data-page-template"),
      offer: attr(el, "data-offer") || attr(b, "data-offer") || "bofu_autopsy",
      cta_position: attr(el, "data-cta-position") || attr(el, "data-cta"),
      cta_id: attr(el, "data-cta-id"),
      landing_page: attrib.landing_page,
      first_utm_source: attrib.utm_source || "",
      first_utm_campaign: attrib.utm_campaign || ""
    };
    if (isTest) { p.debug_mode = true; p.test_hit = "TEST"; }
    return p;
  }
  function track(name, el, extra) {
    var p = payload(el); for (var k in (extra || {})) p[k] = extra[k];
    if (/debug_track=1/.test(location.search)) console.log("[bb-track]", name, p, LIVE ? "" : "(not sent: placeholder ID)");
    if (LIVE && typeof window.gtag === "function") window.gtag("event", name, p);
  }
  window.bbTrack = track;

  /* ---- UTM passthrough into Calendly (links + inline widgets) ---- */
  function withAttr(url) {
    try {
      var u = new URL(url, location.href);
      // visitor's own UTMs win over hard-coded page UTMs; page UTMs kept if visitor has none
      UTM_KEYS.forEach(function (k) { if (attrib[k] && k.indexOf("utm_") === 0) u.searchParams.set(k, attrib[k]); });
      // Calendly maps salesforce_uuid / utm_* only; landing page goes in a1 (custom answer slot) via utm_term fallback
      if (!u.searchParams.get("utm_term")) u.searchParams.set("utm_term", (attrib.landing_page || "/").slice(0, 100));
      return u.toString();
    } catch (e) { return url; }
  }
  function rewrite() {
    document.querySelectorAll('a[href*="calendly.com"]').forEach(function (a) { a.href = withAttr(a.href); });
    document.querySelectorAll(".calendly-inline-widget[data-url]").forEach(function (w) {
      w.setAttribute("data-url", withAttr(w.getAttribute("data-url")));
    });
  }
  // inline widget script is async; rewrite synchronously at defer time (before widget.js usually initialises)
  rewrite();

  function loadCal(done, fail) {
    if (window.Calendly && window.Calendly.initPopupWidget) return done();
    if (!document.querySelector('link[href="' + CAL_CSS + '"]')) {
      var l = document.createElement("link"); l.rel = "stylesheet"; l.href = CAL_CSS; document.head.appendChild(l);
    }
    var sc = document.createElement("script"); sc.src = CAL_JS; sc.async = true;
    sc.onload = done; sc.onerror = fail; document.head.appendChild(sc);
  }
  function openCal(a) {
    var url = a.href;
    loadCal(function () {
      if (window.Calendly && window.Calendly.initPopupWidget) window.Calendly.initPopupWidget({ url: url });
      else location.href = url;
    }, function () { location.href = url; });
  }

  /* ---- clicks ---- */
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a[href], button[data-track]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var kind = attr(a, "data-track");
    if (href.indexOf("mailto:") === 0) return track("outbound_email_click", a);
    if (href.indexOf("tel:") === 0) return track("outbound_phone_click", a);
    if (href.indexOf("calendly.com") !== -1) {
      track("cta_click", a);
      if (kind === "autopsy") { track("autopsy_request", a, { step: "start" }); pending = { kind: "autopsy", el: a }; }
      else { track("book_call_click", a); pending = { kind: "book_call", el: a }; }
      if (a.target !== "_blank") { ev.preventDefault(); openCal(a); }
      return;
    }
    // internal CTAs to the offer/contact pages
    if (kind || /^\/(15minutes5xtraffic|contact)\//.test(href)) track("cta_click", a, { cta_target: href.split("?")[0] });
  }, true);

  /* ---- Calendly booked (popup + inline widget) ---- */
  window.addEventListener("message", function (ev) {
    var d = ev.data;
    if (!d || d.event !== "calendly.event_scheduled") return;
    if (ev.origin && ev.origin.indexOf("calendly.com") === -1) return;
    var el = pending ? pending.el : (document.querySelector(".calendly-inline-widget") || document.body);
    if (pending && pending.kind === "autopsy") track("autopsy_request", el, { step: "scheduled" });
    track("book_call_scheduled", el);
    pending = null;
  });

  /* ---- forms (none live today; ready for when one ships) ---- */
  document.addEventListener("submit", function (ev) {
    var f = ev.target; if (!f || f.tagName !== "FORM") return;
    // stamp hidden attribution fields so the brief gets them
    ["landing_page", "referrer"].concat(UTM_KEYS).forEach(function (k) {
      if (!attrib[k]) return;
      var i = f.querySelector('input[name="' + k + '"]');
      if (!i) { i = document.createElement("input"); i.type = "hidden"; i.name = k; f.appendChild(i); }
      i.value = attrib[k];
    });
    track(attr(f, "data-track") === "autopsy" ? "autopsy_request" : "contact_form_submit", f, { step: "submit" });
  }, true);
})();
