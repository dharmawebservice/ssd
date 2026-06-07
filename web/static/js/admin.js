/* admin.js — SSD Nursery Admin Panel */
(function () {
    "use strict";

    // ── Sidebar ───────────────────────────────────────────────
    function initSidebar() {
        const sidebar  = document.getElementById("sidebar");
        const overlay  = document.getElementById("sidebarOverlay");
        const openBtn  = document.getElementById("openSidebar");
        const closeBtn = document.getElementById("closeSidebar");

        if (!sidebar) return;

        function open()  {
            sidebar.classList.add("active");
            overlay && overlay.classList.add("active");
            document.body.style.overflow = "hidden";
        }
        function close() {
            sidebar.classList.remove("active");
            overlay && overlay.classList.remove("active");
            document.body.style.overflow = "";
        }

        openBtn  && openBtn.addEventListener("click", open);
        closeBtn && closeBtn.addEventListener("click", close);
        overlay  && overlay.addEventListener("click", close);
    }

    // ── Modals ────────────────────────────────────────────────
    function initModals() {
        // Open: any element with data-modal-open="<modal-id>"
        document.querySelectorAll("[data-modal-open]").forEach(btn => {
            btn.addEventListener("click", () => {
                const modal = document.getElementById(btn.dataset.modalOpen);
                if (modal) {
                    modal.classList.add("active");
                    document.body.style.overflow = "hidden";
                }
            });
        });

        // Close: .close-modal, [data-modal-close], .btn-cancel
        document.querySelectorAll("[data-modal-close], .close-modal, .btn-cancel").forEach(btn => {
            btn.addEventListener("click", () => {
                const overlay = btn.closest(".modal-overlay");
                if (overlay) {
                    overlay.classList.remove("active");
                    document.body.style.overflow = "";
                }
            });
        });

        // Close on backdrop click
        document.querySelectorAll(".modal-overlay").forEach(overlay => {
            overlay.addEventListener("click", e => {
                if (e.target === overlay) {
                    overlay.classList.remove("active");
                    document.body.style.overflow = "";
                }
            });
        });
    }

    // ── File input display ────────────────────────────────────
    function initFileInputs() {
        document.querySelectorAll(".file-drop-area input[type=file]").forEach(input => {
            const nameEl = input.closest(".file-drop-area")?.querySelector(".file-name");
            if (!nameEl) return;
            input.addEventListener("change", () => {
                if (input.files.length) {
                    nameEl.textContent = input.files[0].name;
                    nameEl.style.color = "var(--accent)";
                } else {
                    nameEl.textContent = "Click to upload or drag image";
                    nameEl.style.color = "";
                }
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
        toast.offsetHeight;                          // force reflow
        toast.classList.add("show");
        clearTimeout(toast._t);
        toast._t = setTimeout(() => toast.classList.remove("show"), 3000);
    };

    // ── Confirm-before-delete ─────────────────────────────────
    function initDeleteConfirm() {
        document.querySelectorAll("[data-confirm]").forEach(link => {
            link.addEventListener("click", e => {
                if (!confirm(link.dataset.confirm || "Are you sure?")) {
                    e.preventDefault();
                }
            });
        });
    }

    // ── Edit modal pre-fill (called from inline onclick) ──────
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

    // ── Auto-flash Django messages ────────────────────────────
    function flashDjangoMessages() {
        document.querySelectorAll(".django-message").forEach(el => {
            adminToast(el.textContent.trim(), el.dataset.level || "success");
        });
    }

    // ── Boot ──────────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", () => {
        initSidebar();
        initModals();
        initFileInputs();
        initDeleteConfirm();
        flashDjangoMessages();
    });

})();