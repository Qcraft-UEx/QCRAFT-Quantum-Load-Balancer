from flask import abort
from braket.aws import AwsDevice
from braket.ir.openqasm import Program
from crear_circuito_aws import *


# Método que comprueba si el aws_access_key_id y el aws_secret_access_key que tenemos es válido para hacer las consultas a AWS
def comprobar_si_la_configuracion_es_valida():
    try:
        # Obtenemos todos los recursos que actualmente están operativos.
        aws_devices = AwsDevice.get_devices(statuses=['ONLINE'])
    except:
        abort(
            400, f"Error - el aws_access_key_id y el aws_secret_access_key no son válidos.")


class Dispositivo_cuantico_aws:
    # nombre        -> Nombre del dispositivo cuántico.
    # arn           -> Arn del dispositivo cuántico.
    # tipo          -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real).
    # metodo_coste  -> Si se cobra por shots (si es una máquina cuántica real) o si se cobra por minuto (si es un simulador).
    # precio        -> Precio de ejecución en el dispositivo cuántico (por minuto si es un simulador o por shots si es una máquina cuántica real).
    # precio_total  -> (SOLO QPU) La suma del precio por cada shot por el número total de shots más el precio por ejecutar la task.
    # qbits         -> El número de qbits que tiene el dispositivo cuántico.
    def __init__(self, nombre, arn, tipo, metodo_coste, precio, precio_total, qbits):
        self.nombre = nombre
        self.arn = arn
        self.tipo = tipo
        self.metodo_coste = metodo_coste
        self.precio = precio
        self.precio_total = precio_total
        self.qbits = qbits


# Método que compruba si una serie de máquinas pasadas como paŕametro están disponibles para su ejecución y aceptan el número de shots pasados como parámetros.
# maquinas_aws          -> Diferentes dispositivos de AWS de los cuales vamos a comprobar si están disponibles para su uso.
# shots_maquinas_aws    -> Número de shots que queremos ejecutar en las máquinas anteriores.
def comprobar_recursos_aws(maquinas_aws, shots_maquinas_aws):

    # Creamos una lista vacía donde estarán todos los recursos de AWS disponibles a la hora de hacer la consulta.
    recursos = []

    # Obtenemos todos los recursos que actualmente están operativos.
    aws_devices = AwsDevice.get_devices(statuses=['ONLINE'])

    # Comprobamos que las máquinas que nos han pasado por parámetro están disponibles para su ejecución.
    for indice, maquina_a_buscar in enumerate(maquinas_aws):
        # Hasta que no la encontremos en la lista de máquinas disponibles es False.
        disponible = False
        # Recorremos los recursos disponibles actualmente para comprobar si se pueden utilizar las máquinas que nos han pasado por parámetro.
        for device in aws_devices:
            # Si encontramos la máquina que estamos buscando y la máquina está disponible guardamos sus datos.
            if (maquina_a_buscar == device.name and device.is_available):
                disponible = True

                # Si la máquina no permite ejecutar circuitos cuánticos, mostramos el error.
                if ('braket.ir.openqasm.program' not in device.properties.dict()['action']):
                    abort(
                        400, f"Error - el recurso {maquina_a_buscar} no puede ejecutar circuitos cuánticos.")

                # Tenemos que comprobar si los shots que hemos enviado los acepta la máquina.
                if (shots_maquinas_aws[indice] < device.properties.service.shotsRange[0] or shots_maquinas_aws[indice] > device.properties.service.shotsRange[1]):
                    abort(
                        400, f"Error - los shots permitidos para {device.name} están comprendidos entre ({device.properties.service.shotsRange[0]},{device.properties.service.shotsRange[1]}).")

                # Si es un simulador.
                if (device.type == "SIMULATOR"):
                    recursos.append(Dispositivo_cuantico_aws(nombre=device.name, arn=device.arn, tipo=device.type,
                                                             metodo_coste=device.properties.service.deviceCost.unit, precio=device.properties.service.deviceCost.price, precio_total=device.properties.service.deviceCost.price, qbits=device.properties.paradigm.qubitCount))
                # Si es una máquina cuántica.
                else:
                    recursos.append(Dispositivo_cuantico_aws(nombre=device.name, arn=device.arn, tipo=device.type,
                                                             metodo_coste=device.properties.service.deviceCost.unit, precio=device.properties.service.deviceCost.price, precio_total=0.30000 + device.properties.service.deviceCost.price*shots_maquinas_aws[indice], qbits=device.properties.paradigm.qubitCount))

        # Si alguna máquina no está disponible, mostramos el mensaje de error.
        if (not disponible):
            abort(
                400, f"Error - el recurso {maquina_a_buscar} no está disponible para ejecutar tareas.")

    return recursos


