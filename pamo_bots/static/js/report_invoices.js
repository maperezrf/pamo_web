function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
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

function show_success(msj) {
  Swal.fire({
    icon: 'success',
    title: 'Proceso Exitoso',
    text: msj || '',
    showConfirmButton: false,
    allowOutsideClick: false,
    timer: 1500,
  })
}

function show_error(msj) {
  Swal.fire({
    icon: 'error',
    title: 'Error',
    text: msj || 'Ocurrió un error inesperado.',
    showConfirmButton: true,
  })
}

document.addEventListener('DOMContentLoaded', function () {
  const syncBtn = document.getElementById('sync-invoices-btn')
  if (!syncBtn) return

  syncBtn.addEventListener('click', async function () {
    show_loading()
    try {
      const resp = await fetch(syncBtn.dataset.url, {
        method: 'GET',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      })
      const data = await resp.json()
      if (data.success) {
        show_success('Facturas sincronizadas correctamente.')
        setTimeout(() => location.reload(), 1500)
      } else {
        show_error(data.message || 'Error desconocido.')
      }
    } catch (err) {
      show_error('Error de red al sincronizar.')
    }
  })
})
