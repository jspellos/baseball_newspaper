from __future__ import annotations

import html
from datetime import date
from string import Template

from src.config import STATIC_DIR, TEMPLATE_DIR


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _table_row(cells: list[object], numeric: set[int] | None = None) -> str:
    numeric = numeric or set()
    out = []
    for index, cell in enumerate(cells):
        class_attr = ' class="num"' if index in numeric else ""
        out.append(f"<td{class_attr}>{esc(cell)}</td>")
    return f"<tr>{''.join(out)}</tr>"


def _standings_table(division: dict) -> str:
    rows = "\n".join(
        _table_row(
            [
                team["abbr"] or team["team"],
                team["w"],
                team["l"],
                team["pct"],
                team["gb"],
                team["streak"],
            ],
            numeric={1, 2, 3, 4},
        )
        for team in division["teams"]
    )
    return f"""
      <details class="standings-division responsive-panel" open>
        <summary><h3>{esc(division["name"])}</h3></summary>
        <table>
          <thead><tr><th>Club</th><th class="num">W</th><th class="num">L</th><th class="num">Pct</th><th class="num">GB</th><th>Strk</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </details>
    """


def _leaders_rows(leaders: list[dict], columns: list[tuple[str, str]]) -> str:
    rows = "\n".join(
        _table_row(
            [leader["name"], leader.get("team", "")]
            + [leader.get(key, leader.get("value", "")) for key, _label in columns],
            numeric=set(range(2, len(columns) + 2)),
        )
        for leader in leaders[:10]
    )
    return rows or '<tr><td colspan="8">No qualified leaders available.</td></tr>'


def _league_leaders_table(league_name: str, leaders: list[dict], columns: list[tuple[str, str]]) -> str:
    headers = "".join(f'<th class="num">{esc(label)}</th>' for _key, label in columns)
    return f"""
      <h4 class="league-title">{esc(league_name)}</h4>
      <table>
        <thead><tr><th>Player</th><th>Club</th>{headers}</tr></thead>
        <tbody>{_leaders_rows(leaders, columns)}</tbody>
      </table>
    """


def _leaders_table(title: str, leaders: list[dict], columns: list[tuple[str, str]]) -> str:
    nl_leaders = [leader for leader in leaders if leader.get("league") == "NL"]
    al_leaders = [leader for leader in leaders if leader.get("league") == "AL"]
    return f"""
      <details class="responsive-panel leaders-panel" open>
        <summary><h3 class="section-title">{esc(title)}</h3></summary>
        {_league_leaders_table("National League", nl_leaders, columns)}
        {_league_leaders_table("American League", al_leaders, columns)}
      </details>
    """


def _compact_table(title: str, rows: list[dict], columns: list[tuple[str, str]], limit: int = 10) -> str:
    headers = "".join(f'<th class="num">{esc(label)}</th>' for _key, label in columns)
    body = "\n".join(
        _table_row(
            [row["name"], row.get("team", "")]
            + [row.get(key, "") for key, _label in columns],
            numeric=set(range(2, len(columns) + 2)),
        )
        for row in rows[:limit]
    )
    return f"""
      <details class="responsive-panel leaders-panel" open>
        <summary><h3 class="section-title">{esc(title)}</h3></summary>
        <table>
          <thead><tr><th>Player</th><th>Club</th>{headers}</tr></thead>
          <tbody>{body}</tbody>
        </table>
      </details>
    """


def _team_performance_table(teams: list[dict]) -> str:
    rows = "\n".join(
        _table_row(
            [
                team["team"],
                team["record"],
                f'{team["run_diff"]:+d}',
                team["expected_record"],
                team["ops"],
                team["era"],
                team["whip"],
            ],
            numeric={2, 4, 5, 6},
        )
        for team in teams[:12]
    )
    return f"""
      <details class="responsive-panel leaders-panel" open>
        <summary><h3 class="section-title">Team Performance</h3></summary>
        <table>
          <thead><tr><th>Club</th><th>W-L</th><th class="num">RD</th><th>xW-L</th><th class="num">OPS</th><th class="num">ERA</th><th class="num">WHIP</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <p class="stats-note">RD: run differential. xW-L: Pythagorean expected record.</p>
      </details>
    """


def _batting_table(team_box: dict) -> str:
    rows = "\n".join(
        _table_row(
            [
                f"{line['name']} {line.get('pos', '')}".strip(),
                line.get("ab", ""),
                line.get("r", ""),
                line.get("h", ""),
                line.get("rbi", ""),
                line.get("bb", ""),
                line.get("k", ""),
                line.get("avg", ""),
            ],
            numeric={1, 2, 3, 4, 5, 6, 7},
        )
        for line in team_box.get("batting", [])
    )
    if not rows:
        rows = '<tr><td colspan="8">No batting lines available.</td></tr>'
    return f"""
      <table>
        <thead><tr><th>{esc(team_box.get("name", "Team"))} Batting</th><th class="num">AB</th><th class="num">R</th><th class="num">H</th><th class="num">RBI</th><th class="num">BB</th><th class="num">K</th><th class="num">AVG</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    """


