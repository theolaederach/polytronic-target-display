function refreshTargetImage() {
    const imgElement = document.querySelector('.target');

    if (!imgElement) {
        console.warn('Element .target non trouvé');
        return;
    }

    // Conserver l'ancienne src (pour restauration en cas d'erreur)
    const previousSrc = imgElement.src || null;

    // Ajout d'un timestamp pour éviter le cache navigateur
    const url = '/api/render_target?target_number=1&_=' + Date.now();

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur serveur: ' + response.status);
            }
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.startsWith('image/')) {
                return response.text().then(text => {
                    throw new Error('Réponse non-image (' + contentType + '): ' + text.slice(0, 200));
                });
            }
            return response.blob();
        })
        .then(blob => {
            if (!blob || blob.size === 0) {
                throw new Error('Blob d\'image vide');
            }

            const newObjectURL = URL.createObjectURL(blob);

            // Attacher des handlers pour gérer le succès / échec de chargement
            function onLoad() {
                // Après chargement réussi, révoquer l'ancienne blob URL si elle existait
                if (previousSrc && previousSrc.startsWith('blob:') && previousSrc !== newObjectURL) {
                    try { URL.revokeObjectURL(previousSrc); } catch (e) { /* ignore */ }
                }
                imgElement.removeEventListener('load', onLoad);
                imgElement.removeEventListener('error', onError);
            }

            function onError() {
                // Si l'image ne charge pas, révoquer la nouvelle URL et restaurer l'ancienne src si possible
                try { URL.revokeObjectURL(newObjectURL); } catch (e) { /* ignore */ }
                if (previousSrc) {
                    imgElement.src = previousSrc;
                } else {
                    imgElement.removeAttribute('src');
                }
                imgElement.removeEventListener('load', onLoad);
                imgElement.removeEventListener('error', onError);
                console.error('Échec du chargement de l\'image depuis le blob');
            }

            imgElement.addEventListener('load', onLoad);
            imgElement.addEventListener('error', onError);

            // Déclencher le changement de source
            imgElement.src = newObjectURL;
        })
        .catch(error => {
            console.error('Échec du rafraîchissement:', error);
            // En cas d'erreur de fetch/parse, ne pas enlever l'ancienne image
        });
}

// Lancement immédiat
refreshTargetImage();

// Rafraîchissement toutes les 5 secondes
setInterval(refreshTargetImage, 5000);