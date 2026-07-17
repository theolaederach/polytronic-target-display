function refreshTargetImage() {
    const imgElement = document.querySelector('.target');

    if (!imgElement) {
        console.warn('Element .target non trouvé');
        return;
    }

    const targetNumber = 1;
    const timestamp = Date.now();
    const refreshUrl = `/api/render_target?target_number=${targetNumber}&_=${timestamp}`;
    const imageUrl = `/static/target${targetNumber}.png?_=${timestamp}`;

    fetch(refreshUrl, { cache: 'no-store' })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur serveur: ' + response.status);
            }
            return response.text();
        })
        .then(() => {
            imgElement.src = imageUrl;
        })
        .catch(error => {
            console.error('Échec du rafraîchissement:', error);
        });
}

refreshTargetImage();
setInterval(refreshTargetImage, 5000);
