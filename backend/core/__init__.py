__all__ = [
    "Transition",
    "evaluate_utility",
    "get_navigation_successors",
    "get_successors",
    "comparar_adversarial",
]


def __getattr__(name: str):
    if name in {"Transition", "get_navigation_successors", "get_successors"}:
        from .successors import Transition, get_navigation_successors, get_successors

        return {
            "Transition": Transition,
            "get_navigation_successors": get_navigation_successors,
            "get_successors": get_successors,
        }[name]
    if name == "evaluate_utility":
        from .utility import evaluate_utility

        return evaluate_utility
    if name == "comparar_adversarial":
        from .adversarial_comparison import comparar_adversarial

        return comparar_adversarial
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
