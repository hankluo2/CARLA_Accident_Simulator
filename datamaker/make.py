import carla
from carla import VehicleLightState as vls
from agents import BasicAgent

import datamaker.carla_vehicle_annotator as cva
import datamaker.cva_custom as cva_custom
from datamaker.utils import exp_dir, retrieve_data
import hydra
import logging
import random
import time
import queue
from pathlib import Path


def launch(cfg):
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    cur_dir = exp_dir(save_dir=cfg.save_dir) + '\\'
    print(cur_dir)

    vehicles_list = []
    nonvehicles_list = []

    client = carla.Client(cfg.host, cfg.port)
    client.set_timeout(10.0)
    random.seed(time.time())
    synchronous_master = False

    try:
        traffic_manager = client.get_trafficmanager(cfg.tm_port)
        traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        world = client.get_world()

        print('RUNNING in synchronous mode:')
        settings = world.get_settings()
        traffic_manager.set_synchronous_mode(True)
        if not settings.synchronous_mode:
            synchronous_master = True
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = cfg.tick_gap
            world.apply_settings(settings)
        else:
            synchronous_master = False

        blueprints = world.get_blueprint_library().filter('vehicle.*')
        # ============================ filter special vehicles ==============================
        blueprints = [
            x for x in blueprints
            if int(x.get_attribute('number_of_wheels')) == 4
        ]
        blueprints = [x for x in blueprints if not x.id.endswith('microlino')]
        blueprints = [x for x in blueprints if not x.id.endswith('carlacola')]
        blueprints = [x for x in blueprints if not x.id.endswith('cybertruck')]
        blueprints = [x for x in blueprints if not x.id.endswith('t2')]
        blueprints = [x for x in blueprints if not x.id.endswith('sprinter')]
        blueprints = [x for x in blueprints if not x.id.endswith('firetruck')]
        blueprints = [x for x in blueprints if not x.id.endswith('ambulance')]

        blueprints = sorted(blueprints, key=lambda bp: bp.id)
        # ===================================================================================

        spawn_points = world.get_map().get_spawn_points()
        number_of_spawn_points = len(spawn_points)

        if cfg.number_of_vehicles < number_of_spawn_points:
            random.shuffle(spawn_points)
        elif cfg.number_of_vehicles > number_of_spawn_points:
            msg = 'Requested %d vehicles, but could only find %d spawn points'
            logging.warning(msg, cfg.number_of_vehicles,
                            number_of_spawn_points)
            cfg.number_of_vehicles = number_of_spawn_points

        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        SetVehicleLightState = carla.command.SetVehicleLightState
        FutureActor = carla.command.FutureActor

        batch = []
        for n, transform in enumerate(spawn_points):
            if n >= cfg.number_of_vehicles:
                break
            blueprint = random.choice(
                blueprints)  # randomly select a vehicle blueprint
            if blueprint.has_attribute('color'):
                color = random.choice(
                    blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
            if blueprint.has_attribute('driver_id'):
                driver_id = random.choice(
                    blueprint.get_attribute('driver_id').recommended_values)
                blueprint.set_attribute('driver_id', driver_id)
            else:
                blueprint.set_attribute('role_name', 'autopilot')

            light_state = vls.NONE
            if cfg.car_lights_on == 1:
                light_state = vls.Position | vls.LowBeam | vls.LowBeam

            # spawn the cars and set their autopilot and light state all together
            batch.append(
                SpawnActor(blueprint, transform).then(
                    SetAutopilot(FutureActor, True,
                                 traffic_manager.get_port())).then(
                                     SetVehicleLightState(
                                         FutureActor, light_state)))

        for response in client.apply_batch_sync(batch, synchronous_master):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)

        print('Created %d npc vehicles.' % len(vehicles_list))

        # ============================== set hero vehicle here!!! =====================
        # TODO: add a hero vehicle: Coding here
        danger_vid = random.choice(vehicles_list)
        # danger_vid = random.sample(vehicles_list,
        #                            int(len(vehicles_list) * cfg.hero_pct))
        for v in [danger_vid]:  # TODO: bracket [] for only one hero instance(patch)
            danger_vehicle = world.get_actor(v)
            traffic_manager.auto_lane_change(danger_vehicle, False)
            traffic_manager.ignore_lights_percentage(danger_vehicle, 100)
            traffic_manager.distance_to_leading_vehicle(danger_vehicle, 0)
            traffic_manager.vehicle_percentage_speed_difference(
                danger_vehicle, -200)
            traffic_manager.ignore_signs_percentage(danger_vehicle, 100)
            traffic_manager.ignore_vehicles_percentage(danger_vehicle, 100)
            traffic_manager.ignore_walkers_percentage(danger_vehicle, 100)
            traffic_manager.set_percentage_keep_right_rule(danger_vehicle, 100)

        # ============================= hero vehicle set ==============================
        hero = world.get_actor(danger_vid)  # for single hero car
        # =============================================================================

        # --------------
        # Spawn sensors
        # --------------
        q_list = []
        idx = 0
        tick_queue = queue.Queue()
        world.on_tick(tick_queue.put)
        q_list.append(tick_queue)
        tick_idx = idx
        idx += 1

        # Spawn RGB camera
        cam_bp = world.get_blueprint_library().find('sensor.camera.rgb')
        cam_bp.set_attribute('sensor_tick', str(cfg.tick_gap))
        cam_bp.set_attribute('image_size_x', '640')
        cam_bp.set_attribute('image_size_y', '480')
        cam_bp.set_attribute('fov', '75')
        cam_transform = carla.Transform(carla.Location(x=-35, y=7, z=6),
                                        carla.Rotation(pitch=-15, yaw=130))
        cam = world.spawn_actor(cam_bp, cam_transform)

        nonvehicles_list.append(cam)
        cam_queue = queue.Queue()
        cam.listen(cam_queue.put)
        q_list.append(cam_queue)
        cam_idx = idx
        idx = idx + 1
        print('RGB camera ready!')

        # Spawn depth camera
        depth_bp = world.get_blueprint_library().find('sensor.camera.depth')
        depth_bp.set_attribute('sensor_tick', str(cfg.tick_gap))
        depth = world.spawn_actor(depth_bp, cam_transform)

        # Spawn collision sensor
        collision_bp = world.get_blueprint_library().find(
            'sensor.other.collision')
        collision_transform = carla.Transform()
        collision = world.spawn_actor(collision_bp, collision_transform, attach_to=hero)
        collision_queue = queue.Queue()
        collision.listen(collision_queue.put)
        nonvehicles_list.append(collision)
        print('Collision sensor ready!')

        # cc_depth_log = carla.ColorConverter.LogarithmicDepth
        nonvehicles_list.append(depth)
        depth_queue = queue.Queue()
        depth.listen(depth_queue.put)
        q_list.append(depth_queue)
        depth_idx = idx
        idx = idx + 1
        print('Depth camera ready!')

        # Begin the loop
        time_sim = 0
        # while True:
        fps = 1 / cfg.tick_gap

        # hero_agents = {}
        # stop_agents = {}
        for _ in range(int(60 * cfg.simul_min * fps)):
            # Extract the available data
            now_frame = world.tick()

            if time_sim >= cfg.tick_gap:
                data = [retrieve_data(q, now_frame) for q in q_list]
                assert all(x.frame == now_frame for x in data if x is not None)

                # Skip if any sensor data is not available
                if None in data:
                    print("No sensor data available. Continue.")
                    continue

                vehicles_raw = world.get_actors().filter('vehicle.*')
                snap = data[tick_idx]
                rgb_img = data[cam_idx]
                depth_img = data[depth_idx]

                # Attach additional information to the snapshot
                vehicles = cva.snap_processing(vehicles_raw, snap)
                # print('\nGet vehicles per tick:')
                # print(len(vehicles))
                # print(vehicles.id)
                # for v in vehicles:
                #     print(v.id)

                # Save depth image, RGB image, and Bounding Boxes data
                depth_meter = cva.extract_depth(depth_img)
                filtered, removed = cva.auto_annotate(vehicles, cam,
                                                      depth_meter)
                # json_path=r'C:\Users\root\Develop\CARLA_0.9.12\WindowsNoEditor\AnomalyDetProj\vehicle_class_json_file.txt')

                # print(filtered, removed)
                filtered_vehicles = filtered['vehicles']
                filtered_vehicles_ids = [fv.id for fv in filtered_vehicles]

                # Judge whether danger vehicle in ROI:
                # danger_roi_ids = inter(filtered_vehicles_ids, danger_vid)

                # Judge whether hero car is in ROI:
                # whether collision happens

                if not collision_queue.empty():
                    print(hero.get_location())
                    if danger_vid in filtered_vehicles:
                        print(f"report collision: {danger_vid}")
                        agt = BasicAgent(hero, target_speed=0)
                        hero.apply_control(agt.run_step())
                        
                    else:
                        collision_queue.queue.clear()

                # if danger_roi_ids:
                    # print(f"Detected danger vehicles: {danger_roi_ids}")
                    # TODO: to debug: agents
                    # ==========================================================
                    # for hero_id in danger_roi_ids:
                        # get each danger car id in roi: hero_id

                        # agt = BasicAgent(hero, target_speed=0)
                        # hero_agents[hero_id] = agt
                        # hero = world.get_actor(hero_id)

                        # attach collision sensor
                        # ==========================================
                        # collision_transform = carla.Transform()
                        # collision = world.spawn_actor(collision_bp, collision_transform, attach_to=hero)
                        # collision_queue = queue.Queue()
                        # collision.listen(collision_queue.put)
                        # ==========================================

                        # unsure whether to tick here
                        # now_frame = world.tick()

                        # if (not collision_queue.empty()) and hero_id not in stop_agents:
                        #     agt = BasicAgent(hero, target_speed=0)  # await for collision sensor signal
                        #     stop_agents[hero_id] = agt
                        #     print("report collision:", collision_queue.get())

                        # for hero_id in stop_agents:
                        #     stop_agents[hero_id].set_target_speed(0)

                        # destroy temporary collision sensor
                        # collision.destroy()
                        # collision_queue.queue.clear()

                    # print(stop_agents)
                    # for hero_id in stop_agents:
                    #     stop_agents[hero_id].set_target_speed(0)
                    #     hero = world.get_actor(hero_id)
                    #     hero.apply_control(stop_agents[hero_id].run_step())
                    # ==========================================================

                # for v in filtered_vehicles:
                #     v = world.get_actor(v.id)
                #     print(v.get_location())
                #     print(v.get_velocity().y)
                #     print(v.get_angular_velocity().y)
                #     print(v.get_acceleration().y)

                # removed_vehicles = removed['vehicles']

                # for v in removed_vehicles:
                #     v = world.get_actor(v.id)
                #     print(v.get_location())
                #     print(v.get_velocity().y)
                #     print(v.get_angular_velocity().y)
                #     print(v.get_acceleration().y)

                # print(len(filtered_vehicles), len(removed_vehicles))

                # The params of following function are attached to filtered and removed vehicles.
                # cva.save_output(rgb_img,
                #                 filtered['bbox'],
                #                 filtered['class'],
                #                 removed['bbox'],
                #                 removed['class'],
                #                 save_patched=True,
                #                 out_format='json')

                cva_custom.save_custom_output(
                    world,
                    rgb_img,
                    filtered_vehicles,
                    filtered['bbox'],
                    # save_patched=True,
                    save_patched=False,
                    path=cur_dir,
                    out_format='json')
                time_sim

            time_sim += settings.fixed_delta_seconds

    except:
        print("\nFailed to enter the main function. Exit.\n")
    # finally:
    try:
        cam.stop()
        depth.stop()
    except:
        print("Simulation ended before sensors have been created")

    settings = world.get_settings()
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = None
    world.apply_settings(settings)

    print('destroying %d nonvehicles' % len(nonvehicles_list))
    client.apply_batch(
        [carla.command.DestroyActor(x) for x in nonvehicles_list])

    print('\ndestroying %d vehicles' % len(vehicles_list))
    client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

    # destroy collision sensor
    # collision.destroy()

    time.sleep(0.5)


def make_data(cfg):
    try:
        for _ in range(cfg.scene_num):
            since = time.time()
            try:
                launch(cfg)
            except KeyboardInterrupt:
                pass
            finally:
                print('\ndone.')
                print("Simulation cost {:.4f} seconds.\n".format(time.time() -
                                                                 since))
    except:
        print("Program terminated. Exit.")


def inter(a, b):
    return list(set(a) & set(b))
