
let cancelCurrentEdit = null;

function hanldeDBClick(element) {
    if (cancelCurrentEdit) {
        cancelCurrentEdit();
        cancelCurrentEdit = null;
    }

    if (element.querySelector('.input-stock')) return;

    const row = element.closest('tr');
    const actionCell = row.querySelector('td:last-child');
    const field = element.dataset.field;
    const originalValue = element.innerText.trim();
    const inputType = field === 'quantity' ? 'number' : 'text';

    element.innerText = '';
    const inputDiv = document.createElement('div');
    const input = document.createElement('input');
    input.type = inputType;
    input.value = originalValue;
    input.classList.add('input-stock', 'form-control');
    inputDiv.appendChild(input);
    element.appendChild(inputDiv);
    input.focus();

    const originalActionHTML = actionCell.innerHTML;
    actionCell.innerHTML = `
        <span class="action-confirm" style="cursor:pointer;color:green;font-size:1.4rem;margin-right:10px;" title="Guardar">&#10003;</span>
        <span class="action-cancel" style="cursor:pointer;color:red;font-size:1.4rem;" title="Cancelar">&#10007;</span>
    `;

    function confirmEdit() {
        const newValue = input.value.trim();
        if (newValue === '') return;
        const id = row.dataset.id;
        const type = row.dataset.type;
        const url = type === 'product'
            ? `/pamo_bots/products_sodimac/${id}/`
            : `/pamo_bots/sodimac_kits/${id}/`;
        fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ field, value: newValue }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                element.innerText = newValue;
                actionCell.innerHTML = originalActionHTML;
                bindDeleteBtn(row);
                cancelCurrentEdit = null;
            } else {
                showError('Error: ' + data.message);
            }
        })
        .catch(() => showError('Error al guardar'));
    }

    function cancelEdit() {
        element.innerText = originalValue;
        actionCell.innerHTML = originalActionHTML;
        bindDeleteBtn(row);
        cancelCurrentEdit = null;
    }

    cancelCurrentEdit = cancelEdit;

    actionCell.querySelector('.action-confirm').addEventListener('click', confirmEdit);
    actionCell.querySelector('.action-cancel').addEventListener('click', cancelEdit);

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') confirmEdit();
        if (e.key === 'Escape') cancelEdit();
    });
}

function bindDeleteBtn(row) {
    const btn = row.querySelector('.delete-btn');
    if (!btn) return;
    btn.addEventListener('click', function () {
        const id = row.dataset.id;
        const type = row.dataset.type;
        const url = type === 'product'
            ? `/pamo_bots/products_sodimac/${id}/`
            : `/pamo_bots/sodimac_kits/${id}/`;
        Swal.fire({
            title: '¿Eliminar registro?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Eliminar',
            cancelButtonText: 'Cancelar',
        }).then(result => {
            if (result.isConfirmed) {
                fetch(url, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) row.remove();
                    else showError(data.message);
                });
            }
        });
    });
}

function showError(msg) {
    Swal.fire({ icon: 'error', title: 'Error', text: msg, timer: 2000, showConfirmButton: false });
}

function setEventDblclick() {
    document.querySelectorAll('.editable').forEach((cell) => {
        cell.addEventListener('dblclick', function () {
            hanldeDBClick(this);
        });
    });
}

