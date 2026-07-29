import json

def get_matches():
    # En un entorno de producción, aquí se usaría BeautifulSoup para hacer scraping de las fuentes
    # y extraer la información en tiempo real.
    # Por confiabilidad en esta demostración, devolvemos un listado estático predefinido.
    return [
        {
            "id": "match_1",
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "competition": "La Liga",
            "category_level": "Tier 1",
            "date": "2026-07-29T20:00:00Z"
        },
        {
            "id": "match_2",
            "home_team": "Luton Town",
            "away_team": "Millwall",
            "competition": "Championship",
            "category_level": "Tier 2",
            "date": "2026-07-29T15:00:00Z"
        },
        {
            "id": "match_3",
            "home_team": "Bayern Munich",
            "away_team": "Borussia Dortmund",
            "competition": "Bundesliga",
            "category_level": "Tier 1",
            "date": "2026-07-29T18:30:00Z"
        },
        {
            "id": "match_4",
            "home_team": "Wrexham",
            "away_team": "Notts County",
            "competition": "League Two",
            "category_level": "Tier 4",
            "date": "2026-07-29T14:00:00Z"
        }
    ]
