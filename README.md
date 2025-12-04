# **Monitor ECG Visualizador de Señales Biomédicas**

Este proyecto es una interfaz gráfica desarrollada en Python para visualizar, procesar y filtrar señales de ECG en tiempo real, adquiridas mediante un Arduino y un sensor AD8232.

## **Requisitos Previos**

* **Python 3.x** instalado en tu sistema. (Asegúrate de marcar la opción "Add Python to PATH" durante la instalación).  
* **Arduino IDE** (para cargar el código ecg_code_arduino.ino en tu placa).

## **Instalación y Configuración (Windows)**

Sigue estos pasos en tu terminal (Símbolo del sistema o PowerShell) para preparar el entorno:

### **1. Ubícate en la carpeta del proyecto**

Abre la terminal en la carpeta donde descargaste los archivos.

cd ruta\a\tu\proyecto

### **2. Crear un Entorno Virtual**

Es recomendable crear un entorno aislado para instalar las librerías sin afectar a otros proyectos. Ejecuta el siguiente comando:

python -m venv venv

### **3. Activar el Entorno Virtual**

Para activar el entorno en Windows, ejecuta:

* **En Símbolo del sistema (cmd):**  
  .\venv\Scripts\activate

* **En PowerShell:**  
  .\venv\Scripts\Activate.ps1

  *(Si te aparece un error de permisos en PowerShell, puedes intentar ejecutar primero: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process)*

Verás que aparece (venv) al principio de la línea de comandos, indicando que está activo.

### **4. Instalar las dependencias**

Una vez activo el entorno, instala todas las librerías necesarias ejecutando:

pip install -r requirements.txt

## **Ejecución del Programa**

1. Conecta tu Arduino al puerto USB.  
2. Asegúrate de tener el entorno virtual activado (debe decir (venv)).  
3. Ejecuta el archivo principal:

python main.py

## **Uso de la Interfaz**

1. En el panel derecho, despliega la lista y selecciona el **Puerto COM** de tu Arduino.  
2. Haz clic en el botón verde **Conectar**.  
3. Presiona **Graficar Señal** para ver el ECG en tiempo real.  
4. Usa los menús desplegables para probar los **Filtros Digitales** (Notch o Pasa Bajos) y limpiar la señal.