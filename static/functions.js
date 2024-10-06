function showAlert(message) {
    if (message) {
        alert(message);
    }
}

function getQuote() {
    fetch("/quote")
        .then(response => {
            if (!response.ok) {
                throw new Error("Error fetching quote");
            }
            return response.json();
        })
        .then(data => {
            document.getElementById("quote").innerText = data.quote;
            document.getElementById("author").innerText = data.author;
            const heartButton = document.querySelector(".heart-button");
            heartButton.classList.remove("active");
        })
        .catch(error => {
            document.getElementById("quote").innerText = "Couldn't fetch quote.";
            document.getElementById("author").innerText = "";
            console.error(error);
        })
}

function toggleFavorite(isActive) {
    const quoteText = document.getElementById("quote").textContent;
    const authorText = document.getElementById("author").textContent;
    const heartButton = document.querySelector(".heart-button");
    
    if (isActive) {
        heartButton.classList.add("active")
        console.log("Heart is clicked!");
    } else {
        heartButton.classList.remove("active");
        console.log("Heart is unclicked!");
    }
    fetch("/toggle_favorite", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            quote: quoteText,
            author: authorText,
            action: isActive ? "add" : "remove"
        })
    })
    .then(response => {
        if (!response.ok) {
            heartButton.classList.toggle("active");
            console.error("Failed to toggle favorite.");
        }
    })
}

function handleHeartButtonClick() {
    const heartButton = document.querySelector(".heart-button")
    const isActive = heartButton.classList.contains("active")
    toggleFavorite(!isActive);
}

function escapeSelector(string) {
    // Remove backslashes before escaping special characters
    const cleanedString = string.replace(/\\/g, ''); // Remove all backslashes
    return cleanedString.replace(/([!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~])/g, '\\$1'); // Escape special characters
}

function removeFavorite(favoriteData, buttonId) {
    const qText = favoriteData.quote; // Destructure to get quote
    const aText = favoriteData.author;
    console.log("Quote being sent for removal:", qText);
    console.log("Author being sent for removal:", aText);

    fetch("/toggle_favorite", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            quote: qText,
            author: aText,
            action: "remove" // Always removing since this button is for removal
        })
    })
    
    .then(response => {
        if (response.ok) {
            console.log("Favorite removed successfully.");
            // Remove the card from the DOM
            const cardElement = document.getElementById(buttonId).closest('.col');
            if (cardElement) {
                cardElement.remove();
                console.log("Card removed from the DOM.");
            } else {
                console.error("Card not found in the DOM.");
            }
        } else {
            console.error("Failed to remove favorite.");
        }
    });
    
    
}