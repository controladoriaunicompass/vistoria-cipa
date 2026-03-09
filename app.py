import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ========================
# CONFIGURAÇÕES
# ========================
APP_TITULO = "Plataforma de Inspeções - CIPA & Brigada"
APP_VERSAO = "v5.0"
AMBIENTE = "Produção"

SENHA_USUARIO = "SSTLIDER"
CHAVE_ADMIN = "Uni06032023"

SPREADSHEET_NAME = "inspecoes_CIPA"
WS_DADOS = "dados"
WS_BACKUP = "backup"

MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# ========================
# PAGE CONFIG
# ========================
st.set_page_config(page_title=APP_TITULO, layout="wide")

# ========================
# QUERY PARAMS
# ========================
def get_qp(name: str, default: str = "") -> str:
    try:
        qp = st.query_params
        val = qp.get(name, default)
        if isinstance(val, (list, tuple)):
            return val[0] if val else default
        return str(val)
    except Exception:
        pass

    try:
        qp = st.experimental_get_query_params()
        val = qp.get(name, [default])
        return val[0] if val else default
    except Exception:
        return default

admin_flag = get_qp("admin", "")
admin_key = get_qp("key", "")
is_admin_url = (admin_flag == "1" and admin_key == CHAVE_ADMIN)

# ========================
# SETORES
# ========================
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

# ========================
# CHECKLISTS
# ========================
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
# GOOGLE SHEETS
# ========================
DADOS_HEADERS = [
    "id_registro","tipo","subgrupo","item","resposta","observacao","ano","mes","mes_ano",
    "setor","data_vistoria","responsavel_area","inspecionado_por","status","atualizado_em"
]
BACKUP_HEADERS = [
    "acao","data_hora","id_registro","tipo","subgrupo","item","resposta","observacao","ano","mes",
    "mes_ano","setor","data_vistoria","responsavel_area","inspecionado_por"
]

def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(creds)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def get_worksheet(spreadsheet, worksheet_name: str, headers: list[str]):
    try:
        ws = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=max(20, len(headers)+5))
        ws.append_row(headers)
        return ws

    first_row = ws.row_values(1)
    if not first_row:
        ws.append_row(headers)
    else:
        normalized_first = [str(c).strip().lower() for c in first_row]
        normalized_headers = [h.lower() for h in headers]
        if normalized_first != normalized_headers:
            ws.clear()
            ws.append_row(headers)
    return ws

def get_spreadsheet_and_tabs():
    gc = get_gsheet_client()
    sh = gc.open(SPREADSHEET_NAME)
    ws_dados = get_worksheet(sh, WS_DADOS, DADOS_HEADERS)
    ws_backup = get_worksheet(sh, WS_BACKUP, BACKUP_HEADERS)
    return sh, ws_dados, ws_backup

def worksheet_to_df(ws, expected_headers: list[str]) -> pd.DataFrame:
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame(columns=[h.lower() for h in expected_headers] + ["_row"])

    headers = [str(h).strip().lower() for h in values[0]]
    rows = values[1:]

    if not rows:
        return pd.DataFrame(columns=headers + ["_row"])

    df = pd.DataFrame(rows, columns=headers)
    df["_row"] = range(2, len(rows) + 2)
    return df

def get_dados_df():
    _, ws_dados, _ = get_spreadsheet_and_tabs()
    df = worksheet_to_df(ws_dados, DADOS_HEADERS)
    return normalize_columns(df)

def get_backup_ws():
    _, _, ws_backup = get_spreadsheet_and_tabs()
    return ws_backup

def next_group_id(df_dados: pd.DataFrame) -> int:
    if df_dados.empty or "id_registro" not in df_dados.columns:
        return 1
    vals = pd.to_numeric(df_dados["id_registro"], errors="coerce").dropna()
    if vals.empty:
        return 1
    return int(vals.max()) + 1

def combo_filter(df: pd.DataFrame, tipo: str, ano: int, mes: str, setor: str):
    if df.empty:
        return df
    out = df.copy()
    for col in ["tipo", "ano", "mes", "setor", "status"]:
        if col not in out.columns:
            out[col] = ""
    return out[
        (out["tipo"].astype(str) == str(tipo)) &
        (out["ano"].astype(str) == str(ano)) &
        (out["mes"].astype(str) == str(mes)) &
        (out["setor"].astype(str) == str(setor)) &
        (out["status"].astype(str).str.upper() != "EXCLUIDO")
    ].copy()

