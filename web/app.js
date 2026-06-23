const state = {
  token: sessionStorage.getItem("vp_token") || "",
  user: null,
  cities: [],
  tools: [],
  chat: {
    mode: "itinerary",
    provider: "auto",
    depth: "standard",
    optionsLoaded: false,
    hasStarted: false,
    isStreaming: false,
  },
  authMode: "login",
  pendingEmail: "",
  authConfig: {
    google: false,
    emailVerification: true,
  },
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function showToast(message, tone = "info") {
  const toast = $("#toast");
  toast.textContent = message;
  toast.dataset.tone = tone;
  toast.classList.add("is-visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("is-visible"), tone === "error" ? 5600 : 3600);
}

function setStatus(selector, message, tone = "neutral") {
  const node = $(selector);
  if (!node) return;
  node.textContent = message || "";
  node.dataset.tone = tone;
}

function emptyState(title, text, actionLabel, action) {
  const article = document.createElement("article");
  article.className = "empty-state";
  article.appendChild(createText("h3", "", title));
  article.appendChild(createText("p", "meta", text));
  if (actionLabel && action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary";
    button.textContent = actionLabel;
    button.addEventListener("click", action);
    article.appendChild(button);
  }
  return article;
}

function loadingCards(count = 3) {
  return Array.from({ length: count }, () => {
    const card = document.createElement("article");
    card.className = "skeleton-card";
    card.appendChild(document.createElement("span"));
    card.appendChild(document.createElement("span"));
    card.appendChild(document.createElement("span"));
    return card;
  });
}

async function withButtonBusy(button, label, task) {
  const oldHtml = button.innerHTML;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  if (label) setButtonLabel(button, label);
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.innerHTML = oldHtml;
  }
}

function setButtonLabel(button, label) {
  const walker = document.createTreeWalker(button, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node && !node.nodeValue.trim()) node = walker.nextNode();
  if (node) {
    node.nodeValue = ` ${label}`;
  } else {
    button.appendChild(document.createTextNode(label));
  }
}

async function fetchWithTimeout(path, options = {}, timeout = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(path, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request took too long. Please try again.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetchWithTimeout(path, { ...options, headers }, options.timeout || 15000);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.error?.message || "Request failed";
    throw new Error(message);
  }
  return data;
}

function setView(view) {
  document.body.dataset.view = view;
  if (view !== "chat") document.body.classList.remove("is-chat-composing");
  $$(".nav__item").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
    button.tabIndex = active ? 0 : -1;
  });
  $$("[data-view='dashboard']:not(.nav__item)").forEach((button) => {
    button.setAttribute("aria-current", view === "dashboard" ? "page" : "false");
  });
  $$("[data-view-panel]").forEach((panel) => {
    const hidden = panel.dataset.viewPanel !== view;
    panel.classList.toggle("is-hidden", hidden);
    panel.toggleAttribute("hidden", hidden);
  });
  if (view === "cities") loadCities();
  if (view === "tools") loadTools();
  if (view === "trips") loadTrips();
  if (window.matchMedia("(max-width: 560px)").matches) {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function createText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value || "";
  return element;
}

function renderTags(parent, items) {
  const wrap = document.createElement("div");
  wrap.className = "tags";
  items.slice(0, 4).forEach((item) => wrap.appendChild(createText("span", "tag", item)));
  parent.appendChild(wrap);
}

function populateSelect(selector, items, selected) {
  const select = $(selector);
  if (!select || !items?.length) return;
  select.replaceChildren(...items.map((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.available === false ? `${item.label} (not configured)` : item.label;
    option.disabled = item.available === false;
    option.title = item.description || "";
    return option;
  }));
  const enabled = items.find((item) => item.id === selected && item.available !== false) || items.find((item) => item.available !== false);
  if (enabled) select.value = enabled.id;
}

function renderFacts(parent, className, items) {
  const wrap = document.createElement("div");
  wrap.className = className;
  items.filter(Boolean).forEach((item) => wrap.appendChild(createText("span", "", item)));
  if (wrap.children.length) parent.appendChild(wrap);
}

async function loadChatOptions() {
  try {
    const data = await api("/api/chat");
    populateSelect("#chatMode", data.modes, state.chat.mode);
    populateSelect("#chatProvider", data.providers, state.chat.provider);
    populateSelect("#chatDepth", data.depths, state.chat.depth);
    state.chat.optionsLoaded = true;
    if (!state.chat.hasStarted) setStatus("#chatStatus", "Ready. Start with a question or a quick prompt.");
  } catch (error) {
    setStatus("#chatStatus", "Chat options are using local defaults.", "error");
  }
}

