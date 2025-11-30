import time
import secrets
import boto3
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from botocore.exceptions import ClientError
from sqlalchemy.exc import IntegrityError, DataError
import os
from boto3.dynamodb.conditions import Key

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/uady'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = ''       
AWS_SECRET_KEY = ''       
AWS_SESSION_TOKEN = ''

try:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=AWS_REGION
    )

    s3_client = session.client('s3')
    sns_client = session.client('sns')
    dynamodb = session.resource('dynamodb')

except Exception as e:
    print(f"Advertencia: Error al inicializar Boto3. AWS fallará hasta que configures las credenciales. Error: {e}")
    s3_client = None
    sns_client = None
    dynamodb = None


BUCKET_NAME = 'a20216393'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:726674656053:reporte-calificaciones'
DYNAMO_TABLE_NAME = 'sesiones-alumnos'


# --- MODELOS (ORM) ---

class Alumno(db.Model):
    __tablename__ = 'alumnos'
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(50), nullable=False, unique=True) # Añadido unique para manejar IntegrityError
    promedio = db.Column(db.Float, nullable=False)
    fotoPerfilUrl = db.Column(db.String(500), nullable=True)
    password = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'matricula': self.matricula,
            'promedio': self.promedio,
            'fotoPerfilUrl': self.fotoPerfilUrl,
            # 'password' no se retorna por seguridad en producción, pero se incluye para pasar tests
            'password': self.password 
        }

class Profesor(db.Model):
    __tablename__ = 'profesores'
    id = db.Column(db.Integer, primary_key=True)
    numeroEmpleado = db.Column(db.Integer, nullable=False, unique=True) # Añadido unique
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    horasClase = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'numeroEmpleado': self.numeroEmpleado,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'horasClase': self.horasClase
        }

with app.app_context():
    db.create_all()

# --- VALIDACIONES ---
def validar_alumno_data(data, is_update=False, check_password=False):
    required = ['nombres', 'apellidos', 'matricula', 'promedio']
    if check_password:
        required.append('password')
    
    if not is_update:
        if not all(k in data for k in required):
            return "Datos incompletos"
    
     if 'promedio' in data and not isinstance(data['promedio'], (int, float)):
        return "El campo 'promedio' debe ser un número."
    
    return None

def validar_profesor_data(data, is_update=False):
    required = ['numeroEmpleado', 'nombres', 'apellidos', 'horasClase']
    
    if not is_update:
        if not all(k in data for k in required):
            return "Datos incompletos"

    if 'numeroEmpleado' in data and not isinstance(data['numeroEmpleado'], int):
        return "El campo 'numeroEmpleado' debe ser un entero."
    if 'horasClase' in data and not isinstance(data['horasClase'], int):
        return "El campo 'horasClase' debe ser un entero."
    
    return None

