window.post = function (url, data) {
    return fetch(url, { method: "POST", headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
}

let lock = false;
let guesses = 0;

function submitGuess() {
    if (lock) return;

    const guess = document.getElementById("guess").value;
    if (guess.length === 0) return;
    appendGuess(guess);

    const spinner = document.getElementById("spinner");
    spinner.style.opacity = "1";
    lock = true;

    window.post(
        '/',
        { code: "greg" }
    ).then(resp => resp.json()).then(data => {
        guesses++;

        // Ignore empty hints (i.e. you've guessed too many times)
        if (data.result.next_hint.length >= 0)
            appendToList("info", data.result.next_hint);
    }).catch(err => {
        console.error(err);
        alert("Error: No connection to server");
    }).finally(() => {
        lock = false;
        spinner.style.opacity = "0";
    });
}

const appendGuess = (guess) => {
    const list = document.getElementById("guesses");
    if (guesses == 0) list.innerHTML = "";
    appendToList("guesses", guess);
}

const appendToList = (id, text) => {
    const list = document.getElementById(id);
    const li = document.createElement("li");
    li.innerText = text;
    list.appendChild(li);
}

const showLightbox = (id) => {
    window.location.replace(`#${id}`);
}