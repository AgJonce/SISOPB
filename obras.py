import os
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
        numero TEXT,
        bairro TEXT,
        responsavel TEXT,
        tipo_obra TEXT,
        valor_obra REAL,
        situacao TEXT,
        prazo_dias INTEGER,
        data_cadastro TEXT
    )
''')

conn.commit()


# ==========================================
# GARANTIR COLUNA MOTIVO_PARALISACAO
# ==========================================

cursor.execute("""
    PRAGMA table_info(obras)
""")

colunas_obras = [
    coluna[1]
    for coluna in cursor.fetchall()
]

if "motivo_paralisacao" not in colunas_obras:

    cursor.execute("""
        ALTER TABLE obras
        ADD COLUMN motivo_paralisacao TEXT
    """)

    conn.commit()

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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantidade REAL DEFAULT 0,
        valor_unitario REAL DEFAULT 0,
        valor_total REAL DEFAULT 0,
        observacao TEXT,

        FOREIGN KEY (obra_id) REFERENCES obras(id),
        FOREIGN KEY (item_id) REFERENCES itens(id)
    )
""")

conn.commit()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsaveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT UNIQUE NOT NULL,
        documento TEXT,
        tipo_responsabilidade TEXT NOT NULL,
        conselho TEXT NOT NULL,
        numero_conselho TEXT,
        ativo INTEGER DEFAULT 1,
        data_cadastro TEXT
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
def situacao_da_obra():

    st.title("🚧 Situação da Obra")

    st.caption(
        "Consulte uma obra e atualize sua situação."
    )

    st.divider()

    # ==========================================
    # SITUAÇÕES DA OBRA
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

    # ==========================================
    # MOTIVOS DE PARALISAÇÃO
    # ==========================================

    motivos_paralisacao = [
        "01 – Atrasos do repasse de convênios",
        "02 – Suspensão do repasse de convênios",
        "03 – Bloqueio do repasse de convênios",
        "04 – Repasses de convênios em valor inferior ao programado",
        "05 – Contingenciamento de recursos próprios",
        "06 – Inadequação ao plano de trabalho da nova gestão",
        "07 – Irregularidades/problemas afetos ao meio ambiente",
        "08 – Pendências com desapropriações",
        "09 – Questões técnicas que vieram a ser conhecidas somente após a licitação",
        "10 – Riscos decorrentes de erros e vícios construtivos",
        "11 – Descumprimento de especificações técnicas e prazos",
        "12 – Irregularidades nos preços e serviços contratados",
        "13 – Problemas relacionados à contratada",
        "14 – Caso Fortuito ou Força Maior",
        "15 – Ordem Judicial",
        "16 – Ausência / Falha de planejamento",
        "17 – Projeto básico e/ou executivo insuficiente",
        "18 – Defasagem entre a data base do orçamento e a realização da licitação",
        "99 – Outros tipos de paralisação ou mais de um motivo"
    ]

    # ==========================================
    # MENSAGEM DE SUCESSO
    # ==========================================

    if st.session_state.pop(
        "situacao_obra_sucesso",
        False
    ):

        st.success(
            "✅ Situação da obra alterada com sucesso!"
        )

    # ==========================================
    # PESQUISA
    # ==========================================

    busca = st.text_input(
        "🔍 Localizar Obra",
        placeholder=(
            "Digite o nome da obra, contrato "
            "ou responsável"
        ),
        key="pesquisa_situacao_obra"
    )

    # ==========================================
    # CONSULTAR OBRAS
    # ==========================================

    if busca:

        termo = f"%{busca}%"

        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                responsavel,
                situacao,
                data_inicio,
                data_entrega
            FROM obras
            WHERE
                obra LIKE ?
                OR contrato LIKE ?
                OR responsavel LIKE ?
            ORDER BY obra
        """, (
            termo,
            termo,
            termo
        ))

    else:

        cursor.execute("""
            SELECT
                id,
                obra,
                contrato,
                responsavel,
                situacao,
                data_inicio,
                data_entrega
            FROM obras
            ORDER BY obra
        """)

    registros = cursor.fetchall()

    # ==========================================
    # VERIFICAR RESULTADOS
    # ==========================================

    if not registros:

        st.info(
            "Nenhuma obra encontrada."
        )
        return

    # ==========================================
    # DATAFRAME
    # ==========================================

    df = pd.DataFrame(
        registros,
        columns=[
            "ID",
            "Obra",
            "Contrato",
            "Responsável",
            "Situação",
            "Data Início",
            "Data Entrega"
        ]
    )

    # ==========================================
    # DUPLO CLIQUE
    # ==========================================

    js_duplo_clique_situacao = JsCode("""
        function(params) {

            if (params.data) {

                params.api.deselectAll();

                params.node.setSelected(true);

            }

        }
    """)

    # ==========================================
    # CONFIGURAÇÃO DA TABELA
    # ==========================================

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
    ] = js_duplo_clique_situacao

    # ==========================================
    # EXIBIR TABELA
    # ==========================================

    resposta = AgGrid(
        df,
        gridOptions=grid_options,
        height=350,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="grid_situacao_obra"
    )

    # ==========================================
    # PEGAR OBRA SELECIONADA
    # ==========================================

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
            "obra_situacao_id"
        ] = int(
            selecionado["ID"]
        )

    # ==========================================
    # OBRA SELECIONADA
    # ==========================================

    id_obra = st.session_state.get(
        "obra_situacao_id"
    )

    if not id_obra:

        st.info(
            "👆 Dê dois cliques em uma obra "
            "para alterar a situação."
        )

        return

    # ==========================================
    # BUSCAR OBRA
    # ==========================================

    cursor.execute("""
        SELECT
            obra,
            contrato,
            responsavel,
            situacao
        FROM obras
        WHERE id = ?
    """, (
        id_obra,
    ))

    obra_selecionada = cursor.fetchone()

    if not obra_selecionada:

        st.error(
            "❌ Obra não encontrada."
        )

        st.session_state.pop(
            "obra_situacao_id",
            None
        )

        return

    nome_obra = obra_selecionada[0]
    contrato = obra_selecionada[1]
    responsavel = obra_selecionada[2]
    situacao_atual = obra_selecionada[3]

    st.divider()

    # ==========================================
    # DADOS DA OBRA
    # ==========================================

    st.markdown(
        f"### 🏗️ {nome_obra}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"**📜 Contrato:** "
            f"{contrato or 'Não informado'}"
        )

    with col2:

        st.write(
            f"**👤 Responsável:** "
            f"{responsavel or 'Não informado'}"
        )

    with col3:

        st.write(
            f"**🚦 Situação atual:** "
            f"{situacao_atual or 'Não informada'}"
        )

    # ==========================================
    # ÍNDICE DA SITUAÇÃO ATUAL
    # ==========================================

    indice_situacao = 0

    if situacao_atual in situacoes:

        indice_situacao = situacoes.index(
            situacao_atual
        )

    # ==========================================
    # NOVA SITUAÇÃO
    # ==========================================

    nova_situacao = st.selectbox(
        "🚦 Situação da Obra",
        situacoes,
        index=indice_situacao,
        key=f"nova_situacao_obra_{id_obra}"
    )

    # ==========================================
    # MOTIVO DA PARALISAÇÃO
    # ==========================================

    motivo_paralisacao = None

    if nova_situacao == "4 – Paralisado":

        motivo_paralisacao = st.selectbox(
            "⛔ Motivo da Paralisação",
            [
                "Selecione o motivo"
            ] + motivos_paralisacao,
            key=f"motivo_paralisacao_{id_obra}"
        )

    # ==========================================
    # BOTÕES
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "❌ Cancelar",
            use_container_width=True,
            key="cancelar_situacao_obra"
        ):

            st.session_state.pop(
                "obra_situacao_id",
                None
            )

            st.rerun()

    with col2:

        salvar = st.button(
            "💾 Salvar Situação",
            type="primary",
            use_container_width=True,
            key="salvar_situacao_obra"
        )

    # ==========================================
    # SALVAR SITUAÇÃO
    # ==========================================

    if salvar:

        # ======================================
        # VALIDAR PARALISAÇÃO
        # ======================================

        if (
            nova_situacao == "4 – Paralisado"
            and motivo_paralisacao == "Selecione o motivo"
        ):
            st.warning(
                "⚠️ Selecione o motivo da paralisação."
            )
            return

        # ======================================
        # LIMPAR MOTIVO SE NÃO FOR PARALISADA
        # ======================================

        if nova_situacao != "4 – Paralisado":
            motivo_paralisacao = None

        try:

            # ==================================
            # ATUALIZAR OBRA
            # ==================================

            cursor.execute("""
                UPDATE obras
                SET
                    situacao = ?,
                    motivo_paralisacao = ?
                WHERE id = ?
            """, (
                nova_situacao,
                motivo_paralisacao,
                id_obra
            ))

            conn.commit()

            # ==================================
            # MENSAGEM DE SUCESSO
            # ==================================

            st.session_state[
                "situacao_obra_sucesso"
            ] = True

            # ==================================
            # FECHAR TELA DE ALTERAÇÃO
            # ==================================

            st.session_state.pop(
                "obra_situacao_id",
                None
            )

            # ==================================
            # LIMPAR SELEÇÃO DA TABELA
            # ==================================

            st.session_state.pop(
                "grid_situacao_obra",
                None
            )

            # ==================================
            # RECARREGAR TELA
            # ==================================

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"❌ Erro ao alterar situação: {e}"
            )

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

    with st.container(border=True):

        st.markdown("### 👤 Dados do Profissional")

        with st.form(
            "form_incluir_responsavel",
            clear_on_submit=True
        ):

            col1, col2 = st.columns(2)

            with col1:

                nome = st.text_input(
                    "👤 Nome Completo *",
                    placeholder="Ex: João da Silva"
                )

                cpf = st.text_input(
                    "🪪 CPF *",
                    placeholder="Ex: 000.000.000-00"
                )

                documento = st.text_input(
                    "📄 Documento",
                    placeholder="Ex: MG-12.345.678"
                )

            with col2:

                tipo_responsabilidade = st.selectbox(
                    "👷 Tipo de Responsabilidade *",
                    [
                        "Engenheiro",
                        "Arquiteto",
                        "Técnico",
                        "Fiscal de Obra",
                        "Outro"
                    ]
                )

                conselho = st.selectbox(
                    "🏛️ Conselho Profissional *",
                    [
                        "CREA",
                        "CAU",
                        "CFT",
                        "CRT",
                        "Outro"
                    ]
                )

                numero_conselho = st.text_input(
                    "🔢 Número do Conselho",
                    placeholder="Ex: CREA-MG 123456/D"
                )

            st.divider()

            salvar = st.form_submit_button(
                "💾 Salvar Responsável",
                type="primary",
                use_container_width=True
            )

    if salvar:

        nome = nome.strip()
        cpf = cpf.strip()
        documento = documento.strip()
        numero_conselho = numero_conselho.strip()

        if not nome:

            st.warning(
                "⚠️ Informe o nome do responsável."
            )

        elif not cpf:

            st.warning(
                "⚠️ Informe o CPF."
            )

        else:

            try:

                cursor.execute("""
                    SELECT id
                    FROM responsaveis
                    WHERE cpf = ?
                """, (
                    cpf,
                ))

                existente = cursor.fetchone()

                if existente:

                    st.warning(
                        "⚠️ Já existe um responsável "
                        "cadastrado com este CPF."
                    )

                else:

                    cursor.execute("""
                        INSERT INTO responsaveis (
                            nome,
                            cpf,
                            documento,
                            tipo_responsabilidade,
                            conselho,
                            numero_conselho,
                            ativo,
                            data_cadastro
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nome,
                        cpf,
                        documento,
                        tipo_responsabilidade,
                        conselho,
                        numero_conselho,
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

                st.error(
                    f"❌ Erro ao cadastrar responsável: {e}"
                )
def localizar_responsavel():

    st.subheader("🔎 Localizar Responsável")

    # ==========================================
    # BOTÃO VOLTAR
    # ==========================================

    if st.button(
        "⬅️ Voltar",
        key="voltar_localizar_responsavel"
    ):
        st.session_state["tela_responsavel"] = "Principal"

        st.session_state.pop(
            "responsavel_edicao_id",
            None
        )

        st.rerun()

    st.divider()

    # ==========================================
    # CAMPO DE PESQUISA
    # ==========================================

    busca = st.text_input(
        "🔍 Pesquisar responsável",
        placeholder=(
            "Digite nome, CPF, conselho "
            "ou número do conselho"
        ),
        key="pesquisa_responsavel"
    )

    # ==========================================
    # CONSULTAR RESPONSÁVEIS
    # ==========================================

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
            WHERE ativo = 1
            AND (
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
            WHERE ativo = 1
            ORDER BY nome
        """)

    registros = cursor.fetchall()

    # ==========================================
    # VERIFICAR RESULTADOS
    # ==========================================

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
            "Documento",
            "Responsabilidade",
            "Conselho",
            "Nº Conselho"
        ]
    )

    # ==========================================
    # JAVASCRIPT - DUPLO CLIQUE
    # ==========================================

    js_duplo_clique = JsCode("""
        function(params) {

            if (params.data) {

                params.api.deselectAll();

                params.node.setSelected(true);

            }

        }
    """)

    # ==========================================
    # CONFIGURAÇÃO DO AGGRID
    # ==========================================

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
        "onRowDoubleClicked"
    ] = js_duplo_clique

    # ==========================================
    # EXIBIR TABELA
    # ==========================================

    resposta = AgGrid(
        df,
        gridOptions=grid_options,
        height=350,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        key="grid_localizar_responsavel"
    )

    # ==========================================
    # PEGAR LINHA SELECIONADA
    # ==========================================

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

    # ==========================================
    # ABRIR ALTERAÇÃO
    # ==========================================

    if selecionados:

        selecionado = selecionados[0]

        id_responsavel = int(
            selecionado["ID"]
        )

        st.session_state[
            "responsavel_edicao_id"
        ] = id_responsavel

        st.session_state[
            "tela_responsavel"
        ] = "Alterar"

        st.rerun()
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

        if st.button(
            "⬅️ Voltar",
            key="voltar_alterar_sem_responsavel"
        ):
            st.session_state[
                "tela_responsavel"
            ] = "Principal"

            st.rerun()

        return

    cursor.execute("""
        SELECT
            nome,
            cpf,
            documento,
            tipo_responsabilidade,
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

        st.session_state.pop(
            "responsavel_edicao_id",
            None
        )

        return

    (
        nome_atual,
        cpf_atual,
        documento_atual,
        responsabilidade_atual,
        conselho_atual,
        numero_conselho_atual
    ) = registro

    if st.button(
        "⬅️ Voltar",
        key="voltar_alterar_responsavel"
    ):
        st.session_state[
            "tela_responsavel"
        ] = "Localizar"

        st.rerun()

    st.divider()

    with st.container(border=True):

        st.markdown(
            f"### 👤 {nome_atual}"
        )

        with st.form(
            "form_alterar_responsavel"
        ):

            col1, col2 = st.columns(2)

            with col1:

                nome = st.text_input(
                    "👤 Nome Completo *",
                    value=nome_atual or ""
                )

                cpf = st.text_input(
                    "🪪 CPF *",
                    value=cpf_atual or ""
                )

                documento = st.text_input(
                    "📄 Documento",
                    value=documento_atual or ""
                )

            responsabilidades = [
                "Engenheiro",
                "Arquiteto",
                "Técnico",
                "Fiscal de Obra",
                "Outro"
            ]

            conselhos = [
                "CREA",
                "CAU",
                "CFT",
                "CRT",
                "Outro"
            ]

            with col2:

                if responsabilidade_atual in responsabilidades:

                    indice_responsabilidade = (
                        responsabilidades.index(
                            responsabilidade_atual
                        )
                    )

                else:

                    indice_responsabilidade = 0

                tipo_responsabilidade = st.selectbox(
                    "👷 Tipo de Responsabilidade *",
                    responsabilidades,
                    index=indice_responsabilidade
                )

                if conselho_atual in conselhos:

                    indice_conselho = (
                        conselhos.index(
                            conselho_atual
                        )
                    )

                else:

                    indice_conselho = 0

                conselho = st.selectbox(
                    "🏛️ Conselho Profissional *",
                    conselhos,
                    index=indice_conselho
                )

                numero_conselho = st.text_input(
                    "🔢 Número do Conselho",
                    value=numero_conselho_atual or ""
                )

            st.divider()

            salvar = st.form_submit_button(
                "💾 Salvar Alterações",
                type="primary",
                use_container_width=True
            )

    if salvar:

        nome = nome.strip()
        cpf = cpf.strip()
        documento = documento.strip()
        numero_conselho = numero_conselho.strip()

        if not nome:

            st.warning(
                "⚠️ Informe o nome."
            )

        elif not cpf:

            st.warning(
                "⚠️ Informe o CPF."
            )

        else:

            try:

                cursor.execute("""
                    SELECT id
                    FROM responsaveis
                    WHERE cpf = ?
                    AND id <> ?
                """, (
                    cpf,
                    id_responsavel
                ))

                cpf_existente = cursor.fetchone()

                if cpf_existente:

                    st.warning(
                        "⚠️ Já existe outro responsável "
                        "com este CPF."
                    )

                else:

                    cursor.execute("""
                        UPDATE responsaveis
                        SET
                            nome = ?,
                            cpf = ?,
                            documento = ?,
                            tipo_responsabilidade = ?,
                            conselho = ?,
                            numero_conselho = ?
                        WHERE id = ?
                    """, (
                        nome,
                        cpf,
                        documento,
                        tipo_responsabilidade,
                        conselho,
                        numero_conselho,
                        id_responsavel
                    ))

                    conn.commit()

                    st.session_state[
                        "responsavel_alterado_sucesso"
                    ] = True

                    st.session_state.pop(
                        "responsavel_edicao_id",
                        None
                    )

                    st.session_state[
                        "tela_responsavel"
                    ] = "Principal"

                    st.rerun()

            except Exception as e:

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

        # ==========================================
        # RESPONSÁVEL PELA OBRA
        # ==========================================

        cursor.execute("""
            SELECT
                id,
                nome,
                tipo_responsabilidade
            FROM responsaveis
            WHERE ativo = 1
            ORDER BY nome
        """)

        responsaveis_cadastrados = cursor.fetchall()

        opcoes_responsaveis = {
            "Selecione o responsável": {
                "id": None,
                "nome": "",
                "tipo_responsabilidade": ""
            }
        }

        for registro in responsaveis_cadastrados:

            id_responsavel = registro[0]
            nome_responsavel = registro[1]
            tipo_responsavel = registro[2]

            opcoes_responsaveis[nome_responsavel] = {
                "id": id_responsavel,
                "nome": nome_responsavel,
                "tipo_responsabilidade": tipo_responsavel
            }

        responsavel_selecionado = st.selectbox(
            "👤 Responsável pela Obra",
            options=list(
                opcoes_responsaveis.keys()
            ),
            key=f"responsavel_{cadastro_id}"
        )

        dados_responsavel = (
            opcoes_responsaveis[
                responsavel_selecionado
            ]
        )

        responsavel = (
            dados_responsavel["nome"]
        )

        tipo_responsabilidade = (
            dados_responsavel[
                "tipo_responsabilidade"
            ]
        )

        # ==========================================
        # TIPO DE RESPONSABILIDADE
        # ==========================================

        st.text_input(
            "👷 Tipo de Responsabilidade",
            value=tipo_responsabilidade,
            disabled=True,
            key=(
                f"tipo_responsabilidade_visual_"
                f"{cadastro_id}_"
                f"{dados_responsavel['id']}"
            )
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

                    rua = (
                        dados_endereco.get("road")
                        or dados_endereco.get("pedestrian")
                        or dados_endereco.get("residential")
                        or "Não informado"
                    )

                    numero_mapa = (
                        dados_endereco.get("house_number")
                        or "Não informado"
                    )

                    bairro_mapa = (
                        dados_endereco.get("suburb")
                        or dados_endereco.get("neighbourhood")
                        or dados_endereco.get("quarter")
                        or dados_endereco.get("city_district")
                        or dados_endereco.get("district")
                        or "Não informado"
                    )

                    cidade = (
                        dados_endereco.get("city")
                        or dados_endereco.get("town")
                        or dados_endereco.get("municipality")
                        or dados_endereco.get("village")
                        or "Não informado"
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
                numero if numero else "Não informado"
            )

        with col2:

            st.write(
                "🏘️ **Bairro:**",
                bairro if bairro else "Não informado"
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

        endereco = (
            f"{dados.get('rua', 'Não informado')}, "
            f"{numero if numero else 'S/N'} - "
            f"{bairro if bairro else 'Não informado'}, "
            f"{dados.get('cidade', 'Não informado')} - "
            f"{dados.get('estado', 'Não informado')}, "
            f"{dados.get('pais', 'Brasil')}"
        )

        st.session_state["endereco_obra"] = endereco

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

                # Guarda a confirmação
                st.session_state["obra_cadastrada_sucesso"] = True

                # Fecha os campos de Incluir
                st.session_state["tela_obras"] = "Principal"

                # Limpa dados temporários da localização
                st.session_state.pop("latitude_obra", None)
                st.session_state.pop("longitude_obra", None)
                st.session_state.pop("endereco_obra", None)
                st.session_state.pop("dados_endereco_obra", None)

                # Reinicia a tela
                st.rerun()

            except Exception as e:
                st.error(
                    f"❌ Erro ao cadastrar obra: {e}"
                )
def alterar_obra():

    st.subheader("✏️ Alterar Obra")

    # Pega o ID da obra escolhida na tela Localizar
    id_obra = st.session_state.get("obra_edicao_id")

    # Se nenhuma obra foi selecionada
    if id_obra is None:
        st.warning("⚠️ Nenhuma obra foi selecionada para alteração.")
        return

    # Busca a obra no banco
    cursor.execute("""
        SELECT *
        FROM obras
        WHERE id = ?
    """, (id_obra,))

    dados = cursor.fetchone()

    if dados is None:
        st.error("❌ Obra não encontrada no banco de dados.")
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
