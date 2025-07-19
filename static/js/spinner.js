var spin = document.getElementById("spin");
var noSpin = document.getElementById("noSpin");
var button = document.getElementById("butSpin");

spin.style.display = "none";

button.onclick = () => {
    spin.style.display = "block";
    noSpin.style.display = "none";
    };

