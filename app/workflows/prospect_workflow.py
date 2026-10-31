import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.integrations.tarqa_client import TarqaClient, TarqaIntegrationError, TarqaNotConfiguredError
from app.integrations.tavily_client import TavilyClient, TavilyIntegrationError, TavilyNotConfiguredError
from app.intelligence.conflict_detector import SignalForConflictCheck, detect_conflicts
from app.intelligence.signal_classifier import entity_matches_prospect, parse_published_at
from app.intelligence.signal_extractor import extract_signals_from_source
from app.intelligence.signal_ranker import RankableSignal, score_signal, select_top_signals
from app.logging_config import get_logger
from app.models.enums import (
    ConflictResolutionStatus,
    DraftStatus,
    ExecutionStatus,
    ExtractionStatus,
    OutreachChannel,
    VerificationStatus,
    WorkflowStage,
)
from app.models.conflict import SignalConflict
from app.models.draft import OutreachDraft
from app.models.execution import Execution
from app.models.log import ExecutionLog
from app.models.prospect import Prospect
from app.models.signal import Signal
from app.models.source import ResearchSource
from app.outreach.email_generator import generate_email_draft
from app.outreach.linkedin_generator import generate_linkedin_draft
from app.outreach.outreach_validator import validate_draft
from app.outreach.strategy_generator import generate_strategy
from app.research.company_research import run_company_research
from app.research.content_cleaner import clean_text
from app.research.content_extractor import extract_content_for_urls
from app.research.linkedin_research import run_linkedin_research
from app.research.public_web_research import run_professional_research
from app.research.source_validator import ValidatedSource, build_validated_sources, deduplicate_search_results
from app.schemas.prospect import ProspectCreate
from app.validation.evidence_validator import select_best_usable_signal
from app.validation.prospect_validator import validate_prospect_identity
from app.workflows.stage_logger import stage

logger = get_logger(__name__)

MAX_URLS_TO_EXTRACT = 25


class _SignalLikeForSelection:
    __slots__ = ("id", "is_disputed", "relevance_tier", "evidence_excerpt", "final_score")

    def __init__(self, signal: Signal):
        self.id = signal.id
        self.is_disputed = signal.is_disputed
        self.relevance_tier = signal.relevance_tier
        self.evidence_excerpt = signal.evidence_excerpt
        self.final_score = signal.final_score


async def _finalize(
    db: AsyncSession,
    execution: Execution,
    status: ExecutionStatus,
    *,
    failure_reason: Optional[str] = None,
    result_summary: Optional[dict] = None,
) -> None:
    execution.status = status
    execution.failure_reason = failure_reason
    execution.completed_at = datetime.now(timezone.utc)
    execution.result_summary = result_summary
    await db.commit()


