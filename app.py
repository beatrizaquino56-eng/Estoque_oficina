import streamlit as st
import pandas as pd
import re
import io
from supabase import create_client, Client

# Bibliotecas para geração do PDF profissional
from reportlab.lib.pagesizes import a4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. CONFIGURAÇÃO DE CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://lgpcpnxhkogtvhjtfwya.supabase.co"
SUPABASE_KEY = "sb_publishable_1kunRmsK4SdXCk849paiyg_1OaraKs_"

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚙️ Sistema Integrado - Oficina Mecânica")
st.markdown("---")

# --- 2. MENU PRINCIPAL DE NAVEGAÇÃO (Com Novo Módulo de Orçamentos!) ---
modulo = st.sidebar.radio(
    "Selecione o Módulo:", 
    ["👥 Clientes & Veículos", "📦 Gerenciar Estoque", "📋 Criar Orçamento (PDF)"]
)

# Função para formatar o telefone com parênteses no DDD e hífen
def formatar_telefone(num):
    apenas_numeros = re.sub(r'\D', '', num)
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
    elif len(apenas_numeros) == 10:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    return num

# Função Inteligente para gerar o PDF do Orçamento
def gerar_pdf_orcamento(cliente, telefone, veiculo, lista_pecas):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=a4,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Customização de estilos visuais para o PDF (Design Limpo e Elegante)
    estilo_titulo = ParagraphStyle(
        'TituloOficina',
        parent=estilos['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#111111"),
        spaceAfter=5
    )
    estilo_sub = ParagraphStyle(
        'SubOrcamento',
        parent=estilos['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20
    )
    estilo_texto = ParagraphStyle(
        'TextoNormal',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#222222"),
        spaceAfter=6
    )
    
    # 1. Cabeçalho da Empresa
    elementos.append(Paragraph("<b>LAUD CAMBIOS AUTO PEÇAS E MECÂNICA</b>", estilo_titulo))
    elementos.append(Paragraph("Especializada em Câmbios e Diferenciais", estilo_texto))
    elementos.append(Paragraph("<b>ORÇAMENTO DE MANUTENÇÃO</b>", estilo_sub))
    elementos.append(Spacer(1, 10))
    
    # 2. Dados do Cliente e Veículo
    elementos.append(Paragraph(f"<b>Cliente:</b> {cliente}", estilo_texto))
    elementos.append(Paragraph(f"<b>Telefone:</b> {telefone}", estilo_texto))
    elementos.append(Paragraph(f"<b>Veículo / Câmbio:</b> {veiculo}", estilo_texto))
    elementos.append(Spacer(1, 15))
    
    # 3. Tabela de Peças e Serviços
    # Cabeçalho da tabela
    dados_tabela = [["Item / Descrição da Peça", "Valor Unitário (R$)"]]
    
    total_geral = 0.0
    for item in lista_pecas:
        dados_tabela.append([item['descricao'], f"R$ {item['valor']:.2f}"])
        total_geral += item['valor']
        
    # Linha do Total Geral no fim da tabela
    dados_tabela.append(["<b>TOTAL DO ORÇAMENTO</b>", f"<b>R$ {total_geral:.2f}</b>"])
    
    # Estilização da Tabela (Preto e Branco clássico para impressão)
    tabela = Table(dados_tabela, colWidths=[380, 130])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#222222")),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'), # Alinha valores à direita
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#DDDDDD")),
        ('LINEABOVE', (0, -1), (1, -1), 1.5, colors.HexColor("#111111")), # Linha forte no total
    ]))
    
    elementos.append(tabela)
    
    # 4. Rodapé / Termos básicos
    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("<i>* Orçamento sujeito a alterações caso surjam novos defeitos ocultos constatados na desmontagem.</i>", estilo_texto))
    elementos.append(Paragraph("<i>Validade deste orçamento: 10 dias.</i>", estilo_texto))
    
    # Constrói o documento
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ==============================================================================
#                      MÓDULO: CLIENTES & VEÍCULOS
# ==============================================================================
if modulo == "👥 Clientes & Veículos":
    st.header("👥 Cadastro de Clientes e Entrada de Veículos")
    aba_cad_cliente, aba_ver_clientes = st.tabs(["📝 Cadastrar Cliente/Carro", "📋 Carros no Pátio / OS"])
    
    with aba_cad_cliente:
        st.subheader("📝 Nova Ordem de Entrada")
        col1, col2 = st.columns(2)
        with col1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            veiculo = st.text_input("Veículo (Modelo/Ano)", placeholder="Ex: Gol G6 2014")
            placa_input = st.text_input("Placa do Carro", placeholder="Ex: ABC1234")
            placa = placa_input.upper().strip() 
        with col2:
            telefone_input = st.text_input("Número de Telefone (com DDD)", placeholder="Ex: 16999999999")
            telefone = formatar_telefone(telefone_input)
            defeito = st.text_area("Defeito Relatado / Sintomas", placeholder="Ex: Barulho na suspensão...")
            
        if st.button("Gravar Entrada do Veículo", key="btn_cliente"):
            if nome_cliente == "" or veiculo == "":
                st.error("Por favor, preencha pelo menos o Nome do Cliente e o Veículo!")
            else:
                novo_cliente = {"nome_cliente": nome_cliente, "veiculo": veiculo, "placa": placa, "telefone": telefone, "defeito": defeito, "status": "Aguardando Diagnóstico"}
                supabase.table("clientes").insert(novo_cliente).execute()
                st.success(f"Sucesso! Registro de '{nome_cliente}' gravado!")
                st.rerun()
                
    with aba_ver_clientes:
        st.subheader("📋 Veículos no Pátio")
        resposta_clientes = supabase.table("clientes").select("*").order("created_at", desc=True).execute()
        dados_clientes = pd.DataFrame(resposta_clientes.data)
        
        if not dados_clientes.empty:
            c_busca, c_filtro = st.columns([2, 1])
            with c_busca:
                busca_pacio = st.text_input("🔍 Buscar por Nome do Cliente ou Placa:", placeholder="Digite para filtrar...")
            with c_filtro:
                filtro_status = st.selectbox("🚦 Filtrar por Status:", ["Todos", "Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"])
            
            if busca_pacio:
                dados_clientes = dados_clientes[dados_clientes['nome_cliente'].str.contains(busca_pacio, case=False, na=False) | dados_clientes['placa'].str.contains(busca_pacio, case=False, na=False)]
            if filtro_status != "Todos":
                dados_clientes = dados_clientes[dados_clientes['status'] == filtro_status]
            
            st.markdown("---")
            if dados_clientes.empty:
                st.info("Nenhum veículo encontrado.")
            else:
                for index, row in dados_clientes.iterrows():
                    status_atual = row['status']
                    cor_status = "🟡" if status_atual == "Aguardando Diagnóstico" else "🔵" if status_atual == "Em Manutenção" else "🟠" if status_atual == "Aguardando Peças" else "🟢"
                    
                    with st.expander(f"{cor_status} {row['veiculo']} — Placa: {row['placa']} ({row['nome_cliente']})", expanded=True):
                        st.markdown(f"**👤 Cliente:** {row['nome_cliente']} | **📞 Tel:** {row['telefone']}")
                        st.markdown(f"**🛠️ Defeito Relatado:** {row['defeito']}")
                        st.markdown(f"**📌 Status Atual:** `{status_atual}`")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            novo_status = st.selectbox("Alterar Status para:", ["Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"], key=f"status_{row['id']}")
                            if st.button("🔄 Atualizar", key=f"btn_status_{row['id']}"):
                                supabase.table("clientes").update({"status": novo_status}).eq("id", row['id']).execute()
                                st.success("Status Atualizado!")
                                st.rerun()
                        with c2:
                            st.write("")
                            if st.button("❌ Apagar Registro", key=f"btn_del_{row['id']}"):
                                supabase.table("clientes").delete().eq("id", row['id']).execute()
                                st.success("Removido!")
                                st.rerun()
        else:
            st.info("Nenhum veículo no pátio atualmente.")

