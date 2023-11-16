console.log('si ser')
function deleteElement(id){
    select = document.getElementById(id)
    var opcionSeleccionada = select.options[select.selectedIndex];
    console.log(opcionSeleccionada)
}