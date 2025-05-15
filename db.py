from dataclasses import dataclass
import json
import os
import pandas as pd

from consts import *
from location import getChildren, parseLocations, serializeLocations
from state import DBInfo, Data, Location, State


def saveToExel(data: Data, filePath: str):
    """
    Saves the ``panda.Dataframe`` in the data to an excel file to the given path.

    Parameters
    ----------
    data : The data to be saved
    filePath : The path to the file
    """
    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:
        # to_excel is not properly typed
        serializeDBInfo(data.info).to_excel(writer, sheet_name=INFO_SHEET, index=False)  # type: ignore
        data.df.to_excel(writer, sheet_name=DATA_SHEET, index=False)  # type: ignore
        serializeLocations(data.locations).to_excel(writer, sheet_name=LOCATION_SHEET, index=False)  # type: ignore


def serializeDBInfo(info: DBInfo) -> pd.DataFrame:
    """
    Serializes the DBInfo object to a pandas DataFrame.
    """
    return pd.DataFrame(
        [
            [INFO_VERSION_KEY, info.version],
        ],
        columns=[INFO_KEY_COLUMN, INFO_VALUE_COLUMN],
    )


def reloadFromFile(data: Data, filePath: str):
    """
    Reloads the data from the given file path.

    Updates references inside the data struct using the ``db.changeDataTo()`` method.
    This means that the reference to the data struct is still valide, enabling seamless reloading of the data.

    Copys like the ``db.Row`` abstraction do not update.

    Throws a ValueError if the file could not be read or if the columns are invalid.

    Parameters
    ----------
    data : The data to be updated
    filePath : The path of the file
    """
    newData = newDataFromExel(filePath)
    __changeDataTo(data, newData, False)


def __changeDataTo(data: Data, to: Data, changeScannedIDs: bool = True):
    """
    Updates references inside the data struct to the new data.
    This means that the reference to the data struct is still valide, enabling seamless reloading of the data.

    Copys like the ``db.Row`` abstraction do not update.

    Parameters
    ----------
    data : The data struct to be updated
    to : The data struct containing the new contents
    """
    if changeScannedIDs:
        data.scannedIDs = to.scannedIDs
        data.anzahlScannedItems = to.anzahlScannedItems
    data.df = to.df
    data.tableHeaders = to.tableHeaders
    data.dataHeaders = to.dataHeaders
    for toLoc in to.locations:
        for dataLoc in data.locations:
            if toLoc.id == dataLoc.id:
                toLoc.expanded = dataLoc.expanded
                break
    data.locations = to.locations


@dataclass
class Row:
    """
    Row is a replica of the data for a row in the data struct.

    When changes are made to the values or the scanCount,
    Call the ``Row.write(Data)`` method to write the changes to the data struct and database.
    If you only changed values not saved in the database (e.g. scanCount), you can call ``Row.writeNoValues(Data)`` instead.

    Setting scanCount to 0 will remove the entry from the scanned IDs list upon writing.
    Setting it to a value > 0 will add the entry to the scanned IDs list upon writing.

    Parameters
    ----------
    values : The values of the row
    dataHeaders : The headers of the database table
        Can only be read, do not modify.
    scanCount : The amount of times the row was scanned
    """

    values: list[int | str]
    _dataHeaders: list[str]
    scanCount: int

    @property
    def dataHeaders(self) -> list[str]:
        return self._dataHeaders

    def setValue(self, header: str, value: int | str):
        if header == ID_COLUMN:
            self.values[headerIndex(self.dataHeaders, header)] = int(value)
        else:
            self.values[headerIndex(self.dataHeaders, header)] = (
                "" if value == "nan" else str(value)
            )

    def getValue(self, header: str) -> str:
        """
        Returns the value in the columns with the header in the row.
        Return an empty string if the value was not present.

        :param header: The header of the column

        :return: The value of the header in the row as a str
        """
        value = str(self.values[headerIndex(self.dataHeaders, header)])
        return value if value != "nan" else ""

    def id(self):
        return int(self.values[headerIndex(self.dataHeaders, ID_COLUMN)])

    def code(self):
        return self.getValue(CODE_COLUMN)

    def empty(self):
        return len(self.values) == 0

    def write(self, data: Data, path: str):
        """
        Writes the values to the database and updates the scannedIDs and anzahlScannedItems dicts.

        :param data: The data struct that holds the dataframe and the scannedIDs and anzahlScannedItems dicts
        """
        self.writeNoValues(data)
        reloadFromFile(data, path)
        dfRow: pd.DataFrame = data.df.loc[data.df[ID_COLUMN] == self.id()]
        if dfRow.empty:
            data.df = pd.concat(
                [data.df, pd.DataFrame([self.values], columns=data.dataHeaders)],
                ignore_index=True,
            )
        else:
            data.df.loc[data.df[ID_COLUMN] == self.id()] = self.values
        saveToExel(data, path)

    def writeNoValues(self, data: Data):
        """
        Updates the scannedIDs and anzahlScannedItems dicts without writing the values to the database.

        :param data: The data struct that holds the dataframe and the scannedIDs and anzahlScannedItems dicts
        """
        if self.isScanned():
            if not self.id() in data.scannedIDs:
                data.scannedIDs.append(self.id())
            data.anzahlScannedItems[self.id()] = self.scanCount
        else:
            data.scannedIDs.remove(self.id())
            data.anzahlScannedItems.pop(self.id())

    def isScanned(self) -> bool:
        """
        Returns whether the entry should be in the scanned IDs list.

        This is based on the scanCount. Read the documentation of the ``Row`` class for more information.
        """
        return self.scanCount > 0

    def delete(self, data: Data, path: str) -> bool:
        """
        Deletes the entry from the database.
        Returns true if the entry was deleted from the database successfully, otherwise false.
        """
        reloadFromFile(data, path)
        try:
            # Remove the row from the DataFrame
            data.df = data.df[data.df[ID_COLUMN] != self.id()]
            # Update the scannedIDs and anzahlScannedItems
            if self.id() in data.scannedIDs:
                data.scannedIDs.remove(self.id())
            data.anzahlScannedItems.pop(self.id(), None)
            # Save the updated DataFrame to the Excel file
            saveToExel(data, SETTINGS_FILE_PATH)
            return True
        except Exception as e:
            print(f"Error deleting row: {e}")
            return False


