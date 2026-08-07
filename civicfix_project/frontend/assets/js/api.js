/* =========================================================================
   CivicFix — API client
   Talks to the Django backend. Change API_BASE if your backend runs
   somewhere other than the default local dev server.
   ========================================================================= */

const API_BASE = "http://127.0.0.1:8000/api";

const Auth = {
  getAccess() { return localStorage.getItem("civicfix_access"); },
  getRefresh() { return localStorage.getItem("civicfix_refresh"); },
  getUser() {
    const raw = localStorage.getItem("civicfix_user");
    return raw ? JSON.parse(raw) : null;
  },
  setSession(access, refresh, user) {
    localStorage.setItem("civicfix_access", access);
    if (refresh) localStorage.setItem("civicfix_refresh", refresh);
    if (user) localStorage.setItem("civicfix_user", JSON.stringify(user));
  },
  setUser(user) { localStorage.setItem("civicfix_user", JSON.stringify(user)); },
  clear() {
    localStorage.removeItem("civicfix_access");
    localStorage.removeItem("civicfix_refresh");
    localStorage.removeItem("civicfix_user");
  },
  isLoggedIn() { return !!this.getAccess(); },
  logout(redirect = "/index.html") {
    this.clear();
    window.location.href = relativeToRoot(redirect);
  },
};

/** Resolve a root-relative path ("/index.html") correctly whether the
 *  current page lives at the frontend root or one folder deep (citizen/, etc). */
function relativeToRoot(path) {
  const depth = window.location.pathname.split("/").filter(Boolean);
  // crude heuristic: if we're inside citizen/, department/ or admin/, go up one level
  const inSubfolder = /\/(citizen|department|admin)\//.test(window.location.pathname);
  return (inSubfolder ? ".." : ".") + path;
}

/** Guard a page: redirect to login if not authenticated, optionally enforce a role. */
function requireAuth(allowedRoles) {
  if (!Auth.isLoggedIn()) {
    window.location.href = relativeToRoot("/index.html");
    return null;
  }
  const user = Auth.getUser();
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    toast("You don't have access to that page.", "error");
    window.location.href = relativeToRoot("/index.html");
    return null;
  }
  return user;
}

let refreshingPromise = null;

async function apiRequest(path, { method = "GET", body = null, isForm = false, auth = true, retry = true } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && Auth.getAccess()) headers["Authorization"] = `Bearer ${Auth.getAccess()}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  if (res.status === 401 && auth && retry && Auth.getRefresh()) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiRequest(path, { method, body, isForm, auth, retry: false });
  }

  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }

  if (!res.ok) {
    const message = extractErrorMessage(data) || `Request failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

async function refreshAccessToken() {
  if (refreshingPromise) return refreshingPromise;
  refreshingPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: Auth.getRefresh() }),
      });
      if (!res.ok) throw new Error("refresh failed");
      const data = await res.json();
      Auth.setSession(data.access, null, null);
      return true;
    } catch (e) {
      Auth.clear();
      return false;
    } finally {
      refreshingPromise = null;
    }
  })();
  return refreshingPromise;
}

function extractErrorMessage(data) {
  if (!data) return null;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.non_field_errors)) return data.non_field_errors.join(" ");
  if (typeof data === "object") {
    const firstKey = Object.keys(data)[0];
    if (firstKey) {
      const val = data[firstKey];
      const text = Array.isArray(val) ? val.join(" ") : String(val);
      return `${firstKey}: ${text}`;
    }
  }
  return null;
}

const Api = {
  register: (payload) => apiRequest("/auth/register/", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiRequest("/auth/login/", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/auth/me/"),
  updateMe: (payload) => apiRequest("/auth/me/", { method: "PATCH", body: payload }),
  changePassword: (payload) => apiRequest("/auth/change-password/", { method: "POST", body: payload }),

  listStaff: () => apiRequest("/auth/staff/"),
  createStaff: (payload) => apiRequest("/auth/staff/", { method: "POST", body: payload }),
  deleteStaff: (id) => apiRequest(`/auth/staff/${id}/`, { method: "DELETE" }),
  listCitizens: () => apiRequest("/auth/citizens/"),

  listDepartments: () => apiRequest("/departments/"),
  createDepartment: (payload) => apiRequest("/departments/", { method: "POST", body: payload }),

  listComplaints: (query = "") => apiRequest(`/complaints/${query}`),
  getComplaint: (id) => apiRequest(`/complaints/${id}/`),
  createComplaint: (formData) => apiRequest("/complaints/", { method: "POST", body: formData, isForm: true }),
  updateStatus: (id, payload) => apiRequest(`/complaints/${id}/status/`, { method: "PATCH", body: payload }),
  listUpdates: (id) => apiRequest(`/complaints/${id}/updates/`),
  postUpdate: (id, payload) => apiRequest(`/complaints/${id}/updates/`, { method: "POST", body: payload }),
  stats: () => apiRequest("/complaints/stats/"),
  notifications: () => apiRequest("/complaints/notifications/"),
  markNotificationRead: (id) => apiRequest(`/complaints/notifications/${id}/read/`, { method: "POST" }),

  chatbotAsk: (message) => apiRequest("/chatbot/ask/", { method: "POST", body: { message }, auth: false }),
};

function toast(message, kind = "success") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

const CATEGORY_LABELS = {
  road_damage: "Road Damage",
  water_leakage: "Water Leakage",
  garbage: "Garbage",
  street_light: "Street Light",
  drainage: "Drainage",
  others: "Others",
};

const STATUS_LABELS = {
  pending: "Pending",
  in_progress: "In Progress",
  resolved: "Resolved",
};

function timeAgo(dateStr) {
  const d = new Date(dateStr);
  const diffMs = Date.now() - d.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

function fullDate(dateStr) {
  return new Date(dateStr).toLocaleString();
}
