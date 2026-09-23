import os
import plotly.express as px
import plotly.graph_objects as go
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
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
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

# =========================================================
# TABELA DE OBRAS
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra TEXT NOT NULL,
        contrato TEXT,
        data_inicio TEXT,
        data_entrega TEXT,
        recurso TEXT,

        art TEXT,
        tipo_art TEXT,
        data_inicio_art TEXT,
        data_final_art TEXT,

        tipo_responsabilidade TEXT,
        tipo_vinculo TEXT,

        latitude REAL,
        longitude REAL,
        endereco TEXT,
        numero TEXT,
        bairro TEXT,

        responsavel TEXT,
        responsavel_id INTEGER,

        tipo_obra TEXT,
        valor_obra REAL,

        situacao TEXT,
        motivo_paralisacao TEXT,

        prazo_dias INTEGER,
        data_cadastro TEXT,

        FOREIGN KEY (responsavel_id)
            REFERENCES responsaveis(id)
    )
""")

conn.commit()


# =========================================================
# GARANTIR COLUNAS NOVAS EM BANCOS ANTIGOS
# =========================================================

cursor.execute("""
    PRAGMA table_info(obras)
""")

colunas_obras = [
    coluna[1]
    for coluna in cursor.fetchall()
]


# ---------------------------------------------------------
# NÚMERO
# ---------------------------------------------------------

if "numero" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN numero TEXT
    """)


# ---------------------------------------------------------
# BAIRRO
# ---------------------------------------------------------

if "bairro" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN bairro TEXT
    """)


# ---------------------------------------------------------
# RESPONSÁVEL ID
# ---------------------------------------------------------

if "responsavel_id" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN responsavel_id INTEGER
    """)


# ---------------------------------------------------------
# TIPO DE VÍNCULO
# ---------------------------------------------------------

if "tipo_vinculo" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN tipo_vinculo TEXT
    """)


# ---------------------------------------------------------
# TIPO DA ART
# ---------------------------------------------------------

if "tipo_art" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN tipo_art TEXT
    """)


# ---------------------------------------------------------
# DATA INICIAL DA ART
# ---------------------------------------------------------

if "data_inicio_art" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN data_inicio_art TEXT
    """)


# ---------------------------------------------------------
# DATA FINAL DA ART
# ---------------------------------------------------------

if "data_final_art" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN data_final_art TEXT
    """)


# ---------------------------------------------------------
# MOTIVO DA PARALISAÇÃO
# ---------------------------------------------------------

if "motivo_paralisacao" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN motivo_paralisacao TEXT
    """)


conn.commit()


# =========================================================
# TABELA DE RESPONSÁVEIS
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsaveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT NOT NULL,

        cpf TEXT UNIQUE NOT NULL,

        documento TEXT,

        tipo_responsabilidade TEXT NOT NULL,

        tipo_vinculo TEXT,

        conselho TEXT NOT NULL,

        numero_conselho TEXT,

        ativo INTEGER DEFAULT 1,

        data_cadastro TEXT
    )
""")

conn.commit()


# =========================================================
# GARANTIR COLUNAS NOVAS EM RESPONSÁVEIS ANTIGOS
# =========================================================

cursor.execute("""
    PRAGMA table_info(responsaveis)
""")

colunas_responsaveis = [
    coluna[1]
    for coluna in cursor.fetchall()
]


# ---------------------------------------------------------
# TIPO DE VÍNCULO
# ---------------------------------------------------------

if "tipo_vinculo" not in colunas_responsaveis:

    cursor.execute("""
        ALTER TABLE responsaveis
        ADD COLUMN tipo_vinculo TEXT
    """)


conn.commit()


# =========================================================
# TABELA DE ITENS
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        codigo TEXT UNIQUE NOT NULL,

        descricao TEXT NOT NULL,

        unidade TEXT NOT NULL,

        categoria TEXT,

        observacao TEXT,

        ativo INTEGER DEFAULT 1,

        data_cadastro TEXT
    )
""")

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_situacao_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        situacao TEXT NOT NULL,
        motivo_paralisacao TEXT,
        data_publicacao TEXT,
        orgao_publicacao TEXT,
        link_publicacao TEXT,
        data_registro TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id)
    )
""")

conn.commit()
# =========================================================
# ITENS DA OBRA
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        obra_id INTEGER NOT NULL,

        item_id INTEGER NOT NULL,

        quantidade REAL DEFAULT 0,

        valor_unitario REAL DEFAULT 0,

        valor_total REAL DEFAULT 0,

        observacao TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id),

        FOREIGN KEY (item_id)
            REFERENCES itens(id)
    )
""")

conn.commit()


# =========================================================
# MEDIÇÕES
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        obra_id INTEGER NOT NULL,

        valor REAL DEFAULT 0,

        tipo_medicao TEXT,

        data_medicao TEXT,

        data_inicio TEXT,

        data_final TEXT,

        percentual_obra REAL DEFAULT 0,

        foto_nome TEXT,

        foto_arquivo BLOB,

        boletim_nome TEXT,

        boletim_arquivo BLOB,

        nota_fiscal TEXT,

        data_nota TEXT,

        empenho TEXT,

        data_cadastro TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id)
    )
""")

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsaveis_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        responsavel_id INTEGER NOT NULL,
        tipo_responsabilidade TEXT,
        tipo_vinculo TEXT,
        numero_art TEXT,
        tipo_art TEXT,
        data_inicio_art TEXT,
        data_final_art TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id),

        FOREIGN KEY (responsavel_id)
            REFERENCES responsaveis(id)
    )
""")

conn.commit()
# =========================================================
# ITENS DA MEDIÇÃO
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_medicao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        medicao_id INTEGER NOT NULL,

        item_obra_id INTEGER NOT NULL,

        valor_medido REAL DEFAULT 0,

        FOREIGN KEY (medicao_id)
            REFERENCES medicoes(id),

        FOREIGN KEY (item_obra_id)
            REFERENCES itens_obra(id)
    )
""")

conn.commit()


# =========================================================
# FISCAIS DA MEDIÇÃO
# =========================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS fiscais_medicao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        medicao_id INTEGER NOT NULL,

        fiscal TEXT NOT NULL,

        FOREIGN KEY (medicao_id)
            REFERENCES medicoes(id)
    )
""")

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsaveis_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        responsavel_id INTEGER NOT NULL,
        tipo_responsabilidade TEXT,
        tipo_vinculo TEXT,
        numero_art TEXT,
        tipo_art TEXT,
        data_inicio_art TEXT,
        data_final_art TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id),

        FOREIGN KEY (responsavel_id)
            REFERENCES responsaveis(id)
    )
""")

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        obra_id INTEGER NOT NULL,

        numero_empenho TEXT NOT NULL,
        ano_empenho INTEGER NOT NULL,
        data_empenho TEXT NOT NULL,

        tipo_empenho TEXT NOT NULL,

        credor TEXT,
        cpf_cnpj TEXT,

        fonte_recurso TEXT,

        valor_empenhado REAL DEFAULT 0,
        valor_anulado REAL DEFAULT 0,
        valor_liquidado REAL DEFAULT 0,
        valor_pago REAL DEFAULT 0,

        observacao TEXT,

        data_cadastro TEXT,

        FOREIGN KEY (obra_id)
            REFERENCES obras(id)
    )
""")

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
            "👨‍🔧 Cadastro de Responsavel",
            "Financeiro 💰",
            "Contabilidade",
            "Medições",
            "➕ Cadastrar Usuário"
        ]

    elif funcao == "Engenheiro":
        menu = [
            "Cadastro de Obras 🛎️",
            "Situação da Obra",
			"👨‍🔧 Cadastro de Responsavel",
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

    elif escolha == "👨‍🔧 Cadastro de Responsavel":
        cadastrar_responsavel()

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

def medicoes():

    # ==================================================
    # TÍTULO
    # ==================================================

    st.title("📏 Medições")

    st.caption(
        "Gerencie as medições das obras."
    )

    st.divider()

    # ==================================================
    # CONTROLE DE TELA
    # ==================================================

    if "tela_medicao" not in st.session_state:
        st.session_state["tela_medicao"] = "Principal"

    tela = st.session_state["tela_medicao"]

    # ==================================================
    # TELA PRINCIPAL
    # ==================================================

    if tela == "Principal":

        # ==============================================
        # MENSAGENS DE SUCESSO
        # ==============================================

        if st.session_state.pop(
            "medicao_cadastrada_sucesso",
            False
        ):
            st.success(
                "✅ Medição cadastrada com sucesso!"
            )

        if st.session_state.pop(
            "medicao_alterada_sucesso",
            False
        ):
            st.success(
                "✅ Medição alterada com sucesso!"
            )

        if st.session_state.pop(
            "medicao_excluida_sucesso",
            False
        ):
            st.success(
                "✅ Medição excluída com sucesso!"
            )

        # ==============================================
        # OPÇÕES
        # ==============================================

        st.markdown(
            "### 🛠️ O que deseja fazer?"
        )

        col1, col2, col3, col4 = st.columns(4)

        # ==============================================
        # INCLUIR
        # ==============================================

        with col1:

            if st.button(
                "➕ Incluir",
                use_container_width=True,
                type="primary",
                key="btn_incluir_medicao"
            ):

                st.session_state[
                    "tela_medicao"
                ] = "Incluir"

                st.session_state.pop(
                    "medicao_edicao_id",
                    None
                )

                st.session_state.pop(
                    "medicao_excluir_id",
                    None
                )

                st.session_state.pop(
                    "medicao_imprimir_id",
                    None
                )

                st.rerun()

        # ==============================================
        # LOCALIZAR
        # ==============================================

        with col2:

            if st.button(
                "🔎 Localizar",
                use_container_width=True,
                key="btn_localizar_medicao"
            ):

                st.session_state[
                    "tela_medicao"
                ] = "Localizar"

                st.session_state.pop(
                    "medicao_edicao_id",
                    None
                )

                st.session_state.pop(
                    "medicao_excluir_id",
                    None
                )

                st.session_state.pop(
                    "medicao_imprimir_id",
                    None
                )

                st.rerun()

        # ==============================================
        # IMPRIMIR
        # ==============================================

        with col3:

            if st.button(
                "🖨️ Imprimir",
                use_container_width=True,
                key="btn_imprimir_medicao"
            ):

                st.session_state[
                    "tela_medicao"
                ] = "Imprimir"

                st.session_state.pop(
                    "medicao_edicao_id",
                    None
                )

                st.session_state.pop(
                    "medicao_excluir_id",
                    None
                )

                st.session_state.pop(
                    "medicao_imprimir_id",
                    None
                )

                st.rerun()

        # ==============================================
        # EXCLUIR
        # ==============================================

        with col4:

            if st.button(
                "🗑️ Excluir",
                use_container_width=True,
                key="btn_excluir_medicao"
            ):

                st.session_state[
                    "tela_medicao"
                ] = "Excluir"

                st.session_state.pop(
                    "medicao_edicao_id",
                    None
                )

                st.session_state.pop(
                    "medicao_excluir_id",
                    None
                )

                st.session_state.pop(
                    "medicao_imprimir_id",
                    None
                )

                st.rerun()

        st.info(
            "Selecione uma opção acima para continuar."
        )

    # ==================================================
    # INCLUIR
    # ==================================================

    elif tela == "Incluir":

        incluir_medicao()

    # ==================================================
    # LOCALIZAR
    # ==================================================

    elif tela == "Localizar":

        localizar_medicao()

    # ==================================================
    # ALTERAR
    # ==================================================

    elif tela == "Alterar":

        alterar_medicao()

    # ==================================================
    # IMPRIMIR
    # ==================================================

    elif tela == "Imprimir":

        imprimir_medicao()

    # ==================================================
    # EXCLUIR
    # ==================================================

    elif tela == "Excluir":

        excluir_medicao()

    # ==================================================
    # SEGURANÇA
    # ==================================================

    else:

        st.session_state[
            "tela_medicao"
        ] = "Principal"

        st.rerun()
def incluir_medicao():

    st.subheader("➕ Incluir Medição")

    # ==================================================
    # VOLTAR
    # ==================================================

    if st.button(
        "⬅️ Voltar",
        key="voltar_incluir_medicao"
    ):
        st.session_state["tela_medicao"] = "Principal"
        st.session_state.pop("fiscais_temp_medicao", None)
        st.session_state.pop("obra_anterior_medicao", None)
        st.rerun()

    st.divider()

    # ==================================================
    # BUSCAR OBRAS QUE POSSUEM ITENS
    # ==================================================

    cursor.execute("""
        SELECT DISTINCT
            o.id,
            o.obra,
            o.valor_obra
        FROM obras o

        INNER JOIN itens_obra io
            ON io.obra_id = o.id

         WHERE
          o.situacao IS NULL   
		  OR o.situacao != '7 – Concluído e recebido definitivamente'
		  
		ORDER BY o.obra
    """)

    obras_cadastradas = cursor.fetchall()

    if not obras_cadastradas:
        st.warning(
            "⚠️ Nenhuma obra com itens cadastrados foi encontrada."
        )
        return

    # ==================================================
    # MONTAR OPÇÕES DAS OBRAS
    # ==================================================

    opcoes_obras = {
        "Selecione a obra": {
            "id": None,
            "nome": "",
            "valor": 0.0
        }
    }

    for registro in obras_cadastradas:

        id_obra = registro[0]
        nome_obra = registro[1]
        valor_obra_registro = registro[2] or 0

        nome_opcao = f"{id_obra} - {nome_obra}"

        opcoes_obras[nome_opcao] = {
            "id": id_obra,
            "nome": nome_obra,
            "valor": float(valor_obra_registro)
        }

    obra_selecionada = st.selectbox(
        "🏗️ Obra",
        options=list(opcoes_obras.keys()),
        key="obra_incluir_medicao"
    )

    dados_obra = opcoes_obras[
        obra_selecionada
    ]

    obra_id = dados_obra["id"]
    valor_obra = dados_obra["valor"]

    # ==================================================
    # AGUARDAR SELEÇÃO DA OBRA
    # ==================================================

    if obra_id is None:

        st.info(
            "Selecione uma obra para continuar."
        )
        return

    # ==================================================
    # LIMPAR RESPONSÁVEL AO TROCAR DE OBRA
    # ==================================================

    obra_anterior = st.session_state.get(
        "obra_anterior_medicao"
    )

    if obra_anterior != obra_id:

        st.session_state[
            "obra_anterior_medicao"
        ] = obra_id

        st.session_state[
            "fiscais_temp_medicao"
        ] = []

    if "fiscais_temp_medicao" not in st.session_state:

        st.session_state[
            "fiscais_temp_medicao"
        ] = []

    # ==================================================
    # RESPONSÁVEIS VINCULADOS À OBRA
    # ==================================================

    st.markdown(
        "### 👷 Responsável pela Medição"
    )

    cursor.execute("""
        SELECT
            ro.id,
            r.id,
            r.nome,
            ro.tipo_responsabilidade,
            ro.tipo_vinculo,
            ro.numero_art,
            ro.tipo_art
        FROM responsaveis_obra ro

        INNER JOIN responsaveis r
            ON r.id = ro.responsavel_id

        WHERE ro.obra_id = ?

        ORDER BY r.nome
    """, (
        obra_id,
    ))

    responsaveis_obra = cursor.fetchall()

    # ==================================================
    # COMPATIBILIDADE COM OBRAS ANTIGAS
    # ==================================================

    if not responsaveis_obra:

        cursor.execute("""
            SELECT
                o.responsavel_id,
                r.nome,
                o.tipo_responsabilidade,
                o.tipo_vinculo,
                o.art,
                o.tipo_art
            FROM obras o

            INNER JOIN responsaveis r
                ON r.id = o.responsavel_id

            WHERE o.id = ?
        """, (
            obra_id,
        ))

        responsavel_antigo = cursor.fetchone()

        if responsavel_antigo:

            responsaveis_obra = [
                (
                    0,
                    responsavel_antigo[0],
                    responsavel_antigo[1],
                    responsavel_antigo[2],
                    responsavel_antigo[3],
                    responsavel_antigo[4],
                    responsavel_antigo[5]
                )
            ]

    # ==================================================
    # VERIFICAR RESPONSÁVEIS
    # ==================================================

    if not responsaveis_obra:

        st.warning(
            "⚠️ Esta obra não possui responsáveis vinculados."
        )
        return

    # ==================================================
    # MONTAR OPÇÕES
    # ==================================================

    opcoes_responsaveis = {
        "Selecione o responsável": None
    }

    dados_responsaveis = {}

    for registro in responsaveis_obra:

        vinculo_obra_id = registro[0]
        responsavel_id = registro[1]
        nome = registro[2] or ""

        tipo_responsabilidade = (
            registro[3] or ""
        )

        tipo_vinculo = (
            registro[4] or ""
        )

        numero_art = (
            registro[5] or ""
        )

        tipo_art = (
            registro[6] or ""
        )

        # Permite inclusive o mesmo profissional
        # possuir mais de uma ART na mesma obra.

        chave = (
            f"{nome} | "
            f"{tipo_responsabilidade} | "
            f"{tipo_art}"
        )

        opcoes_responsaveis[
            chave
        ] = vinculo_obra_id

        dados_responsaveis[
            vinculo_obra_id
        ] = {
            "vinculo_obra_id": vinculo_obra_id,
            "responsavel_id": responsavel_id,
            "nome": nome,
            "tipo_responsabilidade": (
                tipo_responsabilidade
            ),
            "tipo_vinculo": (
                tipo_vinculo
            ),
            "numero_art": (
                numero_art
            ),
            "tipo_art": (
                tipo_art
            )
        }

    # ==================================================
    # ESCOLHER RESPONSÁVEL PELA MEDIÇÃO
    # ==================================================

    responsavel_escolhido = st.selectbox(
        "👤 Selecione o responsável pela medição",
        options=list(
            opcoes_responsaveis.keys()
        ),
        key=f"responsavel_medicao_{obra_id}"
    )

    vinculo_escolhido = (
        opcoes_responsaveis[
            responsavel_escolhido
        ]
    )

    # ==================================================
    # MOSTRAR DADOS DO RESPONSÁVEL
    # ==================================================

    if vinculo_escolhido is not None:

        dados_responsavel = (
            dados_responsaveis[
                vinculo_escolhido
            ]
        )

        col1, col2 = st.columns(2)

        with col1:

            st.text_input(
                "👷 Tipo de Responsabilidade",
                value=dados_responsavel[
                    "tipo_responsabilidade"
                ],
                disabled=True,
                key=(
                    f"resp_tipo_medicao_"
                    f"{obra_id}_"
                    f"{vinculo_escolhido}"
                )
            )

            st.text_input(
                "🔗 Tipo de Vínculo",
                value=dados_responsavel[
                    "tipo_vinculo"
                ],
                disabled=True,
                key=(
                    f"resp_vinculo_medicao_"
                    f"{obra_id}_"
                    f"{vinculo_escolhido}"
                )
            )

        with col2:

            st.text_input(
                "📜 Número da ART",
                value=dados_responsavel[
                    "numero_art"
                ],
                disabled=True,
                key=(
                    f"resp_art_medicao_"
                    f"{obra_id}_"
                    f"{vinculo_escolhido}"
                )
            )

            st.text_input(
                "🏗️ Tipo da ART",
                value=dados_responsavel[
                    "tipo_art"
                ],
                disabled=True,
                key=(
                    f"resp_tipo_art_medicao_"
                    f"{obra_id}_"
                    f"{vinculo_escolhido}"
                )
            )

        # ==================================================
        # ADICIONAR RESPONSÁVEL À MEDIÇÃO
        # ==================================================

        if st.button(
            "➕ Adicionar Responsável",
            use_container_width=True,
            key=(
                f"adicionar_responsavel_medicao_"
                f"{obra_id}"
            )
        ):

            # A medição terá apenas o responsável
            # escolhido pelo usuário.

            st.session_state[
                "fiscais_temp_medicao"
            ] = [
                {
                    "responsavel_id": (
                        dados_responsavel[
                            "responsavel_id"
                        ]
                    ),
                    "nome": (
                        dados_responsavel[
                            "nome"
                        ]
                    ),
                    "tipo_responsabilidade": (
                        dados_responsavel[
                            "tipo_responsabilidade"
                        ]
                    ),
                    "tipo_vinculo": (
                        dados_responsavel[
                            "tipo_vinculo"
                        ]
                    ),
                    "numero_art": (
                        dados_responsavel[
                            "numero_art"
                        ]
                    ),
                    "tipo_art": (
                        dados_responsavel[
                            "tipo_art"
                        ]
                    )
                }
            ]

            st.rerun()

    # ==================================================
    # RESPONSÁVEL DEFINIDO PARA A MEDIÇÃO
    # ==================================================

    fiscais_temp = st.session_state[
        "fiscais_temp_medicao"
    ]

    if fiscais_temp:

        st.markdown(
            "#### ✅ Responsável definido para a medição"
        )

        dados_tabela = []

        for fiscal_temp in fiscais_temp:

            dados_tabela.append({
                "Responsável": (
                    fiscal_temp["nome"]
                ),
                "Responsabilidade": (
                    fiscal_temp[
                        "tipo_responsabilidade"
                    ]
                ),
                "Vínculo": (
                    fiscal_temp[
                        "tipo_vinculo"
                    ]
                ),
                "Número ART": (
                    fiscal_temp[
                        "numero_art"
                    ]
                ),
                "Tipo ART": (
                    fiscal_temp[
                        "tipo_art"
                    ]
                )
            })

        st.dataframe(
            pd.DataFrame(
                dados_tabela
            ),
            use_container_width=True,
            hide_index=True
        )

        if st.button(
            "🗑️ Remover Responsável",
            use_container_width=True,
            key=(
                f"remover_responsavel_medicao_"
                f"{obra_id}"
            )
        ):

            st.session_state[
                "fiscais_temp_medicao"
            ] = []

            st.rerun()

    else:

        st.info(
            "Selecione e adicione o responsável "
            "por esta medição."
        )

    # ==================================================
    # DADOS DA MEDIÇÃO
    # ==================================================

    st.divider()

    st.markdown(
        "### 📋 Dados da Medição"
    )

    col1, col2 = st.columns(2)

    with col1:

        tipo_medicao = st.selectbox(
            "📑 Tipo de Medição",
            [
                "Inicial",
                "Parcial",
                "Final"
            ],
            key=f"tipo_medicao_{obra_id}"
        )

        data_medicao = st.date_input(
            "📅 Data da Medição",
            key=f"data_medicao_{obra_id}"
        )

        data_inicio = st.date_input(
            "📅 Data de Início",
            key=f"inicio_medicao_{obra_id}"
        )

    with col2:

        data_final = st.date_input(
            "📅 Data Final",
            key=f"final_medicao_{obra_id}"
        )

        nota_fiscal = st.text_input(
            "🧾 Nota Fiscal",
            placeholder="Número da nota fiscal",
            key=f"nota_medicao_{obra_id}"
        )

        data_nota = st.date_input(
            "📅 Data da Nota Fiscal",
            key=f"data_nota_medicao_{obra_id}"
        )

        empenho = st.text_input(
            "💰 Empenho",
            placeholder="Número do empenho",
            key=f"empenho_medicao_{obra_id}"
        )

    # ==================================================
    # ITENS DA OBRA
    # ==================================================

    st.divider()

    st.markdown(
        "### 🧱 Itens da Medição"
    )

    cursor.execute("""
        SELECT
            io.id,
            i.codigo,
            i.descricao,
            i.unidade,
            io.quantidade,
            io.valor_unitario,
            io.valor_total,

            COALESCE(
                (
                    SELECT SUM(
                        im.valor_medido
                    )
                    FROM itens_medicao im
                    WHERE im.item_obra_id = io.id
                ),
                0
            ) AS valor_ja_medido

        FROM itens_obra io

        INNER JOIN itens i
            ON i.id = io.item_id

        WHERE io.obra_id = ?

        ORDER BY i.codigo
    """, (
        obra_id,
    ))

    itens = cursor.fetchall()

    if not itens:

        st.warning(
            "⚠️ Esta obra não possui itens cadastrados."
        )
        return

    itens_selecionados = []

    # ==================================================
    # MOSTRAR ITENS
    # ==================================================

    for item in itens:

        item_obra_id = item[0]
        codigo = item[1]
        descricao = item[2]
        unidade = item[3]

        quantidade = float(
            item[4] or 0
        )

        valor_unitario = float(
            item[5] or 0
        )

        valor_total_item = float(
            item[6] or 0
        )

        valor_ja_medido = float(
            item[7] or 0
        )

        saldo_item = (
            valor_total_item
            - valor_ja_medido
        )

        if saldo_item < 0:
            saldo_item = 0.0

        st.markdown(
            f"#### {codigo} - {descricao}"
        )

        col_item1, col_item2, col_item3 = (
            st.columns(3)
        )

        with col_item1:

            st.write(
                f"**Quantidade:** "
                f"{quantidade:,.2f} {unidade}"
            )

            st.write(
                f"**Valor Unitário:** "
                f"R$ {valor_unitario:,.2f}"
            )

        with col_item2:

            st.write(
                f"**Valor do Item:** "
                f"R$ {valor_total_item:,.2f}"
            )

            st.write(
                f"**Já Medido:** "
                f"R$ {valor_ja_medido:,.2f}"
            )

        with col_item3:

            st.write(
                f"**Saldo para Medição:** "
                f"R$ {saldo_item:,.2f}"
            )

        if saldo_item <= 0:

            st.success(
                "✅ Item totalmente medido."
            )

        else:

            selecionar = st.checkbox(
                "Selecionar para esta medição",
                key=(
                    f"selecionar_medicao_"
                    f"{obra_id}_"
                    f"{item_obra_id}"
                )
            )

            if selecionar:

                valor_medido = st.number_input(
                    "💵 Valor a medir neste item",
                    min_value=0.0,
                    max_value=float(
                        saldo_item
                    ),
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    key=(
                        f"valor_medicao_"
                        f"{obra_id}_"
                        f"{item_obra_id}"
                    )
                )

                if valor_medido > 0:

                    itens_selecionados.append({
                        "item_obra_id": (
                            item_obra_id
                        ),
                        "valor_medido": float(
                            valor_medido
                        )
                    })

        st.divider()

    # ==================================================
    # TOTAL DA MEDIÇÃO
    # ==================================================

    valor_total_medicao = sum(
        item["valor_medido"]
        for item in itens_selecionados
    )

    # ==================================================
    # PERCENTUAL DA OBRA
    # ==================================================

    if valor_obra > 0:

        percentual = (
            valor_total_medicao
            / valor_obra
        ) * 100

    else:

        percentual = 0.0

    # ==================================================
    # RESUMO FINANCEIRO
    # ==================================================

    st.markdown(
        "### 💰 Resumo da Medição"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Valor da Obra",
            f"R$ {valor_obra:,.2f}"
        )

    with col2:

        st.metric(
            "Valor da Medição",
            f"R$ {valor_total_medicao:,.2f}"
        )

    with col3:

        st.metric(
            "% da Obra",
            f"{percentual:.2f}%"
        )

    # ==================================================
    # DOCUMENTOS
    # ==================================================

    st.divider()

    st.markdown(
        "### 📎 Documentos"
    )

    col1, col2 = st.columns(2)

    with col1:

        foto = st.file_uploader(
            "📷 Foto da Medição",
            type=[
                "jpg",
                "jpeg",
                "png"
            ],
            key=f"foto_medicao_{obra_id}"
        )

    with col2:

        # SOMENTE EXCEL

        boletim = st.file_uploader(
            "📊 Boletim de Medição (Excel)",
            type=[
                "xlsx",
                "xls"
            ],
            key=f"boletim_medicao_{obra_id}"
        )

        st.caption(
            "Formatos permitidos: .xlsx e .xls"
        )

    # ==================================================
    # SALVAR MEDIÇÃO
    # ==================================================

    st.divider()

    if st.button(
        "💾 Salvar Medição",
        type="primary",
        use_container_width=True,
        key=f"salvar_medicao_{obra_id}"
    ):

        # ==================================================
        # VALIDAÇÕES
        # ==================================================

        if not st.session_state[
            "fiscais_temp_medicao"
        ]:

            st.warning(
                "⚠️ Defina o responsável "
                "pela medição."
            )
            return

        if not itens_selecionados:

            st.warning(
                "⚠️ Selecione pelo menos um item "
                "e informe o valor da medição."
            )
            return

        if valor_total_medicao <= 0:

            st.warning(
                "⚠️ O valor da medição deve ser "
                "maior que zero."
            )
            return

        if data_final < data_inicio:

            st.warning(
                "⚠️ A data final não pode ser "
                "anterior à data inicial."
            )
            return

        # ==================================================
        # CONFERIR SALDO DOS ITENS NOVAMENTE
        # ==================================================

        for item_medicao in itens_selecionados:

            item_obra_id = (
                item_medicao[
                    "item_obra_id"
                ]
            )

            valor_medido = (
                item_medicao[
                    "valor_medido"
                ]
            )

            cursor.execute("""
                SELECT
                    io.valor_total,

                    COALESCE(
                        (
                            SELECT SUM(
                                im.valor_medido
                            )
                            FROM itens_medicao im
                            WHERE im.item_obra_id = io.id
                        ),
                        0
                    )

                FROM itens_obra io

                WHERE io.id = ?
            """, (
                item_obra_id,
            ))

            resultado_item = cursor.fetchone()

            if not resultado_item:

                st.error(
                    "❌ Um dos itens da obra "
                    "não foi encontrado."
                )
                return

            valor_item_banco = float(
                resultado_item[0] or 0
            )

            valor_ja_medido_banco = float(
                resultado_item[1] or 0
            )

            saldo_banco = (
                valor_item_banco
                - valor_ja_medido_banco
            )

            if (
                valor_medido
                > saldo_banco + 0.001
            ):

                st.warning(
                    "⚠️ O valor informado para "
                    "um dos itens ultrapassa o "
                    "saldo disponível."
                )
                return

        # ==================================================
        # PREPARAR ARQUIVOS
        # ==================================================

        foto_nome = None
        foto_arquivo = None

        if foto is not None:

            foto_nome = foto.name
            foto_arquivo = foto.getvalue()

        boletim_nome = None
        boletim_arquivo = None

        if boletim is not None:

            boletim_nome = boletim.name
            boletim_arquivo = (
                boletim.getvalue()
            )

        # ==================================================
        # SALVAR
        # ==================================================

        try:

            # ==================================================
            # MEDIÇÃO
            # ==================================================

            cursor.execute("""
                INSERT INTO medicoes (
                    obra_id,
                    valor,
                    tipo_medicao,
                    data_medicao,
                    data_inicio,
                    data_final,
                    percentual_obra,
                    foto_nome,
                    foto_arquivo,
                    boletim_nome,
                    boletim_arquivo,
                    nota_fiscal,
                    data_nota,
                    empenho,
                    data_cadastro
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                obra_id,
                valor_total_medicao,
                tipo_medicao,

                data_medicao.strftime(
                    "%Y-%m-%d"
                ),

                data_inicio.strftime(
                    "%Y-%m-%d"
                ),

                data_final.strftime(
                    "%Y-%m-%d"
                ),

                percentual,

                foto_nome,
                foto_arquivo,

                boletim_nome,
                boletim_arquivo,

                nota_fiscal,

                data_nota.strftime(
                    "%Y-%m-%d"
                ),

                empenho,

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))

            medicao_id = cursor.lastrowid

            # ==================================================
            # ITENS DA MEDIÇÃO
            # ==================================================

            for item_medicao in itens_selecionados:

                cursor.execute("""
                    INSERT INTO itens_medicao (
                        medicao_id,
                        item_obra_id,
                        valor_medido
                    )
                    VALUES (?, ?, ?)
                """, (
                    medicao_id,
                    item_medicao[
                        "item_obra_id"
                    ],
                    item_medicao[
                        "valor_medido"
                    ]
                ))

            # ==================================================
            # RESPONSÁVEL DA MEDIÇÃO
            # ==================================================

            for fiscal in st.session_state[
                "fiscais_temp_medicao"
            ]:

                cursor.execute("""
                    INSERT INTO fiscais_medicao (
                        medicao_id,
                        fiscal
                    )
                    VALUES (?, ?)
                """, (
                    medicao_id,
                    fiscal["nome"]
                ))

            # ==================================================
            # COMMIT
            # ==================================================

            conn.commit()

            # ==================================================
            # LIMPAR
            # ==================================================

            st.session_state[
                "fiscais_temp_medicao"
            ] = []

            st.session_state.pop(
                "obra_anterior_medicao",
                None
            )

            # ==================================================
            # SUCESSO
            # ==================================================

            st.session_state[
                "medicao_cadastrada_sucesso"
            ] = True

            st.session_state[
                "tela_medicao"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao cadastrar medição: {e}"
            )
