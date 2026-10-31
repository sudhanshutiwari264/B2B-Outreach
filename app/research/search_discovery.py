from app.integrations.schemas import SearchQuerySpec
from app.schemas.prospect import ProspectCreate


def _dedupe(specs: list[SearchQuerySpec]) -> list[SearchQuerySpec]:
    seen: set[str] = set()
    deduped: list[SearchQuerySpec] = []
    for spec in specs:
        key = spec.query.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(spec)
    return deduped


def generate_linkedin_queries(prospect: ProspectCreate) -> list[SearchQuerySpec]:
    name, company = prospect.name, prospect.company
    specs = [
        SearchQuerySpec(
            query=f'site:linkedin.com/in/ "{name}" "{company}"',
            category_hint="linkedin_profile",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'site:linkedin.com/posts/ "{name}" "{company}"',
            category_hint="linkedin_post",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{name}" "{company}" {prospect.designation}',
            category_hint="linkedin_profile",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{name}" {company} promoted OR "new role" OR appointed',
            category_hint="job_change",
            max_results=5,
        ),
    ]
    return _dedupe(specs)


def generate_company_queries(prospect: ProspectCreate) -> list[SearchQuerySpec]:
    company = prospect.company
    specs = [
        SearchQuerySpec(
            query=f'"{company}" funding round OR raises OR "Series A" OR "Series B" OR "Series C"',
            category_hint="funding",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{company}" announces OR announcement OR launches',
            category_hint="company_news",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{company}" hiring OR "is hiring" OR careers OR "open roles"',
            category_hint="hiring",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{company}" partnership OR partners with',
            category_hint="partnership",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{company}" expansion OR "new office" OR "new market"',
            category_hint="company_growth",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{company}" layoffs OR challenges OR restructuring',
            category_hint="business_challenge",
            max_results=5,
        ),
    ]
    if prospect.industry:
        specs.append(
            SearchQuerySpec(
                query=f'"{company}" {prospect.industry} industry news',
                category_hint="industry_development",
                max_results=5,
            )
        )
    return _dedupe(specs)


def generate_professional_queries(prospect: ProspectCreate) -> list[SearchQuerySpec]:
    name, company = prospect.name, prospect.company
    specs = [
        SearchQuerySpec(
            query=f'"{name}" {company} interview',
            category_hint="interview",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{name}" {company} podcast',
            category_hint="podcast",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{name}" {company} conference OR keynote OR speaker',
            category_hint="public_speaking",
            max_results=5,
        ),
        SearchQuerySpec(
            query=f'"{name}" {prospect.designation} {company} article OR opinion',
            category_hint="thought_leadership",
            max_results=5,
        ),
    ]
    return _dedupe(specs)


def generate_all_queries(prospect: ProspectCreate) -> dict[str, list[SearchQuerySpec]]:
    return {
        "linkedin": generate_linkedin_queries(prospect),
        "company": generate_company_queries(prospect),
        "professional": generate_professional_queries(prospect),
    }


def generate_alternative_query(original: SearchQuerySpec, attempt: int) -> SearchQuerySpec:
    """Bounded alternative query formulations for EC-06 (Tavily returns zero results).

    attempt is 1-indexed; callers should stop after a small fixed number of attempts.
    """
    stripped = original.query.replace('"', "")
    if attempt == 1:
        new_query = stripped
    elif attempt == 2:
        new_query = " ".join(stripped.split()[:6])
    else:
        new_query = stripped.split(" OR ")[0]
    return SearchQuerySpec(
        query=new_query, category_hint=original.category_hint, max_results=original.max_results
    )
