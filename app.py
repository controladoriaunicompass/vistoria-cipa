import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date

# ========================
# CONFIGURAÇÕES
# ========================
APP_TITULO = "Plataforma de Inspeções - CIPA & Brigada"

SENHA_USUARIO = "cipa2026"       # senha para usuários preencherem/consultarem
CHAVE_ADMIN = "Uni06032023"      # chave interna (admin via URL)

# Troquei o nome do DB para evitar conflito com versões antigas
DB = "banco_v4.db"

MESES = ["01","02","03","04","05","06","07","08","09","10","11","12"]

# ===== Setores CIPA (seus 24) =====
CIPA_SETORES = [
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

# ===== Setores BRIGADA (Hidrantes) =====
BRIGADA_SETORES = [
    "HIDRANTE 1 - DDP",
    "HIDRANTE 2 - CLICHERIA",
    "HIDRANTE 3 - DOCAS DE RECEBIMENTO",
    "HIDRANTE 4 - ESTOQUE DE CHAPAS",
    "HIDRANTE 5 - CORREDOR XTD-FF E COLADEIRA",
    "HIDRANTE 6 - BANHEIROS",
    "HIDRANTE 7 - COMERCIAL - SALA DE VIDRO",
    "HIDRANTE 8 - PALETIZAÇÃO",
    "HIDRANTE 9 - COMERCIAL - PRESIDÊNCIA",
    "HIDRANTE 10 - JYNIA",
    "HIDRANTE 11 - CARTÃO DE PONTO",
    "HIDRANTE 12 - QUIOSQUE",
    "HIDRANTE 13 - BARRACÃO LONADO (DESATIVADO)",
]

# ===== Perguntas por TIPO e ASSUNTO =====
CHECKLISTS = {
    "CIPA": {
        # Placeholder (você manda o checklist completo depois e eu organizo por assunto)
        "Geral": [
            "Superfícies de trabalho estão secas ou são antiderrapantes?",
            "Iluminação é adequada às tarefas?",
            "Há sinalização/placas de advertência adequadas?",
            "Instalações prediais (pisos, paredes, teto, fechamentos) estão em boas condições?",
            "Saídas de emergência estão demarcadas, desobstruídas e iluminadas?",
        ]
    },
    "BRIGADA": {
        "Instalações Elétricas": [
            "Há Instalações com fiação aparente?",
            "Há Inst. com ligações improvisadas?",
            "As Instal. oferecem algum risco?",
            "Há aterramento nos equipamentos?",
        ],
        "Extintores": [
            "Os extintores estão carregados?",
            "Há extintores obstruídos?",
            "Os extintores estão limpos?",
            "Os extintores estão sinalizados?",
            "Os extintores estão com selo do IMETRO?",
            "Os extintores estão com lacre OK?",
        ],
        "Hidrantes": [
            "Os hidrantes estão obstruídos?",
            "Sinalização de solo?",
            "Há vazamentos de água?",
            "Os registros estão O.K.?",
            "As mangueiras estão O.K.?",
            "As caixas estão completas?",
            "Há esguichos de jato regulável?",
            "Há esguicho de jato sólido?",
            "Há chaves de união (chave storz)?",
            "O sistema é usado p/ outros fins?",
            "Botoeiras para acionar a bomba estão funcionando?",
            "Sinal de alarme estão funcionando?",
        ],
        "Outros": [
            "Os alarmes de incêndio estão O.K.?",
            "Há líquidos inflam. estocados em local impróprio?",
            "Há acompanhamento da Brigada de Incêndio?",
            "O pára-raios está O.K.?",
            "Há sinalização para casos de emergência?",
            "As saídas de emerg. estão livres?",
            "A iluminação de emerg. está O.K.? (Verificar no Restaurante também)",
        ],
        "Sistemas Fixos": [
            "O NO-BREAK está conectado e O.K.?",
            "Os difusores estão desobstruídos?",
            "Os detetores de fumaça e calor estão O.K.? (verificar último relatório)",
            "As chaves seletoras estão O.K.?",
            "Os painéis de comando estão O.K.?",
        ],
    }
}

def setores_por_tipo(tipo: str):
    return CIPA_SETORES if tipo == "CIPA" else BRIGADA_SETORES

def assuntos_por_tipo(tipo: str):
    return list(CHECKLISTS[tipo].keys())

def perguntas_por_tipo_assunto(tipo: str, assunto: str):
    return CHECKLISTS[tipo][assunto]

# ========================
# BANCO (SQLite)
# ========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    tipo TEXT NOT NULL,          -- CIPA / BRIGADA
    assunto TEXT NOT NULL,       -- assunto do checklist
    ano INTEGER NOT NULL,
    mes TEXT NOT NULL,
    setor TEXT NOT NULL,
    data_vistoria TEXT NOT NULL,
    responsavel_area TEXT NOT NULL,
    inspecionado_por TEXT NOT NULL,
    respostas_json TEXT NOT NULL,
    UNIQUE(tipo, assunto, ano, mes, setor)
)
""")
conn.commit()

def upsert_registro(tipo, assunto, ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas_dict):
    created_at = datetime.now().isoformat(timespec="seconds")
    c.execute("""
        INSERT INTO registros
        (created_at, tipo, assunto, ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(tipo, assunto, ano, mes, setor) DO UPDATE SET
            created_at=excluded.created_at,
            data_vistoria=excluded.data_vistoria,
            responsavel_area=excluded.responsavel_area,
            inspecionado_por=excluded.inspecionado_por,
            respostas_json=excluded.respostas_json
    """, (
        created_at, tipo, assunto, int(ano), str(mes), str(setor),
        str(data_vistoria), str(responsavel_area), str(inspecionado_por),
        json.dumps(respostas_dict, ensure_ascii=False)
    ))
    conn.commit()

def delete_registro(tipo, assunto, ano, mes, setor):
    c.execute("""
        DELETE FROM registros
        WHERE tipo=? AND assunto=? AND ano=? AND mes=? AND setor=?
    """, (tipo, assunto, int(ano), str(mes), str(setor)))
    conn.commit()

def load_df():
    df = pd.read_sql("SELECT * FROM registros", conn)
    if df.empty:
        return df
    df["respostas"] = df["respostas_json"].apply(json.loads)
    df["sim"] = df["respostas"].apply(lambda r: sum(1 for v in r.values() if v == "Sim"))
    df["nao"] = df["respostas"].apply(lambda r: sum(1 for v in r.values() if v == "Não"))
    df["total_itens"] = df["respostas"].apply(lambda r: len(r))
    df["mes_ano"] = df["ano"].astype(str) + "-" + df["mes"]
    return df

def export_flat_csv(dff: pd.DataFrame) -> bytes:
    rows = []
    for _, r in dff.iterrows():
        for item, resp in r["respostas"].items():
            rows.append({
                "created_at": r["created_at"],
                "tipo": r["tipo"],
                "assunto": r["assunto"],
                "ano": r["ano"],
                "mes": r["mes"],
                "setor": r["setor"],
                "data_vistoria": r["data_vistoria"],
                "responsavel_area": r["responsavel_area"],
                "inspecionado_por": r["inspecionado_por"],
                "item": item,
                "resposta": resp,
            })
    flat = pd.DataFrame(rows)
    return flat.to_csv(index=False).encode("utf-8-sig")

# ========================
# MODO ADMIN (interno via URL)
# ========================
# Ex.: https://SEUAPP.streamlit.app/?admin=1&key=Uni06032023
is_admin = (st.query_params.get("admin") == "1" and st.query_params.get("key") == CHAVE_ADMIN)

# ========================
# LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h1 style='color:#2EA3D4;'>Plataforma de Inspeções</h1>", unsafe_allow_html=True)
    st.caption("CIPA & Brigada - acesso restrito")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == SENHA_USUARIO:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ========================
# UI
# ========================
st.markdown("<h1 style='color:#2EA3D4;'>Plataforma de Inspeções</h1>", unsafe_allow_html=True)
st.caption("CIPA & Brigada")

# Se subir o logo como logo.png no GitHub (raiz do repo), ele aparece:
try:
    st.image("logo.png", width=220)
except Exception:
    pass

st.divider()

abas = ["📝 Preencher", "📊 Dashboard"] + (["🛠️ Admin (interno)"] if is_admin else [])
tabs = st.tabs(abas)

# ========================
# TAB: PREENCHER
# ========================
with tabs[0]:
    st.subheader("Preencher Checklist")

    colA, colB = st.columns([2, 3])
    with colA:
        tipo = st.radio("Tipo", ["CIPA", "BRIGADA"], horizontal=True)
    with colB:
        assunto = st.selectbox("Assunto", assuntos_por_tipo(tipo))

    col1, col2, col3, col4 = st.columns([1,1,4,2])
    with col1:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=datetime.now().year, step=1)
    with col2:
        mes = st.selectbox("Mês", MESES, index=MESES.index(f"{datetime.now().month:02d}"))
    with col3:
        setor = st.selectbox("Setor", setores_por_tipo(tipo))
    with col4:
        data_vistoria = st.date_input("Data", value=date.today())

    col5, col6 = st.columns(2)
    with col5:
        responsavel_area = st.text_input("Responsável da área *")
    with col6:
        inspecionado_por = st.text_input("Inspecionado por *")

    st.caption("Campos com * são obrigatórios. Regra: 1 registro por Tipo + Assunto + Setor + Mês + Ano (salvar atualiza).")
    st.divider()

    perguntas = perguntas_por_tipo_assunto(tipo, assunto)
    respostas = {}

    for p in perguntas:
        respostas[p] = st.radio(p, ["Sim", "Não"], horizontal=True, key=f"{tipo}_{assunto}_{p}")

    if st.button("💾 Salvar/Atualizar", type="primary"):
        if not responsavel_area.strip():
            st.error("Informe o Responsável da área.")
        elif not inspecionado_por.strip():
            st.error("Informe quem realizou a inspeção (Inspecionado por).")
        else:
            upsert_registro(
                tipo=tipo,
                assunto=assunto,
                ano=ano,
                mes=mes,
                setor=setor,
                data_vistoria=data_vistoria.isoformat(),
                responsavel_area=responsavel_area.strip(),
                inspecionado_por=inspecionado_por.strip(),
                respostas_dict=respostas
            )
            st.success("✅ Registro salvo/atualizado!")

# ========================
# TAB: DASHBOARD
# ========================
with tabs[1]:
    st.subheader("Dashboard")

    df = load_df()
    if df.empty:
        st.info("Ainda não há registros.")
    else:
        # Filtros (inclui tipo/assunto + competência + setor)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f_tipo = st.selectbox("Tipo", sorted(df["tipo"].unique().tolist()))
        with c2:
            assuntos = sorted(df[df["tipo"] == f_tipo]["assunto"].unique().tolist())
            f_assunto = st.selectbox("Assunto", assuntos)
        with c3:
            anos = sorted(df[(df["tipo"] == f_tipo) & (df["assunto"] == f_assunto)]["ano"].unique().tolist())
            f_ano = st.multiselect("Ano", anos, default=anos)
        with c4:
            meses = sorted(df[(df["tipo"] == f_tipo) & (df["assunto"] == f_assunto)]["mes"].unique().tolist())
            f_mes = st.multiselect("Mês", meses, default=meses)

        setores_disp = sorted(df[(df["tipo"] == f_tipo) & (df["assunto"] == f_assunto)]["setor"].unique().tolist())
        f_setor = st.multiselect("Setor", setores_disp, default=setores_disp)

        dff = df[
            (df["tipo"] == f_tipo) &
            (df["assunto"] == f_assunto) &
            (df["ano"].isin(f_ano)) &
            (df["mes"].isin(f_mes)) &
            (df["setor"].isin(f_setor))
        ].copy()

        if dff.empty:
            st.warning("Sem dados para os filtros selecionados.")
        else:
            total_sim = int(dff["sim"].sum())
            total_nao = int(dff["nao"].sum())
            total_itens = int(dff["total_itens"].sum())
            pct = (total_sim / total_itens * 100) if total_itens > 0 else 0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Registros", len(dff))
            k2.metric("Conformidades (Sim)", total_sim)
            k3.metric("Não conformidades (Não)", total_nao)
            k4.metric("% Conformidade", f"{pct:.1f}%")

            st.divider()

            st.write("### Conformidade x Não conformidade por Setor")
            graf_setor = dff.groupby("setor")[["sim", "nao"]].sum().sort_values("nao", ascending=False)
            st.bar_chart(graf_setor)

            st.write("### Evolução por competência (mês/ano)")
            evol = dff.groupby("mes_ano")[["sim", "nao"]].sum().sort_index()
            st.line_chart(evol)

            st.divider()

            # ✅ Export CSV para usuário (como você pediu)
            st.write("### Exportar (CSV)")
            csv_bytes = export_flat_csv(dff)
            st.download_button(
                "⬇️ Baixar CSV (filtrado)",
                data=csv_bytes,
                file_name=f"inspecoes_{f_tipo}_{f_assunto}.csv".replace(" ", "_"),
                mime="text/csv"
            )

# ========================
# TAB: ADMIN (interno)
# ========================
if is_admin:
    with tabs[2]:
        st.subheader("Admin (interno)")
        st.caption("Acesso via URL: ?admin=1&key=...")

        df = load_df()
        if df.empty:
            st.info("Sem registros.")
        else:
            st.write("### Excluir registro (por Tipo / Assunto / Competência / Setor)")

            col1, col2, col3, col4, col5 = st.columns([1.2, 2.2, 1, 1, 3])
            with col1:
                a_tipo = st.selectbox("Tipo", sorted(df["tipo"].unique().tolist()), key="adm_tipo")
            with col2:
                a_assunto = st.selectbox("Assunto", sorted(df[df["tipo"] == a_tipo]["assunto"].unique().tolist()), key="adm_assunto")
            with col3:
                a_ano = st.selectbox("Ano", sorted(df[(df["tipo"] == a_tipo) & (df["assunto"] == a_assunto)]["ano"].unique().tolist()), key="adm_ano")
            with col4:
                a_mes = st.selectbox("Mês", sorted(df[(df["tipo"] == a_tipo) & (df["assunto"] == a_assunto) & (df["ano"] == a_ano)]["mes"].unique().tolist()), key="adm_mes")
            with col5:
                setores = sorted(df[
                    (df["tipo"] == a_tipo) &
                    (df["assunto"] == a_assunto) &
                    (df["ano"] == a_ano) &
                    (df["mes"] == a_mes)
                ]["setor"].unique().tolist())
                a_setor = st.selectbox("Setor", setores, key="adm_setor") if setores else None

            if a_setor:
                preview = df[
                    (df["tipo"] == a_tipo) &
                    (df["assunto"] == a_assunto) &
                    (df["ano"] == a_ano) &
                    (df["mes"] == a_mes) &
                    (df["setor"] == a_setor)
                ].copy()

                if preview.empty:
                    st.warning("Registro não encontrado.")
                else:
                    r = preview.iloc[0]
                    st.json({
                        "tipo": r["tipo"],
                        "assunto": r["assunto"],
                        "ano": int(r["ano"]),
                        "mes": r["mes"],
                        "setor": r["setor"],
                        "data_vistoria": r["data_vistoria"],
                        "responsavel_area": r["responsavel_area"],
                        "inspecionado_por": r["inspecionado_por"],
                        "sim": int(r["sim"]),
                        "nao": int(r["nao"]),
                    })

                    confirm = st.checkbox("Confirmar exclusão", key="adm_confirm")
                    if st.button("🗑️ Excluir", disabled=not confirm):
                        delete_registro(a_tipo, a_assunto, a_ano, a_mes, a_setor)
                        st.success("✅ Registro excluído.")
                        st.rerun()
