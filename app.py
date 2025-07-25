from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
app = Flask(__name__)
CORS(app)

# Conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://Admin:Admin1234@cluster0.s7aaxq1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["Olimpiadas"]
equipos_col = db["equipos"]
partidos_col = db["partidos"]

print("✅ Conectado exitosamente a MongoDB Atlas")

# ====== Helpers ======
def serialize_doc(doc):
    """Convierte ObjectId en string para que sea JSON serializable."""
    doc["_id"] = str(doc["_id"])
    return doc

# ====== Rutas de Equipos ======
@app.route("/equipos", methods=["GET", "POST"])
def equipos():
    if request.method == "POST":
        data = request.json
        equipos_col.insert_one(data)
        return jsonify({"mensaje": "Equipo creado exitosamente"})
    equipos = list(equipos_col.find())
    return jsonify([serialize_doc(e) for e in equipos])

# ====== Comentarios (reseñas) ======
comentarios_col = db["comentarios"]

@app.route("/comentarios", methods=["GET", "POST"])
def comentarios():
    if request.method == "POST":
        data = request.json
        nuevo = {"nombre": data.get("nombre"), "mensaje": data.get("mensaje")}
        comentarios_col.insert_one(nuevo)
        nuevo["_id"] = str(nuevo["_id"])
        return jsonify(nuevo)
    else:
        comentarios = list(comentarios_col.find())
        for c in comentarios:
            c["_id"] = str(c["_id"])
        return jsonify(comentarios)


# ====== Rutas de Partidos ======
@app.route("/partidos", methods=["GET", "POST"])
def partidos():
    if request.method == "POST":
        data = request.json
        partidos_col.insert_one(data)
        return jsonify({"mensaje": "Partido registrado"})
    partidos = list(partidos_col.find())
    return jsonify([serialize_doc(p) for p in partidos])

# ====== Ranking estilo Liga FIFA ======
@app.route("/ranking/<deporte>", methods=["GET"])
def ranking(deporte):
    partidos = list(partidos_col.find({"deporte": deporte}))
    tabla = {}

    for p in partidos:
        local = p.get("equipoLocal")
        visitante = p.get("equipoVisitante")
        goles_local = p.get("golesLocal", 0)
        goles_visitante = p.get("golesVisitante", 0)

        # Inicializar equipos en la tabla si no existen
        for equipo in [local, visitante]:
            if equipo not in tabla:
                tabla[equipo] = {
                    "equipo": equipo,
                    "pj": 0, "pg": 0, "pe": 0, "pp": 0,
                    "gf": 0, "gc": 0, "dg": 0, "puntos": 0
                }

        # Actualizar partidos jugados y goles
        tabla[local]["pj"] += 1
        tabla[visitante]["pj"] += 1
        tabla[local]["gf"] += goles_local
        tabla[local]["gc"] += goles_visitante
        tabla[visitante]["gf"] += goles_visitante
        tabla[visitante]["gc"] += goles_local

        # Actualizar diferencia de goles
        tabla[local]["dg"] = tabla[local]["gf"] - tabla[local]["gc"]
        tabla[visitante]["dg"] = tabla[visitante]["gf"] - tabla[visitante]["gc"]

        # Resultado del partido
        if goles_local > goles_visitante:
            tabla[local]["pg"] += 1
            tabla[local]["puntos"] += 3
            tabla[visitante]["pp"] += 1
        elif goles_local < goles_visitante:
            tabla[visitante]["pg"] += 1
            tabla[visitante]["puntos"] += 3
            tabla[local]["pp"] += 1
        else:
            tabla[local]["pe"] += 1
            tabla[visitante]["pe"] += 1
            tabla[local]["puntos"] += 1
            tabla[visitante]["puntos"] += 1

    # Ordenar por puntos y diferencia de goles
    ranking = sorted(tabla.values(), key=lambda x: (x["puntos"], x["dg"]), reverse=True)
    return jsonify(ranking)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
