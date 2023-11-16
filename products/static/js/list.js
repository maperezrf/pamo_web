btnUpdate = document.getElementById('update')
btnUpdate.addEventListener("click", function(){
    confirmation('2')
}) 


function confirmation (changes){
    Swal.fire({
    title: "Estás seguro de actualizar estos datos?",
    // text: 'Se realizaran '+ changes + ' cambios',
    showDenyButton: true,
    showCancelButton: false,
    confirmButtonText: "Aceptar",
    denyButtonText: "Cancelar"
  }).then((result) => {
    if (result.isConfirmed) {
        show_loading();
        $.ajax({
            url: "update_products",
        success: function(response) {
            console.log(response['not_successful'])
            Swal.close()
            Swal.fire({
                title: "Informe proceso",
                html: "<div> <label>Registros Modificados satisfactoriamente: " + response['success'] + " </label> <label>SKUS no modificados: " +  response['not_successful'] + " </label> </div>",
                icon: "success"
              });
        }
        })
    } else if (result.isDenied) {
      Swal.fire("No se realizaron cambios", "", "info");
    }
  })}
