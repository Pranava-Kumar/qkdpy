"""QKDpy: A Python Package for Quantum Key Distribution.

QKDpy is a comprehensive library for Quantum Key Distribution (QKD) simulations,
implementing various QKD protocols, quantum simulators, and cryptographic tools.
"""

# ruff: noqa: F403, F405 — star imports intentional for public API re-export

__version__ = "0.6.6"
__author__ = "Pranava Kumar"
__email__ = "pranavakumar.it@gmail.com"

# Bring names into top-level namespace + keep module refs for __all__
from . import (
    core,
    crypto,
    exceptions,
    integrations,
    key_management,
    ml,
    network,
    protocols,
    utils,
)

# Configuration — explicit imports (config.py has no __all__)
from .config import (
    QKDConfig,
    get_config,
    is_debug_mode,
    is_production_mode,
    set_config,
)
from .core import *
from .crypto import *
from .exceptions import *
from .integrations import *
from .key_management import *
from .ml import *
from .network import *
from .protocols import *
from .utils import *

__all__ = [
    # Configuration
    "QKDConfig",
    "get_config",
    "set_config",
    "is_debug_mode",
    "is_production_mode",
    # Subpackage exports (from __all__)
    *core.__all__,
    *crypto.__all__,
    *exceptions.__all__,
    *integrations.__all__,
    *key_management.__all__,
    *ml.__all__,
    *network.__all__,
    *protocols.__all__,
    *utils.__all__,
]
