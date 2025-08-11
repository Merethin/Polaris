from dataclasses import dataclass
from collections import deque
from filters.recruit import RecruitFilter
import time

NON_WA = 0
WA_MEMBER = 1
WA_DELEGATE = 2

@dataclass
class Nation:
    id: str
    name: str
    flagUrl: str
    waStatus: int
    region: str
    endorsements: set[str]
    residencyNum: float
    population: int
    canRecruit: bool
    lastLogin: int
    foundedAt: int
    lastApiUpdateTime: float
    lastResidencyUpdateTime: float
    flagDirty: bool = False

    def resetLogin(self):
        self.lastLogin = int(time.time())

    def resetResidency(self):
        self.residencyNum = 0
        self.lastResidencyUpdateTime = time.time()

    def residency(self):
        return self.residencyNum + ((time.time() - self.lastResidencyUpdateTime) / 86400)

@dataclass
class Authority:
    successor: bool
    appearance: bool
    borderControl: bool
    communications: bool
    embassies: bool
    polls: bool

    def parse(text: str):
        authority = Authority(False, False, False, False, False, False)

        for character in text:
            if character == "S":
                authority.successor = True
            elif character == "A":
                authority.appearance = True
            elif character == "B":
                authority.borderControl = True
            elif character == "C":
                authority.communications = True
            elif character == "E":
                authority.embassies = True
            elif character == "P":
                authority.polls = True
        
        return authority

@dataclass
class RegionalOfficer:
    nationId: str
    officeName: str
    authority: Authority

@dataclass
class Region:
    id: str
    name: str
    nations: set[str]
    delegate: str | None
    officers: dict[str, RegionalOfficer]
    recruiters: set[str]
    lastApiUpdateTime: float

@dataclass
class APITelegram:
    targetId: str
    tgid: str
    key: str

MODE_API = 0
MODE_MANUAL = 1
MODE_BOTH = 2

@dataclass
class BucketQueue:
    name: str
    filter: RecruitFilter
    nations: deque[tuple[str, float]]
    priority: float
    mode: int
    templates: list[str]

    def create(name: str, filter: str, size: int, priority: float, mode: int, templates: list[str]):
        return BucketQueue(name, RecruitFilter().parse(filter), deque(maxlen=size), priority, mode, templates)

    def lastUpdate(self) -> float:
        if self.nations:
            return self.nations[-1][1] + self.priority
        else:
            return 0

    def supportsManual(self):
        return self.mode != MODE_API

    def supportsAPI(self):
        return self.mode != MODE_MANUAL

RMB_NORMAL_POST = 0
RMB_SUPPRESSED = 1
RMB_SELF_DELETED = 2
RMB_MOD_SUPPRESSED = 9
    
@dataclass
class Message:
    id: int
    timestamp: int
    nation: str
    status: int
    suppressor: str | None
    content: str | None