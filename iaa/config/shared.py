from typing import Literal

from pydantic import BaseModel


class TelemetryConfig(BaseModel):
    sentry: bool | None = None


class ProfilesConfig(BaseModel):
    last_used: str | None = None
    open_tabs: list[str] = []


class InterfaceConfig(BaseModel):
    window_style: str = ''
    theme_color: str | None = None
    color_scheme: Literal['auto', 'light', 'dark'] = 'auto'


class CustomPushData(BaseModel):
    command: str = ''


PushData = CustomPushData


class PushConfig(BaseModel):
    enabled: bool = False
    type: Literal['custom'] = 'custom'
    data: CustomPushData = CustomPushData()


class NotifyConfig(BaseModel):
    system: bool = True
    push: PushConfig = PushConfig()


class HotkeysConfig(BaseModel):
    start: str | None = None
    stop: str | None = None


class SharedConfig(BaseModel):
    version: int = 1
    profiles: ProfilesConfig = ProfilesConfig()
    telemetry: TelemetryConfig = TelemetryConfig()
    interface: InterfaceConfig = InterfaceConfig()
    notify: NotifyConfig = NotifyConfig()
    hotkeys: HotkeysConfig = HotkeysConfig()
