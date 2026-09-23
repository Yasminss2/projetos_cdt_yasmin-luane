import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk,  ImageDraw, ImageFont

# ============================================================
# INTEGRÇÃO COM BANCO DE DADOS (FALLBACK DE SEGURANÇA)
# ============================================================
try:
    from database.db import cadastrar_cliente, buscar_cliente_por_id, buscar_ultimo_pedido, salvar_pedido
except ImportError:
    def cadastrar_cliente(nome, apelido, email, telefone, endereco, idade, cpf, face_encoding=None):
        return True, 1
    def buscar_cliente_por_id(cliente_id):
        return (1, "Cliente Exemplo", "Exemplo", "cliente@email.com", "11999999999", "Rua Açaí, 123", 20, "123.456.789-00", 120)
    def buscar_ultimo_pedido(cliente_id):
        return ("Açaí Tradicional 500ml", "Granola, Leite em Pó", "Pix", "Entrega")
    def salvar_pedido(cliente_id, tamanho, toppings, forma_pagamento, opcao_entrega, subtotal, taxa_entrega, total):
        return True

# ============================================================
# CONFIGURAÇÕES E CORES (PADRÃO YAS + SISTEMA)
# ============================================================
LARGURA = 1200
ALTURA = 700

ROXO_ESCURO = "#17062F"
ROXO = "#3A126B"
ROXO_MEDIO = "#5A1B91"
ROSA = "#E91E83"
ROSA_CLARO = "#F52B91"
AMARELO = "#FFD21C"
BRANCO = "#FFFFFF"
CINZA = "#B9AFC8"
VERDE = "#42A62A"

# Estado Global do Sistema
cliente_logado = None  # Dicionário com informações do cliente
carrinho = []          # Lista de itens do pedido atual
logo_cardapio = None   # Manter referência da imagem na memória

# ============================================================
# JANELA PRINCIPAL
# ============================================================
janela = tk.Tk()
janela.title("Açaízon - Sistema PDV")
janela.geometry(f"{LARGURA}x{ALTURA}")
janela.minsize(1000, 600)
janela.configure(bg=ROXO_ESCURO)

# ============================================================
# FUNÇÕES DE SUPORTE E SEGURANÇA
# ============================================================
def limpar_conteudo():
    """Remove os widgets da área central."""
    for widget in area_conteudo.winfo_children():
        widget.destroy()

def mascarar_dado(texto, visiveis=3):
    """Mascara dados sensíveis (CPF e Telefone)."""
    if not texto or texto == "-":
        return "-"
    if len(texto) <= visiveis:
        return "*" * len(texto)
    return "*" * (len(texto) - visiveis) + texto[-visiveis:]

