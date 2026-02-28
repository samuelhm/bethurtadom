/**
 * Selector de partidos para Winamax.
 * Prioriza PRELOADED_STATE (estable) y deja el DOM como fallback.
 */
(cards) => {
    const normalize = (value) => String(value ?? '').replace(/\s+/g, ' ').trim();

    const parseScore = (scoreText) => {
        if (!scoreText) {
            return [0, 0];
        }

        const mainScore = String(scoreText).split(' - ')[0];
        const match = mainScore.match(/(\d{1,2})\s*[:\-]\s*(\d{1,2})/);
        if (!match) {
            return [0, 0];
        }

        return [parseInt(match[1], 10), parseInt(match[2], 10)];
    };

    const parseFromPreloadedState = () => {
        const state = window.PRELOADED_STATE || window.__PRELOADED_STATE__;
        if (!state || !state.matches) {
            return null;
        }

        const categories = state.categories || {};
        const tournaments = state.tournaments || {};

        const cardIds = new Set(
            cards
                .map((card) => card?.getAttribute?.('data-testid') || '')
                .map((testId) => testId.replace('match-card-', ''))
                .filter(Boolean)
        );

        const results = Object.values(state.matches)
            .filter((match) => {
                if (!match || Number(match.sportId) !== 1) {
                    return false;
                }

                if (match.status !== 'LIVE') {
                    return false;
                }

                if (!cardIds.size) {
                    return true;
                }

                return cardIds.has(String(match.matchId));
            })
            .map((match) => {
                const [scoreHome, scoreAway] = parseScore(match.score || match.setScores);
                const minute = Number.isFinite(match.matchtime) ? Number(match.matchtime) : null;

                const category = normalize(categories[String(match.categoryId)]?.categoryName);
                const tournament = normalize(tournaments[String(match.tournamentId)]?.tournamentName);
                const round = normalize(match.roundName);

                const competitionParts = [category, tournament, round]
                    .filter(Boolean)
                    .filter((part, index, list) => list.indexOf(part) === index);
                const competition = competitionParts.length ? competitionParts.join(' - ') : null;

                return {
                    home_team: normalize(match.competitor1Name),
                    away_team: normalize(match.competitor2Name),
                    score_home: scoreHome,
                    score_away: scoreAway,
                    minute,
                    competition,
                    match_url: `https://www.winamax.es/apuestas-deportivas/match/${match.matchId}`
                };
            })
            .filter((match) => match.home_team && match.away_team);

        return results;
    };

    const matchesFromState = parseFromPreloadedState();
    if (matchesFromState && matchesFromState.length) {
        return matchesFromState;
    }

    const NOISE_WORDS = [
        'alineaciones',
        'estadísticas',
        'combi',
        'resultado final',
        'más apuestas',
        'ver más',
        'en vivo',
        'live',
        'mi apuesta',
        'descanso',
        'en curso',
        'total a domicilio',
        'total a favor',
        'total',
    ];

    const COMPETITION_HINTS = [
        'primera',
        'segunda',
        'liga',
        'division',
        'división',
        'serie',
        'campeonato',
        'clausura',
        'apertura',
        'playoff',
        'copa',
        'amistoso',
        'amistosos',
        'torneo',
        'championship',
    ];

    const isNoise = (text) => {
        const lower = text.toLowerCase();
        if (NOISE_WORDS.some((word) => lower.includes(word))) {
            return true;
        }

        if (/^(1|x|2|1x|x2|12)$/i.test(text)) {
            return true;
        }

        if (/^\d{1,2}:\d{2}$/.test(text)) {
            return true;
        }

        if (/^\d{1,3}'(?:\+\d{1,2})?$/.test(text)) {
            return true;
        }

        if (/^\d+[.,]\d+$/.test(text)) {
            return true;
        }

        if (/^[+\-]?\d+$/.test(text)) {
            return true;
        }

        return false;
    };

    const isCompetitionLine = (text) => {
        const lower = text.toLowerCase();
        if (lower.includes(' - ')) {
            return true;
        }
        if (/\bj\d+\b/i.test(lower)) {
            return true;
        }
        return COMPETITION_HINTS.some((hint) => lower.includes(hint));
    };

    const isValidTeamText = (text) => {
        if (!text) {
            return false;
        }
        if (isNoise(text)) {
            return false;
        }
        if (isCompetitionLine(text)) {
            return false;
        }
        if (!/[\p{L}]/u.test(text)) {
            return false;
        }
        if (text.length < 3) {
            return false;
        }
        return true;
    };

    return cards.map((card) => {
        try {
            const matchId = card.getAttribute('data-testid').replace('match-card-', '');
            const matchUrl = `https://www.winamax.es/apuestas-deportivas/match/${matchId}`;

            const rawLines = card.innerText
                .split('\n')
                .map((line) => normalize(line))
                .filter(Boolean);

            if (!rawLines.length) {
                return null;
            }

            const uniqueLines = [];
            for (const line of rawLines) {
                if (!uniqueLines.includes(line)) {
                    uniqueLines.push(line);
                }
            }

            const competitionLine = uniqueLines.find((line) => isCompetitionLine(line)) || null;

            const domTeamCandidates = [];
            const domTeamNodes = card.querySelectorAll('[class*="gbWBZM"], .ovm-FixtureDetailsTwoWay_TeamName');
            domTeamNodes.forEach((node) => {
                const teamText = normalize(node.textContent);
                if (!isValidTeamText(teamText)) {
                    return;
                }
                if (!domTeamCandidates.includes(teamText)) {
                    domTeamCandidates.push(teamText);
                }
            });

            const fallbackTeamCandidates = uniqueLines.filter((line) => isValidTeamText(line));
            const teamCandidates = domTeamCandidates.length >= 2 ? domTeamCandidates : fallbackTeamCandidates;

            if (teamCandidates.length < 2) {
                return null;
            }

            const homeTeam = teamCandidates[0];
            const awayTeam = teamCandidates[1];

            if (homeTeam === awayTeam) {
                return null;
            }

            let scoreHome = 0;
            let scoreAway = 0;

            const scoreFromText = card.innerText.match(/\b(\d{1,2})\s*-\s*(\d{1,2})\b/);
            if (scoreFromText) {
                scoreHome = parseInt(scoreFromText[1], 10);
                scoreAway = parseInt(scoreFromText[2], 10);
            }

            let minute = null;
            const minuteClock = card.innerText.match(/\b(\d{1,3}):(\d{2})\b/);
            const minuteApostrophe = card.innerText.match(/\b(\d{1,3})'(?:\+\d{1,2})?\b/);
            if (minuteClock) {
                minute = parseInt(minuteClock[1], 10);
            } else if (minuteApostrophe) {
                minute = parseInt(minuteApostrophe[1], 10);
            }

            return {
                home_team: homeTeam,
                away_team: awayTeam,
                score_home: scoreHome,
                score_away: scoreAway,
                minute: minute,
                competition: competitionLine,
                match_url: matchUrl
            };
        } catch (err) {
            return null;
        }
    }).filter((match) => match !== null && match.home_team && match.away_team);
}
