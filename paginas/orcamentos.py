import streamlit as st
from supabase import create_client, Client
from fpdf import FPDF
import datetime
import re
import io

# ===================================================
# 🔌 CONEXÃO COM O BANCO DE DADOS SUPABASE
# ===================================================
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# ===================================================
# 📞 FUNÇÃO AUXILIAR: FORMATAR TELEFONE
# ===================================================
def formatar_telefone(num):
    if not num:
        return ""
    penas_numeros = re.sub(r'\D', '', str(num))
    if len(penas_numeros) == 11:
        return f"({penas_numeros[:2]}) {penas_numeros[2:7]}-{penas_numeros[7:]}"
    elif len(penas_numeros) == 10:
        return f"({penas_numeros[:2]}) {penas_numeros[2:6]}-{penas_numeros[6:]}"
    return num

# ===================================================
# 🎨 CLASSE PERSONALIZADA PARA O LAYOUT DO PDF
# ===================================================
class PDF_Oficina(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 8, 'LAUD OFICINA MECANICA', ln=True, align='C')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Avenida Maria Antonia Camargo De Oliveira, n 3053 - Vila Ferroviaria', ln=True, align='C')
        self.cell(0, 5, 'Telefone: (16) 98811-2234 | Email: contato@laud.com.br', ln=True, align='C')
        
        self.ln(4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

# ===================================================
# ⚙️ FUNÇÃO PRINCIPAL: GERADOR DO PDF (CORRIGIDA)
# ===================================================
def gerar_pdf_orcamento_fpdf(nome, telefone, cpf, veiculo, lista_itens, total_geral):
    pdf = PDF_Oficina(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    data_atual = datetime.date.today().strftime('%d/%m/%Y')
    pdf.cell(0, 10, f'ORDEM DE SERVICO / ORCAMENTO - DATA: {data_atual}', ln=True, align='L')
    pdf.ln(2)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, ' DADOS DO CLIENTE E DO VEICULO', ln=True, fill=True)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Cliente: {nome}", ln=True)
    pdf.cell(0, 6, f"CPF: {cpf if cpf else 'Nao informado'}", ln=True)
    pdf.cell(0, 6, f"Telefone: {formatar_telefone(telefone)}", ln=True)
    pdf.cell(0, 6, f"Veiculo: {veiculo}", ln=True)
    pdf.ln(6)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Descricao", 1)
    pdf.cell(25, 10, "Qtd", 1, align="C")
    pdf.cell(40, 10, "Val. Unitario", 1, align="C")
    pdf.cell(45, 10, "Total", 1, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    for item in lista_itens:
        desc = item.get('descricao', '')[:38]
        qtd = item.get('quantidade', 1)
        val_unit = item.get('valor_unitario', 0.0)
        subtotal = item.get('total', float(qtd) * float(val_unit))
        
        pdf.cell(80, 10, f" {desc}", 1)
        pdf.cell(25, 10, str(qtd), 1, align="C")
        pdf.cell(40, 10, f"R$ {val_unit:.2f}", 1, align="C")
        pdf.cell(45, 10, f"R$ {subtotal:.2f}", 1, align="C")
        pdf.ln(10)
        
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(145, 10, "TOTAL GERAL: ", align="R")
    pdf.cell(45, 10, f"R$ {total_geral:.2f}", 1, align="C", fill=True)
    pdf.ln(15)
    
    if pdf.get_y() > 230:
        pdf.add_page()
        
    pdf.set_font('Arial', '', 9)
    termo = "Autorizo a realizacao dos servicos descritos acima e a aplicacao das pecas listadas."
    pdf.cell(0, 5, termo, ln=True, align='C')
    pdf.ln(12)
    
    pdf.line(45, pdf.get_y(), 165, pdf.get_y())
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, 'Assinatura do Cliente / Responsavel', ln=True, align='C')
    
    # 🌟 SOLUÇÃO DO ERRO AQUI:
    # Captura o retorno do PDF de forma segura para evitar o erro de 'bytearray'
    resultado_pdf = pdf.output(dest='S')
    if isinstance(resultado_pdf, str):
        return resultado_pdf.encode('latin1', errors='ignore')
    return bytes(resultado_pdf)

# ===================================================
# 🖥️ INTERFACE DO USUÁRIO (STREAMLIT) - ABAS CRUD
# ===================================================
st.title("📋 Gerenciador de Orçamentos")

aba_novo, aba_gerenciar = st.tabs(["🆕 Novo Orçamento", "🗂️ Gerenciar Orçamentos Salvos"])

# --- ABA 1: NOVO ORÇAMENTO (CRIAR / SALVAR) ---
with aba_novo:
    if "itens_orcamento" not in st.session_state:
        st.session_state.itens_orcamento = []

    st.subheader("👤 Informações do Cliente e Veículo")

    nome_padrao = ""
    cpf_padrao = ""
    telefone_padrao = ""
    veiculo_padrao = ""

    vincular_cliente = st.checkbox("🔗 Vincular a um cliente já cadastrado na Oficina", key="vinculo_novo")

    if vincular_cliente:
        try:
            response = supabase.table("clientes").select("*").execute()
            clientes_db = response.data
            
            if clientes_db:
                def formatar_opcao(c):
                    nome = c.get("nome_cliente") or c.get("nome") or c.get("nome_completo") or c.get("cliente") or "Sem nome"
                    veiculo = c.get("veiculo") or c.get("modelo") or c.get("carro") or c.get("veiculo_cliente") or "Sem veiculo"
                    placa = c.get("placa") or c.get("placa_veiculo") or ""
                    return f"{nome} | {veiculo} ({placa})" if placa else f"{nome} | {veiculo}"
                
                cliente_selecionado = st.selectbox(
                    "Selecione o cliente desejado:",
                    options=clientes_db,
                    format_func=formatar_opcao,
                    key="select_cliente_novo"
                )
                
                if cliente_selecionado:
                    nome_padrao = cliente_selecionado.get("nome_cliente") or cliente_selecionado.get("nome") or cliente_selecionado.get("nome_completo") or cliente_selecionado.get("cliente") or ""
                    cpf_padrao = cliente_selecionado.get("cpf") or cliente_selecionado.get("cpf_cliente") or ""
                    telefone_padrao = cliente_selecionado.get("telefone") or cliente_selecionado.get("whatsapp") or cliente_selecionado.get("celular") or ""
                    
                    v_mod = cliente_selecionado.get("veiculo") or cliente_selecionado.get("modelo") or cliente_selecionado.get("carro") or ""
                    v_placa = cliente_selecionado.get("placa") or cliente_selecionado.get("placa_veiculo") or ""
                    if v_mod and v_placa:
                        veiculo_padrao = f"{v_mod} - Placa: {v_placa}"
                    else:
                        veiculo_padrao = v_mod if v_mod else v_placa
        except Exception as e:
            st.error(f"Erro ao carregar os clientes do Supabase: {e}")

    col1, col2 = st.columns(2)
    with col1:
        nome_cliente = st.text_input("Nome do Cliente", value=nome_padrao, placeholder="Ex: João da Silva", key="nome_n")
        cpf_cliente = st.text_input("CPF do Cliente", value=cpf_padrao, placeholder="000.000.000-00", key="cpf_n")
    with col2:
        telefone_cliente = st.text_input("Telefone", value=telefone_padrao, placeholder="(16) 99721-0572", key="tel_n")
        veiculo_cliente = st.text_input("Veículo / Modelo", value=veiculo_padrao, placeholder="Ex: Câmbio Crossfox", key="vei_n")

    st.divider()

    st.subheader("🛠️ Adicionar Itens ao Orçamento")
    col_desc, col_qtd, col_val = st.columns([3, 1, 1])

    with col_desc:
        nova_descricao = st.text_input("Descrição da Peça ou Serviço", key="desc_n")
    with col_qtd:
        nova_qtd = st.number_input("Quantidade", min_value=1, value=1, step=1, key="qtd_n")
    with col_val:
        novo_valor = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0, step=5.0, key="val_n")

    if st.button("➕ Incluir Item na Lista", key="btn_add_n"):
        if nova_descricao:
            st.session_state.itens_orcamento.append({
                "descricao": nova_descricao,
                "quantidade": nova_qtd,
                "valor_unitario": novo_valor,
                "total": nova_qtd * novo_valor
            })
            st.success(f"'{nova_descricao}' adicionado com sucesso!")
            st.rerun()
        else:
            st.warning("Por favor, digite uma descrição válida antes de adicionar.")

    if st.session_state.itens_orcamento:
        st.subheader("🛒 Itens Selecionados")
        total_geral_calculado = 0.0
        for idx, item in enumerate(st.session_state.itens_orcamento):
            total_geral_calculado += item["total"]
            st.text(f"{item['quantidade']}x  -  {item['descricao']}  -  R$ {item['valor_unitario']:.2f} (Total: R$ {item['total']:.2f})")
            
        st.markdown(f"### **Valor Total Acumulado: R$ {total_geral_calculado:.2f}**")
        
        if st.button("🗑️ Limpar Lista de Itens", key="btn_limpar_n"):
            st.session_state.itens_orcamento = []
            st.rerun()

        st.divider()

        st.subheader("💾 Ações do Orçamento")
        c_salvar, c_pdf = st.columns(2)
        
        with c_salvar:
            if st.button("💾 Gravar Orçamento no Banco de Dados", key="btn_salvar_db"):
                if not nome_cliente:
                    st.error("Preencha o nome do cliente antes de gravar.")
                else:
                    try:
                        dados_orcamento = {
                            "nome_cliente": nome_cliente,
                            "cpf_cliente": cpf_cliente if cpf_cliente else None,
                            "telefone_cliente": telefone_cliente if telefone_cliente else None,
                            "veiculo_cliente": veiculo_cliente if veiculo_cliente else None,
                            "itens": st.session_state.itens_orcamento,
                            "total_geral": total_geral_calculado
                        }
                        supabase.table("orcamentos_salvos").insert(dados_orcamento).execute()
                        st.success("✔️ Orçamento gravado com sucesso no banco de dados!")
                        st.session_state.itens_orcamento = []
                        st.rerun()
                    except Exception as error:
                        st.error(f"Erro ao salvar orçamento: {error}")
                        
        with c_pdf:
            pdf_bytes = gerar_pdf_orcamento_fpdf(
                nome=nome_cliente, telefone=telefone_cliente, cpf=cpf_cliente,
                veiculo=veiculo_cliente, lista_itens=st.session_state.itens_orcamento,
                total_geral=total_geral_calculado
            )
            st.download_button(
                label="📥 Baixar Ordem de Serviço (PDF)",
                data=pdf_bytes,
                file_name=f"OS_{nome_cliente.replace(' ', '_')}_{datetime.date.today()}.pdf",
                mime="application/pdf",
                key="btn_pdf_n"
            )
    else:
        st.info("Adicione pelo menos um item acima para habilitar as ações de salvar ou baixar PDF.")


