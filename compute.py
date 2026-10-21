"""Compute Open in Time from the tracking data and write parquet files in cache/.

Usage: python compute.py [--sample N] [--workers W]
"""
import argparse
import math
import time
from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd

import config as C

KEY = ["gameId", "playId"]
TRACK_DTYPES = {
    "gameId": "int64", "playId": "int32", "nflId": "float64", "frameId": "int32",
    "jerseyNumber": "float32", "team": "category", "playDirection": "category",
    "x": "float32", "y": "float32", "o": "float32", "dir": "float32", "event": "category",
}
META = None  # (plays, players, pff), set in each worker


# ---------- loading ----------

def load_meta():
    """Plays kept, player info and PFF roles (QB, routes, rushers only)."""
    plays = pd.read_csv(C.DATA_DIR / "plays.csv", usecols=[
        "gameId", "playId", "playDescription", "possessionTeam", "defensiveTeam",
        "passResult", "playResult", "pff_passCoverageType"])
    plays = plays[plays.passResult.isin(C.PASS_RESULTS)]
    players = pd.read_csv(C.DATA_DIR / "players.csv", usecols=["nflId", "officialPosition", "displayName"])
    pff = pd.read_csv(C.DATA_DIR / "pffScoutingData.csv", usecols=["gameId", "playId", "nflId", "pff_role"])
    pff = pff[pff.pff_role.isin(["Pass", "Pass Route", "Pass Rush"])]
    return plays, players, pff


def read_tracking(path, plays):
    """Read one game, keep retained plays, normalize so offense goes right."""
    df = pd.read_csv(path, usecols=list(TRACK_DTYPES), dtype=TRACK_DTYPES)
    df = df.merge(plays[KEY + ["possessionTeam", "defensiveTeam"]], on=KEY)
    left = df.playDirection == "left"
    df.loc[left, "x"] = 120 - df.loc[left, "x"]
    df.loc[left, "y"] = 53.3 - df.loc[left, "y"]
    df.loc[left, "o"] = (df.loc[left, "o"] + 180) % 360
    df.loc[left, "dir"] = (df.loc[left, "dir"] + 180) % 360
    return df


def snap_end_frames(df):
    """Snap frame, end frame (pass/sack, else last frame) and line of scrimmage per play."""
    ev = df[KEY + ["frameId", "event"]].drop_duplicates()
    snap = ev[ev.event.isin(C.SNAP_EVENTS)].groupby(KEY).frameId.min().rename("snap")
    ev = ev.join(snap, on=KEY, how="inner")
    end = ev[(ev.frameId > ev.snap) & ev.event.isin(C.END_EVENTS)].groupby(KEY).frameId.min().rename("end")
    last = df.groupby(KEY).frameId.max().rename("last")
    fr = snap.to_frame().join(end).join(last)
    fr["end"] = fr.end.fillna(fr["last"])
    fr = fr[["snap", "end"]].astype(int).reset_index()
    # Line of scrimmage = ball x at the snap
    ball = df[df.team == "football"].merge(fr, on=KEY)
    los = ball[ball.frameId == ball.snap].set_index(KEY).x.rename("los")
    return fr.join(los, on=KEY)


# ---------- distances ----------

def min_dist(a, b):
    """For each row of a: distance to the closest row of b at the same play and frame."""
    m = a[KEY + ["frameId", "nflId", "x", "y"]].merge(
        b[KEY + ["frameId", "x", "y"]], on=KEY + ["frameId"], suffixes=("", "_b"))
    m["d"] = np.hypot(m.x - m.x_b, m.y - m.y_b)
    return m.groupby(KEY + ["nflId", "frameId"], as_index=False).d.min()


