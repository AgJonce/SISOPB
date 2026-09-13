import sqlite3
import streamlit as st
import pandas as pd
import folium
from datetime import datetime, timedelta
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
conn = sqlite3.connect("obras.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
        senha TEXT,
        funcao TEXT
    );
''')
cursor.execute("""
    INSERT OR IGNORE INTO usuarios (nome, usuario, senha, funcao)
    VALUES (?, ?, ?, ?)
""", (
    "Administrador",
    "admin",
    "123",
    "Administrador"
))

cursor.execute('''
    CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra TEXT NOT NULL,
        contrato TEXT,
        data_inicio TEXT,
        data_entrega TEXT,
        recurso TEXT,
        art TEXT,
        tipo_responsabilidade TEXT,
        latitude REAL,
        longitude REAL,
        endereco TEXT,
        responsavel TEXT,
        tipo_obra TEXT,
        valor_obra REAL,
        situacao TEXT,
        prazo_dias INTEGER,
        data_cadastro TEXT
    )
''')

conn.commit()

def main ():
    st.set_page_config(page_title="Sistemas de Obras Públicas ", page_icon="🏗️", layout="wide")
    st.title("🏗️SISOPB")
    st.markdown("---")

    if "usuario_logado" not in st.session_state:
        st.warning("Faça login para acessar o sistema.")
        login()
        return

    funcao = st.session_state.get("funcao_usuario", "")
    st.sidebar.success(f"👤 Usuário: {st.session_state['usuario_logado']}")
    st.sidebar.info(f"🔐 Função: {funcao}")

    # Menus por função
    # Menus por função
    if funcao == "Administrador":
        menu = [
            "Cadastro de Obras 🛎️",
            "Situação da Obra",
            "Dashboard 📊",
            "👨‍🔧 Cadastro de Funcionário",
            "Financeiro 💰",
            "Contabilidade",
            "Medições",
            "➕ Cadastrar Usuário"
        ]

    elif funcao == "Engenheiro":
        menu = [
            "Cadastro de Obras 🛎️",
            "Situação da Obra",
            "Financeiro 💰",
            "Medições",
            "Contabilidade"
        ]

    elif funcao == "Financeiro":
        menu = [
            "Financeiro 💰"
        ]

    elif funcao == "Contador":
        menu = [
            "Contabilidade"
        ]

    else:
        st.error("❌ Função não reconhecida. Contate o administrador.")
        return

    escolha = st.sidebar.selectbox("📋 Menu", menu + ["🔓 Logout"])

    # Mapeamento de funcionalidades
    if escolha == "Dashboard 📊":
        dashboard()
    elif escolha == "👨‍🔧 Cadastro de Funcionário":
        cadastrar_funcionario()
    elif escolha == "Contabilidade":
        opcao = st.sidebar.radio("🧰 Contas - Módulos:", [
            "🧹 Contabilidade",
            "📦 Financeiro",
        ])
        if opcao == "🧹 Contabilidade":
            modulo_contabil()
        elif opcao == "📦 Financeiro":
            modulo_financeiro()
    elif escolha == "➕ Cadastrar Usuário":
        cadastrar_usuario()
		
def login():
    st.subheader("🔐 Login no Sistema")

    with st.form("form_login"):
        usuario = st.text_input("👤 Usuário")
        senha = st.text_input("🔑 Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        if usuario and senha:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
            resultado = cursor.fetchone()
            if resultado:
                st.session_state["usuario_logado"] = usuario
                st.session_state["funcao_usuario"] = resultado[4]  # índice 4 = função
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("🚫 Usuário ou senha inválidos.")
        else:
            st.warning("⚠️ Preencha todos os campos.")
def exibir_mapa():
    # Localização inicial de Carangola
    carangola_location = [-20.7029, -42.0105]

    # Criação do mapa
    mapa = folium.Map(
        location=carangola_location,
        zoom_start=15
    )

    # Exibir mapa no Streamlit
    mapa_interativo = st_folium(
        mapa,
        width=725,
        height=500
    )

    return mapa_interativo


def obter_nome_rua_com_numero(lat, lon):
    geolocator = Nominatim(
        user_agent="sisopb"
    )

    location = geolocator.reverse(
        (lat, lon),
        language="pt",
        timeout=10,
        exactly_one=True
    )

    if location:
        componentes_endereco = location.raw.get(
            "address",
            {}
        )

        numero = componentes_endereco.get(
            "house_number",
            "Número não disponível"
        )

        rua = componentes_endereco.get(
            "road",
            "Rua não disponível"
        )

        endereco = location.address

        return rua, numero, endereco

    return (
        "Rua não encontrada",
        "Número não encontrado",
        "Endereço não encontrado"
    )

def cadastrar_usuario():
    st.subheader("➕ Cadastrar Novo Usuário")

    with st.form("form_cadastro_usuario", clear_on_submit=True):

        nome = st.text_input("Nome Completo")

        usuario = st.text_input("Nome de Usuário")

        senha = st.text_input(
            "Senha",
            type="password"
        )

        funcao = st.selectbox(
            "Função",
            [
                "Administrador",
                "Contador",
                "Engenheiro",
                "Financeiro"
            ],
            key="cad_funcao"
        )

        cadastrar = st.form_submit_button("Cadastrar")

    if cadastrar:
        if nome and usuario and senha and funcao:

            try:
                cursor.execute("""
                    INSERT INTO usuarios (nome, usuario, senha, funcao)
                    VALUES (?, ?, ?, ?)
                """, (
                    nome,
                    usuario,
                    senha,
                    funcao
                ))

                conn.commit()

                st.success("✅ Usuário cadastrado com sucesso.")

            except sqlite3.IntegrityError:
                st.error("🚫 Nome de usuário já existe.")

        else:
            st.warning("⚠️ Preencha todos os campos.")
def cadastro_de_obras():
    st.title("🏗️ Cadastro de Nova Obra")

    with st.form("form_cadastro_obra", clear_on_submit=True):

        st.subheader("📋 Informações da Obra")

        col1, col2 = st.columns(2)

        with col1:
            obra = st.text_input(
                "🏗️ Nome da Obra",
                placeholder="Ex: Construção da Escola XYZ"
            )

            contrato = st.text_input(
                "📜 Número do Contrato",
                placeholder="Ex: 1234-ABCD"
            )

            recurso = st.selectbox(
                "💰 Recurso",
                ["Federal", "Estadual", "Terceiros", "Outros"]
            )

            valor_obra = st.number_input(
                "💵 Valor da Obra (R$)",
                min_value=0.0,
                format="%.2f"
            )

        with col2:
            responsavel = st.text_input(
                "👤 Responsável pela Obra"
            )

            tipo_responsabilidade = st.selectbox(
                "👷 Tipo de Responsabilidade",
                ["Engenheiro", "Arquiteto", "Técnico", "Outros"]
            )

            art = st.text_input("📜 ART")

            tipo_obra = st.selectbox(
                "🏢 Tipo de Obra",
                ["Construção", "Reforma", "Manutenção", "Outros"]
            )

            prazo = st.number_input(
                "📅 Prazo de Entrega (em dias)",
                min_value=1,
                step=1
            )

            data_inicio = st.date_input("📅 Data de Início")

            data_entrega = data_inicio + timedelta(days=prazo)

        situacao = st.selectbox(
            "📊 Situação da Obra",
            ["Em andamento", "Concluída", "Paralisada", "Planejada"]
        )

        st.subheader("📍 Local da Obra")

        mapa = folium.Map(
            location=[-20.7336, -42.0306],
            zoom_start=15
        )

        map_data = st_folium(
            mapa,
            width=800,
            height=500
        )

        latitude = None
        longitude = None
        endereco = "Não selecionado"

        if map_data and map_data.get("last_clicked"):

            latitude = map_data["last_clicked"]["lat"]
            longitude = map_data["last_clicked"]["lng"]

            try:
                geolocator = get_geolocator()

                location = geolocator.reverse(
                    (latitude, longitude),
                    language="pt",
                    timeout=10,
                    exactly_one=True
                )

                if location:
                    endereco = location.address

            except Exception:
                endereco = "Endereço não localizado"

            st.info(
                f"**Coordenadas:** "
                f"{latitude:.6f}, {longitude:.6f}"
            )

            st.info(f"**Endereço:** {endereco}")

        salvar = st.form_submit_button("💾 Salvar Obra")

    # ==========================
    # SALVAR
    # ==========================

    if salvar:

        if not obra:
            st.warning("⚠️ Informe o nome da obra.")

        elif not contrato:
            st.warning("⚠️ Informe o número do contrato.")

        elif latitude is None or longitude is None:
            st.warning(
                "⚠️ Clique no mapa para selecionar "
                "a localização da obra."
            )

        else:

            cursor.execute("""
                INSERT INTO obras (
                    obra,
                    contrato,
                    data_inicio,
                    data_entrega,
                    recurso,
                    art,
                    tipo_responsabilidade,
                    latitude,
                    longitude,
                    endereco,
                    responsavel,
                    tipo_obra,
                    valor_obra,
                    situacao,
                    prazo_dias,
                    data_cadastro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                obra,
                contrato,
                data_inicio.strftime("%Y-%m-%d"),
                data_entrega.strftime("%Y-%m-%d"),
                recurso,
                art,
                tipo_responsabilidade,
                latitude,
                longitude,
                endereco,
                responsavel,
                tipo_obra,
                valor_obra,
                situacao,
                prazo,
                datetime.now().strftime("%Y-%m-%d")
            ))

            conn.commit()

            st.success("✅ Obra cadastrada com sucesso!")
if __name__ == "__main__":
    main()