def localizar_medicao():

    st.subheader("🔎 Localizar Medição")

    if st.button(
        "⬅️ Voltar",
        key="voltar_localizar_medicao"
    ):
        st.session_state["tela_medicao"] = "Principal"
        st.session_state.pop(
            "medicao_edicao_id",
            None
        )
        st.rerun()

    st.divider()

    busca = st.text_input(
        "🔍 Pesquisar",
        placeholder="Obra, tipo de medição ou nota fiscal",
        key="pesquisa_medicao"
    )

    if busca:

        termo = f"%{busca}%"

        cursor.execute("""
            SELECT
                m.id,
                o.obra,
                m.tipo_medicao,
                m.data_medicao,
                m.valor,
                m.percentual_obra,
                m.nota_fiscal
            FROM medicoes m
            INNER JOIN obras o
                ON o.id = m.obra_id
            WHERE
                o.obra LIKE ?
                OR m.tipo_medicao LIKE ?
                OR m.nota_fiscal LIKE ?
            ORDER BY m.id DESC
        """, (
            termo,
            termo,
            termo
        ))

    else:

        cursor.execute("""
            SELECT
                m.id,
                o.obra,
                m.tipo_medicao,
                m.data_medicao,
                m.valor,
                m.percentual_obra,
                m.nota_fiscal
            FROM medicoes m
            INNER JOIN obras o
                ON o.id = m.obra_id
            ORDER BY m.id DESC
        """)

    registros = cursor.fetchall()

    if not registros:

        st.info(
            "Nenhuma medição encontrada."
        )
        return

    df = pd.DataFrame(
        registros,
        columns=[
            "ID",
            "Obra",
            "Tipo",
            "Data",
            "Valor",
            "Percentual",
            "Nota Fiscal"
        ]
    )

    js_duplo_clique = JsCode("""
        function(params) {
            if (params.data) {
                params.api.deselectAll();
                params.node.setSelected(true);
            }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    gb.configure_column(
        "ID",
        hide=True
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False
    )

    grid_options = gb.build()

    # IMPORTANTE:
    # clique simples não seleciona
    grid_options[
        "suppressRowClickSelection"
    ] = True

    grid_options[
        "onRowDoubleClicked"
    ] = js_duplo_clique

    resposta = AgGrid(
        df,
        gridOptions=grid_options,
        height=350,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="grid_localizar_medicao"
    )

    selecionados = resposta.get(
        "selected_rows",
        []
    )

    if isinstance(
        selecionados,
        pd.DataFrame
    ):
        selecionados = selecionados.to_dict(
            "records"
        )

    if selecionados:

        selecionado = selecionados[0]

        st.session_state[
            "medicao_edicao_id"
        ] = int(
            selecionado["ID"]
        )

        st.session_state[
            "tela_medicao"
        ] = "Alterar"

        st.rerun()

    st.info(
        "👆 Dê dois cliques em uma medição para alterar."
    )
def imprimir_medicao():

    st.subheader("🖨️ Imprimir Medição")

    # ==================================================
    # VOLTAR
    # ==================================================

    if st.button(
        "⬅️ Voltar",
        key="voltar_imprimir_medicao"
    ):
        st.session_state["tela_medicao"] = "Principal"

        st.session_state.pop(
            "medicao_imprimir_id",
            None
        )

        st.rerun()

    st.divider()

    # ==================================================
    # PESQUISA
    # ==================================================

    busca = st.text_input(
        "🔍 Pesquisar",
        placeholder="Obra, tipo de medição ou nota fiscal",
        key="pesquisa_imprimir_medicao"
    )

    # ==================================================
    # BUSCAR MEDIÇÕES
    # ==================================================

    if busca:

        termo = f"%{busca}%"

        cursor.execute("""
            SELECT
                m.id,
                o.obra,
                m.tipo_medicao,
                m.data_medicao,
                m.valor,
                m.percentual_obra,
                m.nota_fiscal
            FROM medicoes m

            INNER JOIN obras o
                ON o.id = m.obra_id

            WHERE
                o.obra LIKE ?
                OR m.tipo_medicao LIKE ?
                OR m.nota_fiscal LIKE ?

            ORDER BY m.id DESC
        """, (
            termo,
            termo,
            termo
        ))

    else:

        cursor.execute("""
            SELECT
                m.id,
                o.obra,
                m.tipo_medicao,
                m.data_medicao,
                m.valor,
                m.percentual_obra,
                m.nota_fiscal
            FROM medicoes m

            INNER JOIN obras o
                ON o.id = m.obra_id

            ORDER BY m.id DESC
        """)

    registros = cursor.fetchall()

    if not registros:

        st.info(
            "Nenhuma medição encontrada."
        )
        return

    # ==================================================
    # DATAFRAME
    # ==================================================

    df = pd.DataFrame(
        registros,
        columns=[
            "ID",
            "Obra",
            "Tipo",
            "Data",
            "Valor",
            "Percentual",
            "Nota Fiscal"
        ]
    )

    # ==================================================
    # DUPLO CLIQUE
    # ==================================================

    js_duplo_clique = JsCode("""
        function(params) {
            if (params.data) {
                params.api.deselectAll();
                params.node.setSelected(true);
            }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    gb.configure_column(
        "ID",
        hide=True
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False
    )

    grid_options = gb.build()

    grid_options[
        "suppressRowClickSelection"
    ] = True

    grid_options[
        "onRowDoubleClicked"
    ] = js_duplo_clique

    resposta = AgGrid(
        df,
        gridOptions=grid_options,
        height=350,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="grid_imprimir_medicao"
    )

    selecionados = resposta.get(
        "selected_rows",
        []
    )

    if isinstance(
        selecionados,
        pd.DataFrame
    ):
        selecionados = selecionados.to_dict(
            "records"
        )

    # ==================================================
    # SELECIONAR MEDIÇÃO
    # ==================================================

    if selecionados:

        selecionado = selecionados[0]

        st.session_state[
            "medicao_imprimir_id"
        ] = int(
            selecionado["ID"]
        )

    st.info(
        "👆 Dê dois cliques na medição que deseja imprimir."
    )

    # ==================================================
    # MEDIÇÃO SELECIONADA
    # ==================================================

    id_medicao = st.session_state.get(
        "medicao_imprimir_id"
    )

    if not id_medicao:
        return

    # ==================================================
    # BUSCAR DADOS DA MEDIÇÃO
    # ==================================================

    cursor.execute("""
        SELECT
            m.id,
            o.obra,
            o.contrato,
            o.valor_obra,

            m.tipo_medicao,
            m.data_medicao,
            m.data_inicio,
            m.data_final,

            m.valor,
            m.percentual_obra,

            m.nota_fiscal,
            m.data_nota,
            m.empenho,

            m.boletim_nome

        FROM medicoes m

        INNER JOIN obras o
            ON o.id = m.obra_id

        WHERE m.id = ?
    """, (
        id_medicao,
    ))

    medicao = cursor.fetchone()

    if not medicao:

        st.error(
            "❌ Medição não encontrada."
        )
        return

    # ==================================================
    # DADOS
    # ==================================================

    nome_obra = medicao[1]
    contrato = medicao[2] or "Não informado"
    valor_obra = float(medicao[3] or 0)

    tipo_medicao = medicao[4] or ""
    data_medicao = medicao[5] or ""
    data_inicio = medicao[6] or ""
    data_final = medicao[7] or ""

    valor_medicao = float(medicao[8] or 0)
    percentual = float(medicao[9] or 0)

    nota_fiscal = medicao[10] or "Não informado"
    data_nota = medicao[11] or ""
    empenho = medicao[12] or "Não informado"

    boletim_nome = medicao[13]

    # ==================================================
    # RESPONSÁVEL DA MEDIÇÃO
    # ==================================================

    cursor.execute("""
        SELECT fiscal
        FROM fiscais_medicao
        WHERE medicao_id = ?
        ORDER BY id
    """, (
        id_medicao,
    ))

    fiscais = cursor.fetchall()

    nomes_fiscais = [
        registro[0]
        for registro in fiscais
        if registro[0]
    ]

    responsavel_medicao = (
        ", ".join(nomes_fiscais)
        if nomes_fiscais
        else "Não informado"
    )

    # ==================================================
    # MOSTRAR RESUMO
    # ==================================================

    st.divider()

    st.markdown(
        "### 📏 Medição selecionada"
    )

    st.write(
        f"🏗️ **Obra:** {nome_obra}"
    )

    st.write(
        f"📜 **Contrato:** {contrato}"
    )

    st.write(
        f"👷 **Responsável pela medição:** "
        f"{responsavel_medicao}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Valor da Obra",
            f"R$ {valor_obra:,.2f}"
        )

    with col2:

        st.metric(
            "Valor da Medição",
            f"R$ {valor_medicao:,.2f}"
        )

    with col3:

        st.metric(
            "Percentual",
            f"{percentual:.2f}%"
        )

    st.write(
        f"📑 **Tipo:** {tipo_medicao}"
    )

    st.write(
        f"📅 **Data da medição:** "
        f"{data_medicao}"
    )

    st.write(
        f"📆 **Período:** "
        f"{data_inicio} até {data_final}"
    )

    st.write(
        f"🧾 **Nota Fiscal:** {nota_fiscal}"
    )

    st.write(
        f"💰 **Empenho:** {empenho}"
    )

    if boletim_nome:

        st.success(
            f"📊 Boletim Excel anexado: "
            f"{boletim_nome}"
        )

    else:

        st.info(
            "📊 Nenhum boletim Excel anexado."
        )

    # ==================================================
    # GERAR PDF
    # ==================================================

    st.divider()

    try:

        pdf = gerar_pdf_medicao(
            id_medicao
        )

        st.download_button(
            "🖨️ Gerar / Baixar PDF",
            data=pdf,
            file_name=(
                f"medicao_{id_medicao}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            key=(
                f"baixar_pdf_medicao_"
                f"{id_medicao}"
            )
        )

    except Exception as e:

        st.error(
            f"❌ Erro ao gerar PDF: {e}"
        )
def gerar_pdf_medicao(id_medicao):

    # ==================================================
    # FUNÇÃO PARA FORMATAR DATA
    # ==================================================

    def formatar_data(data):

        if not data:
            return "Não informado"

        try:

            return datetime.strptime(
                str(data)[:10],
                "%Y-%m-%d"
            ).strftime(
                "%d/%m/%Y"
            )

        except Exception:

            return str(data)

    # ==================================================
    # FUNÇÃO PARA FORMATAR DINHEIRO
    # ==================================================

    def moeda(valor):

        try:

            valor = float(
                valor or 0
            )

            texto = (
                f"{valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            return f"R$ {texto}"

        except Exception:

            return "R$ 0,00"

    # ==================================================
    # BUSCAR MEDIÇÃO
    # ==================================================

    cursor.execute("""
        SELECT
            m.id,

            o.id,
            o.obra,
            o.contrato,
            o.valor_obra,

            m.tipo_medicao,
            m.data_medicao,
            m.data_inicio,
            m.data_final,

            m.valor,
            m.percentual_obra,

            m.nota_fiscal,
            m.data_nota,
            m.empenho,

            m.boletim_nome

        FROM medicoes m

        INNER JOIN obras o
            ON o.id = m.obra_id

        WHERE m.id = ?
    """, (
        id_medicao,
    ))

    medicao = cursor.fetchone()

    if not medicao:

        raise Exception(
            "Medição não encontrada."
        )

    # ==================================================
    # VARIÁVEIS
    # ==================================================

    obra_id = medicao[1]
    nome_obra = medicao[2] or "Não informado"
    contrato = medicao[3] or "Não informado"
    valor_obra = medicao[4] or 0

    tipo_medicao = medicao[5] or "Não informado"
    data_medicao = medicao[6]
    data_inicio = medicao[7]
    data_final = medicao[8]

    valor_medicao = medicao[9] or 0
    percentual = float(
        medicao[10] or 0
    )

    nota_fiscal = (
        medicao[11]
        or "Não informado"
    )

    data_nota = medicao[12]

    empenho = (
        medicao[13]
        or "Não informado"
    )

    boletim_nome = medicao[14]

    # ==================================================
    # RESPONSÁVEL EFETIVO DA MEDIÇÃO
    # ==================================================

    cursor.execute("""
        SELECT fiscal
        FROM fiscais_medicao
        WHERE medicao_id = ?
        ORDER BY id
    """, (
        id_medicao,
    ))

    registros_fiscais = (
        cursor.fetchall()
    )

    fiscais = [
        registro[0]
        for registro in registros_fiscais
        if registro[0]
    ]

    # ==================================================
    # DADOS DOS RESPONSÁVEIS
    #
    # fiscal_medicao guarda o nome escolhido.
    # Aqui procuramos esse profissional entre os
    # responsáveis vinculados à obra para obter ART etc.
    # ==================================================

    responsaveis_pdf = []

    for nome_fiscal in fiscais:

        cursor.execute("""
            SELECT
                r.nome,
                ro.tipo_responsabilidade,
                ro.tipo_vinculo,
                ro.numero_art,
                ro.tipo_art,
                ro.data_inicio_art,
                ro.data_final_art

            FROM responsaveis_obra ro

            INNER JOIN responsaveis r
                ON r.id = ro.responsavel_id

            WHERE ro.obra_id = ?
              AND r.nome = ?

            ORDER BY ro.id

            LIMIT 1
        """, (
            obra_id,
            nome_fiscal
        ))

        dados_resp = cursor.fetchone()

        if dados_resp:

            responsaveis_pdf.append(
                dados_resp
            )

        else:

            responsaveis_pdf.append(
                (
                    nome_fiscal,
                    "",
                    "",
                    "",
                    "",
                    "",
                    ""
                )
            )

    # ==================================================
    # ITENS DA MEDIÇÃO
    # ==================================================

    cursor.execute("""
        SELECT
            i.codigo,
            i.descricao,
            i.unidade,
            im.valor_medido

        FROM itens_medicao im

        INNER JOIN itens_obra io
            ON io.id = im.item_obra_id

        INNER JOIN itens i
            ON i.id = io.item_id

        WHERE im.medicao_id = ?

        ORDER BY i.codigo
    """, (
        id_medicao,
    ))

    itens = cursor.fetchall()

    # ==================================================
    # CONFIGURAÇÃO DO PDF
    # ==================================================

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloMedicao",
        parent=estilos["Title"],
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=12
    )

    subtitulo = ParagraphStyle(
        "SubtituloMedicao",
        parent=estilos["Heading2"],
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=6
    )

    normal = ParagraphStyle(
        "NormalMedicao",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12
    )

    cabecalho_tabela = ParagraphStyle(
        "CabecalhoTabelaMedicao",
        parent=normal,
        fontSize=8,
        leading=10
    )

    historia = []

    # ==================================================
    # TÍTULO
    # ==================================================

    historia.append(
        Paragraph(
            "SISOPB",
            titulo
        )
    )

    historia.append(
        Paragraph(
            "RELATÓRIO DE MEDIÇÃO",
            titulo
        )
    )

    historia.append(
        Spacer(
            1,
            0.2 * cm
        )
    )

    # ==================================================
    # IDENTIFICAÇÃO
    # ==================================================

    historia.append(
        Paragraph(
            "Identificação",
            subtitulo
        )
    )

    tabela_identificacao = Table(
        [
            [
                Paragraph(
                    "<b>Obra</b>",
                    normal
                ),
                Paragraph(
                    str(nome_obra),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Contrato</b>",
                    normal
                ),
                Paragraph(
                    str(contrato),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Medição</b>",
                    normal
                ),
                Paragraph(
                    f"Nº {id_medicao}",
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Tipo</b>",
                    normal
                ),
                Paragraph(
                    str(tipo_medicao),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Data da Medição</b>",
                    normal
                ),
                Paragraph(
                    formatar_data(
                        data_medicao
                    ),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Período</b>",
                    normal
                ),
                Paragraph(
                    (
                        f"{formatar_data(data_inicio)} "
                        f"a "
                        f"{formatar_data(data_final)}"
                    ),
                    normal
                )
            ]
        ],
        colWidths=[
            4 * cm,
            13.5 * cm
        ]
    )

    tabela_identificacao.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    historia.append(
        tabela_identificacao
    )

    # ==================================================
    # RESPONSÁVEL
    # ==================================================

    historia.append(
        Paragraph(
            "Responsável pela Medição",
            subtitulo
        )
    )

    if responsaveis_pdf:

        dados_responsaveis = [
            [
                Paragraph(
                    "<b>Responsável</b>",
                    cabecalho_tabela
                ),
                Paragraph(
                    "<b>Responsabilidade</b>",
                    cabecalho_tabela
                ),
                Paragraph(
                    "<b>Vínculo</b>",
                    cabecalho_tabela
                ),
                Paragraph(
                    "<b>ART</b>",
                    cabecalho_tabela
                ),
                Paragraph(
                    "<b>Tipo ART</b>",
                    cabecalho_tabela
                )
            ]
        ]

        for responsavel in responsaveis_pdf:

            dados_responsaveis.append([
                Paragraph(
                    str(
                        responsavel[0]
                        or "-"
                    ),
                    normal
                ),
                Paragraph(
                    str(
                        responsavel[1]
                        or "-"
                    ),
                    normal
                ),
                Paragraph(
                    str(
                        responsavel[2]
                        or "-"
                    ),
                    normal
                ),
                Paragraph(
                    str(
                        responsavel[3]
                        or "-"
                    ),
                    normal
                ),
                Paragraph(
                    str(
                        responsavel[4]
                        or "-"
                    ),
                    normal
                )
            ])

        tabela_responsaveis = Table(
            dados_responsaveis,
            colWidths=[
                4 * cm,
                4 * cm,
                3.5 * cm,
                3 * cm,
                3 * cm
            ],
            repeatRows=1
        )

        tabela_responsaveis.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )
            ])
        )

        historia.append(
            tabela_responsaveis
        )

    else:

        historia.append(
            Paragraph(
                "Responsável não informado.",
                normal
            )
        )

    # ==================================================
    # RESUMO FINANCEIRO
    # ==================================================

    historia.append(
        Paragraph(
            "Resumo Financeiro",
            subtitulo
        )
    )

    tabela_financeira = Table(
        [
            [
                Paragraph(
                    "<b>Valor da Obra</b>",
                    normal
                ),
                Paragraph(
                    "<b>Valor da Medição</b>",
                    normal
                ),
                Paragraph(
                    "<b>Percentual da Obra</b>",
                    normal
                )
            ],
            [
                Paragraph(
                    moeda(valor_obra),
                    normal
                ),
                Paragraph(
                    moeda(valor_medicao),
                    normal
                ),
                Paragraph(
                    f"{percentual:.2f}%",
                    normal
                )
            ]
        ],
        colWidths=[
            5.8 * cm,
            5.8 * cm,
            5.8 * cm
        ]
    )

    tabela_financeira.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    historia.append(
        tabela_financeira
    )

    # ==================================================
    # ITENS MEDIDOS
    # ==================================================

    historia.append(
        Paragraph(
            "Itens Medidos",
            subtitulo
        )
    )

    dados_itens = [
        [
            Paragraph(
                "<b>Código</b>",
                cabecalho_tabela
            ),
            Paragraph(
                "<b>Descrição</b>",
                cabecalho_tabela
            ),
            Paragraph(
                "<b>Unidade</b>",
                cabecalho_tabela
            ),
            Paragraph(
                "<b>Valor Medido</b>",
                cabecalho_tabela
            )
        ]
    ]

    for item in itens:

        dados_itens.append([
            Paragraph(
                str(item[0] or ""),
                normal
            ),
            Paragraph(
                str(item[1] or ""),
                normal
            ),
            Paragraph(
                str(item[2] or ""),
                normal
            ),
            Paragraph(
                moeda(item[3]),
                normal
            )
        ])

    if len(dados_itens) == 1:

        dados_itens.append([
            "",
            Paragraph(
                "Nenhum item encontrado.",
                normal
            ),
            "",
            ""
        ])

    tabela_itens = Table(
        dados_itens,
        colWidths=[
            2.5 * cm,
            9 * cm,
            2.5 * cm,
            3.5 * cm
        ],
        repeatRows=1
    )

    tabela_itens.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "ALIGN",
                (3, 1),
                (3, -1),
                "RIGHT"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    historia.append(
        tabela_itens
    )

    # ==================================================
    # DOCUMENTOS
    # ==================================================

    historia.append(
        Paragraph(
            "Documentos",
            subtitulo
        )
    )

    boletim_texto = (
        f"Sim - {boletim_nome}"
        if boletim_nome
        else "Não anexado"
    )

    tabela_documentos = Table(
        [
            [
                Paragraph(
                    "<b>Nota Fiscal</b>",
                    normal
                ),
                Paragraph(
                    str(nota_fiscal),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Data da Nota</b>",
                    normal
                ),
                Paragraph(
                    formatar_data(
                        data_nota
                    ),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Empenho</b>",
                    normal
                ),
                Paragraph(
                    str(empenho),
                    normal
                )
            ],
            [
                Paragraph(
                    "<b>Boletim de Medição</b>",
                    normal
                ),
                Paragraph(
                    str(boletim_texto),
                    normal
                )
            ]
        ],
        colWidths=[
            4 * cm,
            13.5 * cm
        ]
    )

    tabela_documentos.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    historia.append(
        tabela_documentos
    )

    # ==================================================
    # ASSINATURA
    # ==================================================

    historia.append(
        Spacer(
            1,
            1.5 * cm
        )
    )

    historia.append(
        Paragraph(
            "_______________________________________________",
            ParagraphStyle(
                "AssinaturaMedicao",
                parent=normal,
                alignment=1
            )
        )
    )

    nome_assinatura = (
        fiscais[0]
        if fiscais
        else "Responsável pela Medição"
    )

    historia.append(
        Paragraph(
            str(nome_assinatura),
            ParagraphStyle(
                "NomeAssinaturaMedicao",
                parent=normal,
                alignment=1
            )
        )
    )

    historia.append(
        Paragraph(
            "Responsável pela Medição",
            ParagraphStyle(
                "CargoAssinaturaMedicao",
                parent=normal,
                alignment=1
            )
        )
    )

    # ==================================================
    # GERAR
    # ==================================================

    documento.build(
        historia
    )

    buffer.seek(0)

    return buffer.getvalue()
