void setup() {
  // initialize the serial communication:
  Serial.begin(115200);
 
}
 
void loop() {
 
  // send the value of analog input 0:
  Serial.println(analogRead(A0));
  
  //Wait for a bit to keep serial data from saturating
  delay(4);
}