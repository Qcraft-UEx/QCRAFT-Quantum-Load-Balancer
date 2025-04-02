from flask import abort
from qiskit_ibm_provider import IBMProvider, least_busy
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Session, Options, Sampler
from crear_circuito_ibm import *


# **********************************************************
# **********************************************************
def guardar_token_QiskitRuntimeService():
    API_TOKEN = "IBM_TOKEN"

    # Una vez que tengas las credenciales de la cuenta, puede guardarlas en el disco para que no tenga que ingresarlas cada vez.
    # Las credenciales se guardan en el $HOME/.qiskit/qiskit-ibm.json archivo, donde $HOME está su directorio de inicio.

    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #!ESTO SOLO LO TENEMOS QUE HACER UNA VEZ PARA GUARDAR LA CUENTA DE IBM QUANTUM EN EL DISCO MEDIANTE EL TOKEN A NUESTRA CUENTA.
    # Save an IBM Quantum account:
    QiskitRuntimeService.save_account(
        channel="ibm_quantum", token=API_TOKEN, overwrite=True)
    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# **********************************************************
# **********************************************************


# **********************************************************
# **********************************************************
def guardar_token_QiskitRuntimeService_nuevo(API_TOKEN):

    # Una vez que tengas las credenciales de la cuenta, puede guardarlas en el disco para que no tenga que ingresarlas cada vez.
    # Las credenciales se guardan en el $HOME/.qiskit/qiskit-ibm.json archivo, donde $HOME está su directorio de inicio.

    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #!ESTO SOLO LO TENEMOS QUE HACER UNA VEZ PARA GUARDAR LA CUENTA DE IBM QUANTUM EN EL DISCO MEDIANTE EL TOKEN A NUESTRA CUENTA.
    # Save an IBM Quantum account:
    QiskitRuntimeService.save_account(
        channel="ibm_quantum", token=API_TOKEN, overwrite=True)
    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# **********************************************************
# **********************************************************


# **********************************************************
# **********************************************************
def guardar_token_IBMProvider():
    API_TOKEN = "¿¿¿¿¿"

    # Una vez que tengas las credenciales de la cuenta, puede guardarlas en el disco para que no tenga que ingresarlas cada vez.
    # Las credenciales se guardan en el $HOME/.qiskit/qiskit-ibm.json archivo, donde $HOME está su directorio de inicio.

    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #!ESTO SOLO LO TENEMOS QUE HACER UNA VEZ PARA GUARDAR LA CUENTA DE IBM QUANTUM EN EL DISCO MEDIANTE EL TOKEN A NUESTRA CUENTA.
    # Save your credentials on disk:
    # IBMProvider.save_account(token=API_TOKEN)
    #!+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# **********************************************************
# **********************************************************


# Método que comprueba si el token que tenemos es válido para hacer las consultas a IBM
def comprobar_si_el_token_es_valido():
    # Creamos el servicio de IBM Quantum.
    # Una vez que la cuenta se guarda en el disco, se puede crear una instancia del servicio sin ningún argumento, lo instanciamos en el método de cargar el token de la cuenta.
    try:
        service = QiskitRuntimeService()
    except:
        abort(
            400, f"Error - el token de IBM no es válido.")


class Dispositivo_cuantico_ibm:
    # nombre    -> Nombre del dispositivo cuántico.
    # tipo      -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real).
    # qbits     -> El número de qbits que tiene el dispositivo cuántico.
    # cola      -> Número de trabajos que tiene el dispositivo cuántico en cola.
    def __init__(self, nombre, tipo, qbits, cola):
        self.nombre = nombre
        self.tipo = tipo
        self.qbits = qbits
        self.cola = cola


