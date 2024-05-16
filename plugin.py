#!/usr/bin/env python
"""
domoticz-dts238 energy meter plugin for Domoticz.
Works with three-phase DTS238-4 ZN/S, DTS238-7 ZN/S (Modbus version)
Author: Paolo Subiaco https://github.com/CreasolTech

Requirements:
    1.python module minimalmodbus -> http://minimalmodbus.readthedocs.io/en/master/
        (pi@raspberrypi:~$ sudo pip3 install minimalmodbus)
    2.USB to RS485 adapter/converter 

TRANSLATIONS: 
    people who want to translate the module in another language can modify the DEVS and LANGS list.
    Please send a Pull request or send the plugin.py to the author tech@creasol.it . Thanks!

BUGS/Feature requests:
    any contribution is welcome!
"""

"""
<plugin key="dts238" name="DTS238 ZN/S three-phase energy meters, connected by serial port"  version="1.0" author="CreasolTech" externallink="https://github.com/CreasolTech/domoticz-dts238">
    <description>
        <h2>Domoticz plugin for DTS238 ZN/S three-phase energy meters (with Modbus port) - Version 1.0 </h2>
        <b>Up to 6 meters can be connected to the same bus</b>, specifying their addresses separated by comma, for example <tt>2,3,124</tt>  to read energy meters with slave address 1, 2, 3, 124.<br/><u>DO NOT CHANGE THE EXISTING SEQUENCE</u> by adding new devices between inside, but just add new device in the end of the sequence, e.g. <tt>2,3,124,6,4,5</tt><br/>
        It's possible to reprogram a meter slave address by editing the corresponding Power Factor device Description field, changing ADDR=x to ADDR=y (y between 1 and 247), then clicking on Update button<br/>
        When the first meter is connected, <b>it's strongly recommended to immediately change default address from 1 to 2 (or more)</b> to permit, in the future, to add new meters.<br/>
        For more info please check the  <a href="https://github.com/CreasolTech/domoticz-dts238">GitHub plugin page</a>
    </description>
    <params>
        <param field="SerialPort" label="Modbus Port" width="200px" required="true" default="/dev/ttyUSB0" />
        <param field="Mode1" label="Baud rate" width="40px" required="true" default="9600"  />
        <param field="Mode3" label="Poll interval">
            <options>
                <option label="2 seconds" value="2" />
                <option label="3 seconds" value="3" />
                <option label="4 seconds" value="4" />
                <option label="5 seconds" value="5" default="true" />
                <option label="10 seconds" value="10" />
                <option label="20 seconds" value="20" />
                <option label="30 seconds" value="30" />
            </options>
        </param>
        <param field="Mode2" label="Meter addresses" width="40px" required="true" default="2,3,4" />
    </params>
</plugin>

"""

import minimalmodbus    #v2.1.1
import random
import Domoticz         #tested on Python 3.9.2 in Domoticz 2021.1 and 2023.1



LANGS=[ "en", "it" ] # list of supported languages, in DEVS dict below
DEVTYPE=0
DEVSUBTYPE=1
DEVSWITCHTYPE=2
DEVOPTIONS=3
DEVIMAGE=4
DEVLANG=5  # item in the DEVS list where the first language starts 

