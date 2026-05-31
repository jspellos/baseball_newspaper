from __future__ import annotations

from dataclasses import dataclass


DIVISION_NAMES = {
    200: "AL West",
    201: "AL East",
    202: "AL Central",
    203: "NL West",
    204: "NL East",
    205: "NL Central",
}
DIVISION_ORDER = {201: 0, 202: 1, 200: 2, 204: 3, 205: 4, 203: 5}


@dataclass(frozen=True)
class TeamLine:
    name: str
    abbr: str
    runs: int
    hits: int
    errors: int
    record: str


def _team_name(team: dict) -> str:
    return team.get("team", {}).get("name") or team.get("name") or "Unknown"


def _team_abbr(team: dict) -> str:
    return team.get("team", {}).get("abbreviation") or team.get("abbreviation") or ""


def _record(league_record: dict | None) -> str:
    if not league_record:
        return ""
    wins = league_record.get("wins")
    losses = league_record.get("losses")
    if wins is None or losses is None:
        return ""
    return f"{wins}-{losses}"


def _runs_by_inning(linescore: dict, side: str) -> list[str]:
    runs = []
    for inning in linescore.get("innings", []):
        runs.append(str(inning.get(side, {}).get("runs", 0)))
    while len(runs) < 9:
        runs.append("")
    return runs


def _player_position(player: dict) -> str:
    position = player.get("position", {})
    return position.get("abbreviation") or ""


def _batting_line(player: dict) -> dict | None:
    stats = player.get("stats", {}).get("batting")
    if not stats:
        return None
    if stats.get("atBats") is None:
        return None
    season = player.get("seasonStats", {}).get("batting", {})
    return {
        "name": player.get("person", {}).get("fullName", "Unknown"),
        "pos": _player_position(player),
        "ab": stats.get("atBats", 0),
        "r": stats.get("runs", 0),
        "h": stats.get("hits", 0),
        "rbi": stats.get("rbi", 0),
        "bb": stats.get("baseOnBalls", 0),
        "k": stats.get("strikeOuts", 0),
        "avg": season.get("avg", ""),
    }


def _pitching_line(player: dict) -> dict | None:
    stats = player.get("stats", {}).get("pitching")
    if not stats:
        return None
    if stats.get("inningsPitched") is None:
        return None
    season = player.get("seasonStats", {}).get("pitching", {})
    return {
        "name": player.get("person", {}).get("fullName", "Unknown"),
        "ip": stats.get("inningsPitched", ""),
        "h": stats.get("hits", 0),
        "r": stats.get("runs", 0),
        "er": stats.get("earnedRuns", 0),
        "bb": stats.get("baseOnBalls", 0),
        "k": stats.get("strikeOuts", 0),
        "era": season.get("era", ""),
    }


def _batting_order(player: dict) -> int:
    value = player.get("battingOrder")
    if value and str(value).isdigit():
        return int(value)
    return 9999


def _team_box(boxscore: dict, side: str) -> dict:
    team_data = boxscore["teams"][side]
    team = team_data["team"]
    players_by_id = team_data.get("players", {})
    players = list(players_by_id.values())
    batting_players = sorted(players, key=_batting_order)
    pitching_players = [
        players_by_id[f"ID{player_id}"]
        for player_id in team_data.get("pitchers", [])
        if f"ID{player_id}" in players_by_id
    ]
    return {
        "name": team.get("name", "Unknown"),
        "abbr": team.get("abbreviation", ""),
        "batting": [line for player in batting_players if (line := _batting_line(player))],
        "pitching": [line for player in pitching_players if (line := _pitching_line(player))],
    }


def _decisions(schedule_game: dict) -> dict:
    decisions = schedule_game.get("decisions", {})
    return {
        "winner": decisions.get("winner", {}).get("fullName", ""),
        "loser": decisions.get("loser", {}).get("fullName", ""),
        "save": decisions.get("save", {}).get("fullName", ""),
    }


def _game_notes(boxscore: dict) -> list[str]:
    info = boxscore.get("info", [])
    notes = []
    labels = ("HR", "2B", "3B", "RBI", "SB", "E", "HBP")
    for item in info:
        label = item.get("label", "").rstrip(":")
        value = item.get("value", "")
        if label in labels and value:
            notes.append(f"{label}: {value}")
    return notes


