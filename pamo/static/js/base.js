function show_loading(){
    Swal.fire({
        icon: 'info',
        title: 'Cargando',
        text: 'Por favor espera...',
        showConfirmButton: false,
        allowOutsideClick: false,
    })
  }

  function show_success(){
    Swal.fire({
        icon: "success",
        title: 'Proceso Exitoso',
        showConfirmButton: false,
        allowOutsideClick: false,
        timer: 1000
    })
  }