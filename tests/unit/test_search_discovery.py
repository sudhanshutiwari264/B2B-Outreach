from app.research.search_discovery import (
    generate_alternative_query,
    generate_all_queries,
    generate_company_queries,
    generate_linkedin_queries,
    generate_professional_queries,
)
from app.schemas.prospect import ProspectCreate

PROSPECT = ProspectCreate(
    name="Jane Doe", company="Acme Corp", designation="VP of Engineering", industry="SaaS"
)


def test_generate_linkedin_queries_includes_profile_and_posts_scopes():
    queries = [q.query for q in generate_linkedin_queries(PROSPECT)]
    assert any("site:linkedin.com/in/" in q for q in queries)
    assert any("site:linkedin.com/posts/" in q for q in queries)
    assert all("Jane Doe" in q for q in queries)


def test_generate_company_queries_cover_distinct_categories():
    specs = generate_company_queries(PROSPECT)
    hints = {s.category_hint for s in specs}
    assert {"funding", "company_news", "hiring", "partnership", "company_growth", "business_challenge"} <= hints


def test_generate_professional_queries_cover_interview_and_podcast():
    specs = generate_professional_queries(PROSPECT)
    hints = {s.category_hint for s in specs}
    assert {"interview", "podcast", "public_speaking", "thought_leadership"} <= hints


def test_generate_all_queries_are_deduplicated_per_category():
    all_queries = generate_all_queries(PROSPECT)
    for category, specs in all_queries.items():
        queries_lower = [s.query.strip().lower() for s in specs]
        assert len(queries_lower) == len(set(queries_lower)), f"duplicates found in {category}"


def test_generate_alternative_query_produces_progressively_simpler_queries():
    original = generate_linkedin_queries(PROSPECT)[0]
    alt1 = generate_alternative_query(original, 1)
    alt2 = generate_alternative_query(original, 2)
    alt3 = generate_alternative_query(original, 3)
    assert '"' not in alt1.query
    assert len(alt2.query.split()) <= 6
    assert alt3.category_hint == original.category_hint
