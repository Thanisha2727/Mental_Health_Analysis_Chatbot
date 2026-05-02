/**
 * chatbot.js — MediCare AI Frontend Logic
 * ─────────────────────────────────────────────────────────────────────────
 * Handles:
 *  • Role selection (patient / doctor)
 *  • Sending messages to FastAPI backend
 *  • Rendering chat bubbles with timestamps
 *  • Typing indicator
 *  • Suggested prompts
 *  • Symptom checker flow
 *  • Document Q&A mode toggle
 *  • Error toasts
 *  • Session management
 *  • Mobile sidebar toggle
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// CONFIGURATION
// ─────────────────────────────────────────────────────────────────────────────

const CONFIG = {
  // Change this to your deployed backend URL in production
  API_BASE: "http://localhost:8000",

  // Endpoints
  CHAT_URL:    "/chat",
  DOC_URL:     "/doc-chat",
  CLEAR_URL:   "/clear-session",
};


// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────

const state = {
  role:        "patient",          // "patient" | "doctor"
  sessionId:   generateSessionId(),
  isDocMode:   false,              // true = query goes to /doc-chat
  isLoading:   false,
  activeTab:   "chat",             // "chat" | "symptoms" | "info"
  selectedSymptoms: new Set(),
  severity:    null,               // "mild" | "moderate" | "severe"
};


// ─────────────────────────────────────────────────────────────────────────────
// DOM REFERENCES
// ─────────────────────────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const DOM = {
  roleScreen:     $("#role-screen"),
  app:            $("#app"),
  roleBtns:       $$(".role-btn"),
  enterBtn:       $("#btn-enter"),
  roleBadge:      $("#role-badge"),
  sidebar:        $(".sidebar"),
  overlay:        $("#overlay"),
  menuToggle:     $("#menu-toggle"),
  navBtns:        $$(".nav-btn[data-tab]"),
  tabPanels:      $$(".tab-panel"),
  messagesArea:   $("#messages-area"),
  chatInput:      $("#chat-input"),
  sendBtn:        $("#send-btn"),
  modeToggle:     $("#mode-toggle"),
  modeLabel:      $("#mode-label"),
  newChatBtn:     $("#btn-new-chat"),
  switchRoleBtn:  $("#btn-switch-role"),
  errorToast:     $("#error-toast"),
  toastMsg:       $("#toast-msg"),
  headerTitle:    $("#header-title"),
  welcomeBlock:   $("#welcome-block"),
  symptomChips:   $$(".symptom-chip"),
  sevBtns:        $$(".sev-btn"),
  analyzeBtn:     $("#btn-analyze"),
};


// ─────────────────────────────────────────────────────────────────────────────
// SUGGESTED PROMPTS (per role)
// ─────────────────────────────────────────────────────────────────────────────

const PROMPTS = {
  patient: [
    "💊 What are common cold remedies?",
    "😴 How can I improve my sleep quality?",
    "🩸 What does high blood pressure feel like?",
    "🧠 Tips for managing anxiety at home?",
    "🏃 How much exercise do I need weekly?",
    "🌡️ When should I see a doctor for a fever?",
  ],
  doctor: [
    "📋 Differential diagnosis for chest pain",
    "💉 Metformin dosing in CKD patients",
    "🔬 Interpretation of elevated troponin levels",
    "🫁 Management of community-acquired pneumonia",
    "🧪 When to order a D-dimer test?",
    "💊 NSAID contraindications overview",
  ],
};

const SYMPTOM_LIST = [
  { label: "Headache",      emoji: "🤕" },
  { label: "Fever",         emoji: "🌡️" },
  { label: "Cough",         emoji: "😷" },
  { label: "Fatigue",       emoji: "😴" },
  { label: "Chest pain",    emoji: "💔" },
  { label: "Nausea",        emoji: "🤢" },
  { label: "Shortness of breath", emoji: "😮‍💨" },
  { label: "Dizziness",     emoji: "💫" },
  { label: "Sore throat",   emoji: "🤒" },
  { label: "Body ache",     emoji: "🦴" },
  { label: "Runny nose",    emoji: "🤧" },
  { label: "Stomach pain",  emoji: "🫄" },
];


// ─────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────

/** Generate a unique session ID using crypto.randomUUID or fallback */
function generateSessionId() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  return "session-" + Date.now() + "-" + Math.random().toString(36).slice(2, 9);
}

/** Format current time as HH:MM */
function formatTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** Escape HTML to prevent XSS */
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Convert newlines to <br> for display */
function nl2br(str) {
  return escapeHtml(str).replace(/\n/g, "<br>");
}

/** Auto-resize the textarea */
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}


// ─────────────────────────────────────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────────────────────────────────────

let toastTimer = null;

function showToast(message, type = "error") {
  DOM.toastMsg.textContent = message;
  DOM.errorToast.className = `show ${type}`;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { DOM.errorToast.classList.remove("show"); }, 4000);
}


// ─────────────────────────────────────────────────────────────────────────────
// ROLE SELECTION SCREEN
// ─────────────────────────────────────────────────────────────────────────────

