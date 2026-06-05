document.addEventListener("DOMContentLoaded", () => {
    // Sidebar
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const openBtn = document.getElementById("openSidebar");
    const closeBtn = document.getElementById("closeSidebar");

    function toggleSidebar(force) {
        const active = sidebar.classList.contains("active");
        if (force === true || (!active && force !== false)) {
            sidebar.classList.add("active");
            overlay.classList.add("active");
            document.body.style.overflow = "hidden";
        } else {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
            document.body.style.overflow = "";
        }
    }

    openBtn?.addEventListener("click", () => toggleSidebar(true));
    closeBtn?.addEventListener("click", () => toggleSidebar(false));
    overlay?.addEventListener("click", () => toggleSidebar(false));

    // Modal
    const modal = document.getElementById("createModal");
    const openModalBtn = document.getElementById("openModalBtn");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const cancelBtn = document.getElementById("cancelBtn");

    function openModal() { modal?.classList.add("active"); document.body.style.overflow = "hidden"; }
    function closeModal() { modal?.classList.remove("active"); document.body.style.overflow = ""; }

    openModalBtn?.addEventListener("click", openModal);
    closeModalBtn?.addEventListener("click", closeModal);
    cancelBtn?.addEventListener("click", closeModal);
    modal?.addEventListener("click", e => { if (e.target === modal) closeModal(); });

    // File upload display
    const fileInput = document.getElementById("fileInput");
    const fileDisplay = document.getElementById("fileNameDisplay");
    fileInput?.addEventListener("change", function () {
        if (this.files.length > 0) {
            fileDisplay.textContent = this.files[0].name;
            fileDisplay.style.color = "var(--accent-color)";
        }
    });

    // Auto-dismiss alerts
    document.querySelectorAll(".admin-alert").forEach(el => {
        setTimeout(() => el.remove(), 4000);
    });
});