# Método que compruba si una serie de máquinas pasadas como paŕametro están disponibles para su ejecución y aceptan el número de shots pasados como parámetros.
# maquinas_ibm          -> Máquinas IBM que recibimos donde tenemos que comprobar si están disponibles para ejecutar tareas.
# shots_maquinas_ibm    -> Número de shots que queremos ejecutar en las máquinas anteriores.
def comprobar_recursos_ibm(maquinas_ibm, shots_maquinas_ibm):

    # Creamos el servicio de IBM Quantum.
    # Una vez que la cuenta se guarda en el disco, se puede crear una instancia del servicio sin ningún argumento, lo instanciamos en el método de cargar el token de la cuenta.
    service = QiskitRuntimeService()

    # Creamos una lista vacía donde estarán todos los recursos de IBM Quantum disponibles a la hora de hacer la consulta.
    recursos = []

    # Obtenemos todos los recursos que actualmente están operativos.
    ibm_devices = service.backends(operational=True)

    for indice, maquina_a_buscar in enumerate(maquinas_ibm):
        # Hasta que no la encontremos en la lista de máquinas disponibles es False.
        disponible = False
        # Recorremos los recursos disponibles actualmente para comprobar si se pueden utilizar las máquinas que nos han pasado por parámetro.
        for device in ibm_devices:

            informacion = device.configuration()

            # Si la máquina esta disponible y está activa guardamos sus datos.
            # if (maquina_a_buscar == informacion.backend_name and (device.status().status_msg == "active" or device.status().status_msg == "dedicated")):
            if (maquina_a_buscar == informacion.backend_name):
                disponible = True

                shots_maximos = informacion.to_dict()["max_shots"]
                # Tenemos que comprobar si los shots que hemos enviado los acepta la máquina.
                if (shots_maquinas_ibm[indice] > shots_maximos):
                    abort(
                        400, f"Error - los shots máximos permitidos para {informacion.backend_name} son ({shots_maximos}).")

                # Si es un simulador.
                if (informacion.simulator):
                    recursos.append(Dispositivo_cuantico_ibm(nombre=informacion.backend_name, tipo="SIMULATOR", qbits=informacion.n_qubits,
                                                             cola=device.status().pending_jobs))
                # Si es una máquina cuántica.
                else:
                    recursos.append(Dispositivo_cuantico_ibm(nombre=informacion.backend_name, tipo="QPU", qbits=informacion.n_qubits,
                                                             cola=device.status().pending_jobs))
        # Si alguna máquina no está disponible, mostramos el mensaje de error.
        if (not disponible):
            abort(
                400, f"Error - el recurso {maquina_a_buscar} no está disponible para ejecutar tareas.")

    return recursos


# Método que devuelve la máquina disponible según el tipo donde queramos ejecutar la tarea, el número de shots que queramos ejecutar y el número de qbits mínimos que busquemos.
def obtener_maquinas_y_simuladores_disponibles_ibm_para_mostrar():

    # Creamos el servicio de IBM Quantum.
    # Una vez que la cuenta se guarda en el disco, se puede crear una instancia del servicio sin ningún argumento, lo instanciamos en el método de cargar el token de la cuenta.
    service = QiskitRuntimeService()

    # Creamos una lista vacía donde estarán todos los recursos de IBM Quantum disponibles a la hora de hacer la consulta.
    recursos = []

    ibm_devices = []

    ibm_devices = service.backends(operational=True)

    # Recorremos los recursos disponibles para obtener sus datos
    for device in ibm_devices:

        informacion = device.configuration()

        resultado = {}
        resultado["proveedor"] = "ibm"
        resultado["maquina"] = informacion.backend_name

        # Si es un simulador.
        if (informacion.simulator):
            resultado["tipo"] = "SIMULATOR"

        # Si es una máquina cuántica.
        else:
            resultado["tipo"] = "QPU"

        resultado["qbits"] = informacion.n_qubits
        resultado["rango_shots"] = (1, informacion.to_dict()["max_shots"])

        # Si el recurso esta ONLINE y se mostrará la información según su estado
        if (device.status().status_msg == "active"):
            resultado["estado"] = "online"
        elif (device.status().status_msg == "dedicated"):
            resultado["estado"] = "reservado"
        elif (device.status().status_msg == "internal"):
            resultado["estado"] = "mantenimiento o problema interno"
        else:
            resultado["estado"] = "otro"

        recursos.append(resultado)

    return recursos


