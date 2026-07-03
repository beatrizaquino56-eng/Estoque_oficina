import streamlit as st
import pandas as pd
from supabase import create_client, Client
import re
from fpdf import FPDF
from validacoes import validar_placa, texto_valido, validar_valores

# ==========================================
# 🛠️ FUNÇÃO PARA FORMATAR TELEFONE
# ==========================================
def formatar_telefone(num):
    apenas_numeros = re.sub(r'\D', '', num)
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
    elif len(apenas_numeros) == 10:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    return num

# ==========================================
# 🛠️ FUNÇÃO PARA GERAR O PDF DO ORÇAMENTO
# ==========================================
def gerar_pdf_orcamento_fpdf(cliente, telefone, veiculo, itens):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "ORCAMENTO - OFICINA", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 8, f"Cliente: {cliente}", ln=True)
    pdf.cell(190, 8, f"Telefone: {telefone}", ln=True)
    pdf.cell(190, 8, f"Veiculo: {veiculo}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 8, "Descricao", border=1)
    pdf.cell(20, 8, "Qtd", border=1, align="C")
    pdf.cell(40, 8, "Val. Unit.", border=1, align="R")
    pdf.cell(40, 8, "Total", border=1, align="R")
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    total_geral = 0
    for item in itens:
        desc = item.get("descricao", "")
        qtd = item.get("quantidade", 1)
        val_uni = item.get("valor_unitario", item.get("valor", 0.0))
        val_tot = item.get("valor", 0.0)
        total_geral += val_tot
        
        pdf.cell(90, 8, desc, border=1)
        pdf.cell(20, 8, str(qtd), border=1, align="C")
        pdf.cell(40, 8, f"R$ {val_uni:.2f}", border=1, align="R")
        pdf.cell(40, 8, f"R$ {val_tot:.2f}", border=1, align="R")
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 8, "TOTAL GERAL: ", align="R")
    pdf.cell(40, 8, f"R$ {total_geral:.2f}", border=1, align="R")
    
    # === CORREÇÃO DO ERRO AQUI ===
    # Força o retorno a ser estritamente em 'bytes' para o Streamlit aceitar
    try:
        resultado = pdf.output()
    except Exception:
        resultado = pdf.output(dest='S')
        
    if isinstance(resultado, str):
        return resultado.encode('latin1')
    return bytes(resultado)

# 1. Conexão com o Banco de Dados
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)
# 2. Título da Página
st.title("📄 Geração de Orçamentos")

# =========================================================================
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