def atualizar_painel_direito():
    """Painel Direito Unificado: Login + Dados Mascarados + Carrinho em Tempo Real."""
    for widget in painel_direito.winfo_children():
        widget.destroy()

    titulo = tk.Label(painel_direito, text="👤 Painel do Cliente", font=("Arial", 11, "bold"), fg=BRANCO, bg="#21103D")
    titulo.pack(pady=(15, 10))

    if cliente_logado:
        info_frame = tk.Frame(painel_direito, bg="#261044", highlightbackground=ROXO_MEDIO, highlightthickness=1)
        info_frame.pack(fill="x", padx=15, pady=5)

        nome = cliente_logado.get("nome", "Cliente")
        cpf_m = mascarar_dado(cliente_logado.get("cpf", ""), visiveis=3)
        tel_m = mascarar_dado(cliente_logado.get("telefone", ""), visiveis=4)
        pontos = cliente_logado.get("pontos", 120)

        tk.Label(info_frame, text=f"Olá, {nome}!", font=("Arial", 10, "bold"), fg=AMARELO, bg="#261044").pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(info_frame, text=f"CPF: ***.***.{cpf_m}", font=("Arial", 8), fg=BRANCO, bg="#261044").pack(anchor="w", padx=10)
        tk.Label(info_frame, text=f"Tel: (**) *****-{tel_m}", font=("Arial", 8), fg=BRANCO, bg="#261044").pack(anchor="w", padx=10)
        tk.Label(info_frame, text=f"Pontos: {pontos} pts 💜", font=("Arial", 9, "bold"), fg=ROSA_CLARO, bg="#261044").pack(anchor="w", padx=10, pady=(2, 8))

        btn_sair = tk.Button(
            painel_direito, text="Sair da Conta", font=("Arial", 9, "bold"), bg=ROSA, fg=BRANCO,
            relief="flat", cursor="hand2", command=deslogar_cliente
        )
        btn_sair.pack(fill="x", padx=15, pady=5)
    else:
        lbl_msg = tk.Label(painel_direito, text="Olá!\nFaça seu cadastro para\nter uma experiência ainda\nmais ESPECIAL!🎁", font=("Arial", 9), fg=CINZA, bg="#21103D", justify="center")
        lbl_msg.pack(pady=5)

        btn_login = tk.Button(
            painel_direito, text="🔑 Entrar na Conta", font=("Arial", 9, "bold"), bg=ROXO_MEDIO, fg=BRANCO,
            relief="flat", cursor="hand2", command=abrir_modal_login
        )
        btn_login.pack(fill="x", padx=15, pady=3)

        btn_cad = tk.Button(
            painel_direito, text="👤 Cadastrar Cliente", font=("Arial", 10, "bold"), bg=AMARELO, fg="#3B2600",
            activebackground="#FFE45C", relief="flat", cursor="hand2", command=abrir_modal_cadastro
        )
        btn_cad.pack(fill="x", padx=15, pady=3)

    # CARRINHO / ÚLTIMOS PEDIDOS
    tk.Label(painel_direito, text="♻ Últimos Pedidos / Carrinho", font=("Arial", 10, "bold"), fg=VERDE, bg="#21103D").pack(anchor="w", padx=15, pady=(15, 5))

    frame_pedidos = tk.Frame(painel_direito, bg="#261044", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    frame_pedidos.pack(fill="x", padx=15)

    if carrinho:
        total_carrinho = sum(item['preco'] for item in carrinho)
        for item in carrinho[-3:]:
            tk.Label(frame_pedidos, text=f"• {item['nome']} (R$ {item['preco']:.2f})", font=("Arial", 8), fg=BRANCO, bg="#261044", anchor="w").pack(fill="x", padx=8, pady=2)
        
        tk.Label(frame_pedidos, text=f"Subtotal: R$ {total_carrinho:.2f}", font=("Arial", 9, "bold"), fg=AMARELO, bg="#261044").pack(pady=5)
        
        btn_checkout = tk.Button(
            frame_pedidos, text="🛒 Finalizar Pedido", font=("Arial", 9, "bold"), bg=VERDE, fg=BRANCO,
            relief="flat", cursor="hand2", command=mostrar_checkout
        )
        btn_checkout.pack(fill="x", padx=10, pady=5)
    else:
        tk.Label(frame_pedidos, text="🥣", font=("Arial", 25), fg=BRANCO, bg="#261044").pack(pady=(12, 3))
        tk.Label(frame_pedidos, text="Nenhum pedido encontrado", font=("Arial", 9, "bold"), fg=BRANCO, bg="#261044").pack()
        tk.Label(frame_pedidos, text="Ainda não há pedidos registrados.", font=("Arial", 8), fg=CINZA, bg="#261044").pack(pady=(3, 12))

def deslogar_cliente():
    global cliente_logado
    cliente_logado = None
    atualizar_painel_direito()
    messagebox.showinfo("Açaízon🍇", "Você saiu da sua conta.")

# ============================================================
# MODAIS DE AUTENTICAÇÃO E CADASTRO
# ============================================================
def abrir_modal_login():
    win = tk.Toplevel(janela)
    win.title("Entrar na Conta")
    win.geometry("350x250")
    win.configure(bg=ROXO_ESCURO)

    tk.Label(win, text="Login Delírio Roxo", font=("Arial", 14, "bold"), fg=BRANCO, bg=ROXO_ESCURO).pack(pady=15)
    tk.Label(win, text="Digite seu CPF ou Telefone:", font=("Arial", 10), fg=CINZA, bg=ROXO_ESCURO).pack(anchor="w", padx=25)
    ent_dado = tk.Entry(win, font=("Arial", 11))
    ent_dado.pack(fill="x", padx=25, pady=5)

    def efetuar_login():
        global cliente_logado
        dado = ent_dado.get().strip()
        if not dado:
            messagebox.showwarning("Atenção", "Preencha o campo de login.")
            return
        cliente_logado = {"id": 1, "nome": "Cliente Açaízon", "cpf": dado, "telefone": dado, "pontos": 150}
        atualizar_painel_direito()
        win.destroy()
        messagebox.showinfo("Sucesso", "Login efetuado com sucesso!")

    tk.Button(win, text="Entrar", font=("Arial", 10, "bold"), bg=ROSA, fg=BRANCO, command=efetuar_login).pack(pady=15, ipadx=10)

def abrir_modal_cadastro():
    win = tk.Toplevel(janela)
    win.title("Cadastro de Cliente")
    win.geometry("350x320")
    win.configure(bg=ROXO_ESCURO)

    tk.Label(win, text="Novo Cadastro", font=("Arial", 14, "bold"), fg=BRANCO, bg=ROXO_ESCURO).pack(pady=10)
    tk.Label(win, text="Nome Completo:", font=("Arial", 9), fg=CINZA, bg=ROXO_ESCURO).pack(anchor="w", padx=25)
    ent_nome = tk.Entry(win)
    ent_nome.pack(fill="x", padx=25, pady=2)

    tk.Label(win, text="CPF:", font=("Arial", 9), fg=CINZA, bg=ROXO_ESCURO).pack(anchor="w", padx=25)
    ent_cpf = tk.Entry(win)
    ent_cpf.pack(fill="x", padx=25, pady=2)

    tk.Label(win, text="Telefone:", font=("Arial", 9), fg=CINZA, bg=ROXO_ESCURO).pack(anchor="w", padx=25)
    ent_tel = tk.Entry(win)
    ent_tel.pack(fill="x", padx=25, pady=2)

    def salvar():
        global cliente_logado
        if not ent_nome.get() or not ent_cpf.get():
            messagebox.showwarning("Atenção", "Preencha os campos obrigatórios.")
            return
        cadastrar_cliente(ent_nome.get(), "", "", ent_tel.get(), "", 0, ent_cpf.get())
        cliente_logado = {"id": 1, "nome": ent_nome.get(), "cpf": ent_cpf.get(), "telefone": ent_tel.get(), "pontos": 50}
        atualizar_painel_direito()
        win.destroy()
        messagebox.showinfo("Sucesso", "Cadastro realizado! Ganhou 50 pontos no Clube Delírio Roxo!")

    tk.Button(win, text="Cadastrar Cliente", font=("Arial", 10, "bold"), bg=AMARELO, fg="#3B2600", command=salvar).pack(pady=15)

# ============================================================
# TELAS DA APLICAÇÃO (MENU LATERAL)
# ============================================================
def mostrar_inicio():
    limpar_conteudo()

    titulo = tk.Label(area_conteudo, text="Bem-vindo ao Açaízon!", font=("Arial", 16, "bold"), fg=BRANCO, bg=ROXO_ESCURO)
    titulo.pack(pady=(35, 10))

    subtitulo = tk.Label(area_conteudo, text="Sabor que combina com Você!", font=("Arial", 25), fg=AMARELO, bg=ROXO_ESCURO)
    subtitulo.pack()

    caixa = tk.Frame(area_conteudo, bg="#21103D", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    caixa.pack(fill="both", expand=True, padx=35, pady=30)

    icone = tk.Label(caixa, text="◉", font=("Arial", 70), fg="#BBA8CC", bg="#21103D")
    icone.pack(pady=(70, 15))

    texto = tk.Label(caixa, text="Posicione seu rosto\nna câmera para continuar", font=("Arial", 14, "bold"), fg=BRANCO, bg="#21103D", justify="center")
    texto.pack()

    linha = tk.Frame(caixa, bg=AMARELO, height=4, width=100)
    linha.pack(pady=15)

    dica = tk.Label(caixa, text="Ou escolha uma opção no menu ao lado.", font=("Arial", 10), fg=CINZA, bg="#21103D")
    dica.pack()

def mostrar_cardapio():
    global logo_cardapio
    limpar_conteudo()

    # Logo com tratamento contra erros de arquivo ausente
    try:
        caminho_logo = os.path.join(os.path.dirname(__file__), "..", "logo_acai.jpeg")
        if os.path.exists(caminho_logo):
            imagem_logo = Image.open(caminho_logo)
            imagem_logo = imagem_logo.resize((180, 100))
            logo_cardapio = ImageTk.PhotoImage(imagem_logo)

            label_logo = tk.Label(area_conteudo, image=logo_cardapio, bg=ROXO_ESCURO)
            label_logo.image = logo_cardapio
            label_logo.pack(pady=(15, 5))
    except Exception as e:
        print(f"Aviso Imagem: {e}")

    tk.Label(area_conteudo, text="Sabor em cada escolha - Segue Nosso Cardápio!", font=("Arial", 20, "bold"), fg=VERDE, bg=ROXO_ESCURO).pack(pady=20)

    # Abas Interativas no Cardápio
    aba_parent = ttk.Notebook(area_conteudo)
    aba_parent.pack(fill="both", expand=True, padx=10, pady=5)

    # 1. MONTE O SEU
    tab_custom = tk.Frame(aba_parent, bg="#21103D")
    aba_parent.add(tab_custom, text=" 🛠 Monte o Seu ")

    tk.Label(tab_custom, text="Escolha o Tamanho:", font=("Arial", 11, "bold"), fg=AMARELO, bg="#21103D").pack(anchor="w", padx=20, pady=(10, 2))
    var_tamanho = tk.StringVar(value="300ml - R$ 15,00")
    tamanhos = [("300ml - R$ 15,00", 15.0), ("500ml - R$ 24,00", 24.0), ("700ml - R$ 35,00",35.0)]
    for text, price in tamanhos:
        tk.Radiobutton(tab_custom, text=text, variable=var_tamanho, value=text, bg="#21103D", fg=BRANCO, selectcolor=ROXO_MEDIO, activebackground="#21103D").pack(anchor="w", padx=35)

    tk.Label(tab_custom, text="Acompanhamentos (2 Grátis / Extras +R$ 3,00):", font=("Arial", 11, "bold"), fg=AMARELO, bg="#21103D").pack(anchor="w", padx=20, pady=(10, 2))
    opts_acomp = ["Granola", "Leite em Pó", "Leite Condensado", "Banana", "Morango", "Paçoca", "Nutella", "Ovomaltine", "M&M's", "Chantilly"]
    vars_acomp = {}
    for opt in opts_acomp:
        var = tk.BooleanVar()
        vars_acomp[opt] = var
        tk.Checkbutton(tab_custom, text=opt, variable=var, bg="#21103D", fg=BRANCO, selectcolor=ROXO_MEDIO, activebackground="#21103D").pack(anchor="w", padx=35)

    def add_custom():
        tam_str = var_tamanho.get()
        preco_base = float(tam_str.split("R$ ")[1].replace(",", "."))
        selecionados = [k for k, v in vars_acomp.items() if v.get()]
        extras = max(0, len(selecionados) - 2)
        preco_final = preco_base + (extras * 3.0)

        item = {"nome": f"Açaí Custom ({tam_str.split(' -')[0]})", "detalhes": ", ".join(selecionados), "preco": preco_final}
        carrinho.append(item)
        atualizar_painel_direito()
        messagebox.showinfo("Açaízon", f"Açaí foi adicionado ao pedido! (R$ {preco_final:.2f})")

    tk.Button(tab_custom, text="Adicionar Personalizado", font=("Arial", 10, "bold"), bg=ROSA, fg=BRANCO, command=add_custom).pack(pady=15)

    # 2. CATEGORIAS PRONTAS
    categorias = {
        "🥤 Tradicional": [("Açaí Tradicional 300ml", 15.90), ("Açaí Tigelão da Casa (Especial)", 30.90), ("Açaí Fitness 300ml", 29.90),("Açaí Power 500ml", 22.90)],
        "🍫 Especiais": [("Açaí Nutella 500ml", 28.00), ("Açaí Ovomaltine 500ml", 27.00)],
        "🍓 Frutas": [("Açaí Morango 500ml", 26.50), ("Açaí Banana 500ml", 25.00)],
        "🍪 Sobremesas": [("Açaí Paçoca 500ml", 27.00), ("Açaí M&M's 500ml", 29.00)],
        
    }

    for cat_nome, itens in categorias.items():
        tab_cat = tk.Frame(aba_parent, bg="#21103D")
        aba_parent.add(tab_cat, text=f" {cat_nome} ")

        for nome, preco in itens:
            f = tk.Frame(tab_cat, bg="#261044", highlightbackground=ROXO_MEDIO, highlightthickness=1)
            f.pack(fill="x", padx=20, pady=8)

            tk.Label(f, text=nome, font=("Arial", 11, "bold"), fg=BRANCO, bg="#261044").pack(side="left", padx=15, pady=10)
            tk.Label(f, text=f"R$ {preco:.2f}".replace('.', ','), font=("Arial", 11, "bold"), fg=AMARELO, bg="#261044").pack(side="right", padx=15)

            def criar_cmd(n=nome, p=preco):
                return lambda: (carrinho.append({"nome": n, "detalhes": "Pronto", "preco": p}), atualizar_painel_direito(), messagebox.showinfo("Açaízon", f"{n} foi adicionado ao pedido!"))

            tk.Button(f, text="Adicionar", font=("Arial", 9, "bold"), bg=ROSA, fg=BRANCO, command=criar_cmd()).pack(side="right", padx=5)

def mostrar_delirio_roxo():
    limpar_conteudo()
def mostrar_delirio_roxo():
    limpar_conteudo()

    # ========================================================
    # TELA DE FIDELIDADE - DELÍRIO ROXO
    # ========================================================

    # Container principal
    fidelidade = tk.Frame(
        area_conteudo,
        bg=ROXO_ESCURO
    )
    fidelidade.pack(
        fill="both",
        expand=True,
        padx=5,
        pady=5
    )

    # ========================================================
    # CABEÇALHO DO CLIENTE
    # ========================================================

    topo_cliente = tk.Frame(
        fidelidade,
        bg="#21103D",
        highlightbackground=ROXO_MEDIO,
        highlightthickness=1
    )
    topo_cliente.pack(
        fill="x",
        padx=5,
        pady=(5, 8)
    )

    # Ícone circular
    circulo = tk.Frame(
        topo_cliente,
        bg="#3A075C",
        width=58,
        height=58,
        highlightbackground=ROSA,
        highlightthickness=2
    )
    circulo.pack(
        side="left",
        padx=12,
        pady=10
    )
    circulo.pack_propagate(False)

    tk.Label(
        circulo,
        text="♙",
        font=("Arial", 30, "bold"),
        fg=ROSA_CLARO,
        bg="#3A075C"
    ).place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    # Nome
    nome_cliente = (
        cliente_logado.get("nome", "Yasmin")
        if cliente_logado
        else "Cliente"
    )

    bloco_nome = tk.Frame(
        topo_cliente,
        bg="#21103D"
    )
    bloco_nome.pack(
        side="left",
        pady=8
    )

    tk.Label(
        bloco_nome,
        text=f"Olá, {nome_cliente}! ♡",
        font=("Arial", 15, "bold"),
        fg=BRANCO,
        bg="#21103D"
    ).pack(anchor="w")

    tk.Label(
        bloco_nome,
        text="Cliente Açaízon • Delírio Roxo",
        font=("Arial", 8),
        fg=CINZA,
        bg="#21103D"
    ).pack(anchor="w")

    # Frase do lado direito
    tk.Label(
        topo_cliente,
        text="Você faz parte\n"
             "dessa energia! 💜",
        font=("Arial", 9, "italic"),
        fg=AMARELO,
        bg="#21103D",
        justify="right"
    ).pack(
        side="right",
        padx=15
    )

    # ========================================================
    # ÁREA DOS PONTOS
    # ========================================================

    pontos_atual = (
        cliente_logado.get("pontos", 70)
        if cliente_logado
        else 70
    )

    # Limite visual do próximo benefício
    meta_pontos = 100

    progresso = min(
        pontos_atual / meta_pontos,
        1
    )

    bloco_pontos = tk.Frame(
        fidelidade,
        bg="#21103D",
        highlightbackground=ROXO_MEDIO,
        highlightthickness=1
    )
    bloco_pontos.pack(
        fill="x",
        padx=5,
        pady=(0, 8)
    )

    # Parte esquerda
    lado_pontos = tk.Frame(
        bloco_pontos,
        bg="#21103D"
    )
    lado_pontos.pack(
        side="left",
        padx=15,
        pady=10
    )

    tk.Label(
        lado_pontos,
        text="👑",
        font=("Arial", 23),
        fg=AMARELO,
        bg="#21103D"
    ).pack(side="left", padx=(0, 8))

    texto_pontos = tk.Frame(
        lado_pontos,
        bg="#21103D"
    )
    texto_pontos.pack(side="left")

    tk.Label(
        texto_pontos,
        text="Seus pontos Delírio Roxo",
        font=("Arial", 8, "bold"),
        fg=BRANCO,
        bg="#21103D"
    ).pack(anchor="w")

    tk.Label(
        texto_pontos,
        text=str(pontos_atual),
        font=("Arial", 23, "bold"),
        fg=BRANCO,
        bg="#21103D"
    ).pack(side="left")

    tk.Label(
        texto_pontos,
        text=" pontos",
        font=("Arial", 9, "bold"),
        fg=AMARELO,
        bg="#21103D"
    ).pack(
        side="left",
        pady=(10, 0)
    )

    # Barra de progresso
    progresso_frame = tk.Frame(
        bloco_pontos,
        bg="#21103D"
    )
    progresso_frame.pack(
        side="left",
        fill="x",
        expand=True,
        padx=20,
        pady=12
    )

    tk.Label(
        progresso_frame,
        text=f"Faltam {max(0, meta_pontos - pontos_atual)} pontos para seu próximo benefício!",
        font=("Arial", 8),
        fg=CINZA,
        bg="#21103D"
    ).pack(anchor="w")

    barra_fundo = tk.Frame(
        progresso_frame,
        bg="#32134F",
        height=9
    )
    barra_fundo.pack(
        fill="x",
        pady=(5, 2)
    )
    barra_fundo.pack_propagate(False)

    largura_barra = max(
        5,
        int(100 * progresso)
    )

    barra = tk.Frame(
        barra_fundo,
        bg=ROSA,
        width=largura_barra,
        height=9
    )
    barra.pack(
        side="left",
        fill="y"
    )

    tk.Label(
        progresso_frame,
        text=f"{pontos_atual}/{meta_pontos}",
        font=("Arial", 7),
        fg=BRANCO,
        bg="#21103D"
    ).pack(anchor="e")

    # ========================================================
    # BOTÕES DE FIDELIDADE
    # ========================================================

    atalhos = tk.Frame(
        fidelidade,
        bg=ROXO_ESCURO
    )
    atalhos.pack(
        fill="x",
        padx=5,
        pady=(0, 8)
    )

    def criar_atalho(parent, icone, titulo, descricao, comando=None):
        card = tk.Frame(
            parent,
            bg="#21103D",
            highlightbackground=ROXO_MEDIO,
            highlightthickness=1,
            width=110,
            height=75
        )
        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=3
        )
        card.pack_propagate(False)

        botao = tk.Button(
            card,
            text=icone,
            font=("Arial", 20),
            fg=ROSA_CLARO,
            bg="#21103D",
            activebackground="#32134F",
            activeforeground=ROSA_CLARO,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            command=comando if comando else lambda: None
        )
        botao.pack(pady=(5, 0))

        tk.Label(
            card,
            text=titulo,
            font=("Arial", 8, "bold"),
            fg=BRANCO,
            bg="#21103D"
        ).pack()

        tk.Label(
            card,
            text=descricao,
            font=("Arial", 6),
            fg=CINZA,
            bg="#21103D"
        ).pack()

    criar_atalho(
        atalhos,
        "🎁",
        "Meus Pedidos",
        "Confira seus pedidos"
    )

    criar_atalho(
        atalhos,
        "☆",
        "Meus Pontos",
        "Acompanhe seus pontos"
    )

    criar_atalho(
        atalhos,
        "♡",
        "Meus Favoritos",
        "Seus sabores favoritos"
    )

    def abrir_cupom():
        messagebox.showinfo(
            "Cupons",
            "Seus cupons e benefícios aparecerão aqui."
        )

    criar_atalho(
        atalhos,
        "🎟",
        "Cupons",
        "Veja seus cupons",
        abrir_cupom
    )

    # ========================================================
    # PARTE INFERIOR
    # ========================================================

    inferior = tk.Frame(
        fidelidade,
        bg=ROXO_ESCURO
    )
    inferior.pack(
        fill="both",
        expand=True,
        padx=5
    )

    # ========================================================
    # ÚLTIMOS PEDIDOS
    # ========================================================

    pedidos = tk.Frame(
        inferior,
        bg="#21103D",
        highlightbackground=ROXO_MEDIO,
        highlightthickness=1
    )
    pedidos.pack(
        fill="both",
        expand=True,
        padx=(0, 4)
    )

    cab_pedidos = tk.Frame(
        pedidos,
        bg="#21103D"
    )
    cab_pedidos.pack(
        fill="x",
        padx=12,
        pady=(8, 5)
    )

    tk.Label(
        cab_pedidos,
        text="◷  Últimos pedidos",
        font=("Arial", 9, "bold"),
        fg=BRANCO,
        bg="#21103D"
    ).pack(side="left")

    tk.Label(
        cab_pedidos,
        text="Ver todos  ›",
        font=("Arial", 7, "bold"),
        fg=CINZA,
        bg="#21103D",
        cursor="hand2"
    ).pack(side="right")

    # Pedidos demonstrativos / últimos pedidos disponíveis
    pedidos_lista = [
        ("🍇", "Açaí Tradicional", "08/07/2025 • 14:32", "R$ 14,90"),
        ("🍓", "Açaí Especial", "05/07/2025 • 16:20", "R$ 17,90"),
        ("💜", "Açaí Power", "02/07/2025 • 12:15", "R$ 20,90")
    ]

    for icone_pedido, nome_pedido, data_pedido, valor_pedido in pedidos_lista:

        linha = tk.Frame(
            pedidos,
            bg="#261044"
        )
        linha.pack(
            fill="x",
            padx=8,
            pady=3
        )

        tk.Label(
            linha,
            text=icone_pedido,
            font=("Arial", 18),
            fg=BRANCO,
            bg="#261044"
        ).pack(
            side="left",
            padx=(5, 8)
        )

        info = tk.Frame(
            linha,
            bg="#261044"
        )
        info.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            info,
            text=nome_pedido,
            font=("Arial", 8, "bold"),
            fg=BRANCO,
            bg="#261044"
        ).pack(anchor="w")

        tk.Label(
            info,
            text=data_pedido,
            font=("Arial", 6),
            fg=CINZA,
            bg="#261044"
        ).pack(anchor="w")

        tk.Label(
            linha,
            text="Entregue",
            font=("Arial", 6, "bold"),
            fg=BRANCO,
            bg=ROXO_MEDIO
        ).pack(
            side="left",
            padx=8
        )

        tk.Label(
            linha,
            text=valor_pedido,
            font=("Arial", 8, "bold"),
            fg=BRANCO,
            bg="#261044"
        ).pack(
            side="left",
            padx=5
        )

        tk.Label(
            linha,
            text="›",
            font=("Arial", 14),
            fg=ROSA_CLARO,
            bg="#261044"
        ).pack(
            side="right",
            padx=5
        )

    # ========================================================
    # BENEFÍCIO DELÍRIO ROXO
    # ========================================================

    beneficio = tk.Frame(
        inferior,
        bg="#21103D",
        highlightbackground=ROXO_MEDIO,
        highlightthickness=1,
        width=180
    )
    beneficio.pack(
        side="right",
        fill="y",
        padx=(4, 0)
    )
    beneficio.pack_propagate(False)

    tk.Label(
        beneficio,
        text="💜",
        font=("Arial", 27),
        fg=ROSA_CLARO,
        bg="#21103D"
    ).pack(pady=(12, 3))

    tk.Label(
        beneficio,
        text="Seu próximo\nbenefício",
        font=("Arial", 10, "bold"),
        fg=BRANCO,
        bg="#21103D",
        justify="center"
    ).pack()

    tk.Label(
        beneficio,
        text="Açaí tradicional\nGRÁTIS",
        font=("Arial", 11, "bold"),
        fg=AMARELO,
        bg="#21103D",
        justify="center"
    ).pack(pady=8)

    tk.Label(
        beneficio,
        text="Ao completar\n100 pontos",
        font=("Arial", 8),
        fg=CINZA,
        bg="#21103D",
        justify="center"
    ).pack()

    def resgatar():
        if pontos_atual < meta_pontos:
            faltam = meta_pontos - pontos_atual
            messagebox.showinfo(
                "Delírio Roxo",
                f"Você ainda precisa de {faltam} pontos "
                f"para liberar seu benefício! 💜"
            )
        else:
            messagebox.showinfo(
                "Delírio Roxo",
                "Parabéns! Seu benefício está disponível! 🎁"
            )

    tk.Button(
        beneficio,
        text="Ver benefício",
        font=("Arial", 8, "bold"),
        bg=ROSA,
        fg=BRANCO,
        activebackground=ROSA_CLARO,
        activeforeground=BRANCO,
        relief="flat",
        cursor="hand2",
        command=resgatar
    ).pack(
        fill="x",
        padx=12,
        pady=12
    )
    
    
    # titulo = tk.Label(area_conteudo, text="💕 Delírio Roxo💕", font=("Arial", 24, "bold"), fg=BRANCO, bg=ROXO_ESCURO)
    # titulo.pack(pady=(30, 10))

    # subtitulo = tk.Label(area_conteudo, text="Seu espaço de fidelidade no Açaízon!", font=("Arial", 12), fg=CINZA, bg=ROXO_ESCURO)
    # subtitulo.pack()

    # caixa = tk.Frame(area_conteudo, bg="#21103D", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    # caixa.pack(fill="both", expand=True, padx=50, pady=30)

    pontos_atual = cliente_logado.get("pontos", 120) if cliente_logado else 120

    tk.Label(caixa, text="Olá, cliente! 💜", font=("Arial", 22, "bold"), fg=BRANCO, bg="#21103D").pack(pady=(30, 10))
    tk.Label(caixa, text="Você está participando do\nprograma de fidelidade Delírio Roxo.", font=("Arial", 11), fg=CINZA, bg="#21103D", justify="center").pack()

    pontos = tk.Frame(caixa, bg="#32134F", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    pontos.pack(padx=60, pady=20, fill="x")

    tk.Label(pontos, text="💜 Seus pontos", font=("Arial", 12, "bold"), fg=AMARELO, bg="#32134F").pack(pady=(15, 5))
    tk.Label(pontos, text=f"{pontos_atual} pontos", font=("Arial", 28, "bold"), fg=BRANCO, bg="#32134F").pack()
    tk.Label(pontos, text=f"Faltam {max(0, 150 - pontos_atual)} pontos para o próximo benefício!", font=("Arial", 9), fg=CINZA, bg="#32134F").pack(pady=(5, 15))

    tk.Label(caixa, text="🎁 Próximo benefício / Cupom", font=("Arial", 11, "bold"), fg=VERDE, bg="#21103D").pack(pady=(5, 5))
    tk.Label(caixa, text="Açaí tradicional grátis ou 10% DE DESCONTO", font=("Arial", 12, "bold"), fg=BRANCO, bg="#21103D").pack()

    def resgatar():
        if not carrinho:
            messagebox.showwarning("Delírio Roxo", "Adicione produtos ao carrinho antes de resgatar o cupom!")
            return
        messagebox.showinfo("Delírio Roxo", "Cupom de desconto aplicado com sucesso no checkout!")

    tk.Button(caixa, text="Resgatar Cupom no Checkout", font=("Arial", 10, "bold"), bg=VERDE, fg=BRANCO, command=resgatar).pack(pady=15)

def mostrar_configuracoes():
    limpar_conteudo()
    tk.Label(area_conteudo, text="⚙ Configurações", font=("Arial", 22, "bold"), fg=BRANCO, bg=ROXO_ESCURO).pack(pady=20)
    
    caixa = tk.Frame(area_conteudo, bg="#21103D", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    caixa.pack(fill="both", expand=True, padx=50, pady=20)

    tk.Button(caixa, text="🗑 Limpar Carrinho de Compras", font=("Arial", 11, "bold"), bg="#32134F", fg=BRANCO, anchor="w", padx=20, command=lambda: (carrinho.clear(), atualizar_painel_direito(), messagebox.showinfo("Açaízon", "Carrinho limpo."))).pack(fill="x", padx=20, pady=10)
    tk.Button(caixa, text="🚪 Sair do Sistema", font=("Arial", 11, "bold"), bg=ROSA, fg=BRANCO, anchor="w", padx=20, command=sair).pack(fill="x", padx=20, pady=10)

def sair():
    resposta = messagebox.askyesno("Sair", "Deseja realmente sair do Açaízon?")
    if resposta:
        janela.destroy()

# ============================================================
# TELA DE CHECKOUT E COMPROVANTE DE PAGAMENTO
# ============================================================
def mostrar_checkout():
    limpar_conteudo()

    tk.Label(area_conteudo, text="🛒 Finalizar Pedido", font=("Arial", 22, "bold"), fg=BRANCO, bg=ROXO_ESCURO).pack(pady=15)

    container = tk.Frame(area_conteudo, bg="#21103D", highlightbackground=ROXO_MEDIO, highlightthickness=1)
    container.pack(fill="both", expand=True, padx=30, pady=10)

    subtotal = sum(i['preco'] for i in carrinho)

    tk.Label(container, text="Forma de Pagamento:", font=("Arial", 11, "bold"), fg=AMARELO, bg="#21103D").pack(anchor="w", padx=25, pady=(15, 2))
    var_pagto = tk.StringVar(value="Pix")
    cbo_pagto = ttk.Combobox(container, textvariable=var_pagto, values=["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], state="readonly")
    cbo_pagto.pack(anchor="w", padx=25)

    tk.Label(container, text="Opção de Entrega:", font=("Arial", 11, "bold"), fg=AMARELO, bg="#21103D").pack(anchor="w", padx=25, pady=(15, 2))
    var_entrega = tk.StringVar(value="Consumo no Local")
    cbo_entrega = ttk.Combobox(container, textvariable=var_entrega, values=["Consumo no Local", "Retirada no Balcão", "Delivery (+R$ 5,00)"], state="readonly")
    cbo_entrega.pack(anchor="w", padx=25)

    def emitir_comprovante():
        taxa = 5.00 if "Delivery" in var_entrega.get() else 0.00
        total = subtotal + taxa

        comp = tk.Toplevel(janela)
        comp.title("Comprovante de Compra - Açaízon")
        comp.geometry("380x480")
        comp.configure(bg="#FFF")

        tk.Label(comp, text="--- AÇAÍZON PDV ---", font=("Courier", 14, "bold"), bg="#FFF", fg="#000").pack(pady=(15, 5))
        tk.Label(comp, text="Comprovante de Compra", font=("Courier", 10), bg="#FFF", fg="#000").pack()
        tk.Label(comp, text="-----------------------------------", bg="#FFF", fg="#000").pack()

        for item in carrinho:
            tk.Label(comp, text=f"{item['nome']} - R$ {item['preco']:.2f}", font=("Courier", 9), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20)

        tk.Label(comp, text="-----------------------------------", bg="#FFF", fg="#000").pack()
        tk.Label(comp, text=f"Subtotal: R$ {subtotal:.2f}", font=("Courier", 9), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20)
        tk.Label(comp, text=f"Taxa Entrega: R$ {taxa:.2f}", font=("Courier", 9), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20)
        tk.Label(comp, text=f"TOTAL: R$ {total:.2f}", font=("Courier", 12, "bold"), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20, pady=5)
        
        tk.Label(comp, text=f"Forma Pagto: {var_pagto.get()}", font=("Courier", 9), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20)
        tk.Label(comp, text=f"Entrega: {var_entrega.get()}", font=("Courier", 9), bg="#FFF", fg="#000", anchor="w").pack(fill="x", padx=20)
        tk.Label(comp, text="Tempo Estimado: 15 a 25 min ⏱", font=("Courier", 10, "bold"), bg="#FFF", fg="#42A62A").pack(pady=15)

        if cliente_logado:
            salvar_pedido(cliente_logado["id"], "Pedido PDV", "Vários", var_pagto.get(), var_entrega.get(), subtotal, taxa, total)

        carrinho.clear()
        atualizar_painel_direito()

        tk.Button(comp, text="Fechar / Imprimir", bg="#000", fg="#FFF", command=lambda: (comp.destroy(), mostrar_inicio())).pack(pady=10)

    tk.Button(container, text=" Confirmar & Emitir Comprovante", font=("Arial", 12, "bold"), bg=VERDE, fg=BRANCO, command=emitir_comprovante).pack(pady=30, ipadx=10, ipady=5)

# ============================================================
# CABEÇALHO
# ============================================================
cabecalho = tk.Frame(janela, bg="#3A075C", height=105)
cabecalho.pack(side="top", fill="x")
cabecalho.pack_propagate(False)

logo = tk.Label(cabecalho, text="Açaízon", font=("Arial", 30, "bold"), fg=BRANCO, bg="#3A075C")
logo.pack(side="left", padx=35)

frase = tk.Label(cabecalho, text="Mais que Açaí,\né energia pra você! ♡", font=("Arial", 10, "italic"), fg=BRANCO, bg="#3A075C", justify="left")
frase.pack(side="left", padx=20)


# ============================================================
# LOGO CENTRAL DO CABEÇALHO
# ============================================================

caminho_logo = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "assets",
        "logo_acai.jpeg"
    )
)

print("CAMINHO DA LOGO:", caminho_logo)

if os.path.exists(caminho_logo):

    # Abre a logo
    imagem_logo = Image.open(caminho_logo).convert("RGBA")

    # Pega o menor lado para formar um quadrado
    tamanho = min(imagem_logo.size)

    esquerda = (imagem_logo.width - tamanho) // 2
    cima = (imagem_logo.height - tamanho) // 2
    direita = esquerda + tamanho
    baixo = cima + tamanho

    # Recorta a imagem em formato quadrado
    imagem_logo = imagem_logo.crop(
        (esquerda, cima, direita, baixo)
    )

    # Redimensiona a logo
    tamanho_logo = 130
    imagem_logo = imagem_logo.resize(
        (tamanho_logo, tamanho_logo),
        Image.LANCZOS
    )

    # Cria uma máscara circular
    mascara = Image.new(
        "L",
        (tamanho_logo, tamanho_logo),
        0
    )

    desenho = ImageDraw.Draw(mascara)

    desenho.ellipse(
        (0, 0, tamanho_logo - 1, tamanho_logo - 1),
        fill=255
    )

    # Aplica a máscara circular
    imagem_logo.putalpha(mascara)

    # Converte para o Tkinter
    logo_central_img = ImageTk.PhotoImage(imagem_logo)

    # Cria o Label da logo
    logo_central = tk.Label(
        cabecalho,
        image=logo_central_img,
        bg="#3A075C",
        borderwidth=0
    )

    # Mantém a imagem na memória
    logo_central.image = logo_central_img

    # Coloca a logo no centro do cabeçalho
    logo_central.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

else:
    print("ERRO: Logo não encontrada!")



qualidade = tk.Label(cabecalho, text="Seu momento\nSua escolha! ✨", font=("Arial", 11, "bold"), fg=BRANCO, bg="#3A075C", justify="center")
qualidade.pack(side="right", padx=90)

# ============================================================
# CORPO PRINCIPAL
# ============================================================
corpo = tk.Frame(janela, bg=ROXO_ESCURO)
corpo.pack(fill="both", expand=True)

# ============================================================
# MENU LATERAL
# ============================================================
menu_lateral = tk.Frame(corpo, bg="#21103D", width=220)
menu_lateral.pack(side="left", fill="y", padx=(10, 5), pady=10)
menu_lateral.pack_propagate(False)

def criar_botao_menu(texto, comando, ativo=False):
    fundo = ROSA if ativo else "#32134F"
    botao = tk.Button(
        menu_lateral, text=texto, font=("Arial", 12, "bold"), bg=fundo, fg=BRANCO,
        activebackground=ROSA_CLARO, activeforeground=BRANCO, relief="flat", cursor="hand2",
        anchor="w", padx=20, command=comando
    )
    botao.pack(fill="x", padx=10, pady=7, ipady=8)
    return botao

botao_inicio = criar_botao_menu("🏠   Início", mostrar_inicio, True)
botao_cardapio = criar_botao_menu("📑   Cardápio", mostrar_cardapio)
botao_delirio = criar_botao_menu("💜   Delírio Roxo", mostrar_delirio_roxo)
botao_config = criar_botao_menu("⚙   Configurações", mostrar_configuracoes)

frase_menu = tk.Label(menu_lateral, text="Aqui seu dia\nfica mais doce! ♡", font=("Arial", 10, "italic"), fg=BRANCO, bg="#21103D", justify="left")
frase_menu.pack(side="bottom", anchor="w", padx=25, pady=35)

# ============================================================
# ÁREA CENTRAL E PAINEL DIREITO
# ============================================================
area_conteudo = tk.Frame(corpo, bg=ROXO_ESCURO)
area_conteudo.pack(side="left", fill="both", expand=True, padx=5, pady=10)

painel_direito = tk.Frame(corpo, bg="#21103D", width=290)
painel_direito.pack(side="right", fill="y", padx=(5, 10), pady=10)
painel_direito.pack_propagate(False)

# ============================================================
# PONTO DE ENTRADA DO APLICATIVO
# ============================================================
def iniciar_aplicacao():
    """Inicia a aplicação garantindo a integração correta com o main.py."""
    atualizar_painel_direito()
    mostrar_inicio()
    janela.mainloop()

if __name__ == "__main__":
    iniciar_aplicacao()