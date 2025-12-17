#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modus_config.py - Zentrale Konfiguration für Modi-GUI-Labels

Dieses Modul definiert alle GUI-Labels für die Modi und ihre Mappings.
Dies sind die Master-Definitionen für die GUI-Darstellung.

WICHTIG: Umlaute (ä, ö, ü) sind in GUI-Labels erlaubt und erwünscht!
"""

from typing import List, Dict

# ================================================================================================
# GUI-LABELS FÜR MODI (Master-Definitionen)
# ================================================================================================

# GUI-Labels in der Reihenfolge wie sie in der ComboBox erscheinen
MODUS_GUI_LABELS: List[str] = [
    "OV + Stärke",
    "Ort + Stärke",
    "Schreiblinie + Stärke",
    "Schreiblinie oder Freitext",  # FIXED: Tippfehler "ooder" -> "oder"
    "Ruf",
    "Dateiname",
    "Nur Grafik"
]

# Mapping: GUI-Label → Interner Wert (constants.py)
MODUS_GUI_TO_INTERNAL: Dict[str, str] = {
    "OV + Stärke": "ov_staerke",
    "Ort + Stärke": "ort_staerke",
    "Schreiblinie + Stärke": "schreiblinie_staerke",
    "Schreiblinie oder Freitext": "freitext",
    "Ruf": "ruf",
    "Dateiname": "dateiname",
    "Nur Grafik": "ohne_text"
}

# Mapping: Interner Wert → GUI-Label (für Anzeige)
MODUS_INTERNAL_TO_GUI: Dict[str, str] = {
    "ov_staerke": "OV + Stärke",
    "ort_staerke": "Ort + Stärke",
    "schreiblinie_staerke": "Schreiblinie + Stärke",
    "freitext": "Schreiblinie oder Freitext",
    "ruf": "Ruf",
    "dateiname": "Dateiname",
    "ohne_text": "Nur Grafik"
}

# Platzhalter-Texte für Textfeld (pro Modus)
MODUS_PLACEHOLDER_TEXT: Dict[str, str] = {
    "ov_staerke": "OV-Name",
    "ort_staerke": "Ort-Name",
    "schreiblinie_staerke": "(Schreiblinie)",
    "freitext": "Freitext",
    "ruf": "Rufname",
    "dateiname": "Dateiname (automatisch)",
    "ohne_text": ""
}

# ================================================================================================
# HELPER-FUNKTIONEN
# ================================================================================================

def get_modus_gui_labels() -> List[str]:
    """
    Gibt GUI-Labels für Modus-ComboBox zurück

    Returns:
        list: GUI-Labels in korrekter Reihenfolge
    """
    return MODUS_GUI_LABELS.copy()


def gui_to_internal(gui_label: str) -> str:
    """
    Konvertiert GUI-Label zu internem Modus-Wert

    Args:
        gui_label: GUI-Label (z.B. "OV + Stärke")

    Returns:
        str: Interner Wert (z.B. "ov_staerke"), Fallback: "ov_staerke"
    """
    return MODUS_GUI_TO_INTERNAL.get(gui_label, "ov_staerke")


def internal_to_gui(internal_value: str) -> str:
    """
    Konvertiert internen Modus-Wert zu GUI-Label

    Args:
        internal_value: Interner Wert (z.B. "ov_staerke")

    Returns:
        str: GUI-Label (z.B. "OV + Stärke"), Fallback: "OV + Stärke"
    """
    return MODUS_INTERNAL_TO_GUI.get(internal_value, "OV + Stärke")


def get_placeholder_text(internal_value: str) -> str:
    """
    Gibt Platzhalter-Text für Textfeld zurück

    Args:
        internal_value: Interner Modus-Wert (z.B. "ov_staerke")

    Returns:
        str: Platzhalter-Text (z.B. "OV-Name"), Fallback: "Eingabefeld"
    """
    return MODUS_PLACEHOLDER_TEXT.get(internal_value, "Eingabefeld")


# ================================================================================================
# TESTING
# ================================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Modus-Config Test")
    print("=" * 80)

    print("\n[GUI-Labels]")
    for label in get_modus_gui_labels():
        print(f"  - {label}")

    print("\n[GUI -> Internal Mapping]")
    for gui_label in MODUS_GUI_LABELS:
        internal = gui_to_internal(gui_label)
        print(f"  '{gui_label}' -> '{internal}'")

    print("\n[Internal -> GUI Mapping]")
    for internal in MODUS_INTERNAL_TO_GUI.keys():
        gui_label = internal_to_gui(internal)
        print(f"  '{internal}' -> '{gui_label}'")

    print("\n[Platzhalter-Texte]")
    for internal, placeholder in MODUS_PLACEHOLDER_TEXT.items():
        print(f"  '{internal}' -> '{placeholder}'")

    print("\n" + "=" * 80)
