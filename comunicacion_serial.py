import serial, serial.tools.list_ports
from threading import Thread, Event
import queue # Importamos la librería queue

class Comunicacion():
    def __init__(self, *args):
        super().__init__(*args)
        # Usamos una cola en lugar de StringVar para almacenar los datos
        self.datos_recibidos = queue.Queue()

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
            self.arduino.baudrate = 115200
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
                    data = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        # En lugar de .set(), usamos .put() para añadir a la cola
                        self.datos_recibidos.put(data)
                except TypeError:
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