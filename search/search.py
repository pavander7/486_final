from search_functions import search_reports, get_characterizations, get_drugid_name_mapping, get_reactions_and_seriousness

def execute_query(drugnames):
    """Execute semantic query over ES, enrich with metadata and drug characterization info."""

    drugnames = [d.lower() for d in drugnames]
    name_to_drugid = get_drugid_name_mapping()
    target_drugids = {name_to_drugid[name] for name in drugnames if name in name_to_drugid}

    results = search_reports(drugnames)
    
    strong_reports = []
    all_reactions = []

    for entry in results:
        reportid = entry["reportid"]
        serious, reactions = get_reactions_and_seriousness(reportid)
        char_map = get_characterizations(reportid)

        in_relevant = {drugid for drugid, char in char_map.items() if drugid in target_drugids and char == 1}
        
        entry["serious"] = serious
        entry["reactions"] = reactions
        entry["char_match"] = len(in_relevant) > 0  # True if any queried drug is a likely cause

        if entry["char_match"]:
            all_reactions.extend(reactions)
            strong_reports.append(entry)

    from collections import Counter
    top_reactions = dict(Counter(all_reactions).most_common(10))

    return results, top_reactions, len(strong_reports), sum(r["serious"] for r in strong_reports)