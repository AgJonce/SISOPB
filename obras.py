import sqlite3
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode
)
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
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

    st.title("🏗️ Gestão de Obras Públicas")

    if "tela_obras" not in st.session_state:
        st.session_state["tela_obras"] = "Incluir"

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "➕ Incluir",
            use_container_width=True
        ):
            st.session_state["tela_obras"] = "Incluir"
            st.rerun()

    with col2:
        if st.button(
            "🔎 Localizar",
            use_container_width=True
        ):
            st.session_state["tela_obras"] = "Localizar"
            st.rerun()

    with col3:
        if st.button(
            "🖨️ Imprimir",
            use_container_width=True
        ):
            st.session_state["tela_obras"] = "Imprimir"
            st.rerun()

    st.markdown("---")

    tela = st.session_state["tela_obras"]

    if tela == "Incluir":
        incluir_obra()

    elif tela == "Localizar":
        localizar_obra()

    elif tela == "Imprimir":
        imprimir_obra()

def incluir_obra():
    # ==================================================
    if st.session_state.get(
        "obra_alterada_sucesso",
        False
    ):
        st.success("✅ Obra alterada com sucesso!")

        st.session_state[
            "obra_alterada_sucesso"
        ] = False

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

def alterar_obra():

    st.subheader("✏️ Alterar Obra")

    # ==========================================
    # VERIFICAR OBRA SELECIONADA
    # ==========================================

    id_obra = st.session_state.get(
        "obra_edicao_id"
    )

    if not id_obra:

        st.warning(
            "⚠️ Nenhuma obra foi selecionada."
        )

        st.info(
            "🔎 Vá em Localizar, encontre a obra "
            "e clique em Alterar Obra Selecionada."
        )

        if st.button(
            "🔎 Ir para Localizar"
        ):

            st.session_state[
                "tela_obras"
            ] = "Localizar"

            st.rerun()

        return

    # ==========================================
    # BUSCAR OBRA
    # ==========================================

    cursor.execute("""
        SELECT
            id,
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
        FROM obras
        WHERE id = ?
    """, (
        id_obra,
    ))

    dados = cursor.fetchone()

    if not dados:

        st.error(
            "❌ Obra não encontrada."
        )

        return

    # ==========================================
    # DADOS
    # ==========================================

    nome_atual = dados[1]
    contrato_atual = dados[2]
    data_inicio_atual = dados[3]
    recurso_atual = dados[5]
    art_atual = dados[6]
    responsabilidade_atual = dados[7]
    endereco_atual = dados[10]
    responsavel_atual = dados[11]
    tipo_atual = dados[12]
    valor_atual = dados[13]
    situacao_atual = dados[14]
    prazo_atual = dados[15]

    st.info(
        f"Editando obra #{id_obra} - {nome_atual}"
    )

    # ==========================================
    # CONVERTER DATA
    # ==========================================

    try:

        data_convertida = datetime.strptime(
            data_inicio_atual,
            "%Y-%m-%d"
        ).date()

    except Exception:

        data_convertida = datetime.now().date()

    # ==========================================
    # CAMPOS
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:

        nome = st.text_input(
            "🏗️ Nome da Obra",
            value=nome_atual,
            key=f"editar_nome_{id_obra}"
        )

        contrato = st.text_input(
            "📜 Contrato",
            value=contrato_atual or "",
            key=f"editar_contrato_{id_obra}"
        )

        recursos = [
            "Federal",
            "Estadual",
            "Terceiros",
            "Outros"
        ]

        indice_recurso = (
            recursos.index(recurso_atual)
            if recurso_atual in recursos
            else 0
        )

        recurso = st.selectbox(
            "💰 Recurso",
            recursos,
            index=indice_recurso,
            key=f"editar_recurso_{id_obra}"
        )

        valor = st.number_input(
            "💵 Valor da Obra",
            min_value=0.0,
            value=float(valor_atual or 0),
            format="%.2f",
            key=f"editar_valor_{id_obra}"
        )

        responsavel = st.text_input(
            "👤 Responsável",
            value=responsavel_atual or "",
            key=f"editar_responsavel_{id_obra}"
        )

    with col2:

        responsabilidades = [
            "Engenheiro",
            "Arquiteto",
            "Técnico",
            "Outros"
        ]

        indice_responsabilidade = (
            responsabilidades.index(
                responsabilidade_atual
            )
            if responsabilidade_atual
            in responsabilidades
            else 0
        )

        tipo_responsabilidade = st.selectbox(
            "👷 Tipo de Responsabilidade",
            responsabilidades,
            index=indice_responsabilidade,
            key=f"editar_resp_tipo_{id_obra}"
        )

        art = st.text_input(
            "📜 ART",
            value=art_atual or "",
            key=f"editar_art_{id_obra}"
        )

        tipos = [
            "Construção",
            "Reforma",
            "Manutenção",
            "Outros"
        ]

        indice_tipo = (
            tipos.index(tipo_atual)
            if tipo_atual in tipos
            else 0
        )

        tipo_obra = st.selectbox(
            "🏢 Tipo da Obra",
            tipos,
            index=indice_tipo,
            key=f"editar_tipo_{id_obra}"
        )

        prazo = st.number_input(
            "📅 Prazo em dias",
            min_value=1,
            value=int(prazo_atual or 1),
            step=1,
            key=f"editar_prazo_{id_obra}"
        )

        data_inicio = st.date_input(
            "📅 Data de Início",
            value=data_convertida,
            key=f"editar_data_{id_obra}"
        )

        situacoes = [
            "Em andamento",
            "Concluída",
            "Paralisada",
            "Planejada"
        ]

        indice_situacao = (
            situacoes.index(situacao_atual)
            if situacao_atual in situacoes
            else 0
        )

        situacao = st.selectbox(
            "📊 Situação",
            situacoes,
            index=indice_situacao,
            key=f"editar_situacao_{id_obra}"
        )

    # Calcula nova entrega
    data_entrega = (
        data_inicio
        + timedelta(days=prazo)
    )

    st.info(
        f"📅 Nova previsão de entrega: "
        f"{data_entrega.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"📍 **Local atual:** "
        f"{endereco_atual or 'Não informado'}"
    )

    # ==========================================
    # SALVAR ALTERAÇÕES
    # ==========================================

    if st.button(
        "💾 Salvar Alterações",
        type="primary"
    ):

        if not nome:

            st.warning(
                "⚠️ Informe o nome da obra."
            )

            return

        try:

            cursor.execute("""
                UPDATE obras

                SET
                    obra = ?,
                    contrato = ?,
                    data_inicio = ?,
                    data_entrega = ?,
                    recurso = ?,
                    art = ?,
                    tipo_responsabilidade = ?,
                    responsavel = ?,
                    tipo_obra = ?,
                    valor_obra = ?,
                    situacao = ?,
                    prazo_dias = ?

                WHERE id = ?
            """, (
                nome,
                contrato,
                data_inicio.strftime("%Y-%m-%d"),
                data_entrega.strftime("%Y-%m-%d"),
                recurso,
                art,
                tipo_responsabilidade,
                responsavel,
                tipo_obra,
                valor,
                situacao,
                prazo,
                id_obra
            ))

            conn.commit()

            # ==========================================
            # LIMPAR OBRA QUE ESTAVA SENDO ALTERADA
            # ==========================================

            if "obra_edicao_id" in st.session_state:
                del st.session_state["obra_edicao_id"]

            # ==========================================
            # LIMPAR LOCALIZAÇÃO
            # ==========================================

            st.session_state["latitude_obra"] = None
            st.session_state["longitude_obra"] = None
            st.session_state["endereco_obra"] = None
            st.session_state["dados_endereco_obra"] = {}

            # ==========================================
            # LIMPAR CAMPOS DA TELA INCLUIR
            # ==========================================

            if "cadastro_obra_id" not in st.session_state:
                st.session_state["cadastro_obra_id"] = 0

            st.session_state["cadastro_obra_id"] += 1

            # ==========================================
            # VOLTAR PARA TELA INCLUIR
            # ==========================================

            st.session_state["tela_obras"] = "Incluir"

            # Mensagem para aparecer depois do rerun
            st.session_state["obra_alterada_sucesso"] = True

            st.rerun()

        except Exception as e:

            st.error(
                f"❌ Erro ao alterar obra: {e}"
            )