def mark_rows_excluido(ws_dados, rows_df: pd.DataFrame):
    if rows_df.empty:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = []
    for _, r in rows_df.iterrows():
        row_num = int(r["_row"])
        updates.append({
            "range": f"N{row_num}:O{row_num}",
            "values": [["EXCLUIDO", now]]
        })
    if updates:
        ws_dados.batch_update(updates)

def append_backup_rows(ws_backup, acao: str, rows: list[list]):
    if not rows:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = []
    for row in rows:
        payload.append([acao, now] + row)
    ws_backup.append_rows(payload, value_input_option="USER_ENTERED")

def upsert_registro(tipo, ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por, respostas_dict):
    _, ws_dados, ws_backup = get_spreadsheet_and_tabs()
    df_dados = get_dados_df()

    existentes = combo_filter(df_dados, tipo, ano, mes, setor)
    if not existentes.empty:
        mark_rows_excluido(ws_dados, existentes)

    novo_id = next_group_id(df_dados)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mes_ano = f"{ano}-{mes}"

    rows_to_append = []
    backup_rows = []

    for item_key, payload in respostas_dict.items():
        if " :: " in item_key:
            subgrupo, item = item_key.split(" :: ", 1)
        else:
            subgrupo, item = "(Sem subgrupo)", item_key

        resp = payload.get("resp")
        obs = payload.get("obs", "")

        row = [
            novo_id,
            tipo,
            subgrupo,
            item,
            resp,
            obs,
            ano,
            mes,
            mes_ano,
            setor,
            data_vistoria,
            responsavel_area,
            inspecionado_por,
            "ATIVO",
            agora,
        ]
        rows_to_append.append(row)

        backup_row = [
            novo_id,
            tipo,
            subgrupo,
            item,
            resp,
            obs,
            ano,
            mes,
            mes_ano,
            setor,
            data_vistoria,
            responsavel_area,
            inspecionado_por,
        ]
        backup_rows.append(backup_row)

    if rows_to_append:
        ws_dados.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        append_backup_rows(ws_backup, "UPSERT", backup_rows)

def delete_registro(tipo, ano, mes, setor):
    _, ws_dados, ws_backup = get_spreadsheet_and_tabs()
    df_dados = get_dados_df()
    existentes = combo_filter(df_dados, tipo, ano, mes, setor)

    if existentes.empty:
        return False

    mark_rows_excluido(ws_dados, existentes)

    backup_rows = []
    for _, r in existentes.iterrows():
        backup_rows.append([
            r.get("id_registro", ""),
            r.get("tipo", ""),
            r.get("subgrupo", ""),
            r.get("item", ""),
            r.get("resposta", ""),
            r.get("observacao", ""),
            r.get("ano", ""),
            r.get("mes", ""),
            r.get("mes_ano", ""),
            r.get("setor", ""),
            r.get("data_vistoria", ""),
            r.get("responsavel_area", ""),
            r.get("inspecionado_por", ""),
        ])
    append_backup_rows(ws_backup, "DELETE", backup_rows)
    return True

