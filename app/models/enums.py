import enum


class OutreachChannel(str, enum.Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"


class ExecutionStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    NEEDS_REVIEW = "needs_review"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class SourceType(str, enum.Enum):
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_POST = "linkedin_post"
    COMPANY_WEBSITE = "company_website"
    COMPANY_NEWS = "company_news"
    PRESS_RELEASE = "press_release"
    JOB_POSTING = "job_posting"
    FUNDING_NEWS = "funding_news"
    INTERVIEW = "interview"
    PODCAST = "podcast"
    INDUSTRY_PUBLICATION = "industry_publication"
    OTHER = "other"


class EvidenceType(str, enum.Enum):
    FULL_PAGE = "full_page"
    SEARCH_SNIPPET = "search_snippet"
    METADATA = "metadata"
    USER_PROVIDED = "user_provided"


class ExtractionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RESTRICTED = "restricted"
    SKIPPED = "skipped"
    PENDING = "pending"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    RESTRICTED = "restricted"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class SignalType(str, enum.Enum):
    PROFESSIONAL_ACTIVITY = "professional_activity"
    JOB_CHANGE = "job_change"
    LEADERSHIP_ANNOUNCEMENT = "leadership_announcement"
    COMPANY_GROWTH = "company_growth"
    FUNDING = "funding"
    HIRING = "hiring"
    PRODUCT_DEVELOPMENT = "product_development"
    BUSINESS_CHALLENGE = "business_challenge"
    THOUGHT_LEADERSHIP = "thought_leadership"
    PARTNERSHIP = "partnership"
    PUBLIC_SPEAKING = "public_speaking"
    INDUSTRY_DEVELOPMENT = "industry_development"


class RelevanceTier(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(str, enum.Enum):
    JOB_TITLE = "job_title"
    FUNDING_AMOUNT = "funding_amount"
    DATE_MISMATCH = "date_mismatch"
    IDENTITY_AMBIGUITY = "identity_ambiguity"
    OTHER = "other"


class ConflictResolutionStatus(str, enum.Enum):
    UNRESOLVED = "unresolved"
    RESOLVED_EXCLUDED = "resolved_excluded"
    RESOLVED_MANUAL = "resolved_manual"


class DraftStatus(str, enum.Enum):
    DRAFT_GENERATED = "draft_generated"
    PENDING_REVIEW = "pending_review"
    EDITED = "edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class StageStatus(str, enum.Enum):
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStage(str, enum.Enum):
    INPUT_VALIDATION = "input_validation"
    RESEARCH_DISCOVERY = "research_discovery"
    URL_DEDUPLICATION = "url_deduplication"
    CONTENT_EXTRACTION = "content_extraction"
    CONTENT_CLEANING = "content_cleaning"
    SOURCE_VALIDATION = "source_validation"
    SIGNAL_EXTRACTION = "signal_extraction"
    SIGNAL_CLASSIFICATION = "signal_classification"
    SIGNAL_SCORING = "signal_scoring"
    CONFLICT_DETECTION = "conflict_detection"
    SIGNAL_SELECTION = "signal_selection"
    OUTREACH_STRATEGY = "outreach_strategy"
    DRAFT_GENERATION = "draft_generation"
    OUTREACH_VALIDATION = "outreach_validation"