async function loadAuthConfig() {
  try {
    state.authConfig = await api("/api/auth/config");
  } catch (error) {
    state.authConfig = { google: false, emailVerification: true };
    showToast("Account providers are using local defaults.", "error");
  }
  updateAuthUi();
}

function cityCard(city) {
  const article = document.createElement("article");
  article.className = "city-card";
  const image = document.createElement("img");
  image.loading = "lazy";
  image.src = city.image || "/static/img/great-wall.jpg";
  image.alt = `${city.name} travel view`;
  image.addEventListener("error", () => {
    image.src = "/static/img/great-wall.jpg";
  }, { once: true });
  article.appendChild(image);
  const body = document.createElement("div");
  body.className = "city-card__body";
  body.appendChild(createText("h3", "", city.name));
  renderFacts(body, "city-card__facts", [city.province, city.duration, city.bestSeason]);
  body.appendChild(createText("p", "meta", city.vibe));
  renderTags(body, city.highlights || []);
  article.appendChild(body);
  return article;
}

async function loadCities() {
  const grid = $("#cityGrid");
  const featured = $("#featuredCities");
  try {
    if (!state.cities.length) {
      setStatus("#cityStatus", "Loading city intelligence...");
      grid.replaceChildren(...loadingCards(6));
      if (featured && !featured.children.length) featured.replaceChildren(...loadingCards(4));
      const data = await api("/api/cities");
      state.cities = data.cities || [];
    }
  } catch (error) {
    setStatus("#cityStatus", error.message, "error");
    grid.replaceChildren(emptyState("Cities did not load", "Check the connection and try again.", "Retry", loadCities));
    return;
  }
  const query = ($("#citySearch")?.value || "").toLowerCase();
  const filtered = state.cities.filter((city) => {
    const haystack = [city.name, city.province, city.vibe, ...(city.highlights || [])].join(" ").toLowerCase();
    return haystack.includes(query);
  });
  setStatus("#cityStatus", `${filtered.length} destination${filtered.length === 1 ? "" : "s"} ready`);
  grid.replaceChildren(...(filtered.length ? filtered.map(cityCard) : [
    emptyState("No city match", "Try a city, province, season, or highlight such as hotpot or Great Wall.", "Clear search", () => {
      $("#citySearch").value = "";
      loadCities();
    }),
  ]));
  if (featured && !featured.children.length) {
    featured.replaceChildren(...state.cities.slice(0, 4).map(cityCard));
  } else if (featured && featured.querySelector(".skeleton-card")) {
    featured.replaceChildren(...state.cities.slice(0, 4).map(cityCard));
  }
}

function renderToolDetail(tool) {
  const detail = $("#toolDetail");
  detail.replaceChildren();
  detail.appendChild(createText("h3", "", tool.name));
  if (tool.items) {
    const list = document.createElement("ul");
    tool.items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item.label ? `${item.label}${item.required ? " - essential" : ""}` : `${item.context}: ${item.english}`;
      list.appendChild(li);
    });
    detail.appendChild(list);
  } else if (tool.numbers) {
    const list = document.createElement("ul");
    Object.entries(tool.numbers).forEach(([label, number]) => {
      const li = document.createElement("li");
      li.textContent = `${label}: ${number}`;
      list.appendChild(li);
    });
    detail.appendChild(list);
  } else {
    detail.appendChild(createText("p", "meta", tool.summary || tool.description || ""));
  }
}

async function loadTools() {
  try {
    if (!state.tools.length) {
      setStatus("#toolStatus", "Loading travel tools...");
      $("#toolGrid").replaceChildren(...loadingCards(4));
      const data = await api("/api/tools");
      state.tools = data.tools || [];
    }
  } catch (error) {
    setStatus("#toolStatus", error.message, "error");
    $("#toolGrid").replaceChildren(emptyState("Tools did not load", "The toolkit is temporarily unavailable.", "Retry", loadTools));
    $("#toolDetail").replaceChildren();
    return;
  }
  setStatus("#toolStatus", `${state.tools.length} tools available`);
  const cards = state.tools.map((tool) => {
    const card = document.createElement("article");
    card.className = "tool-card";
    card.appendChild(createText("h3", "", tool.name));
    card.appendChild(createText("p", "meta", tool.description));
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary";
    button.textContent = "Open";
    button.addEventListener("click", async () => {
      await withButtonBusy(button, "Opening", async () => {
        try {
          const data = await api(`/api/tools/${tool.id}`);
          renderToolDetail(data.tool);
          showToast(`${tool.name} opened`);
        } catch (error) {
          showToast(error.message, "error");
        }
      });
    });
    card.appendChild(button);
    return card;
  });
  $("#toolGrid").replaceChildren(...cards);
  if (!$("#toolDetail").children.length && state.tools[0]) {
    const data = await api(`/api/tools/${state.tools[0].id}`);
    renderToolDetail(data.tool);
  }
}

