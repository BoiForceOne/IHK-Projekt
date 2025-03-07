from typing import Any
import uuid
from state import Location, Settings


def getLocationPath(locations: list[Location], uid: str) -> list[int] | None:
    """Converts a location uid to a path."""
    for idx, location in enumerate(locations):
        if location.id == uid:
            return [idx]
        path = getLocationPath(location.children, uid)
        if path is not None:
            return [idx] + path
    return None

def keepTopParents(selectedLocations: list[Location]) -> list[Location]:
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
            if isSomeParent(l2, l1):
                child = True
        if not child:
            result.append(l1)
    return result


def isSomeParent(parent: Location, child: Location) -> bool:
    """Checks if the child is a child of the parent."""
    while child.parent is not None:
        if child.parent == parent:
            return True
        child = child.parent
    return False

def getLocation(locations: list[Location], id: str) -> Location:
    """Converts a location uid to a location."""
    location = getLocationRec(locations, id)
    if location is not None:
        return location
    raise ValueError(f"Location with id {id} not found.")


def getLocationRec(locations: list[Location], id: str) -> Location | None:
    for location in locations:
        if location.id == id:
            return location
        child = getLocationRec(location.children, id)
        if child is not None:
            return child
    return None


def getLocationFromPath(locations: list[Location], path: list[int]) -> Location:
    if len(path) == 0:
        raise ValueError("Location from path not found.")
    return getLocationFromPath(locations[path[0]].children, path[1:])


def getLocationString(locations: list[Location], uid: str) -> str:
    path = getLocationPath(locations, uid)
    if path is None:
        return ""
    strings = getLocationStrings(locations, path)
    return " > ".join(strings)


def getLocationStrings(locations: list[Location], path: list[int]) -> list[str]:
    if len(path) == 0:
        return []
    return [locations[path[0]].name] + getLocationStrings(
        locations[path[0]].children, path[1:]
    )


def getLocationFromNames(
    locations: list[Location], namePath: list[str] | None
) -> Location | None:
    """Converts a name path to a location."""
    if namePath is None:
        return None
    section = None
    for location in locations:
        if location.name == namePath[0]:
            section = location

    if section is not None:
        if len(namePath) == 1:
            return section
        return getLocationFromNames(section.children, namePath[1:])
    return None


def dictToLocation(name: str, children: Any, parent: Location | None) -> Location:
    """Maps a subsection from the configuration file to a SubLocation object."""
    assert type(name) == str and name != ""
    assert type(children) == dict
    assert "id" in children
    id: Any = children["id"]
    assert type(id) == str and id != ""
    location: Location = Location(name, id, [], parent)
    childName: Any
    child: Any
    for childName, child in children.items():
        assert type(childName) == str and childName != ""
        if childName == "id":
            continue
        assert type(child) == dict
        location.children.append(dictToLocation(childName, child, location))
    return location


def dictToLocations(locations: Any) -> list[Location]:
    """Maps the locations from the configuration file to a list of Location objects."""
    sections: list[Location] = []
    for name, children in locations.items():
        assert type(name) == str and name != ""
        assert type(children) == dict
        sections.append(dictToLocation(name, children, None))
    return sections


def tryDictToLocations(locations: Any) -> list[Location]:
    """Tries to map the locations from the configuration file to a list of Location objects."""
    try:
        return dictToLocations(locations)
    except Exception as e:
        print(f"[Error] Could not map locations: {e}")
        return []


def settingsToDict(settings: Settings) -> dict[str, Any]:
    return {
        "filePath": settings.filePath,
        "language": settings.language,
        "persistScannedIDs": settings.persistScannedIDs,
        "unitSystem": settings.unitSystem,
    }


def storageToDict(
    storageLocations: list[Location], parent: Location | None = None
) -> dict[str, Any]:
    storageDict: dict[str, Any] = {}
    if parent is not None:
        storageDict["id"] = parent.id
    for location in storageLocations:
        storageDict[location.name] = storageToDict(location.children, location)

    return storageDict

def newLocation(name: str, parent: Location | None) -> Location:
    return Location(name, str(uuid.uuid4()), [], parent)

def isDuplicateNameWithinParent(
    locations: list[Location],
    name: str,
    parent: Location | None,
) -> bool:
    """Check if the name already exists within the same parent location."""
    if parent is not None:
        locations = parent.children
    for location in locations:
        if location.name == name:
            return True
    return False
