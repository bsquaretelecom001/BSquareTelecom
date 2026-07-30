window.addEventListener("load", function () {

    const loader = document.getElementById("preloader");

    if (loader) {

        setTimeout(function () {

            loader.classList.add("hide");

        }, 800);

    }

});