function addMessage(author, text, kind = "") {
  const node = $("#messageTemplate").content.firstElementChild.cloneNode(true);
  node.classList.toggle("is-user", kind === "user");
  $(".message__author", node).textContent = author;
  $(".message__body", node).textContent = text;
  $("#chatLog").appendChild(node);
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
  return $(".message__body", node);
}

function currentChatSettings(overrides = {}) {
  return {
    mode: overrides.mode || $("#chatMode")?.value || state.chat.mode,
    provider: overrides.provider || $("#chatProvider")?.value || state.chat.provider,
    depth: overrides.depth || $("#chatDepth")?.value || state.chat.depth,
  };
}

async function sendChat(message, overrides = {}) {
  const settings = currentChatSettings(overrides);
  state.chat = { ...state.chat, ...settings };
  startChatExperience();
  setStatus("#chatStatus", "Thinking through the route...");
  addMessage("You", message, "user");
  const target = addMessage("VisePanda", "");
  const targetMessage = target.closest(".message");
  const input = $("#chatInput");
  try {
    state.chat.isStreaming = true;
    if (input) input.disabled = true;
    const headers = { "Content-Type": "application/json" };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const response = await fetchWithTimeout("/api/chat", {
      method: "POST",
      headers,
      body: JSON.stringify({ message, ...settings }),
    }, 22000);
    if (!response.ok || !response.body) {
      throw new Error("I could not reach the guide service. Please try again.");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      lines.forEach((line) => {
        if (!line.startsWith("data:")) return;
        let payload;
        try {
          payload = JSON.parse(line.slice(5).trim());
        } catch {
          return;
        }
        if (payload.meta) {
          $(".message__author", targetMessage).textContent = `VisePanda - ${payload.meta.modeLabel} - ${payload.meta.providerLabel}`;
          setStatus("#chatStatus", `${payload.meta.modeLabel} via ${payload.meta.providerLabel}`);
        }
        if (payload.token) target.textContent += payload.token;
      });
      $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
    }
  } catch (error) {
    target.textContent = "I could not reach the guide service. Please try again.";
    showToast(error.message, "error");
  } finally {
    state.chat.isStreaming = false;
    if (input) input.disabled = false;
    if (window.matchMedia("(max-width: 560px)").matches) {
      document.body.classList.remove("is-chat-composing");
      requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
    } else {
      input?.focus({ preventScroll: true });
    }
  }
}

function startChatExperience() {
  if (state.chat.hasStarted) return;
  state.chat.hasStarted = true;
  $("#panel-chat")?.classList.add("has-started");
  $("#chatWelcome")?.classList.add("is-hidden");
  [".chat-toolbar", ".chat-prompts"].forEach((selector) => {
    const node = $(selector);
    if (!node) return;
    node.classList.remove("is-hidden");
    node.classList.add("fade-in");
  });
}

async function loadTrips() {
  const list = $("#tripList");
  try {
    if (!state.token) {
      const localTrips = JSON.parse(localStorage.getItem("vp_guest_trips") || "[]");
      setStatus("#tripStatus", localTrips.length ? "Guest trips are saved on this device." : "Guest mode: save a quick trip on this device.");
      list.replaceChildren(...(localTrips.length ? localTrips.map(tripCard) : [
        emptyState("No trips yet", "Save a draft here, or sign in later to sync across devices.", "Ask AI", () => setView("chat")),
      ]));
      return;
    }
    setStatus("#tripStatus", "Loading saved trips...");
    list.replaceChildren(...loadingCards(2));
    const data = await api("/api/trips");
    const trips = data.trips || [];
    setStatus("#tripStatus", trips.length ? "Synced trips loaded." : "Signed in, but no saved trips yet.");
    list.replaceChildren(...(trips.length ? trips.map(tripCard) : [
      emptyState("No saved trips", "Create your first China trip and it will sync to this account.", "Ask AI", () => setView("chat")),
    ]));
  } catch (error) {
    setStatus("#tripStatus", error.message, "error");
    list.replaceChildren(emptyState("Trips did not load", "Try refreshing this view.", "Retry", loadTrips));
  }
}

