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
        responsavel TEXT,
        tipo_obra TEXT,
        valor_obra REAL,
        situacao TEXT,
        prazo_dias INTEGER,
        data_cadastro TEXT
    )
''')

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

def incluir_item_obra():

    st.subheader("🧱 Itens da Obra")

    # ==========================================
    # LISTA TEMPORÁRIA
    # ==========================================

    if "itens_temporarios_obra" not in st.session_state:
        st.session_state["itens_temporarios_obra"] = []

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

    # ==========================================
    # SELECIONAR OBRA
    # ==========================================

    opcoes_obras = {}

    for registro in obras:

        id_obra = registro[0]
        nome_lista = registro[1]
        contrato_lista = registro[2]

        texto = (
            f"{id_obra} - {nome_lista} | "
            f"Contrato: {contrato_lista}"
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

    # ==========================================
    # SE TROCOU DE OBRA, LIMPA ITENS TEMPORÁRIOS
    # ==========================================

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

    st.session_state[
        "obra_itens_anterior"
    ] = obra_id

    # ==========================================
    # BUSCAR DADOS DA OBRA
    # ==========================================

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
    # VALOR JÁ REGISTRADO
    # ==========================================

    try:
        cursor.execute("""
            SELECT
                COALESCE(SUM(valor_total), 0)
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

    # ==========================================
    # INFORMAÇÕES DA OBRA
    # ==========================================

    st.markdown(
        "### 🏗️ Informações da Obra"
    )

    with st.container(
        border=True
    ):

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

    # ==========================================
    # CONTROLE FINANCEIRO
    # ==========================================

    st.markdown(
        "### 💰 Controle dos Itens"
    )

    col_valor1, col_valor2, col_valor3 = (
        st.columns(3)
    )

    with col_valor1:

        with st.container(
            border=True
        ):

            st.caption(
                "💰 VALOR DA OBRA"
            )

            st.markdown(
                f"##### {moeda(valor_obra)}"
            )

    with col_valor2:

        with st.container(
            border=True
        ):

            st.caption(
                "📦 VALOR REGISTRADO"
            )

            st.markdown(
                f"##### {moeda(valor_utilizado)}"
            )

    with col_valor3:

        with st.container(
            border=True
        ):

            st.caption(
                "💵 SALDO DISPONÍVEL"
            )

            st.markdown(
                f"##### {moeda(saldo_disponivel)}"
            )

    st.markdown("---")

    # ==========================================
    # GERAR CÓDIGO VISUAL
    # ==========================================

    try:

        cursor.execute("""
            SELECT
                COALESCE(MAX(id), 0) + 1
            FROM itens
        """)

        proximo_numero = (
            cursor.fetchone()[0]
        )

    except Exception:

        proximo_numero = 1

    quantidade_temporaria = len(
        st.session_state[
            "itens_temporarios_obra"
        ]
    )

    codigo_visual = (
        f"ITEM"
        f"{proximo_numero + quantidade_temporaria:05d}"
    )

    # ==========================================
    # NOVO ITEM
    # ==========================================

    st.markdown(
        "### 📦 Novo Item"
    )

    # clear_on_submit limpa os campos
    # sempre que clicar em Adicionar Item

    with st.form(
        "form_adicionar_item_obra",
        clear_on_submit=True
    ):

        col_item1, col_item2 = (
            st.columns([1, 3])
        )

        with col_item1:

            st.text_input(
                "🔢 Código",
                value=codigo_visual,
                disabled=True
            )

        with col_item2:

            descricao = st.text_input(
                "📝 Descrição",
                placeholder="Ex: Areia lavada"
            )

        col_item3, col_item4 = (
            st.columns(2)
        )

        with col_item3:

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

        with col_item4:

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

        col_item5, col_item6 = (
            st.columns(2)
        )

        with col_item5:

            quantidade = st.number_input(
                "📦 Quantidade",
                min_value=0.0,
                step=1.0
            )

        with col_item6:

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

    # ==========================================
    # ADICIONAR À LISTA TEMPORÁRIA
    # ==========================================

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

            # Soma os itens que ainda
            # não foram registrados

            total_temporario = sum(
                float(
                    item["valor_total"]
                )
                for item in st.session_state[
                    "itens_temporarios_obra"
                ]
            )

            total_com_novo_item = (
                total_temporario
                + valor_total_item
            )

            # ==================================
            # NÃO DEIXA ULTRAPASSAR A OBRA
            # ==================================

            if (
                total_com_novo_item
                > saldo_disponivel
            ):

                excedente = (
                    total_com_novo_item
                    - saldo_disponivel
                )

                st.error(
                    "❌ Item não adicionado. "
                    "O valor ultrapassaria o "
                    "saldo disponível da obra "
                    f"em {moeda(excedente)}."
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

    # ==========================================
    # CONFIRMAÇÃO DE ADIÇÃO
    # ==========================================

    if st.session_state.get(
        "item_adicionado_temporario",
        False
    ):

        st.success(
            "✅ Item adicionado à lista. "
            "Clique em Salvar Registro para "
            "gravar os itens na obra."
        )

        st.session_state[
            "item_adicionado_temporario"
        ] = False

    # ==========================================
    # ITENS AGUARDANDO REGISTRO
    # ==========================================

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

        # ======================================
        # TOTAL TEMPORÁRIO
        # ======================================

        total_temporario = sum(
            float(
                item["valor_total"]
            )
            for item in itens_temporarios
        )

        saldo_apos_registro = (
            saldo_disponivel
            - total_temporario
        )

        col_temp1, col_temp2 = (
            st.columns(2)
        )

        with col_temp1:

            with st.container(
                border=True
            ):

                st.caption(
                    "📦 TOTAL DESTE REGISTRO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(total_temporario)}"
                )

        with col_temp2:

            with st.container(
                border=True
            ):

                st.caption(
                    "💰 SALDO APÓS REGISTRO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(saldo_apos_registro)}"
                )

        # ======================================
        # REMOVER ÚLTIMO ITEM
        # ======================================

        col_acao1, col_acao2 = (
            st.columns([1, 2])
        )

        with col_acao1:

            if st.button(
                "↩️ Remover Último",
                use_container_width=True,
                key=f"remover_ultimo_item_{obra_id}"
            ):

                st.session_state[
                    "itens_temporarios_obra"
                ].pop()

                st.rerun()

        # ======================================
        # SALVAR REGISTRO
        # ======================================

        with col_acao2:

            salvar_registro = st.button(
                "💾 Salvar Registro",
                type="primary",
                use_container_width=True,
                key=f"salvar_registro_{obra_id}"
            )

        if salvar_registro:

            try:

                # ==================================
                # RECALCULAR SALDO DO BANCO
                # ==================================

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
                    float(
                        item["valor_total"]
                    )
                    for item
                    in itens_temporarios
                )

                # ==================================
                # VALIDAÇÃO FINAL
                # ==================================

                if (
                    total_registro
                    > saldo_atual
                ):

                    st.error(
                        "❌ Registro não salvo. "
                        "O valor total dos itens "
                        "ultrapassa o saldo "
                        "disponível da obra."
                    )

                else:

                    # ==================================
                    # SALVAR CADA ITEM
                    # ==================================

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

                        # ==============================
                        # VERIFICAR SE JÁ EXISTE
                        # ==============================

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

                        # ==============================
                        # REUTILIZA ITEM EXISTENTE
                        # ==============================

                        if item_existente:

                            item_id = (
                                item_existente[0]
                            )

                        # ==============================
                        # CADASTRA NOVO ITEM
                        # ==============================

                        else:

                            cursor.execute("""
                                SELECT
                                    COALESCE(
                                        MAX(id),
                                        0
                                    ) + 1
                                FROM itens
                            """)

                            numero_item = (
                                cursor.fetchone()[0]
                            )

                            codigo_item = (
                                f"ITEM"
                                f"{numero_item:05d}"
                            )

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

                        # ==============================
                        # VINCULAR À OBRA
                        # ==============================

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

                    # ==================================
                    # CONFIRMAR TRANSAÇÃO
                    # ==================================

                    conn.commit()

                    # ==================================
                    # LIMPAR LISTA TEMPORÁRIA
                    # ==================================

                    st.session_state[
                        "itens_temporarios_obra"
                    ] = []

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

    # ==========================================
    # CONFIRMAÇÃO DO REGISTRO
    # ==========================================

    if st.session_state.get(
        "registro_itens_salvo",
        False
    ):

        st.success(
            "✅ Registro de itens salvo "
            "com sucesso!"
        )

        st.session_state[
            "registro_itens_salvo"
        ] = False

    # ==========================================
    # ITENS JÁ REGISTRADOS NA OBRA
    # ==========================================

    st.markdown("---")

    st.subheader(
        "📋 Itens Registrados na Obra"
    )

    try:

        cursor.execute("""
            SELECT
                io.id,
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

            ORDER BY i.descricao
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

    # ==========================================
    # MOSTRAR ITENS REGISTRADOS
    # ==========================================

    if itens_registrados:

        df_registrados = pd.DataFrame(
            itens_registrados,
            columns=[
                "ID",
                "Código",
                "Descrição",
                "Unidade",
                "Quantidade",
                "Valor Unitário",
                "Valor Total"
            ]
        )

        df_exibicao = (
            df_registrados.copy()
        )

        df_exibicao[
            "Valor Unitário"
        ] = df_exibicao[
            "Valor Unitário"
        ].apply(
            moeda
        )

        df_exibicao[
            "Valor Total"
        ] = df_exibicao[
            "Valor Total"
        ].apply(
            moeda
        )

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )

        # ======================================
        # TOTAL JÁ REGISTRADO
        # ======================================

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

        col_final1, col_final2 = (
            st.columns(2)
        )

        with col_final1:

            with st.container(
                border=True
            ):

                st.caption(
                    "📦 TOTAL REGISTRADO"
                )

                st.markdown(
                    f"##### "
                    f"{moeda(total_registrado)}"
                )

        with col_final2:

            with st.container(
                border=True
            ):

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

        # IMPORTANTE:
        # salva antes de chamar qualquer função
        st.session_state["ultimo_menu"] = escolha

    # ==========================================
    # ABRIR TELAS
    # ==========================================

    if escolha == "Cadastro de Obras 🛎️":

        cadastro_de_obras()

    elif escolha == "Dashboard 📊":

        dashboard()

    elif escolha == "👨‍🔧 Cadastro de Funcionário":

        cadastrar_funcionario()

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
