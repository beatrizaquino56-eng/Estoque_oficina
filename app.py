import streamlit as st
import pandas as pd
import re
import io
from supabase import create_client, Client
from fpdf import FPDF

# --- 1. CONFIGURAÇÃO DE CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://lgpcpnxhkogtvhjtfwya.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxncGNwbnhoa29ndHZoanRmd3lhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDA1NzAxNiwiZXhwIjoyMDk1NjMzMDE2fQ.84Otv9sBd7QDEfw8fPS15ybNK5_ps_ZGYR5PrBLKtKM"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Oficina Mecânica", layout="wide")
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

# Função para gerar o PDF do Orçamento corrigida com suporte a colunas de quantidade e valores
def gerar_pdf_orcamento_fpdf(cliente, telefone, veiculo, lista_pecas):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho da Empresa
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(140, 10, text="LAUD AUTOPEÇAS E MECÂNICA")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 10, text="ORÇAMENTO", new_x="LMARGIN", new_y="NEXT", align="R")
    
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(140, 5, text="Avenida Maria Antônia Camargo de Oliveira, 3053 - Vila Ferroviária")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 5, text=f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="R")
    
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(190, 5, text="Araraquara - SP | Fone: (16) 3336-8899", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Bloco de Informações do Cliente
    pdf.set_fill_color(250, 250, 250)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 36, 190, 24, "DF")
    
    cliente_limpo = cliente.encode('latin-1', 'ignore').decode('latin-1')
    veiculo_limpo = veiculo.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(190, 6, text=f" Cliente: {cliente_limpo}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 6, text=f" Telefone: {telefone}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 6, text=f" Veículo / Câmbio: {veiculo_limpo}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Tabela de Itens
    pdf.set_fill_color(34, 34, 34)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 8, text=" Descrição da Peça / Serviço", border=0, fill=True)
    pdf.cell(20, 8, text="Qtd", border=0, fill=True, align="C")
    pdf.cell(35, 8, text="Val. Unit (R$)", border=0, fill=True, align="R")
    pdf.cell(40, 8, text="Total (R$) ", border=0, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    
    total_geral = 0.0
    for item in lista_pecas:
        desc_limpa = item['descricao'].encode('latin-1', 'ignore').decode('latin-1')
        qtd = item.get("quantidade", 1)
        val_uni = item.get("valor_unitario", item['valor'])
        val_tot = item['valor']
        
        pdf.cell(95, 8, text=f" {desc_limpa}", border="B")
        pdf.cell(20, 8, text=f"{qtd}", border="B", align="C")
        pdf.cell(35, 8, text=f"R$ {val_uni:.2f}", border="B", align="R")
        pdf.cell(40, 8, text=f"R$ {val_tot:.2f} ", border="B", align="R", new_x="LMARGIN", new_y="NEXT")
        total_geral += val_tot
        
    # Linha de Totalização
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(150, 10, text=" TOTAL DO ORÇAMENTO:", border="T", fill=True)
    pdf.cell(40, 10, text=f"R$ {total_geral:.2f} ", border="T", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(85, 85, 85)
    pdf.cell(190, 5, text="* Orçamento sujeito a alterações caso surjam novos defeitos ocultos constatados na desmontagem do câmbio.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 5, text="Validade deste orçamento: 10 dias.", new_x="LMARGIN", new_y="NEXT")
    
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
            custo_previsto_reparo = st.number_input("Custo Previsto do Reparo (R$)", min_value=0.0, value=0.0, step=50.0)
            
        with col2:
            telefone_input = st.text_input("Número de Telefone (com DDD)", placeholder="Ex: 16999999999")
            telefone = formatar_telefone(telefone_input)
            
            # ALTERADO: Adicionado format="DD/MM/YYYY"
            data_chegada = st.date_input("Data de Entrada/Chegada", value=pd.Timestamp.now().date(), format="DD/MM/YYYY")
            
            # ALTERADO: Adicionado format="DD/MM/YYYY"
            data_prevista_entrega = st.date_input("Data Prevista para Entrega", value=pd.Timestamp.now().date(), format="DD/MM/YYYY")
            
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
                    "data_chegada": str(data_chegada),
                    "data_prevista_entrega": str(data_prevista_entrega),
                    "custo_previsto_reparo": float(custo_previsto_reparo),
                    "defeito": defeito, 
                    "status": "Aguardando Diagnóstico"
                }
                supabase.table("clientes").insert(novo_cliente).execute()
                st.success(f"Sucesso! Registro de '{nome_cliente}' gravado!")
                st.rerun()
                
    with aba_ver_clientes:
        st.subheader("📋 Veículos no Pátio")
        
        resposta_clientes = supabase.table("clientes").select("*").order("id", desc=True).execute()
        dados_clientes = pd.DataFrame(resposta_clientes.data)
        
        if not dados_clientes.empty:
            c_busca, c_filtro = st.columns([2, 1])
            with c_busca:
                busca_pacio = st.text_input("🔍 Buscar por Nome do Cliente ou Placa:", placeholder="Digite para filtrar...")
            with c_filtro:
                lista_status_opcoes = ["Todos", "Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"]
                filtro_status = st.selectbox("🚦 Filtrar por Status:", lista_status_opcoes)
            
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
                    
                    data_formatada = "Não informada"
                    if "data_chegada" in row and pd.notna(row['data_chegada']):
                        try:
                            data_formatada = pd.to_datetime(row['data_chegada']).strftime('%d/%m/%Y')
                        except:
                            data_formatada = str(row['data_chegada'])

                    data_prev_formatada = "Não informada"
                    if "data_prevista_entrega" in row and pd.notna(row['data_prevista_entrega']):
                        try:
                            data_prev_formatada = pd.to_datetime(row['data_prevista_entrega']).strftime('%d/%m/%Y')
                        except:
                            data_prev_formatada = str(row['data_prevista_entrega'])

                    custo_previsto = row.get('custo_previsto_reparo', 0.0)
                    if pd.isna(custo_previsto):
                        custo_previsto = 0.0

                    with st.expander(f"{cor_status} {row['veiculo']} — Placa: {row['placa']} ({row['nome_cliente']})", expanded=True):
                        st.markdown(f"**👤 Cliente:** {row['nome_cliente']} | **📞 Tel:** {row['telefone']}")
                        st.markdown(f"**📅 Chegada:** `{data_formatada}` | **📅 Prev. Entrega:** `{data_prev_formatada}` | **💰 Custo Previsto:** `R$ {custo_previsto:.2f}`")
                        st.markdown(f"**🛠️ Defeito Relatado:** {row['defeito']}")
                        st.markdown(f"**📌 Status Atual:** `{status_atual}`")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            status_fluxo = ["Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"]
                            try:
                                index_status_atual = status_fluxo.index(status_atual)
                            except ValueError:
                                index_status_atual = 0
                                
                            novo_status = st.selectbox("Alterar Status para:", status_fluxo, index=index_status_atual, key=f"status_{row['id']}")
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
                    novo_produto = {
                        "descricao": nome_produto, 
                        "codigo_original": codigo_original, 
                        "marca": marca, 
                        "quantidade": int(quantidade), 
                        "preco_custo": float(preco_custo),
                        "ncm": ncm,
                        "cest": cest,
                        "csosn": csosn,
                        "origem": origem,
                        "peso": float(peso)
                    }
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
                    st.success("Estoque Atualizado!")
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
    
    aba_criar, aba_historico = st.tabs(["📝 Criar Novo Orçamento", "📚 Histórico de Salvos"])
    
    if 'pecas_orcamento' not in st.session_state:
        st.session_state.pecas_orcamento = []
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = -1
        
    with aba_criar:
        c1, c2 = st.columns(2)
        with c1:
            orc_cliente = st.text_input("Nome do Cliente:", placeholder="Ex: Roberto Almeida")
            orc_veiculo = st.text_input("Veículo ou Modelo do Câmbio:", placeholder="Ex: Amarok - Câmbio ZF8HP")
        with c2:
            orc_tel_input = st.text_input("Telefone do Cliente:", placeholder="Ex: 16988888888")
            orc_tel = formatar_telefone(orc_tel_input)
            
        st.markdown("---")
        
        idx_editar = st.session_state.edit_index
        
        if idx_editar == -1:
            st.subheader("🛠️ Adicionar Peças / Serviços")
            col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
            with col_p1:
                peca_desc = st.text_input("Descrição da Peça ou Serviço:", placeholder="Ex: Jogo de Juntas", key="add_p_desc")
            with col_p2:
                peca_qtd = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="add_p_qtd")
            with col_p3:
                peca_val_unit = st.number_input("Valor Unitário (R$):", min_value=0.0, value=0.0, step=10.0, key="add_p_val")
                
            if st.button("➕ Adicionar Peça ao Orçamento"):
                if peca_desc == "":
                    st.error("Digite a descrição da peça!")
                else:
                    total_item = peca_qtd * peca_val_unit
                    st.session_state.pecas_orcamento.append({
                        "descricao": peca_desc,
                        "quantidade": int(peca_qtd),
                        "valor_unitario": float(peca_val_unit),
                        "valor": float(total_item)
                    })
                    st.success(f"'{peca_desc}' adicionado!")
                    st.rerun()
        else:
            st.subheader("✏️ Alterar Item Selecionado")
            item_atual = st.session_state.pecas_orcamento[idx_editar]
            col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
            with col_p1:
                peca_desc = st.text_input("Descrição da Peça ou Serviço:", value=item_atual.get("descricao", ""), key="edit_p_desc")
            with col_p2:
                peca_qtd = st.number_input("Quantidade:", min_value=1, value=int(item_atual.get("quantidade", 1)), step=1, key="edit_p_qtd")
            with col_p3:
                val_inicial_unit = item_atual.get("valor_unitario", item_atual.get("valor", 0.0))
                peca_val_unit = st.number_input("Valor Unitário (R$):", min_value=0.0, value=float(val_inicial_unit), step=10.0, key="edit_p_val")
            
            c_ed1, c_ed2 = st.columns(2)
            with c_ed1:
                if st.button("💾 Confirmar Alteração"):
                    if peca_desc == "":
                        st.error("A descrição não pode ser vazia!")
                    else:
                        st.session_state.pecas_orcamento[idx_editar] = {
                            "descricao": peca_desc,
                            "quantidade": int(peca_qtd),
                            "valor_unitario": float(peca_val_unit),
                            "valor": float(peca_qtd * peca_val_unit)
                        }
                        st.session_state.edit_index = -1
                        st.success("Item updated!")
                        st.rerun()
            with c_ed2:
                if st.button("❌ Cancelar Edição"):
                    st.session_state.edit_index = -1
                    st.rerun()
                    
        st.markdown("---")
        
        if st.session_state.pecas_orcamento:
            st.markdown("### 📝 Itens incluídos:")
            
            c_h1, c_h2, c_h3, c_h4, c_h5, c_h6 = st.columns([3, 1, 1, 1, 0.6, 0.6])
            c_h1.markdown("**Descrição**")
            c_h2.markdown("**Qtd**")
            c_h3.markdown("**Val. Unitário**")
            c_h4.markdown("**Total Item**")
            c_h5.markdown("**Editar**")
            c_h6.markdown("**Excluir**")
            st.markdown("<hr style='margin:0px 0px 10px 0px;'>", unsafe_allow_html=True)
            
            for index, item in enumerate(st.session_state.pecas_orcamento):
                c_i1, c_i2, c_i3, c_i4, c_i5, c_i6 = st.columns([3, 1, 1, 1, 0.6, 0.6])
                
                qtd = item.get("quantidade", 1)
                val_uni = item.get("valor_unitario", item["valor"])
                val_tot = item["valor"]
                
                c_i1.write(item["descricao"])
                c_i2.write(f"{qtd}")
                c_i3.write(f"R$ {val_uni:.2f}")
                c_i4.write(f"R$ {val_tot:.2f}")
                
                if c_i5.button("✏️", key=f"btn_edit_{index}"):
                    st.session_state.edit_index = index
                    st.rerun()
                
                if c_i6.button("❌", key=f"btn_del_{index}"):
                    if st.session_state.edit_index == index:
                        st.session_state.edit_index = -1
                    elif st.session_state.edit_index > index:
                        st.session_state.edit_index -= 1
                    st.session_state.pecas_orcamento.pop(index)
                    st.rerun()
            
            total_acumulado = sum(item['valor'] for item in st.session_state.pecas_orcamento)
            st.markdown(f"### **Total Atual: R$ {total_acumulado:.2f}**")
            
            c_acao1, c_acao2, c_acao3 = st.columns(3)
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
                if st.button("💾 Salvar no Sistema", key="btn_salvar_orcamento"):
                    if orc_cliente == "" or orc_veiculo == "":
                        st.error("Erro: Preencha o Nome do Cliente e o Veículo antes de salvar!")
                    else:
                        dados_salvar = {
                            "cliente": orc_cliente,
                            "veiculo": orc_veiculo,
                            "telefone": orc_tel,
                            "total": float(total_acumulado),
                            "itens": st.session_state.pecas_orcamento
                        }
                        supabase.table("orcamentos_salvos").insert(dados_salvar).execute()
                        st.success("✅ Orçamento salvo com sucesso no banco de dados!")
            with c_acao3:
                if st.button("🧹 Limpar Tudo / Novo Orçamento"):
                    st.session_state.pecas_orcamento = []
                    st.session_state.edit_index = -1
                    st.rerun()
                    
    with aba_historico:
        st.subheader("📚 Histórico de Orçamentos Salvos")
        
        resposta_orc = supabase.table("orcamentos_salvos").select("*").order("id", desc=True).execute()
        dados_orc = pd.DataFrame(resposta_orc.data)
        
        if not dados_orc.empty:
            busca_orc = st.text_input("🔍 Buscar orçamento salvo por nome de cliente:", placeholder="Digite para pesquisar...")
            if busca_orc:
                dados_orc = dados_orc[dados_orc['cliente'].str.contains(busca_orc, case=False, na=False)]
                
            st.markdown("---")
            for index, row in dados_orc.iterrows():
                with st.expander(f"📋 {row['cliente']} — {row['veiculo']} (Total: R$ {row['total']:.2f})"):
                    st.markdown(f"**📞 Telefone:** {row['telefone']}")
                    
                    df_itens_salvos = pd.DataFrame(row['itens'])
                    if "quantidade" not in df_itens_salvos.columns:
                        df_itens_salvos["quantidade"] = 1
                    if "valor_unitario" not in df_itens_salvos.columns:
                        df_itens_salvos["valor_unitario"] = df_itens_salvos["valor"]
                    
                    df_itens_salvos = df_itens_salvos[["descricao", "quantidade", "valor_unitario", "valor"]]
                    df_itens_salvos.columns = ["Descrição", "Qtd", "Val. Unitário", "Total Item"]
                    df_itens_salvos.index = df_itens_salvos.index + 1
                    st.table(df_itens_salvos.style.format({"Val. Unitário": "R$ {:.2f}", "Total Item": "R$ {:.2f}"}))
                    
                    col_dl, col_del = st.columns([1, 4])
                    with col_dl:
                        pdf_historico = gerar_pdf_orcamento_fpdf(row['cliente'], row['telefone'], row['veiculo'], row['itens'])
                        st.download_button(
                            label="📥 Baixar PDF",
                            data=pdf_historico,
                            file_name=f"Orcamento_{row['cliente'].replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_hist_{row['id']}"
                        )
                    with col_del:
                        if st.button("❌ Excluir do Histórico", key=f"del_hist_{row['id']}"):
                            supabase.table("orcamentos_salvos").delete().eq("id", row['id']).execute()
                            st.success("Orçamento removido do histórico!")
                            st.rerun()
        else:
            st.info("Nenhum orçamento foi salvo no sistema até o momento.")