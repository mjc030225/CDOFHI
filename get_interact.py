#!/usr/bin/env python3

import asyncio
from mavsdk import System
# from mavsdk import connect
# from mavsdk import start_mavlink

async def run():
    # start_mavlink()
    drone = System()
    # drone = connect(host='localhost')
    await drone.connect(system_address="udp://:14550")

    status_text_task = asyncio.ensure_future(print_status_text(drone))
     # 获取无人机的GPS信息
   
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    gps = drone.telemetry.gps_info()
 
    # 打印GPS数据
    # async for gps_info in gps:
    # print(f"Got GPS: {gps}")
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    # drone.manual_control
    await drone.action.takeoff()

    await asyncio.sleep(10)

    print("-- Landing")
    await drone.action.land()

    status_text_task.cancel()


async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
