// Title : update targets loop
// Author : Euria (Infomaniak AI)
// Last update : 2026-09-17
// Description : Fetch shots for each target every second and draw crosshairs.

const SVG_NS = "http://www.w3.org/2000/svg";
const API_BASE_URL = "/api/shots";
const REFRESH_INTERVAL = 2000; // 1 seconde

// Configuration graphique
const CONFIG = {
  svgSize: 1024,
  targetSizeM: 1.0, // Taille réelle de la cible en mètres
  crossSize: 22,    // Taille des bras de la croix
  strokeWidth: 8,
  colors: {
    base: "255, 0, 0", // Rouge
    lastShot: "rgba(0, 170, 255, 1)", // Bleu pour le dernier tir
    minOpacity: 0.40
  }
};

/**
 * Convertit les coordonnées réelles (mètres) en coordonnées SVG (pixels)
 */
function metersToSvg(xMeters, yMeters) {
  const center = CONFIG.svgSize / 2;
  const scale = CONFIG.svgSize / CONFIG.targetSizeM;

  return {
    x: center + xMeters * scale,
    y: center - yMeters * scale // Inversion de l'axe Y
  };
}

/**
 * Efface les anciens tirs d'un SVG donné
 */
function clearSvg(svgElement) {
  if (!svgElement) return;
  // On sélectionne tous les éléments créés par le script (lines et texts)
  // On peut utiliser une classe ou simplement supprimer tout ce qui n'est pas l'image de fond
  const elementsToRemove = svgElement.querySelectorAll("line, text.shot-number");
  elementsToRemove.forEach(el => el.remove());
}

/**
 * Dessine les tirs sur un SVG spécifique
 */
function drawShotsOnSvg(svgElement, shots) {
  if (!svgElement || !shots) return;

  // 1. Nettoyer l'ancien dessin
  clearSvg(svgElement);

  // 2. Dessiner les nouveaux tirs
  shots.forEach((shot, index) => {
    const coords = metersToSvg(shot.x, shot.y);
    const x = coords.x;
    const y = coords.y;

    // Détermination de la couleur
    // Le premier élément du tableau (index 0) est le tir le plus récent (selon votre exemple JSON)
    let color;
    if (index === 0) {
      color = CONFIG.colors.lastShot;
    } else {
      let opacity = 1.0 - (index * 0.1); // Réduit l'opacité de 10% par tir ancien
      if (opacity < CONFIG.colors.minOpacity) opacity = CONFIG.colors.minOpacity;
      color = `rgba(${CONFIG.colors.base}, ${opacity})`;
    }

    // Création de la ligne horizontale
    const lineH = document.createElementNS(SVG_NS, "line");
    lineH.setAttribute("x1", x - CONFIG.crossSize);
    lineH.setAttribute("y1", y);
    lineH.setAttribute("x2", x + CONFIG.crossSize);
    lineH.setAttribute("y2", y);
    lineH.setAttribute("stroke", color);
    lineH.setAttribute("stroke-width", CONFIG.strokeWidth);

    // Création de la ligne verticale
    const lineV = document.createElementNS(SVG_NS, "line");
    lineV.setAttribute("x1", x);
    lineV.setAttribute("y1", y - CONFIG.crossSize);
    lineV.setAttribute("x2", x);
    lineV.setAttribute("y2", y + CONFIG.crossSize);
    lineV.setAttribute("stroke", color);
    lineV.setAttribute("stroke-width", CONFIG.strokeWidth);

    // Création du numéro
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", x + CONFIG.crossSize + 5);
    text.setAttribute("y", y + 5);
    text.setAttribute("fill", color);
    text.setAttribute("font-size", "24");
    text.setAttribute("font-family", "Arial, sans-serif");
    text.classList.add("shot-number");
    text.textContent = shot.number;

    // Ajout au DOM
    svgElement.appendChild(lineH);
    svgElement.appendChild(lineV);
    svgElement.appendChild(text);
  });
}

/**
 * Récupère les données pour une cible spécifique et met à jour son SVG
 * @param {string} targetId - L'identifiant de la cible (ex: "1", "2", "other")
 * @param {HTMLElement} svgElement - L'élément SVG DOM à mettre à jour
 */
async function updateTarget(targetId, svgElement) {
  try {
    // Construction de l'URL avec le paramètre target
    // Si targetId est "other", on peut décider d'envoyer "other" ou un numéro spécifique selon votre API
    const url = `${API_BASE_URL}?target=${targetId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) {
      // Si l'API renvoie une erreur (ex: 404), on nettoie juste et on arrête pour cette cible
      if (response.status !== 404) {
        console.warn(`Erreur API pour la cible ${targetId}: ${response.status}`);
      }
      return;
    }

    const shots = await response.json();
    drawShotsOnSvg(svgElement, shots);

  } catch (error) {
    console.error(`Erreur lors de la mise à jour de la cible ${targetId} :`, error);
  }
}

/**
 * Fonction principale lancée toutes les secondes
 */
function refreshAllTargets() {
  // Liste des cibles à mettre à jour
  // On cible les classes .target1, .target2... et .other
  const targetSelectors = [
    { id: "1", selector: ".target1" },
    { id: "2", selector: ".target2" },
    { id: "3", selector: ".target3" },
    { id: "4", selector: ".target4" },
    { id: "5", selector: ".target5" },
    { id: "other", selector: ".other" }
  ];

  targetSelectors.forEach(item => {
    const container = document.querySelector(item.selector);
    if (container) {
      // On cherche le SVG à l'intérieur de ce conteneur
      const svgElement = container.querySelector("svg");
      if (svgElement) {
        updateTarget(item.id, svgElement);
      } else {
        console.warn(`SVG non trouvé dans le conteneur ${item.selector}`);
      }
    }
  });
}

// Démarrage
document.addEventListener("DOMContentLoaded", () => {
  // Premier chargement immédiat
  refreshAllTargets();

  // Puis rafraîchissement toutes les secondes
  setInterval(refreshAllTargets, REFRESH_INTERVAL);

  console.log("Système de mise à jour des cibles démarré (1s interval)");
});
