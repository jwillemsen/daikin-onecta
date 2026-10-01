# daikin-onecta

[![CI](https://github.com/jwillemsen/daikin-onecta/actions/workflows/ci.yml/badge.svg)](https://github.com/jwillemsen/daikin-onecta/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jwillemsen/daikin-onecta/graph/badge.svg)](https://codecov.io/gh/jwillemsen/daikin-onecta)
[![PyPI version](https://img.shields.io/pypi/v/daikin-onecta.svg)](https://pypi.org/project/daikin-onecta/)
[![Python versions](https://img.shields.io/pypi/pyversions/daikin-onecta.svg)](https://pypi.org/project/daikin-onecta/)
[![License](https://img.shields.io/pypi/l/daikin-onecta.svg)](https://github.com/jwillemsen/daikin-onecta/blob/main/LICENSE)

Async Python client for the Daikin Onecta cloud API.

This library contains the Daikin-specific API layer used by the Home Assistant
Daikin Onecta integration. It deliberately has no dependency on Home Assistant.

## Usage

```python
import aiohttp

from daikin_onecta import OnectaClient


async def token_provider() -> str:
    return "access-token"


async with aiohttp.ClientSession() as session:
    client = OnectaClient(session, token_provider)
    devices = await client.get_gateway_devices()
```

Authentication is supplied by an asynchronous token callback so applications
remain responsible for their own OAuth flow and token refresh.

## Status

The API is currently alpha. The first release intentionally exposes gateway
devices as raw dictionaries while the stable typed device model is developed.
