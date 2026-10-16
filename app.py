import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Cats")

ADMIN_USER = os.environ.get("ADMIN_USER", "Sendai6021")
ADMIN_PASS_HASH = generate_password_hash(os.environ.get("ADMIN_PASS", "Haru&Maki1302"))

db_url = os.environ.get("DATABASE_URL", "sqlite:///referencias.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Ficha(db.Model):
    __tablename__ = "fichas"
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(80), nullable=False, index=True)
    aro = db.Column(db.String(50), default="")
    freno = db.Column(db.String(50), default="")
    batan = db.Column(db.String(50), default="")
    tex = db.Column(db.String(100), default="")
    rpm = db.Column(db.String(50), default="")
    pasadas = db.Column(db.String(100), default="")
    alimentacion = db.Column(db.String(100), default="")
    transmision = db.Column(db.String(100), default="")
    bob = db.Column(db.String(100), default="")
    tipo_bobinador = db.Column(db.String(50), default="")  # Bobinador grande / Bobinador pequeño
    tension_bob_gra = db.Column(db.String(50), default="")  # Valor de Tensión
    nota_variante = db.Column(db.String(150), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "referencia": self.referencia or "",
            "aro": self.aro or "",
            "freno": self.freno or "",
            "batan": self.batan or "",
            "tex": self.tex or "",
            "rpm": self.rpm or "",
            "pasadas": self.pasadas or "",
            "alimentacion": self.alimentacion or "",
            "transmision": self.transmision or "",
            "bob": self.bob or "",
            "tipo_bobinador": self.tipo_bobinador or "",
            "tension_bob_gra": self.tension_bob_gra or "",
            "nota_variante": self.nota_variante or ""
        }

with app.app_context():
    db.create_all()
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE fichas ADD COLUMN IF NOT EXISTS tex VARCHAR(100);"))
            conn.execute(text("ALTER TABLE fichas ADD COLUMN IF NOT EXISTS tipo_bobinador VARCHAR(50);"))
            conn.commit()
    except Exception as e:
        print("Aviso al verificar columnas:", e)

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
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
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
        
        if ficha_id and ficha_id.isdigit():
            ficha = db.session.get(Ficha, int(ficha_id))
            if ficha:
                ficha.referencia = referencia
                ficha.aro = request.form.get("aro", "")
                ficha.freno = request.form.get("freno", "")
                ficha.batan = request.form.get("batan", "")
                ficha.tex = request.form.get("tex", "")
                ficha.rpm = request.form.get("rpm", "")
                ficha.pasadas = request.form.get("pasadas", "")
                ficha.alimentacion = request.form.get("alimentacion", "")
                ficha.transmision = request.form.get("transmision", "")
                ficha.bob = request.form.get("bob", "")
                ficha.tipo_bobinador = request.form.get("tipo_bobinador", "")
                ficha.tension_bob_gra = request.form.get("tension_bob_gra", "")
                ficha.nota_variante = request.form.get("nota_variante", "")
        else:
            ficha = Ficha(
                referencia=referencia,
                aro=request.form.get("aro", ""),
                freno=request.form.get("freno", ""),
                batan=request.form.get("batan", ""),
                tex=request.form.get("tex", ""),
                rpm=request.form.get("rpm", ""),
                pasadas=request.form.get("pasadas", ""),
                alimentacion=request.form.get("alimentacion", ""),
                transmision=request.form.get("transmision", ""),
                bob=request.form.get("bob", ""),
                tipo_bobinador=request.form.get("tipo_bobinador", ""),
                tension_bob_gra=request.form.get("tension_bob_gra", ""),
                nota_variante=request.form.get("nota_variante", "")
            )
            db.session.add(ficha)
        
        db.session.commit()
        return redirect(url_for("admin"))

    fichas = Ficha.query.order_by(Ficha.referencia.asc(), Ficha.id.desc()).all()
    return render_template("admin.html", fichas=fichas)

@app.route("/admin/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    ficha = db.session.get(Ficha, id)
    if ficha:
        db.session.delete(ficha)
        db.session.commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)





                
