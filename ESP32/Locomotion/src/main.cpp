#include <Arduino.h>
#include <math.h>

struct Motor {
  int in1;
  int in2;
  int pwmChannel;
};

Motor motors[4] = {
  {32, 15, 0},  // Front Left (was 33 → now 15)
  {25, 26, 1},  // Front Right
  {27, 14, 2},  // Rear Left
  {4,  16, 3}   // Rear Right
};

const int PWM_FREQ = 1000;
const int PWM_RES = 8;

const int trigPin = 12;
const int echoPin = 13;


float vx = -0.8;
float vy = -        0.4;

void setupMotors() {
  for (int i = 0; i < 4; i++) {
    pinMode(motors[i].in1, OUTPUT);
    pinMode(motors[i].in2, OUTPUT);
    ledcSetup(motors[i].pwmChannel, PWM_FREQ, PWM_RES);
    ledcAttachPin(motors[i].in1, motors[i].pwmChannel);  // Attach IN1 first
  }
}

void setMotor(int id, float speed) {
  int pwmVal = constrain(abs(speed * 255), 0, 255);

  if (speed > 0) {
    digitalWrite(motors[id].in2, LOW);
    ledcDetachPin(motors[id].in2);
    ledcAttachPin(motors[id].in1, motors[id].pwmChannel);
    ledcWrite(motors[id].pwmChannel, pwmVal);
  } else if (speed < 0) {
    digitalWrite(motors[id].in1, LOW);
    ledcDetachPin(motors[id].in1);
    ledcAttachPin(motors[id].in2, motors[id].pwmChannel);
    ledcWrite(motors[id].pwmChannel, pwmVal);
  } else {
    digitalWrite(motors[id].in1, LOW);
    digitalWrite(motors[id].in2, LOW);
    ledcWrite(motors[id].pwmChannel, 0);
  }
}

void move(float vx, float vy) {
  float speeds[4];
  speeds[0] = vy + vx;  // FL
  speeds[1] = vy - vx;  // FR
  speeds[2] = vy - vx;  // RL
  speeds[3] = vy + vx;  // RR

  float maxVal = max(max(abs(speeds[0]), abs(speeds[1])), max(abs(speeds[2]), abs(speeds[3])));
  if (maxVal > 1.0) {
    for (int i = 0; i < 4; i++) speeds[i] /= maxVal;
  }

  for (int i = 0; i < 4; i++) {
    setMotor(i, speeds[i]);
  }
}

float readDistanceCM() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // timeout at 30ms = ~5m
  float distance = duration * 0.0343 / 2;  // speed of sound in air

  return distance;
}


void setup() {
  Serial.begin(115200);
  setupMotors();
  pinMode(trigPin, OUTPUT);
pinMode(echoPin, INPUT);

}

const int stepsPerCycle = 100;
int stepIndex = 0;

void loop() {
  // Angle per step (full cycle = 2π)
  float angle = 2 * PI * stepIndex / stepsPerCycle;

  // Sinusoidal motion
  vx = sin(angle);
  vy = cos(angle);  // use sin(angle + PI/2) for smooth circular motion

  move(vx, vy);

  Serial.print("vx: ");
  Serial.print(vx, 2);
  Serial.print(" | vy: ");
  Serial.println(vy, 2);

  stepIndex = (stepIndex + 1) % stepsPerCycle;

    float distance = readDistanceCM();
  Serial.print("Distance: ");
  Serial.print(distance, 1);
  Serial.println(" cm");

  delay(300); // adjust for speed
}