// options: { prefill: {field: value}, insertAfter: DOMElement }
function addNewRow(tbody, type, options = {}) {
    if (cancelCurrentEdit) {
        cancelCurrentEdit();
        cancelCurrentEdit = null;
    }

    const isKit = type === 'kit';
    const fields = isKit
        ? ['kitnumber', 'ean', 'sku', 'quantity']
        : ['sku_sodimac', 'sku_pamo', 'ean'];
    const url = isKit ? '/pamo_bots/sodimac_kits/' : '/pamo_bots/products_sodimac/';
    const prefill = options.prefill || {};
    const insertAfter = options.insertAfter || null;

    const row = document.createElement('tr');
    row.dataset.type = type;

    if (isKit) {
        row.appendChild(document.createElement('td'));
    }

    const inputs = {};
    fields.forEach(field => {
        const td = document.createElement('td');
        td.className = 'text-center';
        const input = document.createElement('input');
        input.type = field === 'quantity' ? 'number' : 'text';
        input.classList.add('form-control', 'input-stock');
        input.placeholder = field;
        if (prefill[field] !== undefined) {
            input.value = prefill[field];
            input.readOnly = true;
            input.style.background = '#e9ecef';
        }
        td.appendChild(input);
        row.appendChild(td);
        inputs[field] = input;
    });

    const actionTd = document.createElement('td');
    actionTd.className = 'text-center';
    actionTd.innerHTML = `
        <span class="action-confirm" style="cursor:pointer;color:green;font-size:1.4rem;margin-right:10px;" title="Guardar">&#10003;</span>
        <span class="action-cancel" style="cursor:pointer;color:red;font-size:1.4rem;" title="Cancelar">&#10007;</span>
    `;
    row.appendChild(actionTd);

    if (insertAfter) {
        insertAfter.after(row);
    } else {
        tbody.prepend(row);
    }

    // Focus first editable input
    const firstEditable = Object.values(inputs).find(i => !i.readOnly);
    if (firstEditable) firstEditable.focus();

    const optionalFields = ['ean'];

    function confirmNew() {
        const body = {};
        for (const field of fields) {
            // Los campos pre-llenados se toman del prefill original, no del input
            const val = prefill[field] !== undefined ? prefill[field] : inputs[field].value.trim();
            if (val === '' && !optionalFields.includes(field)) { showError('Completa todos los campos obligatorios'); return; }
            body[field] = val || null;
        }
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(body),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                row.dataset.id = data.id;
                if (isKit) {
                    row.classList.add('kit-row');
                    row.dataset.kitnumber = body.kitnumber;
                }
                fields.forEach(field => {
                    const td = inputs[field].parentNode;
                    td.className = 'text-center editable';
                    td.dataset.field = field;
                    td.innerText = body[field];
                    td.addEventListener('dblclick', function () { hanldeDBClick(this); });
                });
                actionTd.innerHTML = `<img class="img mx-1 delete-btn" src="${window.DELETE_IMG_SRC}" alt="Eliminar" style="cursor:pointer;width:20px;" />`;
                bindDeleteBtn(row);
                cancelCurrentEdit = null;
            } else {
                showError('Error: ' + data.message);
            }
        })
        .catch(() => showError('Error al guardar'));
    }

    function cancelNew() {
        row.remove();
        cancelCurrentEdit = null;
    }

    cancelCurrentEdit = cancelNew;

    actionTd.querySelector('.action-confirm').addEventListener('click', confirmNew);
    actionTd.querySelector('.action-cancel').addEventListener('click', cancelNew);

    Object.values(inputs).forEach(input => {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter') confirmNew();
            if (e.key === 'Escape') cancelNew();
        });
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function show_loading() {
    Swal.fire({
        icon: 'info',
        title: 'Cargando',
        text: 'Por favor espera...',
        showConfirmButton: false,
        allowOutsideClick: false,
    })
}

document.addEventListener('DOMContentLoaded', () => {
    setEventDblclick();
    document.querySelectorAll('tr[data-id]').forEach(row => bindDeleteBtn(row));

    document.getElementById('add-product-btn').addEventListener('click', () => {
        addNewRow(document.getElementById('products-tbody'), 'product');
    });
    document.getElementById('add-kit-btn').addEventListener('click', () => {
        addNewRow(document.getElementById('kits-tbody'), 'kit');
    });

    document.getElementById('kits-tbody').addEventListener('click', e => {
        const btn = e.target.closest('.add-kit-item-btn');
        if (!btn) return;
        const kitnumber = btn.dataset.kitnumber;
        const kitRows = document.querySelectorAll(`.kit-row[data-kitnumber="${kitnumber}"]`);
        const headerRow = btn.closest('tr');

        // Expandir el acordeón si está cerrado
        const toggle = headerRow.querySelector('.accordion-toggle');
        if (toggle && toggle.dataset.expanded !== 'true') {
            toggle.click();
        }

        // Insertar después del último item del kit, o después del header si no hay items
        const insertAfter = kitRows.length > 0 ? kitRows[kitRows.length - 1] : headerRow;
        addNewRow(document.getElementById('kits-tbody'), 'kit', {
            prefill: { kitnumber },
            insertAfter,
        });
    });
});
