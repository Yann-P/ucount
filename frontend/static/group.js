const _el = document.getElementById('group-js');
const labels = JSON.parse(_el.dataset.labels);
const TABS = ['spendings', 'add', 'members'];
const TAB_KEY = 'tab:' + location.pathname;

let graphInited = false;

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
    if (id === 'members' && !graphInited) {
        graphInited = true;
        initGraph();
    }
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

function initGraph() {
    const svg = document.getElementById('graph-svg');
    if (!svg) return;
    const graphData = _el.dataset.graph;
    if (!graphData) return;
    let parsed;
    try { parsed = JSON.parse(graphData); } catch { return; }
    const { members, flows, settlements } = parsed;
    if (!members || members.length === 0) return;

    const W = 400, H = 300;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

    const NS = 'http://www.w3.org/2000/svg';
    const N = members.length;
    const fontSize = Math.max(7, Math.min(11, 60 / N));
    const PAD_X = 6, PAD_Y = 4;
    const polyR = Math.min(W / 2, H / 2) - 32;

    function mkEl(tag, attrs) {
        const el = document.createElementNS(NS, tag);
        for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
        return el;
    }

    const defs = mkEl('defs', {});
    function addMarker(id, color) {
        const m = mkEl('marker', { id, markerWidth: 5, markerHeight: 4, refX: 5, refY: 2, orient: 'auto' });
        m.appendChild(mkEl('path', { d: 'M0,0 L5,2 L0,4 Z', fill: color }));
        defs.appendChild(m);
    }
    addMarker('arr-blue', '#3b82f6');
    addMarker('arr-green', '#16a34a');
    svg.appendChild(defs);

    const gZoom = mkEl('g', {});
    svg.appendChild(gZoom);

    const nodes = members.map((name, i) => {
        const angle = (i / N) * 2 * Math.PI - Math.PI / 2;
        const hw = name.length * fontSize * 0.35 + PAD_X;
        const hh = fontSize / 2 + PAD_Y;
        return {
            name,
            x: W / 2 + polyR * Math.cos(angle),
            y: H / 2 + polyR * Math.sin(angle),
            hw, hh,
        };
    });
    const nodeIdx = Object.fromEntries(nodes.map((n, i) => [n.name, i]));

    // Returns the point on the border of `node` in direction (ddx, ddy) (unit vector).
    function borderPt(node, ddx, ddy) {
        const tx = ddx !== 0 ? node.hw / Math.abs(ddx) : Infinity;
        const ty = ddy !== 0 ? node.hh / Math.abs(ddy) : Infinity;
        const t = Math.min(tx, ty);
        return { x: node.x + ddx * t, y: node.y + ddy * t };
    }

    // Canonical perpendicular normal for a pair — same direction regardless of which end is "from".
    // This ensures flow and settlement arrows are always offset to opposite sides.
    function pairNormal(nameA, nameB) {
        const [s, t] = nodeIdx[nameA] < nodeIdx[nameB]
            ? [nodes[nodeIdx[nameA]], nodes[nodeIdx[nameB]]]
            : [nodes[nodeIdx[nameB]], nodes[nodeIdx[nameA]]];
        const dx = t.x - s.x, dy = t.y - s.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        return { nx: -dy / d, ny: dx / d };
    }

    const OFFSET = 9;

    function drawEdge(from, to, amount, type) {
        const s = nodes[nodeIdx[from]], t = nodes[nodeIdx[to]];
        const dx = t.x - s.x, dy = t.y - s.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        const ddx = dx / d, ddy = dy / d;

        const { nx, ny } = pairNormal(from, to);
        const offsetMult = type === 'flow' ? (nodeIdx[from] < nodeIdx[to] ? 1 : -1) : 0;
        const ox = nx * OFFSET * offsetMult, oy = ny * OFFSET * offsetMult;

        const sb = borderPt(s, ddx, ddy);
        const te = borderPt(t, -ddx, -ddy);

        const sx = sb.x + ox, sy = sb.y + oy;
        const tx2 = te.x + ox - ddx * 5, ty2 = te.y + oy - ddy * 5;
        const mx = (sx + tx2) / 2 + ox * 2, my = (sy + ty2) / 2 + oy * 2;

        const color = type === 'flow' ? '#3b82f6' : '#16a34a';
        const marker = type === 'flow' ? 'arr-blue' : 'arr-green';
        gZoom.appendChild(mkEl('path', {
            d: `M${sx},${sy} Q${mx},${my} ${tx2},${ty2}`,
            fill: 'none', stroke: color,
            'stroke-width': 1,
            'stroke-dasharray': type === 'flow' ? '4,3' : 'none',
            'marker-end': `url(#${marker})`,
        }));
        const lx = (sx + 2 * mx + tx2) / 4, ly = (sy + 2 * my + ty2) / 4;
        const lbl = mkEl('text', {
            x: lx + ox, y: ly + oy,
            'text-anchor': 'middle', 'dominant-baseline': 'middle',
            style: 'font-size: 12px', fill: color,
        });
        lbl.textContent = amount.toFixed(2);
        gZoom.appendChild(lbl);
    }

    flows.forEach(e => drawEdge(e.from, e.to, e.amount, 'flow'));
    settlements.forEach(e => drawEdge(e.from, e.to, e.amount, 'settle'));

    nodes.forEach(n => {
        const g = mkEl('g', { transform: `translate(${n.x},${n.y})` });
        g.appendChild(mkEl('rect', {
            x: -n.hw, y: -n.hh,
            width: n.hw * 2, height: n.hh * 2,
            rx: 4, fill: 'white', stroke: '#e5e7eb', 'stroke-width': 1.5,
        }));
        const txt = mkEl('text', {
            'text-anchor': 'middle', 'dominant-baseline': 'middle',
            'font-size': fontSize, fill: '#111827',
        });
        txt.textContent = n.name;
        g.appendChild(txt);
        gZoom.appendChild(g);
    });

    // Legend (fixed, outside gZoom so it doesn't pan/zoom)
    const legend = mkEl('g', {});
    const legendItems = [
        { color: '#3b82f6', dash: '4,3', label: labels.legend_flows },
        { color: '#16a34a', dash: 'none', label: labels.legend_settlements },
    ];
    legendItems.forEach(({ color, dash, label }, i) => {
        const y = 10 + i * 13;
        const line = mkEl('line', { x1: 8, y1: y, x2: 24, y2: y, stroke: color, 'stroke-width': 1, 'stroke-dasharray': dash });
        const lbl = mkEl('text', { x: 28, y: y, 'dominant-baseline': 'middle', style: 'font-size: 12px', fill: '#374151' });
        lbl.textContent = label;
        legend.appendChild(line);
        legend.appendChild(lbl);
    });
    svg.appendChild(legend);

}
