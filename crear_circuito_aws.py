from braket.circuits import Circuit, Observable
import requests


# Método para usar la api que se ocupa de transpilar el circuito de formato gráfico al lenguaje de AWS.
def crear_circuito_aws_api(circuito):

    # Url donde vamos a hacer la llamada.
    url = "http://quantumservicesdeployment.spilab.es:8081/code/aws"

    # Codificamos la url en formato utf-8.
    header_value_utf8 = circuito.encode('utf-8')

    headers = {
        'x-url': header_value_utf8}

    # Hacemos la llamada get.
    data = requests.get(url, headers=headers)

    # Si no ocurre ningún fallo.
    if data.status_code == 200:
        print("Circuito: ")
        data = data.json()['code'][:-1]
        for i in data:
            print(i)
        print()

    variables = {}

    # Ejecutamos la salida del get para crear el circuito transpilado que nos devuelve la API.
    for i in data:
        exec(i, variables)

    # Ahora el circuito que hemos transpilado lo guardamos para devolverlo.
    circuito_generado = variables['circuit']
    # print(circuito_generado)

    return circuito_generado
