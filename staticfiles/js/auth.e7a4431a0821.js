document.addEventListener("DOMContentLoaded", () => {
    
    // --- Elements ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const authTabs = document.getElementById('auth-tabs');
    const formLogin = document.getElementById('login');
    const formSignup = document.getElementById('signup');
    const formVerify = document.getElementById('verify');
    const formDetails = document.getElementById('details');
    const displayEmail = document.getElementById('display-email');
    const authLayout = document.getElementById('auth-layout');

    // --- CSRF Helper (Robust Cookie Parser for Django) ---
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.startsWith("csrftoken=")) {
                    cookieValue = cookie.substring("csrftoken=".length, cookie.length);
                    break;
                }
            }
        }
        
        // Fallback to meta tag if cookie isn't available
        if (!cookieValue) {
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) cookieValue = meta.content;
        }
        
        return cookieValue;
    }

    // --- Custom Toast UI ---
    function showToast(message, isSuccess = false) {
        const toast = document.getElementById('custom-toast');
        const icon = document.getElementById('toast-icon');
        const msgSpan = document.getElementById('toast-message');

        msgSpan.textContent = message;
        
        if (isSuccess) {
            toast.classList.add('success');
            icon.className = 'fas fa-check-circle';
        } else {
            toast.classList.remove('success');
            icon.className = 'fas fa-exclamation-circle';
        }

        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 4000);
    }
    
    // --- HTML5 Validation Interceptor ---
    function validateForm(formElement) {
        if (!formElement.checkValidity()) {
            const firstInvalid = formElement.querySelector(':invalid');
            if (firstInvalid) {
                showToast(firstInvalid.validationMessage);
                firstInvalid.focus();
            }
            return false;
        }
        return true;
    }

    // --- Input Restrictions & Sanitization ---

    const signupEmail = document.getElementById("signup-email");
    if(signupEmail) {
        signupEmail.addEventListener("input", function() {
            this.value = this.value.replace(/\s/g, "");
        });
    }

    const phoneInput = document.getElementById("phone");
    if(phoneInput) {
        phoneInput.addEventListener("input", function() {
            this.value = this.value.replace(/\D/g, "").slice(0, 10);
        });
    }

    const pincodeInput = document.getElementById("pincode");
    const pincodeSpinner = document.getElementById('pincode-spinner');
    
    if(pincodeInput) {
        pincodeInput.addEventListener("input", function() {
            this.value = this.value.replace(/\D/g, "").slice(0, 6);
        });
        
        // Pincode Lookup API
        pincodeInput.addEventListener("keyup", async function () {
            const pincode = this.value;
            
            if (pincode.length !== 6) {
                // Clear fields if backspaced/invalid length
                document.getElementById("area").value = "";
                document.getElementById("city").value = "";
                document.getElementById("state").value = "";
                return;
            }

            pincodeSpinner.classList.remove('hidden');

            try {
                const response = await fetch(`/get-location/?pincode=${pincode}`);
                const result = await response.json();
                
                // Debugging Log
                console.log("Pincode API Response:", result);

                if (result.success) {
                    document.getElementById("area").value = result.area || "";
                    document.getElementById("city").value = result.city || "";
                    document.getElementById("state").value = result.state || "";
                    showToast("Location details found!", true);
                } else {
                    showToast("Pincode not found or invalid.");
                }
            } catch (error) {
                console.error(error);
                showToast("Failed to fetch location details.");
            } finally {
                pincodeSpinner.classList.add('hidden');
            }
        });
    }

    const pass = document.getElementById("reg-pass");
    const confirmPass = document.getElementById("reg-confirm-pass");
    if (pass && confirmPass) {
        confirmPass.addEventListener("input", function() {
            if (pass.value !== confirmPass.value) {
                confirmPass.setCustomValidity("Passwords do not match");
            } else {
                confirmPass.setCustomValidity("");
            }
        });
    }

    // --- Password Visibility Toggle ---
    const togglePasswordIcons = document.querySelectorAll('.password-toggle');
    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const inputField = this.previousElementSibling;
            if (inputField.type === 'password') {
                inputField.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else {
                inputField.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });
    
    // --- Step Navigation Logic ---
    function navigateTo(targetForm) {
        [formLogin, formSignup, formVerify, formDetails].forEach(form => {
            form.className = 'form-step exit-right';
        });

        if (targetForm === 'login') {
            authLayout.className = 'auth-layout scroll-locked'; 
            formLogin.className = 'form-step active';
            authTabs.classList.remove('hidden'); 
            updateTabUI('login');
        } 
        else if (targetForm === 'signup') {
            authLayout.className = 'auth-layout scroll-enabled'; 
            formLogin.className = 'form-step exit-left'; 
            formSignup.className = 'form-step active';
            authTabs.classList.remove('hidden'); 
            updateTabUI('signup');
        }
        else if (targetForm === 'verify') {
            authLayout.className = 'auth-layout scroll-locked';
            formLogin.className = 'form-step exit-left';
            formSignup.className = 'form-step exit-left';
            formVerify.className = 'form-step active';
            authTabs.classList.add('hidden'); 
        }
        else if (targetForm === 'details') {
            authLayout.className = 'auth-layout scroll-enabled';
            formLogin.className = 'form-step exit-left';
            formSignup.className = 'form-step exit-left';
            formVerify.className = 'form-step exit-left';
            formDetails.className = 'form-step active';
            authTabs.classList.add('hidden');
        }
    }

    function updateTabUI(targetId) {
        tabBtns.forEach(btn => {
            if (btn.dataset.target === targetId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            navigateTo(e.target.dataset.target);
        });
    });

    // --- Geolocation (Current Location) Logic ---
    const currentLocationBtn = document.getElementById("current-location-btn");
    if(currentLocationBtn){
        currentLocationBtn.addEventListener("click", getCurrentLocation);
    }

    function getCurrentLocation() {
        if (!navigator.geolocation) {
            showToast("Geolocation not supported by your browser");
            return;
        }

        showToast("Fetching your location...", true);

        navigator.geolocation.getCurrentPosition(
            async function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                try {
                    const response = await fetch(`/reverse-geocode/?lat=${lat}&lon=${lon}`);
                    const result = await response.json();

                        if (result.success) {
                                                if(result.pincode){

                            document.getElementById("pincode").value =
                                result.pincode;

                        }else{

                            showToast(
                                "Location found. Please enter pincode manually."
                            );
                        }
                        document.getElementById("state").value = result.state || "";
                        document.getElementById("city").value = result.city || "";
                        document.getElementById("area").value = result.area || "";
                        document.getElementById("address").value = result.address || "";

                        showToast("Location detected successfully", true);
                    } else {
                        showToast(result.message);
                    }
                } catch(error) {
                    console.error(error);
                    showToast("Unable to fetch location details");
                }
            },
            function(error) {
                showToast("Location permission denied");
            }
        );
    }

    // --- API Requests ---
    
    // 1. SIGNUP
    formSignup.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateForm(formSignup)) return;

        const password = document.getElementById("reg-pass").value;
        const confirmPassword = document.getElementById("reg-confirm-pass").value;

        if (password !== confirmPassword) {
            showToast("Passwords do not match.");
            return;
        }

        const btn = document.getElementById('signup-btn');
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.fa-spinner');
        
        btnText.textContent = "Sending Code...";
        spinner.classList.remove('hidden');
        btn.disabled = true;

        try {
            const response = await fetch("/send-otp/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    fullname: document.querySelector('#signup [name="fullname"]').value,
                    email: document.getElementById("signup-email").value,
                    phone: document.querySelector('#signup [name="phone"]').value,
                    password: password
                })
            });

            const result = await response.json();

            if (result.success) {
                displayEmail.textContent = document.getElementById("signup-email").value;
                showToast("OTP sent to your email.", true);
                navigateTo("verify");
            } else {
                showToast(result.message || "Signup failed. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            showToast("Network error. Please try again.");
        } finally {
            btnText.textContent = "Create Account";
            spinner.classList.add('hidden');
            btn.disabled = false;
        }
    });

    // 2. VERIFY OTP
    formVerify.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateForm(formVerify)) return;

        let otp = "";
        document.querySelectorAll(".otp-input").forEach(input => { otp += input.value; });

        if (otp.length < 6) {
            showToast("Please enter the complete 6-digit OTP.");
            return;
        }

        const btn = document.getElementById('verify-btn');
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.fa-spinner');
        
        btnText.textContent = "Verifying...";
        spinner.classList.remove('hidden');
        btn.disabled = true;

        try {
            const response = await fetch("/verify-otp/", {
                method: "POST",
                headers: {
                    "Content-Type":"application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    email: document.getElementById("signup-email").value,
                    otp: otp
                })
            });

            const result = await response.json();

            if(result.success){
                showToast("Email Verified!", true);
                navigateTo("details");
            } else {
                showToast(result.message || "Invalid OTP.");
            }
        } catch (error) {
            console.error("Error:", error);
            showToast("Network error during verification.");
        } finally {
            btnText.textContent = "Verify & Proceed";
            spinner.classList.add('hidden');
            btn.disabled = false;
        }
    });

    // 3. RESEND OTP
    const resendLink = document.getElementById("resend-link");
    if (resendLink) {
        resendLink.addEventListener("click", async function(e) {
            e.preventDefault();
            try {
                const response = await fetch("/resend-otp/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: document.getElementById("signup-email").value
                    })
                });
                const result = await response.json();
                showToast(result.message, result.success);
            } catch (error) {
                console.error(error);
                showToast("Failed to resend OTP. Please try again.");
            }
        });
    }

    // 4. SUBMIT DETAILS
    formDetails.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateForm(formDetails)) return;

        const btn = document.getElementById('details-btn');
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.fa-spinner');
        
        btnText.textContent = "Saving...";
        spinner.classList.remove('hidden');
        btn.disabled = true;

        try {
            const response = await fetch("/save-details/", {
                method: "POST",
                headers: {
                    "Content-Type":"application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    email: document.getElementById("signup-email").value,
                    pincode: document.getElementById("pincode").value,
                    state: document.getElementById("state").value,
                    city: document.getElementById("city").value,
                    area: document.getElementById("area").value,
                    address: document.getElementById("address").value,
                    instructions: document.getElementById("instructions").value
                })
            });

            const result = await response.json();

            if(result.success){
                showToast("Welcome to SSD Nursery!", true);
                setTimeout(() => { window.location.href = result.redirect || "/"; }, 1000);
            } else {
                showToast(result.message || "Failed to save details.");
            }
        } catch (error) {
            console.error("Error:", error);
            showToast("Network error. Please try again.");
        } finally {
            btnText.textContent = "Save Details & Finish";
            spinner.classList.add('hidden');
            btn.disabled = false;
        }
    });

    // 5. LOGIN REQUEST
    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateForm(formLogin)) return;

        const btn = document.getElementById('login-btn');
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.fa-spinner');
        
        btnText.textContent = "Authenticating...";
        spinner.classList.remove('hidden');
        btn.disabled = true;

        try {
            const response = await fetch("/login-user/", {
                method: "POST",
                headers: {
                    "Content-Type":"application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({
                    email: document.querySelector('#login input[name="email"]').value,
                    password: document.querySelector('#login input[name="password"]').value
                })
            });

            const result = await response.json();

            if(result.success){
                showToast("Login Successful!", true);
                setTimeout(() => { window.location.href = result.redirect || "/"; }, 1000);
            } else {
                showToast(result.message || "Invalid credentials.");
            }
        } catch (error) {
            console.error("Login Error:", error);
            showToast("Error connecting to server.");
        } finally {
            btnText.textContent = "Sign In";
            spinner.classList.add('hidden');
            btn.disabled = false;
        }
    });

    // --- OTP Input Auto-Advance Logic ---
    const otpInputs = document.querySelectorAll('.otp-input');
    
    otpInputs.forEach((input, index) => {
        input.addEventListener("keypress", function(e){
            if(!/[0-9]/.test(e.key)){
                e.preventDefault();
            }
        });

        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
        
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pastedData = e.clipboardData.getData('text').slice(0, 6).replace(/[^0-9]/g, '');
            for(let i = 0; i < pastedData.length; i++) {
                if(i < otpInputs.length) {
                    otpInputs[i].value = pastedData[i];
                    if(i < otpInputs.length - 1) otpInputs[i+1].focus();
                }
            }
        });
    });

    // --- Init: Check URL for pre-selected tab ---
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tab') === 'signup' || window.location.hash === '#signup') {
        navigateTo('signup');
    } else {
        navigateTo('login');
    }
});