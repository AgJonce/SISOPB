import sqlite3
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
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
    if escolha == "Cadastro de Obras 🛎️":
        cadastro_de_obras()

    elif escolha == "Dashboard 📊":
        dashboard()

    elif escolha == "👨‍🔧 Cadastro de Funcionário":
        cadastrar_funcionario()

    elif escolha == "Contabilidade":
        opcao = st.sidebar.radio(
            "🧰 Contas - Módulos:",
            [
                "🧹 Contabilidade",
                "📦 Financeiro"
            ]
        )

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
def get_geolocator():
    return Nominatim(user_agent="SISOPB")
	
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

    # ==================================================
    if st.session_state.get("obra_salva", False):
        st.success("✅ Obra registrada com sucesso!")
        st.session_state["obra_salva"] = False

    if "cadastro_obra_id" not in st.session_state:
        st.session_state["cadastro_obra_id"] = 0

    cadastro_id = st.session_state["cadastro_obra_id"]

    # Mensagem após salvar
    if st.session_state.get("obra_salva"):
        st.success("✅ Obra cadastrada com sucesso!")
        st.session_state["obra_salva"] = False

    # ==================================================
    # INFORMAÇÕES DA OBRA
    # ==================================================

    st.subheader("📋 Informações da Obra")

    col1, col2 = st.columns(2)

    with col1:

        obra = st.text_input(
            "🏗️ Nome da Obra",
            placeholder="Ex: Construção da Escola XYZ",
            key=f"obra_{cadastro_id}"
        )

        contrato = st.text_input(
            "📜 Número do Contrato",
            placeholder="Ex: 1234-ABCD",
            key=f"contrato_{cadastro_id}"
        )

        recurso = st.selectbox(
            "💰 Recurso",
            [
                "Federal",
                "Estadual",
                "Terceiros",
                "Outros"
            ],
            key=f"recurso_{cadastro_id}"
        )

        valor_obra = st.number_input(
            "💵 Valor da Obra (R$)",
            min_value=0.0,
            format="%.2f",
            key=f"valor_{cadastro_id}"
        )

    with col2:

        responsavel = st.text_input(
            "👤 Responsável pela Obra",
            key=f"responsavel_{cadastro_id}"
        )

        tipo_responsabilidade = st.selectbox(
            "👷 Tipo de Responsabilidade",
            [
                "Engenheiro",
                "Arquiteto",
                "Técnico",
                "Outros"
            ],
            key=f"responsabilidade_{cadastro_id}"
        )

        art = st.text_input(
            "📜 ART",
            key=f"art_{cadastro_id}"
        )

        tipo_obra = st.selectbox(
            "🏢 Tipo de Obra",
            [
                "Construção",
                "Reforma",
                "Manutenção",
                "Outros"
            ],
            key=f"tipo_obra_{cadastro_id}"
        )

        prazo = st.number_input(
            "📅 Prazo de Entrega (em dias)",
            min_value=1,
            step=1,
            key=f"prazo_{cadastro_id}"
        )

        data_inicio = st.date_input(
            "📅 Data de Início",
            key=f"data_inicio_{cadastro_id}"
        )

        data_entrega = data_inicio + timedelta(days=prazo)

        st.info(
            f"📅 Previsão de entrega: "
            f"{data_entrega.strftime('%d/%m/%Y')}"
        )

    situacao = st.selectbox(
        "📊 Situação da Obra",
        [
            "Em andamento",
            "Concluída",
            "Paralisada",
            "Planejada"
        ],
        key=f"situacao_{cadastro_id}"
    )

    # ==================================================
    # ESTADO DA LOCALIZAÇÃO
    # ==================================================

    if "latitude_obra" not in st.session_state:
        st.session_state["latitude_obra"] = None

    if "longitude_obra" not in st.session_state:
        st.session_state["longitude_obra"] = None

    if "endereco_obra" not in st.session_state:
        st.session_state["endereco_obra"] = None

    if "dados_endereco_obra" not in st.session_state:
        st.session_state["dados_endereco_obra"] = {}

    # ==================================================
    # MAPA
    # ==================================================

    st.subheader("📍 Local da Obra")

    st.info(
        "🖱️ Clique no mapa exatamente no local da obra."
    )

    mapa = folium.Map(
        location=[-20.7336, -42.0306],
        zoom_start=15
    )

    # Marcador do local selecionado
    if (
        st.session_state["latitude_obra"] is not None
        and st.session_state["longitude_obra"] is not None
    ):

        folium.Marker(
            [
                st.session_state["latitude_obra"],
                st.session_state["longitude_obra"]
            ],
            popup="Local da Obra",
            tooltip="Local selecionado"
        ).add_to(mapa)

    map_data = st_folium(
        mapa,
        width=800,
        height=500,
        key=f"mapa_{cadastro_id}"
    )

    # ==================================================
    # LOCAL CLICADO
    # ==================================================

    if map_data and map_data.get("last_clicked"):

        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]

        # Só consulta novamente se mudou o ponto
        if (
            latitude != st.session_state["latitude_obra"]
            or longitude != st.session_state["longitude_obra"]
        ):

            st.session_state["latitude_obra"] = latitude
            st.session_state["longitude_obra"] = longitude

            try:

                geolocator = get_geolocator()

                location = geolocator.reverse(
                    (latitude, longitude),
                    language="pt",
                    timeout=10,
                    exactly_one=True
                )

                if location:

                    dados_endereco = location.raw.get(
                        "address",
                        {}
                    )

                    rua = dados_endereco.get(
                        "road",
                        "Não informado"
                    )

                    numero = dados_endereco.get(
                        "house_number",
                        "Não informado"
                    )

                    bairro = dados_endereco.get(
                        "suburb",
                        dados_endereco.get(
                            "neighbourhood",
                            "Não informado"
                        )
                    )

                    cidade = dados_endereco.get(
                        "city",
                        dados_endereco.get(
                            "town",
                            dados_endereco.get(
                                "municipality",
                                "Não informado"
                            )
                        )
                    )

                    estado = dados_endereco.get(
                        "state",
                        "Não informado"
                    )

                    pais = dados_endereco.get(
                        "country",
                        "Brasil"
                    )

                    st.session_state["endereco_obra"] = (
                        location.address
                    )

                    st.session_state["dados_endereco_obra"] = {
                        "rua": rua,
                        "numero": numero,
                        "bairro": bairro,
                        "cidade": cidade,
                        "estado": estado,
                        "pais": pais
                    }

            except Exception as e:

                st.warning(
                    f"⚠️ Não foi possível localizar "
                    f"o endereço: {e}"
                )

    # ==================================================
    # MOSTRAR LOCALIZAÇÃO
    # ==================================================

    latitude = st.session_state["latitude_obra"]
    longitude = st.session_state["longitude_obra"]
    endereco = st.session_state["endereco_obra"]
    dados = st.session_state["dados_endereco_obra"]

    if latitude is not None and longitude is not None:

        st.success("✅ Local selecionado")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                "🛣️ **Rua:**",
                dados.get("rua", "Não informado")
            )

            st.write(
                "🔢 **Número:**",
                dados.get("numero", "Não informado")
            )

        with col2:

            st.write(
                "🏘️ **Bairro:**",
                dados.get("bairro", "Não informado")
            )

            st.write(
                "🏙️ **Cidade:**",
                dados.get("cidade", "Não informado")
            )

        with col3:

            st.write(
                "🗺️ **Estado:**",
                dados.get("estado", "Não informado")
            )

            st.write(
                "🌎 **País:**",
                dados.get("pais", "Brasil")
            )

        st.info(
            f"📌 Coordenadas: "
            f"{latitude:.6f}, {longitude:.6f}"
        )

        st.info(
            f"🏠 Endereço: {endereco}"
        )

    # ==================================================
    # SALVAR
    # ==================================================

    if st.button(
        "💾 Salvar Obra",
        type="primary",
        key=f"salvar_{cadastro_id}"
    ):

        if not obra:
            st.warning("⚠️ Informe o nome da obra.")

        elif not contrato:
            st.warning("⚠️ Informe o número do contrato.")

        elif latitude is None or longitude is None:
            st.warning("⚠️ Selecione o local da obra no mapa.")

        else:
            try:
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

                # Limpa a localização
                st.session_state["latitude_obra"] = None
                st.session_state["longitude_obra"] = None
                st.session_state["endereco_obra"] = None
                st.session_state["dados_endereco_obra"] = {}

                # Troca o ID dos campos para eles nascerem vazios
                st.session_state["cadastro_obra_id"] += 1

                # Guarda confirmação
                st.session_state["obra_salva"] = True

                # Recarrega a tela
                st.rerun()

            except Exception as e:
                st.error(
                    f"❌ Erro ao cadastrar obra: {e}"
                )

		
if __name__ == "__main__":
    main()
