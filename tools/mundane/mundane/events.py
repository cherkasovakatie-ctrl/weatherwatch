"""Hand-picked reference events for orienting the timeline (not a test sample)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldEvent:
    date: str
    category: str  # war · political · economic · independence · health
    event: str
    region: str


WORLD_EVENTS: tuple[WorldEvent, ...] = (
    WorldEvent("1914-07-28", "war", "First World War begins", "Europe"),
    WorldEvent("1917-11-07", "political", "Bolshevik revolution", "Russia"),
    WorldEvent("1918-11-11", "war", "Armistice ends the First World War", "Europe"),
    WorldEvent("1929-10-29", "economic", "Wall Street crash (Black Tuesday)", "USA"),
    WorldEvent("1933-01-30", "political", "Hitler appointed German chancellor", "Germany"),
    WorldEvent("1939-09-01", "war", "Germany invades Poland; Second World War begins", "Europe"),
    WorldEvent("1941-12-07", "war", "Attack on Pearl Harbor", "USA / Japan"),
    WorldEvent("1945-09-02", "war", "Japan surrenders; Second World War ends", "Global"),
    WorldEvent("1947-08-15", "independence", "Independence and partition of India", "South Asia"),
    WorldEvent("1948-05-14", "independence", "State of Israel declared", "Middle East"),
    WorldEvent("1949-10-01", "political", "People's Republic of China proclaimed", "China"),
    WorldEvent("1950-06-25", "war", "Korean War begins", "Korea"),
    WorldEvent("1956-10-29", "war", "Suez Crisis", "Middle East"),
    WorldEvent("1962-10-16", "war", "Cuban Missile Crisis begins", "USA / USSR / Cuba"),
    WorldEvent("1971-08-15", "economic", "US ends dollar–gold convertibility", "Global"),
    WorldEvent("1973-10-17", "economic", "OPEC oil embargo", "Global"),
    WorldEvent("1979-02-11", "political", "Iranian Revolution", "Iran"),
    WorldEvent("1979-12-24", "war", "Soviet intervention in Afghanistan", "Afghanistan"),
    WorldEvent("1987-10-19", "economic", "Black Monday stock crash", "Global"),
    WorldEvent("1989-11-09", "political", "Fall of the Berlin Wall", "Germany"),
    WorldEvent("1990-08-02", "war", "Iraq invades Kuwait", "Middle East"),
    WorldEvent("1991-08-24", "independence", "Ukraine declares independence", "Ukraine"),
    WorldEvent("1991-12-26", "political", "Soviet Union dissolved", "USSR"),
    WorldEvent("1997-07-02", "economic", "Asian financial crisis begins (baht floated)", "Asia"),
    WorldEvent("1998-08-17", "economic", "Russian debt default", "Russia"),
    WorldEvent("2000-03-10", "economic", "Dot-com bubble peaks (Nasdaq)", "USA"),
    WorldEvent("2001-09-11", "war", "September 11 attacks", "USA"),
    WorldEvent("2003-03-20", "war", "Invasion of Iraq", "Middle East"),
    WorldEvent("2008-09-15", "economic", "Lehman Brothers collapses", "Global"),
    WorldEvent("2010-12-17", "political", "Arab Spring begins in Tunisia", "Middle East / N Africa"),
    WorldEvent("2014-03-18", "war", "Russia annexes Crimea", "Ukraine"),
    WorldEvent("2016-06-23", "political", "UK votes to leave the EU", "United Kingdom"),
    WorldEvent("2020-03-11", "health", "WHO declares COVID-19 a pandemic", "Global"),
    WorldEvent("2022-02-24", "war", "Russia's full-scale invasion of Ukraine", "Ukraine"),
    WorldEvent("2023-10-07", "war", "Hamas attack on Israel; Gaza war begins", "Middle East"),
)
