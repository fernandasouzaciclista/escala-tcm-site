from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
import math
import uuid

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client, Client

APP_VERSION = "v1.0-site-supabase"
ATIVIDADES = ["DOC", "Manhã", "Tarde"]
PERIODOS = ["", "Dia inteiro", "DOC", "Manhã", "Tarde"]
TIPOS_AUSENCIA = ["", "Férias", "Abonada", "Manhã", "Tarde", "Juri", "OTC", "Lic.Médica", "Folga TRE", "Substituição de chefia"]
SERVIDORES_PADRAO = ["Bruno", "Carlos", "Fábio", "Fernanda", "Júlia", "Luciane", "Neto", "Patrícia", "Silvana"]
NOMES_AUSENCIA = SERVIDORES_PADRAO + ["Gil"]

FERIADOS_2026 = [
    ("2026-01-01", "Confraternização Universal", "Calendário oficial"),
    ("2026-01-25", "Aniversário da Cidade de São Paulo", "Calendário municipal"),
    ("2026-02-16", "Carnaval - ponto facultativo", "Calendário municipal"),
    ("2026-02-17", "Carnaval - ponto facultativo", "Calendário municipal"),
    ("2026-02-18", "Quarta-feira de Cinzas / suspensão de expediente", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-04-03", "Paixão de Cristo", "Calendário oficial"),
    ("2026-04-20", "Suspensão de expediente", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-04-21", "Tiradentes", "Calendário oficial"),
    ("2026-05-01", "Dia do Trabalho", "Calendário oficial"),
    ("2026-06-04", "Corpus Christi", "Calendário municipal"),
    ("2026-06-05", "Suspensão de expediente", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-07-09", "Data Magna do Estado de São Paulo", "Calendário estadual"),
    ("2026-07-10", "Suspensão de expediente", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-09-07", "Independência do Brasil", "Calendário oficial"),
    ("2026-10-12", "Nossa Senhora Aparecida", "Calendário oficial"),
    ("2026-10-28", "Dia do Servidor Público", "Calendário oficial"),
    ("2026-11-02", "Finados", "Calendário oficial"),
    ("2026-11-15", "Proclamação da República", "Calendário oficial"),
    ("2026-11-20", "Consciência Negra", "Calendário oficial/municipal"),
    ("2026-12-17", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-18", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-21", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-22", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-23", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-24", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-25", "Natal", "Calendário oficial"),
    ("2026-12-28", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-29", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-30", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2026-12-31", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2027-01-01", "Confraternização Universal", "Calendário oficial"),
    ("2027-01-04", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
    ("2027-01-05", "Suspensão de expediente / recesso de fim de ano", "TCM-SP Portaria SG/GAB 06/2025 retificada pela 07/2025"),
]

st.set_page_config(page_title="Escalador TCM", page_icon="📅", layout="wide")

# ---------- conexão ----------

def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

@st.cache_resource(show_spinner=False)
def get_supabase() -> Client | None:
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

sb = get_supabase()

# ---------- utilidades ----------

def parse_date(x):
    if x is None or x == "" or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    try:
        return pd.to_datetime(x, dayfirst=True).date()
    except Exception:
        return None


def to_iso(x):
    d = parse_date(x)
    return d.isoformat() if d else None


def first_day(year: int, month: int) -> date:
    return date(year, month, 1)


def last_day(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def month_days(year: int, month: int) -> list[date]:
    d0, d1 = first_day(year, month), last_day(year, month)
    return [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]


def normalize_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"sim", "true", "1", "yes", "x"}


def clean_df_records(df: pd.DataFrame, date_cols: list[str] | None = None) -> list[dict]:
    date_cols = date_cols or []
    out = []
    for _, row in df.iterrows():
        rec = {}
        for col, value in row.items():
            if col == "id":
                continue
            if pd.isna(value):
                rec[col] = None
            elif col in date_cols:
                rec[col] = to_iso(value)
            elif isinstance(value, (np.bool_, bool)):
                rec[col] = bool(value)
            else:
                rec[col] = str(value).strip() if isinstance(value, str) else value
        # ignora linhas totalmente vazias
        non_empty = [v for k, v in rec.items() if k != "observacao" and v not in (None, "")]
        if non_empty:
            out.append(rec)
    return out

# ---------- supabase CRUD ----------

def require_db():
    if sb is None:
        st.error("Configure SUPABASE_URL e SUPABASE_KEY nos Secrets do Streamlit para usar o site.")
        st.stop()


def load_table(name: str) -> pd.DataFrame:
    require_db()
    try:
        data = sb.table(name).select("*").execute().data
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Não consegui carregar a tabela {name}. Rode o supabase_schema.sql no Supabase.\n\nErro: {e}")
        st.stop()


def replace_table(name: str, df: pd.DataFrame, date_cols: list[str] | None = None):
    require_db()
    # apaga tudo e reinsere a tabela editada. Simples e honesto.
    try:
        sb.table(name).delete().gte("id", 0).execute()
    except Exception:
        pass
    records = clean_df_records(df, date_cols=date_cols)
    if records:
        sb.table(name).insert(records).execute()


def seed_defaults(force: bool = False):
    require_db()
    current = load_table("servidores")
    if force or current.empty:
        serv_df = pd.DataFrame({
            "nome": SERVIDORES_PADRAO,
            "ativo": [True] * len(SERVIDORES_PADRAO),
            "pode_doc": [True] * len(SERVIDORES_PADRAO),
            "pode_manha": [True] * len(SERVIDORES_PADRAO),
            "pode_tarde": [True] * len(SERVIDORES_PADRAO),
        })
        replace_table("servidores", serv_df)

    current_f = load_table("feriados")
    if force or current_f.empty:
        fer_df = pd.DataFrame(FERIADOS_2026, columns=["data", "descricao", "fonte"])
        replace_table("feriados", fer_df, date_cols=["data"])

    current_a = load_table("ausencias")
    if force or current_a.empty:
        abs_df = pd.DataFrame({
            "servidor": NOMES_AUSENCIA,
            "data_inicio": [None] * len(NOMES_AUSENCIA),
            "data_fim": [None] * len(NOMES_AUSENCIA),
            "periodo": [""] * len(NOMES_AUSENCIA),
            "tipo": [""] * len(NOMES_AUSENCIA),
            "substituto_gil": [""] * len(NOMES_AUSENCIA),
            "observacao": [""] * len(NOMES_AUSENCIA),
        })
        replace_table("ausencias", abs_df, date_cols=["data_inicio", "data_fim"])

# ---------- lógica da escala ----------

@dataclass
class Server:
    nome: str
    ativo: bool
    pode_doc: bool
    pode_manha: bool
    pode_tarde: bool

    def can(self, atividade: str) -> bool:
        return {
            "DOC": self.pode_doc,
            "Manhã": self.pode_manha,
            "Tarde": self.pode_tarde,
        }.get(atividade, False)


def prepare_inputs(serv_df: pd.DataFrame, abs_df: pd.DataFrame, fer_df: pd.DataFrame):
    if "data" in fer_df.columns:
        fer_df["data"] = fer_df["data"].apply(parse_date)
    for c in ["data_inicio", "data_fim"]:
        if c in abs_df.columns:
            abs_df[c] = abs_df[c].apply(parse_date)
    for c in ["ativo", "pode_doc", "pode_manha", "pode_tarde"]:
        if c in serv_df.columns:
            serv_df[c] = serv_df[c].apply(normalize_bool)
    return serv_df, abs_df, fer_df


def effective_end(row) -> date | None:
    return row.get("data_fim") or row.get("data_inicio")


def row_overlaps(row, day: date) -> bool:
    di = row.get("data_inicio")
    df = effective_end(row)
    return di is not None and df is not None and di <= day <= df


def periodo_blocks(periodo: str, atividade: str | None = None) -> bool:
    p = str(periodo or "").strip()
    if p == "Dia inteiro":
        return True
    if atividade is None:
        return bool(p)
    return p == atividade


def bruno_indisponivel_no_periodo(gil_row, abs_df: pd.DataFrame) -> bool:
    di = gil_row.get("data_inicio")
    df = effective_end(gil_row)
    if di is None or df is None:
        return False
    for _, r in abs_df.iterrows():
        if str(r.get("servidor", "")).strip() != "Bruno":
            continue
        ri, rf = r.get("data_inicio"), effective_end(r)
        if ri is None or rf is None:
            continue
        if ri <= df and rf >= di:
            return True
    return False


def gil_substitute_for_row(gil_row, abs_df: pd.DataFrame) -> str:
    manual = str(gil_row.get("substituto_gil") or "").strip()
    if manual and manual != "A definir":
        return manual
    return "A definir" if bruno_indisponivel_no_periodo(gil_row, abs_df) else "Bruno"


def is_blocked(server: str, day: date, atividade: str, abs_df: pd.DataFrame) -> bool:
    # ausência do próprio servidor
    for _, r in abs_df.iterrows():
        nome = str(r.get("servidor", "")).strip()
        if nome == server and row_overlaps(r, day) and periodo_blocks(r.get("periodo"), atividade):
            return True
    # substituto do Gil sai da escala
    for _, r in abs_df.iterrows():
        nome = str(r.get("servidor", "")).strip()
        if nome == "Gil" and row_overlaps(r, day):
            sub = gil_substitute_for_row(r, abs_df)
            if sub == server:
                return True
    return False


def build_availability(days_uteis: list[date], servers: list[Server], abs_df: pd.DataFrame):
    avail = {s.nome: 0 for s in servers}
    avail_act = {s.nome: {a: 0 for a in ATIVIDADES} for s in servers}
    for d in days_uteis:
        for s in servers:
            any_can = False
            for a in ATIVIDADES:
                if s.can(a) and not is_blocked(s.nome, d, a, abs_df):
                    avail_act[s.nome][a] += 1
                    any_can = True
            if any_can:
                avail[s.nome] += 1
    return avail, avail_act


def score_candidate(name: str, atividade: str, day: date, assigned_today: list[str], counts: dict, counts_act: dict,
                    prev_by_activity: dict, servers: dict[str, Server], avail: dict, avail_act: dict, abs_df: pd.DataFrame,
                    tasks_done: int, tasks_by_act_done: dict, days_elapsed: int, total_avail_sum: int) -> float:
    s = servers[name]
    total_after = counts[name] + 1
    act_after = counts_act[name][atividade] + 1

    # Proporcionalidade total por dias disponíveis.
    denom = max(1, total_avail_sum)
    expected_total = (tasks_done + 1) * (avail[name] / denom)
    score = ((total_after - expected_total) ** 2) * 120

    # Proporcionalidade por atividade, calculada só entre quem pode aquela atividade.
    denom_act = sum(max(0, avail_act[n][atividade]) for n in servers)
    expected_act = (tasks_by_act_done[atividade] + 1) * (avail_act[name][atividade] / max(1, denom_act))
    score += ((act_after - expected_act) ** 2) * 90

    # Equilíbrio interno do próprio servidor: evita 4/2/4 quando dá para 4/3/3.
    enabled = [a for a in ATIVIDADES if s.can(a)]
    if len(enabled) > 1:
        projected = []
        for a in enabled:
            v = counts_act[name][a] + (1 if a == atividade else 0)
            projected.append(v)
        score += (max(projected) - min(projected)) * 250
        score += float(np.var(projected)) * 120

    # Evita repetir no mesmo dia, mas deixa como fallback.
    if name in assigned_today:
        score += 100000

    # Evita repetição no mesmo tipo em dia útil consecutivo.
    if prev_by_activity.get(atividade) == name:
        # não bloqueia se a pessoa só puder essa atividade
        if sum(1 for a in ATIVIDADES if s.can(a)) > 1:
            score += 50000

    return score


def generate_schedule(year: int, month: int, serv_df: pd.DataFrame, abs_df: pd.DataFrame, fer_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    serv_df, abs_df, fer_df = prepare_inputs(serv_df.copy(), abs_df.copy(), fer_df.copy())
    servers_list = []
    for _, r in serv_df.iterrows():
        if normalize_bool(r.get("ativo", False)):
            servers_list.append(Server(
                nome=str(r.get("nome")).strip(),
                ativo=True,
                pode_doc=normalize_bool(r.get("pode_doc", False)),
                pode_manha=normalize_bool(r.get("pode_manha", False)),
                pode_tarde=normalize_bool(r.get("pode_tarde", False)),
            ))
    servers = {s.nome: s for s in servers_list}

    feriados = set(fer_df["data"].dropna().tolist()) if "data" in fer_df.columns else set()
    all_days = month_days(year, month)
    days_uteis = [d for d in all_days if d.weekday() < 5 and d not in feriados]
    avail, avail_act = build_availability(days_uteis, servers_list, abs_df)
    total_avail_sum = sum(avail.values())

    counts = {s.nome: 0 for s in servers_list}
    counts_act = {s.nome: {a: 0 for a in ATIVIDADES} for s in servers_list}
    tasks_done = 0
    tasks_by_act_done = {a: 0 for a in ATIVIDADES}
    prev_by_activity: dict[str, str | None] = {a: None for a in ATIVIDADES}

    rows = []
    for d in all_days:
        is_workday = d.weekday() < 5 and d not in feriados
        row = {"Data": d, "Dia útil?": is_workday, "DOC": "", "Manhã": "", "Tarde": "", "Ausências/impedimentos do dia": "", "Status": ""}
        if not is_workday:
            row["Status"] = "Sem expediente" if d in feriados else ""
            rows.append(row)
            continue

        assigned_today: list[str] = []
        day_status = []
        for atividade in ATIVIDADES:
            candidates = [s.nome for s in servers_list if s.can(atividade) and not is_blocked(s.nome, d, atividade, abs_df)]
            if not candidates:
                row[atividade] = ""
                day_status.append(f"Sem candidato para {atividade}")
                continue
            # Preferência sem repetição no dia. Se zerar, usa fallback com repetição.
            primary = [c for c in candidates if c not in assigned_today]
            pool = primary if primary else candidates
            best = min(pool, key=lambda n: score_candidate(
                n, atividade, d, assigned_today, counts, counts_act, prev_by_activity, servers,
                avail, avail_act, abs_df, tasks_done, tasks_by_act_done,
                days_elapsed=0, total_avail_sum=total_avail_sum,
            ))
            if best in assigned_today:
                day_status.append("Repetição no dia - exceção")
            row[atividade] = best
            assigned_today.append(best)
            counts[best] += 1
            counts_act[best][atividade] += 1
            tasks_done += 1
            tasks_by_act_done[atividade] += 1
            prev_by_activity[atividade] = best

        # Texto de ausências do dia
        notes = []
        for _, ar in abs_df.iterrows():
            nome = str(ar.get("servidor", "")).strip()
            if nome and row_overlaps(ar, d):
                periodo = str(ar.get("periodo") or "").strip()
                tipo = str(ar.get("tipo") or "").strip()
                sub = ""
                if nome == "Gil":
                    sub = gil_substitute_for_row(ar, abs_df)
                    if sub:
                        sub = f"; substituto: {sub}"
                obs = str(ar.get("observacao") or "").strip()
                obs_txt = f"; obs: {obs}" if obs else ""
                notes.append(f"{nome} ({periodo} - {tipo}{sub}{obs_txt})")
        row["Ausências/impedimentos do dia"] = " | ".join(notes)
        row["Status"] = "OK" if not day_status else " | ".join(day_status)
        rows.append(row)

    escala = pd.DataFrame(rows)
    resumo_rows = []
    for s in servers_list:
        r = {"Servidor": s.nome}
        for a in ATIVIDADES:
            r[a] = int((escala[a] == s.nome).sum())
        r["Total"] = sum(r[a] for a in ATIVIDADES)
        r["Dias úteis disponíveis"] = avail[s.nome]
        r["Atividades por dia útil"] = round(r["Total"] / avail[s.nome], 2) if avail[s.nome] else 0
        resumo_rows.append(r)
    resumo = pd.DataFrame(resumo_rows)
    return escala, resumo

# ---------- exportação excel ----------

def weekday_pt(d: date) -> str:
    nomes = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]
    return nomes[d.weekday()]


def make_excel(year, month, escala, resumo, serv_df, abs_df, fer_df) -> bytes:
    import xlsxwriter
    output = BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    blue = "#1F4E79"
    light = "#DDEBF7"
    header = wb.add_format({"bold": True, "font_color": "white", "bg_color": blue, "align": "center", "valign": "vcenter", "border": 1})
    title = wb.add_format({"bold": True, "font_color": "white", "bg_color": blue, "align": "center", "font_size": 14, "border": 1})
    cell = wb.add_format({"bg_color": light, "border": 1, "align": "center", "valign": "vcenter"})
    left = wb.add_format({"bg_color": light, "border": 1, "align": "left", "valign": "vcenter"})
    label = wb.add_format({"bold": True, "border": 1, "align": "center"})
    datefmt = wb.add_format({"num_format": "dd/mm/yyyy", "bg_color": light, "border": 1, "align": "center"})

    # Visual Mensal
    ws = wb.add_worksheet("Visual Mensal")
    ws.set_column("A:A", 16)
    ws.set_column("B:F", 24)
    month_name = pd.Timestamp(date(year, month, 1)).strftime("%B/%Y").upper()
    # traduz mês mais comum do locale inglês
    trans = {"JANUARY":"JANEIRO","FEBRUARY":"FEVEREIRO","MARCH":"MARÇO","APRIL":"ABRIL","MAY":"MAIO","JUNE":"JUNHO","JULY":"JULHO","AUGUST":"AGOSTO","SEPTEMBER":"SETEMBRO","OCTOBER":"OUTUBRO","NOVEMBER":"NOVEMBRO","DECEMBER":"DEZEMBRO"}
    for en, pt in trans.items():
        month_name = month_name.replace(en, pt)
    ws.merge_range(0, 0, 0, 5, f"ESCALA - {month_name}", title)
    # semanas de segunda a sexta que tenham dia do mês
    days = month_days(year, month)
    start = days[0] - timedelta(days=days[0].weekday())
    weeks = []
    cur = start
    while cur <= days[-1]:
        wk = [cur + timedelta(days=i) for i in range(5)]
        if any(d.month == month for d in wk):
            weeks.append(wk)
        cur += timedelta(days=7)
    r = 2
    for wk in weeks:
        ws.write(r, 0, "Atividade", header)
        for idx, d in enumerate(wk, start=1):
            txt = "" if d.month != month else f"{weekday_pt(d)}: {d:%d/%m}"
            ws.write(r, idx, txt, header)
        for ai, a in enumerate(ATIVIDADES, start=1):
            ws.write(r + ai, 0, a, label)
            for idx, d in enumerate(wk, start=1):
                if d.month != month:
                    ws.write(r + ai, idx, "", cell)
                    continue
                er = escala.loc[escala["Data"] == d]
                if er.empty:
                    val = ""
                elif not bool(er.iloc[0]["Dia útil?"]):
                    val = "Sem expediente"
                else:
                    val = er.iloc[0][a]
                ws.write(r + ai, idx, val, cell)
        r += 5

    # Demais abas
    def write_df(sheet_name, df):
        sh = wb.add_worksheet(sheet_name)
        if df.empty:
            return sh
        for c, col in enumerate(df.columns):
            sh.write(0, c, col, header)
        for rr, (_, row) in enumerate(df.iterrows(), start=1):
            for c, col in enumerate(df.columns):
                v = row[col]
                if isinstance(v, date):
                    sh.write_datetime(rr, c, datetime.combine(v, datetime.min.time()), datefmt)
                else:
                    sh.write(rr, c, "" if pd.isna(v) else v, left if c == 0 else cell)
        for c, col in enumerate(df.columns):
            sh.set_column(c, c, min(max(len(str(col)) + 4, 12), 36))
        return sh

    write_df("Escala", escala)
    write_df("Resumo", resumo)
    write_df("Servidores", serv_df)
    write_df("Ausências", abs_df)
    write_df("Feriados", fer_df)
    wb.close()
    return output.getvalue()

# ---------- interface ----------

st.title("Escalador DOC e Controle da Entrada")
st.caption(f"{APP_VERSION} · Site com dados persistentes no Supabase")

if sb is None:
    st.warning("Configure os Secrets do Streamlit antes de usar. Veja o README_DEPLOY.md do pacote.")
    st.code('SUPABASE_URL = "https://...supabase.co"\nSUPABASE_KEY = "..."')
    st.stop()

with st.sidebar:
    st.header("Configuração")
    ano = st.number_input("Ano", min_value=2026, max_value=2035, value=2026, step=1)
    mes = st.selectbox("Mês", list(range(1,13)), index=7, format_func=lambda x: f"{x:02d}")
    st.divider()
    if st.button("Inicializar/atualizar dados padrão", type="secondary"):
        seed_defaults(force=False)
        st.success("Dados padrão criados se estavam vazios.")
        st.rerun()
    if st.button("Resetar tudo para padrão", type="secondary"):
        seed_defaults(force=True)
        st.success("Dados resetados.")
        st.rerun()

serv_df = load_table("servidores")
abs_df = load_table("ausencias")
fer_df = load_table("feriados")

# Se o banco estiver vazio, prepara dados mínimos.
if serv_df.empty and abs_df.empty and fer_df.empty:
    seed_defaults(force=True)
    st.rerun()

abas = st.tabs(["Servidores", "Ausências", "Feriados", "Gerar escala", "Sobre"])

with abas[0]:
    st.subheader("Servidores e habilitações")
    cols = ["nome", "ativo", "pode_doc", "pode_manha", "pode_tarde"]
    edit = serv_df.reindex(columns=[c for c in cols if c in serv_df.columns])
    edited = st.data_editor(
        edit,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "nome": st.column_config.TextColumn("Servidor", required=True),
            "ativo": st.column_config.CheckboxColumn("Ativo?"),
            "pode_doc": st.column_config.CheckboxColumn("Pode DOC?"),
            "pode_manha": st.column_config.CheckboxColumn("Pode Manhã?"),
            "pode_tarde": st.column_config.CheckboxColumn("Pode Tarde?"),
        },
        key="servidores_editor",
    )
    if st.button("Salvar servidores", type="primary"):
        replace_table("servidores", edited)
        st.success("Servidores salvos.")
        st.rerun()

with abas[1]:
    st.subheader("Ausências e impedimentos")
    st.info("Para ausência de um dia só, preencha apenas Data início. Se Servidor = Gil, o substituto padrão é Bruno; se Bruno estiver ausente no período, o sistema considera A definir.")
    cols = ["servidor", "data_inicio", "data_fim", "periodo", "tipo", "substituto_gil", "observacao"]
    edit = abs_df.reindex(columns=cols)
    edited = st.data_editor(
        edit,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "servidor": st.column_config.SelectboxColumn("Servidor", options=NOMES_AUSENCIA, required=False),
            "data_inicio": st.column_config.DateColumn("Data início", format="DD/MM/YYYY"),
            "data_fim": st.column_config.DateColumn("Data fim (opcional)", format="DD/MM/YYYY"),
            "periodo": st.column_config.SelectboxColumn("Período afetado", options=PERIODOS),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS_AUSENCIA),
            "substituto_gil": st.column_config.SelectboxColumn("Substituto(a) do Gil", options=[""] + SERVIDORES_PADRAO + ["A definir"]),
            "observacao": st.column_config.TextColumn("Observação"),
        },
        key="ausencias_editor",
    )
    if st.button("Salvar ausências", type="primary"):
        replace_table("ausencias", edited, date_cols=["data_inicio", "data_fim"])
        st.success("Ausências salvas.")
        st.rerun()

with abas[2]:
    st.subheader("Feriados e dias sem expediente")
    edit = fer_df.reindex(columns=["data", "descricao", "fonte"])
    edited = st.data_editor(
        edit,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "descricao": st.column_config.TextColumn("Descrição"),
            "fonte": st.column_config.TextColumn("Fonte"),
        },
        key="feriados_editor",
    )
    if st.button("Salvar feriados", type="primary"):
        replace_table("feriados", edited, date_cols=["data"])
        st.success("Feriados salvos.")
        st.rerun()

with abas[3]:
    st.subheader(f"Escala de {mes:02d}/{ano}")
    escala, resumo = generate_schedule(int(ano), int(mes), serv_df, abs_df, fer_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Dias úteis", int(escala["Dia útil?"].sum()))
    c2.metric("Atividades", int(escala["Dia útil?"].sum()) * 3)
    c3.metric("Servidores ativos", int(serv_df["ativo"].apply(normalize_bool).sum()) if "ativo" in serv_df.columns else 0)

    st.markdown("### Resumo")
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.markdown("### Escala detalhada")
    show = escala.copy()
    show["Data"] = show["Data"].apply(lambda d: d.strftime("%d/%m/%Y") if isinstance(d, date) else d)
    st.dataframe(show, use_container_width=True, hide_index=True)

    excel_bytes = make_excel(int(ano), int(mes), escala, resumo, serv_df, abs_df, fer_df)
    st.download_button(
        "Baixar Excel da escala",
        data=excel_bytes,
        file_name=f"escala_doc_entrada_{ano}_{mes:02d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

with abas[4]:
    st.markdown("""
    **Como funciona**

    - Os dados ficam salvos no Supabase.
    - A escala respeita feriados, ausências, habilitações por atividade e substituição do Gil.
    - Quando não houver três pessoas diferentes disponíveis, o sistema pode repetir alguém no mesmo dia como exceção, mas nunca usa pessoa ausente ou não habilitada.
    - A exportação em Excel é gerada na hora.
    """)
