from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from threading import Thread
from pathlib import Path
from balancer_aws import *
from balancer_ibm import *
import botocore.session
import boto3
import re
import os
import configparser

app = Flask(__name__)
CORS(app)


# ******************************************************************************************************************************************
# *Clase hilo*******************************************************************************************************************************
# ******************************************************************************************************************************************
# Clase padre Hilo con los atributos compartidos entre AWS y IBM.
class Hilo(Thread):
    def __init__(self, aws_arn_device_o_name_ibm, circuito, tipo_circuito, shots_ejecutar, tipo_ejecucion):
        super().__init__()
        self.aws_arn_device_o_name_ibm = aws_arn_device_o_name_ibm
        self.circuito = circuito
        self.tipo_circuito = tipo_circuito
        self.shots_ejecutar = shots_ejecutar
        self.tipo_ejecucion = tipo_ejecucion
        self.resultado = ""


# Clase hija AWS con sus atributos propios y el método run donde se ejecuta el circuito según la información almacenada.
class AWS(Hilo):
    def __init__(self, aws_arn_device_o_name_ibm, circuito, tipo_circuito, shots_ejecutar, aws_bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds):
        super().__init__(aws_arn_device_o_name_ibm, circuito,
                         tipo_circuito, shots_ejecutar, tipo_ejecucion)
        self.aws_bucket_s3 = aws_bucket_s3
        self.poll_timeout_seconds = poll_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    def run(self):
        self.resultado = ejecutar_servicio_cuantico_aws(
            self.aws_arn_device_o_name_ibm, self.circuito, self.tipo_circuito, self.shots_ejecutar, self.aws_bucket_s3, self.tipo_ejecucion, self.poll_timeout_seconds, self.poll_interval_seconds)


# Clase hija IBM con sus atributos propios y el método run donde se ejecuta el circuito según la información almacenada.
class IBM(Hilo):
    def __init__(self, aws_arn_device_o_name_ibm, circuito, tipo_circuito, shots_ejecutar, tipo_ejecucion, optimization_level, resilience_level):
        super().__init__(aws_arn_device_o_name_ibm, circuito,
                         tipo_circuito, shots_ejecutar, tipo_ejecucion)
        self.optimization_level = optimization_level
        self.resilience_level = resilience_level

    def run(self):
        self.resultado = ejecutar_servicio_cuantico_ibm(
            self.aws_arn_device_o_name_ibm, self.circuito, self.tipo_circuito, self.shots_ejecutar, self.tipo_ejecucion, self.optimization_level, self.resilience_level)

# ******************************************************************************************************************************************
# ******************************************************************************************************************************************
# ******************************************************************************************************************************************


def index_show_aws():
    respuesta = '''
    # Los parámetros aceptados para luego mostrar los recursos disponibles en el proveedor de AWS son:
    # * aws_access_key_id       -> ID que nos asocia a nuestro usuario de AWS.
    # * aws_secret_access_key   -> Clave secreta que nos asocia a nuestro usuario de AWS. 
    '''
    return respuesta


def index_aws(tipo):
    respuesta = ""

    if (tipo == "Error"):
        respuesta = "# Error - No se ha recibido el json con los parámetros."

    respuesta += '''
    # Los parámetros aceptados para luego elegir la mejor combinación a la hora de lanzar el programa en el proveedor de AWS son:
    # * aws_access_key_id       -> ID que nos asocia a nuestro usuario de AWS.
    # * aws_secret_access_key   -> Clave secreta que nos asocia a nuestro usuario de AWS. 
    # * tipo_ejecucion          -> Si queremos obtener el resultado de la ejecución o la probabilidad de cada resultado. (Puede variar entre - "ejecucion" o "probabilidad")
    # * poll_timeout_seconds    -> El tiempo de espera de sondeo para la tarea de AWS. (Por defecto - 432000 segundos = 5 días. Puede variar entre - 1 segundo a 432000 segundos)
    # * poll_interval_seconds   -> El intervalo de sondeo para la tarea de AWS. (Por defecto - 1 segundo. Puede variar entre - 1 segundo a 432000 segundos)
    # * maquinas_aws            -> Especifica en qué conjunto de recursos de AWS se quiere ejecutar el programa. (Por ejemplo - ["SV1", "TN1", "dm1"])
    # * shots_maquinas_aws      -> Especifica el número de shots para cada recurso de AWS donde se quiere ejecutar el programa. (Por ejemplo - [10,10,10])
    # * tipo                    -> Tipo de recurso cuántico donde queremos que se ejecute el programa. (Por defecto - ["SIMULATOR", "QPU"]. Puede variar entre - ["SIMULATOR", "QPU"], ["SIMULATOR"] o ["QPU"])
    # * shots                   -> Especifica el número de shots del programa. (Por ejemplo - 10)
    # * qbits                   -> Especifica el valor mínimo de Qubits que debe tener el recurso donde vamos a ejecutar el programa. (Por ejemplo - 5)
    # * numero_buscado_recursos -> Número de recursos que buscamos para ejecutar el programa. (Por defecto - 1)
    # * circuito_api            -> Circuito que vamos a querer ejecutar procedente de una url. (Por ejemplo - "https://algassert.com/quirk#circuit={%22cols%22:[[%22H%22],[1,%22X%22,%22X%22],[%22X%22,%22%E2%80%A2%22],[%22X%22,1,%22%E2%80%A2%22],[%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22]]}")
    # * circuito_openqasm       -> Circuito que vamos a querer ejecutar procedente de un formato OPENQASM. (Por ejemplo - "OPENQASM 3;qubit[2] q;bit[2] c;h q[0];h q[1];x q[1];h q[1];cnot q[0], q[1];h q[1];x q[1];h q[1];c = measure q;")
    # * bucket_s3               -> Nombre del bucket S3 que vamos a utilizar para guardar los resultados obtenidos tras la ejecución. (Por defecto - tfg-ignacio-2023)
    '''
    return respuesta


def index_show_ibm():
    respuesta = '''
    # Los parámetros aceptados para luego mostrar los recursos disponibles en el proveedor de IBM son:
    # * api_token               -> Token de IBM que nos asocia a nuestra cuenta.
    '''
    return respuesta


