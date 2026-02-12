# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import os
import sys

from naoqi import ALProxy

try:
    # When run as part of a package
    from ..nao_config import InitNao
except (ImportError, ValueError):
    # When run directly as a script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from nao_config import InitNao


def _fmt_pose(pose):
    try:
        return "x={:.3f} y={:.3f} th={:.3f}".format(float(pose[0]), float(pose[1]), float(pose[2]))
    except Exception:
        return str(pose)


def run_walk_forward_test(nao, x_norm=0.08, duration_s=4.0, frequency=0.25):
    """
    Isolierter Geh-Test ohne Vision:
    1) StandInit + moveInit
    2) kurzer moveTo als Sanity-Check
    3) moveToward geradeaus mit Velocity-Logs
    """

    motion = None
    posture = None
    try:
        print("Verbinde mit NAO...")
        motion = ALProxy("ALMotion", nao.ip, nao.port)
        posture = ALProxy("ALRobotPosture", nao.ip, nao.port)

        print("Setze Body-Stiffness und WakeUp...")
        motion.setStiffnesses("Body", 1.0)
        motion.wakeUp()
        posture.goToPosture("StandInit", 0.5)
        motion.moveInit()

        p0 = motion.getRobotPosition(True)
        print("Startpose:", _fmt_pose(p0))

        print("Sanity-Check moveTo(0.08, 0, 0)...")
        motion.moveTo(0.08, 0.0, 0.0)
        p1 = motion.getRobotPosition(True)
        print("Nach moveTo:", _fmt_pose(p1))

        print(
            "Starte moveToward (safe): x={:.2f} y=0.00 th=0.00 freq={:.2f} fuer {:.1f}s".format(
                x_norm, frequency, duration_s
            )
        )
        print("Nutze conservative move config: MaxStepX=0.02 MaxStepTheta=0.15 StepHeight=0.01")
        move_config = [
            ["Frequency", float(frequency)],
            ["MaxStepX", 0.02],
            ["MaxStepY", 0.08],
            ["MaxStepTheta", 0.15],
            ["StepHeight", 0.01],
            ["TorsoWx", 0.0],
            ["TorsoWy", 0.0],
        ]
        start = time.time()
        next_log = start
        ramp_s = 1.5
        while (time.time() - start) < duration_s:
            now = time.time()
            elapsed = now - start
            ramp = min(1.0, max(0.0, elapsed / ramp_s))
            cmd_x = float(x_norm) * ramp
            motion.moveToward(cmd_x, 0.0, 0.0, move_config)
            if now >= next_log:
                try:
                    v = motion.getRobotVelocity()
                    print(
                        "cmd_x={:.3f} vel: x={:.3f} y={:.3f} th={:.3f}".format(
                            cmd_x, float(v[0]), float(v[1]), float(v[2])
                        )
                    )
                except Exception as e:
                    print("vel read failed:", e)
                next_log = now + 0.5
            time.sleep(0.1)

        print("Stoppe Bewegung...")
        motion.stopMove()
        time.sleep(0.8)

        p2 = motion.getRobotPosition(True)
        print("Endpose:", _fmt_pose(p2))
        print("Geh-Test beendet.")

    except KeyboardInterrupt:
        print("\nAbgebrochen durch Benutzer.")
    finally:
        try:
            if motion is not None:
                motion.stopMove()
        except Exception:
            pass


if __name__ == "__main__":
    nao = InitNao()
    run_walk_forward_test(nao)
