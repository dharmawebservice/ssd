document.addEventListener("DOMContentLoaded", () => {

    // ================= NAVBAR SCROLL EFFECT =================
    const navbar = document.getElementById("navbar");
    if (navbar) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 20) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        });
    }

    // ================= MOBILE HAMBURGER MENU =================
    const mobileMenuBtn = document.getElementById("mobile-menu");
    const navLinks = document.getElementById("nav-links");

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener("click", () => {
            navLinks.classList.toggle("active");
            
            // Switch icon between hamburger (bars) and close (times)
            const icon = mobileMenuBtn.querySelector("i");
            if(navLinks.classList.contains("active")){
                icon.classList.remove("fa-bars");
                icon.classList.add("fa-times");
            } else {
                icon.classList.remove("fa-times");
                icon.classList.add("fa-bars");
            }
        });
    }

    // ================= ADD TO CART INTERACTION =================
    const quickAddButtons = document.querySelectorAll(".quick-add");
    const cartCountBadge = document.querySelector(".cart-count");
    let cartItemCount = 0;

    quickAddButtons.forEach(button => {
        button.addEventListener("click", function () {
            // Update Number
            cartItemCount++;
            if (cartCountBadge) {
                cartCountBadge.textContent = cartItemCount;
            }

            // Visual Pop Effect
            this.style.transform = "scale(1.15)";
            this.style.backgroundColor = "#1A3622";
            this.style.color = "#ffffff";

            setTimeout(() => {
                this.style.transform = "";
                this.style.backgroundColor = "";
                this.style.color = "";
            }, 300);

            // Fetch Product Name (for potential backend link)
            const productCard = this.closest(".product-card");
            if (productCard) {
                const productName = productCard.querySelector("h3")?.textContent || "Plant";
                console.log(`${productName} added to cart`);
            }
        });
    });

    // ================= PROFILE DROPDOWN LOGIC =================
    const profileBtn = document.getElementById("profileToggle");
    const profileMenu = document.getElementById("profileMenu");

    if (profileBtn && profileMenu) {
        profileBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            profileMenu.classList.toggle("active");
        });

        // Close dropdown when clicking elsewhere
        document.addEventListener("click", (e) => {
            if (!profileMenu.contains(e.target) && !profileBtn.contains(e.target)) {
                profileMenu.classList.remove("active");
            }
        });
    }

});