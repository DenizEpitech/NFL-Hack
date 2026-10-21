"""Open in Time - Streamlit app. Run: streamlit run app.py (after python compute.py)."""
import base64
import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config as C

st.set_page_config(page_title="Open in Time", layout="wide")

# Theme (same values as .streamlit/config.toml)
INK, MUTED, ACCENT, ALERT, BORDER = "#1C1F23", "#6B7280", "#1F6F4A", "#B4442F", "#E5E7EB"
NAVY, NFL_RED = "#013369", "#D50A0A"
FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"
POS_COLORS = {"WR": "#013369", "TE": "#C8963E", "RB": ACCENT, "FB": "#8B8F97"}
FIELD, OFFENSE, QB_GOLD, BALL = "#2F6B45", "#1E3A5F", "#E3B341", "#7A4B2A"
OPEN_RING, COVERED_RING = "#B9F0CB", "#F7B2A5"
PLOT_CONFIG = {"displayModeBar": False}
ZOOM_CONFIG = {"displaylogo": False, "displayModeBar": True, "modeBarButtons": [["zoom2d", "pan2d", "resetScale2d"]]}
LOGO_DIR = C.ROOT / "assets" / "logos"

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Barlow+Condensed:wght@600;700&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea { font-family: Inter, -apple-system, Segoe UI, Roboto, sans-serif; }
.stApp { font-size: 17px; }
.stMarkdown p, .stMarkdown li { font-size: 1.05rem; line-height: 1.6; }
.block-container { padding-top: 4.4rem; max-width: 1320px; }
h1 { font-family: 'Barlow Condensed', Inter, sans-serif !important; font-weight: 700 !important; font-size: 3.4rem !important;
  color: #1C1F23; padding-bottom: 0.2rem !important; }
h2, h3 { font-weight: 700 !important; color: #1C1F23; letter-spacing: -0.01em; }
h3 { font-family: 'Barlow Condensed', Inter, sans-serif !important; font-size: 2rem !important; text-transform: uppercase;
  color: #013369 !important; border-left: 6px solid #D50A0A; padding-left: 12px !important; }
h4 { color: #013369; }
[data-testid="stWidgetLabel"] p { font-size: 1rem !important; font-weight: 600; color: #1C1F23; }
/* Top navigation: dark turf bar */
[data-testid="stHeader"] { background: #013369; border-bottom: 4px solid #D50A0A; }
[data-testid="stTopNavLink"] p { color: rgba(255, 255, 255, 0.8); font-weight: 700; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.03em; }
[data-testid="stTopNavLink"]:hover p, [data-testid="stTopNavLink"][aria-current="page"] p { color: #FFFFFF; }
[data-testid="stTopNavLink"][aria-current="page"] { background: rgba(255, 255, 255, 0.14); box-shadow: inset 0 -3px 0 #D50A0A; }
[data-testid="stToolbar"] button { color: #FFFFFF; }
/* Stat boxes */
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E5E7EB; border-top: 4px solid #013369; border-radius: 4px; padding: 14px 18px; }
[data-testid="stMetricLabel"] p { color: #4B5563; font-size: 0.95rem !important; font-weight: 600; }
[data-testid="stMetricValue"] { font-family: 'Barlow Condensed', Inter, sans-serif; font-weight: 700; font-size: 2.6rem; color: #013369; }
.brand { font-family: 'Barlow Condensed', Inter, sans-serif; font-size: 1.6rem; font-weight: 700; color: #013369; }
.brand span { font-family: Inter, sans-serif; font-size: 0.98rem; color: #6B7280; font-weight: 500; margin-left: 10px; }
.muted { color: #4B5563; font-size: 1.02rem; }
/* Tables */
.tbl-wrap { max-height: 660px; overflow-y: auto; border: 1px solid #E5E7EB; border-radius: 4px; background: #FFFFFF; }
table.board { width: 100%; border-collapse: collapse; font-size: 1rem; }
table.board th { position: sticky; top: 0; background: #013369; color: #FFFFFF; text-transform: uppercase; letter-spacing: 0.03em; font-weight: 600; text-align: left;
  padding: 11px 12px; border-bottom: 3px solid #D50A0A; font-size: 0.85rem; }
table.board td { padding: 8px 12px; border-bottom: 1px solid #EEF0EE; vertical-align: middle; }
table.board tr:hover td { background: #F1F4F9; }
table.board tr:nth-child(even) td { background: #FAFBFC; }
table.board td.num, table.board th.num { text-align: right; font-variant-numeric: tabular-nums; }
.rank { color: #6B7280; font-weight: 600; width: 44px; }
.player { display: flex; align-items: center; gap: 10px; font-weight: 600; }
.player img, .logo { width: 30px; height: 30px; }
.pos { display: inline-block; min-width: 34px; text-align: center; padding: 2px 6px; border-radius: 4px; color: #FFFFFF;
  font-size: 0.82rem; font-weight: 700; }
.bar { display: flex; align-items: center; gap: 10px; }
.bar .track { flex: 1; height: 8px; background: #EEF0EE; border-radius: 4px; min-width: 90px; }
.bar .fill { height: 8px; background: #013369; border-radius: 4px; }
.bar b { width: 52px; text-align: right; font-variant-numeric: tabular-nums; }
/* Leaders */
.leaders h4 { font-size: 1.15rem; margin: 0 0 8px 0; padding: 0; }
.leader { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #EEF0EE; font-size: 1.02rem; }
.leader .n { color: #6B7280; width: 18px; }
.leader .name { flex: 1; font-weight: 600; }
.leader .v { font-family: 'Barlow Condensed', Inter, sans-serif; font-size: 1.35rem; font-weight: 700; color: #013369; }
/* Player header and matchup */
.head { display: flex; align-items: center; gap: 18px; margin: 4px 0 14px 0; }
.head img { width: 84px; height: 84px; }
.head .nm { font-family: 'Barlow Condensed', Inter, sans-serif; font-size: 2.6rem; font-weight: 700; line-height: 1; }
.head .sub { color: #4B5563; font-size: 1.05rem; margin-top: 4px; }
.matchup { display: flex; align-items: center; gap: 14px; font-family: 'Barlow Condensed', Inter, sans-serif;
  font-size: 1.8rem; font-weight: 700; margin: 6px 0 10px 0; }
.matchup img { width: 52px; height: 52px; }
.matchup .at { color: #6B7280; font-size: 1.2rem; }
.verdict { display: inline-block; padding: 10px 18px; border-radius: 6px; color: #FFFFFF; font-family: 'Barlow Condensed', Inter, sans-serif;
  font-weight: 700; font-size: 1.6rem; letter-spacing: 0.03em; }
.verdict.ok { background: #1F6F4A; }
.verdict.late { background: #B4442F; }
hr { margin: 0.4rem 0 1.2rem 0; border-color: #E5E7EB; }
.shot { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; object-position: top; background: #E5E7EB; }
.head .photo { width: 104px; height: 104px; border-radius: 50%; object-fit: cover; background: #E5E7EB; border: 3px solid #FFFFFF;
  box-shadow: 0 0 0 1px #E5E7EB; }
.head .tm { width: 44px; height: 44px; }
.brand-row { display: flex; align-items: center; gap: 12px; }
.brand-row img { width: 40px; height: 40px; }
/* Replay: story, timeline, legend */
.brand-row .photo { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; }
.story { font-size: 1.2rem; line-height: 1.6; color: #1C1F23; margin: 4px 0 18px 0; }
.tl { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 58px 36px 14px 36px; margin-bottom: 18px; }
.tl-mark.below span { bottom: auto; top: 34px; }
.tl-space { height: 62px; }
.tl-track { position: relative; height: 14px; background: #E5E7EB; border-radius: 7px; }
.tl-window { position: absolute; top: 0; height: 14px; border-radius: 7px; }
.tl-window.ok { background: #1F6F4A; }
.tl-window.late { background: #B4442F; }
.tl-mark { position: absolute; top: -8px; width: 3px; height: 30px; background: #1C1F23; transform: translateX(-1px); }
.tl-mark span { position: absolute; bottom: 34px; left: 50%; transform: translateX(-50%); white-space: nowrap;
  font-size: 0.85rem; color: #4B5563; text-align: center; line-height: 1.25; }
.tl-mark span b { display: block; font-family: 'Barlow Condensed', Inter, sans-serif; font-size: 1.35rem; color: #1C1F23; }
.tl-mark.open { background: #1F6F4A; } .tl-mark.open span b { color: #1F6F4A; }
.tl-mark.press { background: #B4442F; } .tl-mark.press span b { color: #B4442F; }
.tl-note { margin-top: 8px; font-size: 1rem; color: #1C1F23; font-weight: 600; }
.legend { display: flex; flex-wrap: wrap; gap: 22px; justify-content: center; font-size: 0.98rem; color: #374151; margin: 4px 0 6px 0; }
.legend i { display: inline-block; width: 14px; height: 14px; border-radius: 50%; margin-right: 7px; vertical-align: -2px; }
.legend i.ring { background: transparent; border: 3px solid; width: 16px; height: 16px; }
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    read = lambda name: pd.read_parquet(C.CACHE_DIR / f"{name}.parquet")
    return read("play_receiver"), read("player_summary"), read("play_level"), read("frames_demo")


@st.cache_data
def load_logos():
    """Team logos as data URIs (stored locally so the demo works offline)."""
    return {p.stem: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode() for p in LOGO_DIR.glob("*.png")}


@st.cache_data
def load_headshots():
    """Official NFL headshot URLs by nflId (mapping from the public nflverse players table)."""
    hs = pd.read_csv(C.ROOT / "assets" / "headshots.csv")
    return dict(zip(hs.nflId, hs.headshot))


pr, ps, pl, demo = load()
LOGOS = load_logos()
SHOTS = load_headshots()
NFL_LOGO = "data:image/png;base64," + base64.b64encode((C.ROOT / "assets" / "nfl.png").read_bytes()).decode()


def logo(team, cls="logo"):
    src = LOGOS.get(team)
    return f'<img class="{cls}" src="{src}" alt="{team}">' if src else ""


def headshot(nfl_id, cls="shot"):
    src = SHOTS.get(int(nfl_id))
    return f'<img class="{cls}" src="{src}" alt="" onerror="this.style.visibility=\'hidden\'">' if src else ""


def pos_badge(pos):
    return f'<span class="pos" style="background:{POS_COLORS.get(pos, MUTED)}">{pos}</span>'


def fmt(v, suffix="", digits=1):
    return f"{v:.{digits}f}{suffix}" if pd.notna(v) else "n/a"


def style_fig(fig, height):
    """Apply the app typography and colors to a plotly figure."""
    fig.update_layout(template="plotly_white", height=height, font=dict(family=FONT, color=INK, size=15),
                      paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, l=10, r=10, b=10),
                      hoverlabel=dict(font_family=FONT, font_size=14, bgcolor="white"))
    return fig


# ---------- shared filters (persist across pages) ----------
FILTERS = {"pos": ["WR", "TE", "RB"], "teams": [], "min_routes": C.MIN_ROUTES}
for k, v in FILTERS.items():
    st.session_state.setdefault(f"f_{k}", v)


def filter_bar(page):
    """Position / team / min routes toolbar; values are shared by every page."""
    def sync(k):
        st.session_state[f"f_{k}"] = st.session_state[f"{page}_{k}"]
    for k in FILTERS:
        st.session_state.setdefault(f"{page}_{k}", st.session_state[f"f_{k}"])
    c = st.columns([2, 3, 2])
    c[0].multiselect("Position", ["WR", "TE", "RB"], key=f"{page}_pos", on_change=sync, args=("pos",))
    c[1].multiselect("Team", sorted(ps.team.unique()), key=f"{page}_teams", on_change=sync, args=("teams",),
                     placeholder="All teams")
    c[2].slider("Minimum routes", C.MIN_ROUTES, 300, key=f"{page}_min_routes", step=10, on_change=sync,
                args=("min_routes",))
    f = ps[ps.position.isin(st.session_state.f_pos) & (ps.nb_routes >= st.session_state.f_min_routes)]
    return f[f.team.isin(st.session_state.f_teams)] if st.session_state.f_teams else f


# ---------- pages ----------
def page_overview():
    st.markdown("# Open in Time")
    st.markdown("Does the receiver get open **before** the pass rush reaches the quarterback? "
                f"We timed it on **{len(pl):,} pass plays** of the 2021 NFL season (weeks 1 to 8). "
                "New to football? Open the **Help** tab.")
    att = pl[pl.passResult.isin(["C", "I", "IN"]) & pl.target_open_in_time.notna()]
    comp = att.groupby("target_open_in_time").passResult.apply(lambda s: (s == "C").mean() * 100)
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown("### It matters")
        fig = go.Figure(go.Bar(
            x=[comp[True], comp[False]], y=["Target open in time", "Target not open in time"], orientation="h",
            marker_color=[ACCENT, ALERT], text=[f"{comp[True]:.1f}%", f"{comp[False]:.1f}%"], textposition="inside",
            insidetextfont=dict(color="white", size=22, family="Barlow Condensed, Inter, sans-serif"),
            hoverinfo="skip"))
        style_fig(fig, 230)
        fig.update_layout(xaxis=dict(range=[0, 100], ticksuffix="%", title="Pass completion rate"),
                          yaxis=dict(autorange="reversed", tickfont=dict(size=15)), margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)
        st.markdown(f'<p class="muted">When the targeted receiver was open in time, the pass was caught '
                    f'<b>{comp[True] - comp[False]:+.1f} points</b> more often. A typical receiver gets open at '
                    f'<b>{pr.t_open.median():.1f} s</b>; when the rush gets home, it arrives at '
                    f'<b>{pl.t_pressure.median():.1f} s</b>.</p>', unsafe_allow_html=True)
    with right:
        st.markdown("### Leaders by position")
        cols = st.columns(3)
        for col, pos in zip(cols, ["WR", "TE", "RB"]):
            top = ps[(ps.position == pos) & (ps.nb_routes >= 80)].head(5)
            rows = "".join(f'<div class="leader"><span class="n">{i}</span>{logo(r.team)}'
                           f'<span class="name">{html.escape(r.displayName.split(" ")[-1])}</span>'
                           f'<span class="v">{r.oit_pct:.0f}%</span></div>'
                           for i, r in enumerate(top.itertuples(), 1))
            col.markdown(f'<div class="leaders"><h4>{pos_badge(pos)}</h4>{rows}</div>', unsafe_allow_html=True)
        st.markdown('<p class="muted">Open in Time %, players with at least 80 routes.</p>', unsafe_allow_html=True)


SORTS = {"Open in Time %": ("oit_pct", False), "Fastest to get open": ("t_open_moyen", True),
         "Most routes": ("nb_routes", False), "Least protection": ("t_pressure_moyen", True)}


def page_leaderboard():
    st.markdown("### Leaderboard")
    f = filter_bar("lb")
    sort = st.radio("Sort by", list(SORTS), horizontal=True)
    col, asc = SORTS[sort]
    f = f.sort_values(col, ascending=asc)
    st.markdown('<p class="muted">Compare within a position: RBs and TEs are often left free underneath, while star '
                'WRs draw the tightest coverage, so they rank lower on raw Open in Time %.</p>', unsafe_allow_html=True)
    rows = "".join(
        f'<tr><td class="rank">{i}</td>'
        f'<td><div class="player">{headshot(r.nflId)}{logo(r.team)}{html.escape(r.displayName)}</div></td>'
        f'<td>{pos_badge(r.position)}</td><td>{r.team}</td><td class="num">{r.nb_routes}</td>'
        f'<td><div class="bar"><div class="track"><div class="fill" style="width:{r.oit_pct:.0f}%"></div></div>'
        f'<b>{r.oit_pct:.1f}%</b></div></td>'
        f'<td class="num">{fmt(r.t_open_moyen, " s", 2)}</td><td class="num">{fmt(r.t_pressure_moyen, " s", 2)}</td>'
        f'<td class="num">{fmt(r.oit_pct_vs_man, "%")}</td><td class="num">{fmt(r.oit_pct_vs_zone, "%")}</td></tr>'
        for i, r in enumerate(f.itertuples(), 1))
    st.markdown(
        '<div class="tbl-wrap"><table class="board"><thead><tr><th>#</th><th>Player</th><th>Pos</th><th>Team</th>'
        '<th class="num">Routes</th><th>Open in Time %</th><th class="num">Time to open</th>'
        '<th class="num">Time to pressure</th><th class="num">vs Man</th><th class="num">vs Zone</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)


def zoom_reset(key):
    """Button that redraws the chart, which resets any zoom."""
    st.session_state.setdefault(key, 0)
    if st.button("Reset zoom", key=f"btn_{key}"):
        st.session_state[key] += 1
    return f"{key}_{st.session_state[key]}"


def page_hidden_gems():
    st.markdown("### Hidden gems")
    f = filter_bar("hg")
    st.markdown('<p class="muted">Each dot is a player. Bottom left: receivers who get open fast but whose quarterback '
                'is pressured early. The offensive line holds their stats back, so they are likely undervalued.</p>',
                unsafe_allow_html=True)
    sc = f.dropna(subset=["t_open_moyen", "t_pressure_moyen"])
    if sc.empty:
        st.info("No player matches the filters.")
        return
    fig = px.scatter(sc, x="t_open_moyen", y="t_pressure_moyen", color="position", size="nb_routes",
                     hover_name="displayName", color_discrete_map=POS_COLORS, size_max=22,
                     hover_data={"team": True, "oit_pct": True, "nb_routes": True, "position": False},
                     labels={"t_open_moyen": "Average time to get open (s), faster to the left",
                             "t_pressure_moyen": "Average time before pressure on his QB (s)",
                             "position": "Position", "oit_pct": "Open in Time %", "nb_routes": "Routes"})
    fig.update_traces(marker=dict(opacity=0.8, line=dict(color="white", width=1)))
    mx, my = sc.t_open_moyen.median(), sc.t_pressure_moyen.median()
    fig.add_vline(x=mx, line_dash="dot", line_color=MUTED, line_width=1)
    fig.add_hline(y=my, line_dash="dot", line_color=MUTED, line_width=1)
    fig.add_shape(type="rect", x0=sc.t_open_moyen.min() - 0.05, x1=mx, y0=sc.t_pressure_moyen.min() - 0.05, y1=my,
                  fillcolor=ACCENT, opacity=0.07, line_width=0, layer="below")
    fig.add_annotation(x=sc.t_open_moyen.min(), y=sc.t_pressure_moyen.min(), xanchor="left", yanchor="bottom",
                       text="<b>HIDDEN GEMS</b><br>open fast, little protection", showarrow=False,
                       font=dict(color=ACCENT, size=15), align="left")
    fig.update_layout(legend=dict(orientation="h", y=1.06, x=0, title_text=""))
    key = zoom_reset("gems_zoom")
    st.caption("Drag on the chart to zoom. Reset zoom or double-click to zoom back out.")
    st.plotly_chart(style_fig(fig, 600), width="stretch", config=ZOOM_CONFIG, key=key)


def page_players():
    if "selected_player" in st.session_state:
        st.session_state.player_select = st.session_state.pop("selected_player")
    names = ps.sort_values("oit_pct", ascending=False).displayName.tolist()
    name = st.selectbox("Player", names, key="player_select")
    p = ps[ps.displayName == name].iloc[0]
    st.markdown(f'<div class="head">{headshot(p.nflId, "photo")}<div><div class="nm">{html.escape(p.displayName)}</div>'
                f'<div class="sub">{pos_badge(p.position)} &nbsp;{logo(p.team, "tm")} {p.team}, {p.nb_routes} routes</div></div></div>',
                unsafe_allow_html=True)
    m = st.columns(5)
    m[0].metric("Open in Time %", f"{p.oit_pct:.1f}%")
    m[1].metric("Avg time to open", fmt(p.t_open_moyen, " s", 2))
    m[2].metric("Avg time to pressure", fmt(p.t_pressure_moyen, " s", 2))
    m[3].metric("vs Man coverage", fmt(p.oit_pct_vs_man, "%"))
    m[4].metric("vs Zone coverage", fmt(p.oit_pct_vs_zone, "%"))
    plays = pr[pr.nflId == p.nflId].merge(pl[["gameId", "playId", "playDescription"]], on=["gameId", "playId"])
    plays = plays.assign(Verdict=np.select([plays.open_in_time, plays.t_open.notna()], ["Open in time", "Too late"], "Never open"))
    st.markdown("### Every route")
    st.dataframe(
        plays[["Verdict", "t_open", "t_pressure", "t_end", "max_separation", "is_target", "pff_passCoverageType",
               "passResult", "playResult", "playDescription"]].round(2).rename(columns={
            "t_open": "Open at (s)", "t_pressure": "Pressure at (s)", "t_end": "Ball out (s)",
            "max_separation": "Max sep (yd)", "is_target": "Targeted", "pff_passCoverageType": "Coverage",
            "passResult": "Result", "playResult": "Yards", "playDescription": "Play"}),
        hide_index=True, width="stretch", height=420)


# ---------- play animation ----------
def circle(x, y, r, color):
    return dict(type="circle", x0=x - r, x1=x + r, y0=y - r, y1=y + r, line=dict(color=color, width=2.5))


def field_shapes(los):
    """End zones, yard lines every 5 yards (bolder every 10) and the line of scrimmage."""
    shapes = [dict(type="rect", x0=x0, x1=x0 + 10, y0=0, y1=53.3, fillcolor="rgba(0,0,0,0.18)", line_width=0, layer="below")
              for x0 in (0, 110)]
    shapes += [dict(type="line", x0=x, x1=x, y0=0, y1=53.3, layer="below",
                    line=dict(color=f"rgba(255,255,255,{0.5 if x % 10 == 0 else 0.2})", width=1.5 if x % 10 == 0 else 1))
               for x in range(10, 111, 5)]
    shapes.append(dict(type="line", x0=los, x1=los, y0=0, y1=53.3, line=dict(color="#9CC3E6", width=2, dash="dash")))
    return shapes


def yard_numbers(x_min, x_max):
    """Yard numbers painted on the field (10, 20, ... 50, ... 10), like on TV."""
    marks = []
    for x in range(20, 101, 10):
        if x_min < x < x_max:
            label = x - 10 if x <= 60 else 110 - x
            marks += [dict(x=x, y=y, text=str(label), showarrow=False, textangle=angle,
                           font=dict(family="Barlow Condensed, Inter, sans-serif", size=22, color="rgba(255,255,255,0.55)"))
                      for y, angle in ((5, 0), (48.3, 180))]
    return marks


def frame_traces(fd, focus):
    """Offense, defense, QB, ball and focus receiver for one frame."""
    off, dfn = fd[fd.side == "offense"], fd[fd.side == "defense"]
    qb, ball = fd[fd.pff_role == "Pass"], fd[fd.side == "ball"]
    rec = fd[fd.nflId == focus]
    txt = lambda d: d.jerseyNumber.fillna(0).astype(int).astype(str)
    mk = lambda d, name, color, size, text_color="white", symbol="circle", edge="white": go.Scatter(
        x=d.x, y=d.y, mode="markers+text", name=name, text=txt(d), textfont=dict(color=text_color, size=10, family=FONT),
        marker=dict(color=color, size=size, symbol=symbol, line=dict(color=edge, width=1.2)),
        hovertext=d.displayName, hoverinfo="text")
    return [mk(off, "Offense", OFFENSE, 20), mk(dfn, "Defense", ALERT, 20),
            mk(qb, "Quarterback", QB_GOLD, 26, INK, "star"), mk(rec, "Tracked receiver", "white", 24, OFFENSE, edge=OFFENSE),
            go.Scatter(x=ball.x, y=ball.y, mode="markers", name="Ball", hoverinfo="skip",
                       marker=dict(color=BALL, size=9, symbol="diamond", line=dict(color="white", width=1)))]


def frame_shapes(fd, focus, los):
    shapes = field_shapes(los)
    rec, qb = fd[fd.nflId == focus], fd[fd.pff_role == "Pass"]
    if len(rec) and pd.notna(rec.sep.iloc[0]):
        r = rec.iloc[0]
        shapes.append(circle(r.x, r.y, r.sep, OPEN_RING if r.sep >= C.OPEN_DIST else COVERED_RING))
    if len(qb) and pd.notna(qb.pocket.iloc[0]):
        q = qb.iloc[0]
        shapes.append(circle(q.x, q.y, q.pocket, QB_GOLD))
    return shapes


def play_figure(d, info):
    focus, los = info.nflId, d.los.iloc[0]
    fids = sorted(d.frameId.unique())
    t_open, t_press = info.t_open, info.t_pressure

    def title(t):
        rec = "open" if pd.notna(t_open) and t >= t_open else "covered"
        poc = "pressure" if pd.notna(t_press) and t >= t_press else "clean"
        return f"t = {t:.1f} s     Receiver: {rec}     Pocket: {poc}"

    frames = []
    for fid in fids:
        fd = d[d.frameId == fid]
        frames.append(go.Frame(name=str(fid), data=frame_traces(fd, focus),
                               layout=go.Layout(shapes=frame_shapes(fd, focus, los), title_text=title(fd.t.iloc[0]))))
    xs = d[d.side != "ball"].x
    pad = max(0, 50 - (xs.max() - xs.min() + 10)) / 2
    x0, x1 = xs.min() - 5 - pad, xs.max() + 5 + pad
    fig = go.Figure(data=frames[0].data, frames=frames, layout=go.Layout(shapes=frames[0].layout.shapes))
    style_fig(fig, 820)
    fig.update_layout(
        title=dict(text=title(d.t.min()), x=0.5, xanchor="center", font=dict(size=17, color=INK)),
        plot_bgcolor=FIELD, margin=dict(t=60, b=10, l=10, r=10),
        annotations=yard_numbers(x0, x1), showlegend=False,
        xaxis=dict(range=[x0, x1], showgrid=False, zeroline=False, constrain="domain", visible=False),
        yaxis=dict(range=[0, 53.3], showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1, visible=False),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=1.1, xanchor="left", bgcolor="white",
                          bordercolor=BORDER, font=dict(color=INK, family=FONT), buttons=[
            dict(label="Play", method="animate",
                 args=[None, dict(frame=dict(duration=100, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
            dict(label="Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])])],
        sliders=[dict(currentvalue=dict(visible=False), pad=dict(t=40), bgcolor="white", bordercolor=BORDER,
                      activebgcolor=ACCENT, tickcolor=MUTED, font=dict(color=MUTED, size=10), steps=[
            dict(method="animate", label="",
                 args=[[str(fid)], dict(mode="immediate", frame=dict(duration=0, redraw=True))]) for fid in fids])],
    )
    return fig



def timeline(info):
    """Snap -> receiver open -> pressure -> ball out, with the throwing window colored."""
    t_end = info.t_end
    span = max(t_end, info.t_open if pd.notna(info.t_open) else 0, info.t_pressure if pd.notna(info.t_pressure) else 0) + 0.3
    pct = lambda t: 100 * t / span
    marks = [("below", "Snap", 0.0), ("below", "Ball out", t_end)]
    if pd.notna(info.t_open):
        marks.append(("open", "Receiver open", info.t_open))
    if pd.notna(info.t_pressure):
        marks.append(("press", "Pressure", info.t_pressure))
    limit = info.t_pressure if pd.notna(info.t_pressure) else t_end
    if info.open_in_time:
        window = f'<div class="tl-window ok" style="left:{pct(info.t_open)}%;width:{pct(limit - info.t_open)}%"></div>'
        note = f"Window to throw: {limit - info.t_open:.1f} s"
    elif pd.notna(info.t_open) and pd.notna(info.t_pressure):
        window = (f'<div class="tl-window late" style="left:{pct(info.t_pressure)}%;'
                  f'width:{pct(info.t_open - info.t_pressure)}%"></div>')
        note = f"The pressure arrived {info.t_open - info.t_pressure:.1f} s before he got open"
    else:
        window, note = "", "He never got open before the ball was out"
    marks_html = "".join(f'<div class="tl-mark {cls}" style="left:{pct(t)}%"><span>{label}<b>{t:.1f} s</b></span></div>'
                         for cls, label, t in marks)
    return (f'<div class="tl"><div class="tl-track">{window}{marks_html}</div>'
            f'<div class="tl-space"></div><div class="tl-note">{note}</div></div>')


def story(info, qb_name):
    """The play told in one plain sentence."""
    name = html.escape(info.displayName)
    opened = f"got open at <b>{info.t_open:.1f} s</b>" if pd.notna(info.t_open) else "never got open"
    press = (f"the pass rush reached {html.escape(qb_name)} at <b>{info.t_pressure:.1f} s</b>"
             if pd.notna(info.t_pressure) else f"{html.escape(qb_name)} was never pressured")
    verdict = "He was open in time." if info.open_in_time else "It came too late."
    return f'<div class="story">{name} {opened}, and {press}. <b>{verdict}</b></div>'


LEGEND = (f'<div class="legend"><span><i style="background:{OFFENSE}"></i>Offense</span>'
          f'<span><i style="background:{ALERT}"></i>Defense</span>'
          f'<span><i style="background:{QB_GOLD}"></i>Quarterback (star)</span>'
          f'<span><i style="background:white;border:2px solid {OFFENSE}"></i>Tracked receiver</span>'
          f'<span><i class="ring" style="border-color:{OPEN_RING}"></i>Receiver ring: open</span>'
          f'<span><i class="ring" style="border-color:{COVERED_RING}"></i>Receiver ring: covered</span>'
          f'<span><i class="ring" style="border-color:{QB_GOLD}"></i>Pocket around the QB</span></div>')


def page_replay():
    st.markdown("### Play replay")
    dp = demo.drop_duplicates(["gameId", "playId"]).merge(pl[["gameId", "playId", "playDescription"]], on=["gameId", "playId"])
    dp = dp.sort_values(["demo_type", "score"], ascending=[False, False])
    labels = {f"{'Open in time' if r.demo_type == 'win' else 'Too late'}  |  {r.playDescription[:105]}": (r.gameId, r.playId)
              for r in dp.itertuples()}
    gid, pid = labels[st.selectbox("Choose a play", list(labels))]
    d = demo[(demo.gameId == gid) & (demo.playId == pid)]
    info = pr[(pr.gameId == gid) & (pr.playId == pid) & (pr.nflId == d.focus_nflId.iloc[0])].iloc[0]
    game = pl[(pl.gameId == gid) & (pl.playId == pid)].iloc[0]
    qb = d[d.pff_role == "Pass"].displayName
    k = st.columns([2, 1], vertical_alignment="center")
    k[0].markdown(f'<div class="matchup">{logo(game.possessionTeam, "")}{game.possessionTeam}<span class="at">vs</span>'
                  f'{logo(game.defensiveTeam, "")}{game.defensiveTeam}</div>', unsafe_allow_html=True)
    verdict = '<span class="verdict ok">OPEN IN TIME</span>' if info.open_in_time else '<span class="verdict late">TOO LATE</span>'
    k[1].markdown(f'<div style="text-align:right">{verdict}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-row">{headshot(info.nflId, "photo")}'
                f'{story(info, qb.iloc[0] if len(qb) else "the quarterback")}</div>', unsafe_allow_html=True)
    st.markdown(timeline(info), unsafe_allow_html=True)
    st.markdown(LEGEND, unsafe_allow_html=True)
    st.plotly_chart(play_figure(d, info), width="stretch", config=PLOT_CONFIG)


@st.cache_data
def team_summary():
    """One row per offense: receivers open in time, protection, completion and best receiver."""
    t = pr.groupby("team").agg(routes=("open_in_time", "size"), oit_pct=("open_in_time", "mean"))
    plays = pl.groupby("possessionTeam").agg(
        pressure_rate=("t_pressure", lambda s: s.notna().mean()), t_pressure=("t_pressure", "mean"),
        t_ball=("t_end", "median"), completion=("passResult", lambda s: (s == "C").sum() / s.isin(["C", "I", "IN"]).sum()))
    t = t.join(plays)
    best = ps[ps.nb_routes >= 80].sort_values("oit_pct", ascending=False).drop_duplicates("team").set_index("team")
    t["best"] = best.displayName
    for c in ["oit_pct", "pressure_rate", "completion"]:
        t[c] = t[c] * 100
    return t.sort_values("oit_pct", ascending=False).reset_index()


def page_teams():
    st.markdown("### Teams")
    st.markdown('<p class="muted">Which offenses give their receivers time? Left = the quarterback is rarely pressured '
                '(good offensive line). Up = receivers get open in time more often.</p>', unsafe_allow_html=True)
    t = team_summary()
    fig = go.Figure(go.Scatter(
        x=t.pressure_rate, y=t.oit_pct, mode="markers", marker=dict(size=1, color="rgba(0,0,0,0)"),
        customdata=t[["team", "completion", "best"]], hovertemplate=(
            "<b>%{customdata[0]}</b><br>Open in Time: %{y:.1f}%<br>Pressure rate: %{x:.1f}%"
            "<br>Completion: %{customdata[1]:.1f}%<br>Best receiver: %{customdata[2]}<extra></extra>")))
    fig.update_layout(images=[dict(source=LOGOS.get(r.team), x=r.pressure_rate, y=r.oit_pct, xref="x", yref="y",
                                   sizex=2.2, sizey=2.2, xanchor="center", yanchor="middle", layer="above")
                              for r in t.itertuples() if r.team in LOGOS])
    mx, my = t.pressure_rate.median(), t.oit_pct.median()
    fig.add_vline(x=mx, line_dash="dot", line_color=MUTED, line_width=1)
    fig.add_hline(y=my, line_dash="dot", line_color=MUTED, line_width=1)
    fig.add_annotation(x=t.pressure_rate.min(), y=t.oit_pct.max() + 1.5, xanchor="left", showarrow=False,
                       text="<b>Clean pocket, open receivers</b>", font=dict(color=ACCENT, size=14))
    style_fig(fig, 620)
    key = zoom_reset("teams_zoom")
    fig.update_layout(xaxis=dict(title="Pass plays with pressure on the QB (%), better protection to the left",
                                 range=[t.pressure_rate.min() - 3, t.pressure_rate.max() + 3]),
                      yaxis=dict(title="Routes open in time (%)", range=[t.oit_pct.min() - 3, t.oit_pct.max() + 3]))
    st.plotly_chart(fig, width="stretch", config=ZOOM_CONFIG, key=key)
    rows = "".join(
        f'<tr><td class="rank">{i}</td><td><div class="player">{logo(r.team)}{r.team}</div></td>'
        f'<td><div class="bar"><div class="track"><div class="fill" style="width:{r.oit_pct:.0f}%"></div></div>'
        f'<b>{r.oit_pct:.1f}%</b></div></td><td class="num">{r.pressure_rate:.1f}%</td>'
        f'<td class="num">{fmt(r.t_ball, " s")}</td><td class="num">{r.completion:.1f}%</td>'
        f'<td>{html.escape(str(r.best)) if pd.notna(r.best) else "n/a"}</td></tr>'
        for i, r in enumerate(t.itertuples(), 1))
    st.markdown(
        '<div class="tbl-wrap"><table class="board"><thead><tr><th>#</th><th>Team</th><th>Routes open in time</th>'
        '<th class="num">QB pressured</th><th class="num">Ball out (median)</th><th class="num">Completion</th>'
        f'<th>Best receiver (80+ routes)</th></tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)


def page_help():
    st.markdown("### Help")
    st.markdown(f"""
#### The idea in one sentence
On every pass play, we check whether the receiver gets open **before** the defense reaches the quarterback.
If he does, the quarterback can throw to him: he is **open in time**. If he gets open later, it is **too late**.

#### How it works
1. **The data.** Every NFL player wears a tracking chip. We know where each player is, **10 times per second**.
2. **Two distances, at every instant.** The distance between the receiver and the closest defender, and the
   distance between the quarterback and the closest pass rusher.
3. **Two clocks.** The *receiver clock* stops when he is at least {C.OPEN_DIST} yards from every defender
   (for {C.OPEN_SUSTAIN / C.FPS:.1f} s, after having been covered once). The *pressure clock* stops when a pass rusher
   gets within {C.PRESSURE_DIST} yards of the quarterback.
4. **The verdict.** Receiver clock first: open in time. Pressure clock first, or never open: too late.
5. **The score.** We repeat this on every route of every player, then count: *open in time 86 times out of 100*
   gives an Open in Time % of 86.

| Time after the snap | Receiver vs closest defender | Quarterback vs closest rusher |
|---|---|---|
| 0.5 s | 1 yard, covered | 8 yards, clean |
| 1.0 s | **3 yards, open** | 6 yards, clean |
| 2.5 s | 4 yards, open | **1 yard, pressure** |

Here the receiver is open at 1.0 s and the pressure arrives at 2.5 s: **open in time**.

#### Football words
- **Quarterback (QB):** the player who throws the ball.
- **Receivers:** the players who catch it. **WR** (wide receiver) lines up wide and runs the longest routes,
  **TE** (tight end) lines up next to the linemen, **RB** (running back) starts behind the quarterback.
- **Snap:** the moment the play starts. Both clocks start here.
- **Route:** the path a receiver runs on a play to get open.
- **Pass rush / pressure:** defenders charging the quarterback to hit him before he throws.
- **Man coverage:** each defender follows one receiver. **Zone coverage:** each defender guards an area.
- **Completion:** the pass is caught. **Yards:** distance gained (1 yard = 0.91 m).

#### What each tab shows
- **Overview:** the proof that the idea matters (completion rate with and without a receiver open in time) and the best players by position.
- **Leaderboard:** every receiver ranked. *Time to open* = how fast he gets open (lower is better).
  *Time to pressure* = how long his quarterback is protected (depends on his team, not on him).
- **Teams:** every offense placed by how well it protects its quarterback (left = rarely pressured) and how often its receivers get open in time (up).
- **Hidden gems:** each dot is a player. Bottom left = gets open fast but poorly protected: undervalued.
- **Players:** one player's numbers and every route he ran, with the verdict of each one.
- **Play replay:** a real play animated from above, with the two clocks and the verdict.
- **Search** (top right): type a name to open his player card.

#### Who uses it
- **Scouts:** find receivers better than their stats, held back by a weak offensive line.
- **Coaches:** know which receiver to trust when protection breaks down.
- **Broadcasters:** show on a replay why a play worked or died.

#### What the numbers reveal
- When the targeted receiver is open in time, the pass is caught **69.9%** of the time, against **47.2%** otherwise.
- A typical receiver gets open at **1.5 s**; when the pass rush gets home, it arrives at **2.7 s**.
- RBs and TEs are open in time more often than WRs: defenses leave them free underneath. Compare players **within a position**.
- Star WRs rank lower because they draw the tightest coverage, sometimes two defenders.

#### Columns and codes
| Name | Meaning |
|---|---|
| **Routes** | Number of plays where the player ran a route |
| **Open in Time %** | Share of his routes where he got open before the pressure |
| **Time to open** | Average seconds after the snap to get open (lower is better) |
| **Time to pressure** | Average seconds before a rusher reaches his QB (depends on his team) |
| **vs Man / vs Zone** | Open in Time % against man coverage and against zone coverage |
| **Max sep** | Largest distance from the nearest defender on the play, in yards |
| **Targeted** | Checked when the ball was thrown to him |
| **Ball out** | Seconds after the snap when the ball was thrown (or the QB was sacked) |
| **Result** | C = caught, I = incomplete, IN = intercepted, S = sack |
| **Verdict** | Open in time, Too late (open after the pressure) or Never open |

#### Limits
- Tracking stops shortly after the throw: we judge separation up to the release, not at the catch.
- Short routes get open earlier than deep routes, so the score depends on the role of the player.
- Thresholds ({C.OPEN_DIST} yards to be open, {C.PRESSURE_DIST} yards for pressure) are fixed and simple.

#### Data
NFL tracking data, 2021 season, weeks 1 to 8: {len(pl):,} pass plays (scrambles excluded) and {len(ps)} players with at least {C.MIN_ROUTES} routes.
""")


# ---------- Help button: a short guide for the page you are on ----------
GUIDES = {
    "Overview": """1. **Read the bar chart first.** When the targeted receiver is open in time, the pass is caught far more often (green) than when he is not (red). This proves the idea matters.
2. **The sentence under it** gives the two typical clocks: when a receiver gets open, and when the pass rush arrives.
3. **Leaders by position** shows the 5 best WRs, TEs and RBs. Click **Players** or use the search to see one in detail.""",
    "Leaderboard": """1. **Pick filters:** a position (WR, TE, RB), one or more teams, and a minimum number of routes (more routes = more reliable score).
2. **Choose a sort:** best Open in Time %, fastest to get open, most routes, or least protected.
3. **Read a row:** the green bar is the share of routes where the player got open before the pressure. *Time to open* is his speed (lower is better). *Time to pressure* is how long his QB is protected (his team's job, not his).
4. Compare players **of the same position**: RBs and TEs are often left free, star WRs are tightly covered.""",
    "Teams": """1. **Each logo is an offense.** Left = its quarterback is rarely pressured (good offensive line). Up = its receivers get open in time more often.
2. **Top left** is the dream: clean pocket and open receivers.
3. **Hover a logo** for its completion rate and best receiver. Drag to zoom, **Reset zoom** to come back.
4. **The table** below ranks all 32 teams.""",
    "Hidden gems": """1. **Each dot is a player.** Left = he gets open fast. Down = his quarterback gets pressured early.
2. **The green box (bottom left)** holds the hidden gems: fast to get open, but poorly protected. Their stats look worse than their real level, so a scout can get them cheap.
3. **Hover a dot** to see the name. Drag to zoom, **Reset zoom** (or double-click) to zoom back out.
4. Use the filters to look at one position or one team.""",
    "Players": """1. **Choose a player** in the list, or type his name in the search bar at the top.
2. **The 5 boxes:** his Open in Time %, his average time to get open, how long his QB is protected, and his score against man coverage (a defender follows him) and zone coverage (defenders guard areas).
3. **Every route:** one line per play, with the verdict (open in time, too late, never open), the two clocks, whether the ball was thrown to him (Targeted) and the result (C = caught, I = incomplete, IN = intercepted, S = sack).""",
    "Play replay": """1. **Choose a play** in the list: *Open in time* plays worked, *Too late* plays did not.
2. **Read the sentence and the timeline:** when the receiver got open, when the pressure arrived, and the window the QB had to throw (green) or the delay (red).
3. **Press Play** on the field. The white dot is the receiver: his ring turns **green** when he is open. The **gold ring** around the quarterback (star) shrinks as the rush closes in.
4. Use the slider under the field to go frame by frame.""",
    "Help": """This page explains the whole project: the idea, how it is computed, the football words and every tab. The **Help** button in the top bar gives a short guide for the page you are on.""",
}


# ---------- layout: top navigation + product bar with player search ----------
players_page = st.Page(page_players, title="Players", url_path="players")
pages = [st.Page(page_overview, title="Overview", url_path="overview", default=True),
         st.Page(page_leaderboard, title="Leaderboard", url_path="leaderboard"),
         st.Page(page_hidden_gems, title="Hidden gems", url_path="hidden-gems"),
         st.Page(page_teams, title="Teams", url_path="teams"),
         players_page,
         st.Page(page_replay, title="Play replay", url_path="replay"),
         st.Page(page_help, title="Help", url_path="help")]
nav = st.navigation(pages, position="top")


def on_search():
    """Open the searched player's card."""
    st.session_state.selected_player = st.session_state.search
    st.session_state.search = None
    st.session_state.goto_players = True


left, mid, right = st.columns([3, 0.55, 1.2], vertical_alignment="center")
left.markdown(f'<div class="brand-row"><img src="{NFL_LOGO}" alt="NFL"><div class="brand">OPEN IN TIME'
              '<span>Receiver separation vs the pass rush clock</span></div></div>', unsafe_allow_html=True)
with mid.popover("Help", width="stretch"):
    st.markdown(f"**{nav.title}: how to read this page**")
    st.markdown(GUIDES.get(nav.title, "Pick a tab in the top bar."))
right.selectbox("Search a player", sorted(ps.displayName), index=None, placeholder="Search a player",
                label_visibility="collapsed", key="search", on_change=on_search)
st.markdown("<hr>", unsafe_allow_html=True)
if st.session_state.pop("goto_players", False):
    st.switch_page(players_page)
nav.run()
