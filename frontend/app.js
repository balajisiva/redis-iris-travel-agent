const state = {
  sessionId: null,
  busy: false,
};

const els = {
  sessionId: document.querySelector("#sessionId"),
  messages: document.querySelector("#messages"),
  form: document.querySelector("#chatForm"),
  input: document.querySelector("#messageInput"),
  send: document.querySelector("#sendButton"),
  newSession: document.querySelector("#newSessionButton"),
  deleteMemory: document.querySelector("#deleteMemoryButton"),
  stm: document.querySelector("#stmList"),
  cacheStatus: document.querySelector("#cacheStatus"),
  tools: document.querySelector("#toolsList"),
  ltm: document.querySelector("#ltmList"),
  written: document.querySelector("#writtenList"),
};

function setBusy(busy) {
  state.busy = busy;
  els.send.disabled = busy;
  els.newSession.disabled = busy;
  els.deleteMemory.disabled = busy;
  els.input.disabled = busy;
}

function setSession(sessionId) {
  state.sessionId = sessionId;
  els.sessionId.textContent = sessionId;
}

function appendMessage(role, label, text) {
  const node = document.createElement("article");
  node.className = `message ${role}`;
  node.innerHTML = `<span class="message-label"></span><div></div>`;
  node.querySelector(".message-label").textContent = label;
  node.querySelector("div").textContent = text;
  els.messages.append(node);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function renderList(element, items, emptyText) {
  element.innerHTML = "";
  element.classList.toggle("empty", items.length === 0);
  const values = items.length ? items : [emptyText];
  for (const item of values) {
    const li = document.createElement("li");
    li.textContent = item;
    element.append(li);
  }
}

function renderCacheStatus(cacheHit, matchedPrompt, similarityScore) {
  els.cacheStatus.innerHTML = "";

  if (cacheHit) {
    const similarity = similarityScore ? (similarityScore * 100).toFixed(1) : "N/A";
    els.cacheStatus.innerHTML = `
      <div class="cache-indicator cache-hit">
        <span class="cache-label">✓ Cache Hit</span>
        <span class="cache-similarity">${similarity}% similar</span>
      </div>
      ${matchedPrompt ? `<div class="cache-matched-prompt"><strong>Matched:</strong> "${matchedPrompt}"</div>` : ""}
    `;
  } else {
    els.cacheStatus.innerHTML = `
      <div class="cache-indicator cache-miss">
        <span class="cache-label">○ Cache Miss</span>
        <span class="cache-detail">Response cached for future queries</span>
      </div>
    `;
  }
}

function renderTools(toolCalls) {
  console.log("[DEBUG] renderTools called with:", toolCalls);

  els.tools.innerHTML = "";
  els.tools.classList.toggle("empty", !toolCalls || toolCalls.length === 0);

  if (!toolCalls || toolCalls.length === 0) {
    els.tools.innerHTML = '<div class="tool-placeholder">No tools called yet</div>';
    return;
  }

  for (const toolCall of toolCalls) {
    console.log("[DEBUG] Processing tool call:", toolCall);

    const toolDiv = document.createElement("div");
    toolDiv.className = "tool-call";

    const toolName = toolCall.tool || "unknown";
    const params = toolCall.params || {};
    const result = toolCall.result || {};
    const results = result.results || [];
    const count = result.count || 0;
    const hasError = result.error;

    console.log(`[DEBUG] Tool: ${toolName}, Results count: ${results.length}, Has error: ${hasError}`);

    // Show tool name and parameters
    let paramsStr = Object.entries(params).map(([k, v]) => `${k}="${v}"`).join(", ");
    let html = `<div class="tool-header">
      <span class="tool-name">${toolName}</span>
      ${paramsStr ? `<span class="tool-params">(${paramsStr})</span>` : ""}
    </div>`;

    if (hasError) {
      html += `<div class="tool-error">Error: ${result.error}</div>`;
    } else if (results.length > 0) {
      html += `<div class="tool-count">Found ${count || results.length} results</div>`;
      html += '<div class="tool-results">';
      for (const item of results.slice(0, 3)) {
        const name = item.name || "Unknown";
        const desc = item.description || "";
        const rating = item.rating ? ` • ⭐ ${item.rating}` : "";
        const price = item.price_range || item.price_usd ? ` • ${item.price_range || "$" + item.price_usd}` : "";
        html += `<div class="tool-result-item">
          <strong>${name}${rating}${price}</strong>
          ${desc ? `<span>${desc.substring(0, 150)}${desc.length > 150 ? "..." : ""}</span>` : ""}
        </div>`;
      }
      html += '</div>';
      if (results.length > 3) {
        html += `<div class="tool-more">+${results.length - 3} more results</div>`;
      }
    } else {
      html += '<div class="tool-no-results">No results found</div>';
    }

    toolDiv.innerHTML = html;
    els.tools.appendChild(toolDiv);
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return payload;
}

async function createSession() {
  const payload = await api("/api/sessions", { method: "POST" });
  setSession(payload.session_id);
  els.messages.innerHTML = "";
  renderList(els.stm, [], "No short-term memory yet.");
  renderTools([]);
  renderList(els.ltm, [], "No long-term memory retrieved yet.");
  renderList(els.written, [], "No long-term memory written yet.");
}

async function sendMessage(message) {
  setBusy(true);
  appendMessage("user", "👤 You", message);
  try {
    const payload = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message }),
    });
    setSession(payload.session_id);
    appendMessage("ai", "🤖 AI", payload.assistant_message);
    renderList(els.stm, payload.short_term_memory, "No short-term memory yet.");
    renderCacheStatus(payload.cache_hit, payload.matched_prompt, payload.similarity_score);
    renderTools(payload.tool_calls || []);
    renderList(els.ltm, payload.long_term_memory, "No long-term memory retrieved yet.");
    renderList(
      els.written,
      payload.extracted_long_term_memory,
      "No long-term memory written this turn."
    );
  } catch (error) {
    appendMessage("system", "Error", error.message);
  } finally {
    setBusy(false);
    els.input.focus();
  }
}

async function deleteSessionMemory() {
  if (!state.sessionId) {
    return;
  }
  setBusy(true);
  try {
    await api(`/api/sessions/${encodeURIComponent(state.sessionId)}/memory`, { method: "DELETE" });
    renderList(els.stm, [], "No short-term memory yet.");
  } catch (error) {
    appendMessage("system", "Error", error.message);
  } finally {
    setBusy(false);
  }
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = els.input.value.trim();
  if (!message || state.busy) {
    return;
  }
  els.input.value = "";
  sendMessage(message);
});

els.newSession.addEventListener("click", () => {
  if (!state.busy) {
    createSession().catch((error) => appendMessage("system", "Error", error.message));
  }
});

els.deleteMemory.addEventListener("click", () => {
  if (!state.busy) {
    deleteSessionMemory();
  }
});

createSession().catch((error) => appendMessage("system", "Error", error.message));