def load_df():
    df = get_dados_df()
    if df.empty:
        return pd.DataFrame()

    for col in DADOS_HEADERS:
        if col not in df.columns:
            df[col] = ""

    ativos = df[df["status"].astype(str).str.upper() != "EXCLUIDO"].copy()
    if ativos.empty:
        return pd.DataFrame()

    ativos["ano"] = pd.to_numeric(ativos["ano"], errors="coerce")
    ativos = ativos.dropna(subset=["ano"])
    ativos["ano"] = ativos["ano"].astype(int)

    ativos["mes"] = ativos["mes"].astype(str).str.zfill(2)
    ativos["mes_ano"] = ativos["ano"].astype(str) + "-" + ativos["mes"]

    group_cols = [
        "tipo", "ano", "mes", "setor", "data_vistoria",
        "responsavel_area", "inspecionado_por"
    ]

    rows = []
    grouped = ativos.groupby(group_cols, dropna=False)
    for keys, g in grouped:
        tipo, ano, mes, setor, data_vistoria, responsavel_area, inspecionado_por = keys

        respostas = {}
        for _, rr in g.iterrows():
            item_key = f"{rr['subgrupo']} :: {rr['item']}"
            respostas[item_key] = {
                "resp": rr["resposta"],
                "obs": rr.get("observacao", "")
            }

        def count_resp(target):
            n = 0
            for v in respostas.values():
                if isinstance(v, dict) and v.get("resp") == target:
                    n += 1
            return n

        sim = count_resp("Sim")
        nao = count_resp("Não")
        total_kpi = sim + nao

        rows.append({
            "tipo": tipo,
            "ano": int(ano),
            "mes": mes,
            "mes_ano": f"{ano}-{mes}",
            "setor": setor,
            "data_vistoria": data_vistoria,
            "responsavel_area": responsavel_area,
            "inspecionado_por": inspecionado_por,
            "respostas": respostas,
            "sim": sim,
            "nao": nao,
            "total_kpi": total_kpi,
        })

    return pd.DataFrame(rows)

def explode_respostas(dff: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in dff.iterrows():
        resp_dict = r["respostas"] if isinstance(r.get("respostas"), dict) else {}
        for item_key, v in resp_dict.items():
            if " :: " in item_key:
                subgrupo, item = item_key.split(" :: ", 1)
            else:
                subgrupo, item = "(Sem subgrupo)", item_key

            if isinstance(v, dict):
                resp = v.get("resp")
                obs = v.get("obs", "")
            else:
                resp = v
                obs = ""

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
                "resposta": resp,
                "observacao": obs
            })

    x = pd.DataFrame(rows)
    if x.empty:
        return x

    x["sim"] = (x["resposta"] == "Sim").astype(int)
    x["nao"] = (x["resposta"] == "Não").astype(int)
    x["na"] = (x["resposta"] == "Não aplicável").astype(int)
    return x

def export_flat_csv(dff: pd.DataFrame) -> bytes:
    x = explode_respostas(dff)
    if x.empty:
        return pd.DataFrame([]).to_csv(index=False).encode("utf-8-sig")

    cols = [
        "tipo", "subgrupo", "item", "resposta", "observacao",
        "ano", "mes", "mes_ano", "setor", "data_vistoria",
        "responsavel_area", "inspecionado_por"
    ]
    return x[cols].to_csv(index=False).encode("utf-8-sig")

# ========================
# SESSÃO / LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "perfil" not in st.session_state:
    st.session_state.perfil = "usuario"

if is_admin_url and not st.session_state.logado:
    st.session_state.logado = True
    st.session_state.perfil = "admin"
    st.rerun()

def show_logo(width=150):
    for name in ["logo.png", "Logo.png", "Logo Oficial.png", "LogoOficial.png"]:
        try:
            st.image(name, width=width)
            return
        except Exception:
            pass

def header_premium(subtitulo: str, is_admin: bool):
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
            st.session_state.perfil = "usuario"
            st.rerun()

    st.divider()

# ========================
# LOGIN SCREEN
# ========================
if not st.session_state.logado:
    header_premium("CIPA & Brigada • acesso restrito", is_admin=False)

    st.markdown("### Acesso")
    perfil = st.radio("Tipo de acesso", ["Usuário", "Admin"], horizontal=True)
    senha = st.text_input("Senha", type="password", key="login_senha")

    if st.button("Entrar", type="primary", key="login_btn"):
        if perfil == "Usuário" and senha == SENHA_USUARIO:
            st.session_state.logado = True
            st.session_state.perfil = "usuario"
            st.rerun()
        elif perfil == "Admin" and senha == CHAVE_ADMIN:
            st.session_state.logado = True
            st.session_state.perfil = "admin"
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

is_admin = (st.session_state.get("perfil") == "admin")

# ========================
# CABEÇALHO INTERNO
# ========================
header_premium("CIPA & Brigada", is_admin=is_admin)

# ========================
# MENU LATERAL
# ========================
st.sidebar.title("Menu")
st.sidebar.caption("Navegação do sistema")

opcoes = ["📝 Preencher", "📊 Dashboard"]
if is_admin:
    opcoes.append("🛠️ Admin")

