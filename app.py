from flask import Flask, jsonify, request

app = Flask(__name__)

alumnos = []
profesores = []

def validar_alumno(data, id_unico=True):
    required_fields = ('id', 'nombres', 'apellidos', 'matricula', 'promedio')
    if not data or not all(k in data for k in required_fields):
        return "Datos incompletos"

    if not isinstance(data['id'], int):
        return "El id debe ser un número entero"
    if any(not isinstance(data[f], str) or not data[f].strip() for f in ('nombres', 'apellidos', 'matricula')):
        return "Nombres, apellidos y matrícula deben ser cadenas no vacías"
    if not isinstance(data['promedio'], (int, float)):
        return "El promedio debe ser numérico"

    if id_unico and any(a['id'] == data['id'] for a in alumnos):
        return "Ya existe un alumno con ese id"

    return None  # Sin errores


def validar_profesor(data, id_unico=True):
    required_fields = ('id', 'numeroEmpleado', 'nombres', 'apellidos', 'horasClase')
    if not data or not all(k in data for k in required_fields):
        return "Datos incompletos"

    if not isinstance(data['id'], int):
        return "El id debe ser un número entero"
    if not isinstance(data['numeroEmpleado'], (str, int)) or str(data['numeroEmpleado']).strip() == "" or int(data['numeroEmpleado']) < 0:
        return "El número de empleado debe ser una cadena o número positivo no vacío"
    if any(not isinstance(data[f], str) or not data[f].strip() for f in ('nombres', 'apellidos')):
        return "Nombres y apellidos deben ser cadenas no vacías"
    if not isinstance(data['horasClase'], (int, float)) or data['horasClase'] < 0:
        return "Las horas de clase deben ser numéricas (positivo)"

    if id_unico and any(p['id'] == data['id'] for p in profesores):
        return "Ya existe un profesor con ese id"

    return None  # Sin errores


# ---------------- ALUMNOS ----------------
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    return jsonify(alumnos), 200

@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno(id):
    for alumno in alumnos:
        if alumno['id'] == id:
            return jsonify(alumno), 200
    return jsonify({'error': 'Alumno no encontrado'}), 404

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    data = request.get_json(force=True)
    error = validar_alumno(data, id_unico=True)
    if error:
        return jsonify({'error': error}), 400
    alumnos.append(data)
    return jsonify({'mensaje': 'Alumno creado'}), 201

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    data = request.get_json(force=True)
    for alumno in alumnos:
        if alumno['id'] == id:
            error = validar_alumno({**alumno, **data}, id_unico=False)
            if error:
                return jsonify({'error': error}), 400
            alumno.update(data)
            return jsonify({'mensaje': 'Alumno actualizado'}), 200
    return jsonify({'error': 'Alumno no encontrado'}), 404

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    global alumnos
    if any(a['id'] == id for a in alumnos):
        alumnos = [a for a in alumnos if a['id'] != id]
        return jsonify({'mensaje': 'Alumno eliminado'}), 200
    return jsonify({'error': 'Alumno no encontrado'}), 404


# ---------------- PROFESORES ----------------
@app.route('/profesores', methods=['GET'])
def get_profesores():
    return jsonify(profesores), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor(id):
    for profesor in profesores:
        if profesor['id'] == id:
            return jsonify(profesor), 200
    return jsonify({'error': 'Profesor no encontrado'}), 404

@app.route('/profesores', methods=['POST'])
def create_profesor():
    data = request.get_json(force=True)
    error = validar_profesor(data, id_unico=True)
    if error:
        return jsonify({'error': error}), 400
    profesores.append(data)
    return jsonify({'mensaje': 'Profesor creado'}), 201

@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    data = request.get_json(force=True)
    for profesor in profesores:
        if profesor['id'] == id:
            error = validar_profesor({**profesor, **data}, id_unico=False)
            if error:
                return jsonify({'error': error}), 400
            profesor.update(data)
            return jsonify({'mensaje': 'Profesor actualizado'}), 200
    return jsonify({'error': 'Profesor no encontrado'}), 404

@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    global profesores
    if any(p['id'] == id for p in profesores):
        profesores = [p for p in profesores if p['id'] != id]
        return jsonify({'mensaje': 'Profesor eliminado'}), 200
    return jsonify({'error': 'Profesor no encontrado'}), 404


# ---------------- ERRORES ----------------
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)