def normalize_game(item: dict) -> dict:
    schedule_game = item["schedule"]
    boxscore = item["boxscore"]
    linescore = schedule_game.get("linescore", {})
    teams = schedule_game.get("teams", {})
    away = teams.get("away", {})
    home = teams.get("home", {})

    away_line = TeamLine(
        name=_team_name(away),
        abbr=_team_abbr(away),
        runs=away.get("score", 0),
        hits=linescore.get("teams", {}).get("away", {}).get("hits", 0),
        errors=linescore.get("teams", {}).get("away", {}).get("errors", 0),
        record=_record(away.get("leagueRecord")),
    )
    home_line = TeamLine(
        name=_team_name(home),
        abbr=_team_abbr(home),
        runs=home.get("score", 0),
        hits=linescore.get("teams", {}).get("home", {}).get("hits", 0),
        errors=linescore.get("teams", {}).get("home", {}).get("errors", 0),
        record=_record(home.get("leagueRecord")),
    )

    winner = away_line if away_line.runs > home_line.runs else home_line
    loser = home_line if winner is away_line else away_line

    return {
        "game_pk": schedule_game.get("gamePk"),
        "venue": schedule_game.get("venue", {}).get("name", ""),
        "headline": f"{winner.abbr or winner.name} {winner.runs}, {loser.abbr or loser.name} {loser.runs}",
        "away": away_line,
        "home": home_line,
        "away_runs": _runs_by_inning(linescore, "away"),
        "home_runs": _runs_by_inning(linescore, "home"),
        "away_box": _team_box(boxscore, "away"),
        "home_box": _team_box(boxscore, "home"),
        "decisions": _decisions(schedule_game),
        "notes": _game_notes(boxscore),
    }


def normalize_standings(payload: dict) -> list[dict]:
    divisions = []
    for record in payload.get("records", []):
        division_info = record.get("division", {})
        division = division_info.get("name") or DIVISION_NAMES.get(division_info.get("id"), "Division")
        teams = []
        for team_record in record.get("teamRecords", []):
            teams.append(
                {
                    "id": team_record.get("team", {}).get("id"),
                    "team": team_record.get("team", {}).get("name", "Unknown"),
                    "abbr": team_record.get("team", {}).get("abbreviation", ""),
                    "w": team_record.get("wins", ""),
                    "l": team_record.get("losses", ""),
                    "pct": team_record.get("winningPercentage", ""),
                    "gb": team_record.get("gamesBack", ""),
                    "streak": team_record.get("streak", {}).get("streakCode", ""),
                }
            )
        divisions.append({"id": division_info.get("id"), "name": division, "teams": teams})
    return sorted(divisions, key=lambda division: DIVISION_ORDER.get(division["id"], 99))


def _league_abbr(team: dict) -> str:
    league = team.get("league", {})
    league_id = league.get("id")
    if league_id == 103:
        return "AL"
    if league_id == 104:
        return "NL"
    return league.get("abbreviation", "")


def normalize_leaders(payload: dict) -> list[dict]:
    leaders = []
    if payload.get("stats"):
        for stats_group in payload.get("stats", []):
            for split in stats_group.get("splits", []):
                stat = split.get("stat", {})
                leaders.append(
                    {
                        "name": split.get("player", {}).get("fullName", "Unknown"),
                        "team": split.get("team", {}).get("abbreviation", ""),
                        "league": _league_abbr(split.get("team", {})),
                        "g": stat.get("gamesPlayed", ""),
                        "ab": stat.get("atBats", ""),
                        "r": stat.get("runs", ""),
                        "h": stat.get("hits", ""),
                        "hr": stat.get("homeRuns", ""),
                        "rbi": stat.get("rbi", ""),
                        "sb": stat.get("stolenBases", ""),
                        "avg": stat.get("avg", ""),
                        "ops": stat.get("ops", ""),
                        "w": stat.get("wins", ""),
                        "l": stat.get("losses", ""),
                        "ip": stat.get("inningsPitched", ""),
                        "era": stat.get("era", ""),
                        "so": stat.get("strikeOuts", ""),
                        "sv": stat.get("saves", ""),
                        "value": "",
                    }
                )
        return leaders

    for league_leaders in payload.get("leagueLeaders", []):
        for leader in league_leaders.get("leaders", []):
            leaders.append(
                {
                    "name": leader.get("person", {}).get("fullName", "Unknown"),
                    "team": leader.get("team", {}).get("abbreviation", ""),
                    "league": _league_abbr(leader.get("team", {})),
                    "value": leader.get("value", ""),
                }
            )
    return leaders


