#include <Arduino.h>
#include <math.h>

struct Motor {
  int in1;
  int in2;
  int pwmChannel;
};

Motor motors[4] = {
  {32, 15, 0},  // Front Left
  {25, 26, 1},  // Front Right
  {14, 27, 2},  // Rear Left
  {16,  4, 3}   // Rear Right
};

const int PWM_FREQ      = 1000;
const int PWM_RES       = 8;
const int TRIG_PIN      = 12;
const int ECHO_PIN      = 13;
const float OBSTACLE_DIST = 20.0;  // cm threshold
const float FWD_SPEED     = 0.4;   // 0…1
const float ROT_SPEED     = 0.4;   // 0…1

//---------------------------------------------------------------------------
// Initialize motor pins & PWM channels
//---------------------------------------------------------------------------
void setupMotors() {
  for (int i = 0; i < 4; i++) {
    pinMode(motors[i].in1, OUTPUT);
    pinMode(motors[i].in2, OUTPUT);
    ledcSetup(motors[i].pwmChannel, PWM_FREQ, PWM_RES);
    ledcDetachPin(motors[i].in1);
    ledcDetachPin(motors[i].in2);
  }
}

//---------------------------------------------------------------------------
// Drive one motor at “speed” (–1…0…+1)
//---------------------------------------------------------------------------
void setMotor(int id, float speed) {
  int pwmVal = constrain(abs(speed) * 255, 0, 255);
   ledcDetachPin(motors[id].in1);
  ledcDetachPin(motors[id].in2);
  if (speed > 0) {
    // forward
    digitalWrite(motors[id].in2, LOW);
    ledcAttachPin(motors[id].in1, motors[id].pwmChannel);
    ledcWrite(motors[id].pwmChannel, pwmVal);
  } 
  else if (speed < 0) {
    // backward
    digitalWrite(motors[id].in1, LOW);
    ledcAttachPin(motors[id].in2, motors[id].pwmChannel);
    ledcWrite(motors[id].pwmChannel, pwmVal);
  } 
  else {
    // stop
    ledcWrite(motors[id].pwmChannel, 0);
    digitalWrite(motors[id].in1, LOW);
    digitalWrite(motors[id].in2, LOW);
  }
}

//---------------------------------------------------------------------------
// Mecanum-style X/Y drive (vx = forward, vy = strafe)
//---------------------------------------------------------------------------
void moveXY(float vx, float vy) {
  float speeds[4] = {
    vy + vx,  // FL
    -vy + vx,  // FR
    vy - vx,  // RL
    -vy - vx   // RR
  };
  // normalize
  float maxVal = 0;
  for (int i = 0; i < 4; i++) maxVal = max(maxVal, abs(speeds[i]));
  if (maxVal > 1.0) for (int i = 0; i < 4; i++) speeds[i] /= maxVal;
  for (int i = 0; i < 4; i++) setMotor(i, speeds[i]);
}

//---------------------------------------------------------------------------
// Spin in place to the right
//---------------------------------------------------------------------------
void rotateRight(float omega) {
  setMotor(0, +omega);  // FL
  setMotor(1, +omega);  // FR
  setMotor(2, +omega);  // RL
  setMotor(3, +omega);  // RR
}

//---------------------------------------------------------------------------
// Read HC-SR04 distance in cm
//---------------------------------------------------------------------------
float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (!duration) return 999;  
  return duration * 0.0343f / 2.0f;
}

//---------------------------------------------------------------------------
// Setup
//---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  setupMotors();
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.println("Auto-drive with obstacle avoidance");
}

//---------------------------------------------------------------------------
// Main loop: go forward until obstacle, then rotate until clear
//---------------------------------------------------------------------------
float vx = 0, vy = 0;
int start = 0;
void loop() {
  if(start == 1){
    float dist = readDistanceCM();
    Serial.print("Distance: ");
    Serial.print(dist);
    Serial.println(" cm");

    if(dist <= 10.0){
      moveXY(0,0);
      delay(100);
      rotateRight(-ROT_SPEED);
      delay(100);
      moveXY(0,0);
    }
    else{
      moveXY(0, FWD_SPEED);
    }
  }
  else{
    moveXY(0, 0);
  }

  // if (dist > OBSTACLE_DIST) {
  //   // clear path: drive straight ahead
  //   moveXY(FWD_SPEED, 0); 
  // } else {
  //   // obstacle too close: stop & rotate until it's gone
  //   Serial.println("Obstacle detected → rotating...");
  //   do {
  //     rotateRight(ROT_SPEED);
  //     delay(100);            // tweak this for rotation step size
  //     dist = readDistanceCM();
  //   } while (dist <= OBSTACLE_DIST);
  //   Serial.println("Path clear → resuming forward");
  // }

  // rotateRight(ROT_SPEED);
  // moveXY(-FWD_SPEED,0);



  if (!Serial.available()) return;

  char c = Serial.read();
  

  switch (c) {
    // case 'w': vx =  0;  vy =  FWD_SPEED;           break;  // forward
    // case 's': vx = 0;  vy =  -FWD_SPEED;           break;  // backward
    // case 'a': vx =  -FWD_SPEED;          vy = 0;   break;  // strafe left
    // case 'd': vx =  FWD_SPEED;          vy =  0;   break;  // strafe right
    // case 'q': rotateRight(-ROT_SPEED); delay(100); return;  // rotate left
    case 'i': moveXY(0, FWD_SPEED); start = 0;              return;  // rotate right
    case 'o': moveXY(0,0); start = 0;              return;  // stop
    default:  return;                                    // ignore others
  }

  // Drive based on WASD
  //moveXY(vx, vy);

  // Echo command & speeds
  Serial.print("Cmd: ");
  Serial.print(c);
  Serial.print("  vx=");
  Serial.print(vx, 2);
  Serial.print("  vy=");
  Serial.println(vy, 2);
  delay(200);
}                 
                                                                              