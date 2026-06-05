let model;
let maxPredictions;
let labelContainer;
let video;

let lockedCard = "";
let possibleCard = "";
let steadyCount = 0;
let isConfirming = false;

const MODEL_URL = "/static/model/";
const CONFIDENCE_NEEDED = 0.92;
const STEADY_SCANS_NEEDED = 8;

function fixCardName(name) {
    const fixes = {
        "Pumkaboo": "Pumpkaboo"
    };

    return fixes[name] || name;
}

async function init() {
    const startBtn = document.getElementById("start-btn");
    const webcamContainer = document.getElementById("webcam-container");

    startBtn.disabled = true;
    startBtn.innerText = "Loading model...";

    try {
        const modelURL = MODEL_URL + "model.json";
        const metadataURL = MODEL_URL + "metadata.json";

        model = await tmImage.load(modelURL, metadataURL);
        maxPredictions = model.getTotalClasses();

        startBtn.innerText = "Starting camera...";

        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        video = document.createElement("video");
        video.srcObject = stream;
        video.autoplay = true;
        video.playsInline = true;
        video.muted = true;
        video.width = 300;
        video.height = 300;

        webcamContainer.innerHTML = "";
        webcamContainer.appendChild(video);

        labelContainer = document.getElementById("label-container");
        labelContainer.innerHTML = "";

        for (let i = 0; i < maxPredictions; i++) {
            const row = document.createElement("div");
            row.className = "prediction-row";
            row.innerHTML = `
                <div class="prediction-top">
                    <span class="prediction-name">Loading...</span>
                    <strong class="prediction-percent">0%</strong>
                </div>
                <div class="bar-bg">
                    <div class="bar-fill" style="width: 0%;"></div>
                </div>
            `;
            labelContainer.appendChild(row);
        }

        startBtn.innerText = "Scanner Running";
        loop();

    } catch (error) {
        console.error(error);
        startBtn.disabled = false;
        startBtn.innerText = "Start Scanner";
        document.getElementById("best-result").innerText =
            "Camera/model error: " + error.message;
    }
}

async function loop() {
    if (video && video.readyState === 4 && !isConfirming) {
        await predict();
    }

    requestAnimationFrame(loop);
}

async function predict() {
    const predictions = await model.predict(video);

    predictions.sort((a, b) => b.probability - a.probability);
    updatePredictionBars(predictions);

    const bestPrediction = predictions[0];
    const bestResult = document.getElementById("best-result");

    if (bestPrediction.className === "None" || bestPrediction.probability < CONFIDENCE_NEEDED) {
        bestResult.innerText = "Card not recognised. Hold it closer and steady.";
        possibleCard = "";
        steadyCount = 0;
        return;
    }

    const cardName = bestPrediction.className;
    const confidence = Math.round(bestPrediction.probability * 100);

    bestResult.innerText = `Scanning... possible card: ${formatCardName(cardName)} (${confidence}%)`;

    if (possibleCard === cardName) {
        steadyCount++;
    } else {
        possibleCard = cardName;
        steadyCount = 1;
    }

    if (steadyCount >= STEADY_SCANS_NEEDED) {
        isConfirming = true;
        lockedCard = cardName;

        document.getElementById("confirm-box").classList.remove("hidden");
        document.getElementById("confirm-text").innerText =
            `I think this is ${formatCardName(cardName)}. Is this correct?`;

        bestResult.innerText = `Detected: ${formatCardName(cardName)} (${confidence}%)`;
        await loadCardDetails(cardName);
    }
}

function updatePredictionBars(predictions) {
    for (let i = 0; i < predictions.length; i++) {
        const percent = Math.round(predictions[i].probability * 100);
        const row = labelContainer.childNodes[i];

        row.querySelector(".prediction-name").innerText = formatCardName(predictions[i].className);
        row.querySelector(".prediction-percent").innerText = `${percent}%`;
        row.querySelector(".bar-fill").style.width = `${percent}%`;

        if (i === 0) {
            row.classList.add("top-prediction");
        } else {
            row.classList.remove("top-prediction");
        }
    }
}

async function confirmCard() {
    document.getElementById("confirm-box").classList.add("hidden");

    console.log("Saving card:", lockedCard);

    saveToCollection(lockedCard);

    document.getElementById("best-result").innerText =
        `${formatCardName(lockedCard)} confirmed and added to your collection!`;

    await loadCardDetails(lockedCard);

    resetScannerState();
}

function rejectCard() {
    document.getElementById("confirm-box").classList.add("hidden");
    document.getElementById("card-details").classList.add("hidden");
    document.getElementById("best-result").innerText =
        "Okay, keep scanning. Try moving the card slightly.";

    resetScannerState();
}

function resetScannerState() {
    lockedCard = "";
    possibleCard = "";
    steadyCount = 0;

    setTimeout(() => {
        isConfirming = false;
    }, 1200);
}

