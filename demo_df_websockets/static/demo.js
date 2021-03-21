function checkAddedText(evt) {
    evt.target.querySelectorAll(
        "i"
    ).forEach(elt => {
        if (elt.classList.contains("original")) {
            elt.classList.add("fail");
        } else {
            elt.classList.add("success");
        }
    })
}

document.addEventListener("DOMContentAdded", checkAddedText);
