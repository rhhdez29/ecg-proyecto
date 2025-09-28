import serial, serial.tools.list_ports
from threading import  Thread, Event
from tkinter import  StringVar

class Comunicacion():
    def __init__(self, *args):
        super().__init__(*args)
        self.datos_recibidos = StringVar()

        self.arduino = serial.Serial()
        self.arduino.timeout = 0.5

        self.baudrates = ['1200', '2400', '4800', '9600', '19200', '38400', '115200']
        self.puertos = []

        self.señal = Event()
        self.hilo = None

    def puertos_disponibles(self):
        self.puertos = [port.device for port in serial.tools.list_ports.comports()]

    def conexion_serial(self):
        try:
            self.arduino.baudrate = 9600
            self.arduino.open()
            if (self.arduino.is_open):
                self.iniciar_hilo()
                print(f'Conectado exitosamente al puerto {self.arduino.port}')
        except serial.SerialException as e:
            print(f"Error al conectar: {e}")

    def enviar_datos(self, data):
        if (self.arduino.is_open):
            self.datos = str(data) + "\n"
            self.arduino.write(self.datos.encode())
        else:
            print('Error: El puerto no está abierto.')

    def leer_datos(self):
        try:
            while(self.señal.is_set() and self.arduino.is_open):
                try:
                    # Usar errors='ignore' para evitar que un mal byte detenga todo
                    data = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    # Procesar cualquier cadena no vacía (corrige el error de un solo dígito)
                    if data:
                        self.datos_recibidos.set(data)
                except TypeError: # Ocurre a veces al cerrar el puerto
                    pass
        except serial.SerialException:
            print("Puerto desconectado o error de lectura.")

    def iniciar_hilo(self):
        self.hilo = Thread(target= self.leer_datos)
        self.hilo.daemon = True
        self.señal.set()
        self.hilo.start()

    def stop_hilo(self):
        if(self.hilo is not None):
            self.señal.clear()
            self.hilo = None
    
    def desconectar(self):
        self.arduino.close()
        self.stop_hilo()
