/**
 * Selectores para el mercado de 'Próximo Gol' en Bet365.
 * Basado en el análisis de test.html
 */

const NEXT_GOAL_SELECTORS = {
    // El grupo que contiene las cuotas especiales
    marketGroup: '.ovm-MarketGroup',
    
    // Título descriptivo (ej: "Anotará el 1° gol")
    header: '.ovm-AlternativeMarketHeader',
    
    // Contenedor de las 3 cuotas (Local, Sin Gol, Visitante)
    participants: '.ovm-HorizontalMarket_Participants',
    
    // El valor numérico de la cuota
    oddsValue: '.ovm-ParticipantNoGoal_Odds',
    
    // Indicador de mercado cerrado/suspendido
    suspended: '.ovm-ParticipantNoGoal_Suspended'
};

/**
 * Ejemplo de cómo se extraerían estos datos dentro del bucle de matches:
 */
/*
const market = match.querySelector(NEXT_GOAL_SELECTORS.marketGroup);
if (market) {
    const marketName = market.querySelector(NEXT_GOAL_SELECTORS.header)?.innerText;
    const oddsElements = market.querySelectorAll(NEXT_GOAL_SELECTORS.oddsValue);
    
    const nextGoalOdds = {
        market_name: marketName,
        home_odds: parseFloat(oddsElements[0]?.innerText) || null,
        no_goal_odds: parseFloat(oddsElements[1]?.innerText) || null,
        away_odds: parseFloat(oddsElements[2]?.innerText) || null,
        is_suspended: !!market.querySelector(NEXT_GOAL_SELECTORS.suspended)
    };
}
*/
