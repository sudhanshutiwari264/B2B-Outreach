export const STAGE_MESSAGES: Record<string, string[]> = {
  input_validation: ["Checking we can uniquely identify this prospect…"],
  research_discovery: [
    "Searching for LinkedIn activity…",
    "Scanning company news and press releases…",
    "Looking for interviews and public talks…",
  ],
  url_deduplication: ["Deduplicating discovered URLs…"],
  content_extraction: [
    "Fetching full page content…",
    "Falling back to alternate extraction where needed…",
  ],
  content_cleaning: ["Cleaning and normalizing extracted text…"],
  source_validation: ["Classifying sources and checking evidence quality…"],
  signal_extraction: [
    "Reading extracted articles…",
    "Identifying business signals with Tarqa AI…",
    "Checking each claim is grounded in the source text…",
    "Filtering out unsupported statements…",
  ],
  signal_scoring: [
    "Scoring relevance, business impact, and recency…",
    "Ranking signals by evidence quality…",
  ],
  conflict_detection: ["Cross-checking claims for contradictions…"],
  signal_selection: ["Selecting the strongest verified signal…"],
  outreach_strategy: ["Choosing a personalization angle…"],
  draft_generation: [
    "Drafting a personalized email…",
    "Drafting a personalized LinkedIn message…",
    "Running quality and grounding checks…",
  ],
};

export const DEFAULT_MESSAGES = ["Working on it…"];
