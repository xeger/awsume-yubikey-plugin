import argparse
import colorama

from subprocess import Popen, CalledProcessError, PIPE

from awsume.awsumepy import hookimpl, safe_print
from awsume.awsumepy.lib import profile
from awsume.awsumepy.lib.logger import logger

# we print only N lines of output to minimize ykman stack trace spam
MAX_OUTPUT_LINES = 2


def find_item(config, mfa_serial):
    config = config.get('yubikey')
    if not config:
        logger.debug('No config subsection')
        return
    elif type(config) != dict:
        logger.debug('Malformed config subsection')
        return
    item = config.get(mfa_serial)
    if not item:
        logger.debug('No vault item specified for this mfa_serial')
    return item


def get_mfa_serial(profiles, target_name):
    mfa_serial = profile.get_mfa_serial(
        profiles, target_name)
    if not mfa_serial:
        logger.debug('No MFA required')
    return mfa_serial


def describe_failure(stderr):
    return stderr.decode().strip('\n')


def get_otp(title):
    try:
        yk = Popen(['ykman', 'oath', 'accounts', 'code', '--single', title],
                   stdout=PIPE, stderr=PIPE)
        linecount = 0
        while True:
            msg = yk.stderr.readline().decode()
            if msg == '' and yk.poll() is not None:
                break
            elif msg != '':
                if linecount < MAX_OUTPUT_LINES:
                    safe_print(msg, colorama.Fore.CYAN, end='')
                    linecount += 1
                else:
                    logger.debug(msg.strip('\n'))

        if yk.returncode != 0:
            return None
        return yk.stdout.readline().decode().strip('\n')
    except FileNotFoundError:
        logger.error('Failed: missing `ykman` command')
        return None


@ hookimpl
def pre_get_credentials(config: dict, arguments: argparse.Namespace, profiles: dict):
    mfa_serial = get_mfa_serial(profiles, arguments.target_profile_name)
    if mfa_serial and not arguments.mfa_token:
        item = find_item(config, mfa_serial)
        if item:
            arguments.mfa_token = get_otp(item)