function initRoleScreen() {
  // Handle role button clicks
  DOM.roleBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      DOM.roleBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.role = btn.dataset.role;
    });
  });

  // Select patient by default
  DOM.roleBtns[0]?.classList.add("active");

  // Enter the app
  DOM.enterBtn.addEventListener("click", enterApp);
}

function enterApp() {
  DOM.roleScreen.classList.add("hidden");
  DOM.app.classList.add("visible");

  // Apply role styling
  applyRoleStyle();

  // Build the welcome screen with prompts
  buildWelcomeScreen();

  // Build symptom checker chips
  buildSymptomChips();
}

function applyRoleStyle() {
  const isDoctor = state.role === "doctor";

  document.body.classList.toggle("doctor-mode", isDoctor);

  DOM.roleBadge.textContent = isDoctor ? "🩺 Doctor Mode" : "🧑‍⚕️ Patient Mode";
  DOM.headerTitle.textContent = isDoctor
    ? "Clinical Assistant"
    : "Health Assistant";
}


// ─────────────────────────────────────────────────────────────────────────────
// WELCOME SCREEN & SUGGESTED PROMPTS
// ─────────────────────────────────────────────────────────────────────────────

function buildWelcomeScreen() {
  const prompts = PROMPTS[state.role] || PROMPTS.patient;
  const grid = $("#prompts-grid");
  if (!grid) return;

  grid.innerHTML = "";

  prompts.slice(0, 4).forEach((text) => {
    const btn = document.createElement("button");
    btn.className = "prompt-chip";
    btn.textContent = text;
    btn.addEventListener("click", () => {
      DOM.chatInput.value = text.replace(/^[^\s]+\s/, ""); // remove emoji prefix
      DOM.chatInput.focus();
      handleSend();
    });
    grid.appendChild(btn);
  });
}


// ─────────────────────────────────────────────────────────────────────────────
// CHAT — SEND & RECEIVE
// ─────────────────────────────────────────────────────────────────────────────

