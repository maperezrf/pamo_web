btnUpdate = document.getElementById('update')
btnUpdate.addEventListener("click", function(){
    confirmation()
}) 


function confirmation (){
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
            if (response.success){
              text_success = "<div> <label>Registros Modificados satisfactoriamente: " + response['element_success']
              text_successfull = (response['not_successful'].length === 0 ) ? "" : "</label> <label>SKUS no modificados: " +  response['not_successful'].join(', ') + " </label> </div>"
              Swal.fire({
                title: "Informe proceso",
                html: text_success + text_successfull,
                icon: "success"
              });

            }
            else{
              Swal.fire({
                icon: "error",
                title: "¡Ocurrio un error al tratar de actualizar los datos!",
              });
            }
        }
        })
    } else if (result.isDenied) {
      Swal.fire("No se realizaron cambios", "", "info");
    }
  })}
