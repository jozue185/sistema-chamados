from flask import Flask, request, render_template, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configuração do MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://jozue185:04101991@cluster0.fbczupu.mongodb.net/chamados?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client["chamados"]  # Nome do banco de dados
chamados_collection = db["chamado"]  # Nome da coleção

# Lista de administradores
ADMINS = ["josue.domingues@smartfit.com", "manager@example.com"]

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
        users = {"josue.domingues@smartfit.com": "1234"} 

        if email in users and users[email] == password:
            session["user"] = email
            session["is_admin"] = email in ADMINS  # Verifica se o email está na lista de admins
            return redirect(url_for("form"))
        else:
            flash("Email ou senha incorretos!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# Rota para o dashboard
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

        # Buscar dados no MongoDB
        data = list(chamados_collection.find({}))  # Converte os resultados para uma lista de dicionários

        # Categorizar os pedidos
        not_started = len([item for item in data if item["status"] == "Não Iniciado"])
        in_progress = len([item for item in data if item["status"] == "Andamento"])
        completed = len([item for item in data if item["status"] == "Entregue"])

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

# Rota para atualizar o status
@app.route("/update-status", methods=["POST"])
def update_status():
    try:
        item_id = request.form["item_id"]
        new_status = request.form["status"]

        # Atualizar o status no MongoDB
        chamados_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"status": new_status}}
        )

        flash("Status atualizado com sucesso!", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        flash("Erro ao atualizar o status.", "danger")
        return redirect(url_for("dashboard"))

# Rota para excluir um chamado
@app.route("/delete", methods=["POST"])
def delete_item():
    try:
        item_id = request.form["item_id"]

        # Excluir o chamado no MongoDB
        chamados_collection.delete_one({"_id": ObjectId(item_id)})

        flash("Chamado excluído com sucesso!", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        print(f"Erro ao excluir chamado: {e}")
        flash("Erro ao excluir o chamado.", "danger")
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

        # Inserir no MongoDB
        chamados_collection.insert_one({
            "nome": nome,
            "departamento": department,
            "email": email,
            "descricao": description,
            "urgencia": urgency,
            "data": delivery_date,
            "status": "Não Iniciado"
        })

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
