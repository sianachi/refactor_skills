const search = document.getElementById("search");
const tagSelect = document.getElementById("tag");
const count = document.getElementById("count");
const list = document.getElementById("notes");
let notes = [];

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function render() {
  const q = search.value.toLowerCase();
  const tag = tagSelect.value;
  const shown = notes.filter((n) => (!tag || n.tag === tag) && n.title.toLowerCase().includes(q));
  count.textContent = `${shown.length} notes`;
  list.innerHTML = shown
    .map(
      (n) =>
        `<li class="note" data-id="${n.id}"><h3>${escapeHtml(n.title)}</h3><p>${escapeHtml(n.excerpt)}</p>` +
        `<small>${escapeHtml(n.author)} · ${escapeHtml(n.tag)}</small></li>`,
    )
    .join("");
}

async function load() {
  const [notesRes, tagsRes] = await Promise.all([fetch("/api/notes"), fetch("/api/stats/tags")]);
  notes = await notesRes.json();
  for (const t of await tagsRes.json()) {
    tagSelect.add(new Option(`${t.tag} (${t.count})`, t.tag));
  }
  render();
}

search.addEventListener("input", render);
tagSelect.addEventListener("change", render);
load();