def clearScanned(data: Data):
    data.scannedIDs.clear()


def newDataFromExel(filePath: str) -> Data:
    """
    Creates a new Data struct from the given excel file.
    Throws a ValueError if the file could not be read or if the columns are invalid.
    """
    # read_excel is not properly typed
    if not os.path.exists(filePath):
        raise ValueError("Datei wurde nicht gefunden.")
    try:
        infoSheet: pd.DataFrame = pd.read_excel(filePath, sheet_name=INFO_SHEET, dtype={INFO_KEY_COLUMN: str, INFO_VALUE_COLUMN: str})  # type: ignore
    except Exception:
        raise ValueError("Diese Datenbank/Excel hat keine Version (altes Format)")
    info = parseDBInfo(infoSheet)
    if info.version != REQUIRED_DB_VERSION:
        raise ValueError(
            f"Diese Datenbank/Excel hat die falsche Version. Benötigte Version: {REQUIRED_DB_VERSION}. Vorhandene Version: {info.version}."
        )

    try:
        df: pd.DataFrame = pd.read_excel(filePath, sheet_name=DATA_SHEET, dtype={ID_COLUMN: int, CODE_COLUMN: str, "Bestellnummer": str, STORED_AMOUNT_COLUMN: int})  # type: ignore
        locationSheet: pd.DataFrame = pd.read_excel(filePath, sheet_name=LOCATION_SHEET, dtype={LOCATION_ID_COLUMN: str, LOCATION_NAME_COLUMN: str, LOCATION_PARENT_COLUMN: str})  # type: ignore
    except Exception:
        raise ValueError("Datei konnte nicht gelesen werden.")
    # Add and remove the columns that shoud be displayed in the table
    locations = parseLocations(locationSheet)
    data = Data(
        tableHeaders=list(df.columns),
        dataHeaders=list(df.columns),
        scannedIDs=[],
        anzahlScannedItems={},
        df=df,
        locations=locations,
        info=info,
    )
    if not validateColumns(data):
        raise ValueError("Die Spalten in der Excel-Datei sind ungültig.")
    data.tableHeaders.remove(ID_COLUMN)
    data.tableHeaders.append(EDIT_COLUMN)
    data.tableHeaders.append(DELETE_COLUMN)
    data.tableHeaders.append(COUNT_COLUMN)
    return data


def parseDBInfo(infoSheet: pd.DataFrame) -> DBInfo:
    version = infoSheet.loc[
        infoSheet[INFO_KEY_COLUMN] == INFO_VERSION_KEY, INFO_VALUE_COLUMN
    ].values[0]
    return DBInfo(version)


