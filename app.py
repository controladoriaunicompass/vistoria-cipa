import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date

# ========================
# CONFIGURAÇÕES
# ========================
APP_TITULO = "Sistema de Vistoria CIPA"

SENHA_USUARIO = "1234"     # senha única para entrar
CHAVE_ADMIN = "admin123"   # chave secreta para modo admin (interno)

DB = "banco_v2.db"

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

# ✅ TROQUE AQUI pelas perguntas reais do seu checklist (pode colar TODAS)
PERGUNTAS = [
    "Superfícies de trabalho estão secas ou então são antiderrapantes.",
    "Iluminação é adequada às tarefas que devem ser executadas.",
    "Há sinalização/placas adequadas para alertar riscos.",
    "Instalações prediais em boas condições (pisos, paredes, teto, fechamentos).",
    "Saídas de emergência demarcadas, desimpedidas e iluminadas."
]

# ========================
# BANCO DE DADOS
# ========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS vistoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    ano INTEGER NOT NULL,
    mes TEXT NOT NULL,
    setor TEXT NOT NULL,
    data_vistoria TEXT NOT NULL,
    responsavel_area TEXT NOT NULL,
    inspecionado_por TEXT NOT NULL,
    respostas_json TEXT NOT NULL,
    UNIQUE(ano, mes, setor)
)
""")
conn.commit()

def upsert_vistoria(ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas):
    created_at = datetime.now().isoformat(timespec="seconds")
    c.execute("""
        INSERT INTO vistoria (created_at, ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ano, mes, setor) DO UPDATE SET
            created_at=excluded.created_at,
            data_vistoria=excluded.data_vistoria,
            responsavel_area=excluded.responsavel_area,
            inspecionado_por=excluded.inspecionado_por,
            respostas_json=excluded.respostas_json
    """, (
        created_at, int(ano), str(mes), str(setor),
        str(data_vistoria), responsavel_area, inspecionado_por,
        json.dumps(respostas, ensure_ascii=False)
    ))
    conn.commit()

def delete_vistoria(ano, mes, setor):
    c.execute("DELETE FROM vistoria WHERE ano=? AND mes=? AND setor=?", (int(ano), str(mes), str(setor)))
    conn.commit()

def get_vistoria(ano, mes, setor):
    df = pd.read_sql(
        "SELECT * FROM vistoria WHERE ano=? AND mes=? AND setor=?",
        conn, params=(int(ano), str(mes), str(setor))
    )
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    row["respostas"] = json.loads(row["respostas_json"])
    return row

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

# ========================
# MODO ADMIN (interno)
# ========================
# Use assim (só você):
# https://SEUAPP.streamlit.app/?admin=1&key=admin123
is_admin = (st.query_params.get("admin") == "1" and st.query_params.get("key") == CHAVE_ADMIN)

# ========================
# LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title(APP_TITULO)
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
# APP
# ========================
st.set_page_config(page_title=APP_TITULO, layout="wide")
st.title(APP_TITULO)

abas = ["📝 Preencher", "📊 Dashboard"] + (["🛠️ Admin (interno)"] if is_admin else [])
tabs = st.tabs(abas)

# ============
# TAB: PREENCHER
# ============
with tabs[0]:
    st.subheader("Preencher Vistoria (mensal por setor)")

    # pré-carga para edição via admin
    default_ano = st.session_state.get("edit_ano", datetime.now().year)
    default_mes = st.session_state.get("edit_mes", f"{datetime.now().month:02d}")
    default_setor = st.session_state.get("edit_setor", SETORES[0])
    default_data = st.session_state.get("edit_data", date.today().isoformat())
    default_resp_area = st.session_state.get("edit_resp_area", "")
    default_insp_por = st.session_state.get("edit_insp_por", "")
    default_respostas = st.session_state.get("edit_respostas", {})

    col1, col2, col3, col4 = st.columns([1, 1, 4, 2])
    with col1:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=int(default_ano), step=1)
    with col2:
        mes = st.selectbox("Mês", MESES, index=MESES.index(str(default_mes)) if str(default_mes) in MESES else 0)
    with col3:
        setor = st.selectbox("Setor", SETORES, index=SETORES.index(default_setor) if default_setor in SETORES else 0)
    with col4:
        data_vistoria = st.date_input("Data", value=date.fromisoformat(default_data) if isinstance(default_data, str) else date.today())

    col5, col6 = st.columns(2)
    with col5:
        responsavel_area = st.text_input("Responsável da área *", value=default_resp_area)
    with col6:
        inspecionado_por = st.text_input("Inspecionado por *", value=default_insp_por)

    st.caption("Campos com * são obrigatórios. Regra: 1 registro por Setor + Mês + Ano (salvar atualiza).")
    st.divider()

    respostas = {}
    for p in PERGUNTAS:
        pre = default_respostas.get(p, "Sim")
        idx = 0 if pre == "Sim" else 1
        respostas[p] = st.radio(p, ["Sim", "Não"], horizontal=True, index=idx, key=f"q_{p}")

    if st.button("💾 Salvar/Atualizar", type="primary"):
        if not str(responsavel_area).strip():
            st.error("Informe o Responsável da área.")
        elif not str(inspecionado_por).strip():
            st.error("Informe quem inspecionou (Inspecionado por).")
        else:
            upsert_vistoria(
                ano=ano, mes=mes, setor=setor,
                data_vistoria=data_vistoria.isoformat(),
                responsavel_area=responsavel_area.strip(),
                inspecionado_por=inspecionado_por.strip(),
                respostas=respostas
            )
            # limpa modo edição
            for k in ["edit_ano","edit_mes","edit_setor","edit_data","edit_resp_area","edit_insp_por","edit_respostas"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("✅ Registro salvo/atualizado com sucesso!")

# ============
# TAB: DASHBOARD
# ============
with tabs[1]:
    st.subheader("Dashboard")

    df = load_df()
    if df.empty:
        st.info("Ainda não há vistorias registradas.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            f_ano = st.multiselect("Ano", sorted(df["ano"].unique().tolist()), default=sorted(df["ano"].unique().tolist()))
        with c2:
            f_mes = st.multiselect("Mês", MESES, default=MESES)
        with c3:
            f_setor = st.multiselect("Setor", SETORES, default=SETORES)

        dff = df[df["ano"].isin(f_ano) & df["mes"].isin(f_mes) & df["setor"].isin(f_setor)].copy()
        if dff.empty:
            st.warning("Sem dados para os filtros selecionados.")
        else:
            total_reg = len(dff)
            total_sim = int(dff["sim"].sum())
            total_nao = int(dff["nao"].sum())
            total_itens = int(dff["total_itens"].sum())
            pct_conf = 100.0 * (total_sim / max(1, total_itens))

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Vistorias", total_reg)
            k2.metric("Conformidades (Sim)", total_sim)
            k3.metric("Não Conformidades (Não)", total_nao)
            k4.metric("% Conformidade", f"{pct_conf:.1f}%")

            st.divider()

            st.write("### Conformidade x Não conformidade por Setor")
            por_setor = dff.groupby("setor", as_index=False)[["sim","nao"]].sum()
            por_setor = por_setor.sort_values("nao", ascending=False)
            por_setor.rename(columns={"sim":"Conformidade (Sim)", "nao":"Não conformidade (Não)"}, inplace=True)
            st.bar_chart(por_setor.set_index("setor"))

            st.write("### Evolução mensal (Sim x Não)")
            por_mes = dff.groupby("mes_ano", as_index=False)[["sim","nao"]].sum().sort_values("mes_ano")
            por_mes.rename(columns={"sim":"Conformidade (Sim)", "nao":"Não conformidade (Não)"}, inplace=True)
            st.line_chart(por_mes.set_index("mes_ano"))

# ============
# TAB: ADMIN (interno)
# ============
if is_admin:
    with tabs[2]:
        st.subheader("Admin (interno)")
        st.caption("Acesso por link secreto: ?admin=1&key=...")

        df = load_df()
        if df.empty:
            st.info("Sem registros.")
        else:
            st.write("### Exportar CSV (resultados por item)")
            rows = []
            for _, r in df.iterrows():
                for item, resp in r["respostas"].items():
                    rows.append({
                        "created_at": r["created_at"],
                        "ano": r["ano"],
                        "mes": r["mes"],
                        "setor": r["setor"],
                        "data_vistoria": r["data_vistoria"],
                        "responsavel_area": r["responsavel_area"],
                        "inspecionado_por": r["inspecionado_por"],
                        "item": item,
                        "resposta": resp
                    })
            flat = pd.DataFrame(rows)
            csv = flat.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Baixar CSV", data=csv, file_name="vistorias_cipa.csv", mime="text/csv")

            st.divider()
            st.write("### Excluir / Editar preenchimento (interno)")
            colA, colB, colC = st.columns([1,1,6])
            with colA:
                a_ano = st.selectbox("Ano", sorted(df["ano"].unique().tolist()), key="adm_ano")
            with colB:
                a_mes = st.selectbox("Mês", sorted(df["mes"].unique().tolist()), key="adm_mes")
            with colC:
                subset = df[(df["ano"] == a_ano) & (df["mes"] == a_mes)].copy()
                setores_disp = subset["setor"].unique().tolist()
                a_setor = st.selectbox("Setor", setores_disp, key="adm_setor") if setores_disp else None

            if a_setor:
                reg = get_vistoria(a_ano, a_mes, a_setor)
                st.write("**Prévia do registro selecionado**")
                st.json({
                    "ano": reg["ano"],
                    "mes": reg["mes"],
                    "setor": reg["setor"],
                    "data_vistoria": reg["data_vistoria"],
                    "responsavel_area": reg["responsavel_area"],
                    "inspecionado_por": reg["inspecionado_por"],
                    "sim": sum(1 for v in reg["respostas"].values() if v == "Sim"),
                    "nao": sum(1 for v in reg["respostas"].values() if v == "Não"),
                })

                colE, colF = st.columns(2)
                with colE:
                    if st.button("✏️ Editar este registro"):
                        st.session_state["edit_ano"] = reg["ano"]
                        st.session_state["edit_mes"] = reg["mes"]
                        st.session_state["edit_setor"] = reg["setor"]
                        st.session_state["edit_data"] = reg["data_vistoria"]
                        st.session_state["edit_resp_area"] = reg["responsavel_area"]
                        st.session_state["edit_insp_por"] = reg["inspecionado_por"]
                        st.session_state["edit_respostas"] = reg["respostas"]
                        st.success("Abra a aba 📝 Preencher para alterar e salvar (atualiza o registro).")

                with colF:
                    confirm = st.checkbox("Confirmar exclusão", key="conf_del")
                    if st.button("🗑️ Excluir este registro", disabled=not confirm):
                        delete_vistoria(a_ano, a_mes, a_setor)
                        st.success("✅ Registro excluído.")
                        st.rerun()


