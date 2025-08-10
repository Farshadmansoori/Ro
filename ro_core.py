# ro_core.py — RO normalization core (simplified) for on-device use
import io, math, json
import pandas as pd
import numpy as np

def water_viscosity_mPa_s(Tc: float) -> float:
    T = Tc + 273.15
    A, B, C = 2.414e-5, 247.8, 140.0
    mu_Pa_s = A * 10**(B/(T - C))
    return mu_Pa_s * 1000

def stcf_from_viscosity(Tc: float, Tref: float = 25.0) -> float:
    return water_viscosity_mPa_s(Tc) / water_viscosity_mPa_s(Tref)

def osmotic_pressure_bar(Tc: float, TDS_mg_L: float, i: float = 2.0):
    gL = TDS_mg_L / 1000.0
    T = Tc + 273.15
    return 0.8 * gL * (T / 298.15) * (i / 2.0)

def tmp_effective_bar(P_feed, P_perm, pi_feed, alpha=1.0):
    return (P_feed - P_perm) - alpha * pi_feed

def normalize_Qp(Qp_meas, Tc, TMP_eff, TMP_ref=10.0, Tref=25.0):
    TMP_eff = max(float(TMP_eff), 0.1)
    TMP_ref = max(float(TMP_ref), 0.1)
    stcf = stcf_from_viscosity(float(Tc), Tref)
    return float(Qp_meas) * stcf * (TMP_ref / TMP_eff)

def process_csv_text(csv_text: str) -> str:
    # Expect columns: time(optional), T_C, Qp_m3h, P_feed_bar, P_perm_bar, Cond_feed_mgL, Cond_perm_mgL, dP_bar
    df = pd.read_csv(io.StringIO(csv_text))
    # Try flexible column names
    ren = { 
        'Temperature','T','temp','Temp','t_C','t_c','T_C',
        'Qp','PermeateFlow','Qp_m3h',
        'Pfeed','P_feed','Pfeed_bar','P_feed_bar',
        'Pperm','P_perm','Pperm_bar','P_perm_bar',
        'Cf','Cond_feed','CondFeed','Cond_feed_mgL',
        'Cp','Cond_perm','CondPerm','Cond_perm_mgL',
        'dP','dP_bar','DP','DeltaP'
    }
    # Minimal normalize of columns if common variants exist
    cols = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in cols: return cols[n.lower()]
        return None

    c_T  = pick('T_C','t_C','Temp','Temperature')
    c_Qp = pick('Qp_m3h','Qp')
    c_Pf = pick('P_feed_bar','Pfeed_bar','P_feed')
    c_Pp = pick('P_perm_bar','Pperm_bar','P_perm')
    c_Cf = pick('Cond_feed_mgL','Cf','CondFeed')
    c_Cp = pick('Cond_perm_mgL','Cp','CondPerm')
    c_dP = pick('dP_bar','dP','DeltaP')

    out = []
    for _, r in df.iterrows():
        try:
            T = float(r[c_T]) if c_T else np.nan
            Qp = float(r[c_Qp]) if c_Qp else np.nan
            Pf = float(r[c_Pf]) if c_Pf else np.nan
            Pp = float(r[c_Pp]) if c_Pp else np.nan
            Cf = float(r[c_Cf]) if c_Cf else np.nan
            Cp = float(r[c_Cp]) if c_Cp else np.nan
            dP = float(r[c_dP]) if c_dP else np.nan

            pi = osmotic_pressure_bar(T, Cf) if np.isfinite(T) and np.isfinite(Cf) else np.nan
            TMP_eff = tmp_effective_bar(Pf, Pp, pi) if all(np.isfinite(x) for x in [Pf,Pp,pi]) else np.nan
            Qp_norm = normalize_Qp(Qp, T, TMP_eff) if all(np.isfinite(x) for x in [Qp,T,TMP_eff]) else np.nan
            sp = (Cp/Cf*100.0) if all(np.isfinite(x) for x in [Cp,Cf]) and Cf>0 else np.nan

            out.append((Qp_norm, sp, dP))
        except Exception:
            out.append((np.nan, np.nan, np.nan))

    arr = np.array(out, dtype=float)
    def stat(col):
        s = arr[:, col]
        s = s[np.isfinite(s)]
        if s.size == 0: return {"mean": None, "std": None}
        return {"mean": float(s.mean()), "std": float(s.std())}

    summary = {
        "Qp_norm_25C_m3h": stat(0),
        "SaltPass_%":      stat(1),
        "dP_bar":          stat(2),
        "rows": int(len(df))
    }
    return json.dumps(summary, ensure_ascii=False)

def quick_test(Tc: float, tds_mgL: float):
    pi = osmotic_pressure_bar(Tc, tds_mgL)
    return {"T_C": Tc, "TDS_mgL": tds_mgL, "pi_bar": round(pi, 3)}
