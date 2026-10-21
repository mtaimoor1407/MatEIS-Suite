"""Theme 3: Corrosion Rate & Kinetics Calculator."""
from __future__ import annotations

from nicegui import ui

from core.corrosion.emf import ENVIRONMENT_FACTORS, assess_couple, delta_matrix
from core.corrosion.materials import MATERIALS, get_material
from core.corrosion.protection import ANODES, ENVIRONMENTS, get_environment, recommend, recommended_anode, size_anodes
from core.corrosion.rates import (
    butler_volmer_data,
    electrochemical_rate,
    service_life,
    stern_geary,
    tafel_extrapolation,
    weight_loss_rate,
)
from core.exceptions import MatEISError, ValidationError
from core.reporting.corrosion_report import corrosion_pdf
from ui.components.kit import (
    chip,
    esc,
    fmt,
    formula_block,
    ghost_button,
    metric,
    notice,
    panel,
    primary_button,
    rating_scale,
    table_html,
)
from ui.components.parsing import parse_polarization
from ui.figures.corrosion_fig import ladder_plotly, matrix_plotly, tafel_plotly
from ui.layout import frame, is_dark
from ui.services import get_services

MASS_UNITS = {"g": 1.0, "mg": 1e-3}
AREA_UNITS = {"cm²": 1.0, "in²": 6.4516, "m²": 1e4}
TIME_UNITS = {"hours": 1.0, "days": 24.0, "weeks": 168.0}
CURRENT_UNITS = {"µA/cm²": 1.0, "mA/cm²": 1e3, "A/m²": 100.0, "nA/cm²": 1e-3}
METHODS = {"wl": "Weight loss", "icorr": "Corrosion current", "tafel": "Tafel extrapolation", "rp": "Polarization resistance"}
DEFAULT_PAIR = {"seawater": ("Carbon / mild steel", "Copper"), "standard": ("Iron", "Copper")}
PRIORITY = {1: ("Primary", "var(--verd)"), 2: ("Supporting", "var(--steel)"), 3: ("Consider", "var(--faint)")}
REPORT_TAB = "4  Report"


def _num(widget, name: str) -> float:
    if widget.value is None or widget.value == "":
        raise ValidationError(f"{name} is required.")
    return float(widget.value)


