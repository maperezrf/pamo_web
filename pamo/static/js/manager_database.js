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
            if (event.keyCode === 13 || event.key === 'Enter') {
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