def alterar_medicao():

    st.subheader("✏️ Alterar Medição")

    medicao_id = st.session_state.get(
        "medicao_edicao_id"
    )

    if not medicao_id:

        st.warning(
            "Nenhuma medição selecionada."
        )

        st.session_state[
            "tela_medicao"
        ] = "Localizar"

        return

    if st.button(
        "⬅️ Voltar",
        key="voltar_alterar_medicao"
    ):
        st.session_state.pop(
            "medicao_edicao_id",
            None
        )

        st.session_state[
            "tela_medicao"
        ] = "Localizar"

        st.rerun()

    # ==========================================
    # MEDIÇÃO
    # ==========================================

    cursor.execute("""
        SELECT
            m.obra_id,
            o.obra,
            o.valor_obra,
            m.tipo_medicao,
            m.data_medicao,
            m.data_inicio,
            m.data_final,
            m.nota_fiscal,
            m.data_nota,
            m.empenho,
            m.foto_nome,
            m.boletim_nome
        FROM medicoes m
        INNER JOIN obras o
            ON o.id = m.obra_id
        WHERE m.id = ?
    """, (
        medicao_id,
    ))

    medicao = cursor.fetchone()

    if not medicao:

        st.error(
            "Medição não encontrada."
        )
        return

    obra_id = medicao[0]
    nome_obra = medicao[1]
    valor_obra = float(
        medicao[2] or 0
    )

    st.info(
        f"🏗️ Obra: {nome_obra}"
    )

    # ==========================================
    # DATAS
    # ==========================================

    try:
        data_medicao_atual = datetime.strptime(
            medicao[4],
            "%Y-%m-%d"
        ).date()
    except Exception:
        data_medicao_atual = datetime.now().date()

    try:
        data_inicio_atual = datetime.strptime(
            medicao[5],
            "%Y-%m-%d"
        ).date()
    except Exception:
        data_inicio_atual = datetime.now().date()

    try:
        data_final_atual = datetime.strptime(
            medicao[6],
            "%Y-%m-%d"
        ).date()
    except Exception:
        data_final_atual = datetime.now().date()

    try:
        data_nota_atual = datetime.strptime(
            medicao[8],
            "%Y-%m-%d"
        ).date()
    except Exception:
        data_nota_atual = datetime.now().date()

    tipos = [
        "Inicial",
        "Parcial",
        "Final"
    ]

    tipo_atual = medicao[3]

    indice_tipo = 0

    if tipo_atual in tipos:
        indice_tipo = tipos.index(
            tipo_atual
        )

    col1, col2 = st.columns(2)

    with col1:

        tipo_medicao = st.selectbox(
            "📋 Tipo de Medição",
            tipos,
            index=indice_tipo,
            key=f"alterar_tipo_{medicao_id}"
        )

        data_medicao = st.date_input(
            "📅 Data da Medição",
            value=data_medicao_atual,
            key=f"alterar_data_{medicao_id}"
        )

        data_inicio = st.date_input(
            "📅 Data de Início",
            value=data_inicio_atual,
            key=f"alterar_inicio_{medicao_id}"
        )

    with col2:

        data_final = st.date_input(
            "📅 Data Final",
            value=data_final_atual,
            key=f"alterar_final_{medicao_id}"
        )

        nota_fiscal = st.text_input(
            "🧾 Nota Fiscal",
            value=medicao[7] or "",
            key=f"alterar_nf_{medicao_id}"
        )

        data_nota = st.date_input(
            "📅 Data da Nota",
            value=data_nota_atual,
            key=f"alterar_data_nf_{medicao_id}"
        )

        empenho = st.text_input(
            "💰 Empenho",
            value=medicao[9] or "",
            key=f"alterar_empenho_{medicao_id}"
        )

    # ==========================================
    # ITENS
    # ==========================================

    st.divider()

    st.markdown("### 🧱 Itens da Medição")

    cursor.execute("""
        SELECT
            io.id,
            i.codigo,
            i.descricao,
            i.unidade,
            io.valor_total,

            COALESCE(
                (
                    SELECT SUM(im2.valor_medido)
                    FROM itens_medicao im2
                    WHERE
                        im2.item_obra_id = io.id
                        AND im2.medicao_id != ?
                ),
                0
            ),

            COALESCE(
                (
                    SELECT im3.valor_medido
                    FROM itens_medicao im3
                    WHERE
                        im3.item_obra_id = io.id
                        AND im3.medicao_id = ?
                ),
                0
            )

        FROM itens_obra io

        INNER JOIN itens i
            ON i.id = io.item_id

        WHERE io.obra_id = ?

        ORDER BY i.codigo
    """, (
        medicao_id,
        medicao_id,
        obra_id
    ))

    itens = cursor.fetchall()

    novos_itens = []

    valor_total_medicao = 0.0

    for item in itens:

        item_obra_id = item[0]
        codigo = item[1]
        descricao = item[2]
        unidade = item[3]

        valor_item = float(
            item[4] or 0
        )

        outras_medicoes = float(
            item[5] or 0
        )

        valor_atual = float(
            item[6] or 0
        )

        saldo_permitido = (
            valor_item
            - outras_medicoes
        )

        if saldo_permitido < 0:
            saldo_permitido = 0

        with st.container(border=True):

            st.markdown(
                f"**{codigo} - {descricao}**"
            )

            st.write(
                f"Unidade: **{unidade}**"
            )

            st.write(
                f"Valor do item: "
                f"**R$ {valor_item:,.2f}**"
            )

            st.write(
                f"Disponível para esta medição: "
                f"**R$ {saldo_permitido:,.2f}**"
            )

            selecionado_atual = (
                valor_atual > 0
            )

            selecionar = st.checkbox(
                "Selecionar",
                value=selecionado_atual,
                key=(
                    f"alterar_selecionar_"
                    f"{medicao_id}_"
                    f"{item_obra_id}"
                )
            )

            if selecionar:

                valor_medido = st.number_input(
                    "💰 Valor medido",
                    min_value=0.0,
                    max_value=float(
                        saldo_permitido
                    ),
                    value=min(
                        valor_atual,
                        saldo_permitido
                    ),
                    step=0.01,
                    format="%.2f",
                    key=(
                        f"alterar_valor_"
                        f"{medicao_id}_"
                        f"{item_obra_id}"
                    )
                )

                novos_itens.append({
                    "item_obra_id": item_obra_id,
                    "valor": valor_medido
                })

                valor_total_medicao += (
                    valor_medido
                )

    percentual = 0

    if valor_obra > 0:

        percentual = (
            valor_total_medicao
            / valor_obra
        ) * 100

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Valor da Obra",
            f"R$ {valor_obra:,.2f}"
        )

    with col2:
        st.metric(
            "Valor da Medição",
            f"R$ {valor_total_medicao:,.2f}"
        )

    with col3:
        st.metric(
            "Percentual",
            f"{percentual:.2f}%"
        )

    # ==========================================
    # FISCAIS EXISTENTES
    # ==========================================

    st.divider()

    st.markdown("### 👷 Fiscais")

    cursor.execute("""
        SELECT fiscal
        FROM fiscais_medicao
        WHERE medicao_id = ?
        ORDER BY id
    """, (
        medicao_id,
    ))

    fiscais_existentes = [
        linha[0]
        for linha in cursor.fetchall()
    ]

    chave_qtd = (
        f"qtd_fiscais_alterar_{medicao_id}"
    )

    if chave_qtd not in st.session_state:

        st.session_state[chave_qtd] = max(
            1,
            len(fiscais_existentes)
        )

    fiscais = []

    for numero in range(
        st.session_state[chave_qtd]
    ):

        valor_fiscal = ""

        if numero < len(
            fiscais_existentes
        ):
            valor_fiscal = (
                fiscais_existentes[numero]
            )

        fiscal = st.text_input(
            f"👷 Fiscal {numero + 1}",
            value=valor_fiscal,
            key=(
                f"alterar_fiscal_"
                f"{medicao_id}_{numero}"
            )
        )

        if fiscal.strip():
            fiscais.append(
                fiscal.strip()
            )

    if st.button(
        "➕ Adicionar Fiscal",
        key=f"add_fiscal_alterar_{medicao_id}"
    ):

        st.session_state[
            chave_qtd
        ] += 1

        st.rerun()

    # ==========================================
    # NOVOS ARQUIVOS
    # ==========================================

    st.divider()

    st.markdown("### 📎 Anexos")

    if medicao[10]:
        st.write(
            f"📷 Foto atual: **{medicao[10]}**"
        )

    if medicao[11]:
        st.write(
            f"📄 Boletim atual: **{medicao[11]}**"
        )

    nova_foto = st.file_uploader(
        "📷 Substituir foto",
        type=["jpg", "jpeg", "png"],
        key=f"alterar_foto_{medicao_id}"
    )

    novo_boletim = st.file_uploader(
        "📄 Substituir boletim",
        type=[
            "pdf",
            "jpg",
            "jpeg",
            "png"
        ],
        key=f"alterar_boletim_{medicao_id}"
    )

    # ==========================================
    # SALVAR
    # ==========================================

    st.divider()

    if st.button(
        "💾 Salvar Alterações",
        type="primary",
        use_container_width=True,
        key=f"salvar_alteracao_medicao_{medicao_id}"
    ):

        if not novos_itens:

            st.warning(
                "Selecione pelo menos um item."
            )
            return

        if valor_total_medicao <= 0:

            st.warning(
                "O valor da medição deve ser maior que zero."
            )
            return

        if not fiscais:

            st.warning(
                "Informe pelo menos um fiscal."
            )
            return

        if data_final < data_inicio:

            st.warning(
                "Data final menor que data inicial."
            )
            return

        try:

            # ==================================
            # ATUALIZAR DADOS
            # ==================================

            cursor.execute("""
                UPDATE medicoes
                SET
                    valor = ?,
                    tipo_medicao = ?,
                    data_medicao = ?,
                    data_inicio = ?,
                    data_final = ?,
                    percentual_obra = ?,
                    nota_fiscal = ?,
                    data_nota = ?,
                    empenho = ?
                WHERE id = ?
            """, (
                valor_total_medicao,
                tipo_medicao,
                str(data_medicao),
                str(data_inicio),
                str(data_final),
                percentual,
                nota_fiscal,
                str(data_nota),
                empenho,
                medicao_id
            ))

            # ==================================
            # FOTO
            # ==================================

            if nova_foto:

                cursor.execute("""
                    UPDATE medicoes
                    SET
                        foto_nome = ?,
                        foto_arquivo = ?
                    WHERE id = ?
                """, (
                    nova_foto.name,
                    nova_foto.getvalue(),
                    medicao_id
                ))

            # ==================================
            # BOLETIM
            # ==================================

            if novo_boletim:

                cursor.execute("""
                    UPDATE medicoes
                    SET
                        boletim_nome = ?,
                        boletim_arquivo = ?
                    WHERE id = ?
                """, (
                    novo_boletim.name,
                    novo_boletim.getvalue(),
                    medicao_id
                ))

            # ==================================
            # REFAZER ITENS
            # ==================================

            cursor.execute("""
                DELETE FROM itens_medicao
                WHERE medicao_id = ?
            """, (
                medicao_id,
            ))

            for item in novos_itens:

                cursor.execute("""
                    INSERT INTO itens_medicao (
                        medicao_id,
                        item_obra_id,
                        valor_medido
                    )
                    VALUES (?, ?, ?)
                """, (
                    medicao_id,
                    item["item_obra_id"],
                    item["valor"]
                ))

            # ==================================
            # REFAZER FISCAIS
            # ==================================

            cursor.execute("""
                DELETE FROM fiscais_medicao
                WHERE medicao_id = ?
            """, (
                medicao_id,
            ))

            for fiscal in fiscais:

                cursor.execute("""
                    INSERT INTO fiscais_medicao (
                        medicao_id,
                        fiscal
                    )
                    VALUES (?, ?)
                """, (
                    medicao_id,
                    fiscal
                ))

            conn.commit()

            st.session_state.pop(
                "medicao_edicao_id",
                None
            )

            st.session_state[
                "medicao_alterada_sucesso"
            ] = True

            st.session_state[
                "tela_medicao"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao alterar medição: {e}"
            )
def excluir_medicao():

    st.subheader("🗑️ Excluir Medição")

    if st.button(
        "⬅️ Voltar",
        key="voltar_excluir_medicao"
    ):

        st.session_state.pop(
            "medicao_excluir_id",
            None
        )

        st.session_state[
            "tela_medicao"
        ] = "Principal"

        st.rerun()

    st.divider()

    medicao_id = st.session_state.get(
        "medicao_excluir_id"
    )

    # ==========================================
    # SE AINDA NÃO SELECIONOU
    # ==========================================

    if not medicao_id:

        busca = st.text_input(
            "🔍 Pesquisar",
            placeholder="Obra, tipo ou nota fiscal",
            key="pesquisa_excluir_medicao"
        )

        if busca:

            termo = f"%{busca}%"

            cursor.execute("""
                SELECT
                    m.id,
                    o.obra,
                    m.tipo_medicao,
                    m.data_medicao,
                    m.valor,
                    m.percentual_obra,
                    m.nota_fiscal
                FROM medicoes m
                INNER JOIN obras o
                    ON o.id = m.obra_id
                WHERE
                    o.obra LIKE ?
                    OR m.tipo_medicao LIKE ?
                    OR m.nota_fiscal LIKE ?
                ORDER BY m.id DESC
            """, (
                termo,
                termo,
                termo
            ))

        else:

            cursor.execute("""
                SELECT
                    m.id,
                    o.obra,
                    m.tipo_medicao,
                    m.data_medicao,
                    m.valor,
                    m.percentual_obra,
                    m.nota_fiscal
                FROM medicoes m
                INNER JOIN obras o
                    ON o.id = m.obra_id
                ORDER BY m.id DESC
            """)

        registros = cursor.fetchall()

        if not registros:

            st.info(
                "Nenhuma medição encontrada."
            )
            return

        df = pd.DataFrame(
            registros,
            columns=[
                "ID",
                "Obra",
                "Tipo",
                "Data",
                "Valor",
                "Percentual",
                "Nota Fiscal"
            ]
        )

        js_duplo_clique = JsCode("""
            function(params) {
                if (params.data) {
                    params.api.deselectAll();
                    params.node.setSelected(true);
                }
            }
        """)

        gb = GridOptionsBuilder.from_dataframe(
            df
        )

        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True
        )

        gb.configure_column(
            "ID",
            hide=True
        )

        gb.configure_selection(
            selection_mode="single",
            use_checkbox=False
        )

        grid_options = gb.build()

        grid_options[
            "suppressRowClickSelection"
        ] = True

        grid_options[
            "onRowDoubleClicked"
        ] = js_duplo_clique

        resposta = AgGrid(
            df,
            gridOptions=grid_options,
            height=350,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="grid_excluir_medicao"
        )

        selecionados = resposta.get(
            "selected_rows",
            []
        )

        if isinstance(
            selecionados,
            pd.DataFrame
        ):
            selecionados = selecionados.to_dict(
                "records"
            )

        if selecionados:

            selecionado = selecionados[0]

            st.session_state[
                "medicao_excluir_id"
            ] = int(
                selecionado["ID"]
            )

            st.rerun()

        st.info(
            "👆 Dê dois cliques na medição que deseja excluir."
        )

        return

    # ==========================================
    # MEDIÇÃO SELECIONADA
    # ==========================================

    cursor.execute("""
        SELECT
            m.id,
            o.obra,
            m.tipo_medicao,
            m.data_medicao,
            m.valor,
            m.percentual_obra,
            m.nota_fiscal
        FROM medicoes m
        INNER JOIN obras o
            ON o.id = m.obra_id
        WHERE m.id = ?
    """, (
        medicao_id,
    ))

    medicao = cursor.fetchone()

    if not medicao:

        st.error(
            "Medição não encontrada."
        )

        st.session_state.pop(
            "medicao_excluir_id",
            None
        )

        return

    # ==========================================
    # DETALHES
    # ==========================================

    st.markdown("### ⚠️ Confirmar Exclusão")

    with st.container(border=True):

        st.write(
            f"🏗️ **Obra:** {medicao[1]}"
        )

        st.write(
            f"📋 **Tipo:** {medicao[2]}"
        )

        st.write(
            f"📅 **Data:** {medicao[3]}"
        )

        st.write(
            f"💰 **Valor:** R$ {float(medicao[4] or 0):,.2f}"
        )

        st.write(
            f"📊 **Percentual:** "
            f"{float(medicao[5] or 0):.2f}%"
        )

        st.write(
            f"🧾 **Nota Fiscal:** "
            f"{medicao[6] or 'Não informada'}"
        )

    confirmar = st.checkbox(
        "Confirmo a exclusão desta medição.",
        key=f"confirmar_exclusao_medicao_{medicao_id}"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "❌ Cancelar",
            use_container_width=True,
            key="cancelar_exclusao_medicao"
        ):

            st.session_state.pop(
                "medicao_excluir_id",
                None
            )

            st.rerun()

    with col2:

        if st.button(
            "💾 Salvar Exclusão",
            type="primary",
            use_container_width=True,
            disabled=not confirmar,
            key="salvar_exclusao_medicao"
        ):

            try:

                # Primeiro dependências

                cursor.execute("""
                    DELETE FROM itens_medicao
                    WHERE medicao_id = ?
                """, (
                    medicao_id,
                ))

                cursor.execute("""
                    DELETE FROM fiscais_medicao
                    WHERE medicao_id = ?
                """, (
                    medicao_id,
                ))

                # Depois medição

                cursor.execute("""
                    DELETE FROM medicoes
                    WHERE id = ?
                """, (
                    medicao_id,
                ))

                conn.commit()

                st.session_state.pop(
                    "medicao_excluir_id",
                    None
                )

                st.session_state[
                    "medicao_excluida_sucesso"
                ] = True

                st.session_state[
                    "tela_medicao"
                ] = "Principal"

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"❌ Erro ao excluir medição: {e}"
                )
def situacao_da_obra():

    # ==================================================
    # TÍTULO
    # ==================================================

    st.title("🚧 Situação da Obra")

    st.caption(
        "Atualize a situação da obra e registre "
        "os dados da publicação."
    )

    st.divider()

    # ==================================================
    # CONTROLE DE TELA
    # ==================================================

    if "tela_situacao_obra" not in st.session_state:
        st.session_state["tela_situacao_obra"] = "Principal"

    tela = st.session_state["tela_situacao_obra"]

    # ==================================================
    # TELA PRINCIPAL
    # ==================================================

    if tela == "Principal":

        # --------------------------------------------------
        # MENSAGEM DE SUCESSO
        # --------------------------------------------------

        if st.session_state.pop(
            "situacao_obra_alterada_sucesso",
            False
        ):
            st.success(
                "✅ Situação da obra atualizada com sucesso!"
            )

        st.markdown("### 🔎 Selecione uma obra")

        # ==================================================
        # BUSCAR OBRAS
        # ==================================================
        #
        # Obras definitivamente recebidas não aparecem
        # mais para alteração de situação.
        # ==================================================

        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                situacao,
                data_inicio,
                data_entrega
            FROM obras
            WHERE
                situacao IS NULL
                OR situacao != '7 – Concluído e recebido definitivamente'
            ORDER BY obra
        """)

        registros = cursor.fetchall()

        if not registros:
            st.info(
                "Nenhuma obra disponível para alteração de situação."
            )
            return

        # ==================================================
        # DATAFRAME
        # ==================================================

        df = pd.DataFrame(
            registros,
            columns=[
                "ID",
                "Obra",
                "Contrato",
                "Situação Atual",
                "Data Início",
                "Data Entrega"
            ]
        )

        # ==================================================
        # DUPLO CLIQUE
        # ==================================================

        js_duplo_clique = JsCode("""
            function(params) {
                if (params.data) {
                    params.api.deselectAll();
                    params.node.setSelected(true);
                }
            }
        """)

        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True
        )

        gb.configure_column(
            "ID",
            hide=True
        )

        gb.configure_selection(
            selection_mode="single",
            use_checkbox=False
        )

        grid_options = gb.build()

        grid_options["suppressRowClickSelection"] = True
        grid_options["onRowDoubleClicked"] = js_duplo_clique

        resposta = AgGrid(
            df,
            gridOptions=grid_options,
            height=350,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="grid_situacao_obra"
        )

        selecionados = resposta.get(
            "selected_rows",
            []
        )

        if isinstance(
            selecionados,
            pd.DataFrame
        ):
            selecionados = selecionados.to_dict(
                "records"
            )

        # ==================================================
        # ABRIR OBRA
        # ==================================================

        if selecionados:

            selecionado = selecionados[0]

            st.session_state[
                "situacao_obra_id"
            ] = int(
                selecionado["ID"]
            )

            st.session_state[
                "tela_situacao_obra"
            ] = "Alterar"

            st.rerun()

        st.info(
            "👆 Dê dois cliques em uma obra "
            "para atualizar sua situação."
        )

    # ==================================================
    # ALTERAR SITUAÇÃO
    # ==================================================

    elif tela == "Alterar":

        id_obra = st.session_state.get(
            "situacao_obra_id"
        )

        if not id_obra:

            st.session_state[
                "tela_situacao_obra"
            ] = "Principal"

            st.rerun()

        # ==================================================
        # VOLTAR
        # ==================================================

        if st.button(
            "⬅️ Voltar",
            key="voltar_situacao_obra"
        ):

            st.session_state[
                "tela_situacao_obra"
            ] = "Principal"

            st.session_state.pop(
                "situacao_obra_id",
                None
            )

            st.rerun()

        st.divider()

        # ==================================================
        # BUSCAR DADOS DA OBRA
        # ==================================================

        cursor.execute("""
            SELECT
                obra,
                contrato,
                situacao,
                motivo_paralisacao,
                data_inicio,
                data_entrega,
                valor_obra
            FROM obras
            WHERE id = ?
        """, (
            id_obra,
        ))

        obra = cursor.fetchone()

        if not obra:

            st.error(
                "❌ Obra não encontrada."
            )
            return

        nome_obra = obra[0]
        contrato = obra[1] or "-"
        situacao_atual = obra[2]
        motivo_atual = obra[3] or ""
        data_inicio = obra[4] or "-"
        data_entrega = obra[5] or "-"
        valor_obra = float(
            obra[6] or 0
        )

        # ==================================================
        # BLOQUEIO DE OBRA FINALIZADA
        # ==================================================
        #
        # Mesmo que a tela tenha sido aberta antes da obra
        # ser finalizada, não será possível alterar.
        # ==================================================

        if (
            situacao_atual
            == "7 – Concluído e recebido definitivamente"
        ):

            st.error(
                "🔒 Esta obra foi concluída e recebida "
                "definitivamente."
            )

            st.warning(
                "A obra está encerrada e não pode mais "
                "ter sua situação alterada."
            )

            if st.button(
                "⬅️ Voltar para Obras",
                key=f"voltar_obra_finalizada_{id_obra}"
            ):

                st.session_state[
                    "tela_situacao_obra"
                ] = "Principal"

                st.session_state.pop(
                    "situacao_obra_id",
                    None
                )

                st.rerun()

            return

        # ==================================================
        # INFORMAÇÕES DA OBRA
        # ==================================================

        st.subheader(
            f"🏗️ {nome_obra}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"**Contrato:** {contrato}"
            )

        with col2:

            st.write(
                f"**Data de início:** "
                f"{data_inicio}"
            )

        with col3:

            st.write(
                f"**Data de entrega:** "
                f"{data_entrega}"
            )

        # --------------------------------------------------
        # FORMATAÇÃO DO VALOR
        # --------------------------------------------------

        valor_formatado = (
            f"{valor_obra:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        st.write(
            f"**Valor da obra:** "
            f"R$ {valor_formatado}"
        )

        st.write(
            f"**Situação atual:** "
            f"{situacao_atual or 'Não informada'}"
        )

        st.divider()

        # ==================================================
        # SITUAÇÕES
        # ==================================================

        situacoes = [
            "1 – Não iniciado",
            "2 – Iniciado",
            "3 – Encerrado por rescisão contratual",
            "4 – Paralisado",
            "5 – Concluído e não recebido",
            "6 – Concluído e recebido provisoriamente",
            "7 – Concluído e recebido definitivamente",
            "8 – Reiniciado"
        ]

        # ==================================================
        # ÍNDICE DA SITUAÇÃO ATUAL
        # ==================================================

        indice_situacao = 0

        if situacao_atual in situacoes:
            indice_situacao = situacoes.index(
                situacao_atual
            )

        # ==================================================
        # NOVA SITUAÇÃO
        # ==================================================

        nova_situacao = st.selectbox(
            "🚧 Nova Situação da Obra",
            situacoes,
            index=indice_situacao,
            key=f"nova_situacao_{id_obra}"
        )

        # ==================================================
        # MOTIVO DA PARALISAÇÃO
        # ==================================================

        motivo_paralisacao = ""

        if nova_situacao == "4 – Paralisado":

            motivo_paralisacao = st.text_area(
                "📝 Motivo da Paralisação",
                value=(
                    motivo_atual
                    if situacao_atual == "4 – Paralisado"
                    else ""
                ),
                placeholder=(
                    "Informe o motivo da paralisação "
                    "da obra..."
                ),
                key=f"motivo_paralisacao_{id_obra}"
            )

        # ==================================================
        # PUBLICAÇÃO
        # ==================================================

        st.divider()

        st.markdown(
            "### 📰 Dados da Publicação"
        )

        st.caption(
            "Informe os dados da publicação oficial "
            "referente à nova situação da obra."
        )

        col1, col2 = st.columns(2)

        # --------------------------------------------------
        # DATA
        # --------------------------------------------------

        with col1:

            data_publicacao = st.date_input(
                "📅 Data da Publicação",
                value=datetime.now().date(),
                key=f"data_publicacao_{id_obra}"
            )

        # --------------------------------------------------
        # ÓRGÃO
        # --------------------------------------------------

        with col2:

            orgao_publicacao = st.text_input(
                "🏛️ Órgão da Publicação",
                placeholder=(
                    "Ex: Diário Oficial do Município"
                ),
                key=f"orgao_publicacao_{id_obra}"
            )

        # --------------------------------------------------
        # LINK
        # --------------------------------------------------

        link_publicacao = st.text_input(
            "🔗 Link da Publicação",
            placeholder="https://...",
            key=f"link_publicacao_{id_obra}"
        )

        st.divider()

        # ==================================================
        # AVISO DE ENCERRAMENTO
        # ==================================================

        if (
            nova_situacao
            == "7 – Concluído e recebido definitivamente"
        ):

            st.warning(
                "⚠️ ATENÇÃO: ao salvar esta situação, "
                "a obra será considerada definitivamente "
                "encerrada."
            )

            st.info(
                "🔒 Após o recebimento definitivo, "
                "não será possível registrar novas situações "
                "nem novas medições para esta obra."
            )

        # ==================================================
        # SALVAR
        # ==================================================

        if st.button(
            "💾 Salvar Situação",
            type="primary",
            use_container_width=True,
            key=f"salvar_situacao_{id_obra}"
        ):

            # ==================================================
            # VERIFICAR NOVAMENTE A SITUAÇÃO NO BANCO
            # ==================================================

            cursor.execute("""
                SELECT situacao
                FROM obras
                WHERE id = ?
            """, (
                id_obra,
            ))

            resultado_situacao = cursor.fetchone()

            if not resultado_situacao:

                st.error(
                    "❌ Obra não encontrada."
                )
                return

            situacao_banco = resultado_situacao[0]

            if (
                situacao_banco
                == "7 – Concluído e recebido definitivamente"
            ):

                st.error(
                    "🔒 Esta obra já foi concluída e "
                    "recebida definitivamente."
                )

                st.warning(
                    "Não é permitido alterar novamente "
                    "a situação desta obra."
                )

                return

            # ==================================================
            # VALIDAR ALTERAÇÃO
            # ==================================================

            if nova_situacao == situacao_atual:

                st.warning(
                    "⚠️ Selecione uma situação diferente "
                    "da situação atual."
                )
                return

            # ==================================================
            # VALIDAR PARALISAÇÃO
            # ==================================================

            if (
                nova_situacao == "4 – Paralisado"
                and not motivo_paralisacao.strip()
            ):

                st.warning(
                    "⚠️ Informe o motivo da paralisação."
                )
                return

            # ==================================================
            # VALIDAR ÓRGÃO
            # ==================================================

            if not orgao_publicacao.strip():

                st.warning(
                    "⚠️ Informe o órgão da publicação."
                )
                return

            # ==================================================
            # VALIDAR LINK
            # ==================================================

            if not link_publicacao.strip():

                st.warning(
                    "⚠️ Informe o link da publicação."
                )
                return

            if not (
                link_publicacao.strip().startswith("http://")
                or
                link_publicacao.strip().startswith("https://")
            ):

                st.warning(
                    "⚠️ Informe um link válido começando "
                    "com http:// ou https://"
                )
                return

            # ==================================================
            # SALVAR
            # ==================================================

            try:

                # --------------------------------------------------
                # MOTIVO
                # --------------------------------------------------

                motivo_salvar = None

                if nova_situacao == "4 – Paralisado":

                    motivo_salvar = (
                        motivo_paralisacao.strip()
                    )

                # --------------------------------------------------
                # ATUALIZAR SITUAÇÃO ATUAL
                # --------------------------------------------------

                cursor.execute("""
                    UPDATE obras
                    SET
                        situacao = ?,
                        motivo_paralisacao = ?
                    WHERE id = ?
                """, (
                    nova_situacao,
                    motivo_salvar,
                    id_obra
                ))

                # --------------------------------------------------
                # REGISTRAR HISTÓRICO
                # --------------------------------------------------

                cursor.execute("""
                    INSERT INTO historico_situacao_obra (
                        obra_id,
                        situacao,
                        motivo_paralisacao,
                        data_publicacao,
                        orgao_publicacao,
                        link_publicacao,
                        data_registro
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    id_obra,
                    nova_situacao,
                    motivo_salvar,
                    data_publicacao.strftime(
                        "%Y-%m-%d"
                    ),
                    orgao_publicacao.strip(),
                    link_publicacao.strip(),
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                # --------------------------------------------------
                # COMMIT
                # --------------------------------------------------

                conn.commit()

                # --------------------------------------------------
                # SUCESSO
                # --------------------------------------------------

                st.session_state[
                    "situacao_obra_alterada_sucesso"
                ] = True

                st.session_state[
                    "tela_situacao_obra"
                ] = "Principal"

                st.session_state.pop(
                    "situacao_obra_id",
                    None
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"❌ Erro ao atualizar situação: {e}"
                )

    # ==================================================
    # SEGURANÇA
    # ==================================================

    else:

        st.session_state[
            "tela_situacao_obra"
        ] = "Principal"

        st.rerun()
def cadastrar_responsavel():

    st.title("👨‍🔧 Cadastro de Responsável")

    st.caption(
        "Gerencie os profissionais responsáveis pelas obras."
    )

    st.divider()

    # ==========================================
    # ESTADO DA TELA
    # ==========================================

    if "tela_responsavel" not in st.session_state:
        st.session_state["tela_responsavel"] = "Principal"

    tela = st.session_state["tela_responsavel"]

    # ==========================================
    # TELA PRINCIPAL
    # ==========================================

    if tela == "Principal":

        # ==========================================
        # MENSAGENS
        # ==========================================

        if st.session_state.pop(
            "responsavel_cadastrado_sucesso",
            False
        ):
            st.success(
                "✅ Responsável cadastrado com sucesso!"
            )

        if st.session_state.pop(
            "responsavel_alterado_sucesso",
            False
        ):
            st.success(
                "✅ Responsável alterado com sucesso!"
            )

        if st.session_state.pop(
            "responsavel_excluido_sucesso",
            False
        ):
            st.success(
                "✅ Responsável excluído com sucesso!"
            )

        st.markdown(
            "### 🛠️ O que deseja fazer?"
        )

        # ==========================================
        # BOTÕES
        # ==========================================

        col1, col2, col3 = st.columns(3)

        # ==========================================
        # INCLUIR
        # ==========================================

        with col1:

            if st.button(
                "➕ Incluir",
                use_container_width=True,
                type="primary",
                key="btn_incluir_responsavel"
            ):

                st.session_state[
                    "tela_responsavel"
                ] = "Incluir"

                st.rerun()

        # ==========================================
        # LOCALIZAR
        # ==========================================

        with col2:

            if st.button(
                "🔎 Localizar",
                use_container_width=True,
                key="btn_localizar_responsavel"
            ):

                st.session_state[
                    "tela_responsavel"
                ] = "Localizar"

                st.rerun()

        # ==========================================
        # EXCLUIR
        # ==========================================

        with col3:

            if st.button(
                "🗑️ Excluir",
                use_container_width=True,
                key="btn_excluir_responsavel"
            ):

                st.session_state[
                    "tela_responsavel"
                ] = "Excluir"

                st.rerun()

        st.info(
            "Selecione uma opção acima para continuar."
        )

    # ==========================================
    # INCLUIR
    # ==========================================

    elif tela == "Incluir":

        incluir_responsavel()

    # ==========================================
    # LOCALIZAR
    # ==========================================

    elif tela == "Localizar":

        localizar_responsavel()

    # ==========================================
    # ALTERAR
    # Acessado pelo duplo clique no Localizar
    # ==========================================

    elif tela == "Alterar":

        alterar_responsavel()

    # ==========================================
    # EXCLUIR
    # ==========================================

    elif tela == "Excluir":

        excluir_responsavel()

def excluir_responsavel():

    st.subheader("🗑️ Excluir Responsável")

    # ==========================================
    # BOTÃO VOLTAR
    # ==========================================

    if st.button(
        "⬅️ Voltar",
        key="voltar_excluir_responsavel"
    ):
        st.session_state.pop(
            "responsavel_excluir_id",
            None
        )

        st.session_state[
            "tela_responsavel"
        ] = "Principal"

        st.rerun()

    st.divider()

    # ==========================================
    # VERIFICAR SE JÁ FOI SELECIONADO
    # ==========================================

    id_responsavel_excluir = st.session_state.get(
        "responsavel_excluir_id"
    )

    # ==========================================
    # SE AINDA NÃO SELECIONOU
    # MOSTRA A TABELA
    # ==========================================

    if not id_responsavel_excluir:

        busca = st.text_input(
            "🔍 Pesquisar responsável",
            placeholder=(
                "Digite nome, CPF, conselho "
                "ou número do conselho"
            ),
            key="pesquisa_excluir_responsavel"
        )

        # ======================================
        # CONSULTA COM PESQUISA
        # ======================================

        if busca:

            termo = f"%{busca}%"

            cursor.execute("""
                SELECT
                    id,
                    nome,
                    cpf,
                    documento,
                    tipo_responsabilidade,
                    conselho,
                    numero_conselho
                FROM responsaveis
                WHERE (
                    nome LIKE ?
                    OR cpf LIKE ?
                    OR documento LIKE ?
                    OR tipo_responsabilidade LIKE ?
                    OR conselho LIKE ?
                    OR numero_conselho LIKE ?
                )
                ORDER BY nome
            """, (
                termo,
                termo,
                termo,
                termo,
                termo,
                termo
            ))

        else:

            cursor.execute("""
                SELECT
                    id,
                    nome,
                    cpf,
                    documento,
                    tipo_responsabilidade,
                    conselho,
                    numero_conselho
                FROM responsaveis
                ORDER BY nome
            """)

        registros = cursor.fetchall()

        # ======================================
        # SEM REGISTROS
        # ======================================

        if not registros:

            st.info(
                "Nenhum responsável encontrado."
            )

            return

        # ======================================
        # DATAFRAME
        # ======================================

        df = pd.DataFrame(
            registros,
            columns=[
                "ID",
                "Nome",
                "CPF",
                "Documento",
                "Responsabilidade",
                "Conselho",
                "Nº Conselho"
            ]
        )

        # ======================================
        # JAVASCRIPT - DUPLO CLIQUE
        # ======================================

        js_duplo_clique_excluir = JsCode("""
            function(params) {

                if (params.data) {

                    params.api.deselectAll();

                    params.node.setSelected(true);

                }

            }
        """)

        # ======================================
        # CONFIGURAÇÃO DO AGGRID
        # ======================================

        gb = GridOptionsBuilder.from_dataframe(
            df
        )

        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True
        )

        gb.configure_column(
            "ID",
            hide=True
        )

        gb.configure_selection(
            selection_mode="single",
            use_checkbox=False
        )

        grid_options = gb.build()

        grid_options[
            "onRowDoubleClicked"
        ] = js_duplo_clique_excluir

        # ======================================
        # TABELA
        # ======================================

        resposta = AgGrid(
            df,
            gridOptions=grid_options,
            height=350,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            key="grid_excluir_responsavel"
        )

        # ======================================
        # PEGAR DUPLO CLIQUE
        # ======================================

        selecionados = resposta.get(
            "selected_rows",
            []
        )

        if isinstance(
            selecionados,
            pd.DataFrame
        ):
            selecionados = selecionados.to_dict(
                "records"
            )

        # ======================================
        # RESPONSÁVEL SELECIONADO
        # ======================================

        if selecionados:

            selecionado = selecionados[0]

            st.session_state[
                "responsavel_excluir_id"
            ] = int(
                selecionado["ID"]
            )

            st.rerun()

    # ==========================================
    # RESPONSÁVEL FOI SELECIONADO
    # ==========================================

    else:

        cursor.execute("""
            SELECT
                id,
                nome,
                cpf,
                documento,
                tipo_responsabilidade,
                conselho,
                numero_conselho
            FROM responsaveis
            WHERE id = ?
        """, (
            id_responsavel_excluir,
        ))

        responsavel = cursor.fetchone()

        # ======================================
        # NÃO ENCONTROU
        # ======================================

        if not responsavel:

            st.error(
                "❌ Responsável não encontrado."
            )

            st.session_state.pop(
                "responsavel_excluir_id",
                None
            )

            return

        (
            id_responsavel,
            nome,
            cpf,
            documento,
            tipo_responsabilidade,
            conselho,
            numero_conselho
        ) = responsavel

        # ======================================
        # DADOS DO RESPONSÁVEL
        # ======================================

        st.warning(
            "⚠️ Você está prestes a excluir "
            "este responsável."
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"### 👤 {nome}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**CPF:** {cpf}"
                )

                st.write(
                    f"**Documento:** "
                    f"{documento or 'Não informado'}"
                )

                st.write(
                    f"**Responsabilidade:** "
                    f"{tipo_responsabilidade}"
                )

            with col2:

                st.write(
                    f"**Conselho:** "
                    f"{conselho or 'Não informado'}"
                )

                st.write(
                    f"**Nº Conselho:** "
                    f"{numero_conselho or 'Não informado'}"
                )

        st.error(
            "🗑️ A exclusão será permanente."
        )

        # ======================================
        # CONFIRMAÇÃO
        # ======================================

        confirmar = st.checkbox(
            "Confirmo que desejo excluir "
            "permanentemente este responsável.",
            key="confirmar_exclusao_responsavel"
        )

        # ======================================
        # BOTÕES
        # ======================================

        col1, col2 = st.columns(2)

        # ======================================
        # CANCELAR
        # ======================================

        with col1:

            if st.button(
                "❌ Cancelar",
                use_container_width=True,
                key="cancelar_exclusao_responsavel"
            ):

                st.session_state.pop(
                    "responsavel_excluir_id",
                    None
                )

                st.rerun()

        # ======================================
        # SALVAR EXCLUSÃO
        # ======================================

        with col2:

            if st.button(
                "💾 Salvar Exclusão",
                type="primary",
                use_container_width=True,
                disabled=not confirmar,
                key="salvar_exclusao_responsavel"
            ):

                try:

                    cursor.execute("""
                        DELETE FROM responsaveis
                        WHERE id = ?
                    """, (
                        id_responsavel,
                    ))

                    conn.commit()

                    # ==========================
                    # LIMPAR SELEÇÃO
                    # ==========================

                    st.session_state.pop(
                        "responsavel_excluir_id",
                        None
                    )

                    st.session_state.pop(
                        "responsavel_edicao_id",
                        None
                    )

                    # ==========================
                    # MENSAGEM
                    # ==========================

                    st.session_state[
                        "responsavel_excluido_sucesso"
                    ] = True

                    # ==========================
                    # VOLTAR
                    # ==========================

                    st.session_state[
                        "tela_responsavel"
                    ] = "Principal"

                    st.rerun()

                except Exception as e:

                    conn.rollback()

                    st.error(
                        f"❌ Erro ao excluir "
                        f"responsável: {e}"
                    )