DEVS={ #unit:     Type,Sub,swtype, Options, Image,  "en name", "it name"  ...other languages should follow  ],
            1:  [ 243,29,0,     None,                   None,   "Power/Energy total",   "Potenza/Energia totale",       ],
            2:  [ 243,29,0,     None,                   None,   "Power/Energy imported","Potenza/Energia importata",    ],
            3:  [ 243,29,4,     None,                   None,   "Power/Energy exported","Potenza/Energia esportata",    ],
            4:  [ 243,29,0,     None,                   None,   "Power/Energy net",     "Potenza/Energia netta",        ],
            5:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Active Power L1",      "Potenza attiva L1",            ],
            6:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Active Power L2",      "Potenza attiva L2",            ],
            7:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Active Power L3",      "Potenza attiva L3",            ],
            8:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Reactive Power",       "Potenza reattiva",             ],
            9:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Reactive Power L1",    "Potenza reattiva L1",          ],
           10:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Reactive Power L2",    "Potenza reattiva L2",          ],
           11:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Reactive Power L3",    "Potenza reattiva L3",          ],
           12:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Apparent Power",       "Potenza apparente",            ],
           13:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Apparent Power L1",    "Potenza apparente L1",         ],
           14:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Apparent Power L2",    "Potenza apparente L2",         ],
           15:  [ 243,29,0,     {'EnergyMeterMode':'1'}, None,  "Apparent Power L3",    "Potenza apparente L3",         ],
           16:  [ 243,31,0,     {'Custom':'1;%'},     None,   "Power Factor",         "Fattore di Potenza",           ],
           17:  [ 243,31,0,     {'Custom':'1;%'},       None,   "Power Factor L1",      "Fattore di Potenza L1",        ],
           18:  [ 243,31,0,     {'Custom':'1;%'},       None,   "Power Factor L2",      "Fattore di Potenza L2",        ],
           19:  [ 243,31,0,     {'Custom':'1;%'},       None,   "Power Factor L3",      "Fattore di Potenza L3",        ],
           20:  [ 243,8,0,      None,                   None,   "Voltage L1",           "Tensione L1",                  ],
           21:  [ 243,8,0,      None,                   None,   "Voltage L2",           "Tensione L2",                  ],
           22:  [ 243,8,0,      None,                   None,   "Voltage L3",           "Tensione L3",                  ],
           23:  [ 243,23,0,     None,                   None,   "Current L1",           "Corrente L1",                  ],
           24:  [ 243,23,0,     None,                   None,   "Current L2",           "Corrente L2",                  ],
           25:  [ 243,23,0,     None,                   None,   "Current L3",           "Corrente L3",                  ],
           26:  [ 243,31,0,     {'Custom': '1;Hz'},     None,   "Frequency",            "Frequenza",                    ],
            # ToDo: add relay device?
}

DEVSMAX=40; # max number of devices for each meter: Unit 1-40 for the first meter, 41-80 for the second meter, ....

