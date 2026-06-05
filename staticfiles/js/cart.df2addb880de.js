// CSRF helper
function getCookie(name) {
    let v = null;
    document.cookie.split(";").forEach(c => {
        const [k, val] = c.trim().split("=");
        if (k === name) v = decodeURIComponent(val);
    });
    return v;
}

// Universal API caller
async function cartAPI(url, data) {
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify(data),
        });
        return await res.json();
    } catch (e) {
        return { success: false, message: "Network error" };
    }
}

function updateCartBadge(count) {
    document.querySelectorAll(".cart-count, #cartBadge").forEach(el => {
        el.textContent = count;
        el.style.transform = "scale(1.4)";
        setTimeout(() => el.style.transform = "", 300);
    });
}

async function addToCart(pid, qty = 1) {
    const res = await cartAPI("/cart/add/", { product_id: pid, qty });
    if (res.success) {
        showToast(res.message || "Added to cart!");
        updateCartBadge(res.cart_count);
    } else {
        showToast(res.message || "Failed to add");
    }
}

async function toggleWishlist(pid, btn) {
    const res = await cartAPI("/wishlist/toggle/", { product_id: pid });
    if (res.success) {
        const icon = btn.querySelector("i");
        if (res.wishlisted) {
            icon.className = "fas fa-heart";
            btn.classList.add("wishlisted");
        } else {
            icon.className = "far fa-heart";
            btn.classList.remove("wishlisted");
        }
        showToast(res.message);
    } else {
        if (!res.success && res.message === "Please login first") {
            window.location.href = "/auth/?tab=login";
        } else {
            showToast(res.message);
        }
    }
}

window.showToast = function (msg) {
    const toast = document.getElementById("toast");
    const msgEl = document.getElementById("toastMsg");
    if (!toast) return;
    if (msgEl) msgEl.textContent = msg;
    toast.classList.add("show");
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
};
