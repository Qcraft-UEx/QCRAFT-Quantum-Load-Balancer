# Utilizar una imagen oficial de Python como imagen base
FROM python:3.9
# Establecer el directorio de trabajo
WORKDIR /app
# Copiar los archivos requeridos al directorio de trabajo
COPY . .
# Instalar los requerimientos
RUN pip install -r /app/requirements.txt
# Exponer el puerto en el que se ejecuta la aplicación
EXPOSE 5000
# Ejecutar la aplicación
CMD ["python", "main.py"]