# Método que devuelve un JSON con los recursos que tenemos disponibles en AWS.
def obtener_maquinas_y_simuladores_disponibles_aws_para_mostrar():

    # Creamos una lista vacía donde estarán todos los recursos de AWS Braket disponibles a la hora de hacer la consulta.
    recursos = []

    # types     -> Va a ser el tipo de recurso que vamos a querer buscar, en nuestro caso ["SIMULATOR", "QPU"].
    # statuses  -> El estado que queremos que tenga nuestro dispositivo, nosotros queremos que esté "ONLINE".
    aws_braket_devices = AwsDevice.get_devices(
        types=["SIMULATOR", "QPU"], statuses=['ONLINE'])

    # Recorremos los recursos disponibles para obtener sus datos
    for device in aws_braket_devices:

        # Si el dispositivo está disponible y puede ejecutar circuitos cuánticos, guardamos los datos.
        if (device.is_available and 'braket.ir.openqasm.program' in device.properties.dict()['action']):

            resultado = {}
            resultado["proveedor"] = "aws"
            resultado["maquina"] = device.name
            resultado["arn"] = device.arn
            resultado["tipo"] = device.type
            resultado["qbits"] = device.properties.paradigm.qubitCount
            resultado["rango_shots"] = (
                1, device.properties.service.shotsRange[1])
            resultado["estado"] = "online"

            recursos.append(resultado)

    return recursos


# Método que devuelve la máquina más barata según el tipo donde queramos ejecutar la tarea, el número de shots que queramos ejecutar y el número de qbits mínimos que busquemos.
# tipo                      -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real). ['SIMULATOR', 'QPU']
# shots                     -> Número de shots que vamos a lanzar.
# qbits                     -> Número de qbits como mínimo que queremos que tenga nuestra máquina cuántica.
# numero_buscado_recursos   -> Número de recursos que buscamos que sean del tipo que pasamos por parámetro.
def obtener_maquinas_y_simuladores_disponibles_aws(tipo, shots, qbits, numero_buscado_recursos):

    # Creamos una lista vacía donde estarán todos los recursos de AWS Braket disponibles a la hora de hacer la consulta.
    recursos = []

    # types     -> Lo recibimos por parámetro del método "tipo".
    # statuses  -> El estado que queremos que tenga nuestro dispositivo, nosotros queremos que esté "ONLINE".
    aws_braket_devices = AwsDevice.get_devices(types=tipo, statuses=['ONLINE'])

    # Vamos a dar por hecho que las máquinas no tiene problema en tratar los shots que queremos ejecutar
    disponibles_pero_bajando_shots = []
    shots_de_maquinas = []

    # Recorremos los recursos disponibles para obtener sus datos
    for device in aws_braket_devices:

        # Si el dispositivo está disponible, puede ejecutar circuitos cuánticos y tiene al menos los qbits que nos pasan por parámetros, guardamos los datos.
        if (device.is_available and 'braket.ir.openqasm.program' in device.properties.dict()['action'] and device.properties.paradigm.qubitCount >= qbits):

            # Si el dispositivo acepta los shots que hemos pasado
            if (shots >= device.properties.service.shotsRange[0] and shots <= device.properties.service.shotsRange[1]):

                # Si es un simulador solamente tiene el coste por minuto, y se refleja en el precio_total.
                if (device.type == "SIMULATOR"):
                    recursos.append(Dispositivo_cuantico_aws(nombre=device.name, arn=device.arn, tipo=device.type,
                                                             metodo_coste=device.properties.service.deviceCost.unit, precio=device.properties.service.deviceCost.price, precio_total=device.properties.service.deviceCost.price, qbits=device.properties.paradigm.qubitCount))

                # Si es una QPU tiene el coste por shot y el coste por lanzar la task de 0.30000$, y se refleja en el precio_total.
                else:
                    recursos.append(Dispositivo_cuantico_aws(nombre=device.name, arn=device.arn, tipo=device.type,
                                                             metodo_coste=device.properties.service.deviceCost.unit, precio=device.properties.service.deviceCost.price, precio_total=0.30000 + device.properties.service.deviceCost.price*shots, qbits=device.properties.paradigm.qubitCount))

            # Hay máquinas disponibles, pero no aceptan tantos shots como queremos ejecutar.
            else:
                disponibles_pero_bajando_shots.append(device.name)
                shots_de_maquinas.append(
                    (device.properties.service.shotsRange[0], device.properties.service.shotsRange[1]))

    if (len(disponibles_pero_bajando_shots) > 0) and (len(recursos) < numero_buscado_recursos) and (len(recursos) + len(disponibles_pero_bajando_shots) >= numero_buscado_recursos):
        abort(400,
              f"Error - habría que bajar el número de shots para poder ejecutar en éstas máquinas {disponibles_pero_bajando_shots} para suplir el número de recursos buscados. Los shots permitidos son: {shots_de_maquinas} respectivamente.")
    else:
        if len(recursos) == 0:
            abort(400, "Error - no hay recursos disponibles para la ejecución.")
        else:
            if len(recursos) < numero_buscado_recursos:
                abort(400,
                      f"Error - no hay tantos recursos disponibles como máquinas quieres usar, actualmente hay disponibles {len(recursos) + len(disponibles_pero_bajando_shots)} recursos.")

    return recursos


