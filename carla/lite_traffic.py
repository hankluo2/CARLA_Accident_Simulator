#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys

try:
    sys.path.append(
        glob.glob('../carla/dist/carla-*%d.%d-%s.egg' %
                  (sys.version_info.major, sys.version_info.minor, 'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# sys.path.append('C:\\Users\\root\\Develop\\CARLA_0.9.12\\WindowsNoEditor\\PythonAPI\\carla\\agents')

import carla
from agents.navigation.basic_agent import BasicAgent
from agents.navigation.behavior_agent import BehaviorAgent

import random
import time

from point_in_polygon import PolygonOperator as PO
from generate_traffic import location_in_region_of_interest as liroi


def main():
    actor_list = []

    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(5.0)

        world = client.get_world()
        blueprint_library = world.get_blueprint_library()

        for tl in world.get_actors().filter('traffic.traffic_light*'):
            tl.set_state(carla.TrafficLightState.Green)
            tl.freeze(True)

        bp = random.choice(blueprint_library.filter('vehicle'))

        if bp.has_attribute('color'):
            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)

        regionX1, regionX2 = [-37.3, -37.3, -55.4, -55.4], [25.1, 22.7, -55.4, -63.9]
        regionY1, regionY2 = [9.0, 124.4, 124.4, 69.2], [124.4, 140.8, 140.8, 129.3]
        region1 = PO(regionY1, regionX1)  # mind that in carla, x, y is not Cartesian, which should be converted
        region2 = PO(regionY2, regionX2)
        regions = [region1, region2]

        # camera_bp = blueprint_library.find('sensor.camera.depth')

        # cc = carla.ColorConverter.LogarithmicDepth
        # camera.listen(lambda image: image.save_to_disk('_out/%06d.png' % image.frame, cc))
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '640')
        camera_bp.set_attribute('image_size_y', '480')
        camera_bp.set_attribute('fov', '75')
        camera_bp.set_attribute('sensor_tick', '0.05')  # mind the ticking gap
        camera_transform = carla.Transform(carla.Location(x=-66, y=145, z=7), carla.Rotation(yaw=-45))
        camera = world.spawn_actor(camera_bp, camera_transform)
        # camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        # camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

        actor_list.append(camera)
        print('created %s' % camera.type_id)

        cc = carla.ColorConverter.Raw
        camera.listen(lambda image: image.save_to_disk('_out/{}.jpg'.format(image.frame), cc))

        while True:
            transform = random.choice(world.get_map().get_spawn_points())
            # print(transform.location.x)
            x, y = transform.location.y, transform.location.x
            if liroi(x, y, regions):
                print("Ego vehicle spawned at {}, {}".format(x, y))
                # vehicle = world.spawn_actor(bp, transform)

                # TODO: use agent class here to control a vehicle
                # BasicAgent = carla.agents.navigation.basic_agent.BasicAgent
                # BehaviorAgent = carla.agents.navigation.behavior_agent.BehaviorAgent
                break

        agent_dict = dict()
        for _ in range(0, 30):
            # search for a spawn point in ROI
            while True:
                transform = random.choice(world.get_map().get_spawn_points())
                # print(transform.location.x)
                x, y = transform.location.y, transform.location.x
                if liroi(x, y, regions):
                    transform.location += carla.Location(x=0.1, y=-0.1)
                    break

            bp = random.choice(blueprint_library.filter('vehicle'))

            try:
                npc = world.try_spawn_actor(bp, transform)
                actor_list.append(npc)
                # agent = BasicAgent(vehicle)
                agent = BehaviorAgent(npc, behavior='aggressive')

                destination = random.choice(world.get_map().get_spawn_points()).location
                agent.set_destination(destination)
                agent_dict[npc.id] = [npc, agent]

            except:
                pass

            if npc is not None:
                # npc.set_autopilot(True)
                print('created %s' % npc.type_id)

        for id in agent_dict:
            npc, agent = agent_dict[id]
            if agent.done():
                print("The target has been reached, stopping the simulation")
                continue
            npc.apply_control(agent.run_step())

        time.sleep(10)

    finally:

        print('destroying actors')
        camera.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        print('done.')


if __name__ == '__main__':

    main()