class BasePlugin:
    def __init__(self):
        self.rs485 = ""
        self.slaves = [1]
        return

    def modbusInit(self, slave):
        self.rs485 = minimalmodbus.Instrument(Parameters["SerialPort"], int(slave))
        self.rs485.serial.baudrate = Parameters["Mode1"]
        self.rs485.serial.bytesize = 8
        self.rs485.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.rs485.serial.stopbits = 1
        self.rs485.serial.timeout = 0.5
        self.rs485.serial.exclusive = True 
        self.rs485.debug = True
        self.rs485.mode = minimalmodbus.MODE_RTU
        self.rs485.close_port_after_each_call = True

    def onStart(self):
        Domoticz.Log("Starting DTS238 plugin")
        self.pollTime=30 if Parameters['Mode3']=="" else int(Parameters['Mode3'])
        self.heartbeatNow=self.pollTime     # this is used to increase heartbeat in case of collisions
        Domoticz.Heartbeat(self.pollTime)
        self.runInterval = 1
        self._lang=Settings["Language"]
        # check if language set in domoticz exists
        if self._lang in LANGS:
            self.lang=DEVLANG+LANGS.index(self._lang)
        else:
            Domoticz.Error(f"Language {self._lang} does not exist in dict DEVS, inside the domoticz-emmeti-mirai plugin, but you can contribute adding it ;-) Thanks!")
            self._lang="en"
            self.lang=DEVLANG # default: english text

        for ss in Parameters["Mode2"].split(','):
            s=int(ss)
            if s>=2 and s<=247:
                self.slaves.append(s)

        # Check that device used to change default address exists
        if 240 not in Devices:
            Domoticz.Log("Create virtual device to change DTS238 address for meters with default address=1")
            Domoticz.Device(Name="Change address 1 -> 2-247", Description=f"DTS238 meter: change address from 1 to, ADDR=1", Unit=240, Type=243, Subtype=19, Used=1).Create()
        # Check that all devices exist, or create them
        s=0     # s used to compute unit for each energy meter: s=10, 20, 30, ... (base unit number for the current energy meter)
        for slave in self.slaves:
            if slave>1 and slave<=247:
                for i in DEVS:
                    unit=s+i
                    if unit<=250 and unit not in Devices:
                        Options=DEVS[i][DEVOPTIONS] if DEVS[i][DEVOPTIONS] else {}
                        Image=DEVS[i][DEVIMAGE] if DEVS[i][DEVIMAGE] else 0
                        Description=""
                        if i==1:
                            Description=f"Meter Addr={slave}, Total power = imported + exported"
                        elif i==7:
                            Description=f"Meter Addr={slave}, Power Factor, ADDR={slave}"
                        elif i==8:
                            Description=f"Meter Addr={slave}, Net power = imported - exported"
                        else:
                            Description=f"Meter Addr={slave}"
                        Domoticz.Log(f"Creating device Name={DEVS[i][self.lang]}, Description={Description}, Unit=unit, Type={DEVS[i][DEVTYPE]}, Subtype={DEVS[i][DEVSUBTYPE]}, Switchtype={DEVS[i][DEVSWITCHTYPE]} Options={Options}, Image={Image}")
                        Domoticz.Device(Name=DEVS[i][self.lang], Description=Description, Unit=unit, Type=DEVS[i][DEVTYPE], Subtype=DEVS[i][DEVSUBTYPE], Switchtype=DEVS[i][DEVSWITCHTYPE], Image=Image, Used=1).Create()
                        if Options!={}: # Init device and set options for kWh with EnergyMeterType=1
                            if DEVS[i][DEVSUBTYPE]==29: # kWh
                                Devices[unit].Update(0, "0;0")
                                Devices[unit].Update(0, "0;0", Options=Options)
                            else:

                                Devices[unit].Update(0, "0", Options=Options)
                s+=DEVSMAX


    def onStop(self):
        Domoticz.Log("Stopping DTS238 plugin")

    def onHeartbeat(self):
        s=0
        for slave in self.slaves:
            # read all registers in one shot
            if slave>1 and slave<=247:
                try:
                    self.modbusInit(slave)
                    # Read data from energy meter
                    registerEnergy=self.rs485.read_registers(0, 2, 3) # Read  registers from 0 to 8, using function code 3
                    register= self.rs485.read_registers(8, 10, 3) # Read  registers from 8 to 0x11, using function code 3
                    register2=self.rs485.read_registers(0x80, 0x19, 3)  # Read registers from 0x80 to 0x98
                    self.rs485.serial.close()  #  Close that door !
                except:
                    Domoticz.Error(f"Error reading Modbus registers from device {slave}")
                    self.heartbeatNow+=random.randint(1,5)    # manage collisions, increasing heartbeat once
                    Domoticz.Heartbeat(self.heartbeatNow)
                else:
                    if self.heartbeatNow!=self.pollTime:
                        self.heartbeatNow=self.pollTime     # restore normal heartbeat time, as defined in the plugin configuration
                        Domoticz.Heartbeat(self.heartbeatNow)
                    voltage1=register2[0]/10                        # V
                    voltage2=register2[1]/10                        # V
                    voltage3=register2[2]/10                        # V
                    current1=register2[3]/100                       # A
                    current2=register2[4]/100                       # A
                    current3=register2[5]/100                       # A
                    # active power
                    power=(register2[6]<<16)+register2[7]           # W signed
                    if power>=0x80000000: 
                        power-=0x100000000
                        powerImp=0
                        powerExp=0-power
                    else:
                        powerImp=power
                        powerExp=0
                    power1=register2[0x08]                          # W signed
                    if power1>=0x8000: power1=0x10000-power1
                    power2=register2[0x09]                          # W signed
                    if power2>=0x8000: power2=0x10000-power2
                    power3=register2[0x0a]                          # W signed
                    if power2>=0x8000: power3=0x10000-power3

                    #reactive power
                    rpower=(register2[0x0b]<<16)+register2[0x0c]           # W signed
                    if rpower>=0x80000000: rpower-=0x100000000
                    rpower1=register2[0x0d]                          # W signed
                    if rpower1>=0x8000: rpower1=0x10000-rpower1
                    rpower2=register2[0x0e]                          # W signed
                    if rpower2>=0x8000: rpower2=0x10000-rpower2
                    rpower3=register2[0x0f]                          # W signed
                    if rpower2>=0x8000: rpower3=0x10000-rpower3

                    #apparent power
                    apower=(register2[0x10]<<16)+register2[0x11]           # W signed
                    if apower>=0x80000000: apower-=0x100000000
                    apower1=register2[0x12]                          # W signed
                    if apower1>=0x8000: apower1=0x10000-apower1
                    apower2=register2[0x13]                          # W signed
                    if apower2>=0x8000: apower2=0x10000-apower2
                    apower3=register2[0x14]                          # W signed
                    if apower2>=0x8000: apower3=0x10000-apower3

                    energy=(registerEnergy[1] + (registerEnergy[0]<<16))*10 # Wh
                    energyImp=(register[3] + (register[2]<<16))*10     # Wh
                    energyExp=(register[1] + (register[0]<<16))*10     # Wh
                    energyNet=energyImp-energyExp
                    frequency=register[9]/100                       # Hz

                    pf=register2[0x15]/10                               # %
                    pf1=register2[0x16]/10                               # %
                    pf2=register2[0x17]/10                               # %
                    pf3=register2[0x18]/10                               # %

                    Domoticz.Status(f"Slave={slave}, P={power}W E={energy/1000}kWh Imp={energyImp/1000}kWh Exp={energyExp/1000}kWh f={frequency}Hz PF={pf}%")
                    Domoticz.Status(f"Slave={slave}, L1: {power1}W {rpower1}VAR {apower1}VA {current1}A {voltage1}V PF={pf1}%")
                    Domoticz.Status(f"Slave={slave}, L2: {power2}W {rpower2}VAR {apower2}VA {current2}A {voltage2}V PF={pf2}%")
                    Domoticz.Status(f"Slave={slave}, L3: {power3}W {rpower3}VAR {apower3}VA {current3}A {voltage3}V PF={pf3}%")
                    self.updateDevice(s+1, f"{power};{energy}")          # imported+exported energy
                    self.updateDevice(s+2, f"{powerImp};{energyImp}")    # imported power/energy
                    self.updateDevice(s+3, f"{powerExp};{energyExp}")    # exported power/energy
                    self.updateDevice(s+4, f"{power};{energyNet}")       # Net energy = imported energy - exported energy.  power=signed energy (negative if exported)
                    self.updateDevice2(s+5, power1)
                    self.updateDevice2(s+6, power2)
                    self.updateDevice2(s+7, power3)
                    self.updateDevice2(s+8, rpower)
                    self.updateDevice2(s+9, rpower1)
                    self.updateDevice2(s+10, rpower2)
                    self.updateDevice2(s+11, rpower3)
                    self.updateDevice2(s+12, apower)
                    self.updateDevice2(s+13, apower1)
                    self.updateDevice2(s+14, apower2)
                    self.updateDevice2(s+15, apower3)
                    self.updateDevice(s+16, pf)
                    self.updateDevice(s+17, pf1)
                    self.updateDevice(s+18, pf2)
                    self.updateDevice(s+19, pf3)
                    self.updateDevice(s+20, voltage1)
                    self.updateDevice(s+21, voltage2)
                    self.updateDevice(s+22, voltage3)
                    self.updateDevice(s+23, current1)
                    self.updateDevice(s+24, current2)
                    self.updateDevice(s+25, current3)
                    self.updateDevice(s+26, frequency)
                s+=DEVSMAX    # Increment the base for each device unit

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Status(f"Command for {Devices[Unit].Name}: Unit={Unit}, Command={Command}, Level={Level}")

    def onDeviceModified(self, Unit): #called when device is modified by the domoticz frontend (e.g. when description or name was changed by the user)
        Domoticz.Status(f"Modified DTS238 device with Unit={Unit}: Description="+Devices[Unit].Description)
        if (Unit%DEVSMAX)==7:   # Power Factor device: check if Description contains ADDR=1..247
            opts=Devices[Unit].Description.split(',')
            for opt in opts:
                opt=opt.strip().upper()
                if (opt[:5]=="ADDR="):
                    par=int(float(opt[5:]))
                    slave=self.slaves[int(Unit/DEVSMAX)]
                    if par>=1 and par<=247 and par!=slave:
                        # Change Modbus slave address to this device
                        baudValue=1
                        if Parameters["Mode1"]==4800:
                            baudValue=2
                        elif Parameters["Mode1"]==2400:
                            baudValue=3
                        elif Parameters["Mode1"]==1200:
                            baudValue=4

                        try: 
                            self.modbusInit(slave)
                            self.rs485.write_registers(0x15, [ par*256+baudValue ])   # Write register 0x15 with (par<<8 | 1) where par=slave address, 1=9600bps
                            self.rs485.serial.close()  #  Close that door !
                        except:
                            Domoticz.Error(f"Error writing Modbus register 0x15 (to change slave address) to device {slave}")
                        else:
                            Domoticz.Log(f"Device with slave address {slave} successfully reprogrammed with new slave address {par}")
                            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Description=f"Power Factor,ADDR={slave}")

    def updateDevice(self, index, value):
        """Check if device value is different from "value" and update it in case"""
        svalue=str(value)
        if Devices[index].sValue != svalue:
            Domoticz.Status(f"Update Devices[{index}] {Devices[index].Name}")
            Devices[index].Update(0, svalue)

    def updateDevice2(self, index, firstvalue):
        """Check if device firstvalue is different from first value in the device,  and update it in case it's different"""
        svalue=f"{firstvalue};"
        if Devices[index].sValue.find(svalue)!=0:
            Domoticz.Status(f"Update Devices[{index}] {Devices[index].Name}")
            Devices[index].Update(0, f"{firstvalue};0")


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)

