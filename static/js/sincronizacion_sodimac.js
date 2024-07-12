document.getElementById('download-template').addEventListener('click', (event) => {
  event.preventDefault()
  location.href = "/products/download/3";
})

document.getElementsByTagName('form')[0].addEventListener('submit', function (e) {
  e.preventDefault();
  console.log('si')
  // Obtener el archivo del input
  var fileInput = document.getElementsByName('file')[0]
  var file = fileInput.files[0];

  // Crear un objeto FormData
  var formData = new FormData();
  formData.append('file', file);
  show_loading()
  // Enviar el archivo con $.ajax
  $.ajax({
    url: 'upload',
    type: 'POST',
    data: formData,
    processData: false, // Evitar que jQuery procese los datos
    contentType: false, // Evitar que jQuery establezca el contentType
    headers: {
      'X-CSRFToken': getCookie('csrftoken')  // Incluye el token CSRF en la solicitud
    }, success: function (response) {
      if (response.success) {
        Swal.fire({
          icon: "success",
          title: 'Proceso Exitoso',
          text: response.message,
          showConfirmButton: false,
          allowOutsideClick: false,
          timer: 2000
        })
        setTimeout(function () {
          location.href = "/pamo_bots/manager_database";
        }, 2000);
        location.href = "/products/download/2"
      }
      else {
        Swal.fire({
          icon: "error",
          title: 'Error',
          text: response.message,
          showConfirmButton: false,
          allowOutsideClick: false,
          timer: 2000
        })
      }
    },
    error: function (jqXHR, textStatus, errorThrown) {
      console.error('Error al subir el archivo:', textStatus, errorThrown);
    }
  });
});


function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}