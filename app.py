import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime

# ========================
# CONFIGURAÇÕES
# ========================
SENHA = "1234"

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

PERGUNTAS = [
"Pisos seguros",
"Iluminação adequada",
"Sinalização correta",
"Uso de EPI",
"Organização e limpeza"
]

DB = "banco.db"

# ========================
# BANCO
# ========================
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS vistoria (
data TEXT,
ano INTEGER,
mes TEXT,
setor TEXT,
responsavel TEXT,
respostas TEXT
)
""")
conn.commit()

# ========================
# LOGIN
# ========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔒 Acesso ao Sistema")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == SENHA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# ========================
# APP
# ========================
st.title("📋 Sistema de Vistoria")

aba1, aba2 = st.tabs(["Preencher", "Dashboard"])

# ========================
# FORMULÁRIO
# ========================
with aba1:
    st.subheader("Nova Vistoria")

    ano = st.number_input("Ano", value=datetime.now().year)
    mes = st.selectbox("Mês", ["01","02","03","04","05","06","07","08","09","10","11","12"])
    setor = st.selectbox("Setor", SETORES)
    responsavel = st.text_input("Responsável")

    respostas = {}
    for p in PERGUNTAS:
        respostas[p] = st.radio(p, ["Sim", "Não"], horizontal=True)

    if st.button("Salvar"):
        c.execute("INSERT INTO vistoria VALUES (?,?,?,?,?,?)", (
            datetime.now().isoformat(),
            ano,
            mes,
            setor,
            responsavel,
            json.dumps(respostas)
        ))
        conn.commit()
        st.success("Salvo com sucesso!")

# ========================
# DASHBOARD
# ========================
with aba2:
    st.subheader("Indicadores")

    df = pd.read_sql("SELECT * FROM vistoria", conn)

    if df.empty:
        st.info("Sem dados ainda.")
    else:
        df["respostas"] = df["respostas"].apply(json.loads)

        total = 0
        nao = 0

        for r in df["respostas"]:
            for v in r.values():
                total += 1
                if v == "Não":
                    nao += 1

        st.metric("Total de inspeções", len(df))
        st.metric("Não conformidades", nao)

