import argparse
import sys
import traceback
from subprocess import Popen, PIPE

import colorama
from awsume.awsumepy import hookimpl, safe_print
from awsume.awsumepy.lib import cache as cache_lib
from awsume.awsumepy.lib import profile as profile_lib
from awsume.awsumepy.lib.logger import logger

# Truncate proxied subprocess output to avoid stack trace spam
MAX_OUTPUT_LINES = 2


# Map an MFA serial to a YubiKey OATH account
def find_item(config, mfa_serial):
    config = config.get("yubikey")
    item = None
    if not config:
        logger.debug("No config subsection")
    elif isinstance(config, str):
        item = config
    elif isinstance(config, dict):
        item = config.get(mfa_serial)
    else:
        logger.debug("Malformed config subsection")
        return
    if not item:
        logger.debug("No OATH account specified for this mfa_serial")
    return item


# Find the MFA serial for a given AWS profile.
def get_mfa_serial(profiles, target_name):
    mfa_serial = profile_lib.get_mfa_serial(profiles, target_name)
    if not mfa_serial:
        logger.debug("No MFA required")
    return mfa_serial


# Make a YubiKey error message more succinct before safe_printing it.
# Return None if it's not worth printing (e.g. an expected error).
def beautify(msg):
    if "No YubiKey detected!" in msg:
        return None
    else:
        return msg


# Call YubiKey to get an OTP for a given vault item.


def get_otp(title):
    try:
        yk = Popen(
            ["ykman", "oath", "accounts", "code", "--single", title],
            stdout=PIPE,
            stderr=PIPE,
        )
        linecount = 0
        while True:
            msg = yk.stderr.readline().decode()
            if msg == "" and yk.poll() is not None:
                break
            elif msg != "" and linecount < MAX_OUTPUT_LINES:
                msg = beautify(msg)
                if msg:
                    safe_print(msg, colorama.Fore.CYAN, end="")
                    linecount += 1
            else:
                logger.debug(msg.strip("\n"))

        if yk.returncode != 0:
            return None
        return yk.stdout.readline().decode().strip("\r\n")
    except FileNotFoundError:
        logger.error("Failed: missing `ykman` command")
        return None


# Print sad message to console with instructions for filing a bug report.
# Log stack trace to stderr in lieu of safe_print.


def handle_crash():
    safe_print(
        "Error invoking YubiKey plugin; please file a bug report:\n  %s"
        % ("https://github.com/xeger/awsume-yubikey-plugin/issues/new/choose"),
        colorama.Fore.RED,
    )
    traceback.print_exc(file=sys.stderr)


@hookimpl
def pre_get_credentials(config: dict, arguments: argparse.Namespace, profiles: dict):
    try:
        target_profile_name = profile_lib.get_profile_name(
            config, profiles, arguments.target_profile_name
        )
        if not profiles.get(target_profile_name):
            logger.debug("No profile %s found, skip plugin flow" % target_profile_name)
            return None
        if target_profile_name is not None:
            # In case that a duration is requested or an empty target_profile_name is provided or
            # the target_profile does not contain a role_arn, then
            # only the [TARGET_PROFILE] is returned, else [SOURCE_PROFILE, TARGET_PROFILE]
            role_chain = profile_lib.get_role_chain(
                config, arguments, profiles, target_profile_name
            )
            first_profile_name = role_chain[0]
            mfa_serial = profile_lib.get_mfa_serial(profiles, first_profile_name)
            first_profile = profiles.get(first_profile_name)

            # AWS API Keys are provided by SOURCE_PROFILES
            # and sometimes by TARGET_PROFILEs (depends on their definition in the .aws/config)
            source_credentials = profile_lib.profile_to_credentials(first_profile)
            access_key_id = source_credentials.get("AccessKeyId")

            request_otp = True
            if access_key_id:
                cache_file_name = f"aws-credentials-{access_key_id}"
                cache_session = cache_lib.read_aws_cache(cache_file_name)
                valid_cache_session = cache_session and cache_lib.valid_cache_session(cache_session)
                request_otp = not valid_cache_session or arguments.force_refresh

            if mfa_serial and not arguments.mfa_token and request_otp:
                item = find_item(config, mfa_serial)
                if item:
                    arguments.mfa_token = get_otp(item)
                    if arguments.mfa_token:
                        safe_print(
                            "Obtained MFA token from YubiKey item: %s" % (item),
                            colorama.Fore.CYAN,
                        )
    except Exception:
        handle_crash()