def open_frames(sep, fr):
    """First frame (after snap + min time, <= end) where separation >= OPEN_DIST for OPEN_SUSTAIN frames.

    Earned separation: the receiver must have been covered (< OPEN_DIST) at least once since the snap,
    so the cushion a cornerback gives at the snap does not count as being open. A receiver never
    covered counts as open from OPEN_UNCOVERED_TIME (blown coverage).
    """
    s = sep.merge(fr, on=KEY).sort_values(KEY + ["nflId", "frameId"])
    ok = s.d >= C.OPEN_DIST
    groups = ok.groupby([s.gameId, s.playId, s.nflId])
    sustained = ok.copy()
    for k in range(1, C.OPEN_SUSTAIN):
        sustained &= groups.shift(-k).fillna(False).astype(bool)
    covered = (~ok).groupby([s.gameId, s.playId, s.nflId]).cummax()
    covered |= s.frameId >= s.snap + round(C.OPEN_UNCOVERED_TIME * C.FPS)
    start = s.frameId >= s.snap + round(C.OPEN_MIN_TIME * C.FPS)
    first = s[sustained & covered & start & (s.frameId <= s.end)].groupby(KEY + ["nflId"]).frameId.min()
    max_sep = s[s.frameId <= s.end].groupby(KEY + ["nflId"]).d.max()
    return pd.concat([first.rename("open_frame"), max_sep.rename("max_separation")], axis=1).reset_index()


def pressure_frames(qb_d, fr):
    """First frame after snap + min time (<= end) where a pass rusher is within PRESSURE_DIST of the QB.

    The QB must first have been clear (>= PRESSURE_CLEAR_DIST): under center, a defensive tackle is
    already ~2 yd away at the snap, which is not pressure.
    """
    q = qb_d.merge(fr, on=KEY).sort_values(KEY + ["frameId"])
    cleared = (q.d >= C.PRESSURE_CLEAR_DIST).groupby([q.gameId, q.playId]).cummax()
    start = q.snap + round(C.PRESSURE_MIN_TIME * C.FPS)
    hit = q[(q.d < C.PRESSURE_DIST) & cleared & (q.frameId >= start) & (q.frameId <= q.end)]
    return hit.groupby(KEY).frameId.min().rename("pressure_frame").reset_index()


# ---------- one game ----------

def process_game(path):
    plays, players, pff = META
    df = read_tracking(path, plays)
    fr = snap_end_frames(df)
    df = df.merge(fr, on=KEY)
    df = df[(df.frameId >= df.snap) & (df.frameId <= df.end + C.EXTRA_FRAMES)]
    df = df.merge(pff, on=KEY + ["nflId"], how="left").merge(players, on="nflId", how="left")

    recv = df[(df.pff_role == "Pass Route") & df.officialPosition.isin(C.RECEIVER_POSITIONS)]
    defense = df[df.team.astype(str) == df.defensiveTeam]
    qb, rush = df[df.pff_role == "Pass"], df[df.pff_role == "Pass Rush"]

    sep = min_dist(recv, defense)
    qb_d = min_dist(qb, rush)
    pr = build_receivers(recv, open_frames(sep, fr), pressure_frames(qb_d, fr), fr, plays)
    pl = build_plays(pr, fr, plays)
    demo = demo_candidates(df, pr, sep, qb_d)
    return pr, pl, demo


def build_receivers(recv, opens, press, fr, plays):
    """One row per (play, receiver) with the two clocks and the verdict."""
    pr = recv[KEY + ["nflId", "displayName", "officialPosition", "possessionTeam"]].drop_duplicates(KEY + ["nflId"])
    pr = pr.rename(columns={"officialPosition": "position", "possessionTeam": "team"})
    pr = pr.merge(opens, on=KEY + ["nflId"], how="left").merge(press, on=KEY, how="left").merge(fr, on=KEY)
    pr = pr.merge(plays[KEY + ["pff_passCoverageType", "passResult", "playResult", "playDescription"]], on=KEY)
    # Targeted receiver: "pass ... to C.Godwin" in the play description
    pr["is_target"] = [f" to {short_name(n)}" in str(d) for n, d in zip(pr.displayName, pr.playDescription)]
    pr["t_open"] = (pr.open_frame - pr.snap) / C.FPS
    pr["t_pressure"] = (pr.pressure_frame - pr.snap) / C.FPS
    pr["t_end"] = (pr.end - pr.snap) / C.FPS
    pr["open_in_time"] = pr.open_frame.notna() & (pr.pressure_frame.isna() | (pr.open_frame < pr.pressure_frame))
    return pr


def short_name(name):
    """'Chris Godwin' -> 'C.Godwin' (format used in playDescription)."""
    parts = str(name).split(" ")
    return f"{parts[0][0]}.{parts[-1]}" if len(parts) > 1 else str(name)


