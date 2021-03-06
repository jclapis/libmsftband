import bdb
import os
import pdb
import re
import sys
from distutils.util import strtobool

from dotenv import load_dotenv

from examples import ExampleClient
from libband.sensors import Sensor
from libband.screens import BandScreens


HELP_TEXT = '''
Available commands:
- sync - syncs device,
- pdb - drops into Python pdb shell
- help - shows this screen
- exit - exits this shell
'''


def cli():
    # check if device address was defined
    DEVICE_MAC_ADDRESS = os.getenv('DEVICE_MAC_ADDRESS')
    if not DEVICE_MAC_ADDRESS:
        print('DEVICE_MAC_ADDRESS env variable not set')
        return

    use_shell = True
    command = None
    if len(sys.argv) > 1:
        command = ' '.join([sys.argv[1].lstrip('--'), *sys.argv[2:]])
        use_shell = False

    app = ExampleClient()
    try:
        # connect to device
        app.select_device(DEVICE_MAC_ADDRESS)
        if not app.device.check_if_oobe_completed():
            # Device in OOBE mode
            bypass_question = input(
                'Your device is in OOBE mode, do you want to bypass it? '
                '[Y/n]: '
            )
            if strtobool(bypass_question):
                app.device.navigate_to_screen(
                    BandScreens.OobePressButtonToStart
                )

        while use_shell or command:
            if use_shell:
                command = input('> ')

            # parse command
            if re.match(r'^sync$', command):
                app.sync()
            elif re.match(r'^pdb$', command):
                pdb.set_trace()
            elif re.match(r'^help$', command):
                print(HELP_TEXT)
            elif re.match(r'^info$', command):
                print(
                    f'Band Type: {app.device.band_type.name}\n'
                    f'Application: {app.device.version.application}\n'
                    f'Bootloader: {app.device.version.bootloader}\n'
                    f'Updater: {app.device.version.updater}\n'
                )
            elif re.match(r'^api-version$', command):
                print(app.device.get_api_version())
            elif re.match(r'^whoami$', command):
                print(app.device.get_running_firmware_app())
            elif re.match(r'^check-sdk .\d* .\d*$', command):
                args = command.split(' ')[1:]
                app.device.check_firmware_sdk_bit(*args)
            elif re.match(r'^subscribe .\d*$', command):
                service = app.services['SensorStreamService']
                subscription = int(command.split(' ')[1])
                result = service.subscribe(subscription)
                if result:
                    print(f'Subscribed to {Sensor(subscription).name}')
            elif re.match(r'^unsubscribe .\d*$', command):
                service = app.services['SensorStreamService']
                subscription = int(command.split(' ')[1])
                result = service.unsubscribe(subscription)
                if result:
                    print(f'Unubscribed from {Sensor(subscription).name}')
            elif re.match(r'^subscriptions$', command):
                service = app.services['SensorStreamService']
                print(', '.join([
                    Sensor(subscription).name
                    for subscription in service.subscriptions
                ]))
            elif re.match(r'^exit$', command):
                raise SystemExit
            else:
                print('Command not recognized')

            if not use_shell:
                raise SystemExit
    except (bdb.BdbQuit, SystemExit, KeyboardInterrupt):
        app.device.disconnect()


if __name__ == '__main__':
    load_dotenv()
    cli()
