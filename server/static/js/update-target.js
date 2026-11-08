// Title : update targets loop
// Author : Euria (Infomaniak AI)
// Last update : 2026-09-17
// Description : Fetch shots for each target every second and draw crosshairs.

const SVG_NS = "http://www.w3.org/2000/svg";
const API_BASE_URL = "/api/shots/targets/all";
const REFRESH_INTERVAL = 2000; // 1 seconde

// Configuration graphique
const CONFIG = {
  svgSize: 1024,
  targetSizeM: 1.0, // Taille réelle de la cible en mètres
  crossSize: 22, // Taille des bras de la croix
  strokeWidth: 8,
  colors: {
    base: "255, 0, 0", // Rouge
    lastShot: "rgba(0, 170, 255, 1)", // Bleu pour le dernier tir
    minOpacity: 0.4,
  },
};

/**
 * Convertit les coordonnées réelles (mètres) en coordonnées SVG (pixels)
 */
function metersToSvg(xMeters, yMeters) {
  const center = CONFIG.svgSize / 2;
  const scale = CONFIG.svgSize / CONFIG.targetSizeM;

  return {
    x: center + xMeters * scale,
    y: center - yMeters * scale, // Inversion de l'axe Y
  };
}

/**
 * Efface les anciens tirs d'un SVG donné
 */
function clearSvg(svgElement) {
  if (!svgElement) return;
  // On sélectionne tous les éléments créés par le script (lines et texts)
  // On peut utiliser une classe ou simplement supprimer tout ce qui n'est pas l'image de fond
  const elementsToRemove = svgElement.querySelectorAll(
    "line, text.shot-number",
  );
  elementsToRemove.forEach((el) => el.remove());
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
      let opacity = 1.0 - index * 0.1; // Réduit l'opacité de 10% par tir ancien
      if (opacity < CONFIG.colors.minOpacity)
        opacity = CONFIG.colors.minOpacity;
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

/**
 * Fonction principale lancée toutes les secondes
 */
async function refreshAllTargets() {
  const url = `${API_BASE_URL}`;
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      console.warn(`Erreur API pour /targets/all : ${response.status}`);
      return;
    }

    const data = await response.json();
    const targetsData = data.targets;

    // Les cibles affichées sont générées par Flask (target_number) :
    // on associe simplement la n-ième cible de l'API au n-ième élément de la page.
    const containers = document.querySelectorAll(".target-container .element");

    targetsData.forEach((targetInfo, idx) => {
      const container = containers[idx];
      if (container) {
        const svgElement = container.querySelector("svg");
        if (svgElement) {
          drawShotsOnSvg(svgElement, targetInfo.shots);
          if (targetInfo.shots && targetInfo.shots.length > 0) {
            const targetType = targetInfo.target_type;
            const image = svgElement.querySelector("image");
            if (image) {
              image.setAttribute(
                "href",
                `/static/assets/target_${targetType}.png`,
              );
            }
          }
        } else {
          console.warn(`SVG non trouvé dans la cible ${idx + 1}`);
        }
      }
    });
  } catch (error) {
    console.error("Erreur lors de la mise à jour des cibles :", error);
  }
}


