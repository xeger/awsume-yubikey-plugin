# Awsume YubiKey Plugin

_Awsume 4+ only_.

This is a plugin that automates the entry of MFA tokens using YubiKey.
It replaces AWSume's `MFA Token:` prompt with a token-touch prompt and delegates to YubiKey for policies on how often unlock is required.
In other words: it saves you from ever having to type an MFA token, ever again!

## Support

If you experience any problems, please [file a bug report](https://github.com/xeger/awsume-yubikey-plugin/issues/new?assignees=xeger&template=bug_report.md).

## Installation

### Install This Plugin

```
pip3 install awsume-yubikey-plugin
```

If you've installed awsume with `pipx`, this will install the console plugin in awsume's virtual environment:

```
pipx inject awsume awsume-yubikey-plugin
```

### Set Up YubiKey

1. Install the [YubiKey CLI](https://docs.yubico.com/software/yubikey/tools/ykman/Install_ykman.html)
2. If a token password is set (rare), remember it on this machine so that `ykman oath accounts code` does not require any keyboard input.

### Configure AWSume

This plugin needs to know which YubiKey OATH token to use for each MFA token.
You can specify this information your AWSume configuration file.


```yaml
# ~/.awsume/config.yaml

colors: true
yubikey: AWS
```

In this example, I have only one MFA token shared among all my accounts (which belong to the same organization).

I have a corresponding YubiKey account that looks like this:

```sh
$ ykman oath accounts list

  AWS
```

### Multiple MFA Tokens

```yaml
# ~/.awsume/config.yaml

colors: true
yubikey:
  "arn:aws:iam::12345:mfa/tony": "AWS (12345, tony)"
  "arn:aws:iam::67890:mfa/xeger": "AWS (67890, xeger)"
```

In this example, I work with two login accounts belonging to two different organizations: one where my name is `tony` and another where my name is `xeger`.

I have corresponding YubiKey accounts that look like this:

```sh
$ ykman oath accounts list

  AWS (12345, tony)
  AWS (67890, xeger)
```

## Usage

This plugin works automatically in the background; just `awsume` roles as you normally would, and it will invoke the `ykman` command to obtain TOTP tokens whenever AWSume requires one.

## Troubleshooting

If you experience any trouble, invoke `awsume` with the `--debug` flag and look for log entries that contain `yubikey`.

The specific command that this plugin invokes is `ykman oath accounts code --single "Account Name Here"`; make sure it succeeds when you invoke it manually.

If you can't solve your problem, [create a GitHub issue](https://github.com/xeger/awsume-yubikey-plugin/issues/new) with diagnostic details and we'll try to help you.