def normalize_advanced_leaders(payload: dict, stat_group: str) -> list[dict]:
    leaders = []
    for stats_group in payload.get("stats", []):
        for split in stats_group.get("splits", []):
            stat = split.get("stat", {})
            leader = {
                "name": split.get("player", {}).get("fullName", "Unknown"),
                "team": split.get("team", {}).get("abbreviation", ""),
                "league": _league_abbr(split.get("team", {})),
                "war": f'{stat.get("war", 0):.1f}',
            }
            if stat_group == "hitting":
                leader.update(
                    {
                        "woba": f'{stat.get("woba", 0):.3f}',
                        "wrc_plus": f'{stat.get("wRcPlus", 0):.0f}',
                        "batting": f'{stat.get("batting", 0):.1f}',
                        "baserunning": f'{stat.get("baseRunning", 0):.1f}',
                    }
                )
            else:
                leader.update(
                    {
                        "fip": f'{stat.get("fip", 0):.2f}',
                        "xfip": f'{stat.get("xfip", 0):.2f}',
                        "era_minus": f'{stat.get("eraMinus", 0):.0f}',
                    }
                )
            leaders.append(leader)
    return leaders


def _pythagorean_record(runs_scored: int, runs_allowed: int, games: int) -> str:
    if not games or not runs_scored + runs_allowed:
        return ""
    exponent = 1.83
    win_pct = runs_scored**exponent / (runs_scored**exponent + runs_allowed**exponent)
    wins = round(games * win_pct)
    return f"{wins}-{games - wins}"


def normalize_team_stats(payload: dict, standings: list[dict]) -> list[dict]:
    records = {}
    for division in standings:
        for team in division["teams"]:
            records[team["id"]] = team

    by_team = {}
    for stats_group in payload.get("stats", []):
        group = stats_group.get("group", {}).get("displayName", "")
        for split in stats_group.get("splits", []):
            team_name = split.get("team", {}).get("name", "Unknown")
            team_id = split.get("team", {}).get("id")
            by_team.setdefault(team_id, {"name": team_name})[group] = split.get("stat", {})

    teams = []
    for team_id, groups in by_team.items():
        hitting = groups.get("hitting", {})
        pitching = groups.get("pitching", {})
        standing = records.get(team_id, {})
        games = int(hitting.get("gamesPlayed", 0) or 0)
        runs_scored = int(hitting.get("runs", 0) or 0)
        runs_allowed = int(pitching.get("runs", 0) or 0)
        teams.append(
            {
                "team": standing.get("abbr") or groups["name"],
                "record": f'{standing.get("w", "")}-{standing.get("l", "")}',
                "run_diff": runs_scored - runs_allowed,
                "expected_record": _pythagorean_record(runs_scored, runs_allowed, games),
                "ops": hitting.get("ops", ""),
                "era": pitching.get("era", ""),
                "whip": pitching.get("whip", ""),
            }
        )
    return sorted(teams, key=lambda team: team["run_diff"], reverse=True)


def normalize_bundle(bundle: dict) -> dict:
    standings = normalize_standings(bundle["standings"])
    return {
        "date": bundle["date"],
        "season": bundle["season"],
        "games": [normalize_game(item) for item in bundle["games"]],
        "standings": standings,
        "leaders": {
            key: normalize_leaders(value)
            for key, value in bundle["leaders"].items()
        },
        "advanced_leaders": {
            key: normalize_advanced_leaders(value, key)
            for key, value in bundle["advanced_leaders"].items()
        },
        "team_stats": normalize_team_stats(bundle["team_stats"], standings),
    }