def localizar_obra():

    st.subheader("🔎 Localizar Obras")

    # ==========================================
    # FILTROS
    # ==========================================

    col1, col2, col3 = st.columns(3)

    with col1:
        filtro_nome = st.text_input(
            "🏗️ Nome da Obra",
            key="filtro_nome_obra"
        )

    with col2:
        filtro_contrato = st.text_input(
            "📜 Contrato",
            key="filtro_contrato_obra"
        )

    with col3:
        filtro_situacao = st.selectbox(
            "📊 Situação",
            [
                "Todas",
                "Em andamento",
                "Concluída",
                "Paralisada",
                "Planejada"
            ],
            key="filtro_situacao_obra"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        filtro_responsavel = st.text_input(
            "👤 Responsável",
            key="filtro_responsavel_obra"
        )

    with col5:
        filtro_tipo = st.selectbox(
            "🏢 Tipo",
            [
                "Todos",
                "Construção",
                "Reforma",
                "Manutenção",
                "Outros"
            ],
            key="filtro_tipo_obra"
        )

    with col6:
        filtro_recurso = st.selectbox(
            "💰 Recurso",
            [
                "Todos",
                "Federal",
                "Estadual",
                "Terceiros",
                "Outros"
            ],
            key="filtro_recurso_obra"
        )

    # ==========================================
    # SQL
    # ==========================================

    query = """
        SELECT
            id,
            obra,
            contrato,
            responsavel,
            tipo_obra,
            recurso,
            valor_obra,
            situacao,
            data_inicio,
            data_entrega
        FROM obras
        WHERE 1 = 1
    """

    parametros = []

    if filtro_nome:
        query += " AND obra LIKE ?"
        parametros.append(f"%{filtro_nome}%")

    if filtro_contrato:
        query += " AND contrato LIKE ?"
        parametros.append(f"%{filtro_contrato}%")

    if filtro_responsavel:
        query += " AND responsavel LIKE ?"
        parametros.append(f"%{filtro_responsavel}%")

    if filtro_situacao != "Todas":
        query += " AND situacao = ?"
        parametros.append(filtro_situacao)

    if filtro_tipo != "Todos":
        query += " AND tipo_obra = ?"
        parametros.append(filtro_tipo)

    if filtro_recurso != "Todos":
        query += " AND recurso = ?"
        parametros.append(filtro_recurso)

    query += " ORDER BY obra"

    try:

        cursor.execute(
            query,
            parametros
        )

        resultados = cursor.fetchall()

    except Exception as e:

        st.error(
            f"❌ Erro ao localizar obras: {e}"
        )

        return

    # ==========================================
    # SEM RESULTADOS
    # ==========================================

    if not resultados:

        st.warning(
            "⚠️ Nenhuma obra encontrada."
        )

        return

    # ==========================================
    # DATAFRAME
    # ==========================================

    df = pd.DataFrame(
        resultados,
        columns=[
            "ID",
            "Obra",
            "Contrato",
            "Responsável",
            "Tipo",
            "Recurso",
            "Valor",
            "Situação",
            "Início",
            "Entrega"
        ]
    )

    st.caption(
        f"{len(df)} obra(s) encontrada(s). "
        "Dê dois cliques na obra desejada."
    )

    # ==========================================
    # CONFIGURAÇÃO DO AGGRID
    # ==========================================

    # ==========================================
    # CONFIGURAÇÃO DA TABELA
    # ==========================================

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False
    )

    grid_options = gb.build()

    # ==========================================
    # DUPLO CLIQUE
    # ==========================================

    duplo_clique = JsCode("""
        function(params) {

            // Remove seleção anterior
            params.api.deselectAll();

            // Seleciona a linha que recebeu duplo clique
            params.node.setSelected(true);
        }
    """)

    grid_options["onCellDoubleClicked"] = duplo_clique

    # ==========================================
    # EXIBIR TABELA
    # ==========================================

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=350,
        key="grid_localizar_obras"
    )

    # ==========================================
    # OBTER LINHA SELECIONADA
    # ==========================================

    selecionadas = grid_response.get("selected_rows")

    id_obra = None

    if selecionadas is not None:

        # Algumas versões retornam DataFrame
        if isinstance(selecionadas, pd.DataFrame):

            if not selecionadas.empty:

                id_obra = int(
                    selecionadas.iloc[0]["ID"]
                )

        # Outras versões retornam lista
        elif isinstance(selecionadas, list):

            if len(selecionadas) > 0:

                id_obra = int(
                    selecionadas[0]["ID"]
                )

    # Guarda a obra selecionada
    if id_obra is not None:

        st.session_state[
            "obra_selecionada_localizar"
        ] = id_obra
    # ==========================================
    # MOSTRAR OBRA SELECIONADA
    # ==========================================

    id_selecionado = st.session_state.get(
        "obra_selecionada_localizar"
    )

    # ==========================================
    # OBRA SELECIONADA
    # ==========================================

    id_selecionado = st.session_state.get(
        "obra_selecionada_localizar"
    )

    if id_selecionado:

        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                responsavel,
                tipo_obra,
                recurso,
                valor_obra,
                situacao,
                data_inicio,
                data_entrega,
                endereco
            FROM obras
            WHERE id = ?
        """, (
            id_selecionado,
        ))

        registro = cursor.fetchone()

        if registro:

            st.markdown("---")

            st.subheader(
                f"🏗️ {registro[1]}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Código:** {registro[0]}"
                )

                st.write(
                    f"**Contrato:** {registro[2]}"
                )

                st.write(
                    f"**Responsável:** "
                    f"{registro[3] or 'Não informado'}"
                )

            with col2:

                st.write(
                    f"**Tipo:** "
                    f"{registro[4] or 'Não informado'}"
                )

                st.write(
                    f"**Recurso:** "
                    f"{registro[5] or 'Não informado'}"
                )

                st.write(
                    f"**Situação:** "
                    f"{registro[7] or 'Não informado'}"
                )

            with col3:

                valor = registro[6] or 0

                st.write(
                    f"**Valor:** "
                    f"R$ {valor:,.2f}"
                )

                st.write(
                    f"**Início:** "
                    f"{registro[8] or 'Não informado'}"
                )

                st.write(
                    f"**Entrega:** "
                    f"{registro[9] or 'Não informado'}"
                )

            st.write(
                f"📍 **Local:** "
                f"{registro[10] or 'Não informado'}"
            )

            # ======================================
            # ALTERAR
            # ======================================

            if st.button(
                "✏️ Alterar esta Obra",
                type="primary",
                use_container_width=True,
                key="btn_alterar_obra_localizada"
            ):

                st.session_state[
                    "obra_edicao_id"
                ] = id_selecionado

                st.session_state[
                    "tela_obras"
                ] = "Alterar"

                st.rerun()
def gerar_pdf_obra(id_obra):

    cursor.execute("""
        SELECT
            id,
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
        FROM obras
        WHERE id = ?
    """, (id_obra,))

    dados = cursor.fetchone()

    if not dados:
        return None

    # ==========================================
    # DADOS
    # ==========================================

    (
        id_registro,
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
    ) = dados

    # ==========================================
    # PDF EM MEMÓRIA
    # ==========================================

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    elementos = []

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloSISOPB",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=15,
        alignment=1
    )

    subtitulo = ParagraphStyle(
        "SubtituloSISOPB",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=8
    )

    normal = styles["BodyText"]

    # ==========================================
    # CABEÇALHO
    # ==========================================

    elementos.append(
        Paragraph(
            "SISOPB - Sistema de Obras Públicas",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Ficha da Obra Nº {id_registro}</b>",
            styles["Heading2"]
        )
    )

    elementos.append(Spacer(1, 10))

    # ==========================================
    # FUNÇÃO PARA ÍCONE
    # ==========================================

    def carregar_icone(nome):

        caminho = f"assets/{nome}"

        if os.path.exists(caminho):
            return Image(
                caminho,
                width=0.6 * cm,
                height=0.6 * cm
            )

        return ""

    # ==========================================
    # INFORMAÇÕES PRINCIPAIS
    # ==========================================

    tabela_principal = [

        [
            carregar_icone("obra.png"),
            Paragraph(
                "<b>Nome da Obra</b>",
                normal
            ),
            obra or "Não informado"
        ],

        [
            carregar_icone("contrato.png"),
            Paragraph(
                "<b>Contrato</b>",
                normal
            ),
            contrato or "Não informado"
        ],

        [
            carregar_icone("responsavel.png"),
            Paragraph(
                "<b>Responsável</b>",
                normal
            ),
            responsavel or "Não informado"
        ],

        [
            carregar_icone("situacao.png"),
            Paragraph(
                "<b>Situação</b>",
                normal
            ),
            situacao or "Não informado"
        ],

        [
            carregar_icone("dinheiro.png"),
            Paragraph(
                "<b>Valor da Obra</b>",
                normal
            ),
            f"R$ {float(valor_obra or 0):,.2f}"
        ]
    ]

    tabela = Table(
        tabela_principal,
        colWidths=[
            1 * cm,
            4.5 * cm,
            11 * cm
        ]
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
        ])
    )

    elementos.append(tabela)

    elementos.append(Spacer(1, 15))

    # ==========================================
    # DADOS TÉCNICOS
    # ==========================================

    elementos.append(
        Paragraph(
            "Informações Técnicas",
            subtitulo
        )
    )

    dados_tecnicos = [

        ["Tipo da Obra", tipo_obra or "Não informado"],

        [
            "Tipo de Responsabilidade",
            tipo_responsabilidade or "Não informado"
        ],

        ["ART", art or "Não informado"],

        ["Recurso", recurso or "Não informado"],

        ["Prazo", f"{prazo_dias or 0} dias"],

        ["Data de Início", data_inicio or "Não informado"],

        ["Data de Entrega", data_entrega or "Não informado"],

        ["Data de Cadastro", data_cadastro or "Não informado"]
    ]

    tabela_tecnica = Table(
        dados_tecnicos,
        colWidths=[
            6 * cm,
            10.5 * cm
        ]
    )

    tabela_tecnica.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    elementos.append(tabela_tecnica)

    elementos.append(Spacer(1, 15))

    # ==========================================
    # LOCALIZAÇÃO
    # ==========================================

    elementos.append(
        Paragraph(
            "Localização da Obra",
            subtitulo
        )
    )

    localizacao = [

        [
            carregar_icone("localizacao.png"),
            Paragraph(
                "<b>Endereço</b>",
                normal
            ),
            endereco or "Não informado"
        ],

        [
            "",
            Paragraph(
                "<b>Latitude</b>",
                normal
            ),
            str(latitude or "Não informado")
        ],

        [
            "",
            Paragraph(
                "<b>Longitude</b>",
                normal
            ),
            str(longitude or "Não informado")
        ]
    ]

    tabela_localizacao = Table(
        localizacao,
        colWidths=[
            1 * cm,
            3.5 * cm,
            12 * cm
        ]
    )

    tabela_localizacao.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
        ])
    )

    elementos.append(tabela_localizacao)

    # ==========================================
    # RODAPÉ
    # ==========================================

    elementos.append(Spacer(1, 30))

    elementos.append(
        Paragraph(
            "Documento gerado pelo SISOPB - Sistema de Obras Públicas",
            styles["Italic"]
        )
    )

    # ==========================================
    # GERAR
    # ==========================================

    pdf.build(elementos)

    buffer.seek(0)

    return buffer 
def imprimir_obra():

    st.subheader("🖨️ Imprimir Obra")

    # ==========================================
    # BUSCAR OBRAS
    # ==========================================

    cursor.execute("""
        SELECT
            id,
            obra,
            contrato,
            situacao
        FROM obras
        ORDER BY obra
    """)

    obras = cursor.fetchall()

    if not obras:

        st.warning(
            "⚠️ Nenhuma obra cadastrada."
        )

        return

    # ==========================================
    # SELEÇÃO
    # ==========================================

    opcoes = {}

    for registro in obras:

        id_obra = registro[0]
        nome = registro[1]
        contrato = registro[2]
        situacao = registro[3]

        descricao = (
            f"{id_obra} - "
            f"{nome} | "
            f"Contrato: {contrato} | "
            f"{situacao}"
        )

        opcoes[descricao] = id_obra

    obra_escolhida = st.selectbox(
        "🏗️ Selecione a obra:",
        list(opcoes.keys())
    )

    id_obra = opcoes[
        obra_escolhida
    ]

    # ==========================================
    # MOSTRAR RESUMO
    # ==========================================

    cursor.execute("""
        SELECT
            obra,
            contrato,
            responsavel,
            valor_obra,
            situacao,
            endereco
        FROM obras
        WHERE id = ?
    """, (
        id_obra,
    ))

    dados = cursor.fetchone()

    if dados:

        st.markdown("---")

        st.subheader(
            f"🏗️ {dados[0]}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"📜 **Contrato:** "
                f"{dados[1]}"
            )

            st.write(
                f"👤 **Responsável:** "
                f"{dados[2]}"
            )

            st.write(
                f"📊 **Situação:** "
                f"{dados[4]}"
            )

        with col2:

            valor = float(
                dados[3] or 0
            )

            st.write(
                f"💰 **Valor:** "
                f"R$ {valor:,.2f}"
            )

            st.write(
                f"📍 **Local:** "
                f"{dados[5]}"
            )

    # ==========================================
    # GERAR PDF
    # ==========================================

    pdf = gerar_pdf_obra(
        id_obra
    )

    if pdf:

        nome_arquivo = (
            f"obra_{id_obra}.pdf"
        )

        st.download_button(
            label="🖨️ Gerar / Baixar PDF",
            data=pdf,
            file_name=nome_arquivo,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
if __name__ == "__main__":
    main()
