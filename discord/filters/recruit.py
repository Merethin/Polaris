import re
from filters import Filter, FilterComponent, FilterError
from typing import Self, Optional

FILTER_REGEX = re.compile(r"(wa|founded|refounded|move)(?::(-)?([a-z0-9_-]+)((?:,[a-z0-9_-]+)*)?)?")

GLOBAL_LABELS = {
    "wa": "new WA joins",
    "founded": "new nations founded",
    "refounded": "nations refounded",
}

INCLUDE_LABELS = {
    "wa": "new WA joins in",
    "founded": "new nations founded in",
    "refounded": "nations refounded in",
    "move": "nations moving to",
}

EXCLUDE_LABELS = {
    "wa": "new WA joins anywhere but",
    "founded": "new nations founded anywhere but",
    "refounded": "nations refounded anywhere but",
}

def compileRegionList(firstMatchedRegion: Optional[str], 
                      otherMatchedRegions: Optional[str]) -> list[str]:
    regions = [firstMatchedRegion]
    if otherMatchedRegions is not None:
        regions += [r for r in otherMatchedRegions.split(",") if r != ""]
    return regions

class GlobalRecruitFilter(FilterComponent):
    def __init__(self, event: str):
        self.event = event

    def create(event: str, exclude: Optional[str], 
               firstRegion: Optional[str], otherRegions: Optional[str]) -> Optional[Self]:
        if firstRegion:
            return None
        if event == "move":
            raise FilterError(f"'move' filter needs a list of regions!")
        return GlobalRecruitFilter(event)

    def matches(self, event: str, region: str) -> bool:
        return event == self.event
    
    def explain(self) -> str:
        return f"Matches all {GLOBAL_LABELS[self.event]}"
    
class IncludeRecruitFilter(FilterComponent):
    def __init__(self, event: str, regions: set[str]):
        self.event = event
        self.regions = regions

    def create(event: str, exclude: Optional[str], 
               firstRegion: Optional[str], otherRegions: Optional[str]) -> Optional[Self]:
        if exclude == "-" or not firstRegion:
            return None
        
        regions = compileRegionList(firstRegion, otherRegions)
        return IncludeRecruitFilter(event, set(regions))

    def matches(self, event: str, region: str) -> bool:
        return event == self.event and region in self.regions
    
    def explain(self) -> str:
        return f"Matches {INCLUDE_LABELS[self.event]}: {", ".join([f"`{r}`" for r in self.regions])}"
    
class ExcludeRecruitFilter(FilterComponent):
    def __init__(self, event: str, regions: set[str]):
        self.event = event
        self.regions = regions

    def create(event: str, exclude: Optional[str], 
               firstRegion: Optional[str], otherRegions: Optional[str]) -> Optional[Self]:
        if exclude != "-" or not firstRegion:
            return None
        if event == "move":
            raise FilterError(f"'move' filter is not compatible with exclusion filters!")
        
        regions = compileRegionList(firstRegion, otherRegions)
        return ExcludeRecruitFilter(event, set(regions))

    def matches(self, event: str, region: str) -> bool:
        return event == self.event and region not in self.regions
    
    def explain(self) -> str:
        return f"Matches {EXCLUDE_LABELS[self.event]}: {", ".join([f"`{r}`" for r in self.regions])}"

class RecruitFilter(Filter):
    def __init__(self):
        super().__init__([GlobalRecruitFilter, IncludeRecruitFilter, ExcludeRecruitFilter], FILTER_REGEX)

    def matches(self, event: str, region: str) -> bool:
        return super().matches(event, region)