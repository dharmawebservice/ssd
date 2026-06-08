(function () {
  "use strict";

  const IS_AUTH = document.body.dataset.auth === "1";
  const CSRF    = () =>
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

  // ── Cookie helper ─────────────────────────────────────────
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // ── Toast ─────────────────────────────────────────────────
  let toastTmr = null;
  window.showToast = function (msg, type = "success") {
    const toastEl  = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMsg");
    if (!toastEl) return;
    clearTimeout(toastTmr);
    if (toastMsg) toastMsg.textContent = msg;
    toastEl.className = `toast ${type} show`;
    toastTmr = setTimeout(() => toastEl.classList.remove("show"), 2800);
  };

  // ── API helper ────────────────────────────────────────────
  async function api(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF(),
      },
      body: JSON.stringify(body),
    });
    return r.json();
  }

  // ══════════════════════════════════════════════════════════
  // NAVBAR
  // ══════════════════════════════════════════════════════════
  const navbar = document.getElementById("navbar");
  if (navbar) {
    const onScroll = () => navbar.classList.toggle("scrolled", window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // Hamburger
  const hamburger = document.getElementById("mobile-menu");
  const navLinks  = document.getElementById("nav-links");
  if (hamburger && navLinks) {
    hamburger.addEventListener("click", () => {
      const open = navLinks.classList.toggle("active");
      hamburger.querySelector("i").className = open ? "fas fa-times" : "fas fa-bars";
    });
    navLinks.querySelectorAll("a:not(.has-drop > a)").forEach(a => {
      a.addEventListener("click", () => {
        navLinks.classList.remove("active");
        hamburger.querySelector("i").className = "fas fa-bars";
      });
    });
    document.querySelectorAll(".has-drop > a").forEach(a => {
      a.addEventListener("click", e => {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          a.parentElement.classList.toggle("open");
        }
      });
    });
  }

  // Profile dropdown
  const profBtn  = document.getElementById("profileToggle");
  const profMenu = document.getElementById("profileMenu");
  if (profBtn && profMenu) {
    profBtn.addEventListener("click", e => {
      e.stopPropagation();
      profMenu.classList.toggle("active");
    });
    document.addEventListener("click", e => {
      if (!profMenu.contains(e.target) && !profBtn.contains(e.target))
        profMenu.classList.remove("active");
    });
  }

  // ══════════════════════════════════════════════════════════
  // SEARCH OVERLAY + AUTOCOMPLETE
  // ══════════════════════════════════════════════════════════
  const searchOverlay = document.getElementById("searchOverlay");
  const searchInput   = document.getElementById("searchInput");
  const searchSugg    = document.getElementById("searchSuggestions");
  const searchTrigger = document.getElementById("searchTrigger") ||
                        document.querySelector(".search-trigger");
  const searchClose   = document.getElementById("searchClose");

  function openSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.add("active");
    document.body.style.overflow = "hidden";
    setTimeout(() => searchInput && searchInput.focus(), 200);
  }
  function closeSearch() {
    if (!searchOverlay) return;
    searchOverlay.classList.remove("active");
    document.body.style.overflow = "";
    if (searchSugg) searchSugg.innerHTML = "";
  }
  searchTrigger && searchTrigger.addEventListener("click", openSearch);
  searchClose   && searchClose.addEventListener("click", closeSearch);
  searchOverlay && searchOverlay.addEventListener("click", e => {
    if (e.target === searchOverlay) closeSearch();
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeSearch(); });

  let suggTimer = null;
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(suggTimer);
      const q = searchInput.value.trim();
      if (q.length < 2) { if (searchSugg) searchSugg.innerHTML = ""; return; }
      suggTimer = setTimeout(async () => {
        try {
          const r    = await fetch(`/api/search/?q=${encodeURIComponent(q)}`);
          const data = await r.json();
          renderSugg(data);
        } catch {}
      }, 280);
    });
    searchInput.addEventListener("keydown", e => {
      if (e.key === "Enter")
        window.location.href = `/shop/?q=${encodeURIComponent(searchInput.value.trim())}`;
    });
  }

  function renderSugg(data) {
    if (!searchSugg) return;
    if (!data.products?.length && !data.categories?.length) {
      searchSugg.innerHTML = `<div class="sugg-empty">No results found</div>`;
      return;
    }
    let html = "";
    if (data.categories?.length) {
      html += `<div class="sugg-group-label">Categories</div>`;
      data.categories.forEach(c => {
        html += `<a class="sugg-item" href="/shop/?category=${c.slug}">
          <div class="sugg-icon"><i class="fas fa-leaf"></i></div>
          <div><span class="sugg-name">${c.name}</span><span class="sugg-sub">Browse collection</span></div>
        </a>`;
      });
    }
    if (data.products?.length) {
      html += `<div class="sugg-group-label">Products</div>`;
      data.products.forEach(p => {
        const price = p.offer_price ? `₹${p.offer_price}` : `₹${p.price}`;
        html += `<a class="sugg-item" href="/product/${p.slug}/">
          <div class="sugg-icon"><i class="fas fa-seedling"></i></div>
          <div><span class="sugg-name">${p.name}</span><span class="sugg-sub">${price}</span></div>
        </a>`;
      });
    }
    searchSugg.innerHTML = html;
  }

  // Shop page search dropdown
  const shopSearchInput = document.getElementById("shopSearchInput");
  const shopSuggDrop    = document.getElementById("shopSuggDrop");
  if (shopSearchInput && shopSuggDrop) {
    let shopTimer = null;
    shopSearchInput.addEventListener("input", () => {
      clearTimeout(shopTimer);
      const q = shopSearchInput.value.trim();
      if (q.length < 2) { shopSuggDrop.classList.remove("open"); return; }
      shopTimer = setTimeout(async () => {
        try {
          const r    = await fetch(`/api/search/?q=${encodeURIComponent(q)}`);
          const data = await r.json();
          renderShopSugg(data, q);
        } catch {}
      }, 280);
    });
    shopSearchInput.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        const url = new URL(window.location.href);
        url.searchParams.set("q", shopSearchInput.value.trim());
        url.searchParams.delete("page");
        window.location.href = url.toString();
      }
    });
    document.addEventListener("click", e => {
      if (!shopSearchInput.contains(e.target)) shopSuggDrop.classList.remove("open");
    });
  }

  function renderShopSugg(data, q) {
    if (!shopSuggDrop) return;
    if (!data.groups?.length) {
      shopSuggDrop.innerHTML = `<div class="sugg-empty">No results for "${q}"</div>`;
      shopSuggDrop.classList.add("open");
      return;
    }
    let html = "";
    data.groups.forEach(group => {
      html += `<a href="/shop/?category=${group.category.slug}" class="sugg-category-link">
        <img src="${group.category.image || '/static/images/category-placeholder.jpg'}" class="sugg-thumb" alt="${group.category.name}">
        <div class="sugg-info">
          <div class="sugg-title">${group.category.name}</div>
          <div class="sugg-subtitle">Collection</div>
        </div>
      </a>`;
      group.products.forEach(product => {
        html += `<a href="/product/${product.slug}/" class="sugg-product-link">
          <img src="${product.image || '/static/images/product-placeholder.jpg'}" class="sugg-thumb" alt="${product.name}">
          <span>${product.name}</span>
        </a>`;
      });
    });
    shopSuggDrop.innerHTML = html;
    shopSuggDrop.classList.add("open");
  }

  // ══════════════════════════════════════════════════════════
  // HERO SLIDER
  // ══════════════════════════════════════════════════════════
  const sliderTrack = document.getElementById("sliderTrack");
  const slides      = document.querySelectorAll(".slide");
  const dots        = document.querySelectorAll(".dot");
  const sliderPrev  = document.getElementById("sliderPrev");
  const sliderNext  = document.getElementById("sliderNext");
  let   cur = 0, sliderTimer = null;
  const N   = slides.length;

  function goTo(i) {
    if (!N) return;
    cur = ((i % N) + N) % N;
    if (sliderTrack) sliderTrack.style.transform = `translateX(-${cur * 100}%)`;
    slides.forEach((s, j) => s.classList.toggle("active", j === cur));
    dots.forEach((d, j) => d.classList.toggle("active", j === cur));
  }
  function startSlider() {
    clearInterval(sliderTimer);
    sliderTimer = setInterval(() => goTo(cur + 1), 5500);
  }
  if (N) {
    goTo(0); startSlider();
    sliderPrev && sliderPrev.addEventListener("click", () => { goTo(cur - 1); startSlider(); });
    sliderNext && sliderNext.addEventListener("click", () => { goTo(cur + 1); startSlider(); });
    dots.forEach(d => d.addEventListener("click", () => { goTo(+d.dataset.index); startSlider(); }));
    const hero = document.querySelector(".hero-slider");
    if (hero) {
      hero.addEventListener("mouseenter", () => clearInterval(sliderTimer));
      hero.addEventListener("mouseleave", startSlider);
      let tx = 0;
      hero.addEventListener("touchstart", e => { tx = e.touches[0].clientX; }, { passive: true });
      hero.addEventListener("touchend", e => {
        const dx = e.changedTouches[0].clientX - tx;
        if (Math.abs(dx) > 50) { goTo(cur + (dx < 0 ? 1 : -1)); startSlider(); }
      }, { passive: true });
    }
  }

  // ══════════════════════════════════════════════════════════
  // CART — server-side sync
  // ══════════════════════════════════════════════════════════
  let cartData = { cart: [], subtotal: 0, count: 0 };

  function updateCartUI() {
    const { cart, subtotal, count } = cartData;
    document.querySelectorAll(".cart-count, #cartNavCount").forEach(el => {
      el.textContent = count;
    });
    document.querySelectorAll("#cartItemCount").forEach(el => el.textContent = count);
    document.querySelectorAll("#cartTotal").forEach(el => el.textContent = `₹${subtotal}`);

    const body   = document.getElementById("cartBody");
    const footer = document.getElementById("cartFooter");
    if (!body) return;

    if (!cart.length) {
      body.innerHTML = `<div class="cart-empty"><i class="fas fa-seedling"></i><p>Basket is empty</p><a href="/shop/" class="btn-hero-sm">Shop Plants</a></div>`;
      if (footer) footer.style.display = "none";
      return;
    }
    if (footer) footer.style.display = "flex";
    body.innerHTML = cart.map(item => `
      <div class="drawer-item">
        ${item.image
          ? `<img src="${item.image}" alt="${item.name}" class="drawer-item-img">`
          : `<div class="drawer-item-img" style="display:flex;align-items:center;justify-content:center;color:var(--sage)"><i class="fas fa-seedling"></i></div>`}
        <div class="drawer-item-info">
          <h4>${item.name}</h4>
          <div class="item-price">₹${item.price}</div>
          <div class="drawer-qty">
            <button class="dqty-btn" data-pid="${item.id}" data-action="dec">−</button>
            <span class="dqty-num">${item.qty}</span>
            <button class="dqty-btn" data-pid="${item.id}" data-action="inc">+</button>
          </div>
        </div>
        <button class="drawer-remove" data-pid="${item.id}"><i class="fas fa-times"></i></button>
      </div>`).join("");

    body.querySelectorAll(".dqty-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid  = +btn.dataset.pid;
        const item = cart.find(i => i.id === pid);
        if (!item) return;
        const newQty = btn.dataset.action === "inc" ? item.qty + 1 : item.qty - 1;
        const data   = await api("/cart/update/", { product_id: pid, qty: newQty });
        if (data.success) { cartData = data; updateCartUI(); }
      });
    });
    body.querySelectorAll(".drawer-remove").forEach(btn => {
      btn.addEventListener("click", async () => {
        const data = await api("/cart/remove/", { product_id: +btn.dataset.pid });
        if (data.success) { cartData = data; updateCartUI(); showToast("Item removed"); }
      });
    });
  }

  async function fetchCart() {
    try {
      const r  = await fetch("/cart/data/");
      cartData = await r.json();
      updateCartUI();
    } catch {}
  }

  // Cart open/close
  const cartNavBtn  = document.getElementById("cartNavBtn") || document.querySelector(".cart-btn");
  const cartSidebar = document.getElementById("cartSidebar");
  const cartOverlay = document.getElementById("cartOverlay");
  const cartClose   = document.getElementById("cartClose");

  function openCart()  {
    cartSidebar?.classList.add("active");
    cartOverlay?.classList.add("active");
    document.body.style.overflow = "hidden";
    fetchCart();
  }
  function closeCart() {
    cartSidebar?.classList.remove("active");
    cartOverlay?.classList.remove("active");
    document.body.style.overflow = "";
  }

  cartNavBtn  && cartNavBtn.addEventListener("click", openCart);
  cartClose   && cartClose.addEventListener("click", closeCart);
  cartOverlay && cartOverlay.addEventListener("click", closeCart);

  // Add to cart (product cards)
  async function addToCart(productId, qty = 1) {
    if (!IS_AUTH) {
      showToast("Please login to add to cart", "error");
      setTimeout(() => window.location.href = "/auth/?tab=login", 1200);
      return;
    }
    const data = await api("/cart/add/", { product_id: +productId, qty });
    if (data.success) {
      cartData = data;
      updateCartUI();
      showToast(data.message || "Added to cart!");
      openCart();
    } else {
      showToast(data.message || "Error", "error");
    }
  }
  window.addToCart = addToCart;

  document.querySelectorAll(".quick-add").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      e.stopPropagation();
      const pid = btn.dataset.product;
      if (pid) addToCart(+pid, 1);
    });
  });

  // ── Cart qty helpers (used by product detail page inline scripts) ──
  window.updateQty = async function (productId, change) {
    const currentResponse = await fetch("/cart/data/");
    const currentData     = await currentResponse.json();
    const item            = currentData.cart.find(i => i.id == productId);
    if (!item) return;
    const newQty = item.qty + change;
    const data   = await api("/cart/update/", { product_id: productId, qty: newQty });
    if (data.success) { cartData = data; updateCartUI(); }
  };

  window.removeFromCart = async function (productId) {
    const data = await api("/cart/update/", { product_id: productId, qty: 0 });
    if (data.success) { cartData = data; updateCartUI(); }
  };

  // ══════════════════════════════════════════════════════════
  // WISHLIST — server-side sync
  // ══════════════════════════════════════════════════════════
  let wishlistIds = new Set((window.__WISHLIST_IDS__ || []).map(Number));

  function updateWishlistUI() {
    const count = wishlistIds.size;
    const badge = document.getElementById("wishlistNavCount");
    if (badge) {
      badge.textContent = count;
      badge.classList.toggle("show", count > 0);
    }
    document.querySelectorAll(".wishlist-btn, .action-btn.wishlist-btn").forEach(btn => {
      const pid = +(btn.dataset.product || btn.closest("[data-product]")?.dataset.product);
      if (!pid) return;
      const active = wishlistIds.has(pid);
      btn.classList.toggle("wishlisted", active);
      btn.classList.toggle("active", active);
      const icon = btn.querySelector("i");
      if (icon) icon.className = active ? "fas fa-heart" : "far fa-heart";
    });
  }

  async function toggleWishlist(productId) {
    if (!IS_AUTH) {
      showToast("Please login to use wishlist", "error");
      setTimeout(() => window.location.href = "/auth/?tab=login", 1200);
      return;
    }
    const data = await api("/wishlist/toggle/", { product_id: +productId });
    if (data.success) {
      if (data.action === "added") wishlistIds.add(+productId);
      else wishlistIds.delete(+productId);
      updateWishlistUI();
      showToast(data.message);
    } else {
      showToast(data.message || "Error", "error");
    }
  }
  window.toggleWishlist = toggleWishlist;

  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".wishlist-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const pid = btn.dataset.product;
    if (pid) toggleWishlist(+pid);
  });

  async function fetchWishlist() {
    try {
      const r    = await fetch("/wishlist/data/");
      const data = await r.json();
      wishlistIds = new Set((data.ids || []).map(Number));
      updateWishlistUI();
    } catch {}
  }

  // ══════════════════════════════════════════════════════════
  // REVIEWS SLIDER
  // ══════════════════════════════════════════════════════════
  const revTrack = document.getElementById("reviewsTrack");
  const revPrev  = document.getElementById("revPrev");
  const revNext  = document.getElementById("revNext");
  let revIdx = 0;
  function perView()   { return window.innerWidth <= 768 ? 1 : window.innerWidth <= 1024 ? 2 : 3; }
  function slideRev(dir) {
    if (!revTrack) return;
    const cards = revTrack.querySelectorAll(".review-card");
    const max   = Math.max(0, cards.length - perView());
    revIdx = Math.max(0, Math.min(revIdx + dir, max));
    const w = cards[0] ? cards[0].offsetWidth + 22 : 0;
    revTrack.style.transform = `translateX(-${revIdx * w}px)`;
  }
  revPrev && revPrev.addEventListener("click", () => slideRev(-1));
  revNext && revNext.addEventListener("click", () => slideRev(1));
  if (revTrack) {
    let rtx = 0;
    revTrack.addEventListener("touchstart", e => { rtx = e.touches[0].clientX; }, { passive: true });
    revTrack.addEventListener("touchend", e => {
      const dx = e.changedTouches[0].clientX - rtx;
      if (Math.abs(dx) > 40) slideRev(dx < 0 ? 1 : -1);
    }, { passive: true });
    setInterval(() => {
      const cards = revTrack.querySelectorAll(".review-card");
      if (revIdx >= cards.length - perView()) revIdx = -1;
      slideRev(1);
    }, 4000);
  }
  window.addEventListener("resize", () => {
    revIdx = 0;
    if (revTrack) revTrack.style.transform = "translateX(0)";
  }, { passive: true });

  // ══════════════════════════════════════════════════════════
  // HOME FILTER TABS
  // ══════════════════════════════════════════════════════════
  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
      this.classList.add("active");
      const filter = this.dataset.filter;
      document.querySelectorAll(".product-card").forEach(card => {
        const hasSale = card.dataset.hasOffer === "true";
        const inStock = card.dataset.inStock  === "true";
        const show = filter === "all" ||
                     (filter === "sale"    && hasSale) ||
                     (filter === "instock" && inStock);
        card.style.transition = "opacity .25s,transform .25s";
        if (show) {
          card.style.opacity = "1"; card.style.transform = ""; card.style.display = "";
        } else {
          card.style.opacity = "0"; card.style.transform = "scale(.95)";
          setTimeout(() => { if (card.style.opacity === "0") card.style.display = "none"; }, 260);
        }
      });
    });
  });

  // ══════════════════════════════════════════════════════════
  // SCROLL REVEAL
  // ══════════════════════════════════════════════════════════
  const ro = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add("visible"); ro.unobserve(e.target); }
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -50px 0px" });
  document.querySelectorAll(".reveal-section").forEach(el => ro.observe(el));

  const co = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const sibs = e.target.parentElement.querySelectorAll(".reveal-child");
        let d = 0;
        sibs.forEach(s => { setTimeout(() => s.classList.add("visible"), d); d += 80; });
        co.unobserve(e.target);
      }
    });
  }, { threshold: 0.07 });
  document.querySelectorAll(".reveal-child").forEach(el => co.observe(el));

  // ══════════════════════════════════════════════════════════
  // SHOP PAGE FILTER DRAWER (mobile)
  // ══════════════════════════════════════════════════════════
  const drawerOv   = document.getElementById("drawerOverlay");
  const filterDr   = document.getElementById("filterDrawer");
  const openDrBtn  = document.getElementById("openFilterDrawer");
  const closeDrBtn = document.getElementById("drawerClose");
  function openDrawer()  { filterDr?.classList.add("active"); drawerOv?.classList.add("active"); document.body.style.overflow = "hidden"; }
  function closeDrawer() { filterDr?.classList.remove("active"); drawerOv?.classList.remove("active"); document.body.style.overflow = ""; }
  openDrBtn  && openDrBtn.addEventListener("click", openDrawer);
  closeDrBtn && closeDrBtn.addEventListener("click", closeDrawer);
  drawerOv   && drawerOv.addEventListener("click", closeDrawer);

  // ══════════════════════════════════════════════════════════
  // NEWSLETTER
  // ══════════════════════════════════════════════════════════
  document.querySelector(".newsletter-form button")?.addEventListener("click", () => {
    const inp = document.querySelector(".newsletter-form input");
    if (inp?.value?.includes("@")) {
      showToast("🌿 Welcome to the family!");
      inp.value = "";
    } else {
      showToast("Please enter a valid email.", "error");
    }
  });

  // ══════════════════════════════════════════════════════════
  // CATEGORY CARD CLICK
  // ══════════════════════════════════════════════════════════
  document.querySelectorAll(".cat-card[data-href]").forEach(card => {
    card.addEventListener("click", () => window.location.href = card.dataset.href);
  });

  // ══════════════════════════════════════════════════════════
  // SMOOTH ANCHOR SCROLL
  // ══════════════════════════════════════════════════════════
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener("click", function (e) {
      const t = document.querySelector(this.getAttribute("href"));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth" }); }
    });
  });

  // ══════════════════════════════════════════════════════════
  // INIT
  // ══════════════════════════════════════════════════════════
  fetchCart();
  fetchWishlist();
  updateWishlistUI();

})();