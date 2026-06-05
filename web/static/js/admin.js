/* admin.js — shared admin panel JS */
(function () {
    "use strict";

    // ── Sidebar toggle ────────────────────────────────────────
    function initSidebar() {
        const sidebar  = document.getElementById("sidebar");
        const overlay  = document.getElementById("sidebarOverlay");
        const openBtn  = document.getElementById("openSidebar");
        const closeBtn = document.getElementById("closeSidebar");

        if (!sidebar) return;

        function open()  { sidebar.classList.add("active"); overlay && overlay.classList.add("active"); document.body.style.overflow = "hidden"; }
        function close() { sidebar.classList.remove("active"); overlay && overlay.classList.remove("active"); document.body.style.overflow = ""; }

        openBtn  && openBtn.addEventListener("click", open);
        closeBtn && closeBtn.addEventListener("click", close);
        overlay  && overlay.addEventListener("click", close);
    }

    // ── Modal helpers ─────────────────────────────────────────
    function initModals() {
        // Any element with data-modal-open="<id>" opens that modal
        document.querySelectorAll("[data-modal-open]").forEach(btn => {
            btn.addEventListener("click", () => {
                const m = document.getElementById(btn.dataset.modalOpen);
                if (m) { m.classList.add("active"); document.body.style.overflow = "hidden"; }
            });
        });

        // Any element with data-modal-close inside a .modal-overlay closes it
        document.querySelectorAll("[data-modal-close], .close-modal, .btn-cancel").forEach(btn => {
            btn.addEventListener("click", () => {
                const overlay = btn.closest(".modal-overlay");
                if (overlay) { overlay.classList.remove("active"); document.body.style.overflow = ""; }
            });
        });

        // Click outside modal card
        document.querySelectorAll(".modal-overlay").forEach(overlay => {
            overlay.addEventListener("click", e => {
                if (e.target === overlay) { overlay.classList.remove("active"); document.body.style.overflow = ""; }
            });
        });
    }

    // ── File input display ────────────────────────────────────
    function initFileInputs() {
        document.querySelectorAll(".file-drop-area input[type=file]").forEach(input => {
            const nameEl = input.closest(".file-drop-area").querySelector(".file-name");
            if (!nameEl) return;
            input.addEventListener("change", () => {
                nameEl.textContent = input.files.length ? input.files[0].name : "Click to upload or drag image";
                nameEl.style.color = input.files.length ? "var(--accent)" : "";
            });
        });
    }

    // ── Admin toast ───────────────────────────────────────────
    window.adminToast = function (msg, type = "success") {
        let toast = document.getElementById("adminToast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "adminToast";
            toast.className = "admin-toast";
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.className = `admin-toast ${type}`;
        // Force reflow
        toast.offsetHeight;
        toast.classList.add("show");
        clearTimeout(toast._t);
        toast._t = setTimeout(() => toast.classList.remove("show"), 3000);
    };

    // ── Confirm delete ────────────────────────────────────────
    function initDeleteConfirm() {
        document.querySelectorAll("[data-confirm]").forEach(link => {
            link.addEventListener("click", e => {
                if (!confirm(link.dataset.confirm || "Are you sure?")) e.preventDefault();
            });
        });
    }

    // ── Edit modal pre-fill ───────────────────────────────────
    window.openEditModal = function (modalId, data) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        Object.entries(data).forEach(([key, val]) => {
            const el = modal.querySelector(`[name="${key}"]`);
            if (el) el.value = val;
        });
        modal.classList.add("active");
        document.body.style.overflow = "hidden";
    };

    // ── Django messages auto-toast ────────────────────────────
    function flashDjangoMessages() {
        document.querySelectorAll(".django-message").forEach(el => {
            adminToast(el.textContent.trim(), el.dataset.level || "success");
        });
    }

    // ── Init ──────────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", () => {
        initSidebar();
        initModals();
        initFileInputs();
        initDeleteConfirm();
        flashDjangoMessages();
    });
})();