def build_plays(pr, fr, plays):
    """One row per play: was the targeted receiver (and was any receiver) open in time?"""
    any_oit = pr.groupby(KEY).open_in_time.any().rename("any_open_in_time")
    tgt = pr[pr.is_target].drop_duplicates(KEY).set_index(KEY)
    pl = fr.merge(plays, on=KEY).join(any_oit, on=KEY)
    pl["any_open_in_time"] = pl.any_open_in_time.fillna(False).astype(bool)
    pl = pl.join(tgt.open_in_time.rename("target_open_in_time"), on=KEY)
    pl = pl.join(tgt.displayName.rename("target_name"), on=KEY)
    t_press = pr.groupby(KEY).t_pressure.first()
    return pl.join(t_press, on=KEY).assign(t_end=lambda d: (d.end - d.snap) / C.FPS)


# ---------- demo plays for the animation ----------

def demo_candidates(df, pr, sep, qb_d):
    """Keep the clearest win and the clearest loss of the game (pressure on both)."""
    p = pr[pr.t_pressure.notna() & pr.t_open.notna() & (pr.t_end <= C.DEMO_MAX_TIME)].copy()
    p["margin"] = p.t_pressure - p.t_open
    oit_play = p.groupby(KEY).open_in_time.transform("any")
    wins = p[p.open_in_time & p.is_target & (p.passResult == "C")].sort_values("margin", ascending=False)
    losses = p[~oit_play & p.passResult.isin(["I", "IN", "S"])].sort_values("margin")
    picks = []
    for kind, cand in [("win", wins), ("loss", losses)]:
        if len(cand):
            row = cand.iloc[0]
            picks.append({"gameId": row.gameId, "playId": row.playId, "focus_nflId": row.nflId,
                          "demo_type": kind, "score": abs(row.margin)})
    if not picks:
        return pd.DataFrame()
    picks = pd.DataFrame(picks)
    f = df.merge(picks, on=KEY)
    f = f.merge(sep.rename(columns={"d": "sep"}), on=KEY + ["nflId", "frameId"], how="left")
    f = f.merge(qb_d.rename(columns={"d": "pocket"}), on=KEY + ["nflId", "frameId"], how="left")
    f["t"] = (f.frameId - f.snap) / C.FPS
    f["side"] = np.where(f.team == "football", "ball",
                         np.where(f.team.astype(str) == f.defensiveTeam, "defense", "offense"))
    cols = KEY + ["nflId", "frameId", "t", "x", "y", "jerseyNumber", "displayName", "officialPosition",
                  "pff_role", "side", "sep", "pocket", "los", "snap", "end", "focus_nflId", "demo_type", "score"]
    return f[cols]


# ---------- summaries ----------

def player_summary(pr):
    """One row per player with enough routes."""
    g = pr.groupby("nflId")
    s = g.agg(displayName=("displayName", "first"), position=("position", "first"), team=("team", "last"),
              nb_routes=("open_in_time", "size"), oit_pct=("open_in_time", "mean"),
              t_open_moyen=("t_open", "mean"), t_pressure_moyen=("t_pressure", "mean"))
    vs = pr.pivot_table(index="nflId", columns="pff_passCoverageType", values="open_in_time", aggfunc="mean")
    s["oit_pct_vs_man"] = vs.get("Man")
    s["oit_pct_vs_zone"] = vs.get("Zone")
    for c in ["oit_pct", "oit_pct_vs_man", "oit_pct_vs_zone"]:
        s[c] = (s[c] * 100).round(1)
    s = s[s.nb_routes >= C.MIN_ROUTES].sort_values("oit_pct", ascending=False)
    return s.reset_index()


def select_demo(demo):
    """Keep the N_DEMO_PLAYS clearest plays, half wins half losses."""
    plays = demo[KEY + ["demo_type", "score"]].drop_duplicates(KEY)
    half = C.N_DEMO_PLAYS // 2
    keep = plays.sort_values("score", ascending=False).groupby("demo_type").head(half)
    return demo.merge(keep[KEY], on=KEY)


