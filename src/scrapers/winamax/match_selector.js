/**
 * Selector de partidos para Winamax.
 * Extrae información básica de fútbol usando anclajes estructurales robustos.
 * 
 * @param {HTMLElement[]} cards - Lista de elementos que coinciden con el selector match-card.
 * @returns {Array} Lista de objetos con la información del partido.
 */
(cards) => {
    return cards.map(card => {
        // 1. Equipos: Buscamos las imágenes (logos) de los equipos
        const icons = Array.from(card.querySelectorAll('img[src*="/icons/"]'));
        if (icons.length < 3) return null;

        const getTeamName = (img) => {
            const parent = img.closest('div');
            return parent.parentElement.innerText.trim();
        };

        const homeTeam = getTeamName(icons[1]);
        const awayTeam = getTeamName(icons[2]);

        // 2. Marcador e Indicador Live
        const liveIndicator = card.querySelector('[data-testid="live-indicator"]');
        if (!liveIndicator) return null;

        // 3. Tiempo (formato MM:SS)
        const cardText = card.innerText;
        const timeMatch = cardText.match(/(\d{1,2}):(\d{2})/);
        const minute = timeMatch ? parseInt(timeMatch[1]) : null;

        // 4. Goles
        let scoreHome = 0;
        let scoreAway = 0;
        
        // Buscamos el contenedor de marcador más cercano al indicador live
        const scoreContainer = liveIndicator.closest('div').parentElement;
        const localScores = Array.from(scoreContainer.querySelectorAll('div, span'))
            .map(el => el.innerText.trim())
            .filter(t => /^\d+$/.test(t));

        if (localScores.length >= 2) {
            scoreHome = parseInt(localScores[0]);
            scoreAway = parseInt(localScores[localScores.length - 1]);
        }

        const matchId = card.getAttribute('data-testid').replace('match-card-', '');
        const matchUrl = `https://www.winamax.es/apuestas-deportivas/match/${matchId}`;

        return {
            home_team: homeTeam,
            away_team: awayTeam,
            score_home: scoreHome,
            score_away: scoreAway,
            minute: minute,
            match_url: matchUrl
        };
    }).filter(m => m !== null);
}
