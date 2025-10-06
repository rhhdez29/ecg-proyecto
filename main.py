from tkinter import Tk, Frame, Button, Label, ttk, PhotoImage
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from comunicacion_serial import Comunicacion
import collections
import numpy as np
from scipy.signal import butter, filtfilt
import time

class Grafica(Frame):
    def __init__(self, master, *args):
        super().__init__(master, *args)

        # --- Configuración del filtro ---
        self.filtro_seleccionado = "Sin Filtro"
        self.b, self.a = None, None # Coeficientes del filtro

        self.datos_arduino = Comunicacion()
        self.datos_arduino.puertos_disponibles()

        self.muestra = 500 # Aumentamos el número de muestras para un mejor filtrado
        self.datos =0.0

        self.fig, ax = plt.subplots(facecolor='#ffffff',  dpi=100, figsize=(4,2))
        plt.title("Grafica ECG", color='black', size=12, family="Arial")
        ax.tick_params(direction="out", length=5, width=2, colors='black', grid_color = 'r', grid_alpha=0.5)

        self.line, =ax.plot([],[], color='black', marker='o', linewidth=2, markersize=1, markeredgecolor='g')

        plt.xlim([0, 10])
        plt.ylim([-200, 1000])

        ax.set_facecolor('#6E6D7000')
        ax.spines['bottom'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['top'].set_color('black')
        ax.spines['right'].set_color('black')

        self.datos_senal_uno = collections.deque([0]*self.muestra, maxlen=self.muestra)
        self.datos_tiempo = collections.deque([0.0]*self.muestra, maxlen=self.muestra)
       
        plt.xlabel('Tiempo (s)')
        self.widgets()

    def animate(self,i):
        dato_str = self.datos_arduino.datos_recibidos.get()
        try:
            # Solo procesar si la cadena no está vacía
            if dato_str:
                valor_numerico = float(dato_str)

                tiempo_actual = time.time() - self.time_inicio

                self.datos_tiempo.append(tiempo_actual)
                self.datos_senal_uno.append(valor_numerico)

                # Aplicar filtro si está seleccionado
                if self.b is not None and self.a is not None:
                    # filtfilt necesita suficientes datos para funcionar correctamente
                    # len(x) debe ser > 3 * max(len(a), len(b))
                    if len(self.datos_senal_uno) > 15:
                        # Aplicamos el filtro a los datos de la señal
                        senal_a_graficar = filtfilt(self.b, self.a, self.datos_senal_uno)
                    else:
                        # No hay suficientes datos, graficamos la señal cruda
                        senal_a_graficar = self.datos_senal_uno
                else:
                    # No hay filtro seleccionado, graficamos la señal cruda
                    senal_a_graficar = self.datos_senal_uno

                self.line.set_data(self.datos_tiempo, senal_a_graficar)

                ax =self.line.axes
                ventana_de_tiempo = 10
                if tiempo_actual > ventana_de_tiempo:
                    ax.set_xlim(tiempo_actual - ventana_de_tiempo, tiempo_actual)

                # AÑADE ESTA LÍNEA AL FINAL
                return self.line, # Devuelve una tupla de los artistas actualizados

        except ValueError:
            # Ignorar silenciosamente datos que no se pueden convertir a float
            pass

    # En la clase Grafica, añade esta nueva función
    def init_animacion(self):
        self.line.set_data([], [])
        return self.line, # Devuelve una tupla de los artistas a animar

    def iniciar(self,):
        self.time_inicio = time.time()
        self.ani = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_animacion ,interval=20, blit=True)
        self.bt_graficar.config(state='disabled')
        self.bt_pausar.config(state='normal')
        self.bt_captura.config(state='normal')
        self.canvas.draw()

    def pausar(self):
        self.ani.event_source.stop()
        self.bt_pausar.config(state='disabled')
        self.bt_reanudar.config(state='normal')

    def reanudar(self):
        self.ani.event_source.start()
        self.bt_pausar.config(state='normal')
        self.bt_reanudar.config(state='disabled')

    def captura(self):
        nombre_archivo = f'captura_ecg_{int(time.time())}.png'
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"¡Gráfica guardada como '{nombre_archivo}'!")

    def widgets(self):
        frame = Frame(self.master, bg='light gray', bd=2)
        frame.grid(column=0, columnspan=2, row=1, sticky='nsew')
        frame1 = Frame(self.master, bg='snow') #puertos com
        frame1.grid(column=2, row=1, sticky='nsew')
        frame2 = Frame(self.master, bg='snow') #botones graficar etc
        frame2.grid(column=0, row=0, sticky='nsew')
        frame3 = Frame(self.master, bg='snow')
        frame3.grid(column=1, row=0, sticky='nsew')
        frame4 = Frame(self.master, bg='snow')
        frame4.grid(column=2, row=0, sticky='nsew')
        


        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=5)
        self.master.columnconfigure(2, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(padx=0, pady=0, expand=True, fill='both')

        self.bt_graficar = Button(frame2, state='disabled',text='Graficar Señal', font=('Arial', 12, 'bold'), width=12, bg='white', fg='black', command=self.iniciar)
        self.bt_graficar.pack(pady=5, expand=1, side='left')
        self.bt_pausar = Button(frame2, state='disabled', text='Pausar', font=('Arial', 12, 'bold'), width=12, bg='white', fg='blue', command=self.pausar)
        self.bt_pausar.pack(pady=5, expand=1, side='left')
        self.bt_reanudar = Button(frame2, state='disabled', text='Reanudar', font=('Arial', 12, 'bold'), width=12, bg='white', fg='green', command=self.reanudar)
        self.bt_reanudar.pack(pady=5, expand=1, side='left')
        self.bt_captura = Button(frame2, state='disabled', text='Guardar Grafica', font=('Arial', 12, 'bold'), width=12, bg='white', fg='green', command=self.captura)
        self.bt_captura.pack(pady=5, expand=1, side='left')

        # Contenedor para alinear el label y el combobox de filtros verticalmente
        filtro_container = Frame(frame2, bg='snow')
        filtro_container.pack(ipady=10, pady=5, padx=5, expand=1, side='left')
        Label(filtro_container, text='Filtros ECG', bg='snow', fg='black', font=('Arial', 12, 'bold')).pack()
        self.filtros_disponibles = ["Sin Filtro", "Pasa Bajos (50Hz)"]
        self.combobox_filtro = ttk.Combobox(filtro_container, values=self.filtros_disponibles, justify='center', width=18, font=('Arial',12), state='readonly')
        self.combobox_filtro.pack()
        self.combobox_filtro.set("Sin Filtro")
        self.combobox_filtro.bind("<<ComboboxSelected>>", self.seleccionar_filtro)
        port = self.datos_arduino.puertos

        Label(frame1, text='Puertos COM', bg='white', fg='black', font=('Arial', 12, 'bold')).pack(padx=15)
        self.combobox_port = ttk.Combobox(frame1, values=port, justify='center', width=12, font='Arial')
        self.combobox_port.pack(pady=10)
        self.combobox_port.current(0)

        self.bt_conectar = Button(frame1, text='Conectar', font=('Arial', 12, 'bold'), width=12, bg='white' ,fg='green2', command=self.conectar_serial)
        self.bt_conectar.pack(pady=10)
        self.bt_actualizar = Button(frame1, text='Actualizar', font=('Arial', 12, 'bold'), width=12, bg='white', fg='orange', command=self.actualizar_puertos)
        self.bt_actualizar.pack(pady=10)
        self.bt_desconectar = Button(frame1, state='disabled', text='Desconectar', font=('Arial', 12, 'bold'), width=12, fg='red', bg='white', command=self.desconectar_serial)
        self.bt_desconectar.pack(pady=10)

    def seleccionar_filtro(self, event=None):
        self.filtro_seleccionado = self.combobox_filtro.get()
        if self.filtro_seleccionado == "Pasa Bajos (50Hz)":
            fs = 250.0  # Frecuencia de muestreo en Hz
            cutoff_freq = 50.0  # Frecuencia de corte
            nyquist_freq = 0.5 * fs
            order = 4 # Orden del filtro
            self.b, self.a = butter(order, cutoff_freq / nyquist_freq, btype='low')
            print("Filtro Pasa Bajos (50Hz) activado.")
        else: # "Sin Filtro"
            self.b, self.a = None, None
            print("Filtros desactivados.")

    def actualizar_puertos(self):
        self.datos_arduino.puertos_disponibles()
        self.combobox_port['values'] = self.datos_arduino.puertos

    def conectar_serial(self):
        self.bt_conectar.config(state='disabled')
        self.bt_desconectar.config(state='normal')
        self.bt_graficar.config(state='normal')
        self.bt_reanudar.config(state='disabled')
            

        self.datos_arduino.arduino.port = self.combobox_port.get()
        self.datos_arduino.conexion_serial()

    def desconectar_serial(self):
        self.bt_conectar.config(state='normal')
        self.bt_desconectar.config(state='disabled')
        self.bt_pausar.config(state='disabled')
        self.bt_graficar.config(state='disabled')
        try:
            self.ani.event_source.stop()
        except AttributeError:
            pass
        self.datos_arduino.desconectar()
        # Limpiamos la gráfica para la próxima conexión
        self.datos_senal_uno = collections.deque([0]*self.muestra, maxlen=self.muestra)
        self.datos_tiempo = collections.deque([0.0]*self.muestra, maxlen=self.muestra)
        self.line.set_data(self.datos_tiempo, self.datos_senal_uno)
        plt.xlim([0, 10])
        self.canvas.draw()

if __name__ == '__main__':
    ventana = Tk()
    ventana.geometry('1280x720')
    ventana.config(bg='gray30', bd=4)
    ventana.wm_title('Grafica Matplotlib Animacion')
    ventana.minsize(width=700, height=400)
    app = Grafica(ventana)
    app.mainloop()