def incluir_responsavel():

    st.subheader("➕ Incluir Responsável")

    if st.button(
        "⬅️ Voltar",
        key="voltar_incluir_responsavel"
    ):
        st.session_state[
            "tela_responsavel"
        ] = "Principal"

        st.rerun()

    st.divider()

    # ==========================================
    # FORMULÁRIO
    # ==========================================

    with st.form(
        "form_incluir_responsavel",
        clear_on_submit=True
    ):

        col1, col2 = st.columns(2)

        # ======================================
        # COLUNA 1
        # ======================================

        with col1:

            nome = st.text_input(
                "👤 Nome do Responsável",
                placeholder="Nome completo"
            )

            cpf = st.text_input(
                "🪪 CPF",
                placeholder="000.000.000-00"
            )

            documento = st.text_input(
                "📄 Documento",
                placeholder="RG ou outro documento"
            )

            tipo_vinculo = st.selectbox(
                "🔗 Tipo de Vínculo",
                [
                    "Selecione",
                    "Servidor Efetivo",
                    "Servidor Comissionado",
                    "Contratado",
                    "Terceirizado",
                    "Prestador de Serviço",
                    "Empresa Contratada",
                    "Outro"
                ]
            )

        # ======================================
        # COLUNA 2
        # ======================================

        with col2:

            tipo_responsabilidade = st.selectbox(
                "👷 Tipo de Responsabilidade",
                [
                    "Selecione",
                    "Engenheiro",
                    "Arquiteto",
                    "Técnico",
                    "Fiscal de Obra",
                    "Outro"
                ]
            )

            conselho = st.selectbox(
                "🏛️ Conselho Profissional",
                [
                    "Selecione",
                    "CREA",
                    "CAU",
                    "CFT",
                    "CRT",
                    "Outro"
                ]
            )

            numero_conselho = st.text_input(
                "🔢 Número do Conselho",
                placeholder="Ex: 123456"
            )

        st.divider()

        salvar = st.form_submit_button(
            "💾 Salvar Responsável",
            type="primary",
            use_container_width=True
        )

    # ==========================================
    # SALVAR
    # ==========================================

    if salvar:

        if not nome.strip():

            st.warning(
                "⚠️ Informe o nome do responsável."
            )
            return

        if not cpf.strip():

            st.warning(
                "⚠️ Informe o CPF."
            )
            return

        if tipo_vinculo == "Selecione":

            st.warning(
                "⚠️ Selecione o tipo de vínculo."
            )
            return

        if tipo_responsabilidade == "Selecione":

            st.warning(
                "⚠️ Selecione o tipo de responsabilidade."
            )
            return

        if conselho == "Selecione":

            st.warning(
                "⚠️ Selecione o conselho profissional."
            )
            return

        # ======================================
        # VERIFICAR CPF
        # ======================================

        cursor.execute("""
            SELECT id
            FROM responsaveis
            WHERE cpf = ?
        """, (
            cpf.strip(),
        ))

        cpf_existente = cursor.fetchone()

        if cpf_existente:

            st.warning(
                "⚠️ Já existe um responsável "
                "cadastrado com este CPF."
            )
            return

        # ======================================
        # INSERT
        # ======================================

        try:

            cursor.execute("""
                INSERT INTO responsaveis (
                    nome,
                    cpf,
                    documento,
                    tipo_responsabilidade,
                    tipo_vinculo,
                    conselho,
                    numero_conselho,
                    ativo,
                    data_cadastro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nome.strip(),
                cpf.strip(),
                documento.strip(),
                tipo_responsabilidade,
                tipo_vinculo,
                conselho,
                numero_conselho.strip(),
                1,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))

            conn.commit()

            st.session_state[
                "responsavel_cadastrado_sucesso"
            ] = True

            st.session_state[
                "tela_responsavel"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao cadastrar responsável: {e}"
            )
def localizar_responsavel():

    st.subheader("🔎 Localizar Responsável")

    if st.button(
        "⬅️ Voltar",
        key="voltar_localizar_responsavel"
    ):

        st.session_state.pop(
            "responsavel_edicao_id",
            None
        )

        st.session_state[
            "tela_responsavel"
        ] = "Principal"

        st.rerun()

    st.divider()

    # ==========================================
    # PESQUISA
    # ==========================================

    busca = st.text_input(
        "🔍 Pesquisar",
        placeholder=(
            "Nome, CPF, responsabilidade ou vínculo"
        ),
        key="pesquisa_responsavel"
    )

    if busca:

        termo = f"%{busca}%"

        cursor.execute("""
            SELECT
                id,
                nome,
                cpf,
                tipo_responsabilidade,
                tipo_vinculo,
                conselho,
                numero_conselho
            FROM responsaveis
            WHERE
                ativo = 1
                AND (
                    nome LIKE ?
                    OR cpf LIKE ?
                    OR tipo_responsabilidade LIKE ?
                    OR tipo_vinculo LIKE ?
                )
            ORDER BY nome
        """, (
            termo,
            termo,
            termo,
            termo
        ))

    else:

        cursor.execute("""
            SELECT
                id,
                nome,
                cpf,
                tipo_responsabilidade,
                tipo_vinculo,
                conselho,
                numero_conselho
            FROM responsaveis
            WHERE ativo = 1
            ORDER BY nome
        """)

    registros = cursor.fetchall()

    if not registros:

        st.info(
            "Nenhum responsável encontrado."
        )
        return

    # ==========================================
    # DATAFRAME
    # ==========================================

    df = pd.DataFrame(
        registros,
        columns=[
            "ID",
            "Nome",
            "CPF",
            "Responsabilidade",
            "Vínculo",
            "Conselho",
            "Nº Conselho"
        ]
    )

    # ==========================================
    # DUPLO CLIQUE
    # ==========================================

    js_duplo_clique = JsCode("""
        function(params) {
            if (params.data) {
                params.api.deselectAll();
                params.node.setSelected(true);
            }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(
        df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    gb.configure_column(
        "ID",
        hide=True
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False
    )

    grid_options = gb.build()

    grid_options[
        "suppressRowClickSelection"
    ] = True

    grid_options[
        "onRowDoubleClicked"
    ] = js_duplo_clique

    resposta = AgGrid(
        df,
        gridOptions=grid_options,
        height=350,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="grid_localizar_responsavel"
    )

    selecionados = resposta.get(
        "selected_rows",
        []
    )

    if isinstance(
        selecionados,
        pd.DataFrame
    ):
        selecionados = selecionados.to_dict(
            "records"
        )

    if selecionados:

        selecionado = selecionados[0]

        st.session_state[
            "responsavel_edicao_id"
        ] = int(
            selecionado["ID"]
        )

        st.session_state[
            "tela_responsavel"
        ] = "Alterar"

        st.rerun()

    st.info(
        "👆 Dê dois cliques no responsável para alterar."
    )
def excluir_item_obra():

    st.subheader("🗑️ Excluir Item da Obra")

    # ==========================================
    # PEGAR ITEM SELECIONADO
    # ==========================================

    id_vinculo = st.session_state.get(
        "item_obra_edicao_id"
    )

    if not id_vinculo:

        st.warning(
            "⚠️ Nenhum item selecionado."
        )

        if st.button(
            "⬅️ Voltar",
            use_container_width=True,
            key="voltar_exclusao_sem_item"
        ):

            st.session_state[
                "modo_item_obra"
            ] = "lista"

            st.rerun()

        return

    # ==========================================
    # BUSCAR DADOS DO ITEM
    # ==========================================

    try:

        cursor.execute("""
            SELECT
                io.id,
                io.obra_id,
                i.codigo,
                i.descricao,
                i.unidade,
                io.quantidade,
                io.valor_unitario,
                io.valor_total,
                o.obra,
                o.contrato
            FROM itens_obra io

            INNER JOIN itens i
                ON i.id = io.item_id

            INNER JOIN obras o
                ON o.id = io.obra_id

            WHERE io.id = ?
        """, (
            id_vinculo,
        ))

        registro = cursor.fetchone()

    except Exception as e:

        st.error(
            f"❌ Erro ao carregar item: {e}"
        )

        return

    if not registro:

        st.error(
            "❌ Registro não encontrado."
        )

        return

    # ==========================================
    # DADOS
    # ==========================================

    codigo = registro[2]
    descricao = registro[3]
    unidade = registro[4]

    quantidade = float(
        registro[5] or 0
    )

    valor_unitario = float(
        registro[6] or 0
    )

    valor_total = float(
        registro[7] or 0
    )

    nome_obra = registro[8]
    contrato = registro[9]

    # ==========================================
    # FORMATAR MOEDA
    # ==========================================

    def moeda(valor):

        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    # ==========================================
    # MOSTRAR OBRA
    # ==========================================

    st.markdown(
        "### 🏗️ Obra"
    )

    with st.container(
        border=True
    ):

        st.markdown(
            f"**🏗️ Obra:** {nome_obra}"
        )

        st.markdown(
            f"**📜 Contrato:** "
            f"{contrato or 'Não informado'}"
        )

    # ==========================================
    # MOSTRAR ITEM
    # ==========================================

    st.markdown(
        "### 📦 Item que será excluído"
    )

    with st.container(
        border=True
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"**🔢 Código:** {codigo}"
            )

            st.markdown(
                f"**📝 Descrição:** {descricao}"
            )

            st.markdown(
                f"**📏 Unidade:** {unidade}"
            )

        with col2:

            st.markdown(
                f"**📦 Quantidade:** "
                f"{quantidade}"
            )

            st.markdown(
                f"**💵 Valor Unitário:** "
                f"{moeda(valor_unitario)}"
            )

            st.markdown(
                f"**💰 Valor Total:** "
                f"{moeda(valor_total)}"
            )

    # ==========================================
    # AVISO
    # ==========================================

    st.warning(
        "⚠️ Ao excluir este registro, "
        f"{moeda(valor_total)} será liberado "
        "novamente no saldo da obra."
    )

    st.info(
        "O item continuará no cadastro geral "
        "de itens. Apenas o vínculo deste item "
        "com esta obra será excluído."
    )

    # ==========================================
    # CONFIRMAÇÃO
    # ==========================================

    confirmar = st.checkbox(
        "Confirmo que desejo excluir este item.",
        key=f"confirmar_exclusao_item_{id_vinculo}"
    )

    # ==========================================
    # BOTÕES
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "⬅️ Cancelar",
            use_container_width=True,
            key=f"cancelar_exclusao_{id_vinculo}"
        ):

            st.session_state[
                "modo_item_obra"
            ] = "lista"

            st.session_state.pop(
                "item_obra_edicao_id",
                None
            )

            st.rerun()

    with col2:

        excluir = st.button(
            "🗑️ Excluir Item",
            type="primary",
            use_container_width=True,
            disabled=not confirmar,
            key=f"confirmar_excluir_{id_vinculo}"
        )

    # ==========================================
    # EXCLUIR
    # ==========================================

    if excluir:

        try:

            cursor.execute("""
                DELETE FROM itens_obra
                WHERE id = ?
            """, (
                id_vinculo,
            ))

            conn.commit()

            # ==================================
            # LIMPAR SELEÇÃO
            # ==================================

            st.session_state.pop(
                "item_obra_edicao_id",
                None
            )

            st.session_state[
                "modo_item_obra"
            ] = "lista"

            st.session_state[
                "item_excluido_sucesso"
            ] = True

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao excluir item: {e}"
            )
def alterar_responsavel():

    st.subheader("✏️ Alterar Responsável")

    id_responsavel = st.session_state.get(
        "responsavel_edicao_id"
    )

    if not id_responsavel:

        st.warning(
            "⚠️ Nenhum responsável selecionado."
        )

        st.session_state[
            "tela_responsavel"
        ] = "Localizar"

        return

    if st.button(
        "⬅️ Voltar",
        key="voltar_alterar_responsavel"
    ):

        st.session_state.pop(
            "responsavel_edicao_id",
            None
        )

        st.session_state[
            "tela_responsavel"
        ] = "Localizar"

        st.rerun()

    st.divider()

    # ==========================================
    # BUSCAR RESPONSÁVEL
    # ==========================================

    cursor.execute("""
        SELECT
            nome,
            cpf,
            documento,
            tipo_responsabilidade,
            tipo_vinculo,
            conselho,
            numero_conselho
        FROM responsaveis
        WHERE id = ?
    """, (
        id_responsavel,
    ))

    registro = cursor.fetchone()

    if not registro:

        st.error(
            "❌ Responsável não encontrado."
        )
        return

    nome_atual = registro[0] or ""
    cpf_atual = registro[1] or ""
    documento_atual = registro[2] or ""
    responsabilidade_atual = registro[3] or ""
    vinculo_atual = registro[4] or ""
    conselho_atual = registro[5] or ""
    numero_conselho_atual = registro[6] or ""

    # ==========================================
    # OPÇÕES
    # ==========================================

    tipos_responsabilidade = [
        "Engenheiro",
        "Arquiteto",
        "Técnico",
        "Fiscal de Obra",
        "Outro"
    ]

    tipos_vinculo = [
        "Servidor Efetivo",
        "Servidor Comissionado",
        "Contratado",
        "Terceirizado",
        "Prestador de Serviço",
        "Empresa Contratada",
        "Outro"
    ]

    conselhos = [
        "CREA",
        "CAU",
        "CFT",
        "CRT",
        "Outro"
    ]

    # ==========================================
    # ÍNDICES
    # ==========================================

    indice_responsabilidade = 0

    if responsabilidade_atual in tipos_responsabilidade:
        indice_responsabilidade = (
            tipos_responsabilidade.index(
                responsabilidade_atual
            )
        )

    indice_vinculo = 0

    if vinculo_atual in tipos_vinculo:
        indice_vinculo = tipos_vinculo.index(
            vinculo_atual
        )

    indice_conselho = 0

    if conselho_atual in conselhos:
        indice_conselho = conselhos.index(
            conselho_atual
        )

    # ==========================================
    # FORMULÁRIO
    # ==========================================

    with st.form(
        f"form_alterar_responsavel_{id_responsavel}"
    ):

        col1, col2 = st.columns(2)

        with col1:

            nome = st.text_input(
                "👤 Nome do Responsável",
                value=nome_atual
            )

            cpf = st.text_input(
                "🪪 CPF",
                value=cpf_atual
            )

            documento = st.text_input(
                "📄 Documento",
                value=documento_atual
            )

            tipo_vinculo = st.selectbox(
                "🔗 Tipo de Vínculo",
                tipos_vinculo,
                index=indice_vinculo
            )

        with col2:

            tipo_responsabilidade = st.selectbox(
                "👷 Tipo de Responsabilidade",
                tipos_responsabilidade,
                index=indice_responsabilidade
            )

            conselho = st.selectbox(
                "🏛️ Conselho Profissional",
                conselhos,
                index=indice_conselho
            )

            numero_conselho = st.text_input(
                "🔢 Número do Conselho",
                value=numero_conselho_atual
            )

        st.divider()

        salvar = st.form_submit_button(
            "💾 Salvar Alterações",
            type="primary",
            use_container_width=True
        )

    # ==========================================
    # SALVAR ALTERAÇÃO
    # ==========================================

    if salvar:

        if not nome.strip():

            st.warning(
                "⚠️ Informe o nome do responsável."
            )
            return

        if not cpf.strip():

            st.warning(
                "⚠️ Informe o CPF."
            )
            return

        # ======================================
        # CPF DUPLICADO
        # ======================================

        cursor.execute("""
            SELECT id
            FROM responsaveis
            WHERE
                cpf = ?
                AND id != ?
        """, (
            cpf.strip(),
            id_responsavel
        ))

        cpf_existente = cursor.fetchone()

        if cpf_existente:

            st.warning(
                "⚠️ Já existe outro responsável "
                "com este CPF."
            )
            return

        # ======================================
        # UPDATE
        # ======================================

        try:

            cursor.execute("""
                UPDATE responsaveis
                SET
                    nome = ?,
                    cpf = ?,
                    documento = ?,
                    tipo_responsabilidade = ?,
                    tipo_vinculo = ?,
                    conselho = ?,
                    numero_conselho = ?
                WHERE id = ?
            """, (
                nome.strip(),
                cpf.strip(),
                documento.strip(),
                tipo_responsabilidade,
                tipo_vinculo,
                conselho,
                numero_conselho.strip(),
                id_responsavel
            ))

            conn.commit()

            st.session_state.pop(
                "responsavel_edicao_id",
                None
            )

            st.session_state[
                "responsavel_alterado_sucesso"
            ] = True

            st.session_state[
                "tela_responsavel"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao alterar responsável: {e}"
            )
def alterar_item_obra():

    st.subheader("✏️ Alterar Item da Obra")

    # ==========================================
    # PEGAR ITEM SELECIONADO
    # ==========================================

    id_vinculo = st.session_state.get(
        "item_obra_edicao_id"
    )

    if not id_vinculo:
        st.warning(
            "⚠️ Nenhum item selecionado."
        )

        if st.button(
            "⬅️ Voltar",
            use_container_width=True,
            key="voltar_sem_item"
        ):
            st.session_state[
                "modo_item_obra"
            ] = "lista"

            st.rerun()

        return

    # ==========================================
    # BUSCAR ITEM + OBRA
    # ==========================================

    try:

        cursor.execute("""
            SELECT
                io.id,
                io.obra_id,
                io.item_id,
                i.codigo,
                i.descricao,
                i.unidade,
                i.categoria,
                io.quantidade,
                io.valor_unitario,
                io.valor_total,
                io.observacao,
                o.obra,
                o.contrato,
                o.responsavel,
                o.valor_obra
            FROM itens_obra io

            INNER JOIN itens i
                ON i.id = io.item_id

            INNER JOIN obras o
                ON o.id = io.obra_id

            WHERE io.id = ?
        """, (
            id_vinculo,
        ))

        registro = cursor.fetchone()

    except Exception as e:

        st.error(
            f"❌ Erro ao carregar item: {e}"
        )

        return

    if not registro:

        st.error(
            "❌ Registro não encontrado."
        )

        return

    # ==========================================
    # DADOS
    # ==========================================

    obra_id = registro[1]

    codigo = registro[3]
    descricao = registro[4]
    unidade = registro[5]
    categoria = registro[6]

    quantidade_atual = float(
        registro[7] or 0
    )

    valor_unitario_atual = float(
        registro[8] or 0
    )

    valor_total_atual = float(
        registro[9] or 0
    )

    observacao_atual = (
        registro[10] or ""
    )

    nome_obra = registro[11]
    contrato = registro[12]
    responsavel = registro[13]

    valor_obra = float(
        registro[14] or 0
    )

    # ==========================================
    # MOEDA
    # ==========================================

    def moeda(valor):

        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    # ==========================================
    # CALCULAR OUTROS ITENS
    # ==========================================

    try:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(valor_total),
                    0
                )
            FROM itens_obra

            WHERE obra_id = ?
            AND id <> ?
        """, (
            obra_id,
            id_vinculo
        ))

        valor_outros_itens = float(
            cursor.fetchone()[0] or 0
        )

    except Exception as e:

        st.error(
            f"❌ Erro ao calcular saldo: {e}"
        )

        return

    # Quanto este item pode valer no máximo
    limite_item = (
        valor_obra
        - valor_outros_itens
    )

    # ==========================================
    # INFORMAÇÕES DA OBRA
    # ==========================================

    st.markdown(
        "### 🏗️ Informações da Obra"
    )

    with st.container(border=True):

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"**🏗️ Obra:** {nome_obra}"
            )

            st.markdown(
                f"**📜 Contrato:** "
                f"{contrato or 'Não informado'}"
            )

        with col2:

            st.markdown(
                f"**👤 Responsável:** "
                f"{responsavel or 'Não informado'}"
            )

            st.markdown(
                f"**💰 Valor da Obra:** "
                f"{moeda(valor_obra)}"
            )

    # ==========================================
    # ITEM SELECIONADO
    # ==========================================

    st.markdown(
        "### 📦 Item Selecionado"
    )

    with st.container(border=True):

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"**Código:** {codigo}"
            )

        with col2:

            st.markdown(
                f"**Descrição:** {descricao}"
            )

        with col3:

            st.markdown(
                f"**Unidade:** {unidade}"
            )

    # ==========================================
    # CONTROLE FINANCEIRO
    # ==========================================

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):

            st.caption(
                "VALOR ATUAL"
            )

            st.markdown(
                f"##### "
                f"{moeda(valor_total_atual)}"
            )

    with col2:

        with st.container(border=True):

            st.caption(
                "OUTROS ITENS"
            )

            st.markdown(
                f"##### "
                f"{moeda(valor_outros_itens)}"
            )

    with col3:

        with st.container(border=True):

            st.caption(
                "LIMITE DESTE ITEM"
            )

            st.markdown(
                f"##### "
                f"{moeda(limite_item)}"
            )

    # ==========================================
    # FORMULÁRIO
    # ==========================================

    st.markdown(
        "### ✏️ Alterar Registro"
    )

    with st.form(
        f"form_alterar_item_{id_vinculo}"
    ):

        col1, col2 = st.columns(2)

        with col1:

            nova_quantidade = st.number_input(
                "📦 Quantidade",
                min_value=0.0,
                value=quantidade_atual,
                step=1.0
            )

        with col2:

            novo_valor_unitario = (
                st.number_input(
                    "💵 Valor Unitário (R$)",
                    min_value=0.0,
                    value=valor_unitario_atual,
                    format="%.2f"
                )
            )

        nova_observacao = st.text_area(
            "📝 Observação",
            value=observacao_atual
        )

        salvar = st.form_submit_button(
            "💾 Salvar Alteração",
            type="primary",
            use_container_width=True
        )

    # ==========================================
    # NOVO TOTAL
    # ==========================================

    novo_total = (
        nova_quantidade
        * novo_valor_unitario
    )

    diferenca = (
        novo_total
        - valor_total_atual
    )

    # ==========================================
    # PRÉVIA
    # ==========================================

    st.markdown(
        "### 💰 Resultado da Alteração"
    )

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.caption(
                "NOVO VALOR DO ITEM"
            )

            st.markdown(
                f"##### {moeda(novo_total)}"
            )

    with col2:

        with st.container(border=True):

            if diferenca > 0:

                st.caption(
                    "AUMENTO"
                )

                st.markdown(
                    f"##### + {moeda(diferenca)}"
                )

            elif diferenca < 0:

                st.caption(
                    "REDUÇÃO"
                )

                st.markdown(
                    f"##### - "
                    f"{moeda(abs(diferenca))}"
                )

            else:

                st.caption(
                    "DIFERENÇA"
                )

                st.markdown(
                    "##### R$ 0,00"
                )

    # ==========================================
    # SALVAR
    # ==========================================

    if salvar:

        if nova_quantidade <= 0:

            st.warning(
                "⚠️ Informe uma quantidade "
                "maior que zero."
            )

        elif novo_valor_unitario <= 0:

            st.warning(
                "⚠️ Informe um valor unitário "
                "maior que zero."
            )

        elif novo_total > limite_item:

            st.error(
                "❌ Alteração não permitida. "
                "O novo valor faria os itens "
                "ultrapassarem o valor total "
                "da obra."
            )

        else:

            try:

                cursor.execute("""
                    UPDATE itens_obra

                    SET
                        quantidade = ?,
                        valor_unitario = ?,
                        valor_total = ?,
                        observacao = ?

                    WHERE id = ?
                """, (
                    nova_quantidade,
                    novo_valor_unitario,
                    novo_total,
                    nova_observacao.strip(),
                    id_vinculo
                ))

                conn.commit()

                st.session_state[
                    "item_alterado_sucesso"
                ] = True

                st.session_state[
                    "modo_item_obra"
                ] = "lista"

                st.session_state.pop(
                    "item_obra_edicao_id",
                    None
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"❌ Erro ao alterar item: {e}"
                )

    # ==========================================
    # VOLTAR
    # ==========================================

    if st.button(
        "⬅️ Voltar sem Alterar",
        use_container_width=True,
        key=f"voltar_alteracao_{id_vinculo}"
    ):

        st.session_state[
            "modo_item_obra"
        ] = "lista"

        st.session_state.pop(
            "item_obra_edicao_id",
            None
        )

        st.rerun()
def incluir_item_obra():

    st.subheader("🧱 Itens da Obra")

    # =====================================================
    # CONTROLE DA TELA
    # =====================================================

    if "modo_item_obra" not in st.session_state:
        st.session_state["modo_item_obra"] = "lista"

    # =====================================================
    # ABRIR ALTERAÇÃO
    # =====================================================

    if st.session_state["modo_item_obra"] == "alterar":
        alterar_item_obra()
        return

    # =====================================================
    # ABRIR EXCLUSÃO
    # =====================================================

    if st.session_state["modo_item_obra"] == "excluir":
        excluir_item_obra()
        return

    # =====================================================
    # MENSAGENS
    # =====================================================

    if st.session_state.pop(
        "item_alterado_sucesso",
        False
    ):
        st.success(
            "✅ Item alterado com sucesso!"
        )

    if st.session_state.pop(
        "item_excluido_sucesso",
        False
    ):
        st.success(
            "✅ Item excluído da obra com sucesso!"
        )

    if st.session_state.pop(
        "registro_itens_salvo",
        False
    ):
        st.success(
            "✅ Registro de itens salvo com sucesso!"
        )

    if st.session_state.pop(
        "item_adicionado_temporario",
        False
    ):
        st.success(
            "✅ Item adicionado à lista."
        )

    # =====================================================
    # LISTA TEMPORÁRIA
    # =====================================================

    if "itens_temporarios_obra" not in st.session_state:
        st.session_state["itens_temporarios_obra"] = []

    # =====================================================
    # BUSCAR OBRAS
    # =====================================================

    try:

        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                responsavel,
                valor_obra
            FROM obras
            ORDER BY obra
        """)

        obras = cursor.fetchall()

    except Exception as e:

        st.error(
            f"❌ Erro ao carregar obras: {e}"
        )
        return

    if not obras:

        st.warning(
            "⚠️ Nenhuma obra cadastrada."
        )
        return

    # =====================================================
    # SELEÇÃO DA OBRA
    # =====================================================

    opcoes_obras = {}

    for registro in obras:

        id_obra = registro[0]
        nome_obra_lista = registro[1]
        contrato_lista = registro[2]

        texto = (
            f"{id_obra} - {nome_obra_lista} | "
            f"Contrato: "
            f"{contrato_lista or 'Não informado'}"
        )

        opcoes_obras[texto] = id_obra

    obra_escolhida = st.selectbox(
        "🏗️ Selecione a Obra",
        list(opcoes_obras.keys()),
        key="item_obra_selecionada"
    )

    obra_id = opcoes_obras[
        obra_escolhida
    ]

    # =====================================================
    # CONTROLE DE TROCA DE OBRA
    # =====================================================

    obra_anterior = st.session_state.get(
        "obra_itens_anterior"
    )

    if (
        obra_anterior is not None
        and obra_anterior != obra_id
    ):

        st.session_state[
            "itens_temporarios_obra"
        ] = []

        st.session_state.pop(
            "item_obra_edicao_id",
            None
        )

    st.session_state[
        "obra_itens_anterior"
    ] = obra_id

    # =====================================================
    # BUSCAR DADOS DA OBRA
    # =====================================================

    try:

        cursor.execute("""
            SELECT
                obra,
                contrato,
                responsavel,
                valor_obra
            FROM obras
            WHERE id = ?
        """, (
            obra_id,
        ))

        dados_obra = cursor.fetchone()

    except Exception as e:

        st.error(
            f"❌ Erro ao carregar obra: {e}"
        )
        return

    if not dados_obra:

        st.error(
            "❌ Obra não encontrada."
        )
        return

    nome_obra = dados_obra[0]
    contrato = dados_obra[1]
    responsavel = dados_obra[2]

    valor_obra = float(
        dados_obra[3] or 0
    )

    # =====================================================
    # FORMATAÇÃO DE MOEDA
    # =====================================================

    def moeda(valor):

        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    # =====================================================
    # VALOR UTILIZADO
    # =====================================================

    try:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(valor_total),
                    0
                )
            FROM itens_obra
            WHERE obra_id = ?
        """, (
            obra_id,
        ))

        valor_utilizado = float(
            cursor.fetchone()[0] or 0
        )

    except Exception as e:

        st.error(
            f"❌ Erro ao calcular itens: {e}"
        )
        return

    saldo_disponivel = (
        valor_obra - valor_utilizado
    )

    # =====================================================
    # INFORMAÇÕES DA OBRA
    # =====================================================

    st.markdown(
        "### 🏗️ Informações da Obra"
    )

    with st.container(border=True):

        col_info1, col_info2 = st.columns(2)

        with col_info1:

            st.markdown(
                f"**🏗️ Obra:** {nome_obra}"
            )

            st.markdown(
                f"**📜 Contrato:** "
                f"{contrato or 'Não informado'}"
            )

        with col_info2:

            st.markdown(
                f"**👤 Responsável:** "
                f"{responsavel or 'Não informado'}"
            )

            st.markdown(
                f"**💰 Valor da Obra:** "
                f"{moeda(valor_obra)}"
            )

    # =====================================================
    # CONTROLE FINANCEIRO
    # =====================================================

    st.markdown(
        "### 💰 Controle dos Itens"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):

            st.caption(
                "💰 VALOR DA OBRA"
            )

            st.markdown(
                f"##### {moeda(valor_obra)}"
            )

    with col2:

        with st.container(border=True):

            st.caption(
                "📦 VALOR REGISTRADO"
            )

            st.markdown(
                f"##### {moeda(valor_utilizado)}"
            )

    with col3:

        with st.container(border=True):

            st.caption(
                "💵 SALDO DISPONÍVEL"
            )

            st.markdown(
                f"##### {moeda(saldo_disponivel)}"
            )

    st.markdown("---")

    # =====================================================
    # PRÓXIMO CÓDIGO
    # =====================================================

    # =====================================================
    # PRÓXIMO CÓDIGO DISPONÍVEL
    # =====================================================

    try:

        # Pega os códigos que realmente estão sendo
        # utilizados em itens vinculados às obras.
        cursor.execute("""
            SELECT DISTINCT
                i.codigo
            FROM itens i

            INNER JOIN itens_obra io
                ON io.item_id = i.id

            WHERE i.codigo LIKE 'ITEM%'
        """)

        codigos_usados = {
            registro[0]
            for registro in cursor.fetchall()
        }

        # Também considera os itens que foram adicionados
        # temporariamente e ainda não foram salvos.
        for item in st.session_state[
            "itens_temporarios_obra"
        ]:

            codigo_temp = item.get(
                "codigo_visual"
            )

            if codigo_temp:
                codigos_usados.add(
                    codigo_temp
                )

        # Procura o primeiro código livre:
        # ITEM00001, ITEM00002, ITEM00003...
        numero = 1

        while True:

            codigo_teste = (
                f"ITEM{numero:05d}"
            )

            if codigo_teste not in codigos_usados:

                codigo_visual = (
                    codigo_teste
                )

                break

            numero += 1

    except Exception:

        codigo_visual = "ITEM00001"

    # =====================================================
    # NOVO ITEM
    # =====================================================

    st.markdown(
        "### 📦 Novo Item"
    )

    with st.form(
        f"form_adicionar_item_obra_{obra_id}",
        clear_on_submit=True
    ):

        col1, col2 = st.columns(
            [1, 3]
        )

        with col1:

            st.text_input(
                "🔢 Código",
                value=codigo_visual,
                disabled=True
            )

        with col2:

            descricao = st.text_input(
                "📝 Descrição",
                placeholder="Ex: Areia lavada"
            )

        col3, col4 = st.columns(2)

        with col3:

            unidade = st.selectbox(
                "📏 Unidade",
                [
                    "UN",
                    "M",
                    "M²",
                    "M³",
                    "KG",
                    "T",
                    "L",
                    "SC",
                    "CX",
                    "PCT",
                    "H",
                    "VB"
                ]
            )

        with col4:

            categoria = st.selectbox(
                "📂 Categoria",
                [
                    "Material",
                    "Serviço",
                    "Equipamento",
                    "Mão de Obra",
                    "Outros"
                ]
            )

        col5, col6 = st.columns(2)

        with col5:

            quantidade = st.number_input(
                "📦 Quantidade",
                min_value=0.0,
                step=1.0
            )

        with col6:

            valor_unitario = st.number_input(
                "💵 Valor Unitário (R$)",
                min_value=0.0,
                format="%.2f"
            )

        observacao = st.text_area(
            "📝 Observação",
            placeholder=(
                "Informações adicionais "
                "sobre o item..."
            )
        )

        adicionar_item = (
            st.form_submit_button(
                "➕ Adicionar Item",
                type="primary",
                use_container_width=True
            )
        )

    # =====================================================
    # ADICIONAR ITEM À LISTA
    # =====================================================

    if adicionar_item:

        valor_total_item = (
            quantidade
            * valor_unitario
        )

        if not descricao.strip():

            st.warning(
                "⚠️ Informe a descrição do item."
            )

        elif quantidade <= 0:

            st.warning(
                "⚠️ Informe uma quantidade "
                "maior que zero."
            )

        elif valor_unitario <= 0:

            st.warning(
                "⚠️ Informe o valor unitário."
            )

        else:

            total_temporario = sum(
                float(item["valor_total"])
                for item
                in st.session_state[
                    "itens_temporarios_obra"
                ]
            )

            total_com_novo = (
                total_temporario
                + valor_total_item
            )

            if (
                total_com_novo
                > saldo_disponivel
            ):

                excedente = (
                    total_com_novo
                    - saldo_disponivel
                )

                st.error(
                    "❌ Item não adicionado. "
                    "O valor ultrapassaria "
                    "o saldo da obra em "
                    f"{moeda(excedente)}."
                )

            else:

                novo_item = {
                    "codigo_visual": codigo_visual,
                    "descricao": descricao.strip(),
                    "unidade": unidade,
                    "categoria": categoria,
                    "quantidade": quantidade,
                    "valor_unitario": valor_unitario,
                    "valor_total": valor_total_item,
                    "observacao": observacao.strip()
                }

                st.session_state[
                    "itens_temporarios_obra"
                ].append(
                    novo_item
                )

                st.session_state[
                    "item_adicionado_temporario"
                ] = True

                st.rerun()

    # =====================================================
    # ITENS PARA REGISTRAR
    # =====================================================

    itens_temporarios = (
        st.session_state[
            "itens_temporarios_obra"
        ]
    )

    if itens_temporarios:

        st.markdown("---")

        st.subheader(
            "📝 Itens para Registrar"
        )

        dados_temporarios = []

        for numero, item in enumerate(
            itens_temporarios,
            start=1
        ):

            dados_temporarios.append({
                "Nº": numero,
                "Código": item[
                    "codigo_visual"
                ],
                "Descrição": item[
                    "descricao"
                ],
                "Unidade": item[
                    "unidade"
                ],
                "Quantidade": item[
                    "quantidade"
                ],
                "Valor Unitário": moeda(
                    item[
                        "valor_unitario"
                    ]
                ),
                "Valor Total": moeda(
                    item[
                        "valor_total"
                    ]
                )
            })

        df_temporarios = pd.DataFrame(
            dados_temporarios
        )

        st.dataframe(
            df_temporarios,
            use_container_width=True,
            hide_index=True
        )

        total_temporario = sum(
            float(item["valor_total"])
            for item
            in itens_temporarios
        )

        saldo_apos_registro = (
            saldo_disponivel
            - total_temporario
        )

        col1, col2 = st.columns(2)

        with col1:

            with st.container(border=True):

                st.caption(
                    "📦 TOTAL DESTE REGISTRO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(total_temporario)}"
                )

        with col2:

            with st.container(border=True):

                st.caption(
                    "💰 SALDO APÓS REGISTRO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(saldo_apos_registro)}"
                )

        # =================================================
        # BOTÕES TEMPORÁRIOS
        # =================================================

        col1, col2 = st.columns(
            [1, 2]
        )

        with col1:

            if st.button(
                "↩️ Remover Último",
                use_container_width=True,
                key=f"remover_ultimo_item_{obra_id}"
            ):

                st.session_state[
                    "itens_temporarios_obra"
                ].pop()

                st.rerun()

        with col2:

            salvar_registro = st.button(
                "💾 Salvar Registro",
                type="primary",
                use_container_width=True,
                key=f"salvar_registro_{obra_id}"
            )

        # =================================================
        # SALVAR REGISTRO
        # =================================================

        if salvar_registro:

            try:

                # Recalcula o saldo
                cursor.execute("""
                    SELECT
                        COALESCE(
                            SUM(valor_total),
                            0
                        )
                    FROM itens_obra
                    WHERE obra_id = ?
                """, (
                    obra_id,
                ))

                utilizado_atual = float(
                    cursor.fetchone()[0] or 0
                )

                saldo_atual = (
                    valor_obra
                    - utilizado_atual
                )

                total_registro = sum(
                    float(item["valor_total"])
                    for item
                    in itens_temporarios
                )

                if (
                    total_registro
                    > saldo_atual
                ):

                    st.error(
                        "❌ Registro não salvo. "
                        "O valor ultrapassa "
                        "o saldo disponível."
                    )

                else:

                    for item in itens_temporarios:

                        descricao_item = (
                            item["descricao"]
                        )

                        unidade_item = (
                            item["unidade"]
                        )

                        categoria_item = (
                            item["categoria"]
                        )

                        # =================================
                        # PROCURAR ITEM EXISTENTE
                        # =================================

                        cursor.execute("""
                            SELECT id
                            FROM itens
                            WHERE
                                LOWER(descricao)
                                = LOWER(?)
                            AND unidade = ?
                        """, (
                            descricao_item,
                            unidade_item
                        ))

                        item_existente = (
                            cursor.fetchone()
                        )

                        if item_existente:

                            item_id = (
                                item_existente[0]
                            )

                        else:

                            # =============================
                            # GERAR PRIMEIRO CÓDIGO LIVRE
                            # =============================

                            numero_item = 1

                            while True:

                                codigo_item = (
                                    f"ITEM{numero_item:05d}"
                                )

                                cursor.execute("""
                                    SELECT id
                                    FROM itens
                                    WHERE codigo = ?
                                """, (
                                    codigo_item,
                                ))

                                codigo_existente = (
                                    cursor.fetchone()
                                )

                                if not codigo_existente:
                                    break

                                numero_item += 1

                            cursor.execute("""
                                INSERT INTO itens (
                                    codigo,
                                    descricao,
                                    unidade,
                                    categoria,
                                    observacao,
                                    ativo,
                                    data_cadastro
                                )
                                VALUES (
                                    ?, ?, ?, ?, ?, ?, ?
                                )
                            """, (
                                codigo_item,
                                descricao_item,
                                unidade_item,
                                categoria_item,
                                item[
                                    "observacao"
                                ],
                                1,
                                datetime.now().strftime(
                                    "%Y-%m-%d"
                                )
                            ))

                            item_id = (
                                cursor.lastrowid
                            )

                        # =================================
                        # VINCULAR ITEM À OBRA
                        # =================================

                        cursor.execute("""
                            INSERT INTO itens_obra (
                                obra_id,
                                item_id,
                                quantidade,
                                valor_unitario,
                                valor_total,
                                observacao
                            )
                            VALUES (
                                ?, ?, ?, ?, ?, ?
                            )
                        """, (
                            obra_id,
                            item_id,
                            item[
                                "quantidade"
                            ],
                            item[
                                "valor_unitario"
                            ],
                            item[
                                "valor_total"
                            ],
                            item[
                                "observacao"
                            ]
                        ))

                    conn.commit()

                    st.session_state[
                        "itens_temporarios_obra"
                    ] = []

                    # IMPORTANTE:
                    # não deixa um ID antigo selecionado
                    st.session_state.pop(
                        "item_obra_edicao_id",
                        None
                    )

                    st.session_state[
                        "registro_itens_salvo"
                    ] = True

                    st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"❌ Erro ao salvar "
                    f"registro: {e}"
                )

    # =====================================================
    # ITENS REGISTRADOS NA OBRA
    # =====================================================

    st.markdown("---")

    st.subheader(
        "📋 Itens Registrados na Obra"
    )

    try:

        cursor.execute("""
            SELECT
                io.id AS id_vinculo,
                i.codigo,
                i.descricao,
                i.unidade,
                io.quantidade,
                io.valor_unitario,
                io.valor_total
            FROM itens_obra io

            INNER JOIN itens i
                ON i.id = io.item_id

            WHERE io.obra_id = ?

            ORDER BY
                i.descricao
        """, (
            obra_id,
        ))

        itens_registrados = (
            cursor.fetchall()
        )

    except Exception as e:

        st.error(
            f"❌ Erro ao carregar "
            f"itens registrados: {e}"
        )

        itens_registrados = []

    # =====================================================
    # MOSTRAR GRID
    # =====================================================

    if itens_registrados:

        df_registrados = pd.DataFrame(
            itens_registrados,
            columns=[
                "ID_VINCULO",
                "Código",
                "Descrição",
                "Unidade",
                "Quantidade",
                "Valor Unitário",
                "Valor Total"
            ]
        )

        # =================================================
        # CONFIGURAR GRID
        # =================================================

        gb = GridOptionsBuilder.from_dataframe(
            df_registrados
        )

        gb.configure_default_column(
            resizable=True,
            sortable=True,
            filter=True
        )

        gb.configure_selection(
            selection_mode="single",
            use_checkbox=False
        )

        # ID real de itens_obra
        gb.configure_column(
            "ID_VINCULO",
            hide=True
        )

        gb.configure_column(
            "Valor Unitário",
            valueFormatter=(
                "'R$ ' + "
                "Number(params.value)"
                ".toLocaleString("
                "'pt-BR', "
                "{minimumFractionDigits: 2, "
                "maximumFractionDigits: 2}"
                ")"
            )
        )

        gb.configure_column(
            "Valor Total",
            valueFormatter=(
                "'R$ ' + "
                "Number(params.value)"
                ".toLocaleString("
                "'pt-BR', "
                "{minimumFractionDigits: 2, "
                "maximumFractionDigits: 2}"
                ")"
            )
        )

        # =================================================
        # DUPLO CLIQUE
        # =================================================

        duplo_clique = JsCode("""
            function(params) {
                params.node.setSelected(true);
            }
        """)

        gb.configure_grid_options(
            onRowDoubleClicked=duplo_clique
        )

        grid_options = (
            gb.build()
        )

        resposta_grid = AgGrid(
            df_registrados,
            gridOptions=grid_options,
            update_mode=(
                GridUpdateMode.SELECTION_CHANGED
            ),
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            height=300,
            key=f"grid_itens_obra_{obra_id}"
        )

        # =================================================
        # PEGAR SELEÇÃO ATUAL
        # =================================================

        selecionado = resposta_grid.get(
            "selected_rows"
        )

        id_selecionado = None

        if selecionado is not None:

            # =============================================
            # AGGRID RETORNOU DATAFRAME
            # =============================================

            if isinstance(
                selecionado,
                pd.DataFrame
            ):

                if not selecionado.empty:

                    linha = (
                        selecionado.iloc[0]
                    )

                    if "ID_VINCULO" in linha:

                        id_selecionado = int(
                            linha[
                                "ID_VINCULO"
                            ]
                        )

            # =============================================
            # AGGRID RETORNOU LISTA
            # =============================================

            elif isinstance(
                selecionado,
                list
            ):

                if len(selecionado) > 0:

                    linha = selecionado[0]

                    if (
                        "ID_VINCULO"
                        in linha
                    ):

                        id_selecionado = int(
                            linha[
                                "ID_VINCULO"
                            ]
                        )

        # =================================================
        # VALIDAR O ID ANTES DE GUARDAR
        # =================================================

        if id_selecionado is not None:

            cursor.execute("""
                SELECT id
                FROM itens_obra
                WHERE id = ?
                AND obra_id = ?
            """, (
                id_selecionado,
                obra_id
            ))

            registro_valido = (
                cursor.fetchone()
            )

            if registro_valido:

                st.session_state[
                    "item_obra_edicao_id"
                ] = id_selecionado

            else:

                st.session_state.pop(
                    "item_obra_edicao_id",
                    None
                )

        # =================================================
        # VERIFICAR SE EXISTE SELEÇÃO ANTIGA
        # =================================================

        item_selecionado_id = (
            st.session_state.get(
                "item_obra_edicao_id"
            )
        )

        item_selecionado = None

        if item_selecionado_id:

            cursor.execute("""
                SELECT
                    io.id,
                    i.descricao
                FROM itens_obra io

                INNER JOIN itens i
                    ON i.id = io.item_id

                WHERE io.id = ?
                AND io.obra_id = ?
            """, (
                item_selecionado_id,
                obra_id
            ))

            item_selecionado = (
                cursor.fetchone()
            )

            # Se o ID não existe mais,
            # remove da sessão.
            if not item_selecionado:

                st.session_state.pop(
                    "item_obra_edicao_id",
                    None
                )

                item_selecionado_id = None

        # =================================================
        # ALTERAR / EXCLUIR
        # =================================================

        if (
            item_selecionado_id
            and item_selecionado
        ):

            nome_item = (
                item_selecionado[1]
            )

            st.info(
                f"📦 Item selecionado: "
                f"**{nome_item}**"
            )

            col_alterar, col_excluir = (
                st.columns(2)
            )

            # =============================================
            # ALTERAR
            # =============================================

            with col_alterar:

                if st.button(
                    "✏️ Alterar Item",
                    type="primary",
                    use_container_width=True,
                    key=(
                        f"alterar_item_"
                        f"{item_selecionado_id}"
                    )
                ):

                    # Valida novamente antes
                    # de abrir alteração.
                    cursor.execute("""
                        SELECT id
                        FROM itens_obra
                        WHERE id = ?
                        AND obra_id = ?
                    """, (
                        item_selecionado_id,
                        obra_id
                    ))

                    if cursor.fetchone():

                        st.session_state[
                            "item_obra_edicao_id"
                        ] = (
                            item_selecionado_id
                        )

                        st.session_state[
                            "modo_item_obra"
                        ] = "alterar"

                        st.rerun()

                    else:

                        st.session_state.pop(
                            "item_obra_edicao_id",
                            None
                        )

                        st.error(
                            "❌ Este registro "
                            "não existe mais."
                        )

            # =============================================
            # EXCLUIR
            # =============================================

            with col_excluir:

                if st.button(
                    "🗑️ Excluir Item",
                    use_container_width=True,
                    key=(
                        f"excluir_item_"
                        f"{item_selecionado_id}"
                    )
                ):

                    # Valida novamente antes
                    # de abrir exclusão.
                    cursor.execute("""
                        SELECT id
                        FROM itens_obra
                        WHERE id = ?
                        AND obra_id = ?
                    """, (
                        item_selecionado_id,
                        obra_id
                    ))

                    if cursor.fetchone():

                        st.session_state[
                            "item_obra_edicao_id"
                        ] = (
                            item_selecionado_id
                        )

                        st.session_state[
                            "modo_item_obra"
                        ] = "excluir"

                        st.rerun()

                    else:

                        st.session_state.pop(
                            "item_obra_edicao_id",
                            None
                        )

                        st.error(
                            "❌ Este registro "
                            "não existe mais."
                        )

        else:

            st.caption(
                "👆 Selecione um item na tabela "
                "para alterar ou excluir."
            )

        # =================================================
        # TOTAL REGISTRADO
        # =================================================

        total_registrado = sum(
            float(
                registro[6] or 0
            )
            for registro
            in itens_registrados
        )

        saldo_final = (
            valor_obra
            - total_registrado
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            with st.container(border=True):

                st.caption(
                    "📦 TOTAL REGISTRADO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(total_registrado)}"
                )

        with col2:

            with st.container(border=True):

                st.caption(
                    "💰 SALDO DA OBRA"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(saldo_final)}"
                )

    else:

        st.info(
            "Nenhum item registrado "
            "nesta obra."
        )

        st.session_state.pop(
            "item_obra_edicao_id",
            None
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

    # ==========================================
    # TELA PADRÃO
    # ==========================================

    if "tela_obras" not in st.session_state:
        st.session_state["tela_obras"] = "Principal"

    # ==========================================
    # BOTÕES
    # ==========================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        if st.button(
            "➕ Incluir",
            use_container_width=True,
            key="btn_incluir_obra"
        ):

            st.session_state["tela_obras"] = "Incluir"

            st.rerun()

    with col2:

        if st.button(
            "🔎 Localizar",
            use_container_width=True,
            key="btn_localizar_obra"
        ):

            st.session_state["tela_obras"] = "Localizar"

            # Limpa seleção anterior
            st.session_state.pop(
                "obra_selecionada_localizar",
                None
            )

            st.rerun()

    with col3:

        if st.button(
            "🖨️ Imprimir",
            use_container_width=True,
            key="btn_imprimir_obra"
        ):

            st.session_state["tela_obras"] = "Imprimir"

            st.rerun()
    with col4:

        if st.button(
            "🧱 Itens",
            use_container_width=True,
            key="btn_itens_obra"
        ):

            st.session_state["tela_obras"] = "Itens"

            st.rerun()
    st.markdown("---")

    # ==========================================
    # QUAL TELA MOSTRAR
    # ==========================================

    # ==========================================
    # QUAL TELA MOSTRAR
    # ==========================================

    tela = st.session_state.get(
        "tela_obras",
        "Principal"
    )

    # ==========================================
    # PRINCIPAL
    # ==========================================

    if tela == "Principal":

        if st.session_state.get(
            "obra_cadastrada_sucesso",
            False
        ):
            st.success(
                "✅ Obra cadastrada com sucesso!"
            )

            st.session_state[
                "obra_cadastrada_sucesso"
            ] = False

        else:
            st.info(
                "Selecione uma opção acima para continuar."
            )

    # ==========================================
    # INCLUIR
    # ==========================================

    elif tela == "Incluir":
        incluir_obra()

    # ==========================================
    # LOCALIZAR
    # ==========================================

    elif tela == "Localizar":
        localizar_obra()

    # ==========================================
    # IMPRIMIR
    # ==========================================

    elif tela == "Imprimir":
        imprimir_obra()

    # ==========================================
    # ALTERAR
    # ==========================================

    elif tela == "AlterarInterno":
        alterar_obra()
		
    elif tela == "Itens":
        incluir_item_obra()

def incluir_obra():

    # ==================================================
    # CONTROLE DO CADASTRO
    # ==================================================

    if "cadastro_obra_id" not in st.session_state:
        st.session_state["cadastro_obra_id"] = 0

    cadastro_id = st.session_state["cadastro_obra_id"]

    # ==================================================
    # ESTADOS TEMPORÁRIOS
    # ==================================================

    if (
        st.session_state.get(
            "responsaveis_temp_obra_cadastro_id"
        ) != cadastro_id
    ):
        st.session_state["responsaveis_temp_obra"] = []
        st.session_state[
            "responsaveis_temp_obra_cadastro_id"
        ] = cadastro_id
        st.session_state[
            "responsaveis_confirmados_obra"
        ] = False
        st.session_state.pop(
            "responsavel_temp_edicao_indice",
            None
        )

    if "responsaveis_temp_obra" not in st.session_state:
        st.session_state["responsaveis_temp_obra"] = []

    if "responsaveis_confirmados_obra" not in st.session_state:
        st.session_state["responsaveis_confirmados_obra"] = False

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

        numero = st.text_input(
            "🔢 Número",
            placeholder="Ex: 125",
            key=f"numero_{cadastro_id}"
        )

        bairro = st.text_input(
            "🏘️ Bairro",
            placeholder="Ex: Centro",
            key=f"bairro_{cadastro_id}"
        )

    with col2:

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

        data_entrega = (
            data_inicio
            + timedelta(days=prazo)
        )

        st.info(
            f"📅 Previsão de entrega: "
            f"{data_entrega.strftime('%d/%m/%Y')}"
        )

    # ==================================================
    # RESPONSÁVEIS / ART
    # ==================================================

    st.divider()

    st.subheader("👷 Responsáveis / ART")

    responsaveis_confirmados = st.session_state.get(
        "responsaveis_confirmados_obra",
        False
    )

    indice_edicao = st.session_state.get(
        "responsavel_temp_edicao_indice"
    )

    # ==================================================
    # BUSCAR RESPONSÁVEIS
    # ==================================================

    cursor.execute("""
        SELECT
            id,
            nome,
            tipo_responsabilidade,
            tipo_vinculo
        FROM responsaveis
        WHERE ativo = 1
        ORDER BY nome
    """)

    responsaveis_cadastrados = cursor.fetchall()

    opcoes_responsaveis = {
        "Selecione o responsável": {
            "id": None,
            "nome": "",
            "tipo_responsabilidade": "",
            "tipo_vinculo": ""
        }
    }

    for registro in responsaveis_cadastrados:

        id_responsavel = registro[0]
        nome_responsavel = registro[1]

        opcoes_responsaveis[nome_responsavel] = {
            "id": id_responsavel,
            "nome": nome_responsavel,
            "tipo_responsabilidade": (
                registro[2] or ""
            ),
            "tipo_vinculo": (
                registro[3] or ""
            )
        }

    # ==================================================
    # MODO DE EDIÇÃO DO RESPONSÁVEL
    # ==================================================

    if (
        responsaveis_confirmados
        and indice_edicao is not None
    ):

        responsaveis_temp = st.session_state[
            "responsaveis_temp_obra"
        ]

        if (
            indice_edicao < 0
            or indice_edicao >= len(responsaveis_temp)
        ):
            st.session_state.pop(
                "responsavel_temp_edicao_indice",
                None
            )
            st.rerun()

        item_edicao = responsaveis_temp[
            indice_edicao
        ]

        st.markdown(
            "### ✏️ Alterar Responsável da Obra"
        )

        st.info(
            "Altere os dados da ART deste responsável."
        )

        # ==================================================
        # DADOS BLOQUEADOS
        # ==================================================

        st.text_input(
            "👤 Responsável",
            value=item_edicao["nome"],
            disabled=True,
            key=(
                f"editar_nome_responsavel_"
                f"{cadastro_id}_"
                f"{indice_edicao}"
            )
        )

        col_ed1, col_ed2 = st.columns(2)

        with col_ed1:

            st.text_input(
                "👷 Tipo de Responsabilidade",
                value=item_edicao[
                    "tipo_responsabilidade"
                ],
                disabled=True,
                key=(
                    f"editar_responsabilidade_"
                    f"{cadastro_id}_"
                    f"{indice_edicao}"
                )
            )

        with col_ed2:

            st.text_input(
                "🔗 Tipo de Vínculo",
                value=item_edicao[
                    "tipo_vinculo"
                ],
                disabled=True,
                key=(
                    f"editar_vinculo_"
                    f"{cadastro_id}_"
                    f"{indice_edicao}"
                )
            )

        # ==================================================
        # ART EDITÁVEL
        # ==================================================

        col_art_ed1, col_art_ed2 = st.columns(2)

        with col_art_ed1:

            numero_art_edicao = st.text_input(
                "📜 Número da ART",
                value=item_edicao["numero_art"],
                key=(
                    f"editar_numero_art_"
                    f"{cadastro_id}_"
                    f"{indice_edicao}"
                )
            )

        with col_art_ed2:

            tipos_art = [
                "Fiscalização",
                "Execução",
                "Projeto"
            ]

            tipo_art_atual = item_edicao[
                "tipo_art"
            ]

            if tipo_art_atual in tipos_art:
                indice_tipo_art = tipos_art.index(
                    tipo_art_atual
                )
            else:
                indice_tipo_art = 0

            tipo_art_edicao = st.selectbox(
                "🏗️ Tipo da ART",
                tipos_art,
                index=indice_tipo_art,
                key=(
                    f"editar_tipo_art_"
                    f"{cadastro_id}_"
                    f"{indice_edicao}"
                )
            )

        # ==================================================
        # DATAS
        # ==================================================

        try:
            data_inicio_art_atual = (
                datetime.strptime(
                    item_edicao[
                        "data_inicio_art"
                    ],
                    "%Y-%m-%d"
                ).date()
            )
        except Exception:
            data_inicio_art_atual = (
                datetime.now().date()
            )

        try:
            data_final_art_atual = (
                datetime.strptime(
                    item_edicao[
                        "data_final_art"
                    ],
                    "%Y-%m-%d"
                ).date()
            )
        except Exception:
            data_final_art_atual = (
                datetime.now().date()
            )

        col_data_ed1, col_data_ed2 = (
            st.columns(2)
        )

        with col_data_ed1:

            data_inicio_art_edicao = (
                st.date_input(
                    "📅 Data Inicial da ART",
                    value=data_inicio_art_atual,
                    key=(
                        f"editar_inicio_art_"
                        f"{cadastro_id}_"
                        f"{indice_edicao}"
                    )
                )
            )

        with col_data_ed2:

            data_final_art_edicao = (
                st.date_input(
                    "📅 Data Final da ART",
                    value=data_final_art_atual,
                    key=(
                        f"editar_final_art_"
                        f"{cadastro_id}_"
                        f"{indice_edicao}"
                    )
                )
            )

        # ==================================================
        # BOTÕES
        # ==================================================

        col_cancelar, col_salvar_edicao = (
            st.columns(2)
        )

        with col_cancelar:

            if st.button(
                "↩️ Cancelar",
                use_container_width=True,
                key=(
                    f"cancelar_edicao_responsavel_"
                    f"{cadastro_id}"
                )
            ):

                st.session_state.pop(
                    "responsavel_temp_edicao_indice",
                    None
                )

                st.rerun()

        with col_salvar_edicao:

            if st.button(
                "💾 Salvar Alteração",
                type="primary",
                use_container_width=True,
                key=(
                    f"salvar_edicao_responsavel_"
                    f"{cadastro_id}"
                )
            ):

                if not numero_art_edicao.strip():

                    st.warning(
                        "⚠️ Informe o número da ART."
                    )

                elif (
                    data_final_art_edicao
                    < data_inicio_art_edicao
                ):

                    st.warning(
                        "⚠️ A data final da ART não pode "
                        "ser anterior à data inicial."
                    )

                else:

                    st.session_state[
                        "responsaveis_temp_obra"
                    ][indice_edicao][
                        "numero_art"
                    ] = numero_art_edicao.strip()

                    st.session_state[
                        "responsaveis_temp_obra"
                    ][indice_edicao][
                        "tipo_art"
                    ] = tipo_art_edicao

                    st.session_state[
                        "responsaveis_temp_obra"
                    ][indice_edicao][
                        "data_inicio_art"
                    ] = (
                        data_inicio_art_edicao.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    st.session_state[
                        "responsaveis_temp_obra"
                    ][indice_edicao][
                        "data_final_art"
                    ] = (
                        data_final_art_edicao.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    st.session_state.pop(
                        "responsavel_temp_edicao_indice",
                        None
                    )

                    st.session_state[
                        "responsavel_temp_alterado_sucesso"
                    ] = True

                    st.rerun()

    # ==================================================
    # CADASTRO DE RESPONSÁVEL
    # ==================================================

    elif not responsaveis_confirmados:

        st.caption(
            "Selecione um responsável, informe os dados "
            "da ART e clique em Adicionar Responsável."
        )

        if not responsaveis_cadastrados:

            st.warning(
                "⚠️ Nenhum responsável ativo cadastrado."
            )

        responsavel_selecionado = st.selectbox(
            "👤 Responsável pela Obra",
            options=list(
                opcoes_responsaveis.keys()
            ),
            key=f"art_responsavel_{cadastro_id}"
        )

        dados_responsavel = (
            opcoes_responsaveis[
                responsavel_selecionado
            ]
        )

        responsavel_id_selecionado = (
            dados_responsavel["id"]
        )

        if responsavel_id_selecionado is not None:

            tipo_responsabilidade_selecionado = (
                dados_responsavel[
                    "tipo_responsabilidade"
                ]
            )

            tipo_vinculo_selecionado = (
                dados_responsavel[
                    "tipo_vinculo"
                ]
            )

            # ==================================================
            # RESPONSABILIDADE / VÍNCULO
            # ==================================================

            col_resp1, col_resp2 = st.columns(2)

            with col_resp1:

                st.text_input(
                    "👷 Tipo de Responsabilidade",
                    value=(
                        tipo_responsabilidade_selecionado
                    ),
                    disabled=True,
                    key=(
                        f"art_resp_visual_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            with col_resp2:

                st.text_input(
                    "🔗 Tipo de Vínculo",
                    value=(
                        tipo_vinculo_selecionado
                    ),
                    disabled=True,
                    key=(
                        f"art_vinculo_visual_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            # ==================================================
            # ART
            # ==================================================

            col_art1, col_art2 = st.columns(2)

            with col_art1:

                numero_art_temp = st.text_input(
                    "📜 Número da ART",
                    placeholder="Informe o número da ART",
                    key=(
                        f"numero_art_temp_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            with col_art2:

                tipo_art_temp = st.selectbox(
                    "🏗️ Tipo da ART",
                    [
                        "Fiscalização",
                        "Execução",
                        "Projeto"
                    ],
                    key=(
                        f"tipo_art_temp_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            # ==================================================
            # DATAS ART
            # ==================================================

            col_data1, col_data2 = st.columns(2)

            with col_data1:

                data_inicio_art_temp = st.date_input(
                    "📅 Data Inicial da ART",
                    key=(
                        f"inicio_art_temp_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            with col_data2:

                data_final_art_temp = st.date_input(
                    "📅 Data Final da ART",
                    key=(
                        f"final_art_temp_"
                        f"{cadastro_id}_"
                        f"{responsavel_id_selecionado}"
                    )
                )

            # ==================================================
            # ADICIONAR RESPONSÁVEL
            # ==================================================

            if st.button(
                "➕ Adicionar Responsável",
                use_container_width=True,
                key=(
                    f"adicionar_responsavel_obra_"
                    f"{cadastro_id}"
                )
            ):

                if not numero_art_temp.strip():

                    st.warning(
                        "⚠️ Informe o número da ART."
                    )

                elif (
                    data_final_art_temp
                    < data_inicio_art_temp
                ):

                    st.warning(
                        "⚠️ A data final da ART não pode "
                        "ser anterior à data inicial."
                    )

                else:

                    ja_adicionado = any(
                        item["responsavel_id"]
                        == responsavel_id_selecionado
                        for item in st.session_state[
                            "responsaveis_temp_obra"
                        ]
                    )

                    if ja_adicionado:

                        st.warning(
                            "⚠️ Este responsável já foi "
                            "adicionado à obra."
                        )

                    else:

                        st.session_state[
                            "responsaveis_temp_obra"
                        ].append({
                            "responsavel_id": (
                                responsavel_id_selecionado
                            ),
                            "nome": (
                                dados_responsavel["nome"]
                            ),
                            "tipo_responsabilidade": (
                                tipo_responsabilidade_selecionado
                            ),
                            "tipo_vinculo": (
                                tipo_vinculo_selecionado
                            ),
                            "numero_art": (
                                numero_art_temp.strip()
                            ),
                            "tipo_art": (
                                tipo_art_temp
                            ),
                            "data_inicio_art": (
                                data_inicio_art_temp.strftime(
                                    "%Y-%m-%d"
                                )
                            ),
                            "data_final_art": (
                                data_final_art_temp.strftime(
                                    "%Y-%m-%d"
                                )
                            )
                        })

                        st.rerun()

    # ==================================================
    # LISTA DE RESPONSÁVEIS
    # ==================================================

    responsaveis_temp = st.session_state[
        "responsaveis_temp_obra"
    ]

    # Não mostra tabela enquanto está editando
    if (
        responsaveis_temp
        and indice_edicao is None
    ):

        # ==================================================
        # MENSAGEM DE ALTERAÇÃO
        # ==================================================

        if st.session_state.pop(
            "responsavel_temp_alterado_sucesso",
            False
        ):
            st.success(
                "✅ Responsável alterado com sucesso."
            )

        if responsaveis_confirmados:

            st.success(
                "✅ Responsáveis salvos para esta obra."
            )

            st.markdown(
                "### 📋 Responsáveis da Obra"
            )

        else:

            st.markdown(
                "### 📋 Responsáveis adicionados"
            )

        # ==================================================
        # DATAFRAME
        # ==================================================

        dados_tabela = []

        for indice, item in enumerate(
            responsaveis_temp
        ):

            dados_tabela.append({
                "Índice": indice,
                "Responsável": (
                    item["nome"]
                ),
                "Responsabilidade": (
                    item["tipo_responsabilidade"]
                ),
                "Vínculo": (
                    item["tipo_vinculo"]
                ),
                "ART": (
                    item["numero_art"]
                ),
                "Tipo ART": (
                    item["tipo_art"]
                ),
                "Início": (
                    item["data_inicio_art"]
                ),
                "Final": (
                    item["data_final_art"]
                )
            })

        df_responsaveis = pd.DataFrame(
            dados_tabela
        )

        # ==================================================
        # DEPOIS DE CONFIRMAR:
        # AGRIGRID COM DUPLO CLIQUE
        # ==================================================

        if responsaveis_confirmados:

            js_duplo_clique = JsCode("""
                function(params) {
                    if (params.data) {
                        params.api.deselectAll();
                        params.node.setSelected(true);
                    }
                }
            """)

            gb = GridOptionsBuilder.from_dataframe(
                df_responsaveis
            )

            gb.configure_default_column(
                sortable=True,
                filter=True,
                resizable=True
            )

            gb.configure_column(
                "Índice",
                hide=True
            )

            gb.configure_selection(
                selection_mode="single",
                use_checkbox=False
            )

            grid_options = gb.build()

            grid_options[
                "suppressRowClickSelection"
            ] = True

            grid_options[
                "onRowDoubleClicked"
            ] = js_duplo_clique

            resposta = AgGrid(
                df_responsaveis,
                gridOptions=grid_options,
                height=220,
                fit_columns_on_grid_load=True,
                update_mode=(
                    GridUpdateMode.SELECTION_CHANGED
                ),
                allow_unsafe_jscode=True,
                key=(
                    f"grid_responsaveis_obra_"
                    f"{cadastro_id}"
                )
            )

            selecionados = resposta.get(
                "selected_rows",
                []
            )

            if isinstance(
                selecionados,
                pd.DataFrame
            ):
                selecionados = (
                    selecionados.to_dict(
                        "records"
                    )
                )

            if selecionados:

                selecionado = selecionados[0]

                st.session_state[
                    "responsavel_temp_edicao_indice"
                ] = int(
                    selecionado["Índice"]
                )

                st.rerun()

            st.caption(
                "👆 Dê dois cliques em um responsável "
                "para alterar os dados da ART."
            )

        # ==================================================
        # ANTES DE CONFIRMAR:
        # DATAFRAME NORMAL
        # ==================================================

        else:

            st.dataframe(
                df_responsaveis.drop(
                    columns=["Índice"]
                ),
                use_container_width=True,
                hide_index=True
            )

            col_remover, col_salvar = (
                st.columns(2)
            )

            # ==================================================
            # REMOVER ÚLTIMO
            # ==================================================

            with col_remover:

                if st.button(
                    "↩️ Remover Último",
                    use_container_width=True,
                    key=(
                        f"remover_responsavel_obra_"
                        f"{cadastro_id}"
                    )
                ):

                    st.session_state[
                        "responsaveis_temp_obra"
                    ].pop()

                    st.rerun()

            # ==================================================
            # SALVAR RESPONSÁVEIS
            # ==================================================

            with col_salvar:

                if st.button(
                    "💾 Salvar Responsável",
                    type="primary",
                    use_container_width=True,
                    key=(
                        f"salvar_responsaveis_obra_"
                        f"{cadastro_id}"
                    )
                ):

                    st.session_state[
                        "responsaveis_confirmados_obra"
                    ] = True

                    st.rerun()

    elif (
        not responsaveis_temp
        and not responsaveis_confirmados
    ):

        st.info(
            "Nenhum responsável adicionado à obra."
        )

    # ==================================================
    # SITUAÇÃO DA OBRA
    # ==================================================

    st.divider()

    st.subheader("🚧 Situação Inicial da Obra")

    situacao = st.selectbox(
        "📊 Situação da Obra",
        [
            "1 – Não iniciado",
            "2 – Iniciado",
            "3 – Encerrado por rescisão contratual",
            "4 – Paralisado",
            "5 – Concluído e não recebido",
            "6 – Concluído e recebido provisoriamente",
            "7 – Concluído e recebido definitivamente",
            "8 – Reiniciado"
        ],
        key=f"situacao_{cadastro_id}"
    )

    # ==================================================
    # MAPA
    # ==================================================

    st.divider()

    st.subheader("📍 Local da Obra")

    st.info(
        "🖱️ Clique no mapa exatamente no local da obra."
    )

    # ==================================================
    # CENTRO DO MAPA
    # ==================================================

    if (
        st.session_state["latitude_obra"] is not None
        and
        st.session_state["longitude_obra"] is not None
    ):

        centro_mapa = [
            st.session_state["latitude_obra"],
            st.session_state["longitude_obra"]
        ]

        zoom_mapa = 17

    else:

        centro_mapa = [
            -20.7336,
            -42.0306
        ]

        zoom_mapa = 15

    # ==================================================
    # CRIAR MAPA
    # ==================================================

    mapa = folium.Map(
        location=centro_mapa,
        zoom_start=zoom_mapa
    )

    # ==================================================
    # MARCADOR
    # ==================================================

    if (
        st.session_state["latitude_obra"] is not None
        and
        st.session_state["longitude_obra"] is not None
    ):

        folium.Marker(
            [
                st.session_state["latitude_obra"],
                st.session_state["longitude_obra"]
            ],
            popup="Local da Obra",
            tooltip="Local selecionado"
        ).add_to(mapa)

    # ==================================================
    # MAPA GRANDE
    # ==================================================

    map_data = st_folium(
        mapa,
        height=700,
        use_container_width=True,
        key=f"mapa_{cadastro_id}"
    )

    # ==================================================
    # LOCAL CLICADO
    # ==================================================

    if (
        map_data
        and
        map_data.get("last_clicked")
    ):

        latitude_clicada = (
            map_data[
                "last_clicked"
            ]["lat"]
        )

        longitude_clicada = (
            map_data[
                "last_clicked"
            ]["lng"]
        )

        ponto_mudou = (
            latitude_clicada
            != st.session_state["latitude_obra"]
            or
            longitude_clicada
            != st.session_state["longitude_obra"]
        )

        if ponto_mudou:

            st.session_state[
                "latitude_obra"
            ] = latitude_clicada

            st.session_state[
                "longitude_obra"
            ] = longitude_clicada

            # ==================================================
            # BUSCAR ENDEREÇO
            # ==================================================

            try:

                geolocator = get_geolocator()

                location = geolocator.reverse(
                    (
                        latitude_clicada,
                        longitude_clicada
                    ),
                    language="pt",
                    timeout=10,
                    exactly_one=True
                )

                if location:

                    dados_endereco = (
                        location.raw.get(
                            "address",
                            {}
                        )
                    )

                    rua = (
                        dados_endereco.get("road")
                        or
                        dados_endereco.get("pedestrian")
                        or
                        dados_endereco.get("residential")
                        or
                        "Não informado"
                    )

                    numero_mapa = (
                        dados_endereco.get(
                            "house_number"
                        )
                        or
                        "Não informado"
                    )

                    bairro_mapa = (
                        dados_endereco.get("suburb")
                        or
                        dados_endereco.get("neighbourhood")
                        or
                        dados_endereco.get("quarter")
                        or
                        dados_endereco.get("city_district")
                        or
                        dados_endereco.get("district")
                        or
                        "Não informado"
                    )

                    cidade = (
                        dados_endereco.get("city")
                        or
                        dados_endereco.get("town")
                        or
                        dados_endereco.get("municipality")
                        or
                        dados_endereco.get("village")
                        or
                        "Não informado"
                    )

                    estado = (
                        dados_endereco.get(
                            "state",
                            "Não informado"
                        )
                    )

                    pais = (
                        dados_endereco.get(
                            "country",
                            "Brasil"
                        )
                    )

                    st.session_state[
                        "endereco_obra"
                    ] = location.address

                    st.session_state[
                        "dados_endereco_obra"
                    ] = {
                        "rua": rua,
                        "numero": numero_mapa,
                        "bairro": bairro_mapa,
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
    # DADOS DA LOCALIZAÇÃO
    # ==================================================

    latitude = st.session_state[
        "latitude_obra"
    ]

    longitude = st.session_state[
        "longitude_obra"
    ]

    dados = st.session_state[
        "dados_endereco_obra"
    ]

    endereco = st.session_state[
        "endereco_obra"
    ]

    # ==================================================
    # MOSTRAR LOCALIZAÇÃO
    # ==================================================

    if (
        latitude is not None
        and
        longitude is not None
    ):

        st.success(
            "✅ Local da obra selecionado"
        )

        col_local1, col_local2, col_local3 = (
            st.columns(3)
        )

        with col_local1:

            st.write(
                "🛣️ **Rua:**",
                dados.get(
                    "rua",
                    "Não informado"
                )
            )

            st.write(
                "🔢 **Número:**",
                numero
                if numero
                else "Não informado"
            )

        with col_local2:

            st.write(
                "🏘️ **Bairro:**",
                bairro
                if bairro
                else "Não informado"
            )

            st.write(
                "🏙️ **Cidade:**",
                dados.get(
                    "cidade",
                    "Não informado"
                )
            )

        with col_local3:

            st.write(
                "🗺️ **Estado:**",
                dados.get(
                    "estado",
                    "Não informado"
                )
            )

            st.write(
                "🌎 **País:**",
                dados.get(
                    "pais",
                    "Brasil"
                )
            )

        st.info(
            f"📌 Coordenadas: "
            f"{latitude:.6f}, "
            f"{longitude:.6f}"
        )

        # ==================================================
        # ENDEREÇO FINAL
        # ==================================================

        endereco = (
            f"{dados.get('rua', 'Não informado')}, "
            f"{numero if numero else 'S/N'} - "
            f"{bairro if bairro else 'Não informado'}, "
            f"{dados.get('cidade', 'Não informado')} - "
            f"{dados.get('estado', 'Não informado')}, "
            f"{dados.get('pais', 'Brasil')}"
        )

        st.session_state[
            "endereco_obra"
        ] = endereco

        st.info(
            f"🏠 Endereço: {endereco}"
        )

    # ==================================================
    # SALVAR OBRA
    # ==================================================

    st.divider()

    st.subheader("💾 Finalizar Cadastro")

    if st.button(
        "💾 Salvar Obra",
        type="primary",
        use_container_width=True,
        key=f"salvar_{cadastro_id}"
    ):

        # ==================================================
        # VALIDAÇÕES
        # ==================================================

        if not obra.strip():

            st.warning(
                "⚠️ Informe o nome da obra."
            )
            return

        if not contrato.strip():

            st.warning(
                "⚠️ Informe o número do contrato."
            )
            return

        if valor_obra <= 0:

            st.warning(
                "⚠️ Informe o valor da obra."
            )
            return

        if not st.session_state[
            "responsaveis_temp_obra"
        ]:

            st.warning(
                "⚠️ Adicione pelo menos um responsável "
                "à obra."
            )
            return

        if not st.session_state.get(
            "responsaveis_confirmados_obra",
            False
        ):

            st.warning(
                "⚠️ Clique em Salvar Responsável "
                "antes de salvar a obra."
            )
            return

        if st.session_state.get(
            "responsavel_temp_edicao_indice"
        ) is not None:

            st.warning(
                "⚠️ Finalize a alteração do responsável "
                "antes de salvar a obra."
            )
            return

        if (
            latitude is None
            or
            longitude is None
        ):

            st.warning(
                "⚠️ Selecione o local da obra no mapa."
            )
            return

        # ==================================================
        # PRIMEIRO RESPONSÁVEL
        # ==================================================

        primeiro_responsavel = (
            st.session_state[
                "responsaveis_temp_obra"
            ][0]
        )

        responsavel_id = (
            primeiro_responsavel[
                "responsavel_id"
            ]
        )

        responsavel = (
            primeiro_responsavel[
                "nome"
            ]
        )

        tipo_responsabilidade = (
            primeiro_responsavel[
                "tipo_responsabilidade"
            ]
        )

        tipo_vinculo = (
            primeiro_responsavel[
                "tipo_vinculo"
            ]
        )

        art = (
            primeiro_responsavel[
                "numero_art"
            ]
        )

        tipo_art = (
            primeiro_responsavel[
                "tipo_art"
            ]
        )

        data_inicio_art = (
            primeiro_responsavel[
                "data_inicio_art"
            ]
        )

        data_final_art = (
            primeiro_responsavel[
                "data_final_art"
            ]
        )

        # ==================================================
        # SALVAR NO BANCO
        # ==================================================

        try:

            cursor.execute("""
                INSERT INTO obras (
                    obra,
                    contrato,
                    data_inicio,
                    data_entrega,
                    recurso,

                    art,
                    tipo_art,
                    data_inicio_art,
                    data_final_art,

                    tipo_responsabilidade,
                    tipo_vinculo,

                    latitude,
                    longitude,
                    endereco,
                    numero,
                    bairro,

                    responsavel,
                    responsavel_id,

                    tipo_obra,
                    valor_obra,
                    situacao,
                    prazo_dias,
                    data_cadastro
                )
                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, (
                obra.strip(),
                contrato.strip(),

                data_inicio.strftime(
                    "%Y-%m-%d"
                ),

                data_entrega.strftime(
                    "%Y-%m-%d"
                ),

                recurso,

                art,
                tipo_art,
                data_inicio_art,
                data_final_art,

                tipo_responsabilidade,
                tipo_vinculo,

                latitude,
                longitude,
                endereco,

                numero.strip(),
                bairro.strip(),

                responsavel,
                responsavel_id,

                tipo_obra,
                valor_obra,
                situacao,
                prazo,

                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            ))

            # ==================================================
            # ID DA NOVA OBRA
            # ==================================================

            obra_id_nova = cursor.lastrowid

            # ==================================================
            # SALVAR TODOS OS RESPONSÁVEIS
            # ==================================================

            for item in st.session_state[
                "responsaveis_temp_obra"
            ]:

                cursor.execute("""
                    INSERT INTO responsaveis_obra (
                        obra_id,
                        responsavel_id,
                        tipo_responsabilidade,
                        tipo_vinculo,
                        numero_art,
                        tipo_art,
                        data_inicio_art,
                        data_final_art
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    obra_id_nova,
                    item["responsavel_id"],
                    item["tipo_responsabilidade"],
                    item["tipo_vinculo"],
                    item["numero_art"],
                    item["tipo_art"],
                    item["data_inicio_art"],
                    item["data_final_art"]
                ))

            # ==================================================
            # COMMIT
            # ==================================================

            conn.commit()

            # ==================================================
            # SUCESSO
            # ==================================================

            st.session_state[
                "obra_cadastrada_sucesso"
            ] = True

            # ==================================================
            # LIMPAR RESPONSÁVEIS
            # ==================================================

            st.session_state.pop(
                "responsaveis_temp_obra",
                None
            )

            st.session_state.pop(
                "responsaveis_temp_obra_cadastro_id",
                None
            )

            st.session_state.pop(
                "responsaveis_confirmados_obra",
                None
            )

            st.session_state.pop(
                "responsavel_temp_edicao_indice",
                None
            )

            st.session_state.pop(
                "responsavel_temp_alterado_sucesso",
                None
            )

            # ==================================================
            # LIMPAR MAPA
            # ==================================================

            st.session_state.pop(
                "latitude_obra",
                None
            )

            st.session_state.pop(
                "longitude_obra",
                None
            )

            st.session_state.pop(
                "endereco_obra",
                None
            )

            st.session_state.pop(
                "dados_endereco_obra",
                None
            )

            # ==================================================
            # NOVO CADASTRO
            # ==================================================

            st.session_state[
                "cadastro_obra_id"
            ] += 1

            # ==================================================
            # VOLTAR
            # ==================================================

            st.session_state[
                "tela_obras"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao cadastrar obra: {e}"
            )
def alterar_obra():

    st.subheader("✏️ Alterar Obra")

    # ==========================================
    # ID DA OBRA
    # ==========================================

    id_obra = st.session_state.get(
        "obra_edicao_id"
    )

    if id_obra is None:

        st.warning(
            "⚠️ Nenhuma obra foi selecionada "
            "para alteração."
        )
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
            tipo_art,
            data_inicio_art,
            data_final_art,
            tipo_responsabilidade,
            tipo_vinculo,
            latitude,
            longitude,
            endereco,
            numero,
            bairro,
            responsavel,
            responsavel_id,
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
    # DADOS ATUAIS
    # ==========================================

    nome_atual = dados[1]
    contrato_atual = dados[2]
    data_inicio_atual = dados[3]
    recurso_atual = dados[5]

    art_atual = dados[6]
    tipo_art_atual = dados[7]
    data_inicio_art_atual = dados[8]
    data_final_art_atual = dados[9]

    responsabilidade_atual = dados[10]
    vinculo_atual = dados[11]

    latitude_atual = dados[12]
    longitude_atual = dados[13]
    endereco_atual = dados[14]

    numero_atual = dados[15]
    bairro_atual = dados[16]

    responsavel_atual = dados[17]
    responsavel_id_atual = dados[18]

    tipo_atual = dados[19]
    valor_atual = dados[20]
    situacao_atual = dados[21]
    prazo_atual = dados[22]

    st.info(
        f"Editando obra #{id_obra} - {nome_atual}"
    )

    # ==========================================
    # CONVERTER DATAS
    # ==========================================

    try:

        data_convertida = datetime.strptime(
            data_inicio_atual,
            "%Y-%m-%d"
        ).date()

    except Exception:

        data_convertida = (
            datetime.now().date()
        )

    try:

        data_inicio_art_convertida = (
            datetime.strptime(
                data_inicio_art_atual,
                "%Y-%m-%d"
            ).date()
        )

    except Exception:

        data_inicio_art_convertida = (
            datetime.now().date()
        )

    try:

        data_final_art_convertida = (
            datetime.strptime(
                data_final_art_atual,
                "%Y-%m-%d"
            ).date()
        )

    except Exception:

        data_final_art_convertida = (
            datetime.now().date()
        )

    # ==========================================
    # CAMPOS
    # ==========================================

    col1, col2 = st.columns(2)

    # ==========================================
    # COLUNA 1
    # ==========================================

    with col1:

        nome = st.text_input(
            "🏗️ Nome da Obra",
            value=nome_atual or "",
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
            recursos.index(
                recurso_atual
            )
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
            value=float(
                valor_atual or 0
            ),
            format="%.2f",
            key=f"editar_valor_{id_obra}"
        )

        numero = st.text_input(
            "🔢 Número",
            value=numero_atual or "",
            key=f"editar_numero_{id_obra}"
        )

        bairro = st.text_input(
            "🏘️ Bairro",
            value=bairro_atual or "",
            key=f"editar_bairro_{id_obra}"
        )

    # ==========================================
    # COLUNA 2
    # ==========================================

    with col2:

        # ======================================
        # RESPONSÁVEIS CADASTRADOS
        # ======================================

        cursor.execute("""
            SELECT
                id,
                nome,
                tipo_responsabilidade,
                tipo_vinculo
            FROM responsaveis
            WHERE ativo = 1
            ORDER BY nome
        """)

        registros_responsaveis = (
            cursor.fetchall()
        )

        opcoes_responsaveis = {}

        for registro in registros_responsaveis:

            opcoes_responsaveis[
                registro[1]
            ] = {
                "id": registro[0],
                "nome": registro[1],
                "tipo_responsabilidade": (
                    registro[2] or ""
                ),
                "tipo_vinculo": (
                    registro[3] or ""
                )
            }

        # ======================================
        # RESPONSÁVEL ANTIGO NÃO ENCONTRADO
        # ======================================

        if (
            responsavel_atual
            and responsavel_atual
            not in opcoes_responsaveis
        ):

            opcoes_responsaveis[
                responsavel_atual
            ] = {
                "id": responsavel_id_atual,
                "nome": responsavel_atual,
                "tipo_responsabilidade": (
                    responsabilidade_atual or ""
                ),
                "tipo_vinculo": (
                    vinculo_atual or ""
                )
            }

        nomes_responsaveis = list(
            opcoes_responsaveis.keys()
        )

        if not nomes_responsaveis:

            st.warning(
                "⚠️ Nenhum responsável cadastrado."
            )

            responsavel = ""
            responsavel_id = None
            tipo_responsabilidade = ""
            tipo_vinculo = ""

        else:

            indice_responsavel = 0

            if (
                responsavel_atual
                in nomes_responsaveis
            ):

                indice_responsavel = (
                    nomes_responsaveis.index(
                        responsavel_atual
                    )
                )

            responsavel_selecionado = (
                st.selectbox(
                    "👤 Responsável pela Obra",
                    nomes_responsaveis,
                    index=indice_responsavel,
                    key=(
                        f"editar_responsavel_"
                        f"{id_obra}"
                    )
                )
            )

            dados_responsavel = (
                opcoes_responsaveis[
                    responsavel_selecionado
                ]
            )

            responsavel = (
                dados_responsavel["nome"]
            )

            responsavel_id = (
                dados_responsavel["id"]
            )

            tipo_responsabilidade = (
                dados_responsavel[
                    "tipo_responsabilidade"
                ]
            )

            tipo_vinculo = (
                dados_responsavel[
                    "tipo_vinculo"
                ]
            )

            st.text_input(
                "👷 Tipo de Responsabilidade",
                value=tipo_responsabilidade,
                disabled=True,
                key=(
                    f"editar_responsabilidade_"
                    f"{id_obra}_"
                    f"{responsavel_id}"
                )
            )

            st.text_input(
                "🔗 Tipo de Vínculo",
                value=tipo_vinculo,
                disabled=True,
                key=(
                    f"editar_vinculo_"
                    f"{id_obra}_"
                    f"{responsavel_id}"
                )
            )

        # ======================================
        # TIPO DA OBRA
        # ======================================

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
            value=int(
                prazo_atual or 1
            ),
            step=1,
            key=f"editar_prazo_{id_obra}"
        )

        data_inicio = st.date_input(
            "📅 Data de Início",
            value=data_convertida,
            key=f"editar_data_{id_obra}"
        )

    # ==========================================
    # PREVISÃO DE ENTREGA
    # ==========================================

    data_entrega = (
        data_inicio
        + timedelta(days=prazo)
    )

    st.info(
        f"📅 Nova previsão de entrega: "
        f"{data_entrega.strftime('%d/%m/%Y')}"
    )

    # ==========================================
    # ART
    # ==========================================

    st.divider()

    st.subheader("📑 ART")

    col_art1, col_art2 = st.columns(2)

    with col_art1:

        art = st.text_input(
            "📜 Número da ART",
            value=art_atual or "",
            key=f"editar_art_{id_obra}"
        )

        tipos_art = [
            "Fiscalização",
            "Execução",
            "Projeto"
        ]

        indice_tipo_art = (
            tipos_art.index(
                tipo_art_atual
            )
            if tipo_art_atual in tipos_art
            else 0
        )

        tipo_art = st.selectbox(
            "🏗️ Tipo de ART",
            tipos_art,
            index=indice_tipo_art,
            key=f"editar_tipo_art_{id_obra}"
        )

    with col_art2:

        data_inicio_art = st.date_input(
            "📅 Data Inicial da ART",
            value=data_inicio_art_convertida,
            key=(
                f"editar_inicio_art_"
                f"{id_obra}"
            )
        )

        data_final_art = st.date_input(
            "📅 Data Final da ART",
            value=data_final_art_convertida,
            key=(
                f"editar_final_art_"
                f"{id_obra}"
            )
        )

    # ==========================================
    # SITUAÇÃO
    # ==========================================

    situacoes = [
        "1 – Não iniciado",
        "2 – Iniciado",
        "3 – Encerrado por rescisão contratual",
        "4 – Paralisado",
        "5 – Concluído e não recebido",
        "6 – Concluído e recebido provisoriamente",
        "7 – Concluído e recebido definitivamente",
        "8 – Reiniciado"
    ]

    indice_situacao = (
        situacoes.index(
            situacao_atual
        )
        if situacao_atual in situacoes
        else 0
    )

    situacao = st.selectbox(
        "📊 Situação",
        situacoes,
        index=indice_situacao,
        key=f"editar_situacao_{id_obra}"
    )

    # ==========================================
    # LOCAL ATUAL
    # ==========================================

    st.divider()

    st.subheader("📍 Localização")

    st.write(
        f"📍 **Local atual:** "
        f"{endereco_atual or 'Não informado'}"
    )

    if (
        latitude_atual is not None
        and longitude_atual is not None
    ):

        st.info(
            f"📌 Coordenadas: "
            f"{float(latitude_atual):.6f}, "
            f"{float(longitude_atual):.6f}"
        )

    # ==========================================
    # SALVAR
    # ==========================================

    st.divider()

    if st.button(
        "💾 Salvar Alterações",
        type="primary",
        use_container_width=True,
        key=f"salvar_alterar_obra_{id_obra}"
    ):

        if not nome:

            st.warning(
                "⚠️ Informe o nome da obra."
            )
            return

        if not contrato:

            st.warning(
                "⚠️ Informe o contrato."
            )
            return

        if responsavel_id is None:

            st.warning(
                "⚠️ Selecione um responsável."
            )
            return

        if not art:

            st.warning(
                "⚠️ Informe o número da ART."
            )
            return

        if data_final_art < data_inicio_art:

            st.warning(
                "⚠️ A data final da ART não pode "
                "ser anterior à data inicial."
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
                    tipo_art = ?,
                    data_inicio_art = ?,
                    data_final_art = ?,

                    tipo_responsabilidade = ?,
                    tipo_vinculo = ?,

                    responsavel = ?,
                    responsavel_id = ?,

                    numero = ?,
                    bairro = ?,

                    tipo_obra = ?,
                    valor_obra = ?,
                    situacao = ?,
                    prazo_dias = ?

                WHERE id = ?
            """, (
                nome,
                contrato,
                data_inicio.strftime(
                    "%Y-%m-%d"
                ),
                data_entrega.strftime(
                    "%Y-%m-%d"
                ),
                recurso,

                art,
                tipo_art,
                data_inicio_art.strftime(
                    "%Y-%m-%d"
                ),
                data_final_art.strftime(
                    "%Y-%m-%d"
                ),

                tipo_responsabilidade,
                tipo_vinculo,

                responsavel,
                responsavel_id,

                numero,
                bairro,

                tipo_obra,
                valor,
                situacao,
                prazo,

                id_obra
            ))

            conn.commit()

            # ==================================
            # LIMPAR EDIÇÃO
            # ==================================

            st.session_state.pop(
                "obra_edicao_id",
                None
            )

            st.session_state.pop(
                "latitude_obra",
                None
            )

            st.session_state.pop(
                "longitude_obra",
                None
            )

            st.session_state.pop(
                "endereco_obra",
                None
            )

            st.session_state.pop(
                "dados_endereco_obra",
                None
            )

            # ==================================
            # SUCESSO
            # ==================================

            st.session_state[
                "obra_alterada_sucesso"
            ] = True

            # Volta para os botões do
            # Cadastro de Obras
            st.session_state[
                "tela_obras"
            ] = "Principal"

            st.rerun()

        except Exception as e:

            conn.rollback()

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

    if id_selecionado:

        if st.button(
            "✏️ Alterar Obra Selecionada",
            type="primary",
            use_container_width=True,
            key="btn_alterar_obra_localizada"
        ):
            st.session_state["obra_edicao_id"] = id_selecionado
            st.session_state["tela_obras"] = "AlterarInterno"
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
            0.7 * cm,
            2.5 * cm,
            14.8 * cm
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

    st.subheader("🖨️ Impressão de Obras")

    # ==========================================
    # BUSCAR OBRAS
    # ==========================================

    try:
        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                responsavel,
                valor_obra,
                situacao,
                endereco
            FROM obras
            ORDER BY obra
        """)

        obras = cursor.fetchall()

    except Exception as e:
        st.error(f"❌ Erro ao carregar obras: {e}")
        return

    if not obras:
        st.warning("⚠️ Nenhuma obra cadastrada.")
        return

    # ==========================================
    # FILTRO
    # ==========================================

    pesquisa = st.text_input(
        "🔎 Pesquisar obra",
        placeholder="Digite o nome da obra ou contrato"
    )

    obras_filtradas = []

    for registro in obras:

        id_obra = registro[0]
        nome = registro[1] or ""
        contrato = registro[2] or ""

        if (
            not pesquisa
            or pesquisa.lower() in nome.lower()
            or pesquisa.lower() in contrato.lower()
        ):
            obras_filtradas.append(registro)

    if not obras_filtradas:
        st.warning("⚠️ Nenhuma obra encontrada.")
        return

    # ==========================================
    # SELEÇÃO
    # ==========================================

    opcoes = {}

    for registro in obras_filtradas:

        id_obra = registro[0]
        nome = registro[1]
        contrato = registro[2]
        situacao = registro[5]

        descricao = (
            f"{id_obra} - {nome} | "
            f"Contrato: {contrato} | "
            f"{situacao}"
        )

        opcoes[descricao] = id_obra

    obra_escolhida = st.selectbox(
        "🏗️ Selecione a obra",
        list(opcoes.keys())
    )

    id_obra = opcoes[obra_escolhida]

    # ==========================================
    # BUSCAR DADOS COMPLETOS
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
    """, (id_obra,))

    dados = cursor.fetchone()

    if not dados:
        st.error("❌ Obra não encontrada.")
        return

    # ==========================================
    # DESEMPACOTAR
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
    # PRÉVIA
    # ==========================================

    st.markdown("---")

    st.subheader(f"🏗️ {obra}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💰 Valor da Obra",
            f"R$ {float(valor_obra or 0):,.2f}"
        )

    with col2:
        st.metric(
            "📊 Situação",
            situacao or "Não informado"
        )

    with col3:
        st.metric(
            "📅 Prazo",
            f"{prazo_dias or 0} dias"
        )

    st.markdown("### 📋 Informações Gerais")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"📜 **Contrato:** {contrato or 'Não informado'}")
        st.write(f"👤 **Responsável:** {responsavel or 'Não informado'}")
        st.write(f"👷 **Responsabilidade:** {tipo_responsabilidade or 'Não informado'}")
        st.write(f"📄 **ART:** {art or 'Não informado'}")

    with col2:
        st.write(f"🏢 **Tipo da Obra:** {tipo_obra or 'Não informado'}")
        st.write(f"💰 **Recurso:** {recurso or 'Não informado'}")
        st.write(f"📅 **Início:** {data_inicio or 'Não informado'}")
        st.write(f"📅 **Entrega:** {data_entrega or 'Não informado'}")

    st.markdown("### 📍 Localização")

    st.write(
        f"🏠 **Endereço:** "
        f"{endereco or 'Não informado'}"
    )

    if latitude is not None and longitude is not None:
        st.write(
            f"🌎 **Coordenadas:** "
            f"{latitude}, {longitude}"
        )

    st.markdown("---")

    # ==========================================
    # GERAR PDF
    # ==========================================

    try:

        pdf = gerar_pdf_obra(id_obra)

        if pdf:

            nome_limpo = (
                obra
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
            )

            nome_arquivo = (
                f"{id_obra}_{nome_limpo}.pdf"
            )

            st.download_button(
                label="🖨️ Gerar / Baixar PDF da Obra",
                data=pdf,
                file_name=nome_arquivo,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"❌ Erro ao gerar PDF: {e}"
        )
