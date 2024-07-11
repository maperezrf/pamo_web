function hanldeDBClick(element) {
    value = element.innerText
    inputDiv = document.createElement('div');
    input = document.createElement('input');
    input.type = 'number'
    input.value = value
    input.classList.add('input-stock', 'form-control');
    element.innerText = ''
    inputDiv.appendChild(input)
    element.appendChild(inputDiv)
    input.focus()
}

function setValueInput() {
    document.body.addEventListener('click', (event) => {
        inputs = document.getElementsByClassName('input-stock')
        if (inputs.length > 0) {
            inputs = document.getElementsByClassName('input-stock')
            if ( ! event.target.contains(input)) {
                elements = Array.from(inputs)
                console.log('inputs')
                entryValue(elements)
            }
        }
    })
}

const observer = new MutationObserver(mutationCallback);
const option = {
    childList: true,
    subtree: true
};
target = document.getElementById('dbSodimac')
observer.observe(target, option);


function mutationCallback() {
    const inputElements = document.querySelectorAll('input');
    inputElements.forEach((element) => {
        element.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                entryValue([element])
            }
        });
    })
}

function entryValue(elements) {
    console.log(elements)
    elements.forEach((element) => {
        cel = element.parentNode.parentNode
        if (!element.value.includes(".") && (element.value != '')) {
            cel.removeChild(element.parentNode)
            cel.innerText = parseInt(element.value)
        } else {
            if (!document.getElementById('errormessage')) {
                errorMessage = document.createElement('p')
                errorMessage.id = 'errormessage'
                errorMessage.innerText = "El valor ingresado no es correcto"
                errorMessage.classList.add('error-message')
                cel.appendChild(errorMessage)
            }
        }
    })
}

function get_inventory() {
    const linksElements = document.querySelectorAll('.get-inventory-link')
    linksElements.forEach((element) => {
        element.addEventListener('click', function (event) {
            event.preventDefault()
            console.log(element.id)
            show_loading()
            $.ajax({
                url: 'get_inventory',
                type: 'POST',
                data: JSON.stringify({ 'products': [element.parentNode.parentNode.id] }),
                contentType: 'application/json',
                dataType: 'json',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')  // Incluye el token CSRF en la solicitud
                },
                success: function (response) {
                    if (response.success) {
                        console.log(response.message)
                        Swal.fire({
                            icon: "success",
                            title: 'Proceso Exitoso',
                            text: response.message,
                            showConfirmButton: false,
                            allowOutsideClick: false,
                            timer: 2000
                        })
                        setTimeout(function () {
                            location.reload();
                        }, 2000);
                    }
                    else {
                        console.log(response.message)
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
                error: function (response) {
                    console.log(response)
                }
            })
        })
    })
}

function set_inventory() {
    const linksElements = document.querySelectorAll('.set-inventory-link')
    linksElements.forEach((element) => {
        element.addEventListener('click', function (event) {
            event.preventDefault()
            stockToSet = element.parentNode.parentNode.parentNode.getElementsByClassName('stock-to-set')[0].innerText
            sku = element.parentNode.parentNode.parentNode.getElementsByClassName('sku')[0].innerText
            id = element.parentNode.parentNode.id
            show_loading()
            $.ajax({
                url: 'set_inventory',
                type: 'POST',
                data: JSON.stringify({ 'product': id, 'stock': stockToSet, 'sku': sku }),
                contentType: 'application/json',
                dataType: 'json',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')  // Incluye el token CSRF en la solicitud
                },
                success: function (response) {
                    if (response.success) {
                        console.log(response.message)
                        Swal.fire({
                            icon: "success",
                            title: 'Proceso Exitoso',
                            text: response.message,
                            showConfirmButton: false,
                            allowOutsideClick: false,
                            timer: 2000
                        })
                        setTimeout(function () {
                            location.reload();
                        }, 2000);
                    }
                    else {
                        console.log(response.message)
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
                error: function (response) {
                    console.log(response)
                }
            })
        })
    })
}


document.addEventListener('DOMContentLoaded', (event) => {
    get_inventory()
    set_inventory()
    setValueInput()
})


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

function show_loading(){
    Swal.fire({
        icon: 'info',
        title: 'Cargando',
        text: 'Por favor espera...',
        showConfirmButton: false,
        allowOutsideClick: false,
    })
  }