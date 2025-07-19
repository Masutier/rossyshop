function theDate() {
    // Get date in formats
    let myDate = new Date();
    let myDay = myDate.getDay();
    let myToDay = String(myDate.getDate()).padStart(2, '0');
    let myMonth = myDate.getMonth();
    let myYear = myDate.getFullYear();

    // Array of days. 
    let weekday = ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'];
    let month = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    // Display date. 
    document.getElementById("dateHere").innerHTML = weekday[myDay] + ", " + myToDay + " de " + month[myMonth] + " " + myYear;
}
theDate();
