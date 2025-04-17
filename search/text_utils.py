def create_synthetic_text(report):
    parts = []

    # Report-level info
    if report.get("serious"):
        seriousness = "Case was serious"
        outcomes = []
        if report.get("seriousnessdeath"):
            outcomes.append('death')
        if report.get("seriousnesslifethreatining"):
            seriousness = "serious and life-threatening"
        if report.get("seriousnesshospitalization"):
            outcomes.append('hospitalization')
        if report.get("seriousnessdisabling"):
            outcomes.append('disability')
        if report.get("seriousnesscongenitalanomali"):
            outcomes.append('congenital anomali')
        if report.get("seriousnessother"):
            outcomes.append('other outcomes')
        if outcomes:
            seriousness = ', resulting in '.join([seriousness, ', '.join(outcomes)])
        parts.append(f'{seriousness}.')
    else:
        parts.append('Case was non-serious.')
    if report.get("patientonsetage"):
        parts.append(f"Patient age: {report.get('patientonsetage')}.")
    if report.get("patientsex") == 1:
        parts.append("Patient sex: Male.")
    elif report.get("patientsex") == 2:
        parts.append("Patient sex: Female.")
    if report.get("patientweight"):
        parts.append(f"Patient weight: {report.get('patientweight')}")

    # Reactions and drugs
    if report["reactions"]:
        parts.append("Reactions: " + ", ".join(report.get("reactions")) + ".")
    if report["drugnames"]:
        parts.append("Drugs: " + ", ".join(report.get("drugnames")) + ".")

    return " ".join(parts)