# Método que devuelve la máquina disponible según el tipo donde queramos ejecutar la tarea, el número de shots que queramos ejecutar y el número de qbits mínimos que busquemos.
# tipo                      -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real). ['SIMULATOR', 'QPU']
# shots                     -> Número de shots que vamos a lanzar.
# qbits                     -> Número de qbits como mínimo que queremos que tenga nuestra máquina cuántica.
# numero_buscado_recursos   -> Número de recursos que buscamos que sean del tipo que pasamos por parámetro.
def obtener_maquinas_y_simuladores_disponibles(tipo, shots, qbits, numero_buscado_recursos):

    # Creamos el servicio de IBM Quantum.
    # Una vez que la cuenta se guarda en el disco, se puede crear una instancia del servicio sin ningún argumento, lo instanciamos en el método de cargar el token de la cuenta.
    service = QiskitRuntimeService()

    # Creamos una lista vacía donde estarán todos los recursos de IBM Quantum disponibles a la hora de hacer la consulta.
    recursos = []

    ibm_devices = []

    # Si el tipo es ['SIMULATOR', 'QPU'], buscamos tanto simuladores como QPU.
    if ("SIMULATOR" in tipo and "QPU" in tipo):
        ibm_devices = service.backends(operational=True, min_num_qubits=qbits)
        print(ibm_devices)
    else:
        # Si el tipo es ['SIMULATOR'], buscamos solamente Simuladores.
        if ("SIMULATOR" in tipo):
            ibm_devices = service.backends(
                simulator=True, operational=True, min_num_qubits=qbits)
            print(ibm_devices)
        else:
            # Si el tipo es ['QPU'], buscamos solamente QPU.
            if ("QPU" in tipo):
                ibm_devices = service.backends(
                    simulator=False, operational=True, min_num_qubits=qbits)
                print(ibm_devices)

    # Vamos a dar por hecho que las máquinas no tiene problema en tratar los shots que queremos ejecutar
    disponibles_pero_bajando_shots = []
    shots_de_maquinas = []
    maquinas_no_validas = []

    # Recorremos los recursos disponibles para obtener sus datos
    for device in ibm_devices:

        informacion = device.configuration()

        # Si el recurso esta ONLINE y activo se tendrá en cuenta
        if (device.status().status_msg == "active"):

            if (shots <= informacion.to_dict()["max_shots"]):

                # Si es un simulador.
                if (informacion.simulator):
                    recursos.append(Dispositivo_cuantico_ibm(nombre=informacion.backend_name, tipo="SIMULATOR", qbits=informacion.n_qubits,
                                                             cola=device.status().pending_jobs))
                # Si es una máquina cuántica.
                else:
                    recursos.append(Dispositivo_cuantico_ibm(nombre=informacion.backend_name, tipo="QPU", qbits=informacion.n_qubits,
                                                             cola=device.status().pending_jobs))
            else:
                disponibles_pero_bajando_shots.append(informacion.backend_name)
                shots_de_maquinas.append(
                    informacion.to_dict()["max_shots"])

        # El dispositivo no está activo
        else:
            maquinas_no_validas.append(device)

    for device in maquinas_no_validas:
        ibm_devices.remove(device)

    for rec in recursos:
        print("nombre: ", rec.nombre)
        print("tipo: ", rec.tipo)
        print("qbits: ", rec.qbits)
        print("cola: ", rec.cola)
        print()

    if (len(disponibles_pero_bajando_shots) > 0) and (len(recursos) < numero_buscado_recursos) and (len(recursos) + len(disponibles_pero_bajando_shots) >= numero_buscado_recursos):
        abort(400,
              f"Error - habría que bajar el número de shots para poder ejecutar en éstas máquinas {disponibles_pero_bajando_shots} para suplir el número de recursos buscados. Los shots máximos permitidos son: {shots_de_maquinas} respectivamente.")
    else:
        if len(recursos) == 0:
            abort(400, "Error - no hay recursos disponibles para la ejecución.")
        else:
            if len(recursos) < numero_buscado_recursos:
                abort(400,
                      f"Error - no hay tantos recursos disponibles como máquinas queremos usar, actualmente hay disponibles {len(recursos) + len(disponibles_pero_bajando_shots)} recursos.")

    return recursos, ibm_devices


