import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from comunicacion_serial import Comunicacion
import collections
import time
# Se añade iirnotch para el filtro de rechazo de banda
from scipy.signal import butter, filtfilt, iirnotch

# --- Configuración de la apariencia ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class Grafica(ctk.CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

        # --- Configuración del filtro ---
        self.filtro_seleccionado = "Sin Filtro"
        self.b, self.a = None, None

        self.datos_arduino = Comunicacion()
        self.datos_arduino.puertos_disponibles()

        self.muestra = 2500
        self.datos = 0.0

        # --- Creación de la figura de Matplotlib ---
        self.fig, self.ax = plt.subplots(facecolor='#242424', dpi=100, figsize=(4, 2))
        self.fig.tight_layout(pad=2.0)
        plt.title("Gráfica ECG", color='white', size=12, family="Arial")
        self.ax.tick_params(direction="out", length=5, width=2, colors='white', grid_color='gray', grid_alpha=0.5)

        self.line, = self.ax.plot([], [], color='#1f77b4', marker='o', linewidth=2, markersize=1, markeredgecolor='#1f77b4')

        plt.xlim([0, 10])
        plt.ylim([-200, 1000])

        self.ax.set_facecolor('#242424')
        for spine in self.ax.spines.values():
            spine.set_color('white')

        self.datos_senal_uno = collections.deque([0] * self.muestra, maxlen=self.muestra)
        self.datos_tiempo = collections.deque([0.0] * self.muestra, maxlen=self.muestra)

        plt.xlabel('Tiempo (s)', color='white')
        self.widgets()

    def animate(self, i):
        # Bucle para procesar todos los datos acumulados en la cola
        while not self.datos_arduino.datos_recibidos.empty():
            try:
                # Obtenemos un dato de la cola con .get()
                dato_str = self.datos_arduino.datos_recibidos.get_nowait()
                
                if dato_str:
                    valor_numerico = float(dato_str)
                    tiempo_actual = time.time() - self.time_inicio

                    self.datos_tiempo.append(tiempo_actual)
                    self.datos_senal_uno.append(valor_numerico)

            except (ValueError, queue.Empty):
                # Ignorar datos que no se pueden convertir o si la cola se vacía
                continue

        # El resto del código de graficado se ejecuta una sola vez por frame
        try:
            senal_a_graficar = self.datos_senal_uno
            if self.b is not None and self.a is not None:
                if len(self.datos_senal_uno) > 3 * max(len(self.a), len(self.b)):
                    senal_a_graficar = filtfilt(self.b, self.a, self.datos_senal_uno)

            self.line.set_data(self.datos_tiempo, senal_a_graficar)
            
            ax = self.line.axes
            ventana_de_tiempo = 10
            if tiempo_actual > ventana_de_tiempo:
                ax.set_xlim(tiempo_actual - ventana_de_tiempo, tiempo_actual)

            return self.line,
        except NameError: # Pasa si no hubo datos nuevos
            return self.line,

    def init_animacion(self):
        self.line.set_data([], [])
        return self.line,

    def iniciar(self):
        self.time_inicio = time.time()
        self.ani = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_animacion, interval=20, blit=True)
        self.bt_graficar.configure(state='disabled')
        self.bt_pausar.configure(state='normal')
        self.bt_captura.configure(state='normal')
        self.canvas.draw()

    def pausar(self):
        self.ani.event_source.stop()
        self.bt_pausar.configure(state='disabled')
        self.bt_reanudar.configure(state='normal')

    def reanudar(self):
        self.ani.event_source.start()
        self.bt_pausar.configure(state='normal')
        self.bt_reanudar.configure(state='disabled')

    def captura(self):
        nombre_archivo = f'captura_ecg_{int(time.time())}.png'
        self.fig.savefig(nombre_archivo, dpi=300, facecolor='#242424', bbox_inches='tight')
        print(f"¡Gráfica guardada como '{nombre_archivo}'!")

    def widgets(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.master)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)

        grafica_frame = ctk.CTkFrame(main_frame)
        grafica_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=grafica_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

        controles_frame = ctk.CTkFrame(main_frame)
        controles_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=(5, 10), pady=10)
        
        botones_grafica_frame = ctk.CTkFrame(main_frame)
        botones_grafica_frame.grid(row=1, column=0, sticky='nsew', padx=(10,5), pady=(0,10))

        ctk.CTkLabel(controles_frame, text='Puertos COM', font=('Arial', 16, 'bold')).pack(pady=(15, 5))
        self.combobox_port = ctk.CTkComboBox(controles_frame, values=self.datos_arduino.puertos, justify='center', width=150)
        self.combobox_port.pack(pady=5)
        if self.datos_arduino.puertos:
            self.combobox_port.set(self.datos_arduino.puertos[0])

        self.bt_conectar = ctk.CTkButton(controles_frame, text='Conectar', command=self.conectar_serial, fg_color="green")
        self.bt_conectar.pack(pady=10, ipady=5, fill='x', padx=20)
        self.bt_actualizar = ctk.CTkButton(controles_frame, text='Actualizar', command=self.actualizar_puertos)
        self.bt_actualizar.pack(pady=10, ipady=5, fill='x', padx=20)
        self.bt_desconectar = ctk.CTkButton(controles_frame, text='Desconectar', command=self.desconectar_serial, state='disabled', fg_color="red")
        self.bt_desconectar.pack(pady=10, ipady=5, fill='x', padx=20)

        self.bt_graficar = ctk.CTkButton(botones_grafica_frame, text='Graficar Señal', state='disabled', command=self.iniciar)
        self.bt_graficar.pack(pady=10, padx=5, side='left', expand=True)
        self.bt_pausar = ctk.CTkButton(botones_grafica_frame, text='Pausar', state='disabled', command=self.pausar)
        self.bt_pausar.pack(pady=10, padx=5, side='left', expand=True)
        self.bt_reanudar = ctk.CTkButton(botones_grafica_frame, text='Reanudar', state='disabled', command=self.reanudar)
        self.bt_reanudar.pack(pady=10, padx=5, side='left', expand=True)
        self.bt_captura = ctk.CTkButton(botones_grafica_frame, text='Guardar Gráfica', state='disabled', command=self.captura)
        self.bt_captura.pack(pady=10, padx=5, side='left', expand=True)

        filtro_container = ctk.CTkFrame(botones_grafica_frame, fg_color="transparent")
        filtro_container.pack(pady=10, padx=5, side='left', expand=True)
        ctk.CTkLabel(filtro_container, text='Filtros ECG').pack()
        # --- Se añade la nueva opción de filtro ---
        self.filtros_disponibles = ["Sin Filtro", "Filtro Notch (50Hz)", "Pasa Bajos (50Hz)"]
        self.combobox_filtro = ctk.CTkComboBox(filtro_container, values=self.filtros_disponibles, justify='center', state='readonly', command=self.seleccionar_filtro)
        self.combobox_filtro.pack()
        self.combobox_filtro.set("Sin Filtro")

    def seleccionar_filtro(self, choice):
        self.filtro_seleccionado = choice
        fs = 250.0  # Frecuencia de muestreo en Hz
        
        if self.filtro_seleccionado == "Pasa Bajos (50Hz)":
            cutoff_freq = 50.0
            nyquist_freq = 0.5 * fs
            order = 4
            self.b, self.a = butter(order, cutoff_freq / nyquist_freq, btype='low')
            print("Filtro Pasa Bajos (50Hz) activado.")
        
        # --- Lógica para el Filtro Notch ---
        elif self.filtro_seleccionado == "Filtro Notch (50Hz)":
            f0 = 50.0  # Frecuencia a eliminar (ruido de línea eléctrica)
            Q = 30.0   # Factor de calidad (qué tan estrecha es la banda de rechazo)
            self.b, self.a = iirnotch(f0, Q, fs=fs)
            print("Filtro Notch (50Hz) activado.")
            
        else: # "Sin Filtro"
            self.b, self.a = None, None
            print("Filtros desactivados.")

    def actualizar_puertos(self):
        self.datos_arduino.puertos_disponibles()
        self.combobox_port.configure(values=self.datos_arduino.puertos)
        if self.datos_arduino.puertos:
            self.combobox_port.set(self.datos_arduino.puertos[0])

    def conectar_serial(self):
        self.bt_conectar.configure(state='disabled')
        self.bt_desconectar.configure(state='normal')
        self.bt_graficar.configure(state='normal')
        self.bt_reanudar.configure(state='disabled')
        
        self.datos_arduino.arduino.port = self.combobox_port.get()
        self.datos_arduino.conexion_serial()

    def desconectar_serial(self):
        self.bt_conectar.configure(state='normal')
        self.bt_desconectar.configure(state='disabled')
        self.bt_pausar.configure(state='disabled')
        self.bt_graficar.configure(state='disabled')
        try:
            if self.ani:
                self.ani.event_source.stop()
        except AttributeError:
            pass
        self.datos_arduino.desconectar()
        
        self.datos_senal_uno.clear()
        self.datos_tiempo.clear()
        self.datos_senal_uno.extend([0]*self.muestra)
        self.datos_tiempo.extend([0.0]*self.muestra)
        self.line.set_data(self.datos_tiempo, self.datos_senal_uno)
        plt.xlim([0, 10])
        self.canvas.draw()

if __name__ == '__main__':
    ventana = ctk.CTk()
    ventana.geometry('1280x720')
    ventana.title('Grafica Matplotlib Animacion')
    ventana.minsize(width=800, height=500)
    app = Grafica(ventana)
    ventana.mainloop()