function tripCard(trip) {
  const card = document.createElement("article");
  card.className = "trip-card";
  card.appendChild(createText("h3", "", trip.title));
  const dates = [trip.startDate, trip.endDate].filter(Boolean).join(" to ");
  renderFacts(card, "trip-card__facts", [trip.destination || "China", dates]);
  return card;
}

async function saveTrip(form) {
  const body = Object.fromEntries(new FormData(form).entries());
  try {
    if (state.token) {
      await api("/api/trips", { method: "POST", body: JSON.stringify(body) });
    } else {
      const trips = JSON.parse(localStorage.getItem("vp_guest_trips") || "[]");
      trips.unshift({ ...body, id: Date.now() });
      localStorage.setItem("vp_guest_trips", JSON.stringify(trips.slice(0, 12)));
    }
  } catch (error) {
    showToast(error.message, "error");
    throw error;
  }
  form.reset();
  await loadTrips();
  showToast("Trip saved");
}

function updateAuthUi() {
  const signedIn = Boolean(state.user);
  const verifying = state.authMode === "verify" && !signedIn;
  $("#authTitle").textContent = signedIn ? "Profile" : verifying ? "Verify email" : state.authMode === "login" ? "Sign in" : "Create account";
  $("#authStatus").textContent = signedIn
    ? `Signed in as ${state.user.email}`
    : verifying
      ? `Enter the code sent to ${state.pendingEmail || "your email"}.`
      : state.authMode === "login"
        ? "Use your email and password, or continue with Google."
        : "Create an account with email and password. We will send a verification code.";
  $("#authButton").title = signedIn ? state.user.email : "Account";
  $("#authForm").classList.toggle("is-hidden", signedIn || verifying);
  $("#verifyForm").classList.toggle("is-hidden", !verifying);
  $("#profileForm").classList.toggle("is-hidden", !signedIn);
  $("#toggleAuthMode").textContent = state.authMode === "login" ? "Create an account" : "Sign in instead";
  $("#googleLogin").classList.toggle("is-hidden", !state.authConfig.google);
  if (verifying && state.pendingEmail) {
    $("#verifyForm").elements.email.value = state.pendingEmail;
  }
  if (signedIn) {
    $("#profileForm").elements.name.value = state.user.name || "";
  }
}

async function restoreSession() {
  if (!state.token) return;
  try {
    const data = await api("/api/auth/me");
    state.user = data.user;
  } catch {
    state.token = "";
    sessionStorage.removeItem("vp_token");
    showToast("Your session expired. Please sign in again.", "error");
  }
  updateAuthUi();
}

function handleAuthReturn() {
  const params = new URLSearchParams(window.location.search);
  const authError = params.get("auth_error");
  if (authError) showToast(authError, "error");
  if (params.get("auth") === "google") showToast("Signed in with Google");
  if (authError || params.get("auth")) {
    history.replaceState({}, "", window.location.pathname);
  }
}

