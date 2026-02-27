/**
 * Script para extraer partidos de fútbol en vivo de Bet365.
 * Basado en la estructura .ovm-CompetitionList -> .ovm-Fixture
 */
(elements) => {
    const results = [];
    
    // Buscamos todas las secciones de competición
    const competitionSections = document.querySelectorAll('.ovm-Competition');
    
    competitionSections.forEach(section => {
        // Extraemos el nombre de la competición (ej: "Argelia - Ligue 2")
        const competitionName = section.querySelector('.ovm-CompetitionHeader_NameText')?.innerText?.trim() || "Desconocida";
        
        // Buscamos los partidos dentro de esta competición
        const matches = section.querySelectorAll('.ovm-Fixture');
        
        matches.forEach(match => {
            try {
                // Equipos
                const teamElements = match.querySelectorAll('.ovm-FixtureDetailsTwoWay_TeamName');
                const home_team = teamElements[0]?.innerText?.trim();
                const away_team = teamElements[1]?.innerText?.trim();
                
                if (!home_team || !away_team) return;

                // Marcador (Scores)
                const scoreElements = match.querySelectorAll('.ovm-FixtureDetailsTwoWay_Score');
                const score_home = parseInt(scoreElements[0]?.innerText) || 0;
                const score_away = parseInt(scoreElements[1]?.innerText) || 0;

                // Minuto / Tiempo
                const timerText = match.querySelector('.ovm-FixtureDetailsTwoWay_Timer')?.innerText?.trim() || "";
                // Limpiamos el minuto (ej: "45:00" -> 45)
                const minute = parseInt(timerText.split(':')[0]) || null;

                // URL del partido (si existe un link directo)
                const match_url = match.querySelector('a')?.href || null;

                results.push({
                    home_team,
                    away_team,
                    score_home,
                    score_away,
                    minute,
                    competition: competitionName,
                    match_url
                });
            } catch (err) {
                console.error("Error procesando partido en Bet365:", err);
            }
        });
    });
    
    return results;
}
