"""Реестр фабрик анализаторов.

Сервис анализа знает только идентификатор анализатора. Чтобы добавить
новый анализатор, достаточно зарегистрировать фабрику, сервис менять не надо.
"""

from collections.abc import Callable

from labcheck.analyzers import Analyzer, LengthAnalyzer, TemplateAnalyzer
from labcheck.errors import AnalyzerError

AnalyzerFactory = Callable[[], Analyzer]


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, AnalyzerFactory] = {}

    def register(self, analyzer_id: str, factory: AnalyzerFactory) -> None:
        if analyzer_id in self._factories:
            raise ValueError(f"анализатор {analyzer_id} уже зарегистрирован")
        self._factories[analyzer_id] = factory

    def create(self, analyzer_id: str) -> Analyzer:
        if analyzer_id not in self._factories:
            raise AnalyzerError("unknown_analyzer", f"неизвестный анализатор {analyzer_id}")
        return self._factories[analyzer_id]()

    def ids(self) -> list[str]:
        return sorted(self._factories)


def default_registry() -> AnalyzerRegistry:
    """Каждый раз создаётся новый реестр, глобального состояния нет."""
    registry = AnalyzerRegistry()
    registry.register("length", LengthAnalyzer)
    registry.register("template", TemplateAnalyzer)
    return registry