# Método para escoger tantos recursos disponibles como busquemos e ir asignándolos según la carga de trabajo de cada uno.
# tipo                      -> Tipo de dispositivo cuántico (Si es un simulador o si es una máquina cuántica real). ['SIMULATOR', 'QPU']
# shots                     -> Número de shots que vamos a lanzar.
# qbits                     -> Número de qbits como mínimo que queremos que tenga nuestra máquina cuántica.
# numero_buscado_recursos   -> Número de recursos que buscamos que sean del tipo que pasamos por parámetro.
def recursos_recomendado_ibm(tipo, shots, qbits, numero_buscado_recursos):

    # Primero obtenemos los recursos según sean QPU, SIMULATOR o ambas que estén disponibles.
    recursos, ibm_devices = obtener_maquinas_y_simuladores_disponibles(
        tipo, shots, qbits, numero_buscado_recursos)

    recursos_ordenados = []

    # Vamos a recoger tantos recursos como hayamos puesto en numero_buscado_recursos.
    for i in range(numero_buscado_recursos):

        buscar = least_busy(ibm_devices)
        print(f"Recurso {i+1} de {numero_buscado_recursos}")

        # Aqui obtenemos los recursos que están menos cargados según los trabajos en cola en este momento.
        for recurso in recursos:
            if recurso.nombre == buscar.name:
                recursos_ordenados.append(recurso)
                print(f"Recurso añadido -> {recurso.nombre}")
                break

        # Una vez que ya lo hemos guardado, borramos el recurso que ya hemos añadido para no repetirlo.
        ibm_devices.remove(buscar)

    return recursos_ordenados


# Método para ejecutar un circuito en un backend específico con el paquete IBM provider.
# nombre            -> Nombre del dispositivo cuántico.
# circuito          -> Circuito que vamos a querer ejecutar.
# tipo_circuito     -> Si se trata de un circuito que nos llega mediante una url o mediante formato OPENQASM.
# shots_ejecutar    -> El número de shots que vamos a querer ejecutar.
def ejecutar_servicio_cuantico_ibm_provider(nombre, circuito, tipo_circuito, shots_ejecutar, optimization_level):

    provider = IBMProvider()

    # Elegimos el backend donde se va a ejecutar.
    backend = provider.get_backend(nombre)

    # Recibimos el circuito en formato OPENQASM.
    if (tipo_circuito == "circuito_openqasm"):
        circuito_ejecutar = QuantumCircuit.from_qasm_str(circuito)

    # Recibimos el circuito mediante url.
    else:
        circuito_ejecutar = crear_circuito_ibm_api(circuito)

    # Si no es un simulador, tengo que transpilar el circuito para que use las puertas propias de la máquina cuántica, ya que el hardware cambia.
    if (not backend.configuration().simulator):
        circuito_ejecutar = transpile(
            circuito_ejecutar, backend=backend, optimization_level=optimization_level)

    job = backend.run(circuito_ejecutar, shots=shots_ejecutar)
    # Obtenemos el resultado
    result = job.result()
    resultado = result.get_counts()
    # Añadimos información relativa al backend donde se ha ejecutado para una mayor orientación en el resultado.
    resultado["proveedor"] = "ibm"
    resultado["maquina"] = nombre
    resultado["shots"] = shots_ejecutar
    return resultado


