from functools import cmp_to_key
import uuid
from consts import LOCATION_ID_COLUMN, LOCATION_NAME_COLUMN, LOCATION_PARENT_COLUMN, LOCATION_SHEET
from state import Location
import pandas as pd

def readLocationsFromDB(path: str) -> list[Location]:
    df: pd.DataFrame = pd.read_excel(path, sheet_name=LOCATION_SHEET, dtype=str) # type: ignore
    return parseLocations(df)

def parseLocations(df: pd.DataFrame) -> list[Location]:
    locations: list[Location] = []
    for _, row in df.iterrows(): # type: ignore
        assert type(row) == pd.Series # type: ignore
        uuid: str = str(row[LOCATION_ID_COLUMN]) # type: ignore
        assert type(uuid) == str
        name: str = str(row[LOCATION_NAME_COLUMN]) # type: ignore
        assert type(name) == str
        parentId: str = str(row[LOCATION_PARENT_COLUMN]) # type: ignore
        assert type(parentId) == str
        parentId: str|None = parentId if parentId not in ["", "nan"] else None
        locations.append(Location(name, uuid, parentId))
    return locations

def serializeLocations(locatios: list[Location]) -> pd.DataFrame:
    data: dict[str, list[str | None]] = {
        LOCATION_ID_COLUMN: [location.id for location in locatios],
        LOCATION_NAME_COLUMN: [location.name for location in locatios],
        LOCATION_PARENT_COLUMN: [location.parent for location in locatios]
    }
    return pd.DataFrame(data)

def keepTopParents(allLocations: list[Location], selectedLocations: list[Location]) -> list[Location]:
    """
    Returns a copy of the selected locations with only the top most parents.
    All location that are children of any depth to another location will be removed.
    This descibes the drag and drop behavior when selecting multiple locations, on different levels.
    Only the top most selected parents will be moved, the children will stay their children.

    Example:
    --------
    ```
    locations
    ├─ a
    │  ├─ aa
    │  │  ├─ aaa
    │  ├─ ab
    ├─ b
    │  ├─ ba
    │  │  ├─ baa

    ```
    input: [a, ab, aaa, ba, baa]
    result: [a, ba]
    """
    result: list[Location] = []
    for l1 in selectedLocations:
        child = False
        for l2 in selectedLocations:
            if l1 == l2:
                continue
            if isSomeParent(allLocations, l2, l1):
                child = True
        if not child:
            result.append(l1)
    return result


def isSomeParent(locations: list[Location], parent: Location, child: Location) -> bool:
    """Checks if the child is a child of the parent."""
    while child.parent is not None:
        if child.parent == parent:
            return True
        child = getLocation(locations, child.parent)
    return False

def getLocation(locations: list[Location], id: str) -> Location:
    """Converts a location uid to a location."""
    for location in locations:
        if location.id == id:
            return location
    raise ValueError(f"Location with id {id} not found.")



def getLocationFromPath(locations: list[Location], path: list[int], parent: Location | None = None) -> Location:
    if len(path) == 0:
        raise ValueError("Location from path not found.")
    location = getChildren(locations, parent)[path[0]]
    return getLocationFromPath(getChildren(locations, location), path[1:], location)


def getLocationString(locations: list[Location], uid: str) -> str:
    if uid == "":
        return ""
    strings = getLocationStrings(locations, uid)
    return " > ".join(strings)


def getLocationStrings(locations: list[Location], target: Location | str) -> list[str]:
    if type(target) == str:
        target = getLocation(locations, target)
    assert(type(target) == Location)
    return (getLocationStrings(locations, target.parent) + [target.name]) if target.parent else []


def getLocationFromNames(
    locations: list[Location], namePath: list[str] | None, parent: Location | None = None
) -> Location | None:
    """Converts a name path to a location."""
    if namePath is None:
        return None
    section = None
    for location in getChildren(locations, parent):
        if location.name == namePath[0]:
            section = location

    if section is not None:
        if len(namePath) == 1:
            return section
        return getLocationFromNames(locations, namePath[1:], parent)
    return None

def newLocation(name: str, parent: str | None) -> Location:
    return Location(name, str(uuid.uuid4()), parent)

def getChildren(locations: list[Location], parent: Location | str | None) -> list[Location]:
    if parent is None:
        return [loc for loc in locations if loc.parent is None]
    if isinstance(parent, str):
        parent = getLocation(locations, parent)
    return [loc for loc in locations if loc.parent and loc.parent == parent.id]

def sortLocations(locations: list[Location], parent: Location | None = None):
    
    def sortComparator(x1: Location, x2: Location):
        return (x1.name.lower() > x2.name.lower()) - (x1.name.lower() < x2.name.lower())

    out: list[Location] = []
    locs = getChildren(locations, parent)
    locs = sorted(locs, key=cmp_to_key(sortComparator))
    for loc in locs:
        out.append(loc)
        out.extend(sortLocations(locations, loc))
    return out

def isDuplicateNameWithinParent(
    locations: list[Location],
    name: str,
    parent: Location | str | None,
) -> bool:
    """Check if the name already exists within the same parent location."""
    if type(parent) == str:
        parent = getLocation(locations, parent)
    for location in getChildren(locations, parent):
        if location.name == name:
            return True
    return False