@ui.page("/corrosion")
def corrosion_page() -> None:
    svc = get_services()
    dark = is_dark()
    S: dict = {"rate": None, "tafel": None, "galv": None, "recs": None, "anode": None, "mat": "carbon_steel", "env": "Seawater immersion", "life": 25.0}
    mat_options = {k: m.name for k, m in MATERIALS.items()}

    with frame("corrosion", "Corrosion", "Calculate corrosion rate from weight loss or electrochemical data, check galvanic compatibility, and get a protection plan.", "corrosion"):
        with ui.tabs().classes("w-full") as tabs:
            t_rate = ui.tab("1  Corrosion rate")
            t_gal = ui.tab("2  Galvanic risk")
            t_prot = ui.tab("3  Protection plan")
            ui.tab(REPORT_TAB)
        with ui.tab_panels(tabs, value=t_rate).classes("w-full bg-transparent"):
            # ============================================================ RATE
            with ui.tab_panel(t_rate).classes("p-0 pt-4"):
                with ui.element("div").classes("mx-grid-side"):
                    with ui.column().classes("gap-4 w-full"):
                        with panel("Method and material", accent=True):
                            method = ui.toggle(METHODS, value="wl").props("no-caps unelevated dense toggle-color=none toggle-text-color=none").classes("w-full flex-wrap")
                            ui.html('<div class="mx-label" style="margin:14px 0 6px">Material</div>', sanitize=False)
                            mat = ui.select({**mat_options, "custom": "Custom (enter values)"}, value="carbon_steel").props("outlined dense").classes("w-full")
                            mat_info = ui.html("", sanitize=False)
                            with ui.row().classes("w-full no-wrap gap-2") as custom_row:
                                c_rho = ui.number("Density (g/cm³)", value=7.85, min=0.001).props("outlined dense").classes("col")
                                c_ew = ui.number("Equivalent weight", value=27.92, min=0.001).props("outlined dense").classes("col")
                            custom_row.set_visibility(False)
                        with panel("Coupon data") as g_wl:
                            with ui.row().classes("w-full no-wrap gap-2"):
                                wl_m0 = ui.number("Initial mass", value=10.0, step=0.001, format="%.5g").props("outlined dense").classes("col")
                                wl_m1 = ui.number("Final mass", value=9.98, step=0.001, format="%.5g").props("outlined dense").classes("col")
                                wl_mu = ui.select(list(MASS_UNITS), value="g").props("outlined dense").classes("w-20")
                            with ui.row().classes("w-full no-wrap gap-2 q-mt-sm"):
                                wl_a = ui.number("Exposed area", value=20.0, min=0, step=1, format="%.5g").props("outlined dense").classes("col")
                                wl_au = ui.select(list(AREA_UNITS), value="cm²").props("outlined dense").classes("w-24")
                            with ui.row().classes("w-full no-wrap gap-2 q-mt-sm"):
                                wl_t = ui.number("Exposure time", value=720.0, min=0, step=1, format="%.5g").props("outlined dense").classes("col")
                                wl_tu = ui.select(list(TIME_UNITS), value="hours").props("outlined dense").classes("w-28")
                        with panel("Electrochemical data") as g_ic:
                            with ui.row().classes("w-full no-wrap gap-2"):
                                ic_i = ui.number("Corrosion current density i_corr", value=10.0, min=0, format="%.5g").props("outlined dense").classes("col")
                                ic_u = ui.select(list(CURRENT_UNITS), value="µA/cm²").props("outlined dense").classes("w-28")
                        with panel("Polarization curve") as g_tf:
                            ui.html('<div style="color:var(--soft);font-size:13.5px;margin-bottom:8px">One point per line: <b>potential (V), current density (A/cm²)</b>. '
                                    'Anodic current positive, cathodic negative (or all positive).</div>', sanitize=False)
                            tf_text = ui.textarea(placeholder="-0.700, -3.1e-4\n-0.690, -2.6e-4\n...").props("outlined dense rows=9 input-style='font-family:monospace;font-size:12.5px'").classes("w-full")
                            with ui.row().classes("w-full no-wrap gap-2 q-mt-sm"):
                                tf_ecorr = ui.number("E_corr (V)", value=-0.45, step=0.01, format="%.4g").props("outlined dense").classes("col")
                                tf_w1 = ui.number("Window from (mV)", value=100, min=0).props("outlined dense").classes("col")
                                tf_w2 = ui.number("to (mV)", value=300, min=0).props("outlined dense").classes("col")
                            ghost_button("Load example data", lambda: load_example(), "science").classes("q-mt-sm")
                        with panel("Linear polarization") as g_rp:
                            rp_r = ui.number("Polarization resistance R_p (Ω·cm²)", value=5000.0, min=0, format="%.6g").props("outlined dense").classes("w-full")
                            with ui.row().classes("w-full no-wrap gap-2 q-mt-sm"):
                                rp_ba = ui.number("β_a (mV/decade)", value=80, min=0).props("outlined dense").classes("col")
                                rp_bc = ui.number("β_c (mV/decade)", value=120, min=0).props("outlined dense").classes("col")
                        primary_button("Calculate", lambda: calculate(), "calculate")
                    rate_out = ui.column().classes("gap-4 w-full min-w-0")

            # ============================================================ GALVANIC
            with ui.tab_panel(t_gal).classes("p-0 pt-4"):
                with ui.element("div").classes("mx-grid-side"):
                    with ui.column().classes("gap-4 w-full"):
                        with panel("Couple", "Two metals in electrical contact in the same electrolyte.", accent=True):
                            series = ui.toggle({"seawater": "Seawater series", "standard": "EMF series"}, value="seawater").props("no-caps unelevated dense toggle-color=none toggle-text-color=none").classes("w-full")
                            series_help = ui.html("", sanitize=False)
                            metal_a = ui.select([], label="Metal A").props("outlined dense").classes("w-full")
                            metal_b = ui.select([], label="Metal B").props("outlined dense").classes("w-full q-mt-sm")
                            ui.html('<div class="mx-label" style="margin:14px 0 6px">Area ratio (cathode : anode)</div>', sanitize=False)
                            area_ratio = ui.number(value=1.0, min=0, step=0.5, format="%.4g").props("outlined dense").classes("w-full")
                            with ui.row().classes("gap-2 q-mt-sm"):
                                for r in (0.1, 1, 10, 100):
                                    ui.html(f'<span class="mx-chip click">{r:g} : 1</span>', sanitize=False).on("click", lambda _=None, v=r: setattr(area_ratio, "value", v))
                            ui.html('<div class="mx-label" style="margin:14px 0 6px">Environment</div>', sanitize=False)
                            gal_env = ui.select(list(ENVIRONMENT_FACTORS), value="Seawater immersion").props("outlined dense").classes("w-full")
                            primary_button("Assess risk", lambda: galvanic(), "bolt").classes("q-mt-md")
                    gal_out = ui.column().classes("gap-4 w-full min-w-0")

            # ============================================================ PROTECTION
            with ui.tab_panel(t_prot).classes("p-0 pt-4"):
                with ui.element("div").classes("mx-grid-side"):
                    with ui.column().classes("gap-4 w-full"):
                        with panel("Service conditions", accent=True):
                            p_mat = ui.select(mat_options, value="carbon_steel", label="Metal to protect").props("outlined dense").classes("w-full")
                            p_env = ui.select(list(ENVIRONMENTS), value="Seawater immersion", label="Environment").props("outlined dense").classes("w-full q-mt-sm")
                            p_life = ui.number("Required service life (years)", value=25, min=0, step=1).props("outlined dense").classes("w-full q-mt-sm")
                            p_rate = ui.number("Measured rate, mm/y (optional)", value=None, min=0, format="%.4g").props("outlined dense clearable").classes("w-full q-mt-sm")
                            ghost_button("Use rate from step 1", lambda: use_rate(), "download").classes("q-mt-xs")
                            p_gal = ui.checkbox("Include the galvanic couple from step 2", value=False).classes("q-mt-sm")
                            primary_button("Generate plan", lambda: protect(), "shield").classes("q-mt-md")
                    prot_out = ui.column().classes("gap-4 w-full min-w-0")

            # ============================================================ REPORT
            with ui.tab_panel(REPORT_TAB).classes("p-0 pt-4"):
                rep_out = ui.column().classes("gap-4 w-full max-w-4xl")

    # ------------------------------------------------------------ helpers
    def material_values() -> tuple[float, float, str]:
        if mat.value == "custom":
            return _num(c_rho, "Density"), _num(c_ew, "Equivalent weight"), "Custom material"
        m = get_material(mat.value)
        return m.density, m.equivalent_weight, m.name

    def refresh_mat_info() -> None:
        custom_row.set_visibility(mat.value == "custom")
        if mat.value == "custom":
            mat_info.set_content("")
            return
        m = get_material(mat.value)
        mat_info.set_content(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">{chip(f"ρ = {m.density:g} g/cm³")}{chip(f"EW = {m.equivalent_weight:.2f}")}'
                             f'{chip(m.family.title())}</div>')

    def refresh_method() -> None:
        g_wl.set_visibility(method.value == "wl")
        g_ic.set_visibility(method.value == "icorr")
        g_tf.set_visibility(method.value == "tafel")
        g_rp.set_visibility(method.value == "rp")
        c_ew.set_visibility(method.value != "wl")

    def load_example() -> None:
        e, i = butler_volmer_data(1e-5, -0.45, 0.080, 0.120, eta_max=0.35, n=71, noise=0.02, seed=3)
        tf_text.value = "\n".join(f"{a:.4f}, {b:.4e}" for a, b in zip(e, i, strict=True))
        tf_ecorr.value, tf_w1.value, tf_w2.value = -0.45, 100, 300
        ui.notify("Example loaded: i_corr ≈ 10 µA/cm², βa = 80 mV/dec, βc = 120 mV/dec (2% noise).", type="info")

    # ------------------------------------------------------------ rate
    def calculate() -> None:
        rate_out.clear()
        S["tafel"] = None
        fit = None
        try:
            rho, ew, name = material_values()
            m = method.value
            if m == "wl":
                res = weight_loss_rate(_num(wl_m0, "Initial mass") * MASS_UNITS[wl_mu.value], _num(wl_m1, "Final mass") * MASS_UNITS[wl_mu.value],
                                       _num(wl_a, "Area") * AREA_UNITS[wl_au.value], _num(wl_t, "Exposure time") * TIME_UNITS[wl_tu.value], rho)
            elif m == "icorr":
                res = electrochemical_rate(_num(ic_i, "i_corr") * CURRENT_UNITS[ic_u.value], ew, rho)
            elif m == "tafel":
                e, i = parse_polarization(tf_text.value or "")
                window = (_num(tf_w1, "Window start") / 1000, _num(tf_w2, "Window end") / 1000)
                ecorr = _num(tf_ecorr, "E_corr")
                fit = tafel_extrapolation(e, i, ecorr, window)
                res = electrochemical_rate(fit.i_corr_uA_cm2, ew, rho, "Tafel extrapolation")
                S["tafel"] = {"potentials": e, "currents": i, "e_corr": ecorr, "fit": fit, "window": window}
            else:
                b, icorr = stern_geary(_num(rp_r, "R_p"), _num(rp_ba, "β_a") / 1000, _num(rp_bc, "β_c") / 1000)
                res = electrochemical_rate(icorr * 1e6, ew, rho, "Polarization resistance (Stern–Geary)")
                res.formulas.insert(0, f"B = βa·βc / (2.303·(βa + βc)) = {b * 1000:.2f} mV;  i_corr = B / R_p = {icorr * 1e6:.4g} µA/cm²")
        except MatEISError as exc:
            with rate_out:
                notice(str(exc), "err")
            return
        S["rate"] = (res, name)
        if mat.value != "custom":
            S["mat"] = mat.value
        with rate_out:
            with panel("Result", f"{res.method} · {name}", accent=True):
                with ui.element("div").classes("mx-grid-3"):
                    metric("Corrosion rate", fmt(res.mm_per_year, 4), "mm/y", hot=True)
                    metric("Imperial", fmt(res.mpy, 4), "mpy", "mils per year")
                    metric("Penetration", fmt(res.um_per_year, 4), "µm/y")
                ui.html(f'<div style="margin:16px 0 4px;display:flex;gap:10px;align-items:center"><span class="mx-label">Relative resistance</span>'
                        f'<span class="mx-chip" style="background:{res.rating_color};color:#0B1220;border-color:transparent">{esc(res.rating)}</span></div>', sanitize=False)
                rating_scale(res.mm_per_year)
                ui.html(f'<p style="color:var(--soft);font-size:14.5px;margin:12px 0 0">{esc(res.rating_text)}</p>', sanitize=False)
            with panel("Working"):
                formula_block(res.formulas)
            with panel("How long will it last?", "Years to lose a given thickness at this constant rate."):
                with ui.row().classes("items-center gap-3 no-wrap"):
                    thick = ui.number("Wall thickness (mm)", value=6.0, min=0, step=0.5).props("outlined dense").classes("w-48")
                    loss = ui.number("Allowed loss (%)", value=50, min=1, max=100, step=5).props("outlined dense").classes("w-40")
                life_out = ui.html("", sanitize=False)

                def life_update(_=None) -> None:
                    try:
                        yrs = service_life(_num(thick, "Thickness"), res.mm_per_year, _num(loss, "Allowed loss") / 100)
                        life_out.set_content(f'<div style="margin-top:10px;font-size:15px">At <b>{res.mm_per_year:.3g} mm/y</b>, losing {loss.value:g}% of {thick.value:g} mm '
                                             f'takes about <b style="font-family:var(--font-display);font-size:22px">{yrs:,.1f} years</b>.</div>')
                    except MatEISError as exc:
                        life_out.set_content(f'<div style="color:var(--danger)">{esc(str(exc))}</div>')
                thick.on_value_change(life_update)
                loss.on_value_change(life_update)
                life_update()
            if fit:
                with panel("Tafel fit", "Straight lines through the linear regions meet at (log i_corr, E_corr).", accent=True):
                    ui.plotly(tafel_plotly(S["tafel"]["potentials"], S["tafel"]["currents"], S["tafel"]["e_corr"], fit, S["tafel"]["window"], dark)).classes("w-full")
                    table_html(["Parameter", "Value"], [["Anodic slope β_a", f"{fit.beta_a * 1000:.1f} mV/decade  (R² = {fit.r2_anodic:.4f}, {fit.n_anodic} points)"],
                                                         ["Cathodic slope β_c", f"{fit.beta_c * 1000:.1f} mV/decade  (R² = {fit.r2_cathodic:.4f}, {fit.n_cathodic} points)"],
                                                         ["Corrosion current i_corr", f"{fit.i_corr_uA_cm2:.4g} µA/cm²"],
                                                         ["E_corr from intersection", f"{fit.e_corr_fit:.4f} V"]])
                    if min(fit.r2_anodic, fit.r2_cathodic) < 0.98:
                        notice("A fit with R² below 0.98 suggests the window includes curved (non-Tafel) data. Narrow or shift the window.", "warn")
            with ui.row().classes("gap-2"):
                ghost_button("Save to history", lambda: save_rate(), "bookmark_add")
                ghost_button("Use in protection plan", lambda: (use_rate(), tabs.set_value(t_prot)), "arrow_forward")

    def save_rate() -> None:
        res, name = S["rate"]
        svc.history.add("corrosion", f"{res.method}: {res.mm_per_year:.3g} mm/y ({name})", {"method": res.method, "material": name}, res.to_dict())
        ui.notify("Saved to history.", type="positive")

    # ------------------------------------------------------------ galvanic
    def series_entries():
        return svc.emf.list(series.value)

    def refresh_series(_=None) -> None:
        names = [e.name for e in series_entries()]
        a, b = DEFAULT_PAIR[series.value]
        metal_a.set_options(names, value=a if a in names else names[0])
        metal_b.set_options(names, value=b if b in names else names[-1])
        text = ("Practical galvanic series in flowing seawater (V vs SCE): includes alloys and passive films."
                if series.value == "seawater" else "Standard electrode potentials of pure metals (V vs SHE): the textbook EMF series.")
        series_help.set_content(f'<div style="color:var(--soft);font-size:13px;margin:8px 0 10px">{text}</div>')

    def galvanic() -> None:
        gal_out.clear()
        try:
            ea, eb = svc.emf.find(metal_a.value, series.value), svc.emf.find(metal_b.value, series.value)
            g = assess_couple(ea, eb, _num(area_ratio, "Area ratio"), gal_env.value)
        except (MatEISError, TypeError) as exc:
            with gal_out:
                notice(str(exc) if isinstance(exc, MatEISError) else "Choose two metals.", "err")
            return
        S["galv"] = g
        unit = "SHE" if series.value == "standard" else "SCE"
        with gal_out:
            with panel("Result", f"{g.anode.name} + {g.cathode.name} · {g.environment}", accent=True):
                with ui.element("div").classes("mx-grid-3"):
                    ui.html(f'<div class="mx-metric" style="border-color:{g.color}"><div class="mx-label">Galvanic corrosion risk</div>'
                            f'<div class="v" style="color:{g.color}">{g.level}</div><div class="h">score {g.score:.2f} of about 6</div></div>', sanitize=False)
                    metric("Potential difference", f"{g.delta_e:.2f}", "V", f"vs {unit}")
                    metric("Corrodes (anode)", g.anode.name, hint=f"E = {g.anode.potential_v:+.2f} V", hot=True)
                pos = min(g.score / 6.0, 1.0) * 100
                ui.html(f'<div style="margin-top:16px"><div class="mx-scale"><div style="background:#2FBF71"></div><div style="background:#C8D655"></div><div style="background:#F2C14E"></div>'
                        f'<div style="background:#EF8354"></div><div style="background:#E4572E"></div><div class="mx-scale-marker" style="left:calc({pos:.1f}% - 2px)"></div></div>'
                        f'<div class="mx-scale-labels"><span>Negligible</span><span>Low</span><span>Moderate</span><span>High</span><span>Severe</span></div></div>', sanitize=False)
                ui.html('<ul style="margin:14px 0 0 18px;padding:0;color:var(--soft);font-size:14.5px;line-height:1.6">' + "".join(f"<li>{esc(t)}</li>" for t in g.explanation) + "</ul>", sanitize=False)
            with panel("What to do about it"):
                ui.html('<ul style="margin:0 0 0 18px;padding:0;color:var(--soft);font-size:14.5px;line-height:1.7">' + "".join(f"<li>{esc(t)}</li>" for t in g.mitigations) + "</ul>", sanitize=False)
            with panel("Where the couple sits in the series", "Most active (anodic) at the top; the two selected metals are highlighted."):
                ui.plotly(ladder_plotly(series_entries(), (g.anode.name, g.cathode.name), dark)).classes("w-full")
            with ui.expansion("Compatibility matrix for several metals", icon="grid_on").classes("w-full"):
                names = [e.name for e in series_entries()]
                pick = ui.select(names, multiple=True, value=[g.anode.name, g.cathode.name], label="Metals to compare").props("use-chips outlined dense").classes("w-full")
                holder = ui.column().classes("w-full")

                def draw_matrix(_=None) -> None:
                    holder.clear()
                    with holder:
                        if len(pick.value) < 2:
                            notice("Select at least two metals.")
                            return
                        es = [svc.emf.find(n, series.value) for n in pick.value]
                        ui.plotly(matrix_plotly([e.name for e in es], delta_matrix(es), dark)).classes("w-full")
                        ui.html('<div style="color:var(--faint);font-size:13px">Guide: below 0.15 V is usually tolerable; above about 0.30 V needs measures such as isolation or coating the cathode.</div>', sanitize=False)
                pick.on_value_change(draw_matrix)
                draw_matrix()
            ghost_button("Save to history", lambda: save_galvanic(g), "bookmark_add")

    def save_galvanic(g) -> None:
        svc.history.add("corrosion", f"Galvanic: {g.anode.name} + {g.cathode.name} ({g.level})",
                        {"series": series.value, "environment": g.environment, "area_ratio": g.area_ratio}, g.to_dict())
        ui.notify("Saved to history.", type="positive")

    # ------------------------------------------------------------ protection
    def use_rate() -> None:
        if S["rate"] is None:
            ui.notify("Calculate a corrosion rate in step 1 first.", type="warning")
            return
        p_rate.value = round(S["rate"][0].mm_per_year, 5)
        if S["mat"] in MATERIALS:
            p_mat.value = S["mat"]

    def protect() -> None:
        prot_out.clear()
        try:
            m = get_material(p_mat.value)
            env = get_environment(p_env.value)
            life = _num(p_life, "Service life")
            rate = float(p_rate.value) if p_rate.value not in (None, "") else None
            partner = level = None
            if p_gal.value and S["galv"] is not None:
                partner = f"{S['galv'].anode.name} / {S['galv'].cathode.name}"
                level = S["galv"].level
            recs = recommend(m, env, life, rate, partner, level)
        except MatEISError as exc:
            with prot_out:
                notice(str(exc), "err")
            return
        S.update(recs=recs, mat_name=m.name, env=env.label, life=life, anode=None)
        with prot_out:
            with panel("Recommendations", f"{m.name} in {env.label} · {life:g}-year life · ISO category {env.iso}", accent=True):
                for r in recs:
                    tag, color = PRIORITY[r.priority]
                    details = "".join(f"<li>{esc(d)}</li>" for d in r.details)
                    ui.html(f'<div class="mx-rec" style="--rec:{color};margin-bottom:10px"><div style="display:flex;gap:8px">{chip(tag, r.priority == 1)}{chip(r.category)}</div>'
                            f'<h4>{esc(r.title)}</h4><p>{esc(r.why)}</p>{f"<ul>{details}</ul>" if details else ""}</div>', sanitize=False)
            anode = recommended_anode(m, env)
            if anode is not None:
                with panel("Sacrificial anode sizing", f"Suggested anode: {anode.name} ({anode.potential}, {anode.capacity_ah_per_kg:g} A·h/kg)", accent=True):
                    ui.html(f'<p style="color:var(--soft);font-size:14px;margin:0 0 10px">{esc(anode.typical_use)}</p>', sanitize=False)
                    with ui.row().classes("w-full no-wrap gap-2"):
                        a_key = ui.select({k: v.name for k, v in ANODES.items()}, value=anode.key, label="Anode material").props("outlined dense").classes("col")
                        a_area = ui.number("Exposed area (m²)", value=50, min=0, step=1).props("outlined dense").classes("col")
                    with ui.row().classes("w-full no-wrap gap-2 q-mt-sm"):
                        a_i = ui.number("Design current density (mA/m²)", value=env.default_current_density or 100, min=0).props("outlined dense").classes("col")
                        a_f = ui.number("Coating breakdown factor (0–1)", value=0.1, min=0, max=1, step=0.05).props("outlined dense").classes("col")
                        a_u = ui.number("Utilisation", value=0.85, min=0, max=1, step=0.05).props("outlined dense").classes("col")
                    a_out = ui.column().classes("w-full gap-2 q-mt-sm")

                    def size(_=None) -> None:
                        a_out.clear()
                        with a_out:
                            try:
                                d = size_anodes(ANODES[a_key.value], _num(a_area, "Area"), _num(a_i, "Current density"), life, _num(a_f, "Breakdown factor"), _num(a_u, "Utilisation"))
                            except MatEISError as exc:
                                notice(str(exc), "err")
                                return
                            S["anode"] = d
                            with ui.element("div").classes("mx-grid-3"):
                                metric("Current demand", fmt(d.current_a), "A")
                                metric("Total charge", f"{d.charge_ah:,.0f}", "A·h")
                                metric("Anode mass", f"{d.mass_kg:,.1f}", "kg", hot=True)
                            formula_block(d.formulas)
                            notice("Indicative, mass-based sizing. A real design also checks anode resistance, current output at end of life and distribution (DNV-RP-B401, NACE SP0176).")
                    for w in (a_key, a_area, a_i, a_f, a_u):
                        w.on_value_change(size)
                    size()

    # ------------------------------------------------------------ report
    def render_report() -> None:
        rep_out.clear()
        with rep_out:
            with panel("Corrosion assessment report", "Combines the results you have produced so far into a two-to-three page PDF.", accent=True):
                items = [("Corrosion rate", S["rate"] is not None, f"{S['rate'][0].mm_per_year:.3g} mm/y · {S['rate'][0].rating}" if S["rate"] else "Run step 1"),
                         ("Galvanic risk", S["galv"] is not None, f"{S['galv'].anode.name} + {S['galv'].cathode.name}: {S['galv'].level}" if S["galv"] else "Run step 2"),
                         ("Protection plan", S["recs"] is not None, f"{len(S['recs'])} recommendations" if S["recs"] else "Run step 3"),
                         ("Anode design", S["anode"] is not None, f"{S['anode'].mass_kg:,.1f} kg {S['anode'].anode.name}" if S["anode"] else "Optional")]
                for name, done, text in items:
                    ui.html(f'<div style="display:flex;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)">'
                            f'<i class="q-icon notranslate material-icons" style="color:{"var(--ok)" if done else "var(--faint)"}">{"check_circle" if done else "radio_button_unchecked"}</i>'
                            f'<b style="min-width:150px">{name}</b><span style="color:var(--soft)">{esc(text)}</span></div>', sanitize=False)
                ui.html('<div style="height:12px"></div>', sanitize=False)
                with ui.row().classes("gap-2"):
                    primary_button("Download PDF report", build_pdf, "picture_as_pdf")
                    ghost_button("Refresh summary", render_report, "refresh")
            if not any(i[1] for i in items):
                notice("Nothing to report yet. Work through steps 1 to 3 first.", "warn")

    def build_pdf() -> None:
        if not (S["rate"] or S["galv"] or S["recs"]):
            ui.notify("Run at least one calculation first.", type="warning")
            return
        res = S["rate"][0] if S["rate"] else None
        name = S.get("mat_name") or (S["rate"][1] if S["rate"] else get_material(S["mat"]).name)
        ladder = svc.emf.list(S["galv"].anode.series) if S["galv"] else None
        pdf = corrosion_pdf(name, S["env"] if S["recs"] else "Not specified", S["life"], res, S["tafel"], S["galv"], ladder, S["recs"], S["anode"])
        ui.download.content(pdf, "mateis_corrosion_report.pdf", "application/pdf")

    mat.on_value_change(lambda _: refresh_mat_info())
    method.on_value_change(lambda _: refresh_method())
    series.on_value_change(refresh_series)
    tabs.on_value_change(lambda e: render_report() if getattr(e.value, "props", {}).get("name", e.value) == REPORT_TAB or e.value == REPORT_TAB else None)
    refresh_mat_info()
    refresh_method()
    refresh_series()
    render_report()
