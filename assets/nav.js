(function () {
  var nav = document.querySelector("nav.site");
  if (!nav) return;
  var btn = nav.querySelector(".navtoggle");
  var menu = nav.querySelector("#site-menu");
  if (!btn || !menu) return;
  var mq = window.matchMedia("(max-width: 900px)");

  function mobile() {
    return mq.matches;
  }

  function setMenu(open) {
    nav.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  function closeMenu(focusBtn) {
    if (btn.getAttribute("aria-expanded") !== "true") return;
    setMenu(false);
    if (focusBtn) btn.focus();
  }

  function visibleLinks() {
    var list = [];
    menu.querySelectorAll("a[href]").forEach(function (a) {
      if (a.getClientRects().length) list.push(a);
    });
    return list;
  }

  btn.addEventListener("click", function () {
    var willOpen = btn.getAttribute("aria-expanded") !== "true";
    setMenu(willOpen);
    if (willOpen) {
      var first = visibleLinks()[0];
      if (first) first.focus();
    }
  });

  document.addEventListener("click", function (e) {
    if (nav.classList.contains("is-open") && !nav.contains(e.target)) closeMenu(false);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Tab" && mobile() && nav.classList.contains("is-open")) {
      var items = [btn].concat(visibleLinks());
      var i = items.indexOf(document.activeElement);
      if (i === -1) return;
      if (e.shiftKey && i === 0) {
        e.preventDefault();
        items[items.length - 1].focus();
      } else if (!e.shiftKey && i === items.length - 1) {
        e.preventDefault();
        items[0].focus();
      }
    }
  });

  menu.addEventListener("click", function (e) {
    var target = e.target;
    var link = target && target.closest ? target.closest("a") : null;
    if (link && mobile()) closeMenu(false);
  });

  function onMq() {
    if (!mobile()) setMenu(false);
  }
  if (mq.addEventListener) mq.addEventListener("change", onMq);
  else if (mq.addListener) mq.addListener(onMq);

  nav.querySelectorAll(".navdrop").forEach(function (drop) {
    var trigger = drop.querySelector(".navdrop-trigger");
    var timer;
    var hoverOpen = false;

    function setDrop(open) {
      drop.setAttribute("data-open", open ? "true" : "false");
      if (trigger) trigger.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function open() {
      clearTimeout(timer);
      if (mobile() || drop.getAttribute("data-suppress") === "true") return;
      nav.querySelectorAll(".navdrop").forEach(function (other) {
        if (other !== drop) {
          other.setAttribute("data-open", "false");
          var otherTrigger = other.querySelector(".navdrop-trigger");
          if (otherTrigger) otherTrigger.setAttribute("aria-expanded", "false");
        }
      });
      setDrop(true);
    }

    function scheduleClose() {
      clearTimeout(timer);
      timer = setTimeout(function () { setDrop(false); }, 120);
    }

    function closeNow(focusTrigger) {
      clearTimeout(timer);
      drop.setAttribute("data-suppress", "true");
      setDrop(false);
      if (focusTrigger && trigger) trigger.focus();
      setTimeout(function () { drop.removeAttribute("data-suppress"); }, 0);
    }

    drop.addEventListener("pointerenter", function (e) {
      if (e.pointerType === "touch" || mobile()) return;
      hoverOpen = true;
      open();
    });
    drop.addEventListener("pointerleave", function (e) {
      if (e.pointerType === "touch" || mobile()) return;
      hoverOpen = false;
      scheduleClose();
    });
    drop.addEventListener("focusin", open);
    drop.addEventListener("focusout", function (e) {
      if (mobile()) return;
      if (!drop.contains(e.relatedTarget)) scheduleClose();
    });
    if (trigger) {
      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        if (mobile()) return;
        if (e.detail === 0) {
          open();
          var first = drop.querySelector(".navdrop-menu a");
          if (first) first.focus();
          return;
        }
        if (hoverOpen) return;
        setDrop(drop.getAttribute("data-open") !== "true");
      });
    }
    drop.addEventListener("keydown", function (e) {
      if (e.key !== "Escape" || mobile()) return;
      e.preventDefault();
      e.stopPropagation();
      closeNow(true);
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" || !mobile() || !nav.classList.contains("is-open")) return;
    e.preventDefault();
    closeMenu(true);
  });

  document.addEventListener("click", function (e) {
    if (mobile()) return;
    nav.querySelectorAll('.navdrop[data-open="true"]').forEach(function (drop) {
      if (!drop.contains(e.target)) {
        drop.setAttribute("data-open", "false");
        var trigger = drop.querySelector(".navdrop-trigger");
        if (trigger) trigger.setAttribute("aria-expanded", "false");
      }
    });
  });
})();