def index_ibm(tipo):
    respuesta = ""

    if (tipo == "Error"):
        respuesta = "# Error - No se ha recibido el json con los parámetros."

    respuesta += '''
    # Los parámetros aceptados para luego elegir la mejor combinación a la hora de lanzar el programa en el proveedor de IBM son:
    # * api_token               -> Token de IBM que nos asocia a nuestra cuenta.
    # * tipo_ejecucion          -> Si queremos obtener el resultado de la ejecución o la probabilidad de cada resultado. (Puede variar entre - "ejecucion" o "probabilidad")
    # * optimization_level      -> Cuánta optimización vamos a querer realizar en los circuitos. (Por defecto - 1 si se trata de una ejecución y 3 si se trata de una probabilidad, rango de 0 a 3 todos inclusive)
    # * resilience_level        -> Cuánta resiliencia vamos a tomar contra los errores. (Por defecto - 1 si se trata de una probabilidad, rango de 0 a 2 todos inclusive)
    # * maquinas_ibm            -> Especifica en qué conjunto de recursos de IBM se quiere ejecutar el programa. (Por ejemplo - ["ibmq_belem", "ibmq_qasm_simulator", "ibmq_jakarta"])
    # * shots_maquinas_ibm      -> Especifica el número de shots para cada recurso de IBM donde se quiere ejecutar el programa. (Por ejemplo - [10,10,10])
    # * tipo                    -> Tipo de recurso cuántico donde queremos que se ejecute el programa. (Por defecto - ["SIMULATOR", "QPU"]. Puede variar entre - ["SIMULATOR", "QPU"], ["SIMULATOR"] o ["QPU"])
    # * shots                   -> Especifica el número de shots del programa. (Por ejemplo - 10)
    # * qbits                   -> Especifica el valor mínimo de Qubits que debe tener el recurso donde vamos a ejecutar el programa. (Por ejemplo - 5)
    # * numero_buscado_recursos -> Número de recursos que buscamos para ejecutar el programa. (Por defecto - 1)
    # * circuito_api            -> Circuito que vamos a querer ejecutar procedente de una url. (Por ejemplo - "https://algassert.com/quirk#circuit={%22cols%22:[[%22H%22],[1,%22X%22,%22X%22],[%22X%22,%22%E2%80%A2%22],[%22X%22,1,%22%E2%80%A2%22],[%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22]]}")
    # * circuito_openqasm       -> Circuito que vamos a querer ejecutar procedente de un formato OPENQASM. (Por ejemplo - "OPENQASM 2.0;include \"qelib1.inc\";qreg q[2];creg c[2];h q[0];h q[1];x q[1];h q[1];cx q[0], q[1];h q[1];x q[1];h q[1];measure q[1] -> c[1];")
    '''
    return respuesta


def index_aws_ibm(tipo):
    respuesta = ""

    if (tipo == "Error"):
        respuesta = "# Error - No se ha recibido el json con los parámetros."

    respuesta = '''
    # Los parámetros aceptados para luego elegir la mejor combinación a la hora de lanzar el programa en alguno de los proveedores de AWS e IBM son:
    # * aws_access_key_id           -> ID que nos asocia a nuestro usuario de AWS.
    # * aws_secret_access_key       -> Clave secreta que nos asocia a nuestro usuario de AWS. 
    # * api_token                   -> Token de IBM que nos asocia a nuestra cuenta.
    # * tipo_ejecucion              -> Si queremos obtener el resultado de la ejecución o la probabilidad de cada resultado. (Puede variar entre - "ejecucion" o "probabilidad")
    # * poll_timeout_seconds        -> El tiempo de espera de sondeo para la tarea de AWS. (Por defecto - 432000 segundos = 5 días. Puede variar entre - 1 segundo a 432000 segundos)
    # * poll_interval_seconds       -> El intervalo de sondeo para la tarea de AWS. (Por defecto - 1 segundo. Puede variar entre - 1 segundo a 432000 segundos)
    # * optimization_level          -> Cuánta optimización vamos a querer realizar en los circuitos. (Por defecto - 1 si se trata de una ejecución y 3 si se trata de una probabilidad, rango de 0 a 3 todos inclusive)
    # * resilience_level            -> Cuánta resiliencia vamos a tomar contra los errores. (Por defecto - 1 si se trata de una probabilidad, rango de 0 a 2 todos inclusive)
    # * maquinas_aws                -> Especifica en qué conjunto de recursos de AWS se quiere ejecutar el programa. (Por ejemplo - ["SV1", "TN1", "dm1"])
    # * shots_maquinas_aws          -> Especifica el número de shots para cada recurso de AWS donde se quiere ejecutar el programa. (Por ejemplo - [10,10,10])
    # * maquinas_ibm                -> Especifica en qué conjunto de recursos de IBM se quiere ejecutar el programa. (Por ejemplo - ["ibmq_belem", "ibmq_qasm_simulator", "ibmq_jakarta"])
    # * shots_maquinas_ibm          -> Especifica el número de shots para cada recurso de IBM donde se quiere ejecutar el programa. (Por ejemplo - [10,10,10])
    # * tipo                        -> Tipo de recurso cuántico donde queremos que se ejecute el programa. (Por defecto - ["SIMULATOR", "QPU"]. Puede variar entre - ["SIMULATOR", "QPU"], ["SIMULATOR"] o ["QPU"])
    # * shots_aws                   -> Especifica el número de shots del programa para AWS. (Por ejemplo - 10)
    # * shots_ibm                   -> Especifica el número de shots del programa para IBM. (Por ejemplo - 10)
    # * shots                       -> Especifica el número de shots del programa. (Por ejemplo - 10)
    # * qbits_aws                   -> Especifica el valor mínimo de Qubits que debe tener el recurso donde vamos a ejecutar el programa en AWS. (Por ejemplo - 5)
    # * qbits_ibm                   -> Especifica el valor mínimo de Qubits que debe tener el recurso donde vamos a ejecutar el programa en IBM. (Por ejemplo - 5)
    # * qbits                       -> Especifica el valor mínimo de Qubits que debe tener el recurso donde vamos a ejecutar el programa. (Por ejemplo - 5)
    # * numero_buscado_recursos_aws -> Número de recursos que buscamos para ejecutar el programa en AWS. (Por ejemplo - 2)
    # * numero_buscado_recursos_ibm -> Número de recursos que buscamos para ejecutar el programa en IBM. (Por ejemplo - 2)
    # * numero_buscado_recursos     -> Número de recursos que buscamos para ejecutar el programa. (Por defecto - 1)
    # * circuito_api                -> Circuito que vamos a querer ejecutar procedente de una url. (Por ejemplo - "https://algassert.com/quirk#circuit={%22cols%22:[[%22H%22],[1,%22X%22,%22X%22],[%22X%22,%22%E2%80%A2%22],[%22X%22,1,%22%E2%80%A2%22],[%22H%22],[%22Measure%22,%22Measure%22,%22Measure%22]]}")
    # * circuito_openqasm_aws       -> Circuito que vamos a querer ejecutar procedente de un formato OPENQASM en AWS. (Por ejemplo - "OPENQASM 3;qubit[2] q;bit[2] c;h q[0];h q[1];x q[1];h q[1];cnot q[0], q[1];h q[1];x q[1];h q[1];c = measure q;")
    # * circuito_openqasm_ibm       -> Circuito que vamos a querer ejecutar procedente de un formato OPENQASM en IBM. (Por ejemplo - "OPENQASM 2.0;include \"qelib1.inc\";qreg q[2];creg c[2];h q[0];h q[1];x q[1];h q[1];cx q[0], q[1];h q[1];x q[1];h q[1];measure q[1] -> c[1];")
    # * bucket_s3                   -> Nombre del bucket S3 que vamos a utilizar para guardar los resultados obtenidos tras la ejecución. (Por defecto - tfg-ignacio-2023)
    '''
    return respuesta


