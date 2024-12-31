from flask import Flask, request, render_template, redirect, url_for, flash, session
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

USER_FILE = "users.txt"  # Arquivo com usuários e senhas

# Lista de administradores
ADMINS = ["josue.domingues@smartfit.com", "manager@example.com"]

# Dados simulados no código
dados = [
    {
        "nome": "Teste",
        "department": "TI",
        "email": "teste@example.com",
        "description": "Teste de entrada",
        "urgency": "Alta",
        "date": "2024-12-31",
        "status": "Entregue",
    },
    {
        "nome": "Maria",
        "department": "RH",
        "email": "maria@example.com",
        "description": "Revisar políticas",
        "urgency": "Média",
        "date": "2024-11-30",
        "status": "Andamento",
    },
    {
        "nome": "João",
        "department": "Financeiro",
        "email": "joao@example.com",
        "description": "Preparar relatório",
        "urgency": "Alta",
        "date": "2024-12-15",
        "status": "Não Iniciado",
    },
]

# Função para carregar usuários e senhas
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return {line.split("|")[0]: line.split("|")[1].strip() for line in f.readlines()}

# Rota inicial para redirecionar para o login
@app.route("/")
def home():
    return redirect(url_for("login"))

# Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        users = load_users()

        if email in users and users[email] == password:
            session["user"] = email
            session["is_admin"] = email in ADMINS
            return redirect(url_for("form"))
        else:
            flash("Email ou senha incorretos!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# Rota para o dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Você precisa fazer login para acessar esta página.", "danger")
        return redirect(url_for("login"))

    if not session.get("is_admin", False):
        flash("Acesso negado. Apenas administradores podem acessar o dashboard.", "danger")
        return redirect(url_for("form"))

    # Categorizar os pedidos
    not_started = len([item for item in dados if item["status"] == "Não Iniciado"])
    in_progress = len([item for item in dados if item["status"] == "Andamento"])
    completed = len([item for item in dados if item["status"] == "Entregue"])

    return render_template(
        "dashboard.html",
        data=dados,
        not_started_count=not_started,
        in_progress_count=in_progress,
        completed_count=completed,
    )

# Rota para atualizar o status
@app.route("/update-status", methods=["POST"])
def update_status():
    try:
        # Capturar o ID e o novo status do formulário
        item_id = int(request.form["item_id"])
        new_status = request.form["status"]

        # Validar se o índice está dentro do intervalo
        if 0 <= item_id < len(dados):
            dados[item_id]["status"] = new_status
            flash("Status atualizado com sucesso!", "success")
        else:
            flash("Item inválido.", "danger")

    except ValueError as ve:
        flash(f"Erro ao processar o ID: {ve}", "danger")
    except Exception as e:
        flash(f"Erro inesperado: {e}", "danger")

    return redirect(url_for("dashboard"))

# Rota para deletar um item
@app.route("/delete", methods=["POST"])
def delete_item():
    try:
        # Capturar o ID do item a ser deletado
        item_id = int(request.form["item_id"])

        # Validar se o índice está dentro do intervalo
        if 0 <= item_id < len(dados):
            dados.pop(item_id)
            flash("Pedido excluído com sucesso!", "success")
        else:
            flash("Item inválido.", "danger")

    except ValueError as ve:
        flash(f"Erro ao processar o ID: {ve}", "danger")
    except Exception as e:
        flash(f"Erro inesperado: {e}", "danger")

    return redirect(url_for("dashboard"))

# Rota para o formulário de chamados
@app.route("/form")
def form():
    if "user" not in session:
        flash("Você precisa fazer login para acessar esta página.", "danger")
        return redirect(url_for("login"))

    user_email = session["user"]
    user_name = user_email.split("@")[0]
    return render_template("form.html", user_name=user_name)

# Rota para processar o envio do formulário
@app.route("/send-email", methods=["POST"])
def send_email():
    try:
        # Capturar os dados do formulário
        nome = request.form["nome"]
        department = request.form["department"]
        email = request.form["email"]
        delivery_date = request.form["delivery_date"]
        description = request.form["description"]
        urgency = request.form["urgency"]

        # Adicionar os dados à lista
        dados.append(
            {
                "nome": nome,
                "department": department,
                "email": email,
                "description": description,
                "urgency": urgency,
                "date": delivery_date,
                "status": "Não Iniciado",
            }
        )

        flash("Solicitação enviada com sucesso!", "success")
        return redirect(url_for("form"))
    except Exception as e:
        print(f"Erro ao processar o formulário: {e}")
        flash("Erro ao salvar os dados.", "danger")
        return redirect(url_for("form"))

# Rota para logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("is_admin", None)
    flash("Você saiu com sucesso!", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
