#!/usr/bin/env python3
"""Větrák 52Pi na GPIO 14. Otáčky podle teploty, při chladnutí klesají."""

import time

import RPi.GPIO as GPIO

PIN = 14
PASMA = ((40, 35, 30), (50, 45, 50), (60, 55, 75), (70, 65, 100))
STAV = "/run/pism-vetrak"


def teplota():
    with open("/sys/class/thermal/thermal_zone0/temp", encoding="ascii") as handle:
        return int(handle.read().strip()) / 1000


def dalsi(stupne, aktualni):
    cil = 0
    for zap, vyp, procent in PASMA:
        prah = vyp if aktualni >= procent else zap
        if stupne >= prah:
            cil = procent
    return cil


def zapis(stupne, procent):
    with open(STAV, "w", encoding="ascii") as handle:
        handle.write(f"{stupne:.1f} {procent}\n")


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.OUT)
    pwm = GPIO.PWM(PIN, 100)
    aktualni = 0
    pwm.start(0)
    zapis(teplota(), 0)
    try:
        while True:
            stupne = teplota()
            cil = dalsi(stupne, aktualni)
            if cil != aktualni:
                if aktualni == 0 and cil > 0:
                    pwm.ChangeDutyCycle(100)
                    time.sleep(0.5)
                pwm.ChangeDutyCycle(cil)
                aktualni = cil
            zapis(stupne, aktualni)
            time.sleep(2)
    finally:
        pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
