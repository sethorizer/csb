# Coders Strike Back Tools

## Simulator Test Suite

The test suite includes a python script and various replay files, used to validate the correctness and accuracy of a CSB simulation. Any simulator, which can be wrapped in a executable file can be tested. A basic visualization of the replay scenarios is also included. Since the new test script version also tests the accuracy of checkpoint detection, the wrapper script should run in a double loop as described below. Note that `angle` is the only value gives as floating point value. This is necessary since CodinGame continues to use exact floating point values internally and only rounds them for providing int angle values of the pods.

### Simulator Input/Output
Outer loop (until process is killed):

First line: The number `checkpointCount` of checkpoints on the map.
Next `checkpointCount` lines: 2 integers `checkpointX`, `checkpointY` for the coordinates of the checkpoint.
Next line: The number `tests` of simulation steps to run on this map.

Inner loop (runs exactly `tests` times):

One line for each of the 4 pods, represented by: 4 integers, 1 float and 3 more integers, `x`, `y` for the position, `vx`, `vy` for the speed vector, `angle` for the rotation angle in degrees (only float value), `ncpid` the number of the next checkpoint, `shield` for the engine recharge timer (goes from 0 up to 3 while shielding and decreases once per turn afterwards), `boosted` as 0/1 variable (=1 if pod has already used boosters)  

One line for each of the pods moves, given by: `tx`, `ty` the target of the pod, and `thrust` the acceleration of the pod (this is `SHIELD` or `BOOST` if the pod wants to use either)

Output for one inner loop execution:
New state for each of the 4 pods: `x`, `y`, `vx`, `vy`, `angle`, `ncpid`, `shield`, `boosted` in the same format as given above.

### Testing Script
The `src/simulator_test.py` script runs the binary and feeds it with replay data from the `data/` directory.

Specify your binary with `--binary` and choose the replays with `--replays`.
A number of options for disabling tests can be used too. Most useful for testing is `--only` for executing only specific test categories.
By default the script only shows a summary, more test details can be seen by raising the verbosity with `-v`, `-vv` and `-vvv`.
In order to see a visualization of the failed test situation, specify `--gui`. Pressing the `Enter` key will advance the view. 
See also `--help` for more details.