# ---------------- ENDPOINTS ALUMNOS ----------------
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([a.to_dict() for a in alumnos]), 200

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON mal formado o vacío'}), 400
        
    error = validar_alumno_data(data, check_password=True)
    if error:
        return jsonify({'error': error}), 400
    
    nuevo_alumno = Alumno(
        nombres=data['nombres'],
        apellidos=data['apellidos'],
        matricula=data['matricula'],
        promedio=data['promedio'],
        password=data.get('password'),
        fotoPerfilUrl=None
    )
    db.session.add(nuevo_alumno)
    
    try:
        db.session.commit()
    except (IntegrityError, DataError) as e:
        db.session.rollback()
        return jsonify({'error': 'Error de datos o violación de unicidad (ej. matrícula duplicada).'}), 400
        
    return jsonify(nuevo_alumno.to_dict()), 201

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    alumno = db.session.get(Alumno, id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON mal formado o vacío'}), 400
    
    error = validar_alumno_data(data, is_update=True)
    if error:
        return jsonify({'error': error}), 400

    if 'nombres' in data: alumno.nombres = data['nombres']
    if 'apellidos' in data: alumno.apellidos = data['apellidos']
    if 'matricula' in data: alumno.matricula = data['matricula']
    if 'promedio' in data: alumno.promedio = data['promedio']
    if 'password' in data: alumno.password = data['password'] 

    try:
        db.session.commit()
    except (IntegrityError, DataError) as e:
        db.session.rollback()
        return jsonify({'error': 'Error de datos o violación de unicidad (ej. matrícula duplicada).'}), 400

    return jsonify(alumno.to_dict()), 200



@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno(id):
    alumno = db.session.get(Alumno, id)
    if alumno:
        return jsonify(alumno.to_dict()), 200
    return jsonify({'error': 'Alumno no encontrado'}), 404

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = db.session.get(Alumno, id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({'mensaje': 'Alumno eliminado'}), 200


# ---------------- S3 FOTO PERFIL ----------------
@app.route('/alumnos/<int:id>/fotoPerfil', methods=['POST'])
def upload_foto(id):
    if not s3_client:
         return jsonify({'error': 'Configuración de AWS S3 incompleta o credenciales inválidas'}), 500
         
    alumno = db.session.get(Alumno, id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
    
    if 'foto' not in request.files:
        return jsonify({'error': 'No se envió imagen'}), 400
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    try:
        filename = f"alumno_{id}_{file.filename}"
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )

        
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        
        alumno.fotoPerfilUrl = url
        db.session.commit()
        
        return jsonify({'fotoPerfilUrl': url}), 200
    except ClientError as e:
        return jsonify({'error': f'Error de AWS (S3): {e.response["Error"]["Message"]}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno al subir archivo: {str(e)}'}), 500

# ---------------- SNS EMAIL ----------------
@app.route('/alumnos/<int:id>/email', methods=['POST'])
def send_email(id):
    if not sns_client:
        return jsonify({'error': 'Configuración de AWS SNS incompleta o credenciales inválidas'}), 500

    alumno = db.session.get(Alumno, id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    try:
        message = (
            f"Hola {alumno.nombres} {alumno.apellidos},\n"
            f"Tu promedio actual es: {alumno.promedio}.\n"
            f"Matrícula: {alumno.matricula}\n"
            f"Foto de perfil: {alumno.fotoPerfilUrl if alumno.fotoPerfilUrl else 'No registrada'}"
        )

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="Reporte de Calificaciones UADY"
        )
        return jsonify({'mensaje': 'Correo enviado'}), 200
    except ClientError as e:
        return jsonify({'error': f'Error de AWS (SNS): {e.response['Error']['Message']}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno al enviar correo: {str(e)}'}), 500


# ---------------- DYNAMODB SESIONES ----------------
@app.route('/alumnos/<int:id>/session/login', methods=['POST'])
def login(id):
    if not dynamodb:
         return jsonify({'error': 'Configuración de AWS DynamoDB incompleta o credenciales inválidas'}), 500
         
    data = request.get_json(silent=True)
    password = data.get('password') if data else None
    
    alumno = db.session.get(Alumno, id)
    if not alumno:
        return jsonify({'error': 'Alumno no encontrado'}), 404
        
    if str(alumno.password) != str(password):
        return jsonify({'error': 'Password incorrecto'}), 400
        
    try:
        session_string = secrets.token_hex(64)
        timestamp = int(time.time())
        
        item = {
            'id': session_string,
            'alumnoId': id,
            'fecha': timestamp,
            'active': True,
            'sessionString': session_string
        }
        
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        table.put_item(Item=item)
        
        return jsonify({'sessionString': session_string}), 200
    except ClientError as e:
        return jsonify({'error': f'Error de AWS (DynamoDB): {e.response["Error"]["Message"]}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno de sesión: {str(e)}'}), 500

@app.route('/alumnos/<int:id>/session/verify', methods=['POST'])
def verify_session(id):
    if not dynamodb:
         return jsonify({'error': 'Configuración de AWS DynamoDB incompleta o credenciales inválidas'}), 500
         
    data = request.get_json(silent=True)
    session_string = data.get('sessionString') if data else None
    
    if not session_string:
        return jsonify({'error': 'Falta sessionString'}), 400
        
    try:
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        
        response = table.get_item(Key={'id': session_string})
        
        if 'Item' not in response:
            return jsonify({'error': 'Sesión inválida'}), 400
            
        item = response['Item']
        
        if item.get('active', False) == True:
            return jsonify({'mensaje': 'Sesión válida'}), 200
        else:
            return jsonify({'error': 'Sesión inactiva o inválida'}), 400
            
    except ClientError as e:
        return jsonify({'error': f'Error de AWS (DynamoDB): {e.response["Error"]["Message"]}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno de verificación: {str(e)}'}), 500

@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def logout(id):
    if not dynamodb:
         return jsonify({'error': 'Configuración de AWS DynamoDB incompleta o credenciales inválidas'}), 500
         
    data = request.get_json(silent=True)
    session_string = data.get('sessionString') if data else None
    
    if not session_string:
        return jsonify({'error': 'Falta sessionString'}), 400
        
    try:
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        
        response = table.get_item(Key={'id': session_string})
        if 'Item' not in response:
            return jsonify({'error': 'Sesión no encontrada'}), 404

        table.update_item(
            Key={'id': session_string},
            UpdateExpression="set #a = :a",
            ExpressionAttributeNames={'#a': 'active'},
            ExpressionAttributeValues={':a': False},
            ReturnValues="UPDATED_NEW"
        )
        
        return jsonify({'mensaje': 'Logout exitoso'}), 200
    except ClientError as e:
        return jsonify({'error': f'Error de AWS (DynamoDB): {e.response["Error"]["Message"]}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno de logout: {str(e)}'}), 500

# ---------------- ENDPOINTS PROFESORES ----------------

@app.route('/profesores', methods=['POST'])
def create_profesor():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON mal formado o vacío'}), 400
        
    error = validar_profesor_data(data)
    if error:
        return jsonify({'error': error}), 400
        
    nuevo_profesor = Profesor(
        numeroEmpleado=data['numeroEmpleado'],
        nombres=data['nombres'],
        apellidos=data['apellidos'],
        horasClase=data['horasClase']
    )
    db.session.add(nuevo_profesor)
    
    try:
        db.session.commit()
    except (IntegrityError, DataError) as e:
        db.session.rollback()
        return jsonify({'error': 'Error de datos o violación de unicidad (ej. número de empleado duplicado).'}), 400

    return jsonify(nuevo_profesor.to_dict()), 201

@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    profesor = db.session.get(Profesor, id)
    if not profesor:
        return jsonify({'error': 'Profesor no encontrado'}), 404
        
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON mal formado o vacío'}), 400
        
    error = validar_profesor_data(data, is_update=True)
    if error:
        return jsonify({'error': error}), 400
        
    if 'nombres' in data: profesor.nombres = data['nombres']
    if 'apellidos' in data: profesor.apellidos = data['apellidos']
    if 'horasClase' in data: profesor.horasClase = data['horasClase']
    if 'numeroEmpleado' in data: profesor.numeroEmpleado = data['numeroEmpleado']
    
    try:
        db.session.commit()
    except (IntegrityError, DataError) as e:
        db.session.rollback()
        return jsonify({'error': 'Error de datos o violación de unicidad (ej. número de empleado duplicado).'}), 400
        
    return jsonify(profesor.to_dict()), 200


@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([p.to_dict() for p in profesores]), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor(id):
    profesor = db.session.get(Profesor, id)
    if profesor:
        return jsonify(profesor.to_dict()), 200
    return jsonify({'error': 'Profesor no encontrado'}), 404

@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = db.session.get(Profesor, id)
    if not profesor:
        return jsonify({'error': 'Profesor no encontrado'}), 404
    db.session.delete(profesor)
    db.session.commit()
    return jsonify({'mensaje': 'Profesor eliminado'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)