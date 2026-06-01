import streamlit as st
import pandas as pd
import re
import io
from supabase import create_client, Client
from fpdf import FPDF  # Usando FPDF2 para evitar os travamentos de cache da nuvem

# --- 1. CONFIGURAÇÃO DE CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://lgpcpnxhkogtvhjtfwya.supabase.co"
SUPABASE_KEY = "sb_publishable_1kunRmsK4SdXCk849paiyg_1oaraKs_"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚙️ Sistema Integrado - Oficina Mecânica")
st.markdown("---")

# --- 2. MENU PRINCIPAL DE NAVEGAÇÃO ---
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

# Função para gerar o PDF do Orçamento (Estilo o impresso da Laud)
def gerar_pdf_orcamento_fpdf(cliente, telefone, veiculo, lista_pecas):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho da Empresa
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(140, 10, txt="LAUD AUTOPECAS E MECANICA", ln=False)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 10, txt="ORCAMENTO", ln=True, align="R")
    
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(140, 5, txt="Avenida Maria Antonia Camargo de Oliveira, 3053 - Vila Ferroviaria", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 5, txt=f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}", ln=True, align="R")
    
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(190, 5, txt="Araraquara - SP | Fone: (16) 3336-8899", ln=True)
    pdf.ln(10)
    
    # Bloco de Informações do Cliente
    pdf.set_fill_color(250, 250, 250)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 36, 190, 24, "DF")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(190, 6, txt=f" Cliente: {cliente}", ln=True)
    pdf.cell(190, 6, txt=f" Telefone: {telefone}", ln=True)
    pdf.cell(190, 6, txt=f" Veiculo / Cambio: {veiculo}", ln=True)
    pdf.ln(10)
    
    # Tabela de Itens (Fundo escuro profissional)
    pdf.set_fill_color(34, 34, 34)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(140, 8, txt=" Descricao da Peca / Servico", border=0, fill=True)
    pdf.cell(50, 8, txt="Valor Total (R$) ", border=0, fill=True, align="R", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    
    total_geral = 0.0
    for item in lista_pecas:
        desc_limpa = item['descricao'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(140, 8, txt=f" {desc_limpa}", border="B")
        pdf.cell(50, 8, txt=f"R$ {item['valor']:.2f} ", border="B", align="R", ln=True)
        total_geral += item['valor']
        
    # Linha de Totalização
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(140, 10, txt=" TOTAL DO ORCAMENTO:", border="T", fill=True)
    pdf.cell(50, 10, txt=f"R$ {total_geral:.2f} ", border="T", fill=True, align="R", ln=True)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(85, 85, 85)
    pdf.cell(190, 5, txt="* Orcamento sujeito a alteracoes caso surjam novos defeitos ocultos constatados na desmontagem do cambio.", ln=True)
    pdf.cell(190, 5, txt="Validade deste orcamento: 10 dias.", ln=True)
    
    return bytes(pdf.output())

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
            defeito = st.text_area("Defeito Relatado / Sintomas", placeholder="Ex: Barulho na segunda...")
            
        if st.button("Gravar Entrada do Veículo", key="btn_cliente"):
            if nome_cliente == "" or veiculo == "":
                st.error("Por favor, preencha pelo menos o Nome do Cliente e o Veículo!")
            else:
                novo_cliente = {
                    "nome_cliente": nome_cliente, 
                    "veiculo": veiculo, 
                    "placa": placa, 
                    "telefone": telefone, 
                    "defeito": defeito, 
                    "status": "Aguardando Diagnóstico"
                }
                supabase.table("clientes").insert(novo_cliente).execute()
                st.success(f"Sucesso! Registro de '{nome_cliente}' gravado!")
                st.rerun()
                
    with aba_ver_clientes:
        st.subheader("📋 Veículos no Pátio")
        
        # Realiza a consulta de forma limpa ordenando por id
        resposta_clientes = supabase.table("clientes").select("*").order("id", desc=True).execute()
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
                                st.success("Status Evaluated!")
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
#                      MÓDULO: CRIAR ORÇAMENTO (FPDF)
# ==============================================================================
elif modulo == "📋 Criar Orçamento (PDF)":
    st.header("📋 Gerador de Orçamentos da Oficina")
    
    if 'pecas_orcamento' not in st.session_state:
        st.session_state.pecas_orcamento = []
        
    c1, c2 = st.columns(2)
    with c1:
        orc_cliente = st.text_input("Nome do Cliente:", placeholder="Ex: Roberto Almeida")
        orc_veiculo = st.text_input("Veículo ou Modelo do Câmbio:", placeholder="Ex: Amarok - Câmbio ZF8HP")
    with c2:
        orc_tel_input = st.text_input("Telefone do Cliente:", placeholder="Ex: 16988888888")
        orc_tel = formatar_telefone(orc_tel_input)
        
    st.markdown("---")
    st.subheader("🛠️ Adicionar Peças / Serviços")
    
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        peca_desc = st.text_input("Descrição da Peça ou Serviço:", placeholder="Ex: Jogo de Juntas", key="input_peca_desc")
    with col_p2:
        peca_val = st.number_input("Valor (R$):", min_value=0.0, value=0.0, step=10.0, key="input_peca_val")
        
    if st.button("➕ Adicionar Peça ao Orçamento"):
        if peca_desc == "":
            st.error("Digite a descrição da peça!")
        else:
            st.session_state.pecas_orcamento.append({"descricao": peca_desc, "valor": float(peca_val)})
            st.success(f"'{peca_desc}' adicionado!")
            st.rerun()
            
    if st.session_state.pecas_orcamento:
        st.markdown("### 📝 Itens incluídos:")
        df_temp = pd.DataFrame(st.session_state.pecas_orcamento)
        df_temp.index = df_temp.index + 1
        st.table(df_temp.style.format({"valor": "R$ {:.2f}"}))
        
        total_acumulado = sum(item['valor'] for item in st.session_state.pecas_orcamento)
        st.markdown(f"### **Total Atual: R$ {total_acumulado:.2f}**")
        
        c_acao1, c_acao2 = st.columns(2)
        with c_acao1:
            if orc_cliente == "" or orc_veiculo == "":
                st.warning("Preencha o nome do cliente e o veículo para liberar o PDF.")
            else:
                pdf_data = gerar_pdf_orcamento_fpdf(orc_cliente, orc_tel, orc_veiculo, st.session_state.pecas_orcamento)
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