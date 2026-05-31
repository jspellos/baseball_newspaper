from __future__ import annotations

from urllib.parse import urlencode

from src.config import CACHE_DIR, MLB_API_BASE, MLB_SPORT_ID
from src.data.cache import get_json


class MlbApi:
    def __init__(self, refresh_cache: bool = False):
        self.refresh_cache = refresh_cache

    def _get(self, path: str, params: dict | None = None) -> dict:
        query = f"?{urlencode(params)}" if params else ""
        return get_json(
            f"{MLB_API_BASE}{path}{query}",
            cache_dir=CACHE_DIR,
            refresh=self.refresh_cache,
        )

    def schedule(self, date: str) -> dict:
        return self._get(
            "/schedule",
            {
                "sportId": MLB_SPORT_ID,
                "date": date,
                "hydrate": "team,linescore,decisions,venue",
            },
        )

    def boxscore(self, game_pk: int) -> dict:
        return self._get(f"/game/{game_pk}/boxscore")

    def standings(self, season: int) -> dict:
        return self._get(
            "/standings",
            {
                "leagueId": "103,104",
                "season": season,
                "standingsTypes": "regularSeason",
                "hydrate": "team",
            },
        )

    def team_stats(self, season: int) -> dict:
        return self._get(
            "/teams/stats",
            {
                "stats": "season",
                "group": "hitting,pitching",
                "season": season,
                "sportIds": MLB_SPORT_ID,
            },
        )

    def leaders(
        self,
        season: int,
        stat_group: str,
        sort_stat: str,
        limit: int = 50,
        player_pool: str = "ALL",
        sort_order: str = "desc",
    ) -> dict:
        return self._get(
            "/stats",
            {
                "stats": "season",
                "group": stat_group,
                "playerPool": player_pool,
                "sortStat": sort_stat,
                "sortOrder": sort_order,
                "statGroup": stat_group,
                "season": season,
                "sportIds": MLB_SPORT_ID,
                "limit": limit,
                "hydrate": "person,team",
            },
        )

    def advanced_leaders(self, season: int, stat_group: str) -> dict:
        return self._get(
            "/stats",
            {
                "stats": "sabermetrics",
                "group": stat_group,
                "playerPool": "QUALIFIED",
                "sortStat": "war",
                "sortOrder": "desc",
                "season": season,
                "sportIds": MLB_SPORT_ID,
                "limit": 50,
                "hydrate": "person,team",
            },
        )

    def daily_bundle(self, date: str) -> dict:
        season = int(date[:4])
        schedule = self.schedule(date)
        games = []

        for day in schedule.get("dates", []):
            for game in day.get("games", []):
                if game.get("status", {}).get("detailedState") != "Final":
                    continue

                game_pk = game["gamePk"]
                games.append(
                    {
                        "schedule": game,
                        "boxscore": self.boxscore(game_pk),
                    }
                )

        return {
            "date": date,
            "season": season,
            "schedule": schedule,
            "games": games,
            "standings": self.standings(season),
            "team_stats": self.team_stats(season),
            "leaders": {
                "avg": self.leaders(season, "hitting", "avg", player_pool="QUALIFIED"),
                "hr": self.leaders(season, "hitting", "homeRuns"),
                "rbi": self.leaders(season, "hitting", "rbi"),
                "era": self.leaders(
                    season,
                    "pitching",
                    "era",
                    player_pool="QUALIFIED",
                    sort_order="asc",
                ),
                "strikeouts": self.leaders(season, "pitching", "strikeOuts"),
                "saves": self.leaders(season, "pitching", "saves"),
            },
            "advanced_leaders": {
                "hitting": self.advanced_leaders(season, "hitting"),
                "pitching": self.advanced_leaders(season, "pitching"),
            },
        }
