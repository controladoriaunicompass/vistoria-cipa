import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date

# ========================
# CONFIGURAÇÕES
# ========================
APP_TITULO = "Sistema de Vistoria CIPA"

SENHA_USUARIO = "cipa2026"
CHAVE_ADMIN = "Uni06032023"

DB = "banco_v3.db"

MESES = ["01","02","03","04","05","06","07","08","09","10","11","12"]

SETORES = [
    "Recebimento e Estoque de Chapas",
    "Laboratório, Estoque de chapas Não conforme, Coletor de Aparas e Acessórios",
    "Pit Stop, Clicheria, ETE",
    "Almoxarifado - área interna e externa",
    "Impressora XTQ - área máquina e estoque em processo",
    "Impressora XTD - área máquina e estoque em processo",
    "Imp2400/XTD FF - área máquina e estoque em processo",
    "Coladeira 5",
    "Coladeira 7",
    "Coladeira 8",
    "Área de Retrabalho, Grampeadeiras e Colagem Manual",
    "Administrativo piso térreo - Salas e Banheiros DPR",
    "Oficina, Gaiola",
    "Acopladeira - área máquina e estoque em processo",
    "Jinya, Boca de Sapo - área máquina e estoque em processo",
    "Impressora 700 - área máquina e estoque em processo",
    "Estoque de bobinas, Cortadeira e Guilhotina",
    "Estoques de Chapas GR e Área Não Conforme",
    "Sobras e Paletização",
    "Estoque de PA, Expedição e docas",
    "Galpão Lonado, área de resíduos e área dos paletes",
    "Portaria, sala de reunião externa, sala de treinamentos, vestiário, estacionamento de motos, bicicletário, sala de descanso, quiosque, restaurante e estacionamento de carros",
    "DDP e Clicheria 3°",
    "Administrativo piso superior",
]

# (Por enquanto está reduzido — quando você quiser, eu deixo com TODAS as perguntas)
PERGUNTAS = [
    "Superfícies de trabalho seguras",
    "Iluminação adequada",
    "Sinalização correta",
    "Uso correto de EPI",
    "Saídas de emergência desobstruídas"
]