async function handleSend() {
  const message = DOM.chatInput.value.trim();

  // Validation
  if (!message) {
    showToast("Please type a message before sending.", "error");
    return;
  }
  if (message.length > 2000) {
    showToast("Message is too long (max 2000 characters).", "error");
    return;
  }
  if (state.isLoading) return;

  // Hide welcome block after first message
  if (DOM.welcomeBlock) DOM.welcomeBlock.style.display = "none";

  // Render user bubble
  appendMessage("user", message);

  // Clear input
  DOM.chatInput.value = "";
  autoResize(DOM.chatInput);

  // Show typing indicator
  const typingEl = showTyping();
  state.isLoading = true;
  DOM.sendBtn.disabled = true;

  try {
    const endpoint = state.isDocMode ? CONFIG.DOC_URL : CONFIG.CHAT_URL;
    const body = state.isDocMode
      ? { query: message, role: state.role }
      : { session_id: state.sessionId, query: message, role: state.role };

    const res = await fetch(CONFIG.API_BASE + endpoint, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const data = await res.json();

    removeTyping(typingEl);

    // Determine message class (crisis = special styling)
    const msgClass = data.is_crisis ? "crisis" : "ai";
    appendMessage(msgClass, data.response);

    // Scroll to bottom
    scrollToBottom();

  } catch (err) {
    removeTyping(typingEl);

    const errMsg = err.message.includes("Failed to fetch")
      ? "Cannot reach the server. Is the backend running on port 8000?"
      : err.message;

    appendMessage("ai", `⚠️ ${errMsg}`);
    showToast(errMsg, "error");
  } finally {
    state.isLoading = false;
    DOM.sendBtn.disabled = false;
    DOM.chatInput.focus();
  }
}

/** Append a message bubble to the chat */
function appendMessage(type, text) {
  const isUser   = type === "user";
  const isCrisis = type === "crisis";

  const wrapper = document.createElement("div");
  wrapper.className = `message ${isUser ? "user" : "ai"} ${isCrisis ? "crisis" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = isUser ? "👤" : "🏥";

  const content = document.createElement("div");
  content.className = "msg-content";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = nl2br(text);

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatTime();

  content.appendChild(bubble);
  content.appendChild(time);
  wrapper.appendChild(avatar);
  wrapper.appendChild(content);

  DOM.messagesArea.appendChild(wrapper);
  scrollToBottom();
}

/** Show the typing indicator; returns the element so we can remove it */
function showTyping() {
  const el = document.createElement("div");
  el.className = "message ai typing-indicator";
  el.id = "typing-el";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "🏥";

  const bubble = document.createElement("div");
  bubble.className = "typing-bubble";
  bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

  el.appendChild(avatar);
  el.appendChild(bubble);
  DOM.messagesArea.appendChild(el);
  scrollToBottom();
  return el;
}

function removeTyping(el) {
  el?.remove();
}

function scrollToBottom() {
  DOM.messagesArea.scrollTop = DOM.messagesArea.scrollHeight;
}


// ─────────────────────────────────────────────────────────────────────────────
// SYMPTOM CHECKER
// ─────────────────────────────────────────────────────────────────────────────

function buildSymptomChips() {
  const grid = $("#symptom-grid");
  if (!grid) return;

  grid.innerHTML = "";

  SYMPTOM_LIST.forEach(({ label, emoji }) => {
    const chip = document.createElement("button");
    chip.className = "symptom-chip";
    chip.dataset.label = label;
    chip.innerHTML = `<span class="chip-dot"></span>${emoji} ${label}`;
    chip.addEventListener("click", () => toggleSymptom(chip, label));
    grid.appendChild(chip);
  });
}

function toggleSymptom(chip, label) {
  if (state.selectedSymptoms.has(label)) {
    state.selectedSymptoms.delete(label);
    chip.classList.remove("selected");
  } else {
    state.selectedSymptoms.add(label);
    chip.classList.add("selected");
  }
}

async function analyzeSymptoms() {
  if (state.selectedSymptoms.size === 0) {
    showToast("Please select at least one symptom.", "error");
    return;
  }
  if (!state.severity) {
    showToast("Please select a severity level.", "error");
    return;
  }

  const durationVal  = $("#duration-val")?.value || "1";
  const durationUnit = $("#duration-unit")?.value || "days";
  const symptoms = Array.from(state.selectedSymptoms).join(", ");

  const query = `I have the following symptoms: ${symptoms}. 
Severity: ${state.severity}. 
Duration: ${durationVal} ${durationUnit}. 
What could this indicate and what should I do?`;

  // Switch to chat tab and send
  switchTab("chat");
  DOM.chatInput.value = query;
  await handleSend();
}


// ─────────────────────────────────────────────────────────────────────────────
// TAB NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────

function switchTab(tabId) {
  state.activeTab = tabId;

  DOM.navBtns.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  DOM.tabPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === tabId);
  });

  // Close sidebar on mobile after selecting
  closeSidebar();
}


// ─────────────────────────────────────────────────────────────────────────────
// NEW CHAT / CLEAR SESSION
// ─────────────────────────────────────────────────────────────────────────────

async function startNewChat() {
  // Clear backend session memory
  try {
    await fetch(CONFIG.API_BASE + CONFIG.CLEAR_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ session_id: state.sessionId, query: "" }),
    });
  } catch (_) { /* ignore — not critical */ }

  // Generate a new session ID
  state.sessionId = generateSessionId();

  // Clear the message area
  DOM.messagesArea.innerHTML = "";

  // Re-show the welcome block
  if (DOM.welcomeBlock) DOM.welcomeBlock.style.display = "";

  showToast("New conversation started.", "success");
  closeSidebar();
}


// ─────────────────────────────────────────────────────────────────────────────
// MOBILE SIDEBAR
// ─────────────────────────────────────────────────────────────────────────────

function toggleSidebar() {
  DOM.sidebar.classList.toggle("open");
  DOM.overlay.classList.toggle("show");
}

function closeSidebar() {
  DOM.sidebar.classList.remove("open");
  DOM.overlay.classList.remove("show");
}


// ─────────────────────────────────────────────────────────────────────────────
// EVENT LISTENERS
// ─────────────────────────────────────────────────────────────────────────────

function initEventListeners() {
  // Send on button click
  DOM.sendBtn?.addEventListener("click", handleSend);

  // Send on Enter (Shift+Enter = new line)
  DOM.chatInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  // Auto-resize textarea
  DOM.chatInput?.addEventListener("input", () => autoResize(DOM.chatInput));

  // Document mode toggle
  DOM.modeToggle?.addEventListener("click", () => {
    state.isDocMode = !state.isDocMode;
    DOM.modeToggle.classList.toggle("doc-mode", state.isDocMode);
    DOM.modeLabel.textContent = state.isDocMode ? "Doc Mode ON" : "Doc Mode";
    showToast(
      state.isDocMode
        ? "Document mode: answers from health library"
        : "Standard AI mode",
      "success"
    );
  });

  // Tab navigation
  DOM.navBtns.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // New chat
  DOM.newChatBtn?.addEventListener("click", startNewChat);

  // Switch role (go back to role screen)
  DOM.switchRoleBtn?.addEventListener("click", () => {
    DOM.app.classList.remove("visible");
    DOM.roleScreen.classList.remove("hidden");
  });

  // Mobile menu
  DOM.menuToggle?.addEventListener("click", toggleSidebar);
  DOM.overlay?.addEventListener("click", closeSidebar);

  // Severity buttons
  DOM.sevBtns?.forEach((btn) => {
    btn.addEventListener("click", () => {
      DOM.sevBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.severity = btn.dataset.sev;
    });
  });

  // Analyze symptoms
  DOM.analyzeBtn?.addEventListener("click", analyzeSymptoms);
}


// ─────────────────────────────────────────────────────────────────────────────
// BOOTSTRAP
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  initRoleScreen();
  initEventListeners();
  switchTab("chat");   // default tab
});