import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 🔌 CONEXÃO CONFIGURADA EXATAMENTE COMO SEU BANCO
# ==========================================
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# ==========================================
# 📍 GERADOR DE OPÇÕES DE LOCALIZAÇÃO
# ==========================================
lista_prateleiras = [chr(i) for i in range(ord('A'), ord('T') + 1)]
lista_fileiras = list(range(1, 10))

# Inicialização do estado de edição inline
if 'id_editar_estoque' not in st.session_state:
    st.session_state.id_editar_estoque = -1

# Títulos da página
st.title("📦 Controle de Estoque")
st.header("📋 Gerenciamento de Peças e Componentes")

# Abas de navegação
aba_consulta, aba_cadastro = st.tabs(["🔍 Consultar e Gerenciar", "➕ Cadastrar Nova Peça"])

# ===================================================
# --- ABA 1: CONSULTAR E GERENCIAR ESTOQUE ---------
# ===================================================
with aba_consulta:
    st.subheader("🔎 Painel Geral do Estoque")
    
    # Filtros de busca rápidos na tela
    col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
    with col_b1:
        busca_nome = st.text_input("Buscar por descrição da peça:", placeholder="Ex: Filtro de Linha")
    with col_b2:
        filtro_prateleira = st.selectbox("Filtrar por Prateleira:", ["Todas"] + lista_prateleiras)
    with col_b3:
        filtro_fileira = st.selectbox("Filtrar por Fileira:", ["Todas"] + [str(f) for f in lista_fileiras])

    try:
        # Puxa os dados respeitando a coluna 'descricao' do seu banco
        resposta = supabase.table("estoque").select("*").order("descricao").execute()
        dados_estoque = resposta.data
        
        if dados_estoque:
            df = pd.DataFrame(dados_estoque)
            
            # Filtros aplicados em tempo de execução
            if busca_nome:
                df = df[df['descricao'].str.contains(busca_nome, case=False, na=False)]
            if filtro_prateleira != "Todas":
                df = df[df['Prateleira'] == filtro_prateleira]
            if filtro_fileira != "Todas":
                df = df[df['Fileira'] == int(filtro_fileira)]
                
            if not df.empty:
                st.markdown(f"**Peças encontradas:** {len(df)}")
                st.markdown("---")
                
                for index, item in df.iterrows():
                    item_id = item['id']
                    
                    # SE CLICOU EM EDITAR: Formulário de alteração baseado nas suas colunas reais
                    if st.session_state.id_editar_estoque == item_id:
                        st.markdown(f"#### 📝 Alterando Dados: {item['descricao']}")
                        with st.form(f"form_edicao_{item_id}"):
                            edit_desc = st.text_input("Descrição da Peça:", value=item.get('descricao', ''))
                            
                            c_ed1, c_ed2, c_ed3 = st.columns(3)
                            with c_ed1:
                                edit_cod = st.text_input("Código Original:", value=item.get('codigo_original', ''))
                            with c_ed2:
                                edit_marca = st.text_input("Marca:", value=item.get('marca', ''))
                            with c_ed3:
                                edit_ncm = st.text_input("NCM:", value=item.get('ncm', ''), max_chars=8)
                                
                            c_ed4, c_ed5 = st.columns(2)
                            with c_ed4:
                                edit_qtd = st.number_input("Quantidade:", min_value=0, value=int(item.get('quantidade', 0)))
                            with c_ed5:
                                idx_prat = lista_prateleiras.index(item['Prateleira']) if item.get('Prateleira') in lista_prateleiras else 0
                                idx_fil = lista_fileiras.index(int(item['Fileira'])) if item.get('Fileira') in lista_fileiras else 0
                                col_p, col_f = st.columns(2)
                                edit_prat = col_p.selectbox("Prat.:", lista_prateleiras, index=idx_prat, key=f"p_{item_id}")
                                edit_fil = col_f.selectbox("Fil.:", lista_fileiras, index=idx_fil, key=f"f_{item_id}")
                                
                            c_b_ed1, c_b_ed2 = st.columns(2)
                            with c_b_ed1:
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    if edit_desc.strip() == "":
                                        st.error("A descrição não pode ser vazia.")
                                    else:
                                        supabase.table("estoque").update({
                                            "descricao": edit_desc.strip(),
                                            "codigo_original": edit_cod.strip(),
                                            "marca": edit_marca.strip(),
                                            "ncm": edit_ncm.strip(),
                                            "quantidade": int(edit_qtd),
                                            "Prateleira": edit_prat,
                                            "Fileira": int(edit_fil)
                                        }).eq("id", item_id).execute()
                                        st.session_state.id_editar_estoque = -1
                                        st.success("Item atualizado com sucesso!")
                                        st.rerun()
                            with c_b_ed2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state.id_editar_estoque = -1
                                    st.rerun()
                        st.markdown("---")
                    
                    # MODO DE EXIBIÇÃO NORMAL (Em formato compactado expansível)
                    else:
                        with st.expander(f"📦 {item['descricao']} — Qtd: {item.get('quantidade', 0)} un"):
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.markdown(f"**🔢 Código Original:** {item.get('codigo_original', 'Não Informado')}")
                                st.markdown(f"**🏷️ Marca:** {item.get('marca', 'Não Informada')}")
                            with col_info2:
                                st.markdown(f"**📑 NCM:** {item.get('ncm', 'Não Cadastrado')}")
                                st.markdown(f"**📍 Localização:** Prateleira {item.get('Prateleira','-')}, Fila {item.get('Fileira','-')}")
                            
                            c_btn1, c_btn2 = st.columns([1, 7])
                            with c_btn1:
                                if st.button("📝 Editar", key=f"btn_ed_{item_id}"):
                                    st.session_state.id_editar_estoque = item_id
                                    st.rerun()
                            with c_btn2:
                                if st.button("❌ Excluir Peça", key=f"btn_del_{item_id}"):
                                    supabase.table("estoque").delete().eq("id", item_id).execute()
                                    st.success("Peça removida com sucesso!")
                                    st.rerun()
            else:
                st.info("Nenhuma peça corresponde aos filtros aplicados.")
        else:
            st.info("Nenhuma peça cadastrada no estoque até o momento.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")

