const state = {
  documents: [],
  currentDocument: null,
  currentSession: null,
};

const el = {
  docList: document.getElementById('doc-list'),
  uploadZone: document.getElementById('upload-zone'),
  fileInput: document.getElementById('file-input'),
  chatScroll: document.getElementById('chat-scroll'),
  chatInner: document.getElementById('chat-inner'),
  chatHeaderTitle: document.getElementById('chat-header-title'),
  chatHeaderSub: document.getElementById('chat-header-sub'),
  composer: document.getElementById('composer'),
  questionInput: document.getElementById('question-input'),
  sendBtn: document.getElementById('send-btn'),
  toast: document.getElementById('toast'),
};

// ---------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------
async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, options);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) { /* ignore parse errors */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function showToast(message) {
  el.toast.textContent = message;
  el.toast.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.toast.classList.remove('show'), 4200);
}

// ---------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------
async function loadDocuments() {
  state.documents = await api('/documents/');
  renderDocList();
}

function renderDocList() {
  if (!state.documents.length) {
    el.docList.innerHTML = `<div class="empty-doc-list">No notes uploaded yet. Add a PDF or DOCX above to get started.</div>`;
    return;
  }

  el.docList.innerHTML = '';
  const heading = document.createElement('div');
  heading.className = 'doc-list-heading';
  heading.textContent = 'Your documents';
  el.docList.appendChild(heading);

  state.documents.forEach((doc) => {
    const item = document.createElement('div');
    item.className = 'doc-item' + (state.currentDocument?.id === doc.id ? ' active' : '');
    item.tabIndex = 0;

    const statusLabel = {
      pending: 'Pending…',
      processing: 'Processing…',
      ready: `${doc.page_or_chunk_count} chunks indexed`,
      failed: 'Failed to process',
    }[doc.status];

    item.innerHTML = `
      <div class="doc-icon">${doc.file_type.toUpperCase()}</div>
      <div class="doc-meta">
        <div class="doc-name" title="${escapeHtml(doc.original_filename)}">${escapeHtml(doc.original_filename)}</div>
        <div class="doc-status ${doc.status}">${statusLabel}</div>
      </div>
      <button class="doc-delete" title="Delete" aria-label="Delete ${escapeHtml(doc.original_filename)}">✕</button>
    `;

    item.addEventListener('click', (e) => {
      if (e.target.closest('.doc-delete')) return;
      selectDocument(doc);
    });
    item.querySelector('.doc-delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteDocument(doc);
    });

    el.docList.appendChild(item);
  });
}