def validateColumns(data: Data):
    """
    Checks that all required columns are present in the data and no special columns are already present.
    Returns True if all requirements are met, False otherwise.
    """
    # Required columns
    for column in [ID_COLUMN, CODE_COLUMN, TYPE_COLUMN]:
        if column not in data.dataHeaders:
            return False
    # Forbidden columns
    for column in [DELETE_COLUMN, EDIT_COLUMN, COUNT_COLUMN]:
        if column in data.tableHeaders:
            return False
    return True


def loadIDsAndCount(data: Data, filePath: str):
    try:
        with open(SCANNED_IDS_FILE_PATH, "r", encoding="utf-8") as f:
            countOfIdsJson: dict[str, int] = json.load(f)
            countOfIds: dict[int, int] = {}
            for id, count in countOfIdsJson.items():
                countOfIds[int(id)] = count

            data.anzahlScannedItems = countOfIds
            data.scannedIDs = list(countOfIds.keys())
    # If the file does not exist, or there is any error parsing it, just ignore it
    # It will be overriden when closing the program
    except Exception as e:
        print(f"[Error] Could not load scanned IDs from file: {e}")
        pass


def saveScannedIDs(data: Data, filePath: str):
    with open("scannedIDs.json", "w", encoding="utf-8") as f:
        syncIdsWithCount(data)
        json.dump(data.anzahlScannedItems, f)


def headerIndex(headers: list[str], header: str) -> int:
    return headers.index(header)


def newRow(data: Data, id: int) -> Row:
    if id not in data.df[ID_COLUMN].to_list():
        raise ValueError(f"ID {id} not found in data")
    return Row(
        list(data.df.loc[data.df[ID_COLUMN] == id].values[0]),  # type: ignore
        data.dataHeaders,
        data.scanCount(id),  # type: ignore
    )


def newRowFromIndex(data: Data, index: int) -> Row:
    return newRow(data, data.scannedIDs[index])


def newRowFromCode(data: Data, code: str) -> Row:
    id: pd.Series[int] = data.df.loc[data.df[CODE_COLUMN] == code][ID_COLUMN]
    if id.empty:
        return Row([], data.dataHeaders, 0)
    return newRow(data, id.values[0])


def validateIDs(data: Data):
    for id in data.scannedIDs:
        if id not in data.df[ID_COLUMN].to_list():
            data.scannedIDs.remove(id)
            data.anzahlScannedItems.pop(id)


def syncIdsWithCount(data: Data):
    # Initialize all IDs in the scannedIDs list with a count of 0 that are not in scannedIDs
    for id in data.scannedIDs:
        if id not in data.anzahlScannedItems:
            data.anzahlScannedItems[id] = 1

    # Remove all IDs from the anzahlScannedItems dict that are not in the scannedIDs list
    keys = list(data.anzahlScannedItems.keys())
    for i in reversed(range(len(data.anzahlScannedItems))):
        if keys[i] not in data.scannedIDs:
            data.anzahlScannedItems.pop(keys[i])


def newDfWithScannedIDs(data: Data) -> pd.DataFrame:
    return data.df[data.df[ID_COLUMN].isin(data.scannedIDs)]  # type: ignore


from typing import List, TypeVar

T = TypeVar("T")


def check_list_type(items: List[T], expected_type: type) -> bool:
    return all(isinstance(item, expected_type) for item in items)


def getSearchableStrings(data: Data) -> list[str]:
    idCol: list[int] = data.df[ID_COLUMN].to_list()
    strings: list[str] = []
    for id in idCol:
        row = newRow(data, id)
        type = row.getValue(TYPE_COLUMN)
        dec = row.getValue(DESC_COLUMN)
        ident = row.getValue(IDENT_COLUMN)
        if type == "" and dec == "" and ident == "":
            continue
        s = f"{id}: {type}, {dec}, {ident}"
        strings.append(s)  # type: ignore
    return strings


def addLocation(state: State, location: Location):
    reloadFromFile(state.data, state.settings.filePath)
    state.data.locations.append(location)
    saveToExel(state.data, state.settings.filePath)


def removeLocation(state: State, location: Location):
    reloadFromFile(state.data, state.settings.filePath)
    [
        removeLocation(state, child)
        for child in getChildren(state.data.locations, location)
    ]
    state.data.locations.remove(location)
    saveToExel(state.data, state.settings.filePath)


def removeLocationById(state: State, id: str):
    reloadFromFile(state.data, state.settings.filePath)
    [removeLocation(state, child) for child in getChildren(state.data.locations, id)]
    state.data.locations = [loc for loc in state.data.locations if loc.id != id]
    saveToExel(state.data, state.settings.filePath)


def renameLocation(state: State, location: Location, newName: str):
    reloadFromFile(state.data, state.settings.filePath)
    location.name = newName
    saveToExel(state.data, state.settings.filePath)