pagina = st.sidebar.radio("Ir para", options=opcoes, key="nav_pagina")

st.sidebar.divider()
st.sidebar.caption("Admin (interno) via URL habilitado.")
st.sidebar.caption("Ex.: ?admin=1&key=*****")

# ========================
# PÁGINA: PREENCHER
# ========================
if pagina == "📝 Preencher":
    st.subheader("Preencher Checklist")

    with st.container():
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

    respostas = {}
    subgrupos = subgrupos_por_tipo(tipo)

    q_index = 0
    for sg in subgrupos:
        itens = CHECKLISTS[tipo][sg]
        st.markdown(f"### {sg}")

        for item in itens:
            item_key = f"{sg} :: {item}"

            colR, colO = st.columns([1.2, 2.8])

            with colR:
                resp = st.radio(
                    item,
                    ["Sim", "Não", "Não aplicável"],
                    horizontal=True,
                    index=None,
                    key=f"q_{tipo}_{ano}_{mes}_{setor}_{q_index}"
                )

            with colO:
                obs = st.text_input(
                    "Observação (opcional)",
                    value="",
                    key=f"obs_{tipo}_{ano}_{mes}_{setor}_{q_index}"
                )

            respostas[item_key] = {"resp": resp, "obs": obs.strip()}
            q_index += 1

        st.divider()

    if st.button("💾 Salvar/Atualizar", type="primary", key="pre_salvar"):
        if not responsavel_area.strip():
            st.error("Informe o Responsável da área.")
        elif not inspecionado_por.strip():
            st.error("Informe quem realizou a inspeção (Inspecionado por).")
        else:
            faltando = [k for k, v in respostas.items() if v.get("resp") is None]
            if faltando:
                st.error(f"⚠️ Existem {len(faltando)} respostas sem preenchimento. Responda todas as perguntas para salvar.")
            else:
                try:
                    upsert_registro(
                        tipo=tipo,
                        ano=ano,
                        mes=mes,
                        setor=setor,
                        data_vistoria=data_vistoria.isoformat(),
                        responsavel_area=responsavel_area.strip(),
                        inspecionado_por=inspecionado_por.strip(),
                        respostas_dict=respostas
                    )
                    st.success("✅ Registro salvo/atualizado!")
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha Google: {e}")

# ========================
# PÁGINA: DASHBOARD
# ========================
elif pagina == "📊 Dashboard":
    st.subheader("Dashboard")

    try:
        df = load_df()
    except Exception as e:
        st.error(f"Erro ao ler a planilha Google: {e}")
        st.stop()

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

        dff = base[(base["ano"].isin(f_ano)) & (base["mes"].isin(f_mes)) & (base["setor"].isin(f_setor))].copy()

        if dff.empty:
            st.warning("Sem dados para os filtros selecionados.")
        else:
            total_sim = int(dff["sim"].sum())
            total_nao = int(dff["nao"].sum())
            total_kpi = total_sim + total_nao
            pct = (total_sim / total_kpi * 100) if total_kpi > 0 else 0

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
            st.write("### Exportar (CSV) — inclui Não aplicável e Observação")
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
elif pagina == "🛠️ Admin":
    if not is_admin:
        st.error("Acesso negado.")
        st.stop()

    st.subheader("Admin (interno)")
    st.caption("Acesso via URL: ?admin=1&key=... (opcional)")

    try:
        df = load_df()
    except Exception as e:
        st.error(f"Erro ao ler a planilha Google: {e}")
        st.stop()

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
            preview = base[(base["ano"] == a_ano) & (base["mes"] == a_mes) & (base["setor"] == a_setor)].copy()

            if preview.empty:
                st.warning("Registro não encontrado.")
            else:
                r = preview.iloc[0]
                st.json({
                    "tipo": r["tipo"],
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
                    try:
                        ok = delete_registro(a_tipo, a_ano, a_mes, a_setor)
                        if ok:
                            st.success("✅ Registro excluído.")
                            st.rerun()
                        else:
                            st.warning("Nenhum registro ativo encontrado para excluir.")
                    except Exception as e:
                        st.error(f"Erro ao excluir na planilha Google: {e}")
