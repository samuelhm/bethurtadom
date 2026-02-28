/**
 * Script para extraer partidos de fútbol en vivo de Bet365.
 * Basado en la estructura .ovm-CompetitionList -> .ovm-Fixture
 */
(elements) => {
    const resultsByKey = new Map();

    const parseMinuteFromTimer = (timerText) => {
        const text = (timerText || "").trim();
        if (!text) return null;

        // Formato típico: "45:23" / "00:45"
        const minuteSecondMatch = text.match(/^(\d{1,3}):(\d{1,2})$/);
        if (minuteSecondMatch) {
            const minuteValue = Number.parseInt(minuteSecondMatch[1], 10);
            return Number.isNaN(minuteValue) ? null : minuteValue;
        }

        // Formato tiempo añadido: "45+2" o "45+2'"
        const addedTimeMatch = text.match(/^(\d{1,3})\s*\+\s*(\d{1,2})/);
        if (addedTimeMatch) {
            const baseMinute = Number.parseInt(addedTimeMatch[1], 10);
            const extraMinute = Number.parseInt(addedTimeMatch[2], 10);
            if (!Number.isNaN(baseMinute) && !Number.isNaN(extraMinute)) {
                return baseMinute + extraMinute;
            }
        }

        // Fallback: primer entero detectado (ej: "45'", "90")
        const genericMinuteMatch = text.match(/\d{1,3}/);
        if (!genericMinuteMatch) return null;

        const minuteValue = Number.parseInt(genericMinuteMatch[0], 10);
        return Number.isNaN(minuteValue) ? null : minuteValue;
    };

    const parseMinuteFromMatchText = (matchText) => {
        const text = (matchText || "").trim();
        if (!text) return null;

        const clockMatch = text.match(/\b(\d{1,3}:\d{2})\b/);
        if (clockMatch) {
            return parseMinuteFromTimer(clockMatch[1]);
        }

        const addedTimeMatch = text.match(/\b(\d{1,3}\s*\+\s*\d{1,2}'?)\b/);
        if (addedTimeMatch) {
            return parseMinuteFromTimer(addedTimeMatch[1]);
        }

        const apostropheMatch = text.match(/\b(\d{1,3}'(?:\+\d{1,2})?)\b/);
        if (apostropheMatch) {
            return parseMinuteFromTimer(apostropheMatch[1]);
        }

        return null;
    };

    const parseMinuteFromFixture = (matchElement) => {
        if (!matchElement) return null;

        const timerSelectors = [
            '.ovm-FixtureDetailsTwoWay_Timer.ovm-InPlayTimer',
            '.ovm-FixtureDetailsTwoWay_Timer',
            '.ovm-InPlayTimer',
            '[class*="InPlayTimer"]',
        ];

        for (const selector of timerSelectors) {
            const timerNodes = matchElement.querySelectorAll(selector);
            for (const timerNode of timerNodes) {
                const timerText = timerNode?.textContent?.trim() || "";
                const minute = parseMinuteFromTimer(timerText);
                if (minute !== null) {
                    return minute;
                }
            }
        }

        return parseMinuteFromMatchText(matchElement.textContent);
    };

    const buildMatchKey = (homeTeam, awayTeam, competitionName) => {
        const home = (homeTeam || "").trim().toLowerCase();
        const away = (awayTeam || "").trim().toLowerCase();
        const competition = (competitionName || "").trim().toLowerCase();
        return `${competition}||${home}||${away}`;
    };

    const scoreCandidate = (matchData) => {
        if (!matchData) return -1;
        return (matchData.score_home || 0) + (matchData.score_away || 0);
    };

    const shouldReplaceExisting = (existingMatch, nextMatch) => {
        if (!existingMatch) return true;

        const existingHasMinute = existingMatch.minute !== null && existingMatch.minute !== undefined;
        const nextHasMinute = nextMatch.minute !== null && nextMatch.minute !== undefined;
        if (nextHasMinute && !existingHasMinute) return true;
        if (existingHasMinute && !nextHasMinute) return false;

        const existingScore = scoreCandidate(existingMatch);
        const nextScore = scoreCandidate(nextMatch);
        if (nextScore > existingScore) return true;

        if (nextHasMinute && existingHasMinute && nextMatch.minute > existingMatch.minute) {
            return true;
        }

        return false;
    };
    
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
                const minute = parseMinuteFromFixture(match);

                // URL del partido (si existe un link directo)
                const match_url = match.querySelector('a')?.href || null;

                const extractedMatch = {
                    home_team,
                    away_team,
                    score_home,
                    score_away,
                    minute,
                    competition: competitionName,
                    match_url
                };

                const matchKey = buildMatchKey(home_team, away_team, competitionName);
                const existingMatch = resultsByKey.get(matchKey);
                if (shouldReplaceExisting(existingMatch, extractedMatch)) {
                    resultsByKey.set(matchKey, extractedMatch);
                }
            } catch (err) {
                console.error("Error procesando partido en Bet365:", err);
            }
        });
    });

    return Array.from(resultsByKey.values());
}