# ===================================================
# --- ABA 2: CADASTRO DE NOVAS PEÇAS ---------------
# ===================================================
with aba_cadastro:
    st.subheader("🚀 Inserir Novo Item no Estoque")
    
    with st.form("form_cadastro_estoque", clear_on_submit=True):
        descricao = st.text_input("Descrição / Nome da Peça:", placeholder="Ex: Filtro do Câmbio Automático ZF 8HP")
        
        col_cad1, col_cad2, col_cad3 = st.columns(3)
        with col_cad1:
            codigo_original = st.text_input("Código Original:", placeholder="Ex: 0501218105")
        with col_cad2:
            marca = st.text_input("Marca da Peça:", placeholder="Ex: ZF / Fram")
        with col_cad3:
            ncm_peca = st.text_input("NCM (8 dígitos):", placeholder="Ex: 87082999", max_chars=8)
            
        col_cad4, col_cad5 = st.columns(2)
        with col_cad4:
            quantidade = st.number_input("Quantidade Inicial:", min_value=0, value=1, step=1)
        with col_cad5:
            st.markdown("##### 📍 Localização Física no Pátio")
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                prateleira_selecionada = st.selectbox("Prateleira:", lista_prateleiras, key="cad_prat")
            with col_loc2:
                fileira_selecionada = st.selectbox("Fileira:", lista_fileiras, key="cad_fil")
            
        botao_salvar = st.form_submit_button("💾 Salvar no Sistema")
        
        if botao_salvar:
            if descricao.strip() == "":
                st.error("❌ Erro: Por favor, informe a descrição da peça antes de salvar!")
            else:
                # Dicionário mapeado perfeitamente com as colunas reais do seu Supabase
                dados_peca = {
                    "descricao": descricao.strip(),
                    "codigo_original": codigo_original.strip(),
                    "marca": marca.strip(),
                    "ncm": ncm_peca.strip(),
                    "quantidade": int(quantidade),
                    "Prateleira": prateleira_selecionada,
                    "Fileira": int(fileira_selecionada)
                }
                
                try:
                    supabase.table("estoque").insert(dados_peca).execute()
                    st.success(f"✔️ '{descricao}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")