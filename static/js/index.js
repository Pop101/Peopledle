window.post = function (url, data) {
    return fetch(url, { method: "POST", headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
}
window.get = function (url) {
    return fetch(url, { method: "GET" });
}

// initialize the carousel(s)
new Glide('.glide').mount();

// Load in the HUGE datalist of names asynchonously
document.addEventListener('DOMContentLoaded', (event) => {
    window.get('/names').then(resp => resp.json()).then(data => {
        const list = document.getElementById("names");
        const fragment = document.createDocumentFragment();
        data.forEach(name => {
            const option = document.createElement("option");
            option.value = name;
            fragment.appendChild(option);
        });
        while (list.firstChild) list.removeChild(list.firstChild);
        list.appendChild(fragment);
    }).catch(err => {
        console.error(err);
        alert("Error: No connection to server");
    });
})

let lock = false;
let game_over = false;
let out_of_guesses = false;
let guesses = 1;

function submitGuess() {
    if (lock || game_over) return;

    const guess = document.getElementById("guess").value;
    if (guess.length === 0) return;
    appendGuess(guess);

    const spinner = document.getElementById("spinner");
    spinner.style.opacity = "1";
    lock = true;

    window.post(
        window.location.pathname,
        { guesses: guesses, guess: guess }
    ).then(resp => resp.json()).then(data => {
        guesses++;

        // If you've guessed correctly, show the lightbox
        if (data.result.correct) {
            showLightbox("correct");
            game_over = true;

            showoverlay("confetti");

        } else {
            // Otherwise, show the next hint
            if (data.result.next_hint.length > 0)
                appendToList("info", data.result.next_hint);
            else {
                if (!out_of_guesses) appendToList("info", "We're out of hints!");
                out_of_guesses = true;
            }

            if (guesses + 1 === 5) showLightbox("lose");

            //... and clear the guess box
            document.getElementById("guess").value = "";
        }
    }).catch(err => {
        console.error(err);
        alert("Error: No connection to server");
    }).finally(() => {
        lock = false;
        spinner.style.opacity = "0";
    });
}

function concede() {
    showLightbox("answer");
    showoverlay("lossoverlay");
    game_over = true;
    document.getElementById("guess").value = answer;
}
const appendGuess = (guess) => {
    const list = document.getElementById("guesses");
    if (guesses == 1) list.innerHTML = "";
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

const showoverlay = (id) => {
    document.getElementById(id).style.display = "block";
    setTimeout(() => document.getElementById(id).style.opacity = "1", 100);
}