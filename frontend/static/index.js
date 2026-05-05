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
    const list = document.getElementById('my-groups-list');
    list.innerHTML = '';
    if (!saved.length) return;

    try {
        const slugs = saved.map(g => g.slug).join(',');
        const r = await fetch('/api/groups/check?slugs=' + encodeURIComponent(slugs));
        const { slugs: existing } = await r.json();
        const valid = saved.filter(g => existing.includes(g.slug));
        if (!valid.length) return;

        const confirmMsg = list.dataset.confirmRemove;
        valid.forEach(({ slug, name }) => {
            const li = document.createElement('li');
            li.style.display = 'flex';
            li.style.alignItems = 'center';
            li.style.gap = '0.375rem';

            const a = document.createElement('a');
            a.href = '/group/' + slug;
            a.textContent = name;
            a.style.flex = '1';

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'member-remove';
            btn.textContent = '×';
            btn.addEventListener('click', () => {
                if (!confirm(confirmMsg)) return;
                const all = JSON.parse(localStorage.getItem('my-groups') || '[]');
                localStorage.setItem('my-groups', JSON.stringify(all.filter(g => g.slug !== slug)));
                loadMyGroups();
            });

            li.appendChild(a);
            li.appendChild(btn);
            list.appendChild(li);
        });
        document.getElementById('my-groups').hidden = false;
    } catch (_) {}
}

loadMyGroups();
