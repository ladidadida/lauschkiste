"""Contract shared by core modules and plugins. See documentation/developers/core-and-plugins.md."""

from lauschkiste.contract.context import Context, ModuleConfig
from lauschkiste.contract.declarations import ExtensionPoint, action, event, extension_point, query
from lauschkiste.contract.errors import ActionError, ContractError, OperationError
from lauschkiste.contract.module import CoreModule, Module, Plugin
from lauschkiste.contract.version import CONTRACT_VERSION

__all__ = [
    'CONTRACT_VERSION', 'ActionError', 'Context', 'ContractError', 'CoreModule', 'ExtensionPoint', 'Module',
    'ModuleConfig', 'OperationError', 'Plugin', 'action', 'event', 'extension_point', 'query',
]