# --- ABA 2: GERENCIAR ORÇAMENTOS (VISUALIZAR, MODIFICAR, EXCLUIR) ---
with aba_gerenciar:
    st.subheader("🗂️ Modificar ou Excluir Orçamentos Gravados")
    
    try:
        res_orcamentos = supabase.table("orcamentos_salvos").select("*").order("id", desc=True).execute()
        orcamentos_db = res_orcamentos.data
        
        if orcamentos_db:
            def formatar_orcamento_opcao(o):
                id_o = o.get("id")
                nome = o.get("nome_cliente") or "Sem Nome"
                veiculo = o.get("veiculo_cliente") or "Sem Veículo"
                total = o.get("total_geral", 0.0)
                return f"OS #{id_o} - {nome} | {veiculo} (R$ {total:.2f})"
                
            orcamento_selecionado = st.selectbox(
                "Selecione o Orçamento para Modificar ou Excluir:",
                options=orcamentos_db,
                format_func=formatar_orcamento_opcao,
                key="select_orc_gerenciar"
            )
            
            if orcamento_selecionado:
                id_orcamento = orcamento_selecionado.get("id")
                
                if "edit_id" not in st.session_state or st.session_state.edit_id != id_orcamento:
                    st.session_state.edit_id = id_orcamento
                    st.session_state.itens_edicao = orcamento_selecionado.get("itens", [])
                
                st.markdown(f"### ⚙️ Editando Cadastro da OS #{id_orcamento}")
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_nome = st.text_input("Nome do Cliente", value=orcamento_selecionado.get("nome_cliente", ""), key="edit_nome_f")
                    edit_cpf = st.text_input("CPF do Cliente", value=orcamento_selecionado.get("cpf_cliente", ""), key="edit_cpf_f")
                with col_e2:
                    edit_telefone = st.text_input("Telefone", value=orcamento_selecionado.get("telefone_cliente", ""), key="edit_tel_f")
                    edit_veiculo = st.text_input("Veículo / Modelo", value=orcamento_selecionado.get("veiculo_cliente", ""), key="edit_vei_f")
                
                st.write("#### 🛠️ Itens do Orçamento")
                
                col_col_d, col_col_q, col_col_v = st.columns([3, 1, 1])
                with col_col_d:
                    add_edit_desc = st.text_input("Adicionar nova peça/serviço:", key="add_edit_desc_f")
                with col_col_q:
                    add_edit_qtd = st.number_input("Qtd:", min_value=1, value=1, step=1, key="add_edit_qtd_f")
                with col_col_v:
                    add_edit_val = st.number_input("Valor Unitário:", min_value=0.0, value=0.0, step=5.0, key="add_edit_val_f")
                    
                if st.button("➕ Adicionar Item à Edição", key="btn_add_edit"):
                    if add_edit_desc:
                        st.session_state.itens_edicao.append({
                            "descricao": add_edit_desc,
                            "quantidade": add_edit_qtd,
                            "valor_unitario": add_edit_val,
                            "total": add_edit_qtd * add_edit_val
                        })
                        st.success("Item adicionado à lista de alteração!")
                        st.rerun()
                
                total_edicao_calculado = 0.0
                st.write("**Lista Atual de Itens:**")
                
                for idx, item in enumerate(st.session_state.itens_edicao):
                    sub_total = item.get("quantidade", 1) * item.get("valor_unitario", 0.0)
                    total_edicao_calculado += sub_total
                    
                    c_text, c_btn = st.columns([4, 1])
                    c_text.text(f"- {item.get('quantidade')}x {item.get('descricao')} | R$ {item.get('valor_unitario'):.2f} (Total: R$ {sub_total:.2f})")
                    if c_btn.button("❌ Remover", key=f"del_item_edit_{idx}"):
                        st.session_state.itens_edicao.pop(idx)
                        st.rerun()
                
                st.markdown(f"#### **Novo Total Evaluado: R$ {total_edicao_calculado:.2f}**")
                st.divider()
                
                c_atualizar, c_excluir, c_pdf_e = st.columns(3)
                
                with c_atualizar:
                    if st.button("🔄 Gravar Alterações (Modificar)", key="btn_update_db"):
                        try:
                            dados_atualizados = {
                                "nome_cliente": edit_nome,
                                "cpf_cliente": edit_cpf if edit_cpf else None,
                                "telefone_cliente": edit_telefone if edit_telefone else None,
                                "veiculo_cliente": edit_veiculo if edit_veiculo else None,
                                "itens": st.session_state.itens_edicao,
                                "total_geral": total_edicao_calculado
                            }
                            supabase.table("orcamentos_salvos").update(dados_atualizados).eq("id", id_orcamento).execute()
                            st.success(f"✔️ Orçamento da OS #{id_orcamento} foi ATUALIZADO com sucesso!")
                            st.rerun()
                        except Exception as error:
                            st.error(f"Erro ao modificar orçamento: {error}")
                            
                with c_excluir:
                    if st.button("🗑️ Excluir Orçamento Definitivamente", key="btn_delete_db"):
                        try:
                            supabase.table("orcamentos_salvos").delete().eq("id", id_orcamento).execute()
                            st.warning(f"🗑️ Orçamento da OS #{id_orcamento} foi EXCLUÍDO permanentemente!")
                            if "itens_edicao" in st.session_state: del st.session_state.itens_edicao
                            if "edit_id" in st.session_state: del st.session_state.edit_id
                            st.rerun()
                        except Exception as error:
                            st.error(f"Erro ao excluir orçamento: {error}")
                            
                with c_pdf_e:
                    pdf_bytes_e = gerar_pdf_orcamento_fpdf(
                        nome=edit_nome, telefone=edit_telefone, cpf=edit_cpf,
                        veiculo=edit_veiculo, lista_itens=st.session_state.itens_edicao,
                        total_geral=total_edicao_calculado
                    )
                    st.download_button(
                        label="📥 Baixar PDF Atualizado",
                        data=pdf_bytes_e,
                        file_name=f"OS_Atualizada_{id_orcamento}.pdf",
                        mime="application/pdf",
                        key="btn_pdf_e_download"
                    )
        else:
            st.info("Nenhum orçamento salvo foi encontrado no banco de dados.")
    except Exception as e:
        st.error(f"Erro ao conectar com a tabela 'orcamentos_salvos': {e}")