def _pitching_table(team_box: dict) -> str:
    rows = "\n".join(
        _table_row(
            [
                line.get("name", ""),
                line.get("ip", ""),
                line.get("h", ""),
                line.get("er", ""),
                line.get("bb", ""),
                line.get("k", ""),
                line.get("era", ""),
            ],
            numeric={1, 2, 3, 4, 5, 6},
        )
        for line in team_box.get("pitching", [])
    )
    if not rows:
        return ""
    return f"""
      <table class="pitching">
        <thead><tr><th>{esc(team_box.get("name", "Team"))} Pitching</th><th class="num">IP</th><th class="num">H</th><th class="num">ER</th><th class="num">BB</th><th class="num">K</th><th class="num">ERA</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    """


def _line_score(game: dict) -> str:
    innings = "".join(f'<th class="num">{i}</th>' for i in range(1, 10))
    away_runs = "".join(f'<td class="num">{esc(run)}</td>' for run in game["away_runs"])
    home_runs = "".join(f'<td class="num">{esc(run)}</td>' for run in game["home_runs"])
    away = game["away"]
    home = game["home"]
    return f"""
      <table class="line-score">
        <thead><tr><th>Team</th>{innings}<th class="num">R</th><th class="num">H</th><th class="num">E</th></tr></thead>
        <tbody>
          <tr><td>{esc(away.name)}</td>{away_runs}<td class="num">{away.runs}</td><td class="num">{away.hits}</td><td class="num">{away.errors}</td></tr>
          <tr><td>{esc(home.name)}</td>{home_runs}<td class="num">{home.runs}</td><td class="num">{home.hits}</td><td class="num">{home.errors}</td></tr>
        </tbody>
      </table>
    """


def _game_article(game: dict) -> str:
    decisions = game.get("decisions", {})
    decision_bits = []
    if decisions.get("winner"):
        decision_bits.append(f"W: {decisions['winner']}")
    if decisions.get("loser"):
        decision_bits.append(f"L: {decisions['loser']}")
    if decisions.get("save"):
        decision_bits.append(f"SV: {decisions['save']}")

    note_rows = []
    for note in game.get("notes", [])[:6]:
        if ":" in note:
            label, value = note.split(":", 1)
            note_rows.append(f"<p><strong>{esc(label)}:</strong> {esc(value.strip())}</p>")
        else:
            note_rows.append(f"<p>{esc(note)}</p>")
    notes = "".join(note_rows)
    if not notes:
        notes = "<p>No scoring notes available.</p>"

    pitching = _pitching_table(game["away_box"]) + _pitching_table(game["home_box"])

    return f"""
      <details class="game responsive-panel" open>
        <summary class="scoreline">
          <span class="record">({esc(game["away"].record)})</span>
          <span>{esc(game["headline"])}</span>
          <span class="record">({esc(game["home"].record)})</span>
        </summary>
        <div class="game-details">
          {_line_score(game)}
          <div class="box-grid">
            {_batting_table(game["away_box"])}
            {_batting_table(game["home_box"])}
          </div>
          <div class="box-grid pitching-grid">
            {pitching}
          </div>
          <div class="notes">
            <div>{notes}</div>
            <div>
              <p><strong>Decisions:</strong> {esc(" | ".join(decision_bits) or "Unavailable")}</p>
              <p><strong>Venue:</strong> {esc(game.get("venue", "Unavailable"))}</p>
            </div>
          </div>
        </div>
      </details>
    """


def render_daily_page(newspaper: dict, edition_links: str = "") -> str:
    template = Template((TEMPLATE_DIR / "daily.html").read_text(encoding="utf-8"))
    css = (STATIC_DIR / "newspaper.css").read_text(encoding="utf-8")

    games_html = "\n".join(_game_article(game) for game in newspaper["games"])
    if not games_html:
        games_html = '<p class="empty">No completed MLB games were found for this date.</p>'

    return template.safe_substitute(
        css=css,
        generated_on=date.today().isoformat(),
        date=esc(newspaper["date"]),
        season=esc(newspaper["season"]),
        edition_links=edition_links,
        standings="\n".join(_standings_table(division) for division in newspaper["standings"]),
        games=games_html,
        leaders_avg=_leaders_table(
            "Batting Average",
            newspaper["leaders"].get("avg", []),
            [("ab", "AB"), ("h", "H"), ("hr", "HR"), ("rbi", "RBI"), ("sb", "SB"), ("avg", "AVG")],
        ),
        leaders_hr=_leaders_table(
            "Home Runs",
            newspaper["leaders"].get("hr", []),
            [("ab", "AB"), ("h", "H"), ("hr", "HR"), ("rbi", "RBI"), ("sb", "SB"), ("avg", "AVG")],
        ),
        leaders_era=_leaders_table(
            "Earned Run Average",
            newspaper["leaders"].get("era", []),
            [("w", "W"), ("l", "L"), ("ip", "IP"), ("era", "ERA"), ("so", "K"), ("sv", "SV")],
        ),
        advanced_hitters=_compact_table(
            "Advanced Hitters",
            newspaper["advanced_leaders"].get("hitting", []),
            [("woba", "wOBA"), ("wrc_plus", "wRC+"), ("war", "WAR")],
        ),
        advanced_pitchers=_compact_table(
            "Advanced Pitchers",
            newspaper["advanced_leaders"].get("pitching", []),
            [("fip", "FIP"), ("xfip", "xFIP"), ("era_minus", "ERA-"), ("war", "WAR")],
        ),
        team_performance=_team_performance_table(newspaper["team_stats"]),
    )
