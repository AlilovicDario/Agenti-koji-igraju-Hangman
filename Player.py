#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
import os
import re
from traceback import format_exc
import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from pyxf import pyxf

clear = lambda: os.system("clear")

class Player(Agent):
    class PonasanjeKA(FSMBehaviour):
        async def on_start(self):
            print("[Player] Pokrećem se!")

    class Izbornik(State):
        async def run(self):
            self.agent.linijePrije = ""
            self.agent.mogucaSlova = ""
            self.agent.abeceda = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            self.agent.strategija = ["AI","AOEIUMBH","AEOIUYHBCK","AEOIUYSBF","SEAOIUYH","EAIOUSY","EIAOUS","EIAOU","EIAOU","EIOAU","EIOAD","EIOAF","IEOA","IEO","IEA","IEH","IER","IEA","IEA","IE"]
            self.agent.pogodenoPrvo = False
            self.agent.pogodeno = False
            self.agent.moguceRijeci = []

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
                self.set_next_state("PocniIgru")
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
    
    class PocniIgru(State):
        async def run(self):
            msg = spade.message.Message(
                to="primatelj@rec.foi.hr",
                body="Pocetak",
                metadata={
                    "language": "hrvatski",
                    "performative": "inform"})
            
            await self.send(msg)

            self.set_next_state("Pogadaj")

    class Pogadaj(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            input()
            if(msg.metadata['performative'] == 'inform'):
                if "Start" in msg.body:
                    linije = msg.body.replace("Start","")
                    self.agent.slovo = self.probajSlovo(len(linije))
                    
                    msgs = spade.message.Message(
                        to="primatelj@rec.foi.hr",
                        body=f"{self.agent.slovo}",
                        metadata={
                            "language": "hrvatski",
                            "performative": "request"})
                    await self.send(msgs)
                    
                    self.setStage(0)
                    print("\nPokušavam slovo '", self.agent.slovo,"'\n")
                    print("\n\n\n\n",linije,"\n")
                    time.sleep(1)

                    try:
                        rijeci = self.agent.kb.query(f"rijec(X).")
                        for rijec in rijeci:
                            if len(rijec['X']) == len(linije):
                                self.agent.moguceRijeci.append(rijec['X'].upper())
                    except:
                        rijeci = []

                    self.agent.linijePrije = linije
                    self.set_next_state("Pogadaj")
                else:
                    clear()
                    if msg.body == "Poraz!":
                        self.setStage(10)
                        print("Izgubio sam!")
                    elif "Pobjeda!" in msg.body:
                        r = msg.body.replace("Pobjeda!","")
                        print("Pobijedio sam! Pogođena riječ ", r)
                        if not self.agent.kb.query(f"rijec({r.lower()})."):
                            self.agent.kb.query(f"assert(rijec({r.lower()})).")
                            print("Naučio sam novu riječ: ", r)
                    input("\nPritisnite [Enter] za nastavak!")
                    self.set_next_state("Izbornik")

            elif(msg.metadata['performative'] == 'request'):
                linije = msg.body
                msg = await self.receive(timeout=10)
                stage = int(msg.body)

                if linije not in self.agent.linijePrije:
                    pattern = "^"
                    pattern += linije.replace("_","\w{1}")
                    pattern += "$"
                    
                    regex = re.compile(pattern)

                    self.agent.pogodenoPrvo = True
                    self.agent.pogodeno = True
                    temp = []
                    for rijec in self.agent.moguceRijeci:
                        m = regex.search(rijec)
                        if m:
                            temp.append(rijec)
                    self.agent.moguceRijeci = temp
                    
                self.agent.slovo = self.probajSlovo(len(linije))

                msg = spade.message.Message(
                    to="primatelj@rec.foi.hr",
                    body=f"{self.agent.slovo}",
                    metadata={
                        "language": "hrvatski",
                        "performative": "request"})
                await self.send(msg)
            
                self.setStage(stage)
                print("\nPokušavam slovo '", self.agent.slovo,"'\n")
                print("\n\n\n\n",linije,"\n")
                time.sleep(1)

                self.agent.linijePrije = linije
                self.set_next_state("Pogadaj")
        
        def probajSlovo(self, n):
            if not self.agent.pogodenoPrvo:
                slovo = self.agent.strategija[n+1][0]
                self.agent.strategija[n+1] = self.agent.strategija[n+1].replace(slovo,"")
            else:
                r = random.randint(0, len(self.agent.abeceda) - 1)
                slovo = self.agent.abeceda[r]

                if self.agent.pogodeno:
                    self.agent.mogucaSlova = ""
                    for rijec in self.agent.moguceRijeci:
                        for s in rijec:
                            if s not in self.agent.mogucaSlova and s in self.agent.abeceda:
                                self.agent.mogucaSlova += s

                if self.agent.mogucaSlova != "":
                    while slovo not in self.agent.mogucaSlova:
                        r = random.randint(0, len(self.agent.abeceda) - 1)
                        slovo = self.agent.abeceda[r]
                    self.agent.mogucaSlova = self.agent.mogucaSlova.replace(slovo,"")

            self.agent.pogodeno = False
            self.agent.abeceda = self.agent.abeceda.replace(slovo,"")
            return slovo
        
        def setStage(self, stage):
            clear()
            if(stage == 0):
                print("\n\n\n\n\n\n\n")
            elif(stage == 1):
                print("\n\n\n\n\n\n\n_________________")
            elif(stage == 2):
                print("\n    |\n    |\n    |\n    |\n    |\n    |\n____|____________")
            elif(stage == 3):
                print("    +-------+\n    |\n    |\n    |\n    |\n    |\n    |\n____|____________")
            elif(stage == 4):
                print("    +-------+\n    |       |\n    |\n    |\n    |\n    |\n    |\n____|____________")
            elif(stage == 5):
                print("    +-------+\n    |       |\n    |       O\n    |\n    |\n    |\n    |\n____|____________")
            elif(stage == 6):
                print("    +-------+\n    |       |\n    |       O\n    |       |\n    |       |\n    |\n    |\n____|____________")
            elif(stage == 7):
                print("    +-------+\n    |       |\n    |       O\n    |      /|\n    |       |\n    |\n    |\n____|____________")
            elif(stage == 8):
                print("    +-------+\n    |       |\n    |       O\n    |      /|\\\n    |       |\n    |\n    |\n____|____________")
            elif(stage == 9):
                print("    +-------+\n    |       |\n    |       O\n    |      /|\\\n    |       |\n    |      /\n    |\n____|____________")
            elif(stage == 10):
                print("    +-------+\n    |       |\n    |       O\n    |      /|\\\n    |       |\n    |      / \\\n    |\n____|____________")

    async def setup(self):
        fsm = self.PonasanjeKA()

        fsm.add_state(name="Izbornik", state=self.Izbornik(), initial=True)
        fsm.add_state(name="PocniIgru", state=self.PocniIgru())
        fsm.add_state(name="IspisRijeci", state=self.IspisRijeci())
        fsm.add_state(name="DodajRijec", state=self.DodajRijec())
        fsm.add_state(name="Pogadaj", state=self.Pogadaj())

        fsm.add_transition(source="Izbornik", dest="PocniIgru")
        fsm.add_transition(source="Izbornik", dest="IspisRijeci")
        fsm.add_transition(source="Izbornik", dest="DodajRijec")
        fsm.add_transition(source="Izbornik", dest="Izbornik")
        fsm.add_transition(source="IspisRijeci", dest="Izbornik")
        fsm.add_transition(source="DodajRijec", dest="Izbornik")
        fsm.add_transition(source="PocniIgru", dest="Izbornik")
        fsm.add_transition(source="PocniIgru", dest="Pogadaj")
        fsm.add_transition(source="Pogadaj", dest="Izbornik")
        fsm.add_transition(source="Pogadaj", dest="Pogadaj")

        self.add_behaviour(fsm)


if __name__ == '__main__':
    player = Player("posiljatelj@rec.foi.hr", "tajna")
    player.start()
    player.kb = pyxf.xsb("/home/dario/software/Flora-2/XSB/bin/xsb")
    player.kb.load("PlayerBaza.P")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        player.stop()
    spade.quit_spade()
    
    print()