const NAV_ITEMS = {
  citizen: [
    { href: "dashboard.html", label: "My Complaints" },
    { href: "submit.html", label: "Report an Issue" },
  ],
  department: [
    { href: "dashboard.html", label: "Assigned Complaints" },
  ],
  admin: [
    { href: "dashboard.html", label: "Overview" },
    { href: "complaints.html", label: "All Complaints" },
    { href: "departments.html", label: "Departments & Staff" },
  ],
};

function renderSidebar(activeHref, user) {
  const root = document.getElementById("sidebar");
  if (!root) return;
  const items = NAV_ITEMS[user.role] || [];
  const linksHtml = items.map(
    (item) => `<a href="${item.href}" class="${item.href === activeHref ? "active" : ""}">${item.label}</a>`
  ).join("");

  const displayName = user.first_name || (user.email ? user.email.split("@")[0] : "User");

  root.innerHTML = `
    <div class="brand-mark">CivicFix</div>
    ${linksHtml}
    <div class="spacer"></div>
    <div class="user-chip">
      <b>${escapeHtml(displayName)}</b>
      <button class="logout-btn" id="logout-btn">Log out</button>
    </div>
  `;
  document.getElementById("logout-btn").addEventListener("click", () => Auth.logout());
}

function roleLabel(role) {
  if (role === "admin") return "Admin";
  if (role === "department") return "Department";
  return "Citizen";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : str;
  return div.innerHTML;
}