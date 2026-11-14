/* Contact form on /contact/. The Formspree id lives only on the form action
   in contact/index.html. This file reads form.action and does not repeat it. */
(function (exports) {
  var EXACT = {
    "gmail.com": 1,
    "googlemail.com": 1,
    "outlook.com": 1,
    "hotmail.com": 1,
    "live.com": 1,
    "msn.com": 1,
    "yahoo.com": 1,
    "ymail.com": 1,
    "me.com": 1,
    "icloud.com": 1,
    "mac.com": 1
  };
  /* Regional variants named in the blocklist: yahoo.co.uk, hotmail.co.uk, outlook.*, live.* */
  var REGIONAL = { yahoo: 1, hotmail: 1, outlook: 1, live: 1 };
  var SECOND_LEVEL = { co: 1, com: 1, org: 1, net: 1, ac: 1, gov: 1, edu: 1 };
  var EM = "\u2014";

  function isFreeMailDomain(domain) {
    var d = String(domain || "").trim().toLowerCase().replace(/\.$/, "");
    if (!d || d.indexOf(" ") !== -1 || d.indexOf(".") === -1) return false;
    if (EXACT[d]) return true;
    var keys = Object.keys(EXACT);
    for (var i = 0; i < keys.length; i++) {
      var exact = keys[i];
      if (d.length > exact.length + 1 && d.slice(-(exact.length + 1)) === "." + exact) return true;
    }
    var labels = d.split(".");
    for (var n = 0; n < labels.length - 1; n++) {
      if (!REGIONAL[labels[n]]) continue;
      var rest = labels.slice(n + 1);
      if (rest.length === 1 && /^[a-z]{2,24}$/.test(rest[0])) return true;
      if (rest.length === 2 && SECOND_LEVEL[rest[0]] && /^[a-z]{2}$/.test(rest[1])) return true;
    }
    return false;
  }

  function emailDomain(email) {
    var value = String(email || "").trim();
    var at = value.lastIndexOf("@");
    if (at < 1 || at !== value.indexOf("@")) return "";
    return value.slice(at + 1);
  }

  function isFreeMailAddress(email) {
    return isFreeMailDomain(emailDomain(email));
  }

  function formatSubject(name, email) {
    var cleanName = String(name || "").replace(/[\r\n\t]+/g, " ").replace(/ {2,}/g, " ").trim();
    var cleanEmail = String(email || "").replace(/[\r\n\t ]+/g, "").trim();
    return "BoFu Baby " + EM + " " + cleanName + " " + EM + " " + cleanEmail;
  }

  function show(el, on) {
    if (!el) return;
    el.hidden = !on;
  }

  function attach(doc) {
    var form = doc.getElementById("contact-form");
    if (!form || form.getAttribute("data-bb-ready") === "1") return;
    form.setAttribute("data-bb-ready", "1");
    var email = form.querySelector('[name="email"]');
    var emailErr = doc.getElementById("email-error");
    var formErr = doc.getElementById("form-error");
    var success = doc.getElementById("contact-success");
    var subject = form.querySelector('[name="_subject"]');
    var replyto = form.querySelector('[name="_replyto"]');
    var button = form.querySelector("button[type=submit]");

    function clearEmailError() {
      show(emailErr, false);
      if (email) email.removeAttribute("aria-invalid");
    }
    if (email) email.addEventListener("input", clearEmailError);

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      show(formErr, false);
      clearEmailError();
      if (formErr) formErr.textContent = "";
      var name = (form.querySelector('[name="name"]') || {}).value || "";
      var mail = email ? email.value : "";
      var company = (form.querySelector('[name="company"]') || {}).value || "";
      var message = (form.querySelector('[name="message"]') || {}).value || "";
      if (!String(name).trim() || !String(mail).trim() || !String(company).trim() || !String(message).trim()) {
        if (formErr) formErr.textContent = "Name, work email, company, and a message are required.";
        show(formErr, true);
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(mail).trim())) {
        if (emailErr) emailErr.textContent = "Enter a valid work email.";
        show(emailErr, true);
        if (email) email.setAttribute("aria-invalid", "true");
        return;
      }
      if (isFreeMailAddress(mail)) {
        if (emailErr) emailErr.textContent = "Please use your work email.";
        show(emailErr, true);
        if (email) email.setAttribute("aria-invalid", "true");
        return;
      }
      if (subject) subject.value = formatSubject(name, mail);
      if (replyto) replyto.value = String(mail).trim();
      if (button) button.disabled = true;
      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" }
      }).then(function (res) {
        if (!res.ok) throw new Error("status");
        return res.json().catch(function () { return { ok: true }; });
      }).then(function () {
        form.hidden = true;
        show(success, true);
        if (success && success.focus) success.focus();
        if (typeof window !== "undefined" && typeof window.bbTrack === "function") {
          window.bbTrack("contact_form_submit", form, { step: "success" });
        }
      }).catch(function () {
        if (formErr) formErr.textContent = "We couldn't send that. Try again, or book the Autopsy above.";
        show(formErr, true);
      }).then(function () {
        if (button) button.disabled = false;
      });
    });
  }

  exports.isFreeMailDomain = isFreeMailDomain;
  exports.isFreeMailAddress = isFreeMailAddress;
  exports.formatSubject = formatSubject;
  exports.attach = attach;

  if (typeof document !== "undefined") attach(document);
})(typeof module !== "undefined" && module.exports ? module.exports : (typeof window !== "undefined" ? (window.bbContact = window.bbContact || {}) : {}));
