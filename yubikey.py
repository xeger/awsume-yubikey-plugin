import argparse
import colorama
import traceback
import sys

from subprocess import Popen, CalledProcessError, PIPE

from awsume.awsumepy import hookimpl, safe_print
from awsume.awsumepy.lib import profile
from awsume.awsumepy.lib.logger import logger

# Truncate proxied subprocess output to avoid stack trace spam
MAX_OUTPUT_LINES = 2


# Map an MFA serial to a YubiKey OATH account
def find_item(config, mfa_serial):
    config = config.get('yubikey')
    item = None
    if not config:
        logger.debug('No config subsection')
    elif type(config) == str:
        item = config
    elif type(config) == dict:
        item = config.get(mfa_serial)
    else:
        logger.debug('Malformed config subsection')
        return
    if not item:
        logger.debug('No OATH account specified for this mfa_serial')
    return item

# Find the MFA serial for a given AWS profile.


def get_mfa_serial(profiles, target_name):
    mfa_serial = profile.get_mfa_serial(
        profiles, target_name)
    if not mfa_serial:
        logger.debug('No MFA required')
    return mfa_serial


# Make a YubiKey error message more succinct before safe_printing it.
# Return None if it's not worth printing (e.g. an expected error).
def beautify(msg):
    if 'No YubiKey detected!' in msg:
        return None
    else:
        return msg

# Call YubiKey to get an OTP for a given vault item.


def get_otp(title):
    try:
        yk = Popen(['ykman', 'oath', 'accounts', 'code', '--single', title],
                   stdout=PIPE, stderr=PIPE)
        linecount = 0
        while True:
            msg = yk.stderr.readline().decode()
            if msg == '' and yk.poll() is not None:
                break
            elif msg != '' and linecount < MAX_OUTPUT_LINES:
                msg = beautify(msg)
                if msg:
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


def canonicalize(config, profiles, name):
    target_name = profile.get_profile_name(config, profiles, name, log=False)
    if profiles.get(target_name) != None:
        return target_name
    else:
        return None

# Print sad message to console with instructions for filing a bug report.
# Log stack trace to stderr in lieu of safe_print.


def handle_crash():
    safe_print('Error invoking YubiKey plugin; please file a bug report:\n  %s' %
               ('https://github.com/xeger/awsume-yubikey-plugin/issues/new/choose'), colorama.Fore.RED)
    traceback.print_exc(file=sys.stderr)


@ hookimpl
def pre_get_credentials(config: dict, arguments: argparse.Namespace, profiles: dict):
    try:
        target_profile_name = canonicalize(
            config, profiles, arguments.target_profile_name)
        if target_profile_name != None:
            mfa_serial = get_mfa_serial(profiles, target_profile_name)
            if mfa_serial and not arguments.mfa_token:
                item = find_item(config, mfa_serial)
                if item:
                    arguments.mfa_token = get_otp(item)
                    if arguments.mfa_token:
                        safe_print('Obtained MFA token from YubiKey item: %s' %
                                   (item), colorama.Fore.CYAN)
    except Exception:
        handle_crash()
