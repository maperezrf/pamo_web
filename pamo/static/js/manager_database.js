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

const observer = new MutationObserver(mutationCallback);
const option = {
    childList: true,
    subtree: true
};
target = document.getElementById('dbSodimac')
observer.observe(target, option);


function mutationCallback() {
    const inputElements = document.querySelectorAll('input'); // Select all 'input' elements
    inputElements.forEach((element) => {
        element.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                console.log(element.value != '')
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
            }
        });
    })
}

function get_inventory() {
    const linksElements = document.querySelectorAll('.get-inventory-link')
    linksElements.forEach((element) => {
        element.addEventListener('click', function (event) {
            console.log(element.id)
            $.ajax({
                url: 'get_inventory',
                type: 'POST',
                data: JSON.stringify({'products': [element.id]}),
                contentType: 'application/json',
                dataType: 'json',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')  // Incluye el token CSRF en la solicitud
                },
                success: function (response) {
                    console.log(response)
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