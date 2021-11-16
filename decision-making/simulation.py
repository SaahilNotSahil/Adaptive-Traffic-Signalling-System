import os
import sys
import optparse
from math import ceil
from time import sleep

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci

over = []
currentGreen = 0

greenTime = 15
allRedTime = 1

phases = {
    0: {
        "green": "rrrrrrrrrrrrGGGG",
        "red": "rrrrrrrrrrrrrrrr"
    },
    1: {
        "green": "GGGGrrrrrrrrrrrr",
        "red": "rrrrrrrrrrrrrrrr"
    },
    2: {
        "green": "rrrrGGGGrrrrrrrr",
        "red": "rrrrrrrrrrrrrrrr"
    },
    3: {
        "green": "rrrrrrrrGGGGrrrr",
        "red": "rrrrrrrrrrrrrrrr"
    }
}


def getOptions():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


def run():
    global over
    global currentGreen
    global greenTime, allRedTime

    step = 0
    s = 1

    traci.trafficlight.setProgram("gneJ0", 0)

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.trafficlight.setRedYellowGreenState(
            "gneJ0", phases[currentGreen]["green"])
        traci.trafficlight.setPhaseDuration("gneJ0", greenTime)

        traci.simulationStep()

        vehicleCounts = []

        step += 1
        signals = []

        totalPhaseTime = greenTime + allRedTime

        if (step - (s - 1)) % totalPhaseTime == 0:
            traci.trafficlight.setRedYellowGreenState(
                "gneJ0", phases[currentGreen]["red"])
            traci.trafficlight.setPhaseDuration("gneJ0", allRedTime)

            s = step
            print("Step:", step)
            over.append(currentGreen)

            if len(over) == 4:
                over = over[2:]

            print("Over:", over)

            for i in range(4):
                if i not in over:
                    signals.append(i)

            print("Signals:", signals)

            for i in signals:
                vehicleCounts.append(
                    [traci.edge.getLastStepVehicleNumber(f"{i}"), i])

            vehicleCounts.sort(key=lambda x: x[0], reverse=True)
            nextGreen = vehicleCounts[0][1]

            print("Next green:", nextGreen)

            vs = traci.edge.getLastStepVehicleIDs(f"{nextGreen}")
            speeds = [traci.vehicle.getSpeed(
                v) for v in vs if traci.vehicle.getSpeed(v) != 0.0]

            laneLength = traci.lane.getLength(f"{nextGreen}_0")

            for i in range(len(speeds)):
                if speeds[i] >= 1.0:
                    speeds[i] *= 10
                else:
                    speeds[i] *= 100

            times = [ceil(laneLength / speed) for speed in speeds]

            greenTime = ceil(sum(times) / 20)
            if greenTime < 10:
                greenTime = 10
            elif greenTime > 45:
                greenTime = 45

            print("Green time:", greenTime)

            currentGreen = nextGreen

            print()

        sleep(0.5)

    traci.close()
    sys.stdout.flush()


if __name__ == "__main__":
    options = getOptions()

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    sumoCmd = [sumoBinary, "-c", "./simulation_sumo/simulation.sumocfg"]

    traci.start(sumoCmd)

    run()
