import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date

# ========================
# CONFIGURAÇÕES
# ========================
APP_TITULO = "Plataforma de Inspeções - CIPA & Brigada"
APP_VERSAO = "v4.3"
AMBIENTE = "Produção"

SENHA_USUARIO = "SSTLIDER"       # senha para usuários preencherem/consultarem
CHAVE_ADMIN = "Uni06032023"      # chave interna (admin via URL)

DB = "banco_v4.db"
MESES = ["01","02","03","04","05","06","07","08","09","10","11","12"]

# ========================
# PAGE CONFIG (TEM QUE SER ANTES DE QUALQUER st.*)
# ========================
st.set_page_config(page_title=APP_TITULO, layout="wide")

# ===== Setores CIPA (24) =====
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

# ============================================================
# PERGUNTAS (AGRUPADAS POR SUBGRUPO) — MOSTRAR TODAS DE UMA VEZ
# ============================================================
# Formato da chave do item salvo:
#   "<SUBGRUPO> :: <ITEM>"
CHECKLISTS = {
    "CIPA": {
        "01. Área Geral de Trabalho / Instalações": [
            "1. Superfícies de trabalho estão secas ou então são antiderrapantes.",
            "2. Iluminação é adequada às tarefas que devem ser executadas.",
            "3. Há sinalização, placas ou outros dispositivos adequados de advertência para alertar os empregados sobre os riscos existentes na área de trabalho.",
            "4. Instalações Prediais (pisos, paredes, teto e fechamentos estão em boas condições).",
        ],
        "02. Corredores e Passadiços": [
            "1. Demarcação (com clareza).",
            "2. São mantidos livres de refugos e desimpedidos para o uso.",
            "3. Buracos, obstruções ou depressões encontram-se cobertos, demarcados, ou protegidos por qualquer outra forma, de modo a evitar que representem risco à segurança.",
            "4. Existe faixa de segurança para pedestres nas áreas de trânsito de empilhadeiras ou de outros equipamentos motorizados e há delimitação para impedir o acesso direto ao corredor de empilhadeiras.",
            "5. Saídas de emergência estão claramente demarcadas, desimpedidas e iluminadas.",
        ],
        "03. Equipamentos de Proteção Individual (EPI)": [
            "1. Existem disponíveis para cada tipo de tarefa.",
            "2. Os empregados estão usando corretamente os EPI’s e estes são apropriados à tarefa.",
            "3. Os EPIs que estão sendo usados apresentam-se limpos e em boas condições.",
            "4. Existe espaço adequado para a guarda de EPIs.",
        ],
        "04. Armazenagem de Materiais": [
            "1. Existe espaço adequado e apropriado para a guarda de cada tipo de material.",
            "2. Materiais estocados não estão bloqueando passagens ou vias de escape, estão afastados 50 cm das paredes / colunas.",
            "3. O espaço disponível no local de trabalho é adequado aos materiais que precisam ser armazenados.",
            "4. Os materiais estão arrumados, empilhados ou estocados, afastados de paredes ou colunas, de forma a evitar que caiam, desmoronem ou fiquem desequilibrados.",
            "5. Não existem quantidades excessivas de materiais armazenados na área de trabalho.",
        ],
        "05. Equipamentos, Máquinas, Ferramentas": [
            "1. Existe espaço adequado para a armazenagem de ferramentas e outros equipamentos.",
            "2. As ferramentas e equipamentos danificados são retirados de serviço.",
            "3. As ferramentas são transportadas adequadamente.",
            "4. Há espaço adequado em torno das máquinas para permitir operação e movimentação segura de materiais e pessoal.",
            "5. Todos os equipamentos fixos estão presos no piso de modo a impedir que se desloquem durante o uso.",
            "6. Todos os pontos de compressão/aperto e todas as partes cortantes/giratórias ou móveis das máquinas estão equipados com guardas de proteção.",
            "7. Guardas de proteção não permitem acesso de partes do corpo junto à área de risco.",
            "8. Dispositivos de proteção contra quedas são inspecionados e utilizados para trabalho em altura elevada (acima de 2 m).",
            "9. Todas as fontes de energia possuem sistema sinalizado e adequado para bloqueio.",
            "10. Quando as máquinas estão em manutenção, limpeza, etc. - Estão bloqueadas e sinalizadas?",
        ],
        "06. Instalações Elétricas": [
            "1. As áreas diante dos quadros elétricos e de controles são mantidas desobstruídas até uma distância mínima de 1 metro.",
            "2. Usa cabos / fiação elétrica e extensão temporária em instalações permanentes.",
            "3. Os cabos/fios de extensão temporária não oferecem risco de tropeções na área de trabalho.",
            "4. Os fios elétricos e cabos estão protegidos por eletrodutos, conduletes, etc..",
        ],
        "07. Housekeeping - Serviço de limpeza": [
            "1. A área está arrumada, limpa, organizada e livre de refugos.",
            "2. Se encontra acúmulo de sujeira, poeira ou outros materiais.",
            "3. Há risco de escorregões, tropeções ou riscos de queda na área de trabalho.",
        ],
        "08. Operações e Processos de Alto Risco (TRABALHO EM ALTURA)": [
            "1. Existe um inventário e procedimentos para a execução de operações e processos de alto risco.",
            "2. Apenas o pessoal treinado executa as atividades de alto risco.",
            "3. As atividades de alto risco estão sendo executadas conforme procedimentos.",
            "4. Trabalhos em altura, espaço confinado, equipamento energizado, ou de abertura de linha têm “Permissão de Trabalho”, devidamente preenchida, válida e assinada pelo emitente e executantes.",
            "5. Os trabalhos especiais estão sendo realizados conforme orientação das Permissões de Trabalho.",
            "6. Os trabalhos especiais estão gerando algum risco não identificado nas Permissões de Trabalho.",
        ],
        "09. Treinamento": [
            "1. Os empregados passaram por treinamento adequado em relação às questões de saúde e segurança.",
            "2. Existe meios de comprovação dos treinamentos.",
            "3. Os empregados têm plena consciência dos riscos envolvidos na tarefa que está sendo executada.",
            "4. As ações dos empregados demonstram terem recebido um nível de treinamento adequado.",
        ],
        "10. Equipamentos com Força Motriz Própria e Outros Equipamentos para Transporte": [
            "1. As empilhadeiras e outros são adequados e estão em boas condições de uso.",
            "2. Carrinhos manuais estão em boas condições de uso.",
            "3. Os equipamentos com força motriz própria são inspecionados antes do uso diariamente (Verificar Check List).",
            "4. Os equipamentos para transporte de materiais possuem identificação da capacidade máxima de carga.",
            "5. Cabos de aço, cintas e outros acessórios estão em boas condições.",
            "6. Os operadores de equipamentos com força motriz própria possuem treinamento e são autorizados/credenciados.",
        ],
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

ASSUNTO_FIXO = "Geral"

def setores_por_tipo(tipo: str):
    return CIPA_SETORES if tipo == "CIPA" else BRIGADA_SETORES

def subgrupos_por_tipo(tipo: str):
    return list(CHECKLISTS[tipo].keys())

# ========================
# BANCO (SQLite)
# ========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    tipo TEXT NOT NULL,
    assunto TEXT NOT NULL,
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

def delete_registro(tipo, ano, mes, setor):
    c.execute("""
        DELETE FROM registros
        WHERE tipo=? AND assunto=? AND ano=? AND mes=? AND setor=?
    """, (tipo, ASSUNTO_FIXO, int(ano), str(mes), str(setor)))
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

def explode_respostas(dff: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in dff.iterrows():
        resp_dict = r["respostas"] if isinstance(r["respostas"], dict) else {}
        for item_key, resp in resp_dict.items():
            if " :: " in item_key:
                subgrupo, item = item_key.split(" :: ", 1)
            else:
                subgrupo, item = "(Sem subgrupo)", item_key
            rows.append({
                "tipo": r["tipo"],
                "ano": r["ano"],
                "mes": r["mes"],
                "mes_ano": r["mes_ano"],
                "setor": r["setor"],
                "data_vistoria": r["data_vistoria"],
                "responsavel_area": r["responsavel_area"],
                "inspecionado_por": r["inspecionado_por"],
                "subgrupo": subgrupo,
                "item": item,
                "resposta": resp
            })
    x = pd.DataFrame(rows)
    if x.empty:
        return x
    x["sim"] = (x["resposta"] == "Sim").astype(int)
    x["nao"] = (x["resposta"] == "Não").astype(int)
    return x

def export_flat_csv(dff: pd.DataFrame) -> bytes:
    x = explode_respostas(dff)
    if x.empty:
        return pd.DataFrame([]).to_csv(index=False).encode("utf-8-sig")
    cols = ["tipo","subgrupo","item","resposta","ano","mes","mes_ano","setor","data_vistoria","responsavel_area","inspecionado_por"]
    return x[cols].to_csv(index=False).encode("utf-8-sig")

# ========================
# MODO ADMIN
# ========================
is_admin = (st.query_params.get("admin") == "1" and st.query_params.get("key") == CHAVE_ADMIN)

# ========================
# SESSÃO / LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False

def show_logo(width=150):
    for name in ["logo.png", "Logo.png", "Logo Oficial.png", "LogoOficial.png"]:
        try:
            st.image(name, width=width)
            return
        except Exception:
            pass

def header_premium(subtitulo: str):
    col_logo, col_title, col_info, col_logout = st.columns([1.2, 5, 2.2, 1.2])

    with col_logo:
        show_logo(width=150)

    with col_title:
        st.markdown(
            f"""
            <div style="line-height:1.1;">
              <div style="color:#2EA3D4; font-size:52px; font-weight:800; margin-bottom:0;">
                Plataforma de Inspeções
              </div>
              <div style="color:#1F2A44; font-size:18px; margin-top:-6px;">
                {subtitulo}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_info:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.markdown(
            f"""
            <div style="text-align:right; color:#1F2A44; font-size:13px; padding-top:10px;">
              <div><b>{AMBIENTE}</b> • {APP_VERSAO}</div>
              <div>{agora}</div>
              <div>{"Admin" if is_admin else "Usuário"}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_logout:
        if st.button("Sair", key="btn_logout"):
            st.session_state.logado = False
            st.rerun()

    st.divider()

# ========================
# TELA DE LOGIN
# ========================
if not st.session_state.logado:
    header_premium("CIPA & Brigada • acesso restrito")
    st.markdown("### Acesso")
    senha = st.text_input("Senha", type="password", key="login_senha")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Entrar", type="primary", key="login_btn"):
            if senha == SENHA_USUARIO:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    with c2:
        st.caption("Dica: use a senha informada pela Unicompass. Para acesso Admin, use o link com parâmetros.")
    st.stop()

# ========================
# CABEÇALHO INTERNO
# ========================
header_premium("CIPA & Brigada")

# ========================
# MENU LATERAL
# ========================
st.sidebar.title("Menu")
st.sidebar.caption("Navegação do sistema")

pagina = st.sidebar.radio(
    "Ir para",
    options=(["📝 Preencher", "📊 Dashboard"] + (["🛠️ Admin"] if is_admin else [])),
    key="nav_pagina"
)

st.sidebar.divider()
st.sidebar.caption("Admin (interno) via URL:")
st.sidebar.code("?admin=1&key=********", language="text")

# ========================
# PÁGINA: PREENCHER
# ========================
if pagina == "📝 Preencher":
    st.subheader("Preencher Checklist")

    colA, colB = st.columns([2, 3])
    with colA:
        tipo = st.radio("Tipo", ["CIPA", "BRIGADA"], horizontal=True, key="pre_tipo")

    col1, col2, col3, col4 = st.columns([1, 1, 4, 2])
    with col1:
        ano = st.number_input("Ano", min_value=2020, max_value=2100, value=datetime.now().year, step=1, key="pre_ano")
    with col2:
        mes = st.selectbox("Mês", MESES, index=MESES.index(f"{datetime.now().month:02d}"), key="pre_mes")
    with col3:
        setor = st.selectbox("Setor", setores_por_tipo(tipo), key="pre_setor")
    with col4:
        data_vistoria = st.date_input("Data", value=date.today(), key="pre_data")

    col5, col6 = st.columns(2)
    with col5:
        responsavel_area = st.text_input("Responsável da área *", key="pre_resp_area")
    with col6:
        inspecionado_por = st.text_input("Inspecionado por *", key="pre_insp_por")

    st.caption("Campos com * são obrigatórios. Regra: 1 registro por Tipo + Setor + Mês + Ano (salvar atualiza).")
    st.divider()

    # Perguntas: SEM PRE-SELECT (index=None) e SEM expander (tudo aberto)
    respostas = {}
    subgrupos = subgrupos_por_tipo(tipo)

    q_index = 0
    for sg in subgrupos:
        itens = CHECKLISTS[tipo][sg]
        st.markdown(f"### {sg}")

        for item in itens:
            item_key = f"{sg} :: {item}"
            respostas[item_key] = st.radio(
                item,
                ["Sim", "Não"],
                horizontal=True,
                index=None,  # <- SEM pré-seleção
                key=f"q_{tipo}_{ano}_{mes}_{setor}_{q_index}"
            )
            q_index += 1

        st.divider()

    if st.button("💾 Salvar/Atualizar", type="primary", key="pre_salvar"):
        if not responsavel_area.strip():
            st.error("Informe o Responsável da área.")
        elif not inspecionado_por.strip():
            st.error("Informe quem realizou a inspeção (Inspecionado por).")
        else:
            faltando = [k for k, v in respostas.items() if v is None]
            if faltando:
                st.error(f"⚠️ Existem {len(faltando)} respostas sem preenchimento. Responda todas as perguntas para salvar.")
            else:
                upsert_registro(
                    tipo=tipo,
                    assunto=ASSUNTO_FIXO,
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
# PÁGINA: DASHBOARD
# ========================
elif pagina == "📊 Dashboard":
    st.subheader("Dashboard")

    df = load_df()
    if df.empty:
        st.info("Ainda não há registros.")
    else:
        c1, c2, c3 = st.columns([1.2, 2.4, 2.4])

        with c1:
            f_tipo = st.selectbox("Tipo", sorted(df["tipo"].unique().tolist()), key="dash_tipo")

        base = df[df["tipo"] == f_tipo].copy()

        with c2:
            anos = sorted(base["ano"].unique().tolist())
            f_ano = st.multiselect("Ano", anos, default=anos, key="dash_ano")

        with c3:
            meses = sorted(base["mes"].unique().tolist())
            f_mes = st.multiselect("Mês", meses, default=meses, key="dash_mes")

        setores_disp = sorted(base["setor"].unique().tolist())
        f_setor = st.multiselect("Setor", setores_disp, default=setores_disp, key="dash_setor")

        dff = base[
            (base["ano"].isin(f_ano)) &
            (base["mes"].isin(f_mes)) &
            (base["setor"].isin(f_setor))
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

            st.write("### Conformidade x Não conformidade por Subgrupo")
            x = explode_respostas(dff)
            if x.empty:
                st.info("Sem itens explodidos.")
            else:
                graf_sg = x.groupby("subgrupo")[["sim", "nao"]].sum().sort_values("nao", ascending=False)
                st.bar_chart(graf_sg)

            st.write("### Evolução por competência (mês/ano)")
            evol = dff.groupby("mes_ano")[["sim", "nao"]].sum().sort_index()
            st.line_chart(evol)

            st.divider()
            st.write("### Exportar (CSV) — disponível para o usuário")
            csv_bytes = export_flat_csv(dff)
            st.download_button(
                "⬇️ Baixar CSV (filtrado)",
                data=csv_bytes,
                file_name=f"inspecoes_{f_tipo}.csv".replace(" ", "_"),
                mime="text/csv",
                key="dash_export_csv"
            )

# ========================
# PÁGINA: ADMIN
# ========================
elif pagina == "🛠️ Admin" and is_admin:
    st.subheader("Admin (interno)")
    st.caption("Acesso via URL: ?admin=1&key=...")

    df = load_df()
    if df.empty:
        st.info("Sem registros.")
    else:
        st.write("### Excluir registro (por Tipo / Competência / Setor)")

        col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 4])

        with col1:
            a_tipo = st.selectbox("Tipo", sorted(df["tipo"].unique().tolist()), key="adm_tipo")

        base = df[df["tipo"] == a_tipo].copy()

        with col2:
            a_anos = sorted(base["ano"].unique().tolist())
            a_ano = st.selectbox("Ano", a_anos, key="adm_ano")

        with col3:
            a_meses = sorted(base[base["ano"] == a_ano]["mes"].unique().tolist())
            a_mes = st.selectbox("Mês", a_meses, key="adm_mes")

        with col4:
            setores = sorted(base[(base["ano"] == a_ano) & (base["mes"] == a_mes)]["setor"].unique().tolist())
            a_setor = st.selectbox("Setor", setores, key="adm_setor") if setores else None

        if a_setor:
            preview = base[
                (base["ano"] == a_ano) &
                (base["mes"] == a_mes) &
                (base["setor"] == a_setor)
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
                if st.button("🗑️ Excluir", disabled=not confirm, key="adm_excluir"):
                    delete_registro(a_tipo, a_ano, a_mes, a_setor)
                    st.success("✅ Registro excluído.")
                    st.rerun()

else:
    st.warning("Você não tem permissão para acessar esta página.")