async function loadCardDetails(cardId) {
    const response = await fetch(`/api/card/${cardId}`);
    const data = await response.json();

    if (data.success) {
        document.getElementById("card-preview").classList.remove("hidden");

        document.getElementById("preview-image").src =
            `/static/card_images/${data.card.name}.png`;

        document.getElementById("card-name").innerText = data.card.name;
        document.getElementById("card-type").innerText = data.card.type;
        document.getElementById("card-rarity").innerText = data.card.rarity;
        document.getElementById("card-value").innerText = data.card.value;
        document.getElementById("card-power").innerText = data.card.power;
        document.getElementById("card-search-link").href = data.card.search_url;
        document.getElementById("card-description").innerText = data.card.description;

        document.getElementById("card-preview").classList.add("preview-pop");

        setTimeout(() => {
            document.getElementById("card-preview").classList.remove("preview-pop");
        }, 600);
    }
}

function formatCardName(name) {
    return name.replaceAll("_", " ");
}

function saveToCollection(cardId) {
    let collection = JSON.parse(localStorage.getItem("collection")) || [];

    let found = false;

    collection = collection.map(card => {
        if (card.id === cardId) {
            found = true;

            return {
                id: card.id,
                name: card.name,
                quantity: Number(card.quantity || 1) + 1,
                date: new Date().toLocaleDateString()
            };
        }

        return {
            id: card.id,
            name: card.name,
            quantity: Number(card.quantity || 1),
            date: card.date
        };
    });

    if (!found) {
        collection.push({
            id: cardId,
            name: formatCardName(cardId),
            quantity: 1,
            date: new Date().toLocaleDateString()
        });
    }

    localStorage.setItem("collection", JSON.stringify(collection));
    console.log("Collection now:", collection);

    displayCollection();
}

function displayCollection() {
    const collection = JSON.parse(localStorage.getItem("collection")) || {};
    const list = document.getElementById("collection-list");
    const empty = document.getElementById("collection-empty");

    list.innerHTML = "";

    const cards = Object.values(collection);

    if (cards.length === 0) {
        empty.style.display = "block";
        return;
    }

    empty.style.display = "none";

    cards.forEach(card => {

        if (!card.status) {
            card.status = "Keep";
        }

        const item = document.createElement("div");
        item.className = "collection-item";

        item.innerHTML = `
            <div class="collection-info">
                <strong>${card.name}</strong>
                <span>Last scanned: ${card.date}</span>
                <span>Quantity: x${card.quantity}</span>

                <select onchange="updateCardStatus('${card.id}', this.value)">
                    <option value="Keep" ${card.status === "Keep" ? "selected" : ""}>Keep</option>
                    <option value="Trade" ${card.status === "Trade" ? "selected" : ""}>Trade</option>
                    <option value="Sell" ${card.status === "Sell" ? "selected" : ""}>Sell</option>
                    <option value="Want" ${card.status === "Want" ? "selected" : ""}>Want</option>
                </select>
            </div>
        `;

        list.appendChild(item);
    });

    localStorage.setItem("collection", JSON.stringify(collection));
}

function updateCardStatus(cardId, status) {
    const collection = JSON.parse(localStorage.getItem("collection")) || {};

    if (collection[cardId]) {
        collection[cardId].status = status;
    }

    localStorage.setItem("collection", JSON.stringify(collection));
}

function scanNextCard() {
    document.getElementById("card-preview").classList.add("hidden");
    document.getElementById("confirm-box").classList.add("hidden");

    document.getElementById("best-result").innerText =
        "Ready for the next card. Hold it close and steady.";

    lockedCard = "";
    possibleCard = "";
    steadyCount = 0;
    isConfirming = false;
}

function saveToCollection(cardId) {
    let collection = JSON.parse(localStorage.getItem("collection")) || {};

    if (collection[cardId]) {
        collection[cardId].quantity += 1;
        collection[cardId].date = new Date().toLocaleDateString();
    } else {
        collection[cardId] = {
            id: cardId,
            name: formatCardName(cardId),
            quantity: 1,
            date: new Date().toLocaleDateString()
        };
    }

    localStorage.setItem("collection", JSON.stringify(collection));
    displayCollection();
}

function displayCollection() {
    const collection = JSON.parse(localStorage.getItem("collection")) || {};
    const list = document.getElementById("collection-list");
    const empty = document.getElementById("collection-empty");

    list.innerHTML = "";

    const cards = Object.values(collection);

    if (cards.length === 0) {
        empty.style.display = "block";
        return;
    }

    empty.style.display = "none";

    cards.forEach(card => {
        const item = document.createElement("div");
        item.className = "collection-item";

        item.innerHTML = `
            <div>
                <strong>${card.name}</strong>
                <span>Last scanned: ${card.date}</span>
            </div>
            <strong>x${card.quantity}</strong>
        `;

        list.appendChild(item);
    });
}

window.addEventListener("load", displayCollection);