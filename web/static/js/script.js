document.addEventListener("DOMContentLoaded", () => {

    // ── Navbar scroll ──────────────────────────────────────────
    const navbar = document.getElementById("navbar");
    if (navbar) {
        const onScroll = () => navbar.classList.toggle("scrolled", window.scrollY > 10);
        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();
    }

    // ── Mobile hamburger ───────────────────────────────────────
    const mobileMenuBtn = document.getElementById("mobile-menu");
    const navLinks      = document.getElementById("nav-links");
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

    // ── Search overlay ─────────────────────────────────────────
    const searchTrigger = document.querySelector(".search-trigger");
    const searchOverlay = document.getElementById("searchOverlay");
    const searchClose   = document.getElementById("searchClose");
    const searchInput   = document.getElementById("searchInput");
    if (searchTrigger && searchOverlay) {
        searchTrigger.addEventListener("click", () => { searchOverlay.classList.add("active"); setTimeout(() => searchInput && searchInput.focus(), 300); });
        searchClose && searchClose.addEventListener("click", () => searchOverlay.classList.remove("active"));
        searchOverlay.addEventListener("click", e => { if (e.target === searchOverlay) searchOverlay.classList.remove("active"); });
        document.addEventListener("keydown", e => { if (e.key === "Escape") searchOverlay.classList.remove("active"); });
    }

    // ── Hero banner auto-slider ────────────────────────────────
    const sliderTrack = document.getElementById("sliderTrack");
    const dots        = document.querySelectorAll(".dot");
    const sliderPrev  = document.getElementById("sliderPrev");
    const sliderNext  = document.getElementById("sliderNext");
    const slides      = document.querySelectorAll(".slide");
    let currentSlide  = 0;
    let slideTimer    = null;
    const SLIDE_COUNT = slides.length;
    const AUTO_DELAY  = 5500;

    function activateSlide(index) {
        if (index < 0) index = SLIDE_COUNT - 1;
        if (index >= SLIDE_COUNT) index = 0;
        currentSlide = index;
        if (sliderTrack) sliderTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
        slides.forEach((s, i) => s.classList.toggle("active", i === currentSlide));
        dots.forEach((d, i) => d.classList.toggle("active", i === currentSlide));
    }

    function startAutoSlide() { clearInterval(slideTimer); slideTimer = setInterval(() => activateSlide(currentSlide + 1), AUTO_DELAY); }

    if (slides.length) {
        activateSlide(0);
        startAutoSlide();
        sliderPrev && sliderPrev.addEventListener("click", () => { activateSlide(currentSlide - 1); startAutoSlide(); });
        sliderNext && sliderNext.addEventListener("click", () => { activateSlide(currentSlide + 1); startAutoSlide(); });
        dots.forEach(dot => dot.addEventListener("click", () => { activateSlide(parseInt(dot.dataset.index)); startAutoSlide(); }));
        const heroSlider = document.querySelector(".hero-slider");
        if (heroSlider) {
            heroSlider.addEventListener("mouseenter", () => clearInterval(slideTimer));
            heroSlider.addEventListener("mouseleave", startAutoSlide);
            let tX = 0;
            heroSlider.addEventListener("touchstart", e => { tX = e.touches[0].clientX; }, { passive: true });
            heroSlider.addEventListener("touchend",   e => { const dx = e.changedTouches[0].clientX - tX; if (Math.abs(dx) > 50) { activateSlide(currentSlide + (dx < 0 ? 1 : -1)); startAutoSlide(); } }, { passive: true });
        }
    }

    // ── Cart system ────────────────────────────────────────────
    const cartBtn     = document.querySelector(".cart-btn");
    const cartOverlay = document.getElementById("cartOverlay");
    const cartSidebar = document.getElementById("cartSidebar");
    const cartClose   = document.getElementById("cartClose");
    const cartBody    = document.getElementById("cartBody");
    const cartFooter  = document.getElementById("cartFooter");
    const cartCountEl = document.querySelector(".cart-count");
    const cartItemCnt = document.getElementById("cartItemCount");
    const cartTotalEl = document.getElementById("cartTotal");

    let cart = JSON.parse(sessionStorage.getItem("ssd_cart") || "[]");

    function saveCart() { sessionStorage.setItem("ssd_cart", JSON.stringify(cart)); }

    function openCart()  { cartSidebar && cartSidebar.classList.add("active"); cartOverlay && cartOverlay.classList.add("active"); document.body.style.overflow = "hidden"; }
    function closeCart() { cartSidebar && cartSidebar.classList.remove("active"); cartOverlay && cartOverlay.classList.remove("active"); document.body.style.overflow = ""; }

    cartBtn     && cartBtn.addEventListener("click", openCart);
    cartClose   && cartClose.addEventListener("click", closeCart);
    cartOverlay && cartOverlay.addEventListener("click", closeCart);

    function renderCart() {
        if (!cartBody) return;
        const totalItems = cart.reduce((s, i) => s + i.qty, 0);
        const totalPrice = cart.reduce((s, i) => s + i.price * i.qty, 0);
        if (cartCountEl) cartCountEl.textContent = totalItems;
        if (cartItemCnt) cartItemCnt.textContent = totalItems;
        if (cartTotalEl) cartTotalEl.textContent = `₹${totalPrice}`;
        if (cart.length === 0) {
            cartBody.innerHTML = `<div class="cart-empty"><i class="fas fa-seedling"></i><p>Your basket is empty</p><a href="/shop/" class="btn-hero-sm" onclick="closeCart()">Shop Plants</a></div>`;
            if (cartFooter) cartFooter.style.display = "none";
            return;
        }
        if (cartFooter) cartFooter.style.display = "block";
        cartBody.innerHTML = cart.map(item => `
            <div class="cart-product-item">
                <div class="cart-item-img"><i class="fas fa-seedling"></i></div>
                <div class="cart-item-details">
                    <h4>${item.name}</h4>
                    <div class="item-price">₹${item.price} each</div>
                    <div class="cart-item-qty">
                        <button class="qty-btn" onclick="updateQty('${item.id}',-1)">−</button>
                        <span class="qty-num">${item.qty}</span>
                        <button class="qty-btn" onclick="updateQty('${item.id}',1)">+</button>
                    </div>
                </div>
                <button class="cart-item-remove" onclick="removeFromCart('${item.id}')"><i class="fas fa-times"></i></button>
            </div>`).join("");
    }

    window.updateQty = function(id, delta) {
        const item = cart.find(i => i.id === id);
        if (!item) return;
        item.qty += delta;
        if (item.qty <= 0) cart = cart.filter(i => i.id !== id);
        saveCart(); renderCart();
    };
    window.removeFromCart = function(id) { cart = cart.filter(i => i.id !== id); saveCart(); renderCart(); };

    document.querySelectorAll(".quick-add").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault(); e.stopPropagation();
            const card  = this.closest(".product-card");
            const name  = card?.querySelector("h3")?.textContent?.trim() || "Plant";
            const pid   = this.dataset.product || `p${Date.now()}`;
            const priceText = card?.querySelector(".price")?.childNodes[0]?.textContent?.replace(/[^\d]/g, "") || "0";
            const price = parseInt(priceText) || 0;
            const existing = cart.find(i => i.id === pid);
            if (existing) existing.qty++;
            else cart.push({ id: pid, name, price, qty: 1 });
            saveCart(); renderCart();
            showToast(`${name} added to basket!`);
            this.style.transform = "scale(1.3) rotate(90deg)";
            setTimeout(() => { this.style.transform = ""; }, 300);
        });
    });

    renderCart(); // restore from session

    // ── Wishlist ───────────────────────────────────────────────
    document.querySelectorAll(".wishlist-btn").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault(); e.stopPropagation();
            const icon = this.querySelector("i");
            icon.classList.toggle("far");
            icon.classList.toggle("fas");
            if (icon.classList.contains("fas")) {
                this.style.background = "#e74c3c"; this.style.color = "white";
                const name = this.closest(".product-card")?.querySelector("h3")?.textContent || "Plant";
                showToast(`${name} added to wishlist!`);
            } else { this.style.background = ""; this.style.color = ""; }
        });
    });

    // ── Home filter tabs ───────────────────────────────────────
    const filterTabs   = document.querySelectorAll(".filter-tab");
    const productCards = document.querySelectorAll(".product-card");
    filterTabs.forEach(tab => {
        tab.addEventListener("click", function() {
            filterTabs.forEach(t => t.classList.remove("active"));
            this.classList.add("active");
            const filter = this.dataset.filter;
            productCards.forEach(card => {
                const hasSale   = card.dataset.hasOffer === "true";
                const isInStock = card.dataset.inStock  === "true";
                let show = true;
                if (filter === "sale"    && !hasSale)   show = false;
                if (filter === "instock" && !isInStock) show = false;
                card.style.transition = "opacity 0.3s ease,transform 0.3s ease";
                if (show) { card.style.opacity = "1"; card.style.transform = ""; card.style.display = ""; }
                else { card.style.opacity = "0"; card.style.transform = "scale(0.95)"; setTimeout(() => { if (card.style.opacity === "0") card.style.display = "none"; }, 310); }
            });
        });
    });

    // ── Reviews slider ─────────────────────────────────────────
    const reviewsTrack = document.getElementById("reviewsTrack");
    const revPrev      = document.getElementById("revPrev");
    const revNext      = document.getElementById("revNext");
    let revIndex = 0;
    function getPerView()    { return window.innerWidth <= 768 ? 1 : window.innerWidth <= 1024 ? 2 : 3; }
    function getRevCards()   { return reviewsTrack ? reviewsTrack.querySelectorAll(".review-card") : []; }
    function slideReviews(dir) {
        if (!reviewsTrack) return;
        const cards   = getRevCards();
        const perView = getPerView();
        const max     = Math.max(0, cards.length - perView);
        revIndex = Math.max(0, Math.min(revIndex + dir, max));
        const cardW = cards[0] ? cards[0].offsetWidth + 24 : 0;
        reviewsTrack.style.transform = `translateX(-${revIndex * cardW}px)`;
    }
    revPrev && revPrev.addEventListener("click", () => slideReviews(-1));
    revNext && revNext.addEventListener("click", () => slideReviews(1));
    if (reviewsTrack) {
        let rTX = 0;
        reviewsTrack.addEventListener("touchstart", e => { rTX = e.touches[0].clientX; }, { passive: true });
        reviewsTrack.addEventListener("touchend",   e => { const dx = e.changedTouches[0].clientX - rTX; if (Math.abs(dx) > 40) slideReviews(dx < 0 ? 1 : -1); }, { passive: true });
    }
    if (reviewsTrack) {
        let revTimer = setInterval(() => { const cards = getRevCards(); const perView = getPerView(); if (revIndex >= cards.length - perView) revIndex = -1; slideReviews(1); }, 4200);
    }
    window.addEventListener("resize", () => { revIndex = 0; if (reviewsTrack) reviewsTrack.style.transform = "translateX(0)"; }, { passive: true });

    // ── Profile dropdown ───────────────────────────────────────
    const profileBtn  = document.getElementById("profileToggle");
    const profileMenu = document.getElementById("profileMenu");
    if (profileBtn && profileMenu) {
        profileBtn.addEventListener("click", e => { e.stopPropagation(); profileMenu.classList.toggle("active"); });
        document.addEventListener("click", e => { if (!profileMenu.contains(e.target) && !profileBtn.contains(e.target)) profileMenu.classList.remove("active"); });
    }

    // ── Scroll reveal ──────────────────────────────────────────
    const revealObs = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add("visible"); revealObs.unobserve(entry.target); } });
    }, { threshold: 0.1, rootMargin: "0px 0px -60px 0px" });
    document.querySelectorAll(".reveal-section").forEach(el => revealObs.observe(el));

    const childObs = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const sibs = entry.target.parentElement.querySelectorAll(".reveal-child");
                let delay = 0;
                sibs.forEach(s => { setTimeout(() => s.classList.add("visible"), delay); delay += 90; });
                childObs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });
    document.querySelectorAll(".reveal-child").forEach(el => childObs.observe(el));

    // ── Toast ──────────────────────────────────────────────────
    const toastEl  = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMsg");
    let toastTimer = null;
    window.showToast = function(msg) {
        if (!toastEl) return;
        clearTimeout(toastTimer);
        if (toastMsg) toastMsg.textContent = msg;
        toastEl.classList.add("show");
        toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2800);
    };

    // ── Category card click ────────────────────────────────────
    document.querySelectorAll(".cat-card[data-href]").forEach(card => {
        card.addEventListener("click", () => window.location.href = card.dataset.href);
    });

    // ── Newsletter ─────────────────────────────────────────────
    const newsletterForm = document.querySelector(".newsletter-form");
    if (newsletterForm) {
        newsletterForm.querySelector("button")?.addEventListener("click", () => {
            const email = newsletterForm.querySelector("input")?.value?.trim();
            if (email && email.includes("@")) { showToast("🌿 Welcome to the family!"); newsletterForm.querySelector("input").value = ""; }
            else showToast("Please enter a valid email address.");
        });
    }

    // ── Smooth anchor scroll ───────────────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener("click", function(e) {
            const t = document.querySelector(this.getAttribute("href"));
            if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth", block: "start" }); }
        });
    });

}); // end DOMContentLoaded