const _el = document.getElementById('group-js');
const labels = JSON.parse(_el.dataset.labels);
const TABS = ['spendings', 'add', 'members'];
const TAB_KEY = 'tab:' + location.pathname;

function activateTab(id) {
    TABS.forEach(t => {
        const tab = document.getElementById('tab-' + t);
        const panel = document.getElementById('panel-' + t);
        const active = t === id;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
        panel.hidden = !active;
    });
    localStorage.setItem(TAB_KEY, id);
}

document.querySelector('[role="tablist"]').addEventListener('keydown', e => {
    const idx = TABS.findIndex(t => document.getElementById('tab-' + t) === document.activeElement);
    if (idx === -1) return;
    let next = idx;
    if      (e.key === 'ArrowRight') next = (idx + 1) % TABS.length;
    else if (e.key === 'ArrowLeft')  next = (idx - 1 + TABS.length) % TABS.length;
    else if (e.key === 'Home')       next = 0;
    else if (e.key === 'End')        next = TABS.length - 1;
    else return;
    e.preventDefault();
    activateTab(TABS[next]);
    document.getElementById('tab-' + TABS[next]).focus();
});

TABS.forEach(t => {
    document.getElementById('tab-' + t).addEventListener('click', () => activateTab(t));
});

const saved = localStorage.getItem(TAB_KEY);
activateTab(TABS.includes(saved) ? saved : TABS[0]);

(function checkAddedParam() {
    const params = new URLSearchParams(location.search);
    if (!params.has('added')) return;
    history.replaceState(null, '', location.pathname);
    const el = document.getElementById('toast');
    el.textContent = labels.spending_added;
    el.classList.add('visible');
    setTimeout(() => el.classList.remove('visible'), 3000);
})();

(function formatDates() {
    const thisYear = new Date().getFullYear();
    document.querySelectorAll('time.spending-date').forEach(el => {
        const [y, m, d] = el.dateTime.split('-').map(Number);
        const date = new Date(y, m - 1, d);
        const opts = y === thisYear ? { day: 'numeric', month: 'short' } : { day: 'numeric', month: 'short', year: 'numeric' };
        el.textContent = date.toLocaleDateString(undefined, opts);
    });
})();

(function descriptionAutocomplete() {
    const input = document.getElementById('description');
    const list = document.querySelector('.autocomplete .suggestions');
    if (!input || !list) return;
    const reasons = JSON.parse(_el.dataset.reasons);
    const norm = s => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
    let active = -1;

    function show(matches) {
        active = -1;
        list.replaceChildren(...matches.map(r => {
            const li = document.createElement('li');
            li.textContent = r;
            li.addEventListener('mousedown', e => { e.preventDefault(); input.value = r; list.hidden = true; });
            return li;
        }));
        list.hidden = false;
    }

    input.addEventListener('input', () => {
        const q = norm(input.value);
        if (!q) { list.hidden = true; return; }
        const matches = reasons.filter(r => norm(r).includes(q)).slice(0, 8);
        matches.length ? show(matches) : (list.hidden = true);
    });

    input.addEventListener('keydown', e => {
        const items = list.querySelectorAll('li');
        if (list.hidden || !items.length) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, items.length - 1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); }
        else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); input.value = items[active].textContent; list.hidden = true; active = -1; return; }
        else if (e.key === 'Escape') { list.hidden = true; active = -1; return; }
        items.forEach((li, i) => li.classList.toggle('active', i === active));
    });

    input.addEventListener('blur', () => { list.hidden = true; });
})();

(function initDateInput() {
    const input = document.getElementById('spending-date');
    if (!input) return;
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    input.value = `${y}-${m}-${d}`;
})();

(function saveToMyGroups() {
    const slug = _el.dataset.slug;
    const name = _el.dataset.name;
    const key = 'my-groups';
    const groups = JSON.parse(localStorage.getItem(key) || '[]');
    const filtered = groups.filter(g => g.slug !== slug);
    filtered.unshift({ slug, name });
    localStorage.setItem(key, JSON.stringify(filtered.slice(0, 20)));
})();

document.getElementById('history-btn').addEventListener('click', () => {
    const panel = document.getElementById('history-panel');
    panel.hidden = !panel.hidden;
});

function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        const btn = document.getElementById('copy-btn');
        btn.textContent = labels.copied;
        setTimeout(() => btn.textContent = labels.copy_link, 2000);
    });
}

let qrGenerated = false;
function toggleQR() {
    const qr = document.getElementById('qr');
    if (qr.style.display === 'none') {
        qr.style.display = 'block';
        if (!qrGenerated) {
            new QRCode(qr, { text: window.location.href, width: 200, height: 200 });
            qrGenerated = true;
        }
    } else {
        qr.style.display = 'none';
    }
}
