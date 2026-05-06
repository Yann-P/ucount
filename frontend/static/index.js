const fieldset = document.getElementById('members-fieldset');
const removeLabel = fieldset.dataset.removeLabel;
const placeholder = fieldset.dataset.placeholder;

fieldset.querySelectorAll('.member-row').forEach(row => {
    row.querySelector('.member-remove').addEventListener('click', () => { row.remove(); syncRemoveButtons(); });
});

document.getElementById('add-member-btn').addEventListener('click', () => {
    const row = makeRow();
    fieldset.insertBefore(row, document.getElementById('add-member-btn'));
    row.querySelector('input').focus();
    syncRemoveButtons();
});

function makeRow() {
    const row = document.createElement('div');
    row.className = 'member-row';

    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'members';
    input.placeholder = placeholder;
    input.autocomplete = 'off';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'member-remove';
    btn.setAttribute('aria-label', removeLabel);
    btn.textContent = '×';
    btn.addEventListener('click', () => { row.remove(); syncRemoveButtons(); });

    row.appendChild(input);
    row.appendChild(btn);
    return row;
}

function syncRemoveButtons() {
    const rows = fieldset.querySelectorAll('.member-row');
    const atMin = rows.length <= 2;
    rows.forEach(row => {
        const btn = row.querySelector('.member-remove');
        btn.disabled = atMin;
    });
}

async function loadMyGroups() {
    const saved = JSON.parse(localStorage.getItem('my-groups') || '[]');
    if (!saved.length) return;
    const slugs = saved.map(g => g.slug).join(',');
    try {
        const html = await fetch('/api/groups/partial?slugs=' + encodeURIComponent(slugs)).then(r => r.text());
        const list = document.getElementById('my-groups-list');
        list.innerHTML = html;
        if (!list.children.length) return;
        list.querySelectorAll('button[data-slug]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!confirm(btn.dataset.confirm)) return;
                const all = JSON.parse(localStorage.getItem('my-groups') || '[]');
                localStorage.setItem('my-groups', JSON.stringify(all.filter(g => g.slug !== btn.dataset.slug)));
                loadMyGroups();
            });
        });
        document.getElementById('my-groups').hidden = false;
    } catch (_) {}
}

loadMyGroups();