def sample_newspaper() -> dict:
    return {
        "date": "2026-05-29",
        "season": 2026,
        "games": [
            {
                "headline": "ATL 8, CIN 3",
                "venue": "Great American Ball Park",
                "away": TeamLine("Atlanta Braves", "ATL", 8, 13, 0, "39-19"),
                "home": TeamLine("Cincinnati Reds", "CIN", 3, 10, 0, "29-27"),
                "away_runs": ["1", "3", "0", "0", "0", "4", "0", "0", "0"],
                "home_runs": ["0", "0", "0", "2", "1", "0", "0", "0", "0"],
                "away_box": {
                    "name": "Atlanta Braves",
                    "batting": [
                        {"name": "Ronald Acuna Jr.", "pos": "RF", "ab": 3, "r": 1, "h": 1, "rbi": 1, "bb": 2, "k": 0, "avg": ".239"},
                        {"name": "Michael Harris II", "pos": "CF", "ab": 5, "r": 0, "h": 3, "rbi": 5, "bb": 0, "k": 0, "avg": ".308"},
                        {"name": "Matt Olson", "pos": "1B", "ab": 5, "r": 0, "h": 2, "rbi": 0, "bb": 0, "k": 2, "avg": ".265"},
                        {"name": "Will Smith", "pos": "DH", "ab": 5, "r": 2, "h": 3, "rbi": 0, "bb": 0, "k": 0, "avg": ".336"},
                    ],
                    "pitching": [],
                },
                "home_box": {
                    "name": "Cincinnati Reds",
                    "batting": [
                        {"name": "Blake Dunn", "pos": "RF", "ab": 5, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 2, "avg": ".304"},
                        {"name": "Elly De La Cruz", "pos": "SS", "ab": 4, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 3, "avg": ".274"},
                        {"name": "Brock Stewart", "pos": "3B", "ab": 4, "r": 0, "h": 3, "rbi": 1, "bb": 0, "k": 0, "avg": ".265"},
                        {"name": "Eugenio Suarez", "pos": "DH", "ab": 4, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 0, "avg": ".229"},
                    ],
                    "pitching": [],
                },
                "decisions": {"winner": "Bryce Elder", "loser": "Hunter Greene", "save": ""},
                "notes": ["2B: Yastrzemski (8), Stewart 2 (11)", "HR: Acuna (4), Bleday (8)", "RBI: Harris 5 (56), Acuna (17), Lowe (25)"],
            },
            {
                "headline": "SEA 4, TEX 2",
                "venue": "Globe Life Field",
                "away": TeamLine("Seattle Mariners", "SEA", 4, 8, 1, "31-25"),
                "home": TeamLine("Texas Rangers", "TEX", 2, 6, 0, "26-31"),
                "away_runs": ["0", "0", "1", "0", "2", "0", "1", "0", "0"],
                "home_runs": ["0", "1", "0", "0", "0", "1", "0", "0", "0"],
                "away_box": {
                    "name": "Seattle Mariners",
                    "batting": [
                        {"name": "Julio Rodriguez", "pos": "CF", "ab": 4, "r": 1, "h": 2, "rbi": 2, "bb": 0, "k": 1, "avg": ".297"},
                        {"name": "Cal Raleigh", "pos": "C", "ab": 3, "r": 1, "h": 1, "rbi": 1, "bb": 1, "k": 0, "avg": ".250"},
                    ],
                    "pitching": [
                        {"name": "Logan Gilbert", "ip": "6.0", "h": 5, "r": 2, "er": 2, "bb": 1, "k": 7, "era": "2.29"},
                    ],
                },
                "home_box": {
                    "name": "Texas Rangers",
                    "batting": [
                        {"name": "Josh Jung", "pos": "3B", "ab": 4, "r": 0, "h": 2, "rbi": 1, "bb": 0, "k": 1, "avg": ".305"},
                    ],
                    "pitching": [
                        {"name": "Nathan Eovaldi", "ip": "5.0", "h": 6, "r": 3, "er": 3, "bb": 2, "k": 4, "era": "3.41"},
                    ],
                },
                "decisions": {"winner": "Logan Gilbert", "loser": "Nathan Eovaldi", "save": "Andres Munoz"},
                "notes": ["HR: Raleigh (15)", "SB: Rodriguez (12)", "Seattle bullpen: 3.0 IP, 0 R, 4 K"],
            },
        ],
        "standings": [
            {
                "name": "AL East",
                "teams": [
                    {"team": "Tampa Bay Rays", "abbr": "TB", "w": 35, "l": 19, "pct": ".648", "gb": "-", "streak": "W1"},
                    {"team": "New York Yankees", "abbr": "NYY", "w": 35, "l": 22, "pct": ".614", "gb": "1.5", "streak": "W5"},
                    {"team": "Toronto Blue Jays", "abbr": "TOR", "w": 29, "l": 29, "pct": ".500", "gb": "8.0", "streak": "W4"},
                    {"team": "Baltimore Orioles", "abbr": "BAL", "w": 26, "l": 32, "pct": ".448", "gb": "11.0", "streak": "L2"},
                    {"team": "Boston Red Sox", "abbr": "BOS", "w": 23, "l": 33, "pct": ".411", "gb": "13.0", "streak": "L2"},
                ],
            },
            {
                "name": "NL East",
                "teams": [
                    {"team": "Atlanta Braves", "abbr": "ATL", "w": 39, "l": 19, "pct": ".672", "gb": "-", "streak": "W6"},
                    {"team": "Philadelphia Phillies", "abbr": "PHI", "w": 32, "l": 24, "pct": ".571", "gb": "6.0", "streak": "W1"},
                    {"team": "Miami Marlins", "abbr": "MIA", "w": 29, "l": 27, "pct": ".518", "gb": "9.0", "streak": "L1"},
                ],
            },
        ],
        "leaders": {
            "avg": [
                {"name": "Lopez", "team": "MIA", "league": "NL", "ab": 223, "h": 75, "hr": 8, "rbi": 31, "sb": 5, "avg": ".336"},
                {"name": "Arraez", "team": "SF", "league": "NL", "ab": 210, "h": 69, "hr": 2, "rbi": 27, "sb": 1, "avg": ".329"},
                {"name": "Marsh", "team": "PHI", "league": "NL", "ab": 184, "h": 60, "hr": 9, "rbi": 29, "sb": 7, "avg": ".326"},
                {"name": "Edwards", "team": "MIA", "league": "NL", "ab": 216, "h": 69, "hr": 4, "rbi": 41, "sb": 12, "avg": ".319"},
                {"name": "Diaz", "team": "TB", "league": "AL", "ab": 195, "h": 61, "hr": 11, "rbi": 34, "sb": 0, "avg": ".313"},
            ],
            "hr": [
                {"name": "Judge", "team": "NYY", "league": "AL", "ab": 188, "h": 57, "hr": 19, "rbi": 44, "sb": 3, "avg": ".303"},
                {"name": "Ohtani", "team": "LAD", "league": "NL", "ab": 229, "h": 73, "hr": 18, "rbi": 46, "sb": 12, "avg": ".319"},
                {"name": "Alvarez", "team": "HOU", "league": "AL", "ab": 209, "h": 63, "hr": 16, "rbi": 38, "sb": 1, "avg": ".301"},
                {"name": "Raleigh", "team": "SEA", "league": "AL", "ab": 172, "h": 43, "hr": 15, "rbi": 36, "sb": 0, "avg": ".250"},
                {"name": "Olson", "team": "ATL", "league": "NL", "ab": 216, "h": 57, "hr": 15, "rbi": 42, "sb": 0, "avg": ".264"},
            ],
            "era": [
                {"name": "Skubal", "team": "DET", "league": "AL", "w": 7, "l": 1, "ip": "72.1", "era": "1.87", "so": 78, "sv": 0},
                {"name": "Burnes", "team": "ARI", "league": "NL", "w": 5, "l": 2, "ip": "69.0", "era": "2.04", "so": 67, "sv": 0},
                {"name": "Wheeler", "team": "PHI", "league": "NL", "w": 6, "l": 3, "ip": "75.0", "era": "2.16", "so": 82, "sv": 0},
                {"name": "Gilbert", "team": "SEA", "league": "AL", "w": 4, "l": 2, "ip": "70.2", "era": "2.29", "so": 70, "sv": 0},
                {"name": "Ragans", "team": "KC", "league": "AL", "w": 4, "l": 3, "ip": "66.1", "era": "2.43", "so": 75, "sv": 0},
            ],
        },
        "advanced_leaders": {
            "hitting": [
                {"name": "Aaron Judge", "team": "NYY", "league": "AL", "woba": ".476", "wrc_plus": "220", "war": "11.3", "batting": "96.5", "baserunning": "-0.5"},
                {"name": "Shohei Ohtani", "team": "LAD", "league": "NL", "woba": ".431", "wrc_plus": "181", "war": "9.1", "batting": "70.6", "baserunning": "4.6"},
            ],
            "pitching": [
                {"name": "Chris Sale", "team": "ATL", "league": "NL", "fip": "2.09", "xfip": "2.64", "era_minus": "57", "war": "6.4"},
                {"name": "Tarik Skubal", "team": "DET", "league": "AL", "fip": "2.49", "xfip": "2.68", "era_minus": "61", "war": "6.3"},
            ],
        },
        "team_stats": [
            {"team": "LAD", "record": "98-64", "run_diff": 156, "expected_record": "96-66", "ops": ".781", "era": "3.90", "whip": "1.23"},
            {"team": "PHI", "record": "95-67", "run_diff": 128, "expected_record": "94-68", "ops": ".750", "era": "3.85", "whip": "1.24"},
            {"team": "NYY", "record": "94-68", "run_diff": 147, "expected_record": "96-66", "ops": ".761", "era": "3.74", "whip": "1.24"},
        ],
    }
