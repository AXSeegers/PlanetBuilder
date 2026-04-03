from dataclasses import dataclass

ElementDictionary = dict[str, float]
AtomicWeightDictionary = dict[str, float]
KdDictionary = dict[str, float]

@dataclass
class MantleAndCoreDictionaries:
    mantle: ElementDictionary
    core: ElementDictionary