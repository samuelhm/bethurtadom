/**
 * Selector de partidos para Winamax (Versión Infalible).
 * Extrae información basándose en la estructura del DOM de React Virtualized.
 */
(cards) => {
    return cards.map(card => {
        try {
            // 1. Obtener el ID y la URL (lo más estable)
            const matchId = card.getAttribute('data-testid').replace('match-card-', '');
            const matchUrl = `https://www.winamax.es/apuestas-deportivas/match/${matchId}`;

            // 2. Extraer nombres de equipos
            // Los nombres suelen estar en elementos con la clase que termina en 'eiMoqO' 
            // o simplemente son los textos más largos en la parte izquierda.
            const teamElements = Array.from(card.querySelectorAll('div'))
                .filter(el => el.innerText && el.innerText.length > 2 && !el.querySelector('div'));
            
            // En Winamax, el primer texto largo es el equipo local y el segundo el visitante
            // tras filtrar ruidos como "1", "X", "2" o el tiempo.
            const names = teamElements
                .map(el => el.innerText.trim())
                .filter(text => !/^[0-9xX:]+$/.test(text) && text.length > 2);

            if (names.length < 2) return null;

            const homeTeam = names[0];
            const awayTeam = names[1];

            // 3. Extraer Marcador
            // Buscamos los números que están cerca del live-indicator
            const scoreElements = Array.from(card.querySelectorAll('div'))
                .filter(el => /^\d+$/.test(el.innerText.trim()) && el.innerText.length <= 2);
            
            // Los scores suelen ser los dos primeros números pequeños encontrados
            let scoreHome = 0;
            let scoreAway = 0;
            
            if (scoreElements.length >= 2) {
                scoreHome = parseInt(scoreElements[0].innerText);
                scoreAway = parseInt(scoreElements[1].innerText);
            }

            // 4. Extraer Tiempo (Minuto)
            const timeSpan = card.querySelector('span');
            const timeMatch = card.innerText.match(/(\d{1,2}):(\d{2})/);
            const minute = timeMatch ? parseInt(timeMatch[1]) : null;

            return {
                home_team: homeTeam,
                away_team: awayTeam,
                score_home: scoreHome,
                score_away: scoreAway,
                minute: minute,
                match_url: matchUrl
            };
        } catch (err) {
            return null;
        }
    }).filter(m => m !== null && m.home_team && m.away_team);
}
