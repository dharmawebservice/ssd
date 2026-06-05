document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // 1. NAVBAR SCROLL
    // ============================================================
    const navbar = document.getElementById("navbar");
    const offerStrip = document.querySelector(".offer-strip");

    if (navbar) {
        const onScroll = () => {
            navbar.classList.toggle("scrolled", window.scrollY > 10);
        };
        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();
    }

    // ============================================================
    // 2. MOBILE MENU
    // ============================================================
    const mobileMenuBtn = document.getElementById("mobile-menu");
    const navLinks = document.getElementById("nav-links");

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener("click", () => {
            navLinks.classList.toggle("active");
            const icon = mobileMenuBtn.querySelector("i");
            icon.classList.toggle("fa-bars");
            icon.classList.toggle("fa-times");
        });
        navLinks.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                navLinks.classList.remove("active");
                const icon = mobileMenuBtn.querySelector("i");
                icon.classList.add("fa-bars");
                icon.classList.remove("fa-times");
            });
        });
    }

    // ============================================================
    // 3. SEARCH OVERLAY
    // ============================================================
    const searchTrigger = document.getElementById("searchTriggerBtn");
    const searchOverlay = document.getElementById("searchOverlay");
    const searchClose = document.getElementById("searchClose");
    const searchInput = document.getElementById("searchInput");

    if (searchTrigger && searchOverlay) {
        searchTrigger.addEventListener("click", () => {
            searchOverlay.classList.add("active");
            setTimeout(() => searchInput?.focus(), 300);
        });
        searchClose?.addEventListener("click", () => searchOverlay.classList.remove("active"));
        searchOverlay.addEventListener("click", e => {
            if (e.target === searchOverlay) searchOverlay.classList.remove("active");
        });
        document.addEventListener("keydown", e => {
            if (e.key === "Escape") searchOverlay.classList.remove("active");
        });
    }

    // ============================================================
    // 4. HERO SLIDER
    // ============================================================
    const sliderTrack = document.getElementById("sliderTrack");
    const dots = document.querySelectorAll(".dot");
    const sliderPrev = document.getElementById("sliderPrev");
    const sliderNext = document.getElementById("sliderNext");
    const slides = document.querySelectorAll(".slide");
    let currentSlide = 0;
    let slideTimer = null;
    const SLIDE_COUNT = slides.length;

    function activateSlide(index) {
        if (SLIDE_COUNT === 0) return;
        if (index < 0) index = SLIDE_COUNT - 1;
        if (index >= SLIDE_COUNT) index = 0;
        currentSlide = index;
        if (sliderTrack) sliderTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
        slides.forEach((s, i) => s.classList.toggle("active", i === currentSlide));
        dots.forEach((d, i) => d.classList.toggle("active", i === currentSlide));
    }

    function startAutoSlide() {
        clearInterval(slideTimer);
        if (SLIDE_COUNT > 1) slideTimer = setInterval(() => activateSlide(currentSlide + 1), 5500);
    }

    if (SLIDE_COUNT > 0) {
        activateSlide(0);
        startAutoSlide();
        sliderPrev?.addEventListener("click", () => { activateSlide(currentSlide - 1); startAutoSlide(); });
        sliderNext?.addEventListener("click", () => { activateSlide(currentSlide + 1); startAutoSlide(); });
        dots.forEach(dot => dot.addEventListener("click", () => { activateSlide(parseInt(dot.dataset.index)); startAutoSlide(); }));
        const heroSlider = document.querySelector(".hero-slider");
        if (heroSlider) {
            heroSlider.addEventListener("mouseenter", () => clearInterval(slideTimer));
            heroSlider.addEventListener("mouseleave", startAutoSlide);
            let touchStartX = 0;
            heroSlider.addEventListener("touchstart", e => { touchStartX = e.touches[0].clientX; }, { passive: true });
            heroSlider.addEventListener("touchend", e => {
                const dx = e.changedTouches[0].clientX - touchStartX;
                if (Math.abs(dx) > 50) { activateSlide(currentSlide + (dx < 0 ? 1 : -1)); startAutoSlide(); }
            }, { passive: true });
        }
    }

    // ============================================================
    // 5. REVIEWS SLIDER
    // ============================================================
    const reviewsTrack = document.getElementById("reviewsTrack");
    const revPrev = document.getElementById("revPrev");
    const revNext = document.getElementById("revNext");
    let revIndex = 0;

    function getPerView() {
        return window.innerWidth <= 768 ? 1 : window.innerWidth <= 1024 ? 2 : 3;
    }

    function slideReviews(dir) {
        if (!reviewsTrack) return;
        const cards = reviewsTrack.querySelectorAll(".review-card");
        const perView = getPerView();
        const max = Math.max(0, cards.length - perView);
        revIndex = Math.max(0, Math.min(revIndex + dir, max));
        if (revIndex >= max) revIndex = 0;
        const cardW = cards[0] ? cards[0].offsetWidth + 24 : 0;
        reviewsTrack.style.transform = `translateX(-${revIndex * cardW}px)`;
    }

    revPrev?.addEventListener("click", () => slideReviews(-1));
    revNext?.addEventListener("click", () => slideReviews(1));

    if (reviewsTrack) {
        let rTouchX = 0;
        reviewsTrack.addEventListener("touchstart", e => { rTouchX = e.touches[0].clientX; }, { passive: true });
        reviewsTrack.addEventListener("touchend", e => {
            const dx = e.changedTouches[0].clientX - rTouchX;
            if (Math.abs(dx) > 40) slideReviews(dx < 0 ? 1 : -1);
        }, { passive: true });
        let revTimer = setInterval(() => slideReviews(1), 4500);
        revNext?.addEventListener("click", () => { clearInterval(revTimer); revTimer = setInterval(() => slideReviews(1), 4500); });
        revPrev?.addEventListener("click", () => { clearInterval(revTimer); revTimer = setInterval(() => slideReviews(1), 4500); });
        window.addEventListener("resize", () => { revIndex = 0; reviewsTrack.style.transform = "translateX(0)"; }, { passive: true });
    }

    // ============================================================
    // 6. PROFILE DROPDOWN
    // ============================================================
    const profileBtn = document.getElementById("profileToggle");
    const profileMenu = document.getElementById("profileMenu");

    if (profileBtn && profileMenu) {
        profileBtn.addEventListener("click", e => {
            e.stopPropagation();
            profileMenu.classList.toggle("active");
        });
        document.addEventListener("click", e => {
            if (!profileMenu.contains(e.target) && !profileBtn.contains(e.target)) {
                profileMenu.classList.remove("active");
            }
        });
    }

    // ============================================================
    // 7. SCROLL REVEAL
    // ============================================================
    const revealSections = document.querySelectorAll(".reveal-section");
    const revealChildren = document.querySelectorAll(".reveal-child");

    const revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) { entry.target.classList.add("visible"); revealObserver.unobserve(entry.target); }
        });
    }, { threshold: 0.08, rootMargin: "0px 0px -50px 0px" });

    revealSections.forEach(el => revealObserver.observe(el));

    const childObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const siblings = entry.target.parentElement.querySelectorAll(".reveal-child");
                let delay = 0;
                siblings.forEach(sib => { setTimeout(() => sib.classList.add("visible"), delay); delay += 80; });
                childObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });

    revealChildren.forEach(el => childObserver.observe(el));

    // ============================================================
    // 8. NEWSLETTER
    // ============================================================
    const newsletterForm = document.querySelector(".newsletter-form");
    if (newsletterForm) {
        newsletterForm.querySelector("button")?.addEventListener("click", () => {
            const email = newsletterForm.querySelector("input")?.value?.trim();
            if (email && email.includes("@")) {
                showToast("🌿 You're on the list! Welcome to the family.");
                newsletterForm.querySelector("input").value = "";
            } else {
                showToast("Please enter a valid email.");
            }
        });
    }

    // ============================================================
    // 9. SMOOTH SCROLL
    // ============================================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) { e.preventDefault(); target.scrollIntoView({ behavior: "smooth", block: "start" }); }
        });
    });

    // ============================================================
    // 10. AUTO-DISMISS MESSAGES
    // ============================================================
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach(el => {
            el.style.transition = "opacity 0.4s";
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 400);
        });
    }, 4000);

});