# Método para ejecutar un circuito en un backend específico con el paquete IBM runtime.
# nombre                -> Nombre del dispositivo cuántico.
# circuito              -> Circuito que vamos a querer ejecutar.
# tipo_circuito         -> Si se trata de un circuito que nos llega mediante una url o mediante formato OPENQASM.
# shots_ejecutar        -> El número de shots que vamos a querer ejecutar.
# optimization_level    -> Cuánta optimización vamos a querer realizar en los circuitos. (Por defecto 3, rango de 0 a 3 ambos inclusive)
# resilience_level      -> Cuánta resiliencia vamos a tomar contra los errores. (Por defecto 1, rango de 0 a 2 ambos inclusive)
def ejecutar_servicio_cuantico_ibm_runtime(nombre, circuito, tipo_circuito, shots_ejecutar, optimization_level, resilience_level):

    # Creamos el servicio de IBM Quantum.
    # Una vez que la cuenta se guarda en el disco, se puede crear una instancia del servicio sin ningún argumento, lo instanciamos en el método de cargar el token de la cuenta.
    service = QiskitRuntimeService()

    # Elegimos el backend donde se va a ejecutar.
    backend = service.get_backend(nombre)
    # Configuramos las opciones.
    options = Options(optimization_level=optimization_level,
                      resilience_level=resilience_level)
    # Establecemos cuantos shots queremos ejecutar.
    options.execution.shots = shots_ejecutar

    # Recibimos el circuito en formato OPENQASM.
    if (tipo_circuito == "circuito_openqasm"):
        circuito_ejecutar = QuantumCircuit.from_qasm_str(circuito)

    # Recibimos el circuito mediante url.
    else:
        circuito_ejecutar = crear_circuito_ibm_api(circuito)

    # Si no es un simulador, tengo que transpilar el circuito para que use las puertas propias de la máquina cuántica, ya que el hardware cambia.
    informacion = backend.configuration()
    if (not informacion.simulator):
        circuito_ejecutar = transpile(circuito_ejecutar, backend=backend)

    with Session(service=service, backend=nombre) as session:
        sampler = Sampler(session=session, options=options)
        job = sampler.run(circuits=circuito_ejecutar)

        # Obtenemos el resultado
        result = job.result()
        resultado_aux = result.quasi_dists[0]

        # Tenemos que convertir las claves del diccionario a str porque nos la devuelve en formato int.
        resultado = {}
        for clave, valor in resultado_aux.items():
            resultado[str(clave)] = valor

        # Añadimos información relativa al backend donde se ha ejecutado para una mayor orientación en el resultado.
        resultado["proveedor"] = "ibm"
        resultado["maquina"] = nombre
        resultado["shots"] = shots_ejecutar
        return resultado


# Método que recibe todos los parámetros necesarios para ejecutar un servicio cuántico en ibm.
# nombre                -> Nombre del recurso donde vamos a ejecutar el servicio cuantico.
# circuito              -> Circuito que vamos a ejecutar en el recurso especificado.
# tipo_circuito         -> Si el circuito va a venir en una url o mediante formato OPENQASM.
# shots_ejecutar        -> Número de shots que vamos a ejecutar en el recurso especificado.
# tipo_ejecucion        -> Si queremos obtener el resultado de la ejecución o la probabilidad de cada resultado.
# optimization_level    -> Cuánta optimización vamos a querer realizar en los circuitos. (Por defecto 3, rango de 0 a 3 ambos inclusive)
# resilience_level      -> Cuánta resiliencia vamos a tomar contra los errores. (Por defecto 1, rango de 0 a 2 ambos inclusive)
def ejecutar_servicio_cuantico_ibm(nombre, circuito, tipo_circuito, shots_ejecutar, tipo_ejecucion, optimization_level, resilience_level):

    # Se ha elegido el paquete provider. (Puede ser provider o runtime.)
    if (tipo_ejecucion == "ejecucion"):
        return ejecutar_servicio_cuantico_ibm_provider(
            nombre, circuito, tipo_circuito, shots_ejecutar, optimization_level)

        # Se ha elegido runtime.
    else:
        return ejecutar_servicio_cuantico_ibm_runtime(
            nombre, circuito, tipo_circuito, shots_ejecutar, optimization_level, resilience_level)