# ==============================================================================
#                      MÓDULO: GERENCIAR ESTOQUE
# ==============================================================================
elif modulo == "📦 Gerenciar Estoque":
    st.header("📦 Gerenciamento de Peças e Estoque")
    aba_entrada, aba_saida, aba_excluir = st.tabs(["📥 Entradas / Reposição", "📤 Dar Saída de Peça", "❌ Excluir Item"])

    with aba_entrada:
        st.subheader("📥 Entrada de Mercadorias")
        tipo_entrada = st.radio("Selecione o tipo de operação:", ["Cadastrar um produto NOVO", "Adicionar quantidade a um produto JÁ CADASTRADO"], horizontal=True)
        
        if tipo_entrada == "Cadastrar um produto NOVO":
            st.write("### 📝 Preencha os dados do novo item:")
            col1, col2 = st.columns(2)
            with col1:
                nome_produto = st.text_input("Descrição do Produto", placeholder="Ex: Kit de Embreagem", key="add_nome")
                codigo_original = st.text_input("Código Original / Nº Montadora", placeholder="Ex: 5Z0141025", key="add_cod_orig").upper()
                marca = st.text_input("Marca/Fabricante", placeholder="Ex: LUK", key="add_marca")
                quantidade = st.number_input("Quantidade Inicial", min_value=0, value=0, step=1, key="add_qtd")
                preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, step=0.50, key="add_custo")
            with col2:
                ncm = st.text_input("Código NCM (8 dígitos)", max_chars=8, placeholder="Ex: 87082999", key="add_ncm")
                cest = st.text_input("Código CEST", max_chars=9, placeholder="Ex: 16.001.00", key="add_cest")
                csosn = st.text_input("Código CSOSN", max_chars=3, placeholder="Ex: 500", key="add_csosn")
                origem = st.selectbox("Origem da Mercadoria", ["0 - Nacional", "1 - Estrangeira", "2 - Adquirida no Mercado Interno"], key="add_origem")
                peso = st.number_input("Peso do Produto (Kg)", min_value=0.000, value=0.000, step=0.050, format="%.3f", key="add_peso")

            if st.button("Gravar Novo Produto", key="btn_gravar"):
                if nome_produto == "":
                    st.error("Por favor, digite o nome do produto antes de salvar!")
                else:
                    novo_produto = {"descricao": nome_produto, "codigo_original": codigo_original, "marca": marca, "quantidade": int(quantidade), "ncm": ncm}
                    supabase.table("estoque").insert(novo_produto).execute()
                    st.success(f"Sucesso! O produto '{nome_produto}' foi salvo na Nuvem!")
                    st.rerun()
                    
        else:
            st.write("### 🔄 Reposição de Estoque Existente:")
            resposta_entrada = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
            dados_produtos = pd.DataFrame(resposta_entrada.data)
            
            if dados_produtos.empty:
                st.info("Nenhum produto cadastrado.")
            else:
                opcoes_entrada = {f"{row['descricao']} - Ult: {row['quantidade']}": row['id'] for index, row in dados_produtos.iterrows()}
                selecao_entrada = st.selectbox("Escolha o produto que chegou:", list(opcoes_entrada.keys()), key="sel_reposicao")
                id_produto_reposicao = opcoes_entrada[selecao_entrada]
                qtd_atual_banco = dados_produtos[dados_produtos['id'] == id_produto_reposicao]['quantidade'].values[0]
                qtd_novas_pecas = st.number_input("Quantidade de peças:", min_value=1, value=1, step=1, key="qtd_reposicao")
                
                if st.button("Confirmar Entrada", key="btn_reposicao"):
                    nova_quantidade = int(qtd_atual_banco + qtd_novas_pecas)
                    supabase.table("estoque").update({"quantidade": nova_quantidade}).eq("id", id_produto_reposicao).execute()
                    st.success("Estoque atualizado!")
                    st.rerun()

    with aba_saida:
        st.subheader("🛠️ Dar Baixa em Peça Utilizada")
        resposta_saida = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
        dados_produtos_saida = pd.DataFrame(resposta_saida.data)
        
        if dados_produtos_saida.empty:
            st.info("Nenhum produto cadastrado.")
        else:
            opcoes_produtos = {f"{row['descricao']} - (Disponível: {row['quantidade']})": row['id'] for index, row in dados_produtos_saida.iterrows()}
            selecao = st.selectbox("Selecione o Produto:", list(opcoes_produtos.keys()), key="sel_saida")
            produto_id_selecionado = opcoes_produtos[selecao]
            qtd_atual = dados_produtos_saida[dados_produtos_saida['id'] == produto_id_selecionado]['quantidade'].values[0]
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, max_value=int(qtd_atual) if qtd_atual > 0 else 1, step=1, key="qtd_saida")
            
            if st.button("Confirmar Saída", key="btn_saida"):
                if qtd_atual <= 0:
                    st.error("Estoque zerado.")
                else:
                    nova_quantidade_saida = int(qtd_atual - qtd_saida)
                    supabase.table("estoque").update({"quantidade": nova_quantidade_saida}).eq("id", produto_id_selecionado).execute()
                    st.success("Baixa realizada!")
                    st.rerun()

    with aba_excluir:
        st.subheader("❌ Remover Item Definitivamente")
        resposta_excluir = supabase.table("estoque").select("id, descricao, codigo_original").order("descricao").execute()
        dados_produtos_excluir = pd.DataFrame(resposta_excluir.data)
        
        if dados_produtos_excluir.empty:
            st.info("Nenhum produto cadastrado.")
        else:
            opcoes_excluir = {f"{row['descricao']} (Cód: {row['codigo_original']})": row['id'] for index, row in dados_produtos_excluir.iterrows()}
            selecao_excluir = st.selectbox("Selecione o produto:", list(opcoes_excluir.keys()), key="sel_excluir")
            id_produto_excluir = opcoes_excluir[selecao_excluir]
            if st.button("🔥 Apagar Produto", key="btn_deletar"):
                supabase.table("estoque").delete().eq("id", id_produto_excluir).execute()
                st.success("Removido!")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Relatório Atual de Estoque")
    busca_codigo = st.text_input("🔍 Buscar por Código Original:", placeholder="Digite o código...")
    resposta_final = supabase.table("estoque").select("*").order("descricao").execute()
    dados_finais = pd.DataFrame(resposta_final.data)
    
    if not dados_finais.empty:
        colunas_ordenadas = ["id", "codigo_original", "ncm", "descricao", "marca", "quantidade", "created_at"]
        colunas_existem = [c for c in colunas_ordenadas if c in dados_finais.columns]
        if busca_codigo:
            dados_finais = dados_finais[dados_finais['codigo_original'].str.contains(busca_codigo, case=False, na=False)]
        st.dataframe(dados_finais[colunas_existem], use_container_width=True)

