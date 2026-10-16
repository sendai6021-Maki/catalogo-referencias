import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-secreta-temporal-12345")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS_HASH = generate_password_hash(os.environ.get("ADMIN_PASS", "admin123"))

db_url = os.environ.get("DATABASE_URL", "sqlite:///referencias.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Ficha(db.Model):
    __tablename__ = "fichas"
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(80), nullable=False, index=True)
    aro = db.Column(db.String(50))
    freno = db.Column(db.String(50))
    batan = db.Column(db.String(50))
    rpm = db.Column(db.String(50))
    pasadas = db.Column(db.String(100))
    alimentacion = db.Column(db.String(100))
    transmision = db.Column(db.String(100))
    bob = db.Column(db.String(100))
    tension_bob_gra = db.Column(db.String(50))
    nota_variante = db.Column(db.String(150))

    def to_dict(self):
        return {
            "id": self.id,
            "referencia": self.referencia,
            "aro": self.aro or "",
            "freno": self.freno or "",
            "batan": self.batan or "",
            "rpm": self.rpm or "",
            "pasadas": self.pasadas or "",
            "alimentacion": self.alimentacion or "",
            "transmision": self.transmision or "",
            "bob": self.bob or "",
            "tension_bob_gra": self.tension_bob_gra or "",
            "nota_variante": self.nota_variante or ""
        }

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    resultados = []
    if query:
        resultados = Ficha.query.filter(Ficha.referencia.ilike(query)).order_by(Ficha.id.desc()).all()
    return render_template("index.html", query=query, resultados=resultados)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            session["logged_in"] = True
            return redirect(url_for("admin"))
        flash("Usuario o contraseña incorrectos", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if request.method == "POST":
        ficha_id = request.form.get("id")
        referencia = request.form.get("referencia", "").strip().upper()
        
        if ficha_id:
            ficha = Ficha.query.get(ficha_id)
            if ficha:
                ficha.referencia = referencia
                ficha.aro = request.form.get("aro")
                ficha.freno = request.form.get("freno")
                ficha.batan = request.form.get("batan")
                ficha.rpm = request.form.get("rpm")
                ficha.pasadas = request.form.get("pasadas")
                ficha.alimentacion = request.form.get("alimentacion")
                ficha.transmision = request.form.get("transmision")
                ficha.bob = request.form.get("bob")
                ficha.tension_bob_gra = request.form.get("tension_bob_gra")
                ficha.nota_variante = request.form.get("nota_variante")
        else:
            ficha = Ficha(
                referencia=referencia,
                aro=request.form.get("aro"),
                freno=request.form.get("freno"),
                batan=request.form.get("batan"),
                rpm=request.form.get("rpm"),
                pasadas=request.form.get("pasadas"),
                alimentacion=request.form.get("alimentacion"),
                transmision=request.form.get("transmision"),
                bob=request.form.get("bob"),
                tension_bob_gra=request.form.get("tension_bob_gra"),
                nota_variante=request.form.get("nota_variante")
            )
            db.session.add(ficha)
        
        db.session.commit()
        return redirect(url_for("admin"))

    fichas = Ficha.query.order_by(Ficha.referencia.asc(), Ficha.id.desc()).all()
    fichas_dict = [f.to_dict() for f in fichas]
    return render_template("admin.html", fichas=fichas_dict)

@app.route("/admin/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    ficha = Ficha.query.get(id)
    if ficha:
        db.session.delete(ficha)
        db.session.commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