function bindEvents() {
  $$(".nav__item").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $$("[data-view='dashboard']:not(.nav__item)").forEach((button) => button.addEventListener("click", () => setView("dashboard")));
  $("#mobileAskButton").addEventListener("click", () => {
    setView("chat");
    setTimeout(() => $("#chatInput")?.focus(), 180);
  });
  $$("[data-prompt]").forEach((button) => button.addEventListener("click", async () => {
    setView("chat");
    if (button.dataset.mode && $("#chatMode")) $("#chatMode").value = button.dataset.mode;
    if (button.dataset.depth && $("#chatDepth")) $("#chatDepth").value = button.dataset.depth;
    await sendChat(button.dataset.prompt, { mode: button.dataset.mode, depth: button.dataset.depth });
  }));
  ["#chatMode", "#chatProvider", "#chatDepth"].forEach((selector) => {
    const control = $(selector);
    if (!control) return;
    control.addEventListener("change", () => {
      state.chat = { ...state.chat, ...currentChatSettings() };
      setStatus("#chatStatus", "Chat settings updated.");
    });
  });
  $("#citySearch").addEventListener("input", loadCities);
  $("#chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = $("#chatInput");
    const button = event.currentTarget.querySelector("button");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    await withButtonBusy(button, "Sending", () => sendChat(message));
  });
  $("#chatInput").addEventListener("focus", () => document.body.classList.add("is-chat-composing"));
  $("#chatInput").addEventListener("blur", () => document.body.classList.remove("is-chat-composing"));
  $("#quickPlanner").addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    const button = event.currentTarget.querySelector("button");
    setView("chat");
    const length = values.length || values.duration || "7 days";
    await withButtonBusy(button, "Asking", () => sendChat(`Plan a ${length} China trip for ${values.destination || "a first-time visitor"}.`));
  });
  $("#tripForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    await withButtonBusy(button, "Saving", () => saveTrip(form));
  });
  $("#refreshTrips").addEventListener("click", (event) => withButtonBusy(event.currentTarget, "Refreshing", loadTrips));
  $("#authButton").addEventListener("click", () => {
    updateAuthUi();
    $("#authDialog").showModal();
  });
  $("#toggleAuthMode").addEventListener("click", () => {
    state.authMode = state.authMode === "login" ? "register" : "login";
    updateAuthUi();
  });
  $("#backToSignIn").addEventListener("click", () => {
    state.authMode = "login";
    updateAuthUi();
  });
  $("#authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form).entries());
    const endpoint = state.authMode === "login" ? "/api/auth/login" : "/api/auth/register";
    const button = form.querySelector("button[type='submit']");
    await withButtonBusy(button, "Working", async () => {
      try {
        const data = await api(endpoint, { method: "POST", body: JSON.stringify(body) });
        let message = "Account ready";
        if (data.token) {
          state.token = data.token;
          sessionStorage.setItem("vp_token", state.token);
          state.user = data.user;
        } else if (data.requiresVerification) {
          state.pendingEmail = data.email || body.email;
          state.authMode = "verify";
          $("#verifyForm").elements.code.value = data.verificationCode || "";
          message = data.delivery === "sent" ? "Verification code sent" : "Verification code ready";
        } else {
          state.authMode = "login";
          const login = await api("/api/auth/login", { method: "POST", body: JSON.stringify(body) });
          state.token = login.token;
          sessionStorage.setItem("vp_token", state.token);
          state.user = login.user;
        }
        form.reset();
        updateAuthUi();
        showToast(message);
      } catch (error) {
        if (error.message.includes("Verify your email")) {
          state.pendingEmail = body.email;
          state.authMode = "verify";
          updateAuthUi();
        }
        showToast(error.message, "error");
      }
    });
  });
  $("#verifyForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form).entries());
    const button = form.querySelector("button[type='submit']");
    await withButtonBusy(button, "Verifying", async () => {
      try {
        const data = await api("/api/auth/verify-email", { method: "POST", body: JSON.stringify(body) });
        state.token = data.token;
        sessionStorage.setItem("vp_token", state.token);
        state.user = data.user;
        state.pendingEmail = "";
        form.reset();
        updateAuthUi();
        showToast("Email verified");
      } catch (error) {
        showToast(error.message, "error");
      }
    });
  });
  $("#resendVerification").addEventListener("click", async (event) => {
    const email = $("#verifyForm").elements.email.value || state.pendingEmail;
    await withButtonBusy(event.currentTarget, "Sending", async () => {
      try {
        const data = await api("/api/auth/resend-verification", { method: "POST", body: JSON.stringify({ email }) });
        state.pendingEmail = data.email || email;
        if (data.verificationCode) $("#verifyForm").elements.code.value = data.verificationCode;
        updateAuthUi();
        showToast(data.delivery === "sent" ? "Verification code sent" : "Verification code ready");
      } catch (error) {
        showToast(error.message, "error");
      }
    });
  });
  $("#profileForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form).entries());
    const button = form.querySelector("button[type='submit']");
    await withButtonBusy(button, "Updating", async () => {
      try {
        const data = await api("/api/auth/update-profile", { method: "POST", body: JSON.stringify(body) });
        state.user = data.user;
        form.elements.currentPassword.value = "";
        form.elements.newPassword.value = "";
        updateAuthUi();
        showToast("Profile updated");
      } catch (error) {
        showToast(error.message, "error");
      }
    });
  });
  $("#logoutButton").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
    state.token = "";
    state.user = null;
    sessionStorage.removeItem("vp_token");
    updateAuthUi();
    showToast("Signed out");
  });
}

async function boot() {
  handleAuthReturn();
  bindEvents();
  setView("chat");
  Promise.all([loadCities(), restoreSession(), loadChatOptions(), loadAuthConfig()]).catch(() => {});
}

document.addEventListener("DOMContentLoaded", boot);