def completion_gap(att, col):
    """Print completion rate for col True vs False, with a two-proportion z-test."""
    rates = {}
    for flag, grp in att.groupby(col):
        rates[bool(flag)] = ((grp.passResult == "C").mean(), len(grp))
        print(f"  {col} = {bool(flag)}: {rates[bool(flag)][0]:.1%}  (n={len(grp)})")
    if len(rates) == 2:
        (p1, n1), (p0, n0) = rates[True], rates[False]
        p = (p1 * n1 + p0 * n0) / (n1 + n0)
        z = (p1 - p0) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n0))
        print(f"  Gap: {100 * (p1 - p0):+.1f} pts, z = {z:.1f} ({'significant' if abs(z) > 1.96 else 'NOT significant'} at 5%)")


def report(pl, ps):
    """Print the key numbers: completion rate with vs without a receiver open in time."""
    att = pl[pl.passResult.isin(["C", "I", "IN"])]
    print(f"\nPlays analysed: {len(pl)}  (pass attempts: {len(att)}, sacks: {(pl.passResult == 'S').sum()})")
    print(f"Plays with at least one receiver open in time: {pl.any_open_in_time.mean():.1%}")
    print(f"Plays with pressure (rusher < {C.PRESSURE_DIST} yd from QB): {pl.t_pressure.notna().mean():.1%}")
    tgt = att[att.target_open_in_time.notna()]
    print(f"Attempts with the targeted receiver identified: {len(tgt)}")
    print("Completion rate by TARGETED receiver open in time (main result):")
    completion_gap(tgt, "target_open_in_time")
    print("Completion rate by ANY receiver open in time (secondary):")
    completion_gap(att, "any_open_in_time")
    sack = pl.groupby("any_open_in_time").passResult.apply(lambda s: (s == "S").mean())
    print(f"Sack rate: some receiver open in time {sack.get(True, np.nan):.1%} vs none {sack.get(False, np.nan):.1%}")
    cols = ["displayName", "position", "team", "nb_routes", "oit_pct", "t_open_moyen", "t_pressure_moyen"]
    print(f"\nTop 10 (min {C.MIN_ROUTES} routes):\n{ps[cols].head(10).to_string(index=False)}")
    print(f"\nBottom 10:\n{ps[cols].tail(10).to_string(index=False)}")


# ---------- main ----------

def init_worker(meta):
    global META
    META = meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, help="only process the first N games")
    ap.add_argument("--workers", type=int, default=min(8, cpu_count()))
    args = ap.parse_args()

    meta = load_meta()
    files = sorted((C.DATA_DIR / "tracking").glob("tracking_*.csv"))[: args.sample]
    t0 = time.time()
    results = []
    with Pool(args.workers, initializer=init_worker, initargs=(meta,)) as pool:
        for i, res in enumerate(pool.imap_unordered(process_game, files), 1):
            results.append(res)
            print(f"\r[{'#' * (30 * i // len(files)):<30}] {i}/{len(files)} games  {time.time() - t0:.0f}s", end="", flush=True)
    print()

    pr = pd.concat([r[0] for r in results], ignore_index=True)
    pl = pd.concat([r[1] for r in results], ignore_index=True)
    demo = select_demo(pd.concat([r[2] for r in results], ignore_index=True))
    ps = player_summary(pr)

    C.CACHE_DIR.mkdir(exist_ok=True)
    pr_cols = KEY + ["nflId", "displayName", "position", "team", "t_open", "t_pressure", "t_end",
                     "open_in_time", "is_target", "max_separation", "pff_passCoverageType", "passResult", "playResult"]
    pr[pr_cols].to_parquet(C.CACHE_DIR / "play_receiver.parquet", index=False)
    ps.to_parquet(C.CACHE_DIR / "player_summary.parquet", index=False)
    pl[KEY + ["playDescription", "possessionTeam", "defensiveTeam", "passResult", "playResult",
              "pff_passCoverageType", "any_open_in_time", "target_open_in_time", "target_name",
              "t_pressure", "t_end", "los"]].to_parquet(
        C.CACHE_DIR / "play_level.parquet", index=False)
    demo.to_parquet(C.CACHE_DIR / "frames_demo.parquet", index=False)

    report(pl, ps)
    print(f"\nDone in {time.time() - t0:.0f}s. Files written to {C.CACHE_DIR}")


if __name__ == "__main__":
    main()
