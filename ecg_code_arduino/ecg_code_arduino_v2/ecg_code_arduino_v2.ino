/*
  Código de ECG con muestreo de frecuencia VARIABLE
  controlado desde Python.
*/

// --- Variables Globales Volátiles ---
volatile bool dato_nuevo = false; 
volatile int valor_ecg = 0;

// --- Configuración del Timer (Frecuencia de CPU / Prescaler) ---
// 16,000,000 / 64 = 250,000 "ticks base" por segundo
const long TICKS_BASE = 250000;


void setup() {
  Serial.begin(115200);

  // --- Configuración del Timer1 para 250 Hz (Valor Inicial) ---
  cli(); 
  
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;

  // Valor inicial para 250 Hz: (250,000 / 250) - 1 = 999
  OCR1A = 999; 
  
  TCCR1B |= (1 << WGM12); // Modo CTC
  TCCR1B |= (1 << CS11) | (1 << CS10); // Prescaler 64
  TIMSK1 |= (1 << OCIE1A); // Habilitar interrupción
  
  sei(); 
}


// --- Rutina de Servicio de Interrupción (ISR) ---
// Esta función se sigue ejecutando automáticamente.
// La VELOCIDAD la define el valor de OCR1A.
ISR(TIMER1_COMPA_vect) {
  valor_ecg = analogRead(A0);
  dato_nuevo = true;
}


void loop() {
  // Tarea 1: Revisar si Python envió una nueva frecuencia
  if (Serial.available() > 0) {
    
    // Leemos el número que llega (ej: 200)
    long nueva_frecuencia = Serial.parseInt();
    
    // Validamos que esté en un rango lógico (ej: 50 Hz a 500 Hz)
    if (nueva_frecuencia >= 50 && nueva_frecuencia <= 500) {
      
      // Calculamos el nuevo valor de Ticks para el Timer
      // Ticks = (Ticks_Base / Frecuencia) - 1
      unsigned int nuevo_ocr_valor = (TICKS_BASE / nueva_frecuencia) - 1;
      
      // Actualizamos el registro del Timer de forma segura
      // Desactivamos interrupciones, cambiamos el valor, reactivamos
      cli();
      OCR1A = nuevo_ocr_valor;
      sei();
    }
    
    // Limpiamos el buffer de cualquier "basura" restante (como el '\n')
    while(Serial.available() > 0) {
      Serial.read();
    }
  }

  // Tarea 2: Enviar el dato si está listo
  if (dato_nuevo) {
    Serial.println(valor_ecg);
    dato_nuevo = false;
  }
}