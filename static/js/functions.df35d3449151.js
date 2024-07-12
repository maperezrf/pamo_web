function formatNumber(number) {
    return (number).toLocaleString('es-CO', {
      style: 'currency',
      currency: 'COP'
    }).replace(/,\d{2}/g, '');
  }

function show_loading(){
  Swal.fire({
      icon: 'info',
      title: 'Cargando',
      text: 'Por favor espera...',
      showConfirmButton: false,
      allowOutsideClick: false,
  })
}

function show_success(msj = None){
  Swal.fire({
      icon: "success",
      title: 'Proceso Exitoso',
      text: msj,
      showConfirmButton: false,
      allowOutsideClick: false,
      timer: 1000
  })
}
