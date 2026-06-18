/* auth.js — SSD Nursery Authentication
 *
 * Key architecture decisions:
 *  - `api()` and `showToast()` are module-level so every handler can reach them.
 *  - The forgot-password flow is three inline steps:
 *      forgot-email  →  forgot-otp  →  forgot-reset
 *    matching the visual language of the signup/verify/details flow.
 *  - showForm() hides the tab bar for all secondary steps.
 *  - OTP wiring is done per-container so signup and forgot OTPs don't clash.
 */

"use strict";

// VERSION CHECK — open browser console, you should see this line.
// If you don't see it, your browser is still serving the old cached file.
console.log("[auth.js v2] loaded ✓");

// ── CSRF token ────────────────────────────────────────────────────────────────
function getCSRF() {
    return (
        document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
        document.querySelector("meta[name='csrf-token']")?.content ||
        document.cookie.match(/csrftoken=([^;]+)/)?.[1] ||
        ""
    );
}

// ── Toast notification ────────────────────────────────────────────────────────
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
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("show"), 3500);
}

// ── JSON POST helper ──────────────────────────────────────────────────────────
async function api(url, body) {
    const res = await fetch(url, {
        method:      "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken":  getCSRF(),
        },
        body: JSON.stringify(body),
    });
    return res.json();
}

// ── Loading state helper ──────────────────────────────────────────────────────
function setLoading(btn, loading) {
    if (!btn) return;
    btn.disabled = loading;
    const text    = btn.querySelector(".btn-text");
    const spinner = btn.querySelector(".fa-spin");
    if (text)    text.style.opacity = loading ? "0.5" : "1";
    if (spinner) spinner.classList.toggle("hidden", !loading);
}

// ── Tab / step visibility ─────────────────────────────────────────────────────
// Steps that should hide the Login / Create Account tab bar
const HIDE_TABS_FOR = new Set(["verify", "details", "forgot-email", "forgot-otp", "forgot-reset"]);

function showForm(id) {
    document.querySelectorAll(".form-step").forEach(f => f.classList.remove("active"));

    const target = document.getElementById(id);
    if (target) target.classList.add("active");

    const tabs = document.getElementById("auth-tabs");
    if (tabs) tabs.style.display = HIDE_TABS_FOR.has(id) ? "none" : "flex";
}

// ── OTP wiring (reusable for any container) ───────────────────────────────────
function wireOtp(containerSelector) {
    const inputs = document.querySelectorAll(`${containerSelector} .otp-input`);

    inputs.forEach((inp, idx) => {
        inp.addEventListener("input", () => {
            inp.value = inp.value.replace(/\D/g, "").slice(0, 1);
            if (inp.value && idx < inputs.length - 1) inputs[idx + 1].focus();
            inp.classList.toggle("filled", !!inp.value);
        });

        inp.addEventListener("keydown", e => {
            if (e.key === "Backspace" && !inp.value && idx > 0) inputs[idx - 1].focus();
        });

        inp.addEventListener("paste", e => {
            e.preventDefault();
            const digits = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
            [...digits].forEach((ch, i) => {
                if (inputs[i]) {
                    inputs[i].value = ch;
                    inputs[i].classList.add("filled");
                }
            });
            const nextEmpty = inputs[digits.length];
            if (nextEmpty) nextEmpty.focus();
        });
    });

    return {
        getOtp:   () => [...inputs].map(i => i.value).join(""),
        clearOtp: () => {
            inputs.forEach(i => { i.value = ""; i.classList.remove("filled"); });
            if (inputs[0]) inputs[0].focus();
        },
    };
}