# ==============================================================================
#                      MÓDULO: CRRIAR ORÇAMENTO (NEW!)
# ==============================================================================
elif modulo == "📋 Criar Orçamento (PDF)":
    st.header("📋 Gerador de Orçamentos da Oficina")
    st.write("Preencha os dados abaixo para gerar o PDF oficial.")
    
    # Inicializa a lista de peças na sessão do aplicativo para não perder os dados ao clicar em botões
    if 'pecas_orcamento' not in st.session_state:
        st.session_state.pecas_orcamento = []
        
    c1, c2 = st.columns(2)
    with c1:
        orc_cliente = st.text_input("Nome do Cliente:", placeholder="Ex: Roberto Almeida")
        orc_veiculo = st.text_input("Veículo ou Modelo do Câmbio:", placeholder="Ex: Amarok - Câmbio Automático ZF8HP")
    with c2:
        orc_tel_input = st.text_input("Telefone do Cliente:", placeholder="Ex: 16988888888")
        orc_tel = formatar_telefone(orc_tel_input)
        
    st.markdown("---")
    st.subheader("🛠️ Adicionar Peças / Serviços")
    
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        peca_desc = st.text_input("Descrição da Peça ou Serviço:", placeholder="Ex: Jogo de Juntas do Câmbio ou Mão de Obra de Montagem", key="input_peca_desc")
    with col_p2:
        peca_val = st.number_input("Valor (R$):", min_value=0.0, value=0.0, step=10.0, key="input_peca_val")
        
    if st.button("➕ Adicionar Peça ao Orçamento"):
        if peca_desc == "":
            st.error("Digite a descrição da peça!")
        else:
            # Salva na lista temporária da sessão
            st.session_state.pecas_orcamento.append({
                "descricao": peca_desc,
                "valor": float(peca_val)
            })
            st.success(f"'{peca_desc}' adicionado!")
            st.rerun()
            
    # Exibe a lista de peças adicionadas até agora
    if st.session_state.pecas_orcamento:
        st.markdown("### 📝 Itens incluídos:")
        df_temp = pd.DataFrame(st.session_state.pecas_orcamento)
        df_temp.index = df_temp.index + 1 # Começa a contagem em 1 em vez de 0
        st.table(df_temp.style.format({"valor": "R$ {:.2f}"}))
        
        total_acumulado = sum(item['valor'] for item in st.session_state.pecas_orcamento)
        st.markdown(f"### **Total Atual: R$ {total_acumulado:.2f}**")
        
        c_acao1, c_acao2 = st.columns(2)
        with c_acao1:
            # Botão de download do PDF
            if orc_cliente == "" or orc_veiculo == "":
                st.warning("Preencha o nome do cliente e o veículo para liberar o PDF.")
            else:
                pdf_data = gerar_pdf_orcamento(orc_cliente, orc_tel, orc_veiculo, st.session_state.pecas_orcamento)
                
                st.download_button(
                    label="📥 Baixar Orçamento em PDF",
                    data=pdf_data,
                    file_name=f"Orcamento_{orc_cliente.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        with c_acao2:
            if st.button("🧹 Limpar Tudo / Novo Orçamento"):
                st.session_state.pecas_orcamento = []
                st.rerun()
    else:
        st.info("Nenhuma peça adicionada ao orçamento ainda.")