const SVG_NS = "http://www.w3.org/2000/svg";

// Fonction de conversion : Mètres -> Pixels SVG
function metersToSvg(xMeters, yMeters, svgSizePx = 1024, targetSizeM = 1.0) {
  const center = svgSizePx / 2;
  const scale = svgSizePx / targetSizeM; // 1024 px par mètre

  return {
    x: center + xMeters * scale,
    y: center - yMeters * scale, // Inversion de l'axe Y (le Y mathématique monte, le Y du SVG descend)
  };
}

async function loadAndDrawShots() {
  try {
    // 1. Exemple de données reçues de l'API (en mètres)
    const response = await fetch("/api/shots");
    const shots = await response.json();
    /*
        Exemple de JSON reçu :
        [
            { "x": 0.012, "y": -0.344, "number": 1 },
            { "x": -0.150, "y": 0.200, "number": 2 }
        ]
        */

    const svg = document.getElementById("target-svg");
    const size = 15;
    const thickness = 4;
    const color = "rgba(255, 0, 0, 0.7)";

    shots.forEach((shot) => {
      // Conversion des coordonnées (mètres -> SVG)
      const coords = metersToSvg(shot.x, shot.y);
      const x = coords.x;
      const y = coords.y;

      // Ligne horizontale
      const lineH = document.createElementNS(SVG_NS, "line");
      lineH.setAttribute("x1", x - size);
      lineH.setAttribute("y1", y);
      lineH.setAttribute("x2", x + size);
      lineH.setAttribute("y2", y);
      lineH.setAttribute("stroke", color);
      lineH.setAttribute("stroke-width", thickness);

      // Ligne verticale
      const lineV = document.createElementNS(SVG_NS, "line");
      lineV.setAttribute("x1", x);
      lineV.setAttribute("y1", y - size);
      lineV.setAttribute("x2", x);
      lineV.setAttribute("y2", y + size);
      lineV.setAttribute("stroke", color);
      lineV.setAttribute("stroke-width", thickness);

      // Numéro du tir
      const text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", x + size + 4);
      text.setAttribute("y", y + 4);
      text.setAttribute("fill", color);
      text.classList.add("shot-number");
      text.textContent = shot.number;

      svg.appendChild(lineH);
      svg.appendChild(lineV);
      svg.appendChild(text);
    });
  } catch (error) {
    console.error("Erreur lors du chargement des tirs :", error);
  }
}

document.addEventListener("DOMContentLoaded", loadAndDrawShots);