async function uploadFile(file) {
  const allowed = ['.pdf', '.docx'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('Only PDF and DOCX files are supported.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  showToast(`Uploading "${file.name}"…`);
  try {
    const doc = await api('/documents/', { method: 'POST', body: formData });
    await loadDocuments();
    const fresh = state.documents.find((d) => d.id === doc.id);
    if (fresh?.status === 'failed') {
      showToast(fresh.error_message || 'Failed to process this document.');
    } else if (fresh?.status === 'ready') {
      showToast(`"${fresh.original_filename}" is ready. Ask it anything.`);
      selectDocument(fresh);
    }
  } catch (err) {
    showToast(err.message);
  }
}

async function deleteDocument(doc) {
  if (!confirm(`Delete "${doc.original_filename}"? This can't be undone.`)) return;
  try {
    await api(`/documents/${doc.id}/`, { method: 'DELETE' });
    if (state.currentDocument?.id === doc.id) {
      state.currentDocument = null;
      state.currentSession = null;
      renderEmptyChat();
    }
    await loadDocuments();
  } catch (err) {
    showToast(err.message);
  }
}

async function selectDocument(doc) {
  state.currentDocument = doc;
  renderDocList();

  if (doc.status !== 'ready') {
    renderChatHeader(doc);
    el.chatInner.innerHTML = `<div class="welcome"><span class="glyph">”</span><h3>Still getting ready</h3><p>This document is ${doc.status === 'failed' ? 'not processed — ' + escapeHtml(doc.error_message || 'an error occurred.') : 'still processing.'}</p></div>`;
    setComposerEnabled(false);
    return;
  }

  try {
    const session = await api(`/documents/${doc.id}/sessions/`, { method: 'POST' });
    state.currentSession = session;
    renderChatHeader(doc);
    renderMessages(session.messages);
    setComposerEnabled(true);
    el.questionInput.focus();
  } catch (err) {
    showToast(err.message);
  }
}

// ---------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------
function renderChatHeader(doc) {
  el.chatHeaderTitle.textContent = doc.original_filename;
  el.chatHeaderSub.textContent = doc.status === 'ready'
    ? `Ready · ${doc.page_or_chunk_count} chunks indexed`
    : doc.status;
}

function renderEmptyChat() {
  el.chatHeaderTitle.textContent = 'Document Q&A';
  el.chatHeaderSub.textContent = 'Upload notes to begin';
  el.chatInner.innerHTML = `
    <div class="welcome">
      <span class="glyph">”</span>
      <h3>Ask your notes anything</h3>
      <p>Upload a PDF or DOCX in the sidebar. Once it's indexed, ask questions and get answers grounded only in that document — with the exact excerpts it used.</p>
    </div>`;
  setComposerEnabled(false);
}

function renderMessages(messages) {
  if (!messages.length) {
    el.chatInner.innerHTML = `<div class="welcome"><span class="glyph">”</span><h3>Ready when you are</h3><p>Ask a question about this document to get started.</p></div>`;
    return;
  }
  el.chatInner.innerHTML = '';
  messages.forEach(appendMessageEl);
  scrollToBottom();
}

function appendMessageEl(msg) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${msg.role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = msg.role === 'user' ? 'YOU' : 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = msg.content;

  if (msg.role === 'assistant' && msg.source_chunks?.length) {
    const sources = document.createElement('div');
    sources.className = 'sources';
    sources.innerHTML = `<div class="sources-label">Grounded in</div>`;
    msg.source_chunks.forEach((chunk) => {
      const chip = document.createElement('div');
      chip.className = 'source-chip collapsed';
      chip.innerHTML = `<span class="source-tag">§${chunk.order + 1}</span>${escapeHtml(chunk.text)}`;
      chip.addEventListener('click', () => chip.classList.toggle('collapsed'));
      sources.appendChild(chip);
    });
    bubble.appendChild(sources);
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  el.chatInner.appendChild(wrap);
}

function appendTypingIndicator() {
  const wrap = document.createElement('div');
  wrap.className = 'msg assistant';
  wrap.id = 'typing-indicator';
  wrap.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>
  `;
  el.chatInner.appendChild(wrap);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById('typing-indicator')?.remove();
}

function scrollToBottom() {
  el.chatScroll.scrollTop = el.chatScroll.scrollHeight;
}

function setComposerEnabled(enabled) {
  el.questionInput.disabled = !enabled;
  el.sendBtn.disabled = !enabled;
  el.questionInput.placeholder = enabled
    ? 'Ask a question about this document…'
    : 'Select a ready document to start chatting…';
}

async function sendQuestion(text) {
  if (!state.currentSession) return;

  appendMessageEl({ role: 'user', content: text, source_chunks: [] });
  scrollToBottom();
  appendTypingIndicator();
  setComposerEnabled(false);

  try {
    const assistantMsg = await api(`/sessions/${state.currentSession.id}/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    });
    removeTypingIndicator();
    appendMessageEl(assistantMsg);
    scrollToBottom();
  } catch (err) {
    removeTypingIndicator();
    showToast(err.message);
  } finally {
    setComposerEnabled(true);
    el.questionInput.focus();
  }
}

// ---------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

el.uploadZone.addEventListener('click', () => el.fileInput.click());
el.fileInput.addEventListener('change', (e) => {
  if (e.target.files[0]) uploadFile(e.target.files[0]);
  e.target.value = '';
});

['dragover', 'dragenter'].forEach((evt) =>
  el.uploadZone.addEventListener(evt, (e) => {
    e.preventDefault();
    el.uploadZone.classList.add('dragover');
  })
);
['dragleave', 'drop'].forEach((evt) =>
  el.uploadZone.addEventListener(evt, (e) => {
    e.preventDefault();
    el.uploadZone.classList.remove('dragover');
  })
);
el.uploadZone.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

el.composer.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = el.questionInput.value.trim();
  if (!text) return;
  el.questionInput.value = '';
  el.questionInput.style.height = 'auto';
  sendQuestion(text);
});

el.questionInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    el.composer.requestSubmit();
  }
});

el.questionInput.addEventListener('input', () => {
  el.questionInput.style.height = 'auto';
  el.questionInput.style.height = Math.min(el.questionInput.scrollHeight, 140) + 'px';
});

// ---------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------
renderEmptyChat();
loadDocuments().catch((err) => showToast(err.message));
