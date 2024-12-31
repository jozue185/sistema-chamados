from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

USER_FILE = "users.txt"  # Arquivo com usuários e senhas
DATA_FILE = "data.txt"  # Arquivo para armazenar os dados do formulário

# Lista de administradores
ADMINS = ["josue.domingues@smartfit.com", "manager@example.com"]

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
            session["is_admin"] = email in ADMINS  # Verifica se o email está na lista de admins
            return redirect(url_for("form"))
        else:
            flash("Email ou senha incorretos!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

#rota para o dashboard
@app.route("/dashboard")
@app.route("/dashboard")
def dashboard():
    try:
        # Verificar se o usuário está logado
        if "user" not in session:
            flash("Você precisa fazer login para acessar esta página.", "danger")
            return redirect(url_for("login"))

        # Verificar se o usuário é administrador
        if not session.get("is_admin", False):
            flash("Acesso negado. Apenas administradores podem acessar o dashboard.", "danger")
            return redirect(url_for("form"))

        # Carregar os dados do arquivo
        data = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # Dividir os campos do TXT
                        parts = line.strip().split("|")
                        data.append({
                            "nome": parts[0].split(":")[1].strip(),
                            "department": parts[1].split(":")[1].strip(),
                            "email": parts[2].split(":")[1].strip(),
                            "description": parts[3].split(":")[1].strip(),
                            "urgency": parts[4].split(":")[1].strip(),
                            "date": parts[5].split(":")[1].strip(),
                            "status": parts[6].split(":")[1].strip(),
                        })
                    except IndexError as e:
                        print(f"Erro ao processar linha: {line} - {e}")
                        continue

        # Categorizar os pedidos
        not_started = len([item for item in data if item["status"] == "Não Iniciado"])
        in_progress = len([item for item in data if item["status"] == "Andamento"])
        completed = len([item for item in data if item["status"] == "Entregue"])

        # Renderizar o template com os dados
        return render_template(
            "dashboard.html",
            data=data,
            not_started_count=not_started,
            in_progress_count=in_progress,
            completed_count=completed
        )
    except Exception as e:
        print(f"Erro ao carregar o dashboard: {e}")
        flash("Erro ao carregar os dados do dashboard.", "danger")
        return redirect(url_for("form"))

#Deletar Pedido
@app.route("/update-status", methods=["POST"])
def update_status():
    item_id = int(request.form["item_id"]) - 1  # Ajustar o índice do loop
    new_status = request.form["status"]

    # Carregar os dados do arquivo
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()

        # Atualizar a linha correspondente
        if 0 <= item_id < len(lines):
            parts = lines[item_id].strip().split("|")
            parts[-1] = f" Status: {new_status}"  # Atualizar o status
            lines[item_id] = " | ".join(parts) + "\n"

        # Salvar os dados de volta no arquivo
        with open(DATA_FILE, "w") as f:
            f.writelines(lines)

    flash("Status atualizado com sucesso!", "success")
    return redirect(url_for("dashboard"))

@app.route("/delete", methods=["POST"])
def delete_item():
    item_id = int(request.form["item_id"]) - 1  # Ajustar o índice do loop

    # Carregar os dados do arquivo
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()

        # Remover a linha correspondente
        if 0 <= item_id < len(lines):
            del lines[item_id]

        # Salvar os dados de volta no arquivo
        with open(DATA_FILE, "w") as f:
            f.writelines(lines)

    flash("Pedido excluído com sucesso!", "success")
    return redirect(url_for("dashboard"))


# Rota para o formulário de chamados
@app.route("/form")
def form():
    if "user" not in session:
        flash("Você precisa fazer login para acessar esta página.", "danger")
        return redirect(url_for("login"))
    
    # Extrai o nome do usuário (parte antes do @)
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

        # Salvar os dados no banco de dados
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        # Inserir os dados na tabela 'chamados'
        cursor.execute("""
        INSERT INTO chamados (nome, departamento, email, descricao, urgencia, data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, department, email, description, urgency, delivery_date, "Não Iniciado"))
        conn.commit()  # IMPORTANTE: Confirma as alterações no banco
        conn.close()

        # Mensagem de sucesso e redirecionamento
        flash("Solicitação enviada com sucesso!", "success")
        return redirect(url_for("form"))
    except Exception as e:
        print(f"Erro ao processar o formulário: {e}")
        flash("Erro ao salvar os dados no banco.", "danger")
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