# ========================
# BANCO
# ========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS vistoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    ano INTEGER,
    mes TEXT,
    setor TEXT,
    data_vistoria TEXT,
    responsavel_area TEXT,
    inspecionado_por TEXT,
    respostas_json TEXT,
    UNIQUE(ano, mes, setor)
)
""")
conn.commit()

# ========================
# FUNÇÕES
# ========================
def upsert_vistoria(ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas):
    created_at = datetime.now().isoformat(timespec="seconds")
    c.execute("""
        INSERT INTO vistoria VALUES (NULL,?,?,?,?,?,?,?,?)
        ON CONFLICT(ano, mes, setor) DO UPDATE SET
            created_at=excluded.created_at,
            data_vistoria=excluded.data_vistoria,
            responsavel_area=excluded.responsavel_area,
            inspecionado_por=excluded.inspecionado_por,
            respostas_json=excluded.respostas_json
    """, (
        created_at, int(ano), str(mes), str(setor), str(data_vistoria),
        str(responsavel_area), str(inspecionado_por),
        json.dumps(respostas, ensure_ascii=False)
    ))
    conn.commit()

def load_df():
    df = pd.read_sql("SELECT * FROM vistoria", conn)
    if df.empty:
        return df

    df["respostas"] = df["respostas_json"].apply(json.loads)
    df["sim"] = df["respostas"].apply(lambda r: sum(1 for v in r.values() if v == "Sim"))
    df["nao"] = df["respostas"].apply(lambda r: sum(1 for v in r.values() if v == "Não"))
    df["total_itens"] = df["respostas"].apply(lambda r: len(r))
    df["mes_ano"] = df["ano"].astype(str) + "-" + df["mes"]
    return df

def delete_vistoria(ano, mes, setor):
    c.execute("DELETE FROM vistoria WHERE ano=? AND mes=? AND setor=?", (int(ano), str(mes), str(setor)))
    conn.commit()

# ========================
# MODO ADMIN (via URL)
# ========================
# Ex.: https://SEUAPP.streamlit.app/?admin=1&key=Uni06032023
is_admin = (st.query_params.get("admin") == "1" and st.query_params.get("key") == CHAVE_ADMIN)

# ========================
# LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='color:#2EA3D4;'>Sistema de Vistoria CIPA</h1>", unsafe_allow_html=True)
    st.write("🔒 Acesso restrito")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == SENHA_USUARIO:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ========================
# CABEÇALHO
# ========================
st.markdown("<h1 style='color:#2EA3D4;'>Sistema de Vistoria CIPA</h1>", unsafe_allow_html=True)

# Se você subir o logo como "logo.png" no GitHub, isso mostra no topo:
try:
    st.image("logo.png", width=220)
except Exception:
    pass

st.divider()

# ========================
# ABAS
# ========================
abas = ["📝 Preencher", "📊 Dashboard"] + (["🛠️ Admin"] if is_admin else [])
tabs = st.tabs(abas)

# ========================
# PREENCHER
# ========================
with tabs[0]:
    ano = st.number_input("Ano", value=datetime.now().year)
    mes = st.selectbox("Mês", MESES)
    setor = st.selectbox("Setor", SETORES)
    data_vistoria = st.date_input("Data", value=date.today())

    responsavel_area = st.text_input("Responsável da área *")
    inspecionado_por = st.text_input("Inspecionado por *")

    st.divider()

    respostas = {}
    for p in PERGUNTAS:
        respostas[p] = st.radio(p, ["Sim", "Não"], horizontal=True, key=f"resp_{p}")

    if st.button("💾 Salvar"):
        if not responsavel_area.strip():
            st.error("Informe o responsável.")
        elif not inspecionado_por.strip():
            st.error("Informe quem inspecionou.")
        else:
            upsert_vistoria(
                ano, mes, setor, data_vistoria.isoformat(),
                responsavel_area.strip(), inspecionado_por.strip(), respostas
            )
            st.success("✅ Registro salvo / atualizado!")

# ========================
# DASHBOARD
# ========================
with tabs[1]:
    st.subheader("Dashboard")

    df = load_df()
    if df.empty:
        st.info("Sem dados.")
    else:
        # FILTROS
        col1, col2, col3 = st.columns(3)

        with col1:
            anos = sorted(df["ano"].unique().tolist())
            f_ano = st.multiselect("Ano", anos, default=anos)

        with col2:
            meses_disp = sorted(df["mes"].unique().tolist())
            f_mes = st.multiselect("Mês", meses_disp, default=meses_disp)

        with col3:
            setores_disp = sorted(df["setor"].unique().tolist())
            f_setor = st.multiselect("Setor", setores_disp, default=setores_disp)

        dff = df[(df["ano"].isin(f_ano)) & (df["mes"].isin(f_mes)) & (df["setor"].isin(f_setor))].copy()

        if dff.empty:
            st.warning("Sem dados para os filtros selecionados.")
        else:
            total_sim = int(dff["sim"].sum())
            total_nao = int(dff["nao"].sum())
            total_itens = int(dff["total_itens"].sum())
            pct = (total_sim / total_itens * 100) if total_itens > 0 else 0

            k1, k2, k3 = st.columns(3)
            k1.metric("Conformidades (Sim)", total_sim)
            k2.metric("Não Conformidades (Não)", total_nao)
            k3.metric("% Conformidade", f"{pct:.1f}%")

            st.divider()

            st.write("### Conformidade x Não conformidade por Setor")
            graf_setor = dff.groupby("setor")[["sim", "nao"]].sum().sort_values("nao", ascending=False)
            st.bar_chart(graf_setor)

            st.write("### Evolução por competência (mês/ano)")
            evol = dff.groupby("mes_ano")[["sim", "nao"]].sum().sort_index()
            st.line_chart(evol)

# ========================
# ADMIN
# ========================
if is_admin:
    with tabs[2]:
        st.subheader("Admin (interno)")

        df = load_df()
        if df.empty:
            st.info("Sem dados para exportar/excluir.")
        else:
            st.write("### Exportar CSV (1 linha por item)")
            rows = []
            for _, r in df.iterrows():
                resp = r["respostas"]
                for item, resposta in resp.items():
                    rows.append({
                        "created_at": r["created_at"],
                        "ano": r["ano"],
                        "mes": r["mes"],
                        "setor": r["setor"],
                        "data_vistoria": r["data_vistoria"],
                        "responsavel_area": r["responsavel_area"],
                        "inspecionado_por": r["inspecionado_por"],
                        "item": item,
                        "resposta": resposta
                    })
            flat = pd.DataFrame(rows)
            csv = flat.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Baixar CSV", data=csv, file_name="vistorias_cipa.csv", mime="text/csv")

            st.divider()
            st.write("### Excluir registro (por Ano / Mês / Setor)")

            colA, colB, colC = st.columns(3)
            with colA:
                a_ano = st.selectbox("Ano", sorted(df["ano"].unique().tolist()))
            with colB:
                a_mes = st.selectbox("Mês", sorted(df[df["ano"] == a_ano]["mes"].unique().tolist()))
            with colC:
                setores_do_periodo = df[(df["ano"] == a_ano) & (df["mes"] == a_mes)]["setor"].unique().tolist()
                a_setor = st.selectbox("Setor", sorted(setores_do_periodo))

            st.caption("⚠️ A exclusão remove o registro e atualiza os gráficos.")

            confirmar = st.checkbox("Confirmar exclusão")
            if st.button("🗑️ Excluir", disabled=not confirmar):
                delete_vistoria(a_ano, a_mes, a_setor)
                st.success("✅ Registro excluído.")
                st.rerun()
