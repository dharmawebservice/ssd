(function () {
    "use strict";

    const CSRF = () => document.querySelector("[name=csrfmiddlewaretoken]")?.value
                     || document.querySelector("meta[name='csrf-token']")?.content || "";

    // ── Toast ─────────────────────────────────────────────────
    function showToast(msg, type = "error") {
        const el   = document.getElementById("custom-toast");
        const icon = document.getElementById("toast-icon");
        const text = document.getElementById("toast-message");
        if (!el) return;
        text.textContent = msg;
        el.className = `toast-notification ${type}`;
        icon.className = type === "success" ? "fas fa-check-circle" : "fas fa-exclamation-circle";
        el.classList.add("show");
        clearTimeout(el._t);
        el._t = setTimeout(() => el.classList.remove("show"), 3500);
    }

    // ── Set loading state on button ───────────────────────────
    function setLoading(btn, loading) {
        const text    = btn.querySelector(".btn-text");
        const spinner = btn.querySelector(".fa-spin");
        btn.disabled  = loading;
        if (text)    text.style.opacity    = loading ? "0.5" : "1";
        if (spinner) spinner.classList.toggle("hidden", !loading);
    }

    // ── Tab switching ─────────────────────────────────────────
    function showForm(id) {

    document.querySelectorAll(".form-step").forEach(form => {
        form.classList.remove("active");
    });

    const target = document.getElementById(id);

    if (target) {
        target.classList.add("active");
    }

    const authTabs = document.getElementById("auth-tabs");

    if (authTabs) {

        if (id === "verify" || id === "details") {
            authTabs.style.display = "none";
        } else {
            authTabs.style.display = "flex";
        }

    }
}

    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            showForm(btn.dataset.target);
        });
    });

    // ── Default tab from URL ──────────────────────────────────
    const urlTab = new URLSearchParams(window.location.search).get("tab") || "login";
    showForm(urlTab);
    tabBtns.forEach(b => b.classList.toggle("active", b.dataset.target === urlTab));

    // ── Password toggle ───────────────────────────────────────
    document.querySelectorAll(".password-toggle").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling;
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            icon.classList.toggle("fa-eye", !show);
            icon.classList.toggle("fa-eye-slash", show);
        });
    });

    // ── LOGIN ─────────────────────────────────────────────────
    const loginForm = document.getElementById("login");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn  = document.getElementById("login-btn");
            const email    = loginForm.querySelector("[name=email]").value.trim();
            const password = loginForm.querySelector("[name=password]").value;
            if (!email || !password) return showToast("Please fill in all fields.");
            setLoading(btn, true);
            try {
                const res  = await fetch("/login-user/", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF() }, body: JSON.stringify({ email, password }) });
                const data = await res.json();
                if (data.success) { showToast("Welcome back!", "success"); setTimeout(() => window.location.href = data.redirect || "/", 800); }
                else { showToast(data.message || "Invalid credentials."); setLoading(btn, false); }
            } catch { showToast("Network error. Please try again."); setLoading(btn, false); }
        });
    }

    // ── SIGNUP ────────────────────────────────────────────────
    const signupForm = document.getElementById("signup");
    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn      = document.getElementById("signup-btn");
            const fullname = document.getElementById("reg-fullname")?.value.trim();
            const email    = document.getElementById("signup-email")?.value.trim();
            const phone    = document.getElementById("phone")?.value.trim();
            const password = document.getElementById("reg-pass")?.value;
            const confirm  = document.getElementById("reg-confirm-pass")?.value;
            if (!fullname || !email || !phone || !password || !confirm) return showToast("Please fill in all fields.");
            if (password !== confirm) return showToast("Passwords do not match.");
            setLoading(btn, true);
            try {
                const res  = await fetch("/send-otp/", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF() }, body: JSON.stringify({ fullname, email, phone, password }) });
                const data = await res.json();
                if (data.success) {
                    showToast("OTP sent to " + email, "success");
                    const displayEl = document.getElementById("display-email");
                    if (displayEl) displayEl.textContent = email;
                    // clear old otp boxes

otpInputs.forEach(input => {
    input.value = "";
    input.classList.remove("filled");
});

showForm("verify");

otpInputs[0].focus();
                    tabBtns.forEach(b => b.classList.remove("active"));
                    const authTabs = document.getElementById("auth-tabs");
                    if (authTabs) {
                        authTabs.style.display = "none";
                    }
                } else { showToast(data.message || "Something went wrong."); }
                setLoading(btn, false);
            } catch { showToast("Network error. Please try again."); setLoading(btn, false); }
        });
    }

    // ── OTP inputs ────────────────────────────────────────────
    const otpInputs = document.querySelectorAll(".otp-input");
    otpInputs.forEach((inp, idx) => {
        inp.addEventListener("input", () => {
            inp.value = inp.value.replace(/\D/g, "").slice(0, 1);
            if (inp.value && idx < otpInputs.length - 1) otpInputs[idx + 1].focus();
            inp.classList.toggle("filled", !!inp.value);
        });
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Backspace" && !inp.value && idx > 0) otpInputs[idx - 1].focus();
        });
        inp.addEventListener("paste", (e) => {
            e.preventDefault();
            const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
            [...pasted].forEach((ch, i) => { if (otpInputs[i]) { otpInputs[i].value = ch; otpInputs[i].classList.add("filled"); } });
            if (otpInputs[pasted.length]) otpInputs[pasted.length].focus();
        });
    });

    // ── VERIFY OTP ────────────────────────────────────────────
    const verifyForm = document.getElementById("verify");
    if (verifyForm) {
        verifyForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("verify-btn");
            const otp = [...otpInputs].map(i => i.value).join("");
            if (otp.length < 6) return showToast("Please enter the complete 6-digit OTP.");
            setLoading(btn, true);
            try {
                const res  = await fetch("/verify-otp/", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF() }, body: JSON.stringify({ otp }) });
                const data = await res.json();
                if (data.success) {

    showToast(
        "Verified! Now add your delivery details.",
        "success"
    );

    showForm("details");
}
                else { showToast(data.message || "Invalid OTP."); }
                setLoading(btn, false);
            } catch { showToast("Network error."); setLoading(btn, false); }
        });
    }

    // ── RESEND OTP ────────────────────────────────────────────
    const resendLink = document.getElementById("resend-link");
    if (resendLink) {
        resendLink.addEventListener("click", async (e) => {
            e.preventDefault();
            resendLink.textContent = "Sending…";
            try {
                const res  = await fetch("/resend-otp/", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF() } });
                const data = await res.json();

if (data.success) {

    otpInputs.forEach(input => {
        input.value = "";
        input.classList.remove("filled");
    });

    otpInputs[0].focus();

    showToast(
        "New OTP sent successfully!",
        "success"
    );

} else {

    showToast(
        data.message || "Error"
    );

}
                showToast(data.success ? "OTP resent!" : (data.message || "Error"), data.success ? "success" : "error");
            } catch { showToast("Network error."); }
            resendLink.textContent = "Resend";
        });
    }

    // ── LOCATION & PINCODE ────────────────────────────────────
    async function fillAddress(lat, lon) {
        try {
            const res  = await fetch(`/reverse-geocode/?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            if (data.success) {
                const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
                set("state", data.state);
                set("city", data.city);
                set("area", data.area);
                set("pincode", data.pincode);
                showToast("Location detected!", "success");
            } else showToast(data.message || "Could not detect location.");
        } catch { showToast("Location lookup failed."); }
    }

    const locBtn = document.getElementById("current-location-btn");
    if (locBtn) {
        locBtn.addEventListener("click", () => {
            if (!navigator.geolocation) return showToast("Geolocation not supported.");
            locBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Detecting…';
            navigator.geolocation.getCurrentPosition(
                async pos => { await fillAddress(pos.coords.latitude, pos.coords.longitude); locBtn.innerHTML = '<i class="fas fa-check"></i> Location Detected'; },
                () => { showToast("Location permission denied."); locBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Use Current Location'; }
            );
        });
    }

    const pincodeInput = document.getElementById("pincode");
    if (pincodeInput) {
        let pincodeTimer = null;
        pincodeInput.addEventListener("input", () => {
            clearTimeout(pincodeTimer);
            const val = pincodeInput.value.replace(/\D/g, "").slice(0, 6);
            pincodeInput.value = val;
            if (val.length === 6) {
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
                            set("city", po.District);
                            set("area", po.Name);
                        }
                    } catch {}
                    if (spinner) spinner.classList.add("hidden");
                }, 600);
            }
        });
    }

    // ── SAVE DETAILS ─────────────────────────────────────────
    const detailsForm = document.getElementById("details");
    if (detailsForm) {
        detailsForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn    = document.getElementById("details-btn");
            const get    = id => document.getElementById(id)?.value?.trim() || "";
            const payload = {
                address:      get("address"),
                pincode:      get("pincode"),
                area:         get("area"),
                city:         get("city"),
                state:        get("state"),
                instructions: get("instructions"),
            };
            if (!payload.address) return showToast("Please enter your address.");
            if (!payload.pincode || payload.pincode.length !== 6) return showToast("Please enter a valid 6-digit pincode.");
            setLoading(btn, true);
            try {
                const res  = await fetch("/save-details/", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF() }, body: JSON.stringify(payload) });
                const data = await res.json();
                if (data.success) { showToast("All done! Welcome to SSD Nursery 🌱", "success"); setTimeout(() => window.location.href = "/", 1200); }
                else { showToast(data.message || "Something went wrong."); }
                setLoading(btn, false);
            } catch { showToast("Network error."); setLoading(btn, false); }
        });
    }

})();