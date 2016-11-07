# Coders Strike Back Tools

## Simulator Test Suite

For testing a CSB simulator, the simulator has to be wrapped in a binary file to accept the following data.

### Simulator Input/Output
Input for one game turn:

Each of the `4` pods is represented by: 6 integers, `x`, `y` for the position, `vx`, `vy` for the speed vector, `angle` for the rotation angle in degrees, `shield` for the shielding timer (goes from 0 up to 3 after shielding), `boost` as 0/1 variable (=1 if pod has already used boosters)  

One move for each of the pods, given by: `tx`, `ty` the target of the pod, and `thrust` the acceleration of the pod (this is `SHIELD` or `BOOST` if the pod wants to use either)

Output for one game turn:
New state for each of the 4 pods: `x`, `y`, `vx`, `vy`, `angle`, `shield`, `boost` as above

### Testing Script
The `src/simulator_test.py` script runs the binary and feeds it with replay data from the `data/` directory.

Specify your binary with `--binary` and choose the replays with `--replays`. A number of options for disabling tests can be used too. See `--help` for details.
