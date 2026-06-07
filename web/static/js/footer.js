/* ============================================================
   SSD NURSERY — Footer JavaScript  v3
   File: static/js/footer.js
   ============================================================ */

(function () {
  "use strict";

  /* ── Newsletter subscription ─────────────────────────────── */
  const btn      = document.getElementById("footerNewsletterBtn");
  const input    = document.getElementById("footerEmailInput");
  const feedback = document.getElementById("footerNlFeedback");

  if (btn && input) {
    btn.addEventListener("click", handleSubscribe);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") handleSubscribe();
    });
  }

  function setFeedback(msg, type) {
    if (!feedback) return;
    feedback.textContent = msg;
    feedback.className   = "footer-nl-feedback" + (type ? " " + type : "");
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function handleSubscribe() {
    const email = input.value.trim();

    if (!email) {
      setFeedback("Please enter your email address.", "error");
      input.focus();
      return;
    }
    if (!isValidEmail(email)) {
      setFeedback("Please enter a valid email address.", "error");
      input.focus();
      return;
    }

    /* Loading state */
    btn.disabled   = true;
    btn.innerHTML  = '<i class="fas fa-spinner fa-spin"></i>';
    setFeedback("", "");

    /* ── Replace with real API call ──────────────────────────
     *
     * fetch("/newsletter/subscribe/", {
     *   method : "POST",
     *   headers: {
     *     "Content-Type": "application/json",
     *     "X-CSRFToken" : getCsrfToken()
     *   },
     *   body: JSON.stringify({ email })
     * })
     * .then(r => r.json())
     * .then(data => {
     *   if (data.success) { onSuccess(); }
     *   else { onError(data.message || "Something went wrong."); }
     * })
     * .catch(() => onError("Network error. Please try again."));
     *
     * ─────────────────────────────────────────────────────── */

    /* Simulated success (remove this timeout block when using real API) */
    setTimeout(function () {
      onSuccess();
    }, 900);
  }

  function onSuccess() {
    input.value    = "";
    input.disabled = true;
    btn.disabled   = true;
    btn.innerHTML  = '<i class="fas fa-check"></i>';
    setFeedback("🌿 Welcome to the family! Check your inbox.", "success");

    /* Reset after 5 s */
    setTimeout(function () {
      btn.disabled   = false;
      btn.innerHTML  = 'Subscribe <i class="fas fa-arrow-right"></i>';
      input.disabled = false;
      setFeedback("", "");
    }, 5000);

    /* Show site-wide toast if available */
    if (typeof window.showToast === "function") {
      window.showToast("🌿 Subscribed! Welcome to SSD family.");
    }
  }

  function onError(msg) {
    btn.disabled   = false;
    btn.innerHTML  = 'Subscribe <i class="fas fa-arrow-right"></i>';
    setFeedback(msg, "error");
    input.focus();
  }

  /* ── Footer logo → scroll to top ────────────────────────── */
  const footerLogo = document.querySelector(".site-footer .footer-logo");
  if (footerLogo) {
    footerLogo.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ── DWS badge: subtle pulse on hover ───────────────────── */
  const dwsBadge = document.querySelector(".dws-badge");
  if (dwsBadge) {
    dwsBadge.addEventListener("mouseenter", function () {
      const bolt = this.querySelector(".dws-bolt");
      if (bolt) {
        bolt.style.transform = "rotate(15deg) scale(1.15)";
        bolt.style.transition = "transform 0.25s ease";
      }
    });
    dwsBadge.addEventListener("mouseleave", function () {
      const bolt = this.querySelector(".dws-bolt");
      if (bolt) {
        bolt.style.transform = "";
      }
    });
  }

  /* ── Social links: staggered hover ripple ───────────────── */
  document.querySelectorAll(".social-link").forEach(function (link, i) {
    link.style.transitionDelay = (i * 30) + "ms";
  });

  /* ── Animate footer items on scroll into view ───────────── */
  if ("IntersectionObserver" in window) {
    const footerEls = document.querySelectorAll(
      ".footer-brand, .footer-links, .footer-newsletter"
    );
    footerEls.forEach(function (el, i) {
      el.style.opacity   = "0";
      el.style.transform = "translateY(22px)";
      el.style.transition = "opacity 0.55s ease " + (i * 90) + "ms, transform 0.55s ease " + (i * 90) + "ms";
    });

    const obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity   = "1";
          entry.target.style.transform = "translateY(0)";
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    footerEls.forEach(function (el) { obs.observe(el); });
  }

  /* ── Helper: get CSRF token ─────────────────────────────── */
  function getCsrfToken() {
    const match = document.cookie.split(";")
      .map(function (c) { return c.trim(); })
      .find(function (c) { return c.startsWith("csrftoken="); });
    return match ? decodeURIComponent(match.split("=")[1]) : "";
  }

})();