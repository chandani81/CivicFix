const params = new URLSearchParams(window.location.search);
const complaintId = params.get("id");
let CURRENT_USER = null;
let map;

async function initComplaintPage() {
  CURRENT_USER = requireAuth();
  if (!CURRENT_USER) return;
  renderSidebar("dashboard.html", CURRENT_USER);
  if (!complaintId) {
    document.getElementById("detail-root").innerHTML = `<div class="empty-state">No complaint specified.</div>`;
    return;
  }
  await loadComplaint();
}

async function loadComplaint() {
  const root = document.getElementById("detail-root");
  try {
    const c = await Api.getComplaint(complaintId);
    root.innerHTML = renderDetail(c);
    if (c.latitude && c.longitude) initMapView(c.latitude, c.longitude, c.address);
    document.getElementById("status-form")?.addEventListener("submit", onUpdateStatus);
    document.getElementById("update-form")?.addEventListener("submit", onPostUpdate);
  } catch (err) {
    root.innerHTML = `<div class="empty-state">Couldn't load this complaint: ${escapeHtml(err.message)}</div>`;
  }
}

function renderDetail(c) {
  // Only department staff can update status now (admin is view-only)
  const canManage = CURRENT_USER.role === "department";

  return `
    <div class="page-head">
      <div>
      <a href="javascript:history.back()" style="display:inline-block; margin-bottom:12px; color:#6b7280;">← Back</a>
        <h1>${escapeHtml(c.title)}</h1>
        <p class="mono">filed ${fullDate(c.created_at)}</p>
      </div>
      <div style="display:flex; gap:10px; align-items:center;">
        ${c.is_emergency ? `<span class="badge-emergency">Emergency</span>` : ""}
        <div class="stamp status-${c.status}">${STATUS_LABELS[c.status]}</div>
      </div>
    </div>

    <div class="detail-grid">
      <div>
        <div class="panel">
          <h3>Description</h3>
          <p style="white-space:pre-wrap;">${escapeHtml(c.description)}</p>
          ${c.emergency_reason ? `<p class="hint" style="margin-top:10px;">AI note: ${escapeHtml(c.emergency_reason)}</p>` : ""}
          ${c.photo ? `<img src="${c.photo}" alt="Complaint photo" style="max-width:100%; border-radius:4px; margin-top:16px; border:1px solid var(--border);">` : ""}
        </div>

        ${c.department ? `
        <div class="panel">
          <h3>AI department routing</h3>
          <p>Routed to <strong>${escapeHtml(c.department.name)}</strong> as
            <strong>${escapeHtml(c.category_display)}</strong>.</p>
          <p class="hint" style="margin-top:8px;">
            ${c.department_email_status === "sent"
              ? `Email forwarded to ${escapeHtml(c.department_email_recipient || c.department.contact_email || "the department")}.`
              : c.department_email_status === "failed"
                ? "Email delivery is pending retry; the complaint remains safely recorded and assigned."
                : "Department email is queued."}
          </p>
        </div>` : ""}

        ${c.address || (c.latitude && c.longitude) ? `
        <div class="panel">
          <h3>Location</h3>
          <p style="margin-bottom:10px;">${escapeHtml(c.address || "")}</p>
          ${c.latitude && c.longitude ? `<div id="map-view"></div>` : ""}
        </div>` : ""}

        <div class="panel">
          <h3>Status history</h3>
          <ul class="timeline">
            ${(c.status_history || []).map((h) => `
              <li>
                <div class="t-status">${STATUS_LABELS[h.status] || h.status}</div>
                ${h.note ? `<div class="t-note">${escapeHtml(h.note)}</div>` : ""}
                <div class="t-meta">${escapeHtml(h.changed_by_email || "system")} · ${fullDate(h.created_at)}</div>
              </li>
            `).join("") || `<li><div class="t-note">No history yet.</div></li>`}
          </ul>
        </div>

        <div class="panel">
          <h3>Updates from the department</h3>
          <ul class="timeline" id="updates-list">
            ${(c.updates || []).map((u) => `
              <li>
                <div class="t-note">${escapeHtml(u.message)}</div>
                <div class="t-meta">${escapeHtml(u.posted_by_email || "")} · ${fullDate(u.created_at)}</div>
              </li>
            `).join("") || `<li><div class="t-note">No updates posted yet.</div></li>`}
          </ul>
          ${canManage ? `
          <form id="update-form" style="margin-top:14px; display:flex; gap:8px;">
            <textarea id="update-message" placeholder="Post a progress update for the citizen…" required style="flex:1;"></textarea>
            <button class="btn btn-teal" type="submit">Post</button>
          </form>` : ""}
        </div>
      </div>

      <div>
        ${canManage ? `
        <div class="panel">
          <h3>Update status</h3>
          <form id="status-form">
            <div class="field">
              <label for="status-select">New status</label>
              <select id="status-select" required>
                <option value="" selected disabled>Select a different status</option>
                ${c.status !== "pending" ? `<option value="pending">Pending</option>` : ""}
                ${c.status !== "in_progress" ? `<option value="in_progress">In Progress</option>` : ""}
                ${c.status !== "resolved" ? `<option value="resolved">Resolved</option>` : ""}
              </select>
            </div>
            <div class="field">
              <label for="status-note">Note (optional)</label>
              <textarea id="status-note" placeholder="e.g. Crew dispatched, ETA tomorrow"></textarea>
            </div>
            <button class="btn btn-primary btn-block" type="submit">Save status</button>
          </form>
        </div>` : ""}
      </div>
    </div>
  `;
}

function initMapView(lat, lng, address) {
  if (map) { map.remove(); map = null; }
  map = L.map("map-view", { zoomControl: false, dragging: false, scrollWheelZoom: false }).setView([lat, lng], 15);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
  L.marker([lat, lng]).addTo(map).bindPopup(address || "Reported location");
}

async function onUpdateStatus(e) {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  try {
    await Api.updateStatus(complaintId, {
      status: document.getElementById("status-select").value,
      note: document.getElementById("status-note").value.trim(),
    });
    toast("Status updated.");
    await loadComplaint();
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

async function onPostUpdate(e) {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  try {
    await Api.postUpdate(complaintId, { message: document.getElementById("update-message").value.trim() });
    toast("Update posted.");
    await loadComplaint();
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

initComplaintPage();
