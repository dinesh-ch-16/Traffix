from perception.sumo_client import SumoClient


CONFIG_FILE = "simulation/sumo/configs/traffix.sumocfg"


def main():

    sumo = SumoClient(CONFIG_FILE)

    sumo.start()

    try:

        for step in range(300):

            sumo.step()

            if step % 10 == 0:

                print(
                    f"Time: {sumo.get_time():.0f}s | "
                    f"Vehicles: {sumo.get_vehicle_count()}"
                )

    finally:

        sumo.close()


if __name__ == "__main__":
    main()