async def run_prospect_workflow(
    db: AsyncSession,
    execution_id: uuid.UUID,
    *,
    tavily: Optional[TavilyClient] = None,
    tarqa: Optional[TarqaClient] = None,
) -> None:
    """End-to-end orchestration of the research -> intelligence -> outreach pipeline for
    one execution, persisting every stage's result and handling all documented edge cases
    rather than letting failures propagate silently.
    """
    tavily = tavily or TavilyClient()
    tarqa = tarqa or TarqaClient()

    execution = await db.get(Execution, execution_id)
    if execution is None:
        logger.error("workflow.execution_not_found", execution_id=str(execution_id))
        return

    prospect_row = await db.get(Prospect, execution.prospect_id)
    if prospect_row is None:
        await _finalize(db, execution, ExecutionStatus.FAILED, failure_reason="Prospect not found")
        return

    prospect = ProspectCreate(
        name=prospect_row.name,
        company=prospect_row.company,
        designation=prospect_row.designation,
        linkedin_url=prospect_row.linkedin_url,
        company_website=prospect_row.company_website,
        industry=prospect_row.industry,
        outreach_channel=prospect_row.outreach_channel,
        product_context=prospect_row.product_context,
    )

    execution.status = ExecutionStatus.RUNNING
    execution.started_at = datetime.now(timezone.utc)
    await db.commit()

    try:
        # --- Stage: INPUT_VALIDATION (EC-03 / EC-11) ---
        async with stage(db, execution_id, WorkflowStage.INPUT_VALIDATION.value) as ctx:
            execution.current_stage = WorkflowStage.INPUT_VALIDATION.value
            identity = validate_prospect_identity(prospect)
            ctx.set_output(is_identifiable=identity.is_identifiable)

        if not identity.is_identifiable:
            await _finalize(
                db, execution, ExecutionStatus.INSUFFICIENT_DATA,
                failure_reason=identity.reason,
                result_summary={"stage_stopped_at": "input_validation", "missing_fields": identity.missing_fields},
            )
            return

        # --- Stage: RESEARCH_DISCOVERY ---
        async with stage(db, execution_id, WorkflowStage.RESEARCH_DISCOVERY.value) as ctx:
            execution.current_stage = WorkflowStage.RESEARCH_DISCOVERY.value
            if not tavily.is_configured:
                raise TavilyNotConfiguredError("TAVILY_API_KEY is not configured; no research can be performed")

            li_results, li_failed = await run_linkedin_research(tavily, prospect)
            co_results, co_failed = await run_company_research(tavily, prospect)
            pr_results, pr_failed = await run_professional_research(tavily, prospect)
            all_results = li_results + co_results + pr_results
            failed_queries = li_failed + co_failed + pr_failed
            ctx.set_output(
                linkedin_results=len(li_results),
                company_results=len(co_results),
                professional_results=len(pr_results),
                failed_queries=len(failed_queries),
            )

        # --- Stage: URL_DEDUPLICATION (EC-06 / EC-07) ---
        async with stage(db, execution_id, WorkflowStage.URL_DEDUPLICATION.value) as ctx:
            execution.current_stage = WorkflowStage.URL_DEDUPLICATION.value
            deduped_results = deduplicate_search_results(all_results)
            ctx.set_output(raw_count=len(all_results), deduped_count=len(deduped_results))

        if not deduped_results:
            await _finalize(
                db, execution, ExecutionStatus.INSUFFICIENT_DATA,
                failure_reason="No research results were found for this prospect after exhausting query variations",
                result_summary={"stage_stopped_at": "url_deduplication"},
            )
            return

        urls_to_extract = [r.url for r in deduped_results][:MAX_URLS_TO_EXTRACT]

        # --- Stage: CONTENT_EXTRACTION (EC-05 / EC-08) ---
        async with stage(db, execution_id, WorkflowStage.CONTENT_EXTRACTION.value) as ctx:
            execution.current_stage = WorkflowStage.CONTENT_EXTRACTION.value
            extracted = await extract_content_for_urls(tavily, urls_to_extract)
            succeeded = sum(1 for e in extracted if e.success)
            restricted = sum(1 for e in extracted if e.restricted)
            ctx.set_output(attempted=len(urls_to_extract), succeeded=succeeded, restricted=restricted)

        # --- Stage: CONTENT_CLEANING ---
        async with stage(db, execution_id, WorkflowStage.CONTENT_CLEANING.value) as ctx:
            execution.current_stage = WorkflowStage.CONTENT_CLEANING.value
            for result in deduped_results:
                result.snippet = clean_text(result.snippet)
            ctx.set_output(cleaned_snippets=len(deduped_results))

        # --- Stage: SOURCE_VALIDATION (EC-07) ---
        async with stage(db, execution_id, WorkflowStage.SOURCE_VALIDATION.value) as ctx:
            execution.current_stage = WorkflowStage.SOURCE_VALIDATION.value
            validated = build_validated_sources(deduped_results, extracted)
            source_rows: dict[str, ResearchSource] = {}
            for v in validated:
                row = ResearchSource(
                    execution_id=execution_id,
                    url=v.url,
                    normalized_url=v.normalized_url,
                    title=v.title,
                    domain=v.domain,
                    source_type=v.source_type,
                    evidence_type=v.evidence_type,
                    content=v.content,
                    content_hash=v.content_hash,
                    published_at=parse_published_at(v.published_at),
                    extraction_status=v.extraction_status,
                    extraction_error=v.extraction_error,
                    verification_status=v.verification_status,
                    extracted_at=datetime.now(timezone.utc)
                    if v.extraction_status == ExtractionStatus.SUCCESS
                    else None,
                    raw_metadata=v.raw_metadata,
                )
                db.add(row)
                source_rows[v.url] = row
            await db.flush()
            ctx.set_output(sources_persisted=len(source_rows))

        # --- Stage: SIGNAL_EXTRACTION (EC-01 / EC-09 / EC-10) ---
        extracted_signals: list[tuple[ResearchSource, ValidatedSource, object]] = []
        async with stage(db, execution_id, WorkflowStage.SIGNAL_EXTRACTION.value) as ctx:
            execution.current_stage = WorkflowStage.SIGNAL_EXTRACTION.value
            if not tarqa.is_configured:
                ctx.set_output(skipped=True, reason="TARQA not configured")
            else:
                extractable = [
                    v for v in validated
                    if v.content and v.extraction_status != ExtractionStatus.RESTRICTED
                ]
                semaphore = asyncio.Semaphore(get_settings().max_concurrent_extractions)

                async def _bounded_extract(v: ValidatedSource):
                    row = source_rows[v.url]
                    async with semaphore:
                        outcome = await extract_signals_from_source(tarqa, prospect, str(row.id), v)
                    return row, v, outcome

                outcomes = await asyncio.gather(*(_bounded_extract(v) for v in extractable))
                extraction_failures = 0
                for row, v, outcome in outcomes:
                    if outcome.error:
                        extraction_failures += 1
                    for sig in outcome.signals:
                        extracted_signals.append((row, v, sig))
                ctx.set_output(
                    sources_processed=len(validated),
                    signals_found=len(extracted_signals),
                    extraction_failures=extraction_failures,
                )

        # --- Stage: SIGNAL_CLASSIFICATION + SIGNAL_SCORING (deterministic) ---
        signal_rows: list[Signal] = []
        async with stage(db, execution_id, WorkflowStage.SIGNAL_SCORING.value) as ctx:
            execution.current_stage = WorkflowStage.SIGNAL_SCORING.value
            for source_row, validated_source, raw_signal in extracted_signals:
                published_at = parse_published_at(raw_signal.published_at) or source_row.published_at
                ent_match = entity_matches_prospect(raw_signal.entity, prospect.name)
                company_matches = (
                    raw_signal.company is None
                    or raw_signal.company.strip().lower() == prospect.company.strip().lower()
                )
                breakdown = score_signal(
                    signal_type=raw_signal.signal_type,
                    entity_matches_prospect=ent_match,
                    company_matches=company_matches,
                    description=raw_signal.description,
                    product_context=prospect.product_context,
                    published_at=published_at,
                    evidence_type=validated_source.evidence_type,
                    domain=validated_source.domain,
                    excerpt_is_grounded=True,
                )
                signal_row = Signal(
                    execution_id=execution_id,
                    source_id=source_row.id,
                    signal_type=raw_signal.signal_type,
                    description=raw_signal.description,
                    entity=raw_signal.entity,
                    company=raw_signal.company,
                    published_at=published_at,
                    evidence_excerpt=raw_signal.evidence_excerpt,
                    relevance_reason=raw_signal.relevance_reason,
                    confidence_score=raw_signal.confidence_score,
                    relevance_score=breakdown.relevance_score,
                    business_impact_score=breakdown.business_impact_score,
                    recency_score=breakdown.recency_score,
                    evidence_quality_score=breakdown.evidence_quality_score,
                    final_score=breakdown.final_score,
                    relevance_tier=breakdown.relevance_tier,
                    verification_status=VerificationStatus.NEEDS_REVIEW,
                )
                db.add(signal_row)
                signal_rows.append(signal_row)
            await db.flush()
            ctx.set_output(signals_scored=len(signal_rows))

        # --- Stage: CONFLICT_DETECTION (EC-02) ---
        has_conflicts = False
        async with stage(db, execution_id, WorkflowStage.CONFLICT_DETECTION.value) as ctx:
            execution.current_stage = WorkflowStage.CONFLICT_DETECTION.value
            check_inputs = [
                SignalForConflictCheck(
                    id=str(s.id), signal_type=s.signal_type, entity=s.entity, company=s.company,
                    description=s.description, evidence_excerpt=s.evidence_excerpt,
                    published_at=s.published_at,
                )
                for s in signal_rows
            ]
            conflicts = detect_conflicts(
                check_inputs, prospect_name=prospect.name, prospect_company=prospect.company
            )
            disputed_ids: set[str] = set()
            for c in conflicts:
                conflict_row = SignalConflict(
                    execution_id=execution_id,
                    conflict_type=c.conflict_type,
                    description=c.description,
                    signal_ids=c.signal_ids,
                    conflicting_claims=c.conflicting_claims,
                    resolution_status=ConflictResolutionStatus.RESOLVED_EXCLUDED,
                )
                db.add(conflict_row)
                disputed_ids.update(c.signal_ids)

            for s in signal_rows:
                if str(s.id) in disputed_ids:
                    s.is_disputed = True
                    s.verification_status = VerificationStatus.DISPUTED
            await db.flush()
            has_conflicts = bool(conflicts)
            ctx.set_output(conflicts_found=len(conflicts), disputed_signals=len(disputed_ids))

        # --- Stage: SIGNAL_SELECTION (EC-04 / EC-12) ---
        best_signal: Optional[Signal] = None
        async with stage(db, execution_id, WorkflowStage.SIGNAL_SELECTION.value) as ctx:
            execution.current_stage = WorkflowStage.SIGNAL_SELECTION.value
            rankable = [
                RankableSignal(id=str(s.id), final_score=s.final_score or 0, is_disputed=s.is_disputed)
                for s in signal_rows
            ]
            top = select_top_signals(rankable)
            top_ids = {r.id for r in top}
            candidate_rows = [s for s in signal_rows if str(s.id) in top_ids]
            best_wrapped = select_best_usable_signal(
                [_SignalLikeForSelection(s) for s in candidate_rows]
            )
            if best_wrapped is not None:
                best_signal = next(s for s in candidate_rows if s.id == best_wrapped.id)
            ctx.set_output(candidates=len(candidate_rows), selected=best_signal is not None)

        if best_signal is None:
            final_status = ExecutionStatus.NEEDS_REVIEW if has_conflicts else ExecutionStatus.INSUFFICIENT_DATA
            await _finalize(
                db, execution, final_status,
                failure_reason=(
                    "No signal met the relevance/evidence bar required to generate a "
                    "personalized outreach angle"
                ),
                result_summary={
                    "stage_stopped_at": "signal_selection",
                    "sources_found": len(source_rows),
                    "signals_found": len(signal_rows),
                    "conflicts_found": len(conflicts),
                },
            )
            return

        best_source = await db.get(ResearchSource, best_signal.source_id)

        # --- Stage: OUTREACH_STRATEGY ---
        async with stage(db, execution_id, WorkflowStage.OUTREACH_STRATEGY.value) as ctx:
            execution.current_stage = WorkflowStage.OUTREACH_STRATEGY.value
            strategy = generate_strategy(
                prospect_name=prospect.name,
                prospect_role=prospect.designation,
                company=prospect.company,
                product_context=prospect.product_context,
                signal_id=str(best_signal.id),
                signal_type=best_signal.signal_type,
                signal_description=best_signal.description,
                signal_relevance_reason=best_signal.relevance_reason,
                evidence_excerpt=best_signal.evidence_excerpt,
                source_url=best_source.url if best_source else "",
                source_id=str(best_signal.source_id),
            )
            ctx.set_output(angle=strategy.communication_angle)

        # --- Stage: DRAFT_GENERATION + OUTREACH_VALIDATION (EC-09 / EC-10) ---
        drafts_created = 0
        async with stage(db, execution_id, WorkflowStage.DRAFT_GENERATION.value) as ctx:
            execution.current_stage = WorkflowStage.DRAFT_GENERATION.value
            if not tarqa.is_configured:
                ctx.set_output(skipped=True, reason="TARQA not configured")
            else:
                try:
                    email_content = await generate_email_draft(tarqa, strategy)
                    email_report = validate_draft(email_content.body, strategy, OutreachChannel.EMAIL)
                    db.add(
                        OutreachDraft(
                            execution_id=execution_id,
                            channel=OutreachChannel.EMAIL,
                            subject=email_content.subject,
                            body=email_content.body,
                            used_signal_ids=[str(best_signal.id)],
                            used_source_ids=[str(best_signal.source_id)],
                            validation_report={
                                "passed": email_report.passed,
                                "issues": email_report.issues,
                                "checks": email_report.checks,
                            },
                            status=DraftStatus.DRAFT_GENERATED,
                        )
                    )
                    drafts_created += 1
                except (TarqaIntegrationError, TarqaNotConfiguredError) as exc:
                    logger.error("workflow.email_draft_failed", error=str(exc))

                try:
                    li_content = await generate_linkedin_draft(tarqa, strategy)
                    li_report = validate_draft(li_content.body, strategy, OutreachChannel.LINKEDIN)
                    db.add(
                        OutreachDraft(
                            execution_id=execution_id,
                            channel=OutreachChannel.LINKEDIN,
                            subject=None,
                            body=li_content.body,
                            used_signal_ids=[str(best_signal.id)],
                            used_source_ids=[str(best_signal.source_id)],
                            validation_report={
                                "passed": li_report.passed,
                                "issues": li_report.issues,
                                "checks": li_report.checks,
                            },
                            status=DraftStatus.DRAFT_GENERATED,
                        )
                    )
                    drafts_created += 1
                except (TarqaIntegrationError, TarqaNotConfiguredError) as exc:
                    logger.error("workflow.linkedin_draft_failed", error=str(exc))

                await db.flush()
            ctx.set_output(drafts_created=drafts_created)

        final_status = ExecutionStatus.NEEDS_REVIEW if has_conflicts else (
            ExecutionStatus.COMPLETED if drafts_created > 0 else ExecutionStatus.PARTIAL
        )
        await _finalize(
            db, execution, final_status,
            result_summary={
                "sources_found": len(source_rows),
                "signals_found": len(signal_rows),
                "conflicts_found": len(conflicts),
                "drafts_created": drafts_created,
                "selected_signal_id": str(best_signal.id),
            },
        )

    except TavilyNotConfiguredError as exc:
        await db.rollback()
        execution = await db.get(Execution, execution_id)
        await _finalize(db, execution, ExecutionStatus.FAILED, failure_reason=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.error("workflow.unhandled_failure", execution_id=str(execution_id), error=str(exc))
        await db.rollback()
        execution = await db.get(Execution, execution_id)
        await _finalize(db, execution, ExecutionStatus.FAILED, failure_reason="An unexpected error occurred during research")
