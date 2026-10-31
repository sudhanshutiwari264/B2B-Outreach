from app.schemas.prospect import ProspectCreate, ProspectIdentityCheck


def validate_prospect_identity(prospect: ProspectCreate) -> ProspectIdentityCheck:
    """Pre-research identity check (EC-03 / EC-11): refuse to research a prospect we
    cannot plausibly identify uniquely rather than guessing and attaching the wrong
    person's facts to this prospect record.
    """
    missing: list[str] = []

    name_parts = [p for p in prospect.name.strip().split() if p]
    if len(name_parts) < 2:
        missing.append("name")
        return ProspectIdentityCheck(
            is_identifiable=False,
            reason=(
                "Name does not appear to include both a first and last name, which makes "
                "it unsafe to uniquely identify this person via public search."
            ),
            missing_fields=missing,
        )

    if len(prospect.company.strip()) < 2:
        missing.append("company")

    if missing:
        return ProspectIdentityCheck(
            is_identifiable=False,
            reason="Required identifying fields are missing or too short to disambiguate the prospect.",
            missing_fields=missing,
        )

    generic_single_word_companies = {"the", "inc", "llc", "corp", "company", "co"}
    if prospect.company.strip().lower() in generic_single_word_companies:
        return ProspectIdentityCheck(
            is_identifiable=False,
            reason="Company name is too generic to disambiguate the prospect.",
            missing_fields=["company"],
        )

    return ProspectIdentityCheck(is_identifiable=True)
