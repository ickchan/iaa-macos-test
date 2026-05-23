from __future__ import annotations

from dataclasses import dataclass

from iaa.config.base import IaaConfig
from iaa.config.shared import SharedConfig


@dataclass
class FormContext:
    """设置页 DSL 上下文。"""

    conf: IaaConfig
    shared: SharedConfig


@dataclass
class PreferencesContext:
    """偏好页 DSL 上下文。"""

    shared: SharedConfig
