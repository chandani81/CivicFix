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

  const today = new Intl.DateTimeFormat("en-GB", {
    weekday: "long", day: "2-digit", month: "short", year: "numeric"
  }).format(new Date());

  root.innerHTML = `
    <div class="utility-bar">
      <div class="utility-inner">
        <span>CivicFix Community Service Platform</span>
        <span class="utility-links"><b>${today}</b><i></i> English <i></i> Accessibility</span>
      </div>
    </div>
    <div class="masthead">
      <div class="masthead-inner">
        ${civicLogo()}
        <div class="government-title">
          <span>Civic Issue Reporting Platform</span>
          <strong>CivicFix</strong>
          <small>Report • Track • Resolve</small>
        </div>
        <div class="service-mark">
          <b>साझा जिम्मेवारी</b>
          <span>Community • Accountability • Action</span>
        </div>
      </div>
    </div>
    <div class="nav-band">
      <div class="nav-inner">
        <div class="portal-nav">${linksHtml}</div>
        <div class="user-chip">
          <span>${roleLabel(user.role)}</span>
          <button class="logout-btn" id="logout-btn">Log out</button>
        </div>
      </div>
    </div>
    <div class="notice-strip">
      <div class="notice-inner"><b>PUBLIC NOTICE</b><span>Report urgent civic hazards with a clear photo and exact location for faster response.</span></div>
    </div>
  `;
  document.getElementById("logout-btn").addEventListener("click", () => Auth.logout());
  renderGovernmentFooter();
}

function civicLogo() {
  return `<div class="civic-logo" aria-hidden="true">
    <svg viewBox="0 0 64 64" role="img">
      <path d="M32 4 55 13v17c0 14-9.6 24.8-23 30C18.6 54.8 9 44 9 30V13L32 4Z" fill="currentColor"/>
      <path d="M18 38V25l8-5v18m0-11 9-6v17m0-10 11-5v15" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/>
      <path d="m22 41 6 6 14-14" fill="none" stroke="#f2b632" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>`;
}

function renderGovernmentFooter() {
  if (document.getElementById("government-footer")) return;
  document.body.insertAdjacentHTML("beforeend", `
    <footer class="government-footer" id="government-footer">
      <div class="footer-inner">
        <div><b>CivicFix</b><span>Community issue reporting and resolution platform</span></div>
        <div><b>Citizen Support</b><span>Service hours: Sunday–Friday, 10:00–17:00</span></div>
        <div><b>Important</b><span>For life-threatening emergencies, contact the appropriate emergency service.</span></div>
      </div>
      <div class="footer-bottom">© ${new Date().getFullYear()} CivicFix • Built for cleaner, safer and more responsive communities</div>
    </footer>`);
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
