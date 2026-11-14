"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const contact = require("../assets/contact.js");

const EM = "\u2014";

test("blocks the named free-mail domains and their subdomains", function () {
  const blocked = [
    "a@gmail.com",
    "a@GoogleMail.com",
    "a@mail.gmail.com",
    "a@googlemail.com",
    "a@outlook.com",
    "a@hotmail.com",
    "a@live.com",
    "a@msn.com",
    "a@yahoo.com",
    "a@ymail.com",
    "a@me.com",
    "a@icloud.com",
    "a@mac.com",
    "a@foo.icloud.com"
  ];
  blocked.forEach(function (email) {
    assert.equal(contact.isFreeMailAddress(email), true, email);
  });
});

test("blocks regional yahoo, hotmail, outlook, and live domains", function () {
  const blocked = [
    "a@yahoo.co.uk",
    "a@yahoo.fr",
    "a@yahoo.com.au",
    "a@yahoo.com.mx",
    "a@mail.yahoo.co.uk",
    "a@hotmail.co.uk",
    "a@hotmail.fr",
    "a@hotmail.co.jp",
    "a@outlook.de",
    "a@outlook.co.uk",
    "a@outlook.com.au",
    "a@live.co.uk",
    "a@live.com.au",
    "a@live.fr"
  ];
  blocked.forEach(function (email) {
    assert.equal(contact.isFreeMailAddress(email), true, email);
  });
});

test("allows work domains and lookalikes that are not the free-mail brand", function () {
  const allowed = [
    "ada@bofubaby.com",
    "ada@acme.co.uk",
    "ada@notyahoo.com",
    "ada@yahoo.example.com",
    "ada@live.bofubaby.com",
    "ada@gmail.co.uk",
    "ada@msn.co.uk",
    "ada@company.com"
  ];
  allowed.forEach(function (email) {
    assert.equal(contact.isFreeMailAddress(email), false, email);
  });
});

test("subject uses em dashes and the BoFu Baby prefix", function () {
  const subject = contact.formatSubject("Ada Lovelace", "Ada@Analytical.example");
  assert.equal(subject, "BoFu Baby " + EM + " Ada Lovelace " + EM + " Ada@Analytical.example");
  assert.equal(subject.includes("-"), false);
  assert.equal(subject.includes("\u2013"), false);
});

test("subject strips line breaks so it stays one line", function () {
  const subject = contact.formatSubject("Ada\nLovelace", "ada@acme.com\r");
  assert.equal(subject, "BoFu Baby " + EM + " Ada Lovelace " + EM + " ada@acme.com");
  assert.equal(/[\r\n]/.test(subject), false);
});

test("the Formspree id is only the form action placeholder", function () {
  const root = path.join(__dirname, "..");
  const html = fs.readFileSync(path.join(root, "contact/index.html"), "utf8");
  const js = fs.readFileSync(path.join(root, "assets/contact.js"), "utf8");
  const hits = html.match(/FORMSPREE_FORM_ID/g) || [];
  assert.equal(hits.length, 1);
  assert.match(html, /action="https:\/\/formspree\.io\/f\/FORMSPREE_FORM_ID"/);
  assert.equal(js.includes("FORMSPREE_FORM_ID"), false);
  assert.match(html, /name="_gotcha"/);
  assert.match(html, /name="_subject"/);
  assert.match(html, /name="_replyto"/);
  assert.match(html, /data-track-on="success"/);
});
