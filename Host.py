#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import random
from traceback import format_exc
import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from pyxf import pyxf

clear = lambda: os.system("clear")
SveRijeci = []

class Host(Agent):
    class PonasanjeKA(FSMBehaviour):
        async def on_start(self):
            print("[Host] Pokrećem se!")

    class Izbornik(State):
        async def run(self):
            clear()
            print("--------------------Izbornik--------------------")
            print("[1] Ispis svih poznatih riječi")
            print("[2] Dodaj novu riječi")
            print("[3] Pokreni igru")
            print("[ctrl + c] Izlaz")
            print("------------------------------------------------")
            izbor = input("Odaberite opciju: ")
            
            if(izbor == "1"):
                print("Dostupne riječi: \n")
                self.set_next_state("IspisRijeci")
            elif(izbor == "2"):
                self.set_next_state("DodajRijec")
            elif(izbor == "3"):
                self.set_next_state("CekajPovezivanjeIgraca")
            else:
                self.set_next_state("Izbornik")

    class IspisRijeci(State):
        async def run(self):
            rijeci = self.agent.kb.query(f"rijec(X).")
            for rijec in rijeci:
                print("\t",rijec['X'].upper())
            input("\nPritisnite [Enter] za nastavak!")
            self.set_next_state("Izbornik")

    class DodajRijec(State):
        async def run(self):
            dalje = True
            while(dalje):
                novaRijec = input("Unesite novu riječ: ")
                res = input(f"Želite li dodati riječ '{novaRijec.upper()}'? [y/n]: ")
                if res in "y" or res in "Y":
                    self.agent.kb.query(f"assert(rijec({novaRijec})).")
                    print(f"Riječ '{novaRijec.upper()}' dodana!")

                res = input("\nŽelite li dodati još? [y/n]: ")
                if res not in "y" and res not in "Y":
                    dalje = False
                print()
                
            self.set_next_state("Izbornik")
    
    class CekajPovezivanjeIgraca(State):
        async def run(self):
            print("\nCekam igrača!")
            msg = await self.receive(timeout=10)
            if msg:
                print(f"Započinjem igru!")
                time.sleep(1)
                self.set_next_state("Igraj")
            else:
                print("Igrač se nije povezao!")
                time.sleep(3)
                self.set_next_state("Izbornik")
    
    class Igraj(State):
        async def run(self):
            rijeci = self.agent.kb.query(f"rijec(X).")
            for ri in rijeci:
                SveRijeci.append(ri['X'].upper())
            
            r = random.randint(0, len(SveRijeci) - 1)
            rijec = SveRijeci[r]
            print("Pogađa se riječ '",rijec,"'")
            
            linije = ""
            for i in range(len(rijec)):
                linije += "_"

            msg = spade.message.Message(
                to="posiljatelj@rec.foi.hr",
                body=f"Start{linije}",
                metadata={
                    "language": "hrvatski",
                    "performative": "inform"})
            
            await self.send(msg)
            
            j = 0
            pogodak = True

            while(pogodak):
                msg = await self.receive(timeout=100000)
                print("Slovo: ", msg.body)
                time.sleep(1)
                if(msg.metadata['performative'] == 'request'):
                    slovo = msg.body
                    if slovo in rijec:
                        for i in range(len(rijec)):
                            if(slovo in rijec[i]):
                                linije = linije[:i] + slovo + linije[i + 1:]
                    else:
                        j = j + 1

                    if rijec in linije:
                        msg = spade.message.Message(
                        to="posiljatelj@rec.foi.hr",
                        body=f"Pobjeda!{rijec}",
                        metadata={
                            "language": "hrvatski",
                            "performative": "inform"})
                        await self.send(msg)

                        print("Pobjeda igrača!")
                        pogodak = False
                    elif j == 10:
                        msg = spade.message.Message(
                        to="posiljatelj@rec.foi.hr",
                        body="Poraz!",
                        metadata={
                            "language": "hrvatski",
                            "performative": "inform"})
                        await self.send(msg)

                        print("Poraz igrača!")
                        pogodak = False
                    else:
                        msg = spade.message.Message(
                        to="posiljatelj@rec.foi.hr",
                        body=f"{linije}",
                        metadata={
                            "language": "hrvatski",
                            "performative": "request"})
                        await self.send(msg)

                        msg = spade.message.Message(
                        to="posiljatelj@rec.foi.hr",
                        body=f"{j}",
                        metadata={
                            "language": "hrvatski",
                            "performative": "request"})
                        await self.send(msg)
            input("\nPritisnite [Enter] za nastavak!")
            self.set_next_state("Izbornik")
                    
    async def setup(self):
        fsm = self.PonasanjeKA()

        fsm.add_state(name="Izbornik", state=self.Izbornik(), initial=True)
        fsm.add_state(name="CekajPovezivanjeIgraca", state=self.CekajPovezivanjeIgraca())
        fsm.add_state(name="IspisRijeci", state=self.IspisRijeci())
        fsm.add_state(name="DodajRijec", state=self.DodajRijec())
        fsm.add_state(name="Igraj", state=self.Igraj())

        fsm.add_transition(source="Izbornik", dest="CekajPovezivanjeIgraca")
        fsm.add_transition(source="Izbornik", dest="IspisRijeci")
        fsm.add_transition(source="Izbornik", dest="DodajRijec")
        fsm.add_transition(source="Izbornik", dest="Izbornik")
        fsm.add_transition(source="IspisRijeci", dest="Izbornik")
        fsm.add_transition(source="DodajRijec", dest="Izbornik")
        fsm.add_transition(source="CekajPovezivanjeIgraca", dest="Izbornik")
        fsm.add_transition(source="CekajPovezivanjeIgraca", dest="Igraj")
        fsm.add_transition(source="Igraj", dest="Igraj")
        fsm.add_transition(source="Igraj", dest="Izbornik")

        self.add_behaviour(fsm)


if __name__ == '__main__':
    host = Host("primatelj@rec.foi.hr", "tajna")
    host.start()
    host.kb = pyxf.xsb("/home/dario/software/Flora-2/XSB/bin/xsb")
    host.kb.load("HostBaza.P")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        host.stop()
    spade.quit_spade()
    
    print()