// ══════════════════════════════════════════════════════════════════════════════
// INIT — runs after DOM is ready
// ══════════════════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {

    // ── Tab buttons ───────────────────────────────────────────────────────────
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            showForm(btn.dataset.target);
        });
    });

    // Default tab from URL query param (?tab=signup)
    const urlTab = new URLSearchParams(window.location.search).get("tab") || "login";
    showForm(urlTab);
    tabBtns.forEach(b => b.classList.toggle("active", b.dataset.target === urlTab));

    // ── Password visibility toggles ───────────────────────────────────────────
    document.querySelectorAll(".password-toggle").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling;
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            icon.classList.toggle("fa-eye",      !show);
            icon.classList.toggle("fa-eye-slash", show);
        });
    });

    // ── Wire OTP containers ───────────────────────────────────────────────────
    const signupOtp = wireOtp("#signup-otp-container");
    const forgotOtp = wireOtp("#forgot-otp-container");

    // ══════════════════════════════════════════════════════════════════════════
    // LOGIN
    // ══════════════════════════════════════════════════════════════════════════
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
                setTimeout(() => { window.location.href = data.redirect || "/"; }, 800);
            } else {
                showToast(data.message || "Invalid credentials.");
                setLoading(btn, false);
            }
        } catch {
            showToast("Network error. Please try again.");
            setLoading(btn, false);
        }
    });

    // ══════════════════════════════════════════════════════════════════════════
    // SIGNUP
    // ══════════════════════════════════════════════════════════════════════════
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
                const el = document.getElementById("display-email");
                if (el) el.textContent = email;
                signupOtp.clearOtp();
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

    // ══════════════════════════════════════════════════════════════════════════
    // VERIFY OTP (signup)
    // ══════════════════════════════════════════════════════════════════════════
    document.getElementById("verify")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn = document.getElementById("verify-btn");
        const otp = signupOtp.getOtp();

        if (otp.length < 6) return showToast("Please enter the complete 6-digit code.");

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

    // ── Resend OTP (signup) ───────────────────────────────────────────────────
    document.getElementById("resend-link")?.addEventListener("click", async e => {
        e.preventDefault();
        const link = e.currentTarget;
        link.textContent = "Sending…";
        try {
            const data = await api("/resend-otp/", {});
            if (data.success) {
                signupOtp.clearOtp();
                showToast("New code sent successfully!", "success");
            } else {
                showToast(data.message || "Error resending code.");
            }
        } catch {
            showToast("Network error.");
        }
        link.textContent = "Resend";
    });

    // ══════════════════════════════════════════════════════════════════════════
    // DELIVERY DETAILS
    // ══════════════════════════════════════════════════════════════════════════

    // Current location button
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

    function fillLocationFields(data) {
        ["state", "city", "area", "pincode"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = data[id] || "";
        });
    }

    // Pincode auto-fill
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

    // Save details form
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
                setTimeout(() => { window.location.href = "/"; }, 1200);
            } else {
                showToast(data.message || "Something went wrong.");
                setLoading(btn, false);
            }
        } catch {
            showToast("Network error.");
            setLoading(btn, false);
        }
    });

    // ══════════════════════════════════════════════════════════════════════════
    // FORGOT PASSWORD FLOW
    // Three inline steps: forgot-email → forgot-otp → forgot-reset
    // ══════════════════════════════════════════════════════════════════════════

    // Step 1 entry — "Forgot password?" link on the login form
    document.getElementById("go-forgot")?.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const emailInput = document.getElementById("forgot-email-input");
        if (emailInput) emailInput.value = "";
        showForm("forgot-email");
    });

    // Back to login from step 1
    document.getElementById("forgot-back-to-login")?.addEventListener("click", () => {
        showForm("login");
        tabBtns.forEach(b => b.classList.toggle("active", b.dataset.target === "login"));
    });

    // ── Step 1: Send OTP ─────────────────────────────────────────────────────
    document.getElementById("forgot-email")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn   = document.getElementById("forgot-send-btn");
        const email = document.getElementById("forgot-email-input")?.value.trim();

        if (!email) return showToast("Please enter your email address.");

        setLoading(btn, true);
        try {
            const data = await api("/forgot-password/", { email });
            if (data.success) {
                showToast("Verification code sent!", "success");
                const el = document.getElementById("forgot-display-email");
                if (el) el.textContent = email;
                forgotOtp.clearOtp();
                showForm("forgot-otp");
            } else {
                showToast(data.message || "Could not send code.");
            }
            setLoading(btn, false);
        } catch {
            showToast("Network error. Please try again.");
            setLoading(btn, false);
        }
    });

    // ── Step 2: Verify OTP ───────────────────────────────────────────────────
    document.getElementById("forgot-otp")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn = document.getElementById("forgot-verify-btn");
        const otp = forgotOtp.getOtp();

        if (otp.length < 6) return showToast("Please enter the complete 6-digit code.");

        setLoading(btn, true);
        try {
            const data = await api("/verify-reset-otp/", { otp });
            if (data.success) {
                showToast("Code verified!", "success");
                // Clear password fields before showing step 3
                const np = document.getElementById("new-password");
                const cp = document.getElementById("confirm-new-password");
                if (np) np.value = "";
                if (cp) cp.value = "";
                showForm("forgot-reset");
            } else {
                showToast(data.message || "Invalid code.");
            }
            setLoading(btn, false);
        } catch {
            showToast("Network error.");
            setLoading(btn, false);
        }
    });

    // Resend code (forgot flow)
    document.getElementById("forgot-resend-link")?.addEventListener("click", async e => {
        e.preventDefault();
        const link = e.currentTarget;
        // Re-use the email that was already submitted in step 1
        const email = document.getElementById("forgot-email-input")?.value.trim();
        if (!email) return showToast("Please go back and enter your email.");

        link.textContent = "Sending…";
        try {
            const data = await api("/forgot-password/", { email });
            if (data.success) {
                forgotOtp.clearOtp();
                showToast("New code sent!", "success");
            } else {
                showToast(data.message || "Error resending code.");
            }
        } catch {
            showToast("Network error.");
        }
        link.textContent = "Resend";
    });

    // ── Step 3: Set new password ─────────────────────────────────────────────
    document.getElementById("forgot-reset")?.addEventListener("submit", async e => {
        e.preventDefault();
        const btn      = document.getElementById("reset-btn");
        const password = document.getElementById("new-password")?.value;
        const confirm  = document.getElementById("confirm-new-password")?.value;

        if (!password || !confirm) return showToast("Please fill in both password fields.");
        if (password !== confirm)  return showToast("Passwords do not match.");

        // Basic strength check (mirrors backend validation)
        const strong = (
            password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /[a-z]/.test(password) &&
            /\d/.test(password) &&
            /[!@#$%^&*()_+=\-{}\[\]:;'<>,.?/]/.test(password)
        );
        if (!strong)
            return showToast("Password needs 8+ chars, uppercase, lowercase, digit & special character.");

        setLoading(btn, true);
        try {
            const data = await api("/reset-password/", { password });
            if (data.success) {
                showToast("Password reset! Signing you in…", "success");
                setTimeout(() => {
                    showForm("login");
                    tabBtns.forEach(b => b.classList.toggle("active", b.dataset.target === "login"));
                }, 1400);
            } else {
                showToast(data.message || "Reset failed. Please try again.");
                setLoading(btn, false);
            }
        } catch {
            showToast("Network error.");
            setLoading(btn, false);
        }
    });

}); // end DOMContentLoaded