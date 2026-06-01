# iaa/application/qt/controllers/log_routing.py

import logging


class ContextVarLogHandler(logging.Handler):
    """将 Python logging 记录路由到当前线程绑定的 per-tab LogBridge。

    调度器线程在 __prepare_context() 中会调用 set_tab_log_bridge() 设置目标；
    未设置的线程（UI 线程等）emit 的日志不会被此 handler 处理。
    """

    def emit(self, record: logging.LogRecord) -> None:
        from iaa.context import _g_log_bridge
        bridge = _g_log_bridge.get()
        if bridge is None:
            return
        try:
            msg = self.format(record) + '\n'
            bridge.write_text(msg, 'normal')
        except Exception:
            self.handleError(record)
