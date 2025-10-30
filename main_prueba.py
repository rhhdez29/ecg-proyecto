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
from scipy.signal import butter, filtfilt, iirnotch, lfilter
import queue

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

        # --- Variables para medir FS ---
        self.fs_contador_muestras = 0
        self.fs_tiempo_inicio = None
        self.fs_calculada = 0.0

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

                    self.fs_contador_muestras += 1

            except (ValueError, queue.Empty):
                # Ignorar datos que no se pueden convertir o si la cola se vacía
                continue

        # El resto del código de graficado se ejecuta una sola vez por frame
        try:

            # --- CÁLCULO Y ACTUALIZACIÓN DE FS ---
            if self.fs_tiempo_inicio:
                tiempo_transcurrido = time.time() - self.fs_tiempo_inicio
                if tiempo_transcurrido > 1.0: # Empezar a calcular después de 1 seg
                    self.fs_calculada = self.fs_contador_muestras / tiempo_transcurrido
                    self.label_fs.configure(text=f'{self.fs_calculada:.2f} Hz')
            # --- FIN CÁLCULO FS ---

            senal_a_graficar = self.datos_senal_uno

            # --- FIX 1: CORRECCIÓN DEL FILTRO ---
            # Comprobamos que el filtro (self.a, self.b) NO es None
            # Y que hay suficientes datos para filtrarlos
            if (self.b is not None and 
                self.a is not None and 
                len(self.datos_senal_uno) > max(len(self.a), len(self.b))):
                
                # Usamos lfilter para el procesamiento en tiempo real
                senal_a_graficar = lfilter(self.b, self.a, self.datos_senal_uno)
            
            # Si no se cumplen las condiciones, se grafica la señal cruda
            # (que ya está asignada en 'senal_a_graficar = self.datos_senal_uno')

            self.line.set_data(self.datos_tiempo, senal_a_graficar)
            
            ax = self.line.axes
            ventana_de_tiempo = 10
            
            # --- FIX 2: CORRECCIÓN DE 'tiempo_actual' ---
            # Usamos el último valor del deque, ya que 'tiempo_actual'
            # solo existe si entraron nuevos datos en este frame.
            tiempo_max_visible = self.datos_tiempo[-1] 
            
            if tiempo_max_visible > ventana_de_tiempo:
                ax.set_xlim(tiempo_max_visible - ventana_de_tiempo, tiempo_max_visible)

            return self.line,

        except IndexError: 
            # Ocurre si self.datos_tiempo está vacío (muy al inicio)
            return self.line,
        except NameError: 
            # Por si 'tiempo_max_visible' falla
            return self.line,

    def init_animacion(self):
        self.line.set_data([], [])
        return self.line,

    def iniciar(self):

        self.fs_contador_muestras = 0
        self.fs_tiempo_inicio = time.time()
        self.label_fs.configure(text='Calculando...')

        self.time_inicio = time.time()
        self.ani = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_animacion, interval=20, blit=True)
        self.bt_graficar.configure(state='disabled')
        self.bt_pausar.configure(state='normal')
        self.bt_captura.configure(state='normal')
        self.combobox_filtro.configure(state='readonly')
        self.entry_y_min.configure(state='normal')
        self.entry_y_max.configure(state='normal')
        self.bt_aplicar_y.configure(state='normal')

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
        else:
            self.combobox_port.set("Sin puertos disponibles")


        self.bt_conectar = ctk.CTkButton(controles_frame, text='Conectar', command=self.conectar_serial, fg_color="green")
        self.bt_conectar.pack(pady=10, ipady=5, fill='x', padx=20)
        self.bt_actualizar = ctk.CTkButton(controles_frame, text='Actualizar', command=self.actualizar_puertos)
        self.bt_actualizar.pack(pady=10, ipady=5, fill='x', padx=20)
        self.bt_desconectar = ctk.CTkButton(controles_frame, text='Desconectar', command=self.desconectar_serial, state='disabled', fg_color="red")
        self.bt_desconectar.pack(pady=10, ipady=5, fill='x', padx=20)

        ctk.CTkLabel(controles_frame, text='Rango Eje Y', font=('Arial', 16, 'bold')).pack(pady=(20, 5))
        
        self.entry_y_min = ctk.CTkEntry(controles_frame, placeholder_text="Y Mínimo", )
        self.entry_y_min.pack(pady=5, fill='x', padx=20)
        self.entry_y_min.configure(state='disabled')
        
        self.entry_y_max = ctk.CTkEntry(controles_frame, placeholder_text="Y Máximo")
        self.entry_y_max.pack(pady=5, fill='x', padx=20)
        self.entry_y_max.configure(state='disabled')
        
        # Botón para aplicar los cambios del eje Y
        self.bt_aplicar_y = ctk.CTkButton(controles_frame, text='Aplicar Rango Y', command=self.aplicar_rango_y)
        self.bt_aplicar_y.pack(pady=10, ipady=5, fill='x', padx=20)
        self.bt_aplicar_y.configure(state='disabled')

        # --- ETIQUETA PARA MOSTRAR FS ---
        ctk.CTkLabel(controles_frame, text='Frec. de Muestreo (fs):', font=('Arial', 14, 'bold')).pack(pady=(20, 0))
        self.label_fs = ctk.CTkLabel(controles_frame, text='N/A', font=('Arial', 14))
        self.label_fs.pack(pady=5)
        # --- FIN DE ETIQUETA FS ---

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

        # --- Se añade la nueva opción de filtro ---
        ctk.CTkLabel(filtro_container, text='Tipo de Filtro').pack()
        self.filtros_disponibles = ["Sin Filtro", "Filtro Notch", "Pasa Bajos"]
        self.combobox_filtro = ctk.CTkComboBox(filtro_container, values=self.filtros_disponibles, justify='center', state='readonly', command=self.seleccionar_filtro)
        self.combobox_filtro.pack()
        self.combobox_filtro.set("Sin Filtro")
        self.combobox_filtro.configure(state='disabled')

        # --- COMBOBOX PARA FRECUENCIAS ---
        hz_container = ctk.CTkFrame(botones_grafica_frame, fg_color="transparent")
        hz_container.pack(pady=10, padx=5, side='left', expand=True)

        ctk.CTkLabel(hz_container, text='Frecuencia de Corte').pack()
        self.hz_disponibles = ["30Hz", "40Hz", "50Hz", "60Hz", "70Hz", "100Hz"]
        self.combobox_hz = ctk.CTkComboBox(hz_container, values=self.hz_disponibles, justify='center', state='readonly', command=self.seleccionar_frecuencia)
        self.combobox_hz.pack()
        self.combobox_hz.set("50Hz")
        self.combobox_hz.configure(state='disabled')

        

    def seleccionar_filtro(self, choice):
        # Habilitar o deshabilitar el combobox de Hz según el filtro seleccionado
        if choice in ["Pasa Bajos", "Filtro Notch"]:
            self.combobox_hz.configure(state='readonly')
        else:
            self.combobox_hz.configure(state='disabled')
        self.seleccionar_frecuencia(self.combobox_hz.get())

    def seleccionar_frecuencia(self, choice):
        # Extraer el número de la cadena (ej. "50Hz" -> 50.0)
        self.cutoff_freq = float(choice.replace("Hz", ""))
        self._actualizar_filtro()

    def _actualizar_filtro(self):
        filtro_seleccionado = self.combobox_filtro.get()
        fs = 233.5

        if filtro_seleccionado == "Pasa Bajos":
            nyquist_freq = 0.5 * fs
            order = 4
            self.b, self.a = butter(order, self.cutoff_freq / nyquist_freq, btype='low')
            print(f"Filtro Pasa Bajos ({self.cutoff_freq}Hz) activado.")
        
        elif filtro_seleccionado == "Filtro Notch":
            f0 = self.cutoff_freq  # Frecuencia a eliminar
            Q = 20.0
            self.b, self.a = iirnotch(f0, Q, fs=fs)
            print(F"Filtro Notch ({self.cutoff_freq}Hz) activado.")
            
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
        self.bt_reanudar.configure(state='disabled')
        self.bt_captura.configure(state='disabled')
        self.combobox_filtro.configure(state='disabled')
        self.entry_y_min.configure(state='disabled')
        self.entry_y_max.configure(state='disabled')
        self.combobox_hz.configure(state='disabled')
        self.bt_aplicar_y.configure(state='disabled')


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
        # --- REINICIAR LABEL FS ---
        self.label_fs.configure(text='N/A')
        self.fs_tiempo_inicio = None

    def aplicar_rango_y(self):
        """
        Toma los valores de los ctk.CTkEntry para actualizar
        los límites del eje Y de la gráfica (self.ax).
        """
        try:
            y_min_str = self.entry_y_min.get()
            y_max_str = self.entry_y_max.get()

            # Obtener los límites actuales para usarlos si un campo está vacío
            current_y_min, current_y_max = self.ax.get_ylim()

            # Convertir a float solo si el string no está vacío
            y_min = float(y_min_str) if y_min_str else current_y_min
            y_max = float(y_max_str) if y_max_str else current_y_max

            # Validación simple
            if y_min >= y_max:
                print("Error: 'Y Mínimo' debe ser menor que 'Y Máximo'.")
                return # No aplicar cambios

            # Aplicar los nuevos límites al eje
            self.ax.set_ylim(y_min, y_max)
            
            # Redibujar el canvas para que los cambios sean visibles
            self.canvas.draw()
            
            print(f"Rango Y actualizado a: ({y_min}, {y_max})")
            #Limpiamos los ctkEntry
            self.entry_y_min.delete(0, 'end')
            self.entry_y_max.delete(0, 'end')


        except ValueError:
            # Mostramos una alerta si el usuario escribe texto no numérico
            print("Error: Los valores de 'Y Mínimo' y 'Y Máximo' deben ser números.")
        except Exception as e:
            print(f"Error al aplicar rango Y: {e}")

if __name__ == '__main__':
    ventana = ctk.CTk()
    ventana.geometry('1280x720')
    ventana.title('Grafica Matplotlib Animacion')
    ventana.minsize(width=800, height=500)
    app = Grafica(ventana)
    ventana.mainloop()