# Método que devuelve la máquina más barata según el tipo donde queramos ejecutar la tarea, el número de shots que queramos ejecutar y el número de qbits mínimos que busquemos.
# tipo                      -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real). ['SIMULATOR', 'QPU']
# shots                     -> Número de shots que vamos a lanzar.
# qbits                     -> Número de qbits como mínimo que queremos que tenga nuestra máquina cuántica.
# numero_buscado_recursos   -> Número de recursos que buscamos que sean del tipo que pasamos por parámetro.
def recursos_recomendado_aws(tipo, shots, qbits, numero_buscado_recursos):

    # Primero obtenemos los recursos según sean QPU o SIMULATOR que estén disponibles.
    recursos = obtener_maquinas_y_simuladores_disponibles_aws(
        tipo, shots, qbits, numero_buscado_recursos)

    # De los recursos que hemos obtenido tenemos que ver cuáles son los más baratos que podemos utilizar.
    recursos_ordenadas_precio = sorted(
        recursos, key=lambda recursos: recursos.precio_total)

    # Devolvemos dichos recursos.
    return recursos_ordenadas_precio[0:numero_buscado_recursos]


# Método que recibe todos los parámetros necesarios para ejecutar un servicio cuántico en aws.
# arn_device            -> ARN (identificador único) del recurso donde vamos a ejecutar el servicio cuántico.
# circuito              -> Circuito que vamos a ejecutar en el recurso especificado.
# tipo_circuito         -> Si el circuito va a venir en una url o mediante formato OPENQASM.
# shots_ejecutar        -> Número de shots que vamos a ejecutar en el recurso especificado.
# bucket_s3             -> Nombre del bucket que vamos a usar para guardar el resultado de la ejecución del circuito en el simulador o máquina cuántica.
# tipo_ejecucion        -> Si queremos obtener el resultado de la ejecución o la probabilidad de cada resultado.
# poll_timeout_seconds  -> El tiempo de espera de sondeo para la tarea de AWS (por defecto 432000 = 5 días)
# poll_interval_seconds -> El intervalo de sondeo para la tarea de AWS (por defecto a 1 segundo)
def ejecutar_servicio_cuantico_aws(arn_device, circuito, tipo_circuito, shots_ejecutar, bucket_s3, tipo_ejecucion, poll_timeout_seconds, poll_interval_seconds):
    # Obtenemos la máquina donde vamos a ejecutar el servicio cuántico.
    device = AwsDevice(arn_device)

    # Especificamos el bucket que vamos a usar para guardar el resultado de la ejecución, y la carpeta donde va a estar almacenado.
    s3_location = (bucket_s3, "tasks")

    # Recibimos el circuito en formato OPENQASM.
    if (tipo_circuito == "circuito_openqasm"):
        print(circuito)

        # Creamos el programa que se va a lanzar, en éste caso con el circuito que recibimos.
        program = Program(source=circuito)

        # Lanzamos la task con la tarea.
        task = device.run(
            program,
            s3_location,
            shots=shots_ejecutar,
            poll_timeout_seconds=poll_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds)

    # Recibimos el circuito mediante url.
    else:
        circuito_ejecutar = crear_circuito_aws_api(circuito)
        print(circuito)

        task = device.run(circuito_ejecutar, s3_location, shots=shots_ejecutar,
                          poll_timeout_seconds=poll_timeout_seconds, poll_interval_seconds=poll_interval_seconds)

    # Obtenemos los resultados de la ejecución.
    result = task.result()

    # Obtenemos los counts de los resultados.
    if (tipo_ejecucion == "ejecucion"):
        resultado = dict(result.measurement_counts)
        resultado["proveedor"] = "aws"
        resultado["maquina"] = arn_device
        resultado["shots"] = shots_ejecutar
    # Obtenemos la probabilidad de cada resultado.
    else:
        resultado = result.measurement_probabilities
        resultado["proveedor"] = "aws"
        resultado["maquina"] = arn_device
        resultado["shots"] = shots_ejecutar

    return resultado