# **********************************************************************************************************************************************
# *Métodos AWS**********************************************************************************************************************************
# **********************************************************************************************************************************************
# Método utilizado para crear los hilos que luego se ejecutarán en AWS.
def main_aws(buscar_o_comprobar_maquinas, tipo, shots, qbits, numero_buscado_recursos, circuito, tipo_circuito, maquinas_aws, shots_maquinas_aws, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds):

    maquinas = []
    # Si no nos pasan las máquinas donde tenemos que ejecutar, tenemos que obtener las mejores, tomando como referencia las que saldrían más baratas.
    if (buscar_o_comprobar_maquinas == "buscar"):
        maquinas = recursos_recomendado_aws(
            tipo, shots, qbits, numero_buscado_recursos)
    # Si nos pasan las máquinas donde tenemos que ejecutar tenemos que comprobar que estén disponibles para que podamos ejecutar en ellas.
    else:
        maquinas = comprobar_recursos_aws(maquinas_aws, shots_maquinas_aws)

    hilos = []

    # Comprobamos si está creado el bucket s3 donde se va a almacenar los resultados de la ejecución.
    comprobar_bucket_s3(bucket_s3)

    # Recorremos todas las máquinas donde vamos a ejecutar para ir creando los hilos de ejecución.
    for indice, i in enumerate(maquinas):
        # Si estamos buscando máquinas, los shots son iguales para todas ellas.
        if (buscar_o_comprobar_maquinas == "buscar"):
            hilo = AWS(i.arn, circuito,
                       tipo_circuito, shots, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            hilos.append(hilo)
        # Si por el contrario, hemos recibido ya las máquinas donde vamos a ejecutar, cada máquina tiene sus propios shots.
        else:
            hilo = AWS(i.arn, circuito,
                       tipo_circuito, shots_maquinas_aws[indice], bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            hilos.append(hilo)

    # Devolvemos los hilos creados que ya tienen toda la información para su ejecución.
    return hilos


# Método para comprobar si existe un bucket_s3 con un nombre recibido por parámetro.
def comprobar_bucket_s3(bucket_s3):
    # Primero creamos la sesión que utilizamos para comprobar la región de nuestra cuenta.
    session = botocore.session.Session()
    # Obtenemos la región de nuestras credenciales guardadas.
    region = session.get_config_variable('region')
    # Creamos el cliente de s3 qie utilizamos para comprobar si existe el recurso s3.
    s3 = boto3.client('s3')
    # Obtenemos la lista de todos los buckets que tenemos creados.
    buckets = [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
    # Si no tenemos el bucket con ese nombre lo creamos.
    if bucket_s3 not in buckets:
        try:
            s3.create_bucket(ACL='private', Bucket=bucket_s3,
                             CreateBucketConfiguration={'LocationConstraint': region})
        except:
            abort(400, "Error - el nombre del bucket s3 puede que ya exista.")


def comprobar_nombre_bucket(bucket_s3):

    if len(bucket_s3) < 3 or len(bucket_s3) > 49:
        abort(400, "Error - los nombres de los buckets s3 deben tener entre 3 (mínimo) y 49 (máximo) caracteres.")

    patron = r'^[a-z0-9][a-z0-9\.-]*[a-z0-9]$'
    if not re.match(patron, bucket_s3):
        abort(400, "Error - los nombres de los buckets s3 deben contener solamente letras minúsculas, números, puntos (.) y guiones (-). Además deben comenzar y terminar con una letra o un número.")

    if '..' in bucket_s3:
        abort(400, "Error - los nombres de los buckets s3 no deben contener dos puntos adyacentes.")


def comprobar_cuentas_aws():
    # Si ejecutamos en aws tenemos que ver si está todo configurado.
    home = str(Path.home())
    os.makedirs(os.path.expanduser("~/.aws"), exist_ok=True)
    if (not os.path.isfile(os.path.join(home, ".aws/credentials"))):
        crear_cuenta_default_aws()
    if (not os.path.isfile(os.path.join(home, ".aws/config"))):
        crear_region_default_aws()


# Método para crear las credenciales por defecto.
def crear_cuenta_default_aws():

    credentials = {
        'aws_access_key_id': 'AWS_KEY_ID',
        'aws_secret_access_key': 'AWS_SECRET_KEY'
    }

    config = configparser.ConfigParser()
    config["default"] = credentials

    # Guarde los cambios en el archivo .aws/credentials
    with open(os.path.expanduser('~/.aws/credentials'), 'w') as configfile:
        config.write(configfile)


# Método para crear la region por defecto.
def crear_region_default_aws():

    credentials = {
        'region': 'us-west-2',
        'output': 'json'
    }

    config = configparser.ConfigParser()
    config["default"] = credentials

    # Guarde los cambios en el archivo .aws/config
    with open(os.path.expanduser('~/.aws/config'), 'w') as configfile:
        config.write(configfile)


# Método para configurar la cuenta por defecto.
def cuenta_default_aws():

    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials'))

    # Configuramos la cuenta con las claves por defecto.
    config.set('default', 'aws_access_key_id', '!!!!!')
    config.set('default', 'aws_secret_access_key',
               '$$$$$')

    # Guarde los cambios en el archivo .aws/credentials
    with open(os.path.expanduser('~/.aws/credentials'), 'w') as configfile:
        config.write(configfile)


# Método para configurar la cuenta a partir de una cuenta nueva que nos pasan.
def cuenta_default_modificar(aws_access_key_id, aws_secret_access_key):

    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials'))

    # Configuramos la cuenta con las claves por defecto.
    config.set('default', 'aws_access_key_id', aws_access_key_id)
    config.set('default', 'aws_secret_access_key', aws_secret_access_key)

    # Guarde los cambios en el archivo .aws/credentials
    with open(os.path.expanduser('~/.aws/credentials'), 'w') as configfile:
        config.write(configfile)


# Método para ver si tenemos que usar la cuenta por defecto o una cuenta nueva que nos pasan.
def comprobar_si_configurar_cuenta_aws(aws_access_key_id, aws_secret_access_key):
    # Si no nos pasan una cuenta de aws, usamos la cuenta por defecto.
    if (aws_access_key_id == None and aws_secret_access_key == None):
        cuenta_default_aws()
    # Si nos pasan la nueva cuenta de aws, hay que modificarla.
    else:
        cuenta_default_modificar(aws_access_key_id, aws_secret_access_key)


# Método para comprobar si recibimos los dos parámetros para configurar la cuenta de aws.
def comprobar_parametros_cuenta_aws(aws_access_key_id, aws_secret_access_key):
    # Si solamente nos han mandado los nombres de las máquinas y no los shots para cada máquina o viceversa.
    if ((aws_access_key_id == None and aws_secret_access_key != None) or (aws_access_key_id != None and aws_secret_access_key == None)):
        abort(400, "Error - hay que configurar tanto el access_key_id como el secret_access_key.")


def comprobar_poll_timeout_seconds_poll_interval_seconds(poll_timeout_seconds, poll_interval_seconds):

    if (type(poll_timeout_seconds) != int or poll_timeout_seconds < 1 or poll_timeout_seconds > 432000):
        abort(
            400, "Error - el parámetro poll_timeout_seconds sólo puede tener valores entre [1, 432000].")
    if (type(poll_interval_seconds) != int or poll_interval_seconds < 1 or poll_interval_seconds > 432000):
        abort(
            400, "Error - el parámetro poll_interval_seconds sólo puede tener valores entre [1, 432000].")

# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************


# **********************************************************************************************************************************************
# *Métodos IBM**********************************************************************************************************************************
# **********************************************************************************************************************************************
# Método utilizado para crear los hilos que luego se ejecutarán en IBM.
def main_ibm(buscar_o_comprobar_maquinas, tipo, shots, qbits, numero_buscado_recursos, circuito, tipo_circuito, maquinas_ibm, shots_maquinas_ibm, tipo_ejecucion, optimization_level, resilience_level):

    maquinas = []
    # Si no nos pasan las máquinas donde tenemos que ejecutar, tenemos que obtener las mejores, tomando como referencia las que tienen menos trabajos en cola.
    if (buscar_o_comprobar_maquinas == "buscar"):
        maquinas = recursos_recomendado_ibm(
            tipo, shots, qbits, numero_buscado_recursos)
    # Si nos pasan las máquinas donde tenemos que ejecutar tenemos que comprobar que estén disponibles para que podamos ejecutar en ellas.
    else:
        maquinas = comprobar_recursos_ibm(maquinas_ibm, shots_maquinas_ibm)

    hilos = []

    # Recorremos todas las máquinas donde vamos a ejecutar para ir creando los hilos de ejecución.
    for indice, i in enumerate(maquinas):
        # Si estamos buscando máquinas, los shots son iguales para todas ellas. Como son máquinas de IBM, no reciben el nombre del bucket S3 que es propio de AWS.
        if (buscar_o_comprobar_maquinas == "buscar"):
            hilo = IBM(i.nombre, circuito,
                       tipo_circuito, shots, tipo_ejecucion, optimization_level, resilience_level)
            hilos.append(hilo)
        # Si por el contrario, hemos recibido ya las máquinas donde vamos a ejecutar, cada máquina tiene sus propios shots. . Como son máquinas de IBM, no reciben el nombre del bucket S3 que es propio de AWS.
        else:
            hilo = IBM(i.nombre, circuito,
                       tipo_circuito, shots_maquinas_ibm[indice], tipo_ejecucion, optimization_level, resilience_level)
            hilos.append(hilo)

    # Devolvemos los hilos creados que ya tienen toda la información para su ejecución.
    return hilos


# Método para guardar el token de la cuenta de IBM Quantum que nos han pasado, si no nos han pasado token, se usa el predeterminado.
def comprobar_api_token(api_token):
    # Si no nos pasan el token de la cuenta se usa el predeterminado.
    if (api_token == None):
        guardar_token_QiskitRuntimeService()
    # Si nos pasan un token se usa dicho token.
    else:
        guardar_token_QiskitRuntimeService_nuevo(api_token)


def comprobar_optimization_level_resilience_level(tipo_ejecucion, optimization_level, resilience_level):

    # Si el tipo de ejecución es probabilidad, que significa que se usa el Sampler en IBM Quantum.
    if (tipo_ejecucion == "probabilidad"):
        if (type(optimization_level) != int or optimization_level < 0 or optimization_level > 3):
            abort(
                400, "Error - el parámetro optimization_level sólo puede tener valores entre [0, 3].")
        if (type(resilience_level) != int or resilience_level < 0 or resilience_level > 2):
            abort(
                400, "Error - el parámetro resilience_level sólo puede tener valores entre [0, 2].")

# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************


# **********************************************************************************************************************************************
# *Métodos Ambas********************************************************************************************************************************
# **********************************************************************************************************************************************
def comprobar_metodo_ejecucion(tipo_ejecucion):
    if (tipo_ejecucion == None or (tipo_ejecucion != "ejecucion" and tipo_ejecucion != "probabilidad")):
        abort(400, "Error - es necesario especificar el tipo de ejecución que se va a utilizar (ejecucion o probabilidad).")


def comprobar_maquinas_y_shots(maquinas, shots):
    # Si solamente nos han mandado los nombres de las máquinas y no los shots para cada máquina o viceversa.
    if ((maquinas == None and shots != None) or (maquinas != None and shots == None)):
        abort(400, "Error - hay que configurar tanto los nombres de las máquinas como los shots de dichas máquinas.")

    # Si nos han mandado tanto el nombre de las máquinas como los shots para cada máquina.
    if (maquinas != None and shots != None):
        if (not isinstance(maquinas, list) or not isinstance(shots, list)):
            abort(400, "Error - tanto los nombres de las máquinas como los shots de dichas máquinas se deben recibir como una lista.")

        if not all(isinstance(element, str) for element in maquinas):
            abort(
                400, "Error - todos los nombres de las máquinas deben ser nombres.")

        if not all(isinstance(element, int) for element in shots):
            abort(
                400, "Error - todos los shots de las máquinas deben ser números enteros.")

        if not all(element > 0 for element in shots):
            abort(
                400, "Error - todos los shots de las máquinas deben ser números enteros mayores que 0.")

        if (len(maquinas) != len(shots)):
            abort(400, "Error - cada máquina debe tener su shots asociado.")


def comprobar_tipo_maquina(tipo, maquinas_aws, shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm):
    # Si no hemos introducido máquinas específicas, tenemos que introducir el tipo de máquina a buscar.
    if (maquinas_aws == None and shots_maquinas_aws == None) or (maquinas_ibm == None and shots_maquinas_ibm == None):
        if (tipo != ['SIMULATOR'] and tipo != ['QPU'] and tipo != ["SIMULATOR", "QPU"] and tipo != ["QPU", "SIMULATOR"]):
            abort(400, "Error - es necesario especificar el tipo de recurso que se quiere buscar (SIMULATOR, QPU o ambos).")


def comprobar_shots_o_qbits(tipo, shots_o_qbits, maquinas_aws, shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm, shots_o_qbits_específicos_aws, shots_o_qbits_específicos_ibm):
    # Si no se han mandado máquinas especificas con sus shots.
    if (maquinas_aws == None and shots_maquinas_aws == None and shots_o_qbits_específicos_aws == None) or (maquinas_ibm == None and shots_maquinas_ibm == None and shots_o_qbits_específicos_ibm == None):
        if (shots_o_qbits == None or type(shots_o_qbits) != int or shots_o_qbits <= 0):
            if (tipo == "shots"):
                abort(
                    400, "Error - es necesario especificar el número de shots del programa como un número mayor que 0.")
            if (tipo == "qbits"):
                abort(
                    400, "Error - es necesario especificar el número de qbits mínimo para el recurso cuántico como un número mayor que 0.")


def comprobar_shots_o_qbits_de_un_proveedor(tipo, shots_o_qbits, maquinas, shots_maquinas):
    # Si no se han mandado máquinas especificas con sus shots.
    if (maquinas == None and shots_maquinas == None):
        # Si hemos introducido datos
        if (shots_o_qbits != None):
            if (type(shots_o_qbits) != int or shots_o_qbits <= 0):
                if (tipo == "shots"):
                    abort(
                        400, "Error - es necesario especificar el número de shots del programa como un número mayor que 0.")
                if (tipo == "qbits"):
                    abort(
                        400, "Error - es necesario especificar el número de qbits mínimo para el recurso cuántico como un número mayor que 0.")


def comprobar_numero_buscado_recursos_aws_ibm(numero_buscado_recursos, maquinas, shots_maquinas):
    # Si no hemos introducido máquinas específicas.
    if (maquinas == None and shots_maquinas == None):
        # Si buscamos un numero especifico de recursos
        if (numero_buscado_recursos != None):
            if (type(numero_buscado_recursos) != int or numero_buscado_recursos <= 0):
                abort(
                    400, "Error - es necesario especificar el número buscado de recursos como un número mayor o igual a 1.")


def comprobar_numero_buscado_recursos_por_defecto_aws_ibm(numero_buscado_recursos, maquinas_aws, shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm, numero_buscado_recursos_aws, numero_buscado_recursos_ibm):
    # Si no se han mandado máquinas especificas con sus shots.
    if (maquinas_aws == None and shots_maquinas_aws == None and numero_buscado_recursos_aws == None) or (maquinas_ibm == None and shots_maquinas_ibm == None and numero_buscado_recursos_ibm == None):
        if (type(numero_buscado_recursos) != int or numero_buscado_recursos <= 0):
            abort(
                400, "Error - es necesario especificar el número buscado de recursos como un número mayor o igual a 1.")


def comprobar_si_se_recibe_circuito(circuito_api, circuito_openqasm):
    # Si no nos pasan ningún circuito no vamos a poder ejecutar ningún circuito.
    if (circuito_api == None and circuito_openqasm == None):
        abort(400, "Error - es necesario especificar la url del circuito cuántico o el circuito cuántico en formato OPENQASM.")

    # Si nos pasan dos circuitos da error, solamente podemos ejecutar uno solo.
    if (circuito_api != None and circuito_openqasm != None):
        abort(400, "Error - solamente se puede elegir entre  especificar la url del circuito cuántico o el circuito cuántico en formato OPENQASM.")


def comprobar_si_se_recibe_circuito_aws_ibm(circuito_api, circuito_openqasm_aws, circuito_openqasm_ibm):
    # Si no nos pasan ningún circuito no vamos a poder ejecutar ningún circuito.
    if (circuito_api == None and circuito_openqasm_aws == None and circuito_openqasm_ibm == None):
        abort(400, "Error - es necesario especificar la url del circuito cuántico o los circuitos cuánticos en formato OPENQASM para aws e ibm.")

    # Si nos pasan dos circuitos da error, solamente podemos ejecutar uno solo.
    if (circuito_api != None and circuito_openqasm_aws != None and circuito_openqasm_ibm != None) or (circuito_api != None and circuito_openqasm_aws != None and circuito_openqasm_ibm == None) or (circuito_api != None and circuito_openqasm_aws == None and circuito_openqasm_ibm != None) or (circuito_api == None and circuito_openqasm_aws != None and circuito_openqasm_ibm == None) or (circuito_api == None and circuito_openqasm_aws == None and circuito_openqasm_ibm != None):
        abort(400, "Error - solamente se puede elegir entre especificar la url del circuito cuántico o los dos circuitos cuánticos en formato OPENQASM para aws e ibm.")


def comprobar_tipo_maquina_individual(tipo, maquinas, shots_maquinas):
    # Si no hemos introducido máquinas específicas, tenemos que introducir el tipo de máquina a buscar.
    if (maquinas == None and shots_maquinas == None):
        if (tipo != ['SIMULATOR'] and tipo != ['QPU'] and tipo != ["SIMULATOR", "QPU"] and tipo != ["QPU", "SIMULATOR"]):
            abort(400, "Error - es necesario especificar el tipo de recurso que se quiere buscar (SIMULATOR, QPU o ambos).")


def comprobar_shots_o_qbits_ambos(tipo, shots_o_qbits, maquinas, shots_maquinas):
    # Si no se han mandado máquinas especificas con sus shots.
    if (maquinas == None and shots_maquinas == None):
        if (shots_o_qbits == None or type(shots_o_qbits) != int or shots_o_qbits <= 0):
            if (tipo == "shots"):
                abort(
                    400, "Error - es necesario especificar el número de shots del programa como un número mayor que 0.")
            if (tipo == "qbits"):
                abort(
                    400, "Error - es necesario especificar el número de qbits mínimo para el recurso cuántico como un número mayor que 0.")


def comprobar_numero_buscado_recursos(numero_buscado_recursos, maquinas, shots_maquinas):
    # Si no hemos introducido máquinas específicas, tenemos que introducir el número de recursos que queremos buscar.
    if (maquinas == None and shots_maquinas == None):
        if (type(numero_buscado_recursos) != int or numero_buscado_recursos <= 0):
            abort(400, "Error - es necesario especificar el número buscado de recursos como un número mayor o igual a 1.")


def organizar_main(proveedor, maquinas, tipo, shots, qbits, numero_buscado_recursos, circuito_api, circuito_openqasm, shots_maquinas, bucket_s3, tipo_ejecucion, optimization_level, resilience_level, poll_timeout_seconds, poll_interval_seconds):
    lista = []
    # Si no nos pasan una máquina o máquinas específicas.
    if (maquinas == None):
        # Si se va a ejecutar con un circuito que procede de una url.
        if (circuito_api != None):
            # Si se va a ejecutar en aws.
            if (proveedor == "aws"):
                lista = main_aws("buscar", tipo, shots, qbits, numero_buscado_recursos, circuito_api,
                                 "circuito_api", maquinas, shots_maquinas, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            # Si se va a ejecutar en ibm.
            else:
                lista = main_ibm("buscar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_api, "circuito_api", maquinas, shots_maquinas, tipo_ejecucion, optimization_level, resilience_level)
        # Si se va a ejecutar con un circuito que procede de un formato OPENQASM.
        else:
            # Si se va a ejecutar en aws.
            if (proveedor == "aws"):
                lista = main_aws("buscar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_openqasm, "circuito_openqasm", maquinas, shots_maquinas, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            # Si se va a ejecutar en ibm.
            else:
                lista = main_ibm("buscar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_openqasm, "circuito_openqasm", maquinas, shots_maquinas, tipo_ejecucion, optimization_level, resilience_level)

    # Si nos pasan una máquina o máquinas específicas.
    else:
        # Si se va a ejecutar con un circuito que procede de una url.
        if (circuito_api != None):
            # Si se va a ejecutar en aws.
            if (proveedor == "aws"):
                lista = main_aws("comprobar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_api, "circuito_api", maquinas, shots_maquinas, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            # Si se va a ejecutar en ibm.
            else:
                lista = main_ibm("comprobar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_api, "circuito_api", maquinas, shots_maquinas, tipo_ejecucion, optimization_level, resilience_level)
        # Si se va a ejecutar con un circuito que procede de un formato OPENQASM.
        else:
            # Si se va a ejecutar en aws.
            if (proveedor == "aws"):
                lista = main_aws("comprobar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_openqasm, "circuito_openqasm", maquinas, shots_maquinas, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds)
            # Si se va a ejecutar en ibm.
            else:
                lista = main_ibm("comprobar", tipo, shots, qbits,
                                 numero_buscado_recursos, circuito_openqasm, "circuito_openqasm", maquinas, shots_maquinas, tipo_ejecucion, optimization_level, resilience_level)
    return lista


def comprobar_shots_qbits_proveedor(shots_qbits_proveedor, shots_qbits):
    if (shots_qbits_proveedor != None):
        return shots_qbits_proveedor
    else:
        return shots_qbits


def comprobar_numero_buscado_recursos_ibm_aws(numero_buscado_recursos_proveedor, numero_buscado_recursos):
    if (numero_buscado_recursos_proveedor != None):
        return numero_buscado_recursos_proveedor
    else:
        return numero_buscado_recursos


# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************


# **********************************************************************************************************************************************
# *Llamadas API Load Balancer*******************************************************************************************************************
# **********************************************************************************************************************************************
# Método para recibir las llamadas GET a /execute_aws/info
@app.route('/execute_aws/info', methods=["get"])
def execute_load_balancer_aws_info():
    return index_aws("Info")


# Método para recibir las llamadas GET a /execute_aws/show/info
@app.route('/execute_aws/show/info', methods=["get"])
def execute_load_balancer_aws_show_info():
    return index_show_aws()


# Método para recibir las llamadas GET a /execute_aws/show
@app.route('/execute_aws/show', methods=["get"])
def execute_load_balancer_aws_show():

    # Recogemos todos los parámetros que nos mandan mediante un json.
    contenido = request.get_json(silent=True)

    # ? ***********************************************
    # Comprobamos si las credenciales de la cuenta de aws están configuradas.
    comprobar_cuentas_aws()
    # ? ***********************************************

    # Si no nos mandan el json, la cuenta con la que buscaremos los recursos disponibles de AWS para mostrar será la predeterminada.
    if contenido:
        # ? ***********************************************
        aws_access_key_id = contenido.get("aws_access_key_id", None)
        aws_secret_access_key = contenido.get("aws_secret_access_key", None)
        # Comprobamos primero si recibimos los dos parámetros.
        comprobar_parametros_cuenta_aws(
            aws_access_key_id, aws_secret_access_key)
        # Configuramos la cuenta con los nuevos parámetros recibidos.
        comprobar_si_configurar_cuenta_aws(
            aws_access_key_id, aws_secret_access_key)
        # Comprobamos si la configuración de la cuenta es válida.
        comprobar_si_la_configuracion_es_valida()
        # ? **********************************************

    # Aquí ya tendríamos los resultados que se devuelven como json.
    resultados = obtener_maquinas_y_simuladores_disponibles_aws_para_mostrar()
    # Devolvemos el conjunto de json que se han generado como resultados.
    return jsonify(resultados)


# Método para recibir las llamadas GET a /execute_aws
@app.route('/execute_aws', methods=["get"])
def execute_load_balancer_aws():

    # Recogemos todos los parámetros que nos mandan mediante un json.
    contenido = request.get_json(silent=True)

    # Si no nos mandan el json, se muestra los parámetros aceptados con un breve resumen de cada uno de ellos.
    if not contenido:
        abort(400, index_aws("Error"))

    print("Llamada /execute_aws")

    # ? ***********************************************
    # Comprobamos si las credenciales de la cuenta de aws están configuradas.
    comprobar_cuentas_aws()
    # ? ***********************************************

    # ? ***********************************************
    aws_access_key_id = contenido.get("aws_access_key_id", None)
    aws_secret_access_key = contenido.get("aws_secret_access_key", None)
    # Comprobamos primero si recibimos los dos parámetros.
    comprobar_parametros_cuenta_aws(aws_access_key_id, aws_secret_access_key)
    # Configuramos la cuenta con los nuevos parámetros recibidos.
    comprobar_si_configurar_cuenta_aws(
        aws_access_key_id, aws_secret_access_key)
    # Comprobamos si la configuración de la cuenta es válida.
    comprobar_si_la_configuracion_es_valida()
    # ? ***********************************************

    # ? ***********************************************
    tipo_ejecucion = contenido.get("tipo_ejecucion", None)
    comprobar_metodo_ejecucion(tipo_ejecucion)
    print("tipo_ejecucion: ", tipo_ejecucion)
    # ? ***********************************************

    # ? ***********************************************
    poll_timeout_seconds = contenido.get("poll_timeout_seconds", 432000)
    poll_interval_seconds = contenido.get("poll_interval_seconds", 1)
    comprobar_poll_timeout_seconds_poll_interval_seconds(
        poll_timeout_seconds, poll_interval_seconds)
    print("poll_timeout_seconds: ", poll_timeout_seconds)
    print("poll_interval_seconds: ", poll_interval_seconds)
    # ? ***********************************************

    # ? ***********************************************
    maquinas_aws = contenido.get("maquinas_aws", None)
    shots_maquinas_aws = contenido.get("shots_maquinas_aws", None)
    comprobar_maquinas_y_shots(maquinas_aws, shots_maquinas_aws)
    print("maquinas_aws: ", maquinas_aws)
    print("shots_maquinas_aws: ", shots_maquinas_aws)
    # ? ***********************************************

    # ? ***********************************************
    tipo = contenido.get("tipo", ["SIMULATOR", "QPU"])
    comprobar_tipo_maquina_individual(
        tipo, maquinas_aws, shots_maquinas_aws)
    print("tipo: ", tipo)
    # ? ***********************************************

    # ? ***********************************************
    shots = contenido.get("shots", None)
    comprobar_shots_o_qbits_ambos("shots", shots, maquinas_aws,
                                  shots_maquinas_aws)
    print("shots: ", shots)
    # ? ***********************************************

    # ? ***********************************************
    qbits = contenido.get("qbits", None)
    comprobar_shots_o_qbits_ambos("qbits", qbits, maquinas_aws,
                                  shots_maquinas_aws)
    print("qbits: ", qbits)
    # ? ***********************************************

    # ? ***********************************************
    numero_buscado_recursos = contenido.get("numero_buscado_recursos", 1)
    comprobar_numero_buscado_recursos(
        numero_buscado_recursos, maquinas_aws, shots_maquinas_aws)
    print("numero_buscado_recursos: ", numero_buscado_recursos)
    # ? ***********************************************

    # ? ***********************************************
    circuito_api = contenido.get("circuito_api", None)
    circuito_openqasm = contenido.get("circuito_openqasm", None)
    comprobar_si_se_recibe_circuito(circuito_api, circuito_openqasm)
    print("circuito_api: ", circuito_api)
    print("circuito_openqasm: ", circuito_openqasm)
    # ? ***********************************************

    # ? ***********************************************
    bucket_s3 = contenido.get("bucket_s3", "tfg-ignacio-2023")
    bucket_s3 = "amazon-braket-"+bucket_s3
    comprobar_nombre_bucket(bucket_s3)
    print("bucket_s3: ", bucket_s3)
    # ? ***********************************************

    # Creamos la lista con los hilos que se van a ejecutar.
    hilos = []

    # Creamos la lista "lista" que es una lista auxiliar con los hilos que devuelven los diferentes main, y una vez que los tenemos los mandamos a la lista "hilos".
    lista = []

    lista = organizar_main("aws", maquinas_aws, tipo, shots, qbits, numero_buscado_recursos,
                           circuito_api, circuito_openqasm, shots_maquinas_aws, bucket_s3, tipo_ejecucion, "", "", poll_timeout_seconds, poll_interval_seconds)

    for i in lista:
        hilos.append(i)

    # Empieza el start de los hilos.
    for hilo in hilos:
        hilo.start()

    # Empieza el join de los hilos.
    for hilo in hilos:
        hilo.join()

    # Aquí ya tendriamos los resultados que los almacenamos en un json para devolverlo.
    resultados = []
    for hilo in hilos:
        print("Resultados AWS")
        print(hilo.resultado)
        resultados.append(hilo.resultado)

    # Devolvemos el conjunto de json que se han generado como resultados.
    return jsonify(resultados)


# Método para recibir las llamadas GET a /execute_ibm/info
@app.route('/execute_ibm/info', methods=["get"])
def execute_load_balancer_ibm_info():
    return index_ibm("Info")


# Método para recibir las llamadas GET a /execute_ibm/show/info
@app.route('/execute_ibm/show/info', methods=["get"])
def execute_load_balancer_ibm_show_info():
    return index_show_ibm()


# Método para recibir las llamadas GET a /execute_ibm/show
@app.route('/execute_ibm/show', methods=["get"])
def execute_load_balancer_ibm_show():

    # Recogemos todos los parámetros que nos mandan mediante un json.
    contenido = request.get_json(silent=True)

    # Si no nos mandan el json, la cuenta con la que buscaremos los recursos disponibles de IBM para mostrar será la predeterminada.
    if not contenido:
        comprobar_api_token(None)
    else:
        # ? ***********************************************
        api_token = contenido.get("api_token", None)
        comprobar_api_token(api_token)
        # Comprobamos si el token introducido es válido.
        comprobar_si_el_token_es_valido()
        # ? ***********************************************

    # Aquí ya tendríamos los resultados que se devuelven como json.
    resultados = obtener_maquinas_y_simuladores_disponibles_ibm_para_mostrar()
    # Devolvemos el conjunto de json que se han generado como resultados.
    return jsonify(resultados)


# Método para recibir las llamadas GET a /execute_ibm
@app.route('/execute_ibm', methods=["get"])
def execute_load_balancer_ibm():
    # Recogemos todos los parámetros que nos mandan mediante un json.
    contenido = request.get_json(silent=True)

    # Si no nos mandan el json, se muestra los parámetros aceptados con un breve resumen de cada uno de ellos.
    if not contenido:
        abort(400, index_ibm("Error"))

    print("Llamada /execute_ibm")

    # ? ***********************************************
    api_token = contenido.get("api_token", None)
    comprobar_api_token(api_token)
    # Comprobamos si el token introducido es válido.
    comprobar_si_el_token_es_valido()
    # ? ***********************************************

    # ? ***********************************************
    tipo_ejecucion = contenido.get("tipo_ejecucion", None)
    comprobar_metodo_ejecucion(tipo_ejecucion)
    print("tipo_ejecucion: ", tipo_ejecucion)
    # ? ***********************************************

    # ? ***********************************************
    if (tipo_ejecucion == "ejecucion"):
        optimization_level = contenido.get("optimization_level", 1)
    else:
        optimization_level = contenido.get("optimization_level", 3)
    resilience_level = contenido.get("resilience_level", 1)
    comprobar_optimization_level_resilience_level(
        tipo_ejecucion, optimization_level, resilience_level)
    print("optimization_level: ", optimization_level)
    print("resilience_level: ", resilience_level)
    # ? ***********************************************

    # ? ***********************************************
    maquinas_ibm = contenido.get("maquinas_ibm", None)
    shots_maquinas_ibm = contenido.get("shots_maquinas_ibm", None)
    comprobar_maquinas_y_shots(maquinas_ibm, shots_maquinas_ibm)
    print("maquinas_ibm: ", maquinas_ibm)
    print("shots_maquinas_ibm: ", shots_maquinas_ibm)
    # ? ***********************************************

    # ? ***********************************************
    tipo = contenido.get("tipo", ["SIMULATOR", "QPU"])
    comprobar_tipo_maquina_individual(
        tipo, maquinas_ibm, shots_maquinas_ibm)
    print("tipo: ", tipo)
    # ? ***********************************************

    # ? ***********************************************
    shots = contenido.get("shots", None)
    comprobar_shots_o_qbits_ambos(
        "shots", shots, maquinas_ibm, shots_maquinas_ibm)
    print("shots: ", shots)
    # ? ***********************************************

    # ? ***********************************************
    qbits = contenido.get("qbits", None)
    comprobar_shots_o_qbits_ambos(
        "qbits", qbits, maquinas_ibm, shots_maquinas_ibm)
    print("qbits: ", qbits)
    # ? ***********************************************

    # ? ***********************************************
    numero_buscado_recursos = contenido.get("numero_buscado_recursos", 1)
    comprobar_numero_buscado_recursos(
        numero_buscado_recursos, maquinas_ibm, shots_maquinas_ibm)
    print("numero_buscado_recursos: ", numero_buscado_recursos)
    # ? ***********************************************

    # ? ***********************************************
    circuito_api = contenido.get("circuito_api", None)
    circuito_openqasm = contenido.get("circuito_openqasm", None)
    comprobar_si_se_recibe_circuito(circuito_api, circuito_openqasm)
    print("circuito_api: ", circuito_api)
    print("circuito_openqasm: ", circuito_openqasm)
    # ? ***********************************************

    # Creamos la lista con los hilos que se van a ejecutar.
    hilos = []

    # Creamos la lista "lista" que es una lista auxiliar con los hilos que devuelven los diferentes main, y una vez que los tenemos los mandamos a la lista "hilos".
    lista = []

    # Si se va a ejecutar en IBM.
    lista = organizar_main("ibm", maquinas_ibm, tipo, shots, qbits, numero_buscado_recursos,
                           circuito_api, circuito_openqasm, shots_maquinas_ibm, "", tipo_ejecucion, optimization_level, resilience_level, "", "")

    for i in lista:
        hilos.append(i)

    # Empieza el start de los hilos.
    for hilo in hilos:
        hilo.start()

    # Empieza el join de los hilos.
    for hilo in hilos:
        hilo.join()

    # Aquí ya tendriamos los resultados que los almacenamos en un json para devolverlo.
    resultados = []
    for hilo in hilos:
        print("Resultados IBM")
        print(hilo.resultado)
        resultados.append(hilo.resultado)

    # Devolvemos el conjunto de json que se han generado como resultados.
    return jsonify(resultados)


# Método para recibir las llamadas GET a /execute_aws_ibm/info
@app.route('/execute_aws_ibm/info', methods=["get"])
def execute_load_balancer_aws_ibm_info():
    return index_aws_ibm("Info")


# Método para recibir las llamadas GET a /execute_aws_ibm
@app.route('/execute_aws_ibm', methods=["get"])
def execute_load_balancer_aws_ibm():

    # Recogemos todos los parámetros que nos mandan mediante un json.
    contenido = request.get_json(silent=True)

    # Si no nos mandan el json, se muestra los parámetros aceptados con un breve resumen de cada uno de ellos.
    if not contenido:
        abort(400, index_aws_ibm("Error"))

    print("Llamada /execute_aws_ibm")

    # ? ***********************************************
    # Comprobamos si las credenciales de la cuenta de aws están configuradas.
    comprobar_cuentas_aws()
    # ? ***********************************************

    # ? ***********************************************
    aws_access_key_id = contenido.get("aws_access_key_id", None)
    aws_secret_access_key = contenido.get("aws_secret_access_key", None)
    # Comprobamos primero si recibimos los dos parámetros.
    comprobar_parametros_cuenta_aws(aws_access_key_id, aws_secret_access_key)
    # Configuramos la cuenta con los nuevos parámetros recibidos.
    comprobar_si_configurar_cuenta_aws(
        aws_access_key_id, aws_secret_access_key)
    # Comprobamos si la configuración de la cuenta es válida.
    comprobar_si_la_configuracion_es_valida()
    # ? ***********************************************

    # ? ***********************************************
    api_token = contenido.get("api_token", None)
    comprobar_api_token(api_token)
    # Comprobamos si el token introducido es válido.
    comprobar_si_el_token_es_valido()
    # ? ***********************************************

    # ? ***********************************************
    tipo_ejecucion = contenido.get("tipo_ejecucion", None)
    comprobar_metodo_ejecucion(tipo_ejecucion)
    print("tipo_ejecucion: ", tipo_ejecucion)
    # ? ***********************************************

    # ? ***********************************************
    poll_timeout_seconds = contenido.get("poll_timeout_seconds", 432000)
    poll_interval_seconds = contenido.get("poll_interval_seconds", 1)
    comprobar_poll_timeout_seconds_poll_interval_seconds(
        poll_timeout_seconds, poll_interval_seconds)
    print("poll_timeout_seconds: ", poll_timeout_seconds)
    print("poll_interval_seconds: ", poll_interval_seconds)
    # ? ***********************************************

    # ? ***********************************************
    if (tipo_ejecucion == "ejecucion"):
        optimization_level = contenido.get("optimization_level", 1)
    else:
        optimization_level = contenido.get("optimization_level", 3)
    resilience_level = contenido.get("resilience_level", 1)
    comprobar_optimization_level_resilience_level(
        tipo_ejecucion, optimization_level, resilience_level)
    print("optimization_level: ", optimization_level)
    print("resilience_level: ", resilience_level)
    # ? ***********************************************

    # ? ***********************************************
    maquinas_aws = contenido.get("maquinas_aws", None)
    shots_maquinas_aws = contenido.get("shots_maquinas_aws", None)
    comprobar_maquinas_y_shots(maquinas_aws, shots_maquinas_aws)
    print("maquinas_aws: ", maquinas_aws)
    print("shots_maquinas_aws: ", shots_maquinas_aws)
    # ? ***********************************************

    # ? ***********************************************
    maquinas_ibm = contenido.get("maquinas_ibm", None)
    shots_maquinas_ibm = contenido.get("shots_maquinas_ibm", None)
    comprobar_maquinas_y_shots(maquinas_ibm, shots_maquinas_ibm)
    print("maquinas_ibm: ", maquinas_ibm)
    print("shots_maquinas_ibm: ", shots_maquinas_ibm)
    # ? ***********************************************

    # ? ***********************************************
    tipo = contenido.get("tipo", ["SIMULATOR", "QPU"])
    comprobar_tipo_maquina(
        tipo, maquinas_aws, shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm)
    print("tipo: ", tipo)
    # ? ***********************************************

    # ? ***********************************************
    shots_aws = contenido.get("shots_aws", None)
    comprobar_shots_o_qbits_de_un_proveedor(
        "shots", shots_aws, maquinas_aws, shots_maquinas_aws)
    print("shots_aws: ", shots_aws)
    # ? ***********************************************

    # ? ***********************************************
    shots_ibm = contenido.get("shots_ibm", None)
    comprobar_shots_o_qbits_de_un_proveedor(
        "shots", shots_ibm, maquinas_ibm, shots_maquinas_ibm)
    print("shots_ibm: ", shots_ibm)
    # ? ***********************************************

    # ? ***********************************************
    shots = contenido.get("shots", None)
    comprobar_shots_o_qbits("shots", shots, maquinas_aws,
                            shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm, shots_aws, shots_ibm)
    print("shots: ", shots)
    # ? ***********************************************

    shots_aws = comprobar_shots_qbits_proveedor(shots_aws, shots)
    shots_ibm = comprobar_shots_qbits_proveedor(shots_aws, shots)

    # ? ***********************************************
    qbits_aws = contenido.get("qbits_aws", None)
    comprobar_shots_o_qbits_de_un_proveedor(
        "qbits", qbits_aws, maquinas_aws, shots_maquinas_aws)
    print("qbits_aws: ", qbits_aws)
    # ? ***********************************************

    # ? ***********************************************
    qbits_ibm = contenido.get("qbits_ibm", None)
    comprobar_shots_o_qbits_de_un_proveedor(
        "qbits", qbits_ibm, maquinas_ibm, shots_maquinas_ibm)
    print("qbits_ibm: ", qbits_ibm)
    # ? ***********************************************

    # ? ***********************************************
    qbits = contenido.get("qbits", None)
    comprobar_shots_o_qbits("qbits", qbits, maquinas_aws,
                            shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm, qbits_aws, qbits_ibm)
    print("qbits: ", qbits)
    # ? ***********************************************

    qbits_aws = comprobar_shots_qbits_proveedor(qbits_aws, qbits)
    qbits_ibm = comprobar_shots_qbits_proveedor(qbits_ibm, qbits)

    # ? ***********************************************
    numero_buscado_recursos_aws = contenido.get(
        "numero_buscado_recursos_aws", None)
    comprobar_numero_buscado_recursos_aws_ibm(
        numero_buscado_recursos_aws, maquinas_aws, shots_maquinas_aws)
    print("numero_buscado_recursos_aws: ", numero_buscado_recursos_aws)
    # ? ***********************************************

    # ? ***********************************************
    numero_buscado_recursos_ibm = contenido.get(
        "numero_buscado_recursos_ibm", None)
    comprobar_numero_buscado_recursos_aws_ibm(
        numero_buscado_recursos_ibm, maquinas_ibm, shots_maquinas_ibm)
    print("numero_buscado_recursos_ibm: ", numero_buscado_recursos_ibm)
    # ? ***********************************************

    # ? ***********************************************
    numero_buscado_recursos = contenido.get(
        "numero_buscado_recursos", 1)
    comprobar_numero_buscado_recursos_por_defecto_aws_ibm(
        numero_buscado_recursos, maquinas_aws, shots_maquinas_aws, maquinas_ibm, shots_maquinas_ibm, numero_buscado_recursos_aws, numero_buscado_recursos_ibm)
    print("numero_buscado_recursos: ", numero_buscado_recursos)
    # ? ***********************************************

    numero_buscado_recursos_aws = comprobar_numero_buscado_recursos_ibm_aws(
        numero_buscado_recursos_aws, numero_buscado_recursos)
    numero_buscado_recursos_ibm = comprobar_numero_buscado_recursos_ibm_aws(
        numero_buscado_recursos_ibm, numero_buscado_recursos)

    # ? ***********************************************
    circuito_api = contenido.get("circuito_api", None)
    circuito_openqasm_aws = contenido.get("circuito_openqasm_aws", None)
    circuito_openqasm_ibm = contenido.get("circuito_openqasm_ibm", None)

    comprobar_si_se_recibe_circuito_aws_ibm(
        circuito_api, circuito_openqasm_aws, circuito_openqasm_ibm)

    print("circuito_api: ", circuito_api)
    print("circuito_openqasm_aws: ", circuito_openqasm_aws)
    print("circuito_openqasm_ibm: ", circuito_openqasm_ibm)
    # ? ***********************************************

    # ? ***********************************************
    bucket_s3 = contenido.get("bucket_s3", "tfg-ignacio-2023")
    bucket_s3 = "amazon-braket-"+bucket_s3
    comprobar_nombre_bucket(bucket_s3)
    print("bucket_s3: ", bucket_s3)
    # ? ***********************************************

    # Creamos la lista con los hilos que se van a ejecutar.
    hilos = []

    # Creamos la lista "lista" que es una lista auxiliar con los hilos que devuelven los diferentes main, y una vez que los tenemos los mandamos a la lista "hilos".
    lista = []

    # Si se va a ejecutar en tanto en AWS como en IBM.

    lista = organizar_main("aws", maquinas_aws, tipo, shots_aws, qbits_aws, numero_buscado_recursos_aws,
                           circuito_api, circuito_openqasm_aws, shots_maquinas_aws, bucket_s3, tipo_ejecucion, "", "", poll_timeout_seconds, poll_interval_seconds)

    for i in lista:
        hilos.append(i)

    lista = organizar_main("ibm", maquinas_ibm, tipo, shots_ibm, qbits_ibm, numero_buscado_recursos_ibm,
                           circuito_api, circuito_openqasm_ibm, shots_maquinas_ibm, "", tipo_ejecucion, optimization_level, resilience_level, "", "")

    for i in lista:
        hilos.append(i)

    # Empieza el start de los hilos.
    for hilo in hilos:
        hilo.start()

    # Empieza el join de los hilos.
    for hilo in hilos:
        hilo.join()

    # Aquí ya tendriamos los resultados que los almacenamos en un json para devolverlo.
    resultados = []
    for hilo in hilos:
        print("Resultados AWS e IBM")
        print(hilo.resultado)
        resultados.append(hilo.resultado)

    # Devolvemos el conjunto de json que se han generado como resultados.
    return jsonify(resultados)
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************


# **********************************************************************************************************************************************
# *Main principal*******************************************************************************************************************************
# **********************************************************************************************************************************************
if __name__ == '__main__':
    print("Ejecutando load balancer...")
    # Configuramos para que se acepten conexiones externas y escuche por el puerto 5000 que es el default.
    app.run("0.0.0.0")
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
# **********************************************************************************************************************************************