def dashboard():

    # ==================================================
    # TÍTULO
    # ==================================================

    st.title("📊 Dashboard Gerencial de Obras")

    st.caption(
        "Visão estratégica da execução física, financeira "
        "e contratual das obras públicas."
    )

    st.divider()

    # ==================================================
    # FUNÇÕES AUXILIARES
    # ==================================================

    def moeda(valor):

        try:
            valor = float(valor or 0)

            texto = (
                f"{valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            return f"R$ {texto}"

        except Exception:
            return "R$ 0,00"

    def formatar_data(data):

        if not data:
            return "-"

        try:
            return datetime.strptime(
                str(data)[:10],
                "%Y-%m-%d"
            ).strftime("%d/%m/%Y")

        except Exception:
            return str(data)

    # ==================================================
    # BUSCAR TODAS AS OBRAS
    # ==================================================

    cursor.execute("""
        SELECT
            o.id,
            o.obra,
            o.contrato,
            o.valor_obra,
            o.situacao,
            o.data_inicio,
            o.data_entrega,
            o.recurso,
            o.latitude,
            o.longitude,
            o.endereco,
            o.numero,
            o.bairro,
            o.tipo_obra
        FROM obras o
        ORDER BY o.obra
    """)

    obras = cursor.fetchall()

    if not obras:
        st.info("Nenhuma obra cadastrada.")
        return

    # ==================================================
    # DATAFRAME DAS OBRAS
    # ==================================================

    df_obras = pd.DataFrame(
        obras,
        columns=[
            "ID",
            "Obra",
            "Contrato",
            "Valor",
            "Situação",
            "Data Início",
            "Data Entrega",
            "Recurso",
            "Latitude",
            "Longitude",
            "Endereço",
            "Número",
            "Bairro",
            "Tipo"
        ]
    )

    df_obras["Valor"] = pd.to_numeric(
        df_obras["Valor"],
        errors="coerce"
    ).fillna(0)

    # ==================================================
    # DATAS
    # ==================================================

    hoje = pd.Timestamp.now().normalize()

    df_obras["Data Entrega DT"] = pd.to_datetime(
        df_obras["Data Entrega"],
        errors="coerce"
    )

    df_obras["Data Início DT"] = pd.to_datetime(
        df_obras["Data Início"],
        errors="coerce"
    )

    # ==================================================
    # SITUAÇÕES CONSIDERADAS FINALIZADAS
    # ==================================================

    situacoes_finalizadas = [
        "3 – Encerrado por rescisão contratual",
        "5 – Concluído e não recebido",
        "6 – Concluído e recebido provisoriamente",
        "7 – Concluído e recebido definitivamente"
    ]

    # ==================================================
    # IDENTIFICAR ATRASOS
    # ==================================================

    df_obras["Atrasada"] = (
        df_obras["Data Entrega DT"].notna()
        &
        (df_obras["Data Entrega DT"] < hoje)
        &
        (~df_obras["Situação"].isin(situacoes_finalizadas))
    )

    df_obras["Dias Atraso"] = 0

    mascara_atraso = df_obras["Atrasada"]

    df_obras.loc[
        mascara_atraso,
        "Dias Atraso"
    ] = (
        hoje
        - df_obras.loc[
            mascara_atraso,
            "Data Entrega DT"
        ]
    ).dt.days

    # ==================================================
    # BUSCAR MEDIÇÕES
    # ==================================================

    cursor.execute("""
        SELECT
            m.id,
            m.obra_id,
            o.obra,
            m.tipo_medicao,
            m.data_medicao,
            m.valor,
            m.percentual_obra,
            m.nota_fiscal
        FROM medicoes m

        INNER JOIN obras o
            ON o.id = m.obra_id

        ORDER BY m.data_medicao DESC
    """)

    medicoes = cursor.fetchall()

    df_medicoes = pd.DataFrame(
        medicoes,
        columns=[
            "ID",
            "Obra ID",
            "Obra",
            "Tipo",
            "Data",
            "Valor",
            "Percentual",
            "Nota Fiscal"
        ]
    )

    if not df_medicoes.empty:

        df_medicoes["Valor"] = pd.to_numeric(
            df_medicoes["Valor"],
            errors="coerce"
        ).fillna(0)

        df_medicoes["Percentual"] = pd.to_numeric(
            df_medicoes["Percentual"],
            errors="coerce"
        ).fillna(0)

        df_medicoes["Data DT"] = pd.to_datetime(
            df_medicoes["Data"],
            errors="coerce"
        )

    # ==================================================
    # FILTROS GERENCIAIS
    # ==================================================

    st.markdown("### 🎛️ Filtros")

    col_f1, col_f2, col_f3 = st.columns(3)

    # --------------------------------------------------
    # SITUAÇÃO
    # --------------------------------------------------

    situacoes_disponiveis = sorted([
        str(x)
        for x in df_obras["Situação"].dropna().unique()
        if str(x).strip()
    ])

    with col_f1:

        filtro_situacao = st.multiselect(
            "Situação da Obra",
            situacoes_disponiveis,
            key="dashboard_filtro_situacao"
        )

    # --------------------------------------------------
    # RECURSO
    # --------------------------------------------------

    recursos_disponiveis = sorted([
        str(x)
        for x in df_obras["Recurso"].dropna().unique()
        if str(x).strip()
    ])

    with col_f2:

        filtro_recurso = st.multiselect(
            "Fonte de Recurso",
            recursos_disponiveis,
            key="dashboard_filtro_recurso"
        )

    # --------------------------------------------------
    # TIPO
    # --------------------------------------------------

    tipos_disponiveis = sorted([
        str(x)
        for x in df_obras["Tipo"].dropna().unique()
        if str(x).strip()
    ])

    with col_f3:

        filtro_tipo = st.multiselect(
            "Tipo de Obra",
            tipos_disponiveis,
            key="dashboard_filtro_tipo"
        )

    # ==================================================
    # APLICAR FILTROS
    # ==================================================

    df_filtrado = df_obras.copy()

    if filtro_situacao:

        df_filtrado = df_filtrado[
            df_filtrado["Situação"].isin(
                filtro_situacao
            )
        ]

    if filtro_recurso:

        df_filtrado = df_filtrado[
            df_filtrado["Recurso"].isin(
                filtro_recurso
            )
        ]

    if filtro_tipo:

        df_filtrado = df_filtrado[
            df_filtrado["Tipo"].isin(
                filtro_tipo
            )
        ]

    ids_filtrados = (
        df_filtrado["ID"]
        .astype(int)
        .tolist()
    )

    if not df_medicoes.empty:

        df_medicoes_filtrado = df_medicoes[
            df_medicoes["Obra ID"].isin(
                ids_filtrados
            )
        ].copy()

    else:

        df_medicoes_filtrado = pd.DataFrame()

    # ==================================================
    # INDICADORES
    # ==================================================

    total_obras = len(df_filtrado)

    valor_total_obras = (
        df_filtrado["Valor"].sum()
    )

    total_atrasadas = int(
        df_filtrado["Atrasada"].sum()
    )

    total_paralisadas = len(
        df_filtrado[
            df_filtrado["Situação"]
            == "4 – Paralisado"
        ]
    )

    total_concluidas = len(
        df_filtrado[
            df_filtrado["Situação"].isin(
                situacoes_finalizadas
            )
        ]
    )

    if not df_medicoes_filtrado.empty:

        total_medido = (
            df_medicoes_filtrado["Valor"].sum()
        )

        quantidade_medicoes = len(
            df_medicoes_filtrado
        )

    else:

        total_medido = 0
        quantidade_medicoes = 0

    saldo_contratual = (
        valor_total_obras
        - total_medido
    )

    if valor_total_obras > 0:

        percentual_medido_geral = (
            total_medido
            / valor_total_obras
        ) * 100

    else:

        percentual_medido_geral = 0

    # ==================================================
    # CARDS PRINCIPAIS
    # ==================================================

    st.divider()

    st.markdown("### 🏛️ Visão Geral")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏗️ Obras",
            total_obras
        )

    with col2:
        st.metric(
            "💰 Valor Contratado",
            moeda(valor_total_obras)
        )

    with col3:
        st.metric(
            "📏 Total Medido",
            moeda(total_medido)
        )

    with col4:
        st.metric(
            "💵 Saldo Contratual",
            moeda(saldo_contratual)
        )

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            "⏰ Obras Atrasadas",
            total_atrasadas
        )

    with col6:
        st.metric(
            "⛔ Paralisadas",
            total_paralisadas
        )

    with col7:
        st.metric(
            "✅ Concluídas",
            total_concluidas
        )

    with col8:
        st.metric(
            "📋 Medições",
            quantidade_medicoes
        )

    # ==================================================
    # EXECUÇÃO FINANCEIRA GERAL
    # ==================================================

    st.divider()

    st.markdown(
        "### 💰 Execução Financeira das Obras"
    )

    st.progress(
        min(
            max(
                percentual_medido_geral / 100,
                0
            ),
            1
        )
    )

    st.write(
        f"**{percentual_medido_geral:.2f}%** "
        f"do valor contratado foi medido."
    )

    col1, col2 = st.columns(2)

    # ==================================================
    # GRÁFICO SITUAÇÃO
    # ==================================================

    with col1:

        st.markdown(
            "#### 📊 Obras por Situação"
        )

        situacao_df = (
            df_filtrado[
                "Situação"
            ]
            .fillna("Não informado")
            .value_counts()
            .reset_index()
        )

        situacao_df.columns = [
            "Situação",
            "Quantidade"
        ]

        fig_situacao = px.pie(
            situacao_df,
            names="Situação",
            values="Quantidade",
            hole=0.45
        )

        fig_situacao.update_layout(
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10
            ),
            legend_title_text=""
        )

        st.plotly_chart(
            fig_situacao,
            use_container_width=True
        )

    # ==================================================
    # GRÁFICO RECURSOS
    # ==================================================

    with col2:

        st.markdown(
            "#### 💵 Valor por Fonte de Recurso"
        )

        recurso_df = (
            df_filtrado
            .assign(
                Recurso=df_filtrado[
                    "Recurso"
                ].fillna(
                    "Não informado"
                )
            )
            .groupby(
                "Recurso",
                as_index=False
            )["Valor"]
            .sum()
            .sort_values(
                "Valor",
                ascending=False
            )
        )

        fig_recurso = px.bar(
            recurso_df,
            x="Recurso",
            y="Valor",
            text_auto=".2s"
        )

        fig_recurso.update_layout(
            xaxis_title="",
            yaxis_title="Valor contratado",
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10
            )
        )

        st.plotly_chart(
            fig_recurso,
            use_container_width=True
        )

    # ==================================================
    # CONTRATADO X MEDIDO POR OBRA
    # ==================================================

    st.divider()

    st.markdown(
        "### 📈 Contratado x Medido por Obra"
    )

    valores_medido_por_obra = {}

    if not df_medicoes_filtrado.empty:

        valores_medido_por_obra = (
            df_medicoes_filtrado
            .groupby("Obra ID")["Valor"]
            .sum()
            .to_dict()
        )

    comparativo = []

    for _, obra in df_filtrado.iterrows():

        obra_id = int(obra["ID"])

        contratado = float(
            obra["Valor"] or 0
        )

        medido = float(
            valores_medido_por_obra.get(
                obra_id,
                0
            )
        )

        saldo = contratado - medido

        percentual_execucao = (
            (medido / contratado) * 100
            if contratado > 0
            else 0
        )

        comparativo.append({
            "Obra": obra["Obra"],
            "Contratado": contratado,
            "Medido": medido,
            "Saldo": saldo,
            "% Medido": percentual_execucao
        })

    df_comparativo = pd.DataFrame(
        comparativo
    )

    if not df_comparativo.empty:

        df_grafico = df_comparativo.melt(
            id_vars=["Obra"],
            value_vars=[
                "Contratado",
                "Medido"
            ],
            var_name="Tipo",
            value_name="Valor"
        )

        fig_comparativo = px.bar(
            df_grafico,
            x="Obra",
            y="Valor",
            color="Tipo",
            barmode="group"
        )

        fig_comparativo.update_layout(
            xaxis_title="",
            yaxis_title="Valor",
            legend_title_text="",
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            )
        )

        st.plotly_chart(
            fig_comparativo,
            use_container_width=True
        )

    # ==================================================
    # EXECUÇÃO FINANCEIRA INDIVIDUAL
    # ==================================================

    st.markdown(
        "#### 📋 Execução por Obra"
    )

    if not df_comparativo.empty:

        df_execucao = (
            df_comparativo.copy()
        )

        df_execucao[
            "Contratado"
        ] = df_execucao[
            "Contratado"
        ].apply(moeda)

        df_execucao[
            "Medido"
        ] = df_execucao[
            "Medido"
        ].apply(moeda)

        df_execucao[
            "Saldo"
        ] = df_execucao[
            "Saldo"
        ].apply(moeda)

        df_execucao[
            "% Medido"
        ] = df_execucao[
            "% Medido"
        ].apply(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(
            df_execucao,
            use_container_width=True,
            hide_index=True
        )

    # ==================================================
    # EVOLUÇÃO DAS MEDIÇÕES
    # ==================================================

    st.divider()

    st.markdown(
        "### 📏 Evolução das Medições"
    )

    if not df_medicoes_filtrado.empty:

        df_evolucao = (
            df_medicoes_filtrado[
                df_medicoes_filtrado[
                    "Data DT"
                ].notna()
            ]
            .copy()
        )

        if not df_evolucao.empty:

            evolucao = (
                df_evolucao
                .groupby(
                    "Data DT",
                    as_index=False
                )["Valor"]
                .sum()
                .sort_values(
                    "Data DT"
                )
            )

            evolucao[
                "Acumulado"
            ] = evolucao[
                "Valor"
            ].cumsum()

            fig_evolucao = go.Figure()

            fig_evolucao.add_trace(
                go.Bar(
                    x=evolucao[
                        "Data DT"
                    ],
                    y=evolucao[
                        "Valor"
                    ],
                    name="Valor Medido"
                )
            )

            fig_evolucao.add_trace(
                go.Scatter(
                    x=evolucao[
                        "Data DT"
                    ],
                    y=evolucao[
                        "Acumulado"
                    ],
                    mode="lines+markers",
                    name="Acumulado"
                )
            )

            fig_evolucao.update_layout(
                xaxis_title="Data",
                yaxis_title="Valor",
                legend_title_text="",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig_evolucao,
                use_container_width=True
            )

    else:

        st.info(
            "Ainda não existem medições "
            "para as obras selecionadas."
        )

    # ==================================================
    # OBRAS ATRASADAS
    # ==================================================

    st.divider()

    st.markdown(
        "### ⏰ Obras Atrasadas"
    )

    df_atrasadas = df_filtrado[
        df_filtrado["Atrasada"]
    ].copy()

    if not df_atrasadas.empty:

        atrasadas_exibir = (
            df_atrasadas[
                [
                    "Obra",
                    "Contrato",
                    "Situação",
                    "Data Entrega",
                    "Dias Atraso",
                    "Valor"
                ]
            ]
            .copy()
        )

        atrasadas_exibir[
            "Data Entrega"
        ] = atrasadas_exibir[
            "Data Entrega"
        ].apply(formatar_data)

        atrasadas_exibir[
            "Valor"
        ] = atrasadas_exibir[
            "Valor"
        ].apply(moeda)

        atrasadas_exibir = (
            atrasadas_exibir
            .sort_values(
                "Dias Atraso",
                ascending=False
            )
        )

        st.dataframe(
            atrasadas_exibir,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "✅ Nenhuma obra atrasada "
            "nos filtros selecionados."
        )

    # ==================================================
    # OBRAS PARALISADAS
    # ==================================================

    st.markdown(
        "### ⛔ Obras Paralisadas"
    )

    cursor.execute("""
        SELECT
            id,
            motivo_paralisacao
        FROM obras
    """)

    motivos = {
        registro[0]: (
            registro[1]
            or "Motivo não informado"
        )
        for registro in cursor.fetchall()
    }

    df_paralisadas = df_filtrado[
        df_filtrado["Situação"]
        == "4 – Paralisado"
    ].copy()

    if not df_paralisadas.empty:

        for _, obra in (
            df_paralisadas.iterrows()
        ):

            with st.expander(
                f"⛔ {obra['Obra']}"
            ):

                st.write(
                    f"**Contrato:** "
                    f"{obra['Contrato'] or '-'}"
                )

                st.write(
                    f"**Valor:** "
                    f"{moeda(obra['Valor'])}"
                )

                st.write(
                    f"**Motivo da paralisação:** "
                    f"{motivos.get(obra['ID'], '-')}"
                )

    else:

        st.success(
            "✅ Nenhuma obra paralisada."
        )

    # ==================================================
    # PRAZOS
    # ==================================================

    st.divider()

    st.markdown(
        "### 📅 Controle de Prazos"
    )

    df_prazos = df_filtrado[
        df_filtrado[
            "Data Entrega DT"
        ].notna()
    ].copy()

    if not df_prazos.empty:

        df_prazos[
            "Dias para Prazo"
        ] = (
            df_prazos[
                "Data Entrega DT"
            ] - hoje
        ).dt.days

        # Remover concluídas
        df_prazos_abertos = df_prazos[
            ~df_prazos[
                "Situação"
            ].isin(
                situacoes_finalizadas
            )
        ].copy()

        # ----------------------------------------------
        # PRAZOS PRÓXIMOS
        # ----------------------------------------------

        proximos = df_prazos_abertos[
            (
                df_prazos_abertos[
                    "Dias para Prazo"
                ] >= 0
            )
            &
            (
                df_prazos_abertos[
                    "Dias para Prazo"
                ] <= 30
            )
        ].copy()

        if not proximos.empty:

            st.warning(
                f"⚠️ {len(proximos)} obra(s) "
                f"com prazo vencendo nos próximos 30 dias."
            )

            proximos_exibir = proximos[
                [
                    "Obra",
                    "Situação",
                    "Data Entrega",
                    "Dias para Prazo"
                ]
            ].copy()

            proximos_exibir[
                "Data Entrega"
            ] = proximos_exibir[
                "Data Entrega"
            ].apply(formatar_data)

            proximos_exibir.rename(
                columns={
                    "Dias para Prazo":
                    "Dias Restantes"
                },
                inplace=True
            )

            st.dataframe(
                proximos_exibir,
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------
        # ATRASADAS
        # ----------------------------------------------

        vencidas = df_prazos_abertos[
            df_prazos_abertos[
                "Dias para Prazo"
            ] < 0
        ]

        if not vencidas.empty:

            st.error(
                f"🚨 {len(vencidas)} obra(s) "
                f"com prazo contratual vencido."
            )

    # ==================================================
    # MEDIÇÕES RECENTES
    # ==================================================

    st.divider()

    st.markdown(
        "### 🧾 Últimas Medições"
    )

    if not df_medicoes_filtrado.empty:

        ultimas = (
            df_medicoes_filtrado
            .sort_values(
                "Data DT",
                ascending=False
            )
            .head(10)
            .copy()
        )

        ultimas[
            "Data"
        ] = ultimas[
            "Data"
        ].apply(formatar_data)

        ultimas[
            "Valor"
        ] = ultimas[
            "Valor"
        ].apply(moeda)

        ultimas[
            "Percentual"
        ] = ultimas[
            "Percentual"
        ].apply(
            lambda x: f"{x:.2f}%"
        )

        st.dataframe(
            ultimas[
                [
                    "Obra",
                    "Tipo",
                    "Data",
                    "Valor",
                    "Percentual",
                    "Nota Fiscal"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Nenhuma medição cadastrada."
        )

    # ==================================================
    # OBRAS SEM MEDIÇÃO
    # ==================================================

    st.markdown(
        "### ⚠️ Obras sem Medição"
    )

    if not df_medicoes.empty:

        ids_com_medicao = set(
            df_medicoes[
                "Obra ID"
            ].astype(int)
        )

    else:

        ids_com_medicao = set()

    obras_sem_medicao = df_filtrado[
        ~df_filtrado[
            "ID"
        ].astype(int).isin(
            ids_com_medicao
        )
    ].copy()

    if not obras_sem_medicao.empty:

        st.dataframe(
            obras_sem_medicao[
                [
                    "Obra",
                    "Contrato",
                    "Situação",
                    "Data Início",
                    "Data Entrega"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "✅ Todas as obras possuem "
            "pelo menos uma medição."
        )

    # ==================================================
    # MAPA
    # ==================================================

    st.divider()

    st.markdown(
        "### 🗺️ Mapa das Obras"
    )

    obras_mapa = df_filtrado[
        df_filtrado["Latitude"].notna()
        &
        df_filtrado["Longitude"].notna()
    ].copy()

    if not obras_mapa.empty:

        # ----------------------------------------------
        # CENTRO AUTOMÁTICO
        # ----------------------------------------------

        latitude_centro = (
            pd.to_numeric(
                obras_mapa["Latitude"],
                errors="coerce"
            ).mean()
        )

        longitude_centro = (
            pd.to_numeric(
                obras_mapa["Longitude"],
                errors="coerce"
            ).mean()
        )

        mapa = folium.Map(
            location=[
                latitude_centro,
                longitude_centro
            ],
            zoom_start=12
        )

        # ----------------------------------------------
        # MARCADORES
        # ----------------------------------------------

        for _, obra in (
            obras_mapa.iterrows()
        ):

            try:

                latitude = float(
                    obra["Latitude"]
                )

                longitude = float(
                    obra["Longitude"]
                )

            except Exception:
                continue

            # ------------------------------------------
            # MEDIDO DA OBRA
            # ------------------------------------------

            obra_id = int(
                obra["ID"]
            )

            valor_medido_obra = float(
                valores_medido_por_obra.get(
                    obra_id,
                    0
                )
            )

            valor_contratado = float(
                obra["Valor"] or 0
            )

            if valor_contratado > 0:

                percentual_obra = (
                    valor_medido_obra
                    / valor_contratado
                ) * 100

            else:

                percentual_obra = 0

            # ------------------------------------------
            # ENDEREÇO
            # ------------------------------------------

            partes_endereco = []

            if obra["Endereço"]:
                partes_endereco.append(
                    str(obra["Endereço"])
                )

            if obra["Número"]:
                partes_endereco.append(
                    str(obra["Número"])
                )

            if obra["Bairro"]:
                partes_endereco.append(
                    str(obra["Bairro"])
                )

            endereco_completo = (
                ", ".join(partes_endereco)
                if partes_endereco
                else "Não informado"
            )

            # ------------------------------------------
            # POPUP
            # ------------------------------------------

            popup_html = f"""
            <div style="width: 280px;">
                <h4>{obra["Obra"]}</h4>

                <b>Contrato:</b>
                {obra["Contrato"] or "-"}
                <br>

                <b>Situação:</b>
                {obra["Situação"] or "-"}
                <br>

                <b>Tipo:</b>
                {obra["Tipo"] or "-"}
                <br><br>

                <b>Valor contratado:</b>
                {moeda(valor_contratado)}
                <br>

                <b>Total medido:</b>
                {moeda(valor_medido_obra)}
                <br>

                <b>Execução financeira:</b>
                {percentual_obra:.2f}%
                <br><br>

                <b>Previsão de entrega:</b>
                {formatar_data(obra["Data Entrega"])}
                <br>

                <b>Endereço:</b>
                {endereco_completo}
            </div>
            """

            folium.Marker(
                location=[
                    latitude,
                    longitude
                ],
                popup=folium.Popup(
                    popup_html,
                    max_width=350
                ),
                tooltip=(
                    f"{obra['Obra']} - "
                    f"{obra['Situação']}"
                )
            ).add_to(mapa)

        st_folium(
            mapa,
            width=None,
            height=500,
            key="mapa_dashboard"
        )

    else:

        st.info(
            "Nenhuma obra dos filtros selecionados "
            "possui localização cadastrada."
        )

    # ==================================================
    # RESUMO GERENCIAL
    # ==================================================

    st.divider()

    st.markdown(
        "### 🧠 Resumo Gerencial"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "#### ⚠️ Pontos de Atenção"
        )

        if total_atrasadas > 0:

            st.error(
                f"⏰ {total_atrasadas} obra(s) "
                f"com prazo vencido."
            )

        if total_paralisadas > 0:

            st.error(
                f"⛔ {total_paralisadas} obra(s) "
                f"paralisada(s)."
            )

        if len(obras_sem_medicao) > 0:

            st.warning(
                f"📏 {len(obras_sem_medicao)} obra(s) "
                f"sem nenhuma medição."
            )

        if (
            total_atrasadas == 0
            and total_paralisadas == 0
            and len(obras_sem_medicao) == 0
        ):

            st.success(
                "✅ Nenhum alerta crítico "
                "identificado."
            )

    with col2:

        st.markdown(
            "#### 📊 Indicadores"
        )

        st.write(
            f"**Execução financeira geral:** "
            f"{percentual_medido_geral:.2f}%"
        )

        st.write(
            f"**Valor contratado:** "
            f"{moeda(valor_total_obras)}"
        )

        st.write(
            f"**Valor medido:** "
            f"{moeda(total_medido)}"
        )

        st.write(
            f"**Saldo contratual:** "
            f"{moeda(saldo_contratual)}"
        )

        st.write(
            f"**Medições registradas:** "
            f"{quantidade_medicoes}"
        )

def contabilidade():

    st.title("📚 Contabilidade")

    st.caption(
        "Gestão de empenhos e acompanhamento da execução "
        "orçamentária e financeira das obras."
    )

    st.divider()

    # ==================================================
    # CONTROLE DE TELA
    # ==================================================

    if "tela_contabilidade" not in st.session_state:
        st.session_state["tela_contabilidade"] = "Principal"

    tela = st.session_state["tela_contabilidade"]

    # ==================================================
    # TELA PRINCIPAL
    # ==================================================

    if tela == "Principal":

        # ==================================================
        # MENSAGENS
        # ==================================================

        if st.session_state.pop(
            "empenho_cadastrado_sucesso",
            False
        ):
            st.success(
                "✅ Empenho cadastrado com sucesso!"
            )

        if st.session_state.pop(
            "empenho_alterado_sucesso",
            False
        ):
            st.success(
                "✅ Empenho alterado com sucesso!"
            )

        if st.session_state.pop(
            "empenho_excluido_sucesso",
            False
        ):
            st.success(
                "✅ Empenho excluído com sucesso!"
            )

        # ==================================================
        # RESUMO GERAL
        # ==================================================

        st.markdown("### 📊 Resumo Contábil")

        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(valor_empenhado), 0),
                COALESCE(SUM(valor_anulado), 0),
                COALESCE(SUM(valor_liquidado), 0),
                COALESCE(SUM(valor_pago), 0)
            FROM empenhos
        """)

        resumo = cursor.fetchone()

        quantidade_empenhos = resumo[0] or 0
        total_empenhado = resumo[1] or 0
        total_anulado = resumo[2] or 0
        total_liquidado = resumo[3] or 0
        total_pago = resumo[4] or 0

        empenho_liquido = (
            total_empenhado
            - total_anulado
        )

        saldo_empenhado = (
            empenho_liquido
            - total_liquidado
        )

        valor_a_pagar = (
            total_liquidado
            - total_pago
        )

        # Evita indicadores negativos por inconsistência
        # nos dados cadastrados.
        saldo_empenhado_visual = max(
            saldo_empenhado,
            0
        )

        valor_a_pagar_visual = max(
            valor_a_pagar,
            0
        )

        # ==================================================
        # CARDS - LINHA 1
        # ==================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "📄 Empenhos",
                quantidade_empenhos
            )

        with col2:

            st.metric(
                "💰 Total Empenhado",
                f"R$ {total_empenhado:,.2f}"
            )

        with col3:

            st.metric(
                "↩️ Total Anulado",
                f"R$ {total_anulado:,.2f}"
            )

        # ==================================================
        # CARDS - LINHA 2
        # ==================================================

        col4, col5, col6 = st.columns(3)

        with col4:

            st.metric(
                "📋 Total Liquidado",
                f"R$ {total_liquidado:,.2f}"
            )

        with col5:

            st.metric(
                "💳 Total Pago",
                f"R$ {total_pago:,.2f}"
            )

        with col6:

            st.metric(
                "⏳ Liquidado a Pagar",
                f"R$ {valor_a_pagar_visual:,.2f}"
            )

        # ==================================================
        # SITUAÇÃO ORÇAMENTÁRIA
        # ==================================================

        st.markdown("### 💵 Situação Orçamentária")

        col7, col8, col9 = st.columns(3)

        with col7:

            st.metric(
                "💼 Empenho Líquido",
                f"R$ {empenho_liquido:,.2f}"
            )

        with col8:

            st.metric(
                "🏦 Saldo a Liquidar",
                f"R$ {saldo_empenhado_visual:,.2f}"
            )

        with col9:

            if empenho_liquido > 0:

                percentual_pago = (
                    total_pago
                    / empenho_liquido
                ) * 100

            else:

                percentual_pago = 0

            st.metric(
                "📈 Execução Financeira",
                f"{percentual_pago:.2f}%"
            )

        # ==================================================
        # PROGRESSO FINANCEIRO
        # ==================================================

        percentual_barra = min(
            max(
                percentual_pago / 100,
                0
            ),
            1
        )

        st.progress(
            percentual_barra
        )

        st.caption(
            "Execução financeira calculada considerando "
            "os pagamentos em relação ao valor líquido empenhado."
        )

        st.divider()

        # ==================================================
        # AÇÕES
        # ==================================================

        st.markdown("### 🛠️ Gestão Contábil")

        col1, col2, col3, col4 = st.columns(4)

        # ==================================================
        # CADASTRAR EMPENHO
        # ==================================================

        with col1:

            if st.button(
                "➕ Cadastrar Empenho",
                use_container_width=True,
                key="contabilidade_incluir"
            ):

                st.session_state[
                    "tela_contabilidade"
                ] = "Incluir"

                st.rerun()

        # ==================================================
        # LOCALIZAR
        # ==================================================

        with col2:

            if st.button(
                "🔎 Localizar Empenho",
                use_container_width=True,
                key="contabilidade_localizar"
            ):

                st.session_state[
                    "tela_contabilidade"
                ] = "Localizar"

                st.rerun()

        # ==================================================
        # GESTÃO POR OBRA
        # ==================================================

        with col3:

            if st.button(
                "📊 Gestão por Obra",
                use_container_width=True,
                key="contabilidade_gestao"
            ):

                st.session_state[
                    "tela_contabilidade"
                ] = "Gestao"

                st.rerun()

        # ==================================================
        # RELATÓRIOS
        # ==================================================

        with col4:

            if st.button(
                "🖨️ Relatórios",
                use_container_width=True,
                key="contabilidade_relatorios"
            ):

                st.session_state[
                    "tela_contabilidade"
                ] = "Relatorios"

                st.rerun()

        st.divider()

        # ==================================================
        # EMPENHOS RECENTES
        # ==================================================

        st.markdown("### 🕒 Empenhos Recentes")

        cursor.execute("""
            SELECT
                e.id,
                e.numero_empenho,
                e.ano_empenho,
                o.obra,
                e.credor,
                e.valor_empenhado,
                e.valor_anulado,
                e.valor_liquidado,
                e.valor_pago,
                e.data_empenho
            FROM empenhos e

            INNER JOIN obras o
                ON o.id = e.obra_id

            ORDER BY
                e.id DESC

            LIMIT 5
        """)

        empenhos_recentes = cursor.fetchall()

        if empenhos_recentes:

            dados_recentes = []

            for registro in empenhos_recentes:

                valor_empenhado = (
                    registro[5] or 0
                )

                valor_anulado = (
                    registro[6] or 0
                )

                valor_liquidado = (
                    registro[7] or 0
                )

                valor_pago = (
                    registro[8] or 0
                )

                empenho_liquido_item = (
                    valor_empenhado
                    - valor_anulado
                )

                saldo_item = (
                    empenho_liquido_item
                    - valor_liquidado
                )

                a_pagar_item = (
                    valor_liquidado
                    - valor_pago
                )

                dados_recentes.append({
                    "Empenho": (
                        f"{registro[1]}/"
                        f"{registro[2]}"
                    ),
                    "Obra": registro[3],
                    "Credor": (
                        registro[4]
                        or "Não informado"
                    ),
                    "Empenhado": (
                        valor_empenhado
                    ),
                    "Anulado": (
                        valor_anulado
                    ),
                    "Liquidado": (
                        valor_liquidado
                    ),
                    "Pago": (
                        valor_pago
                    ),
                    "A Pagar": (
                        a_pagar_item
                    ),
                    "Saldo": (
                        saldo_item
                    ),
                    "Data": (
                        registro[9]
                    )
                })

            df_recentes = pd.DataFrame(
                dados_recentes
            )

            st.dataframe(
                df_recentes,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Empenhado":
                        st.column_config.NumberColumn(
                            "Empenhado",
                            format="R$ %.2f"
                        ),
                    "Anulado":
                        st.column_config.NumberColumn(
                            "Anulado",
                            format="R$ %.2f"
                        ),
                    "Liquidado":
                        st.column_config.NumberColumn(
                            "Liquidado",
                            format="R$ %.2f"
                        ),
                    "Pago":
                        st.column_config.NumberColumn(
                            "Pago",
                            format="R$ %.2f"
                        ),
                    "A Pagar":
                        st.column_config.NumberColumn(
                            "A Pagar",
                            format="R$ %.2f"
                        ),
                    "Saldo":
                        st.column_config.NumberColumn(
                            "Saldo",
                            format="R$ %.2f"
                        )
                }
            )

        else:

            st.info(
                "📭 Nenhum empenho cadastrado."
            )

        st.divider()

        # ==================================================
        # RESUMO POR OBRA
        # ==================================================

        st.markdown(
            "### 🏗️ Execução Contábil por Obra"
        )

        cursor.execute("""
            SELECT
                o.id,
                o.obra,
                o.contrato,
                o.valor_obra,

                COALESCE(
                    SUM(e.valor_empenhado),
                    0
                ),

                COALESCE(
                    SUM(e.valor_anulado),
                    0
                ),

                COALESCE(
                    SUM(e.valor_liquidado),
                    0
                ),

                COALESCE(
                    SUM(e.valor_pago),
                    0
                )

            FROM obras o

            LEFT JOIN empenhos e
                ON e.obra_id = o.id

            GROUP BY
                o.id,
                o.obra,
                o.contrato,
                o.valor_obra

            ORDER BY
                o.obra
        """)

        resumo_obras = cursor.fetchall()

        if resumo_obras:

            dados_obras = []

            for registro in resumo_obras:

                valor_contrato = (
                    registro[3] or 0
                )

                empenhado = (
                    registro[4] or 0
                )

                anulado = (
                    registro[5] or 0
                )

                liquidado = (
                    registro[6] or 0
                )

                pago = (
                    registro[7] or 0
                )

                empenho_liquido_obra = (
                    empenhado
                    - anulado
                )

                saldo_empenho = (
                    empenho_liquido_obra
                    - liquidado
                )

                liquidado_a_pagar = (
                    liquidado
                    - pago
                )

                saldo_contrato = (
                    valor_contrato
                    - pago
                )

                if valor_contrato > 0:

                    percentual_execucao = (
                        pago
                        / valor_contrato
                    ) * 100

                else:

                    percentual_execucao = 0

                dados_obras.append({
                    "Obra": (
                        registro[1]
                    ),
                    "Contrato": (
                        registro[2]
                        or "Não informado"
                    ),
                    "Valor da Obra": (
                        valor_contrato
                    ),
                    "Empenhado": (
                        empenhado
                    ),
                    "Anulado": (
                        anulado
                    ),
                    "Empenho Líquido": (
                        empenho_liquido_obra
                    ),
                    "Liquidado": (
                        liquidado
                    ),
                    "Pago": (
                        pago
                    ),
                    "A Pagar": (
                        liquidado_a_pagar
                    ),
                    "Saldo Empenho": (
                        saldo_empenho
                    ),
                    "Saldo da Obra": (
                        saldo_contrato
                    ),
                    "Execução": (
                        f"{percentual_execucao:.2f}%"
                    )
                })

            df_obras = pd.DataFrame(
                dados_obras
            )

            st.dataframe(
                df_obras,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valor da Obra":
                        st.column_config.NumberColumn(
                            "Valor da Obra",
                            format="R$ %.2f"
                        ),
                    "Empenhado":
                        st.column_config.NumberColumn(
                            "Empenhado",
                            format="R$ %.2f"
                        ),
                    "Anulado":
                        st.column_config.NumberColumn(
                            "Anulado",
                            format="R$ %.2f"
                        ),
                    "Empenho Líquido":
                        st.column_config.NumberColumn(
                            "Empenho Líquido",
                            format="R$ %.2f"
                        ),
                    "Liquidado":
                        st.column_config.NumberColumn(
                            "Liquidado",
                            format="R$ %.2f"
                        ),
                    "Pago":
                        st.column_config.NumberColumn(
                            "Pago",
                            format="R$ %.2f"
                        ),
                    "A Pagar":
                        st.column_config.NumberColumn(
                            "A Pagar",
                            format="R$ %.2f"
                        ),
                    "Saldo Empenho":
                        st.column_config.NumberColumn(
                            "Saldo Empenho",
                            format="R$ %.2f"
                        ),
                    "Saldo da Obra":
                        st.column_config.NumberColumn(
                            "Saldo da Obra",
                            format="R$ %.2f"
                        )
                }
            )

        else:

            st.info(
                "🏗️ Nenhuma obra cadastrada."
            )

    # ==================================================
    # INCLUIR EMPENHO
    # ==================================================

    elif tela == "Incluir":

        incluir_empenho()

    # ==================================================
    # LOCALIZAR EMPENHO
    # ==================================================

    elif tela == "Localizar":

        localizar_empenho()

    # ==================================================
    # ALTERAR EMPENHO
    # ==================================================

    elif tela == "Alterar":

        alterar_empenho()

    # ==================================================
    # GESTÃO POR OBRA
    # ==================================================

    elif tela == "Gestao":

        gestao_empenhos()

    # ==================================================
    # RELATÓRIOS
    # ==================================================

    elif tela == "Relatorios":

        relatorios_contabilidade()
def main():

    st.set_page_config(
        page_title="Sistemas de Obras Públicas",
        page_icon="🏗️",
        layout="wide"
    )

    st.title("🏗️ SISOPB")
    st.markdown("---")

    # ==========================================
    # LOGIN
    # ==========================================

    if "usuario_logado" not in st.session_state:
        st.warning("Faça login para acessar o sistema.")
        login()
        return

    funcao = st.session_state.get(
        "funcao_usuario",
        ""
    )

    st.sidebar.success(
        f"👤 Usuário: {st.session_state['usuario_logado']}"
    )

    st.sidebar.info(
        f"🔐 Função: {funcao}"
    )

    # ==========================================
    # MENUS POR FUNÇÃO
    # ==========================================

    if funcao == "Administrador":

        menu = [
            "Cadastro de Obras 🛎️",
            "Situação da Obra",
            "Dashboard 📊",
            "👨‍🔧 Cadastro de Responsavel",
            "Financeiro 💰",
            "Contabilidade",
            "Medições",
            "➕ Cadastrar Usuário"
        ]

    elif funcao == "Engenheiro":

        menu = [
            "Cadastro de Obras 🛎️",
            "Situação da Obra",
            "👨‍🔧 Cadastro de Responsavel",
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

        st.error(
            "❌ Função não reconhecida. "
            "Contate o administrador."
        )

        return

    # ==========================================
    # MENU LATERAL
    # ==========================================

    escolha = st.sidebar.selectbox(
        "📋 Menu",
        menu + ["🔓 Logout"]
    )

    # ==========================================
    # DETECTAR TROCA DE MENU
    # ==========================================

    menu_anterior = st.session_state.get(
        "ultimo_menu"
    )

    if menu_anterior != escolha:

        # Entrou novamente em Cadastro de Obras
        if escolha == "Cadastro de Obras 🛎️":

            # Volta para tela inicial
            st.session_state["tela_obras"] = "Principal"

            # Limpa obra em edição
            st.session_state.pop(
                "obra_edicao_id",
                None
            )

            # Limpa obra localizada
            st.session_state.pop(
                "obra_selecionada_localizar",
                None
            )

        # Salva o menu atual
        st.session_state["ultimo_menu"] = escolha

    # ==========================================
    # ABRIR TELAS
    # ==========================================

    if escolha == "Cadastro de Obras 🛎️":

        cadastro_de_obras()

    elif escolha == "Situação da Obra":

        situacao_da_obra()

    elif escolha == "Dashboard 📊":

        dashboard()

    elif escolha == "👨‍🔧 Cadastro de Responsavel":

        cadastrar_responsavel()

    elif escolha == "Financeiro 💰":

        modulo_financeiro()

    elif escolha == "Contabilidade":

        modulo_contabil()

    elif escolha == "Medições":

        medicoes()

    elif escolha == "➕ Cadastrar Usuário":

        cadastrar_usuario()

    elif escolha == "🔓 Logout":

        st.session_state.pop(
            "usuario_logado",
            None
        )

        st.session_state.pop(
            "funcao_usuario",
            None
        )

        st.session_state.pop(
            "ultimo_menu",
            None
        )

        st.session_state.pop(
            "tela_obras",
            None
        )

        st.rerun()


if __name__ == "__main__":
    main()
