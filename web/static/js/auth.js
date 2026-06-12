/* auth.js — SSD Nursery Authentication */
(function () {
    "use strict";

    // ── CSRF ──────────────────────────────────────────────────
    const CSRF = () =>
        document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
        document.querySelector("meta[name='csrf-token']")?.content ||
        document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

    // ── Toast ─────────────────────────────────────────────────
    function showToast(msg, type = "error") {
        const el   = document.getElementById("custom-toast");
        const icon = document.getElementById("toast-icon");
        const text = document.getElementById("toast-message");
        if (!el) return;
        text.textContent = msg;
        el.className     = `toast-notification ${type}`;
        icon.className   = type === "success"
            ? "fas fa-check-circle"
            : "fas fa-exclamation-circle";
        el.classList.add("show");
        clearTimeout(el._t);
        el._t = setTimeout(() => el.classList.remove("show"), 3500);
    }

    // ── Loading state ─────────────────────────────────────────
    function setLoading(btn, loading) {
        if (!btn) return;
        btn.disabled = loading;
        const text    = btn.querySelector(".btn-text");
        const spinner = btn.querySelector(".fa-spin");
        if (text)    text.style.opacity = loading ? "0.5" : "1";
        if (spinner) spinner.classList.toggle("hidden", !loading);
    }

    // ── API helper ────────────────────────────────────────────
    async function api(url, body) {
        const res = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": CSRF(),
            },
            body: JSON.stringify(body),
        });
        return res.json();
    }

    // ── Tab / form switching ──────────────────────────────────
    function showForm(id) {
        document.querySelectorAll(".form-step").forEach(f => {
            f.classList.remove("active");
        });
        const target = document.getElementById(id);
        if (target) target.classList.add("active");

        const authTabs = document.getElementById("auth-tabs");
        if (authTabs) {
            authTabs.style.display =
                (id === "verify" || id === "details") ? "none" : "flex";
        }
    }

    // Tab button clicks
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            showForm(btn.dataset.target);
        });
    });

    // Default tab from URL param
    const urlTab = new URLSearchParams(window.location.search).get("tab") || "login";
    showForm(urlTab);
    tabBtns.forEach(b => b.classList.toggle("active", b.dataset.target === urlTab));

    // ── Password visibility toggle ────────────────────────────
    document.querySelectorAll(".password-toggle").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling;
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            icon.classList.toggle("fa-eye",       !show);
            icon.classList.toggle("fa-eye-slash",  show);
        });
    });

    // ── OTP inputs (declared early — referenced by signup handler) ──
    const otpInputs = document.querySelectorAll(".otp-input");

    function clearOtp() {
        otpInputs.forEach(inp => { inp.value = ""; inp.classList.remove("filled"); });
        if (otpInputs[0]) otpInputs[0].focus();
    }

    otpInputs.forEach((inp, idx) => {
        inp.addEventListener("input", () => {
            inp.value = inp.value.replace(/\D/g, "").slice(0, 1);
            if (inp.value && idx < otpInputs.length - 1) otpInputs[idx + 1].focus();
            inp.classList.toggle("filled", !!inp.value);
        });

        inp.addEventListener("keydown", e => {
            if (e.key === "Backspace" && !inp.value && idx > 0) otpInputs[idx - 1].focus();
        });

        inp.addEventListener("paste", e => {
            e.preventDefault();
            const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
            [...pasted].forEach((ch, i) => {
                if (otpInputs[i]) { otpInputs[i].value = ch; otpInputs[i].classList.add("filled"); }
            });
            if (otpInputs[pasted.length]) otpInputs[pasted.length].focus();
        });
    });

    // ── LOGIN ─────────────────────────────────────────────────
    document.getElementById("login")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn      = document.getElementById("login-btn");
        const email    = e.target.querySelector("[name=email]").value.trim();
        const password = e.target.querySelector("[name=password]").value;
        if (!email || !password) return showToast("Please fill in all fields.");
        setLoading(btn, true);
        try {
            const data = await api("/login-user/", { email, password });
            if (data.success) {
                showToast("Welcome back!", "success");
                setTimeout(() => window.location.href = data.redirect || "/", 800);
            } else {
                showToast(data.message || "Invalid credentials.");
                setLoading(btn, false);
            }
        } catch {
            showToast("Network error. Please try again.");
            setLoading(btn, false);
        }
    });

    // ── SIGNUP ────────────────────────────────────────────────
    document.getElementById("signup")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn      = document.getElementById("signup-btn");
        const fullname = document.getElementById("reg-fullname")?.value.trim();
        const email    = document.getElementById("signup-email")?.value.trim();
        const phone    = document.getElementById("phone")?.value.trim();
        const password = document.getElementById("reg-pass")?.value;
        const confirm  = document.getElementById("reg-confirm-pass")?.value;

        if (!fullname || !email || !phone || !password || !confirm)
            return showToast("Please fill in all fields.");
        if (password !== confirm)
            return showToast("Passwords do not match.");

        setLoading(btn, true);
        try {
            const data = await api("/send-otp/", { fullname, email, phone, password });
            if (data.success) {
                showToast("OTP sent to " + email, "success");
                const displayEl = document.getElementById("display-email");
                if (displayEl) displayEl.textContent = email;
                clearOtp();
                showForm("verify");
                tabBtns.forEach(b => b.classList.remove("active"));
            } else {
                showToast(data.message || "Something went wrong.");
            }
            setLoading(btn, false);
        } catch {
            showToast("Network error. Please try again.");
            setLoading(btn, false);
        }
    });

    // ── VERIFY OTP ────────────────────────────────────────────
    document.getElementById("verify")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn = document.getElementById("verify-btn");
        const otp = [...otpInputs].map(i => i.value).join("");
        if (otp.length < 6) return showToast("Please enter the complete 6-digit OTP.");
        setLoading(btn, true);
        try {
            const data = await api("/verify-otp/", { otp });
            if (data.success) {
                showToast("Verified! Now add your delivery details.", "success");
                showForm("details");
            } else {
                showToast(data.message || "Invalid OTP.");
            }
            setLoading(btn, false);
        } catch {
            showToast("Network error.");
            setLoading(btn, false);
        }
    });

    // ── RESEND OTP ────────────────────────────────────────────
    document.getElementById("resend-link")?.addEventListener("click", async e => {
        e.preventDefault();
        const link = e.currentTarget;
        link.textContent = "Sending…";
        try {
            const data = await api("/resend-otp/", {});
            if (data.success) {
                clearOtp();
                showToast("New OTP sent successfully!", "success");
            } else {
                showToast(data.message || "Error resending OTP.");
            }
        } catch {
            showToast("Network error.");
        }
        link.textContent = "Resend";
    });

    // ── REVERSE GEOCODE helper ────────────────────────────────
    function fillLocationFields(data) {
        const set = id => { const el = document.getElementById(id); if (el) el.value = data[id] || ""; };
        set("state"); set("city"); set("area"); set("pincode");
    }

    // ── CURRENT LOCATION button ───────────────────────────────
    document.getElementById("current-location-btn")?.addEventListener("click", function () {
        if (!navigator.geolocation) return showToast("Geolocation not supported.");
        const btn = this;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Detecting…';
        navigator.geolocation.getCurrentPosition(
            async pos => {
                try {
                    const res  = await fetch(`/reverse-geocode/?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
                    const data = await res.json();
                    if (data.success) {
                        fillLocationFields(data);
                        showToast("Location detected!", "success");
                        btn.innerHTML = '<i class="fas fa-check"></i> Location Detected';
                    } else {
                        showToast(data.message || "Could not detect location.");
                        btn.innerHTML = '<i class="fas fa-location-arrow"></i> Use Current Location';
                    }
                } catch {
                    showToast("Location lookup failed.");
                    btn.innerHTML = '<i class="fas fa-location-arrow"></i> Use Current Location';
                }
            },
            () => {
                showToast("Location permission denied.");
                btn.innerHTML = '<i class="fas fa-location-arrow"></i> Use Current Location';
            }
        );
    });

    // ── PINCODE auto-fill ─────────────────────────────────────
    let pincodeTimer = null;
    document.getElementById("pincode")?.addEventListener("input", function () {
        clearTimeout(pincodeTimer);
        const val = this.value.replace(/\D/g, "").slice(0, 6);
        this.value = val;
        if (val.length !== 6) return;
        pincodeTimer = setTimeout(async () => {
            const spinner = document.getElementById("pincode-spinner");
            if (spinner) spinner.classList.remove("hidden");
            try {
                const res  = await fetch(`https://api.postalpincode.in/pincode/${val}`);
                const data = await res.json();
                if (data[0]?.Status === "Success") {
                    const po = data[0].PostOffice[0];
                    const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ""; };
                    set("state", po.State);
                    set("city",  po.District);
                    set("area",  po.Name);
                }
            } catch { /* silent — user can fill manually */ }
            if (spinner) spinner.classList.add("hidden");
        }, 600);
    });

    // ── SAVE DETAILS ─────────────────────────────────────────
    document.getElementById("details")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn = document.getElementById("details-btn");
        const get = id => document.getElementById(id)?.value?.trim() || "";
        const payload = {
            address:      get("address"),
            pincode:      get("pincode"),
            area:         get("area"),
            city:         get("city"),
            state:        get("state"),
            instructions: get("instructions"),
        };
        if (!payload.address)
            return showToast("Please enter your address.");
        if (!payload.pincode || payload.pincode.length !== 6)
            return showToast("Please enter a valid 6-digit pincode.");
        setLoading(btn, true);
        try {
            const data = await api("/save-details/", payload);
            if (data.success) {
                showToast("All done! Welcome to SSD Nursery 🌱", "success");
                setTimeout(() => window.location.href = "/", 1200);
            } else {
                showToast(data.message || "Something went wrong.");
                setLoading(btn, false);
            }
        } catch {
            showToast("Network error.");
            setLoading(btn, false);
        }
    });

})();