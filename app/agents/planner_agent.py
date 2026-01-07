"""app/agents/planner_agent.py

PlannerAgent helps with UPSC preparation by:
- Creating objective tests with balanced section coverage (15 Qs each).
- Evaluating submissions against MongoDB question bank answers.
- Persisting test performance for the user and comparing with prior attempts.
- Producing detailed feedback and a structured study schedule.

When `OPENAI_API_KEY` is provided the agent will attempt to enrich the
study-plan via the OpenAI Chat Completions API; otherwise it falls back to the
deterministic planner so that behaviour stays predictable offline.
"""

import json
import logging
import os
import random
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta, time as dtime
from typing import Any, Dict, List, Optional, Tuple

import certifi
import requests
from requests.adapters import HTTPAdapter
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError
from urllib3.util.retry import Retry

from app.services.mongo import get_mongo_client
from app.utils.planner_utils import (
    allocate_weekly_hours,
    compute_subject_weights_from_percentages,
    fallback_schedule_text,
    load_memory,
    make_summary_text,
    save_memory,
)


THRESHOLDS = [
    (0, 40, "Critical Weak"),
    (40, 60, "Weak"),
    (60, 75, "Average"),
    (75, 90, "Strong"),
    (90, 100, "Excellent"),
]


DEFAULT_BOOKLIST = {
    "Polity": ["Indian Polity — M. Laxmikanth", "NCERT Polity (Class 11-12)"],
    "Economy": ["Indian Economy — Ramesh Singh", "NCERT Economics"],
    "History": ["Spectrum Modern India", "NCERT History"],
    "Geography": ["Oxford School Atlas", "NCERT Geography"],
    "Environment": ["Shankar IAS Environment", "NCERT Biology (relevant)"],
    "Science & Tech": ["NCERT Science", "Current Affairs summaries"],
    "Current Affairs": ["PIB releases", "Rajya Sabha TV Debates"],
}


SECTION_CONFIG: Dict[str, Dict[str, Any]] = {
    "polity": {"label": "Polity", "aliases": ["Polity", "polity"]},
    "economy": {"label": "Economy", "aliases": ["Economy", "economy", "Economic"]},
    "history": {"label": "History", "aliases": ["History", "history"]},
    "geography": {"label": "Geography", "aliases": ["Geography", "geography"]},
    "environment": {"label": "Environment", "aliases": ["Environment", "environment", "Ecology"]},
    "scienceTech": {
        "label": "Science & Tech",
        "aliases": ["ScienceTech", "scienceTech", "Science", "Technology", "Science & Tech"],
    },
    "currentAffairs": {"label": "Current Affairs", "aliases": ["CurrentAffairs", "Current Affairs", "currentAffairs"]},
}

SECTION_ORDER = list(SECTION_CONFIG.keys())


# Deterministic fallback question templates when the Mongo question bank is unavailable.
MOCK_SECTION_BLUEPRINTS: Dict[str, List[Dict[str, Any]]] = {
    "polity": [
        {
            "question": "Which Article empowers the Supreme Court to issue writs for the enforcement of Fundamental Rights?",
            "topic": "Fundamental Rights",
            "difficulty": "Medium",
            "options": {
                "A": "Article 32",
                "B": "Article 21",
                "C": "Article 356",
                "D": "Article 143",
            },
            "answer": "A",
        },
        {
            "question": "The concept of judicial review in the Indian Constitution is borrowed from which country?",
            "topic": "Judiciary",
            "difficulty": "Easy",
            "options": {
                "A": "United Kingdom",
                "B": "United States",
                "C": "Canada",
                "D": "Ireland",
            },
            "answer": "B",
        },
        {
            "question": "Who presides over the joint sitting of Parliament?",
            "topic": "Parliament",
            "difficulty": "Easy",
            "options": {
                "A": "President of India",
                "B": "Speaker of Lok Sabha",
                "C": "Chairman of Rajya Sabha",
                "D": "Prime Minister",
            },
            "answer": "B",
        },
        {
            "question": "Which schedule contains the languages recognized by the Constitution?",
            "topic": "Schedules of Constitution",
            "difficulty": "Medium",
            "options": {
                "A": "Sixth Schedule",
                "B": "Seventh Schedule",
                "C": "Eighth Schedule",
                "D": "Tenth Schedule",
            },
            "answer": "C",
        },
    ],
    "economy": [
        {
            "question": "Which index is released by the National Statistical Office to track retail inflation?",
            "topic": "Inflation",
            "difficulty": "Medium",
            "options": {
                "A": "Wholesale Price Index",
                "B": "Consumer Price Index",
                "C": "Index of Industrial Production",
                "D": "Purchasing Managers Index",
            },
            "answer": "B",
        },
        {
            "question": "Which body recommends the distribution of tax revenues between the Union and the States?",
            "topic": "Public Finance",
            "difficulty": "Easy",
            "options": {
                "A": "Finance Commission",
                "B": "GST Council",
                "C": "NITI Aayog",
                "D": "RBI",
            },
            "answer": "A",
        },
        {
            "question": "MSP for crops in India is recommended by which commission?",
            "topic": "Agriculture",
            "difficulty": "Easy",
            "options": {
                "A": "Finance Commission",
                "B": "Tariff Commission",
                "C": "Commission for Agricultural Costs and Prices",
                "D": "NABARD",
            },
            "answer": "C",
        },
        {
            "question": "Which of the following is NOT a component of the balance of payments?",
            "topic": "External Sector",
            "difficulty": "Medium",
            "options": {
                "A": "Current Account",
                "B": "Capital Account",
                "C": "Financial Account",
                "D": "Revenue Account",
            },
            "answer": "D",
        },
    ],
    "history": [
        {
            "question": "Which of the following was NOT a feature of the Indus Valley Civilization?",
            "topic": "Ancient India",
            "difficulty": "Medium",
            "options": {
                "A": "Grid pattern town planning",
                "B": "Use of iron tools",
                "C": "Standardized weights",
                "D": "Advanced drainage",
            },
            "answer": "B",
        },
        {
            "question": "Who among the following founded the Prarthana Samaj?",
            "topic": "Modern India",
            "difficulty": "Easy",
            "options": {
                "A": "Atmaram Pandurang",
                "B": "M.G. Ranade",
                "C": "Swami Dayanand",
                "D": "Keshab Chandra Sen",
            },
            "answer": "A",
        },
        {
            "question": "Which Governor-General introduced the Doctrine of Lapse?",
            "topic": "British Policies",
            "difficulty": "Easy",
            "options": {
                "A": "Lord Dalhousie",
                "B": "Lord Wellesley",
                "C": "Lord Hastings",
                "D": "Lord Bentick",
            },
            "answer": "A",
        },
        {
            "question": "The Battle of Plassey was fought in which year?",
            "topic": "Modern India",
            "difficulty": "Medium",
            "options": {
                "A": "1748",
                "B": "1757",
                "C": "1764",
                "D": "1782",
            },
            "answer": "B",
        },
    ],
    "geography": [
        {
            "question": "Which of the following rivers is a tributary of the Brahmaputra?",
            "topic": "Indian Rivers",
            "difficulty": "Medium",
            "options": {
                "A": "Beas",
                "B": "Lohit",
                "C": "Chambal",
                "D": "Son",
            },
            "answer": "B",
        },
        {
            "question": "Black cotton soil is ideal for the cultivation of which crop?",
            "topic": "Soils",
            "difficulty": "Easy",
            "options": {
                "A": "Rice",
                "B": "Tea",
                "C": "Cotton",
                "D": "Wheat",
            },
            "answer": "C",
        },
        {
            "question": "The Tropic of Cancer passes through how many Indian states?",
            "topic": "Location Based",
            "difficulty": "Medium",
            "options": {
                "A": "6",
                "B": "8",
                "C": "9",
                "D": "10",
            },
            "answer": "C",
        },
        {
            "question": "Which plateau is known as the \"Mineral Storehouse\" of India?",
            "topic": "Physiography",
            "difficulty": "Easy",
            "options": {
                "A": "Deccan Plateau",
                "B": "Chota Nagpur Plateau",
                "C": "Malwa Plateau",
                "D": "Bastar Plateau",
            },
            "answer": "B",
        },
    ],
    "environment": [
        {
            "question": "Which Indian Act provides the legal basis for declaring Eco-sensitive Zones?",
            "topic": "Conservation",
            "difficulty": "Medium",
            "options": {
                "A": "Forest Conservation Act, 1980",
                "B": "Wildlife Protection Act, 1972",
                "C": "Biological Diversity Act, 2002",
                "D": "Environment Protection Act, 1986",
            },
            "answer": "B",
        },
        {
            "question": "Biosphere Reserves aim to conserve which level of biodiversity?",
            "topic": "Biodiversity",
            "difficulty": "Easy",
            "options": {
                "A": "Genetic",
                "B": "Species",
                "C": "Ecosystem",
                "D": "All of the above",
            },
            "answer": "D",
        },
        {
            "question": "Which gas has the highest global warming potential among the following?",
            "topic": "Climate Change",
            "difficulty": "Medium",
            "options": {
                "A": "Carbon dioxide",
                "B": "Methane",
                "C": "Nitrous oxide",
                "D": "Sulphur hexafluoride",
            },
            "answer": "D",
        },
        {
            "question": "Project Tiger was launched in which year?",
            "topic": "Schemes",
            "difficulty": "Easy",
            "options": {
                "A": "1969",
                "B": "1973",
                "C": "1985",
                "D": "1992",
            },
            "answer": "B",
        },
    ],
    "scienceTech": [
        {
            "question": "Which of the following is a reusable launch vehicle developed by ISRO?",
            "topic": "Space",
            "difficulty": "Medium",
            "options": {
                "A": "PSLV",
                "B": "GSLV Mk III",
                "C": "RLV-TD",
                "D": "ASLV",
            },
            "answer": "C",
        },
        {
            "question": "CRISPR technology is primarily used for what purpose?",
            "topic": "Biotechnology",
            "difficulty": "Easy",
            "options": {
                "A": "Protein folding",
                "B": "Genome editing",
                "C": "RNA sequencing",
                "D": "Drug delivery",
            },
            "answer": "B",
        },
        {
            "question": "Which mission aims to study the Sun from L1 point?",
            "topic": "Space",
            "difficulty": "Medium",
            "options": {
                "A": "Chandrayaan-3",
                "B": "Mangalyaan",
                "C": "Aditya-L1",
                "D": "Gaganyaan",
            },
            "answer": "C",
        },
        {
            "question": "Li-Fi technology primarily uses which wave for data transmission?",
            "topic": "Communication",
            "difficulty": "Easy",
            "options": {
                "A": "Radio waves",
                "B": "Microwaves",
                "C": "Infrared/Visible light",
                "D": "Gamma rays",
            },
            "answer": "C",
        },
    ],
    "currentAffairs": [
        {
            "question": "The 'PM-PRANAM' scheme is related to which of the following?",
            "topic": "Government Schemes",
            "difficulty": "Medium",
            "options": {
                "A": "Crop insurance",
                "B": "Fertilizer usage",
                "C": "Rural housing",
                "D": "Skill development",
            },
            "answer": "B",
        },
        {
            "question": "Which organization publishes the Global Gender Gap Report?",
            "topic": "Reports",
            "difficulty": "Easy",
            "options": {
                "A": "UNDP",
                "B": "World Economic Forum",
                "C": "World Bank",
                "D": "IMF",
            },
            "answer": "B",
        },
        {
            "question": "'PM MITRA' parks are associated with which sector?",
            "topic": "Industries",
            "difficulty": "Easy",
            "options": {
                "A": "Electronics",
                "B": "Textiles",
                "C": "Automobile",
                "D": "Pharmaceuticals",
            },
            "answer": "B",
        },
        {
            "question": "India recently signed the Artemis Accords. These are related to which domain?",
            "topic": "International",
            "difficulty": "Medium",
            "options": {
                "A": "Space exploration",
                "B": "Climate finance",
                "C": "Nuclear disarmament",
                "D": "Cyber security",
            },
            "answer": "A",
        },
    ],
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOCAL_LLM_ENDPOINT = os.environ.get("LOCAL_LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")
PLANNER_MEMORY_PATH = os.environ.get("PLANNER_MEMORY_PATH", "planner_memory.json")

DAY_HEADERS = [
    "📅 Monday",
    "📅 Tuesday",
    "📅 Wednesday",
    "📅 Thursday",
    "📅 Friday",
    "📅 Saturday",
    "📅 Sunday",
]
DAY_NAME_TO_INDEX = {
    header.replace("📅", "").strip().lower(): idx for idx, header in enumerate(DAY_HEADERS)
}
TIME_RANGE_RE = re.compile(
    r"\b(0?[1-9]|1[0-2]):[0-5][0-9]\s?(am|pm)\s*-\s*(0?[1-9]|1[0-2]):[0-5][0-9]\s?(am|pm)",
    flags=re.IGNORECASE,
)
TIME_BLOCK_RE = re.compile(
    r"(?P<start>\d{1,2}:[0-5]\d\s*(?:am|pm)?)\s*-\s*(?P<end>\d{1,2}:[0-5]\d\s*(?:am|pm)?)\s*(?:—|–|-)+\s*(?P<title>.+)",
    flags=re.IGNORECASE,
)


def _requests_session_with_retries(total_retries: int = 3, backoff: float = 0.4) -> requests.Session:
    session = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def local_llama_call(
    prompt: str,
    max_tokens: int = 1600,
    temperature: float = 0.08,
    endpoint: str = LOCAL_LLM_ENDPOINT,
    timeout: int = 90,
) -> str:
    """Single robust LLM call. Returns assistant content or empty string on failure."""

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": float(temperature),
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    session = _requests_session_with_retries()
    try:
        logger.debug("Calling local LLM server at %s", endpoint)
        resp = session.post(endpoint, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict) and message.get("content"):
                    return str(message["content"]).strip()
                if "text" in choice:
                    return str(choice["text"]).strip()
        logger.warning("LLM returned unexpected structure: %s", list(data.keys()))
        return ""
    except Exception as exc:  # pragma: no cover - network errors handled at runtime
        logger.exception("LLM request failed: %s", exc)
        return ""


class LLMSchedulePlanner:
    """LLM backed weekly schedule generator that stores short-term memory."""

    def __init__(
        self,
        memory_path: Optional[str] = None,
        calendar_tool=None,
        calendar_enabled: Optional[bool] = None,
    ):
        # memory works normally
        self.memory_path = memory_path or PLANNER_MEMORY_PATH
        self.memory = load_memory(self.memory_path)

        # FORCE calendar sync disabled (since ics library missing on Railway)
        self.calendar_sync_enabled = False
        self.calendar_tool = None

def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _uri_requires_tls(uri: str) -> bool:
    lowered = uri.lower()
    return uri.startswith("mongodb+srv://") or "tls=true" in lowered or "ssl=true" in lowered


def _build_client(uri: str) -> MongoClient:
    timeout_ms = int(os.getenv("MONGODB_SELECTION_TIMEOUT_MS", "5000"))
    client_kwargs = {"serverSelectionTimeoutMS": timeout_ms}

    ca_file = os.getenv("MONGODB_TLS_CA_FILE")
    if ca_file:
        client_kwargs["tlsCAFile"] = ca_file
    elif _uri_requires_tls(uri):
        client_kwargs["tlsCAFile"] = certifi.where()

    if _env_flag("MONGODB_TLS_ALLOW_INVALID_CERTS"):
        client_kwargs["tlsAllowInvalidCertificates"] = True

    return MongoClient(uri, **client_kwargs)


def classify_score(score: float) -> str:
    for lo, hi, label in THRESHOLDS:
        if lo <= score <= hi:
            return label
    return "Unknown"


class PlannerAgent:
    """Composite agent that orchestrates testing and planning for learners."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        mongo_uri: Optional[str] = None,
        mongo_db: Optional[str] = None,
        questions_collection: Optional[str] = None,
        users_collection: str = "users",
        reports_collection: str = "reports",
    ) -> None:
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = mongo_db or os.getenv("MONGODB_DB", "civicbriefs")
        questions_coll_name = questions_collection or os.getenv("MONGODB_QUESTIONS_COLLECTION", "questions")

        if mongo_uri:
            self._client: MongoClient = _build_client(uri)
        else:
            self._client = get_mongo_client()

        self._db: Database = self._client[db_name]
        self._questions: Collection = self._db[questions_coll_name]
        self._users: Collection = self._db[users_collection]
        self._reports: Collection = self._db[reports_collection]
        self.schedule_planner = LLMSchedulePlanner()

    # ------------------------------------------------------------------
    # Test generation
    # ------------------------------------------------------------------
    def prepare_test(self, questions_per_section: int = 15) -> Dict[str, Any]:
        if questions_per_section <= 0:
            raise ValueError("questions_per_section must be positive")

        try:
            return self._prepare_test_from_db(questions_per_section)
        except PyMongoError:
            # Fall back to deterministic mock questions when MongoDB is unavailable.
            return self._prepare_test_from_mock(questions_per_section)
        except ValueError:
            # When the live bank lacks enough questions, still serve a mock test so UI stays functional.
            return self._prepare_test_from_mock(questions_per_section)

    def _prepare_test_from_db(self, questions_per_section: int) -> Dict[str, Any]:
        test_id = str(uuid.uuid4())
        sections_payload: Dict[str, Dict[str, Any]] = {}
        total_questions = 0

        for section in SECTION_ORDER:
            label = SECTION_CONFIG[section]["label"]
            aliases = SECTION_CONFIG[section]["aliases"]

            available = self._questions.count_documents({"subject": {"$in": aliases}})
            if available < questions_per_section:
                raise ValueError(
                    f"Not enough questions for section '{label}' (required={questions_per_section}, available={available})"
                )

            pipeline = [
                {"$match": {"subject": {"$in": aliases}}},
                {"$sample": {"size": questions_per_section}},
            ]

            docs = list(self._questions.aggregate(pipeline))
            random.shuffle(docs)

            questions = []
            for doc in docs:
                qid = doc.get("question_id") or str(doc.get("_id"))
                questions.append(
                    {
                        "question_id": qid,
                        "section": section,
                        "section_label": label,
                        "subject": doc.get("subject"),
                        "topic": doc.get("topic"),
                        "difficulty": doc.get("difficulty"),
                        "question": doc.get("question"),
                        "options": doc.get("options", {}),
                    }
                )

            sections_payload[section] = {
                "label": label,
                "questions": questions,
            }
            total_questions += len(questions)

        return {
            "test_id": test_id,
            "questions_per_section": questions_per_section,
            "total_questions": total_questions,
            "sections": sections_payload,
        }

    def _prepare_test_from_mock(self, questions_per_section: int) -> Dict[str, Any]:
        test_id = str(uuid.uuid4())
        sections_payload: Dict[str, Dict[str, Any]] = {}
        total_questions = 0

        for section in SECTION_ORDER:
            label = SECTION_CONFIG[section]["label"]
            blueprints = MOCK_SECTION_BLUEPRINTS.get(section)
            if not blueprints:
                raise ValueError(f"No mock question blueprints configured for section '{section}'")

            start_index = random.randint(0, 999)
            questions: List[Dict[str, Any]] = []
            for offset in range(questions_per_section):
                index = start_index + offset
                doc = self._mock_question_document(section, index, include_answer=False)
                questions.append(doc)

            sections_payload[section] = {
                "label": label,
                "questions": questions,
            }
            total_questions += len(questions)

        return {
            "test_id": test_id,
            "questions_per_section": questions_per_section,
            "total_questions": total_questions,
            "sections": sections_payload,
        }

    def _mock_question_document(self, section: str, index: int, *, include_answer: bool) -> Dict[str, Any]:
        blueprints = MOCK_SECTION_BLUEPRINTS.get(section)
        if not blueprints:
            raise ValueError(f"No mock question blueprints configured for section '{section}'")

        blueprint = blueprints[index % len(blueprints)]
        variant = index // len(blueprints)
        label = SECTION_CONFIG[section]["label"]

        question_text = blueprint["question"]
        if variant:
            question_text = f"{question_text} (Variant {variant + 1})"

        qid = f"mock-{section}-{index:04d}"
        payload: Dict[str, Any] = {
            "question_id": qid,
            "section": section,
            "section_label": label,
            "subject": label,
            "topic": blueprint["topic"],
            "difficulty": blueprint["difficulty"],
            "question": question_text,
            "options": dict(blueprint["options"]),
        }

        if include_answer:
            payload["correct_answer"] = blueprint["answer"]

        return payload

    def _mock_question_from_id(self, qid: str) -> Optional[Dict[str, Any]]:
        if not qid.startswith("mock-"):
            return None

        parts = qid.split("-", 2)
        if len(parts) != 3:
            return None

        _, section, index_str = parts
        try:
            index = int(index_str)
        except ValueError:
            return None

        try:
            return self._mock_question_document(section, index, include_answer=True)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Submission evaluation
    # ------------------------------------------------------------------
    def evaluate_test(self, user_id: Optional[str], answers: Dict[str, str]) -> Dict[str, Any]:
        if not answers:
            raise ValueError("answers payload cannot be empty")

        question_ids = list(answers.keys())
        mock_question_ids = [qid for qid in question_ids if qid.startswith("mock-")]
        db_question_ids = [qid for qid in question_ids if qid not in mock_question_ids]

        id_filters = []
        question_id_keys = [qid for qid in db_question_ids if not ObjectId.is_valid(qid)]
        object_id_keys = [ObjectId(qid) for qid in db_question_ids if ObjectId.is_valid(qid)]

        if question_id_keys:
            id_filters.append({"question_id": {"$in": question_id_keys}})
        if object_id_keys:
            id_filters.append({"_id": {"$in": object_id_keys}})

        question_map: Dict[str, Dict[str, Any]] = {}

        if id_filters:
            query = id_filters[0] if len(id_filters) == 1 else {"$or": id_filters}
            try:
                cursor = self._questions.find(
                    query,
                    {
                        "question_id": 1,
                        "question": 1,
                        "options": 1,
                        "correct_answer": 1,
                        "subject": 1,
                        "topic": 1,
                        "difficulty": 1,
                    },
                )
            except PyMongoError as exc:
                raise ValueError(f"Unable to load questions from database: {exc}")

            for doc in cursor:
                stored_qid = doc.get("question_id")
                if stored_qid:
                    question_map[stored_qid] = doc
                fallback_qid = str(doc.get("_id")) if doc.get("_id") else None
                if fallback_qid:
                    question_map[fallback_qid] = doc

        for qid in mock_question_ids:
            mock_doc = self._mock_question_from_id(qid)
            if mock_doc:
                question_map[qid] = mock_doc

        missing_ids = [qid for qid in question_ids if qid not in question_map]
        if missing_ids:
            raise ValueError(f"Unknown question_ids supplied: {missing_ids[:5]}")

        section_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "review": []}
        )

        total_correct = 0
        total_questions = 0

        for qid, response in answers.items():
            doc = question_map[qid]
            section = self._normalize_section(doc.get("subject"))
            label = SECTION_CONFIG[section]["label"]
            correct_option = str(doc.get("correct_answer")).strip().upper()
            chosen = str(response).strip().upper()

            is_correct = chosen == correct_option

            section_stats[section]["total"] += 1
            total_questions += 1

            if is_correct:
                section_stats[section]["correct"] += 1
                total_correct += 1
            else:
                section_stats[section]["review"].append(
                    {
                        "question_id": qid,
                        "section": section,
                        "section_label": label,
                        "question": doc.get("question"),
                        "topic": doc.get("topic"),
                        "difficulty": doc.get("difficulty"),
                        "selected_answer": chosen,
                        "correct_answer": correct_option,
                    }
                )

        section_report: Dict[str, Dict[str, Any]] = {}
        percentage_scores: Dict[str, float] = {}

        for section in SECTION_ORDER:
            stats = section_stats.get(section, {"total": 0, "correct": 0, "review": []})
            total = stats["total"]
            correct = stats["correct"]
            accuracy = round((correct / total) * 100, 2) if total else 0.0
            percentage_scores[SECTION_CONFIG[section]["label"]] = accuracy
            section_report[section] = {
                "label": SECTION_CONFIG[section]["label"],
                "total": total,
                "correct": correct,
                "accuracy": accuracy,
                "incorrect_questions": stats["review"],
            }

        overall_accuracy = round((total_correct / total_questions) * 100, 2) if total_questions else 0.0

        user_doc, persisted = self._persist_score(user_id, percentage_scores)
        user_email = (user_doc or {}).get("email")
        history = self._load_history(user_doc)
        feedback = self._build_feedback(history, percentage_scores)
        schedule_payload = self.schedule_planner.build_schedule_from_percentages(percentage_scores)
        study_plan = self.generate(
            percentage_scores,
            user_id=user_id,
            user_email=user_email,
        )

        result = {
            "user": self._public_user_payload(user_doc, fallback_id=user_id),
            "test_summary": {
                "total_questions": total_questions,
                "total_correct": total_correct,
                "overall_accuracy": overall_accuracy,
            },
            "section_report": section_report,
            "feedback": feedback,
            "study_plan": study_plan,
            "study_plan_sections": self._summarize_study_plan(study_plan),
            "history": history,
            "weekly_schedule": schedule_payload,
            "persistence": persisted,
        }

        result["report_storage"] = self._persist_final_report(result, user_id, user_email)

        return result

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _normalize_section(self, subject: Optional[str]) -> str:
        subject = (subject or "").strip()
        for key, meta in SECTION_CONFIG.items():
            if subject in meta["aliases"]:
                return key
        # fallback to polity when unknown to avoid KeyErrors, but keep trace
        return "polity"

    def _public_user_payload(self, user: Optional[Dict[str, Any]], fallback_id: Optional[str]) -> Dict[str, Any]:
        if not user:
            return {"id": fallback_id}
        return {
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "email": user.get("email"),
            "phoneNumber": user.get("phoneNumber"),
        }

    def _persist_score(self, user_id: Optional[str], scores: Dict[str, float]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        if not user_id:
            return None, {"saved": False, "message": "user_id not supplied — result not persisted"}

        user_doc = self._find_user(user_id)
        if not user_doc:
            return None, {"saved": False, "message": f"user '{user_id}' not found in database"}

        sections_payload: Dict[str, float] = {}
        for key in SECTION_ORDER:
            label = SECTION_CONFIG[key]["label"]
            value = round(float(scores.get(label, 0.0)), 2)
            sections_payload[key] = value

        entry = {
            "date": datetime.utcnow(),
            "sections": sections_payload,
        }

        try:
            self._users.update_one({"_id": user_doc["_id"]}, {"$push": {"testScores": entry}})
            refreshed = self._users.find_one({"_id": user_doc["_id"]})
            return refreshed, {"saved": True, "message": "Result stored successfully"}
        except PyMongoError as exc:
            return user_doc, {"saved": False, "message": f"Failed to persist result: {exc}"}

    def _persist_final_report(
        self,
        report: Dict[str, Any],
        user_id: Optional[str],
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        doc = {
            "date": datetime.utcnow(),
            "user_id": user_id,
            "report": report,
        }
        if user_email:
            doc["user_email"] = user_email
        try:
            inserted = self._reports.insert_one(doc)
            return {"saved": True, "report_id": str(inserted.inserted_id)}
        except PyMongoError as exc:
            logger.warning("Unable to persist final report: %s", exc)
            return {"saved": False, "message": str(exc)}

    def _fetch_previous_report(
        self,
        *,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not user_email and not user_id:
            return None

        query: Dict[str, Any]
        if user_email:
            query = {"user_email": user_email.strip().lower()}
        else:
            query = {"user_id": user_id}

        try:
            return self._reports.find_one(query, sort=[("date", -1)])
        except PyMongoError as exc:
            logger.warning("Failed to fetch previous report: %s", exc)
            return None

    def _extract_scores_from_report(self, report_doc: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not report_doc:
            return {}

        payload = report_doc.get("report") or {}
        section_report = payload.get("section_report") or {}
        extracted: Dict[str, float] = {}

        for slug, meta in section_report.items():
            if not isinstance(meta, dict):
                continue
            label = meta.get("label") or SECTION_CONFIG.get(slug, {}).get("label", slug.title())
            try:
                extracted[label] = float(meta.get("accuracy", 0.0) or 0.0)
            except (TypeError, ValueError):
                continue

        return extracted

    def _serialize_report_date(self, raw: Optional[object]) -> Optional[str]:
        if isinstance(raw, datetime):
            return raw.isoformat()
        if isinstance(raw, date):
            return datetime.combine(raw, datetime.min.time()).isoformat()
        if isinstance(raw, str):
            return raw
        return None

    def _build_comparison_payload(
        self,
        *,
        current_scores: Dict[str, float],
        previous_scores: Dict[str, float],
        previous_doc: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not previous_scores:
            return None

        sections: List[Dict[str, Any]] = []
        improved: List[Dict[str, Any]] = []
        downgraded: List[Dict[str, Any]] = []
        stable: List[Dict[str, Any]] = []

        labels = sorted({*previous_scores.keys(), *current_scores.keys()})
        for label in labels:
            prev_val = float(previous_scores.get(label, 0.0))
            curr_val = float(current_scores.get(label, 0.0))
            delta = round(curr_val - prev_val, 2)

            if delta >= 2:
                status = "improved"
            elif delta <= -2:
                status = "downgraded"
            else:
                status = "stable"

            entry = {
                "label": label,
                "previous": prev_val,
                "current": curr_val,
                "delta": delta,
                "status": status,
            }
            sections.append(entry)
            if status == "improved":
                improved.append(entry)
            elif status == "downgraded":
                downgraded.append(entry)
            else:
                stable.append(entry)

        metadata = {
            "sections": sections,
            "improved": improved,
            "downgraded": downgraded,
            "stable": stable,
        }

        if previous_doc:
            metadata["previous_report_id"] = str(previous_doc.get("_id")) if previous_doc.get("_id") else None
            metadata["previous_report_date"] = self._serialize_report_date(previous_doc.get("date"))

        return metadata

    def _find_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        identifier = identifier.strip()
        if ObjectId.is_valid(identifier):
            user = self._users.find_one({"_id": ObjectId(identifier)})
            if user:
                return user
        if "@" in identifier:
            user = self._users.find_one({"email": identifier.lower()})
            if user:
                return user
        # fallback on phone number match
        return self._users.find_one({"phoneNumber": identifier})

    def _load_history(self, user_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not user_doc:
            return {"available": False, "entries": []}

        entries = user_doc.get("testScores", []) or []
        entries.sort(key=lambda item: item.get("date", datetime.min))

        history_payload = []
        for item in entries[-5:]:
            dt = item.get("date")
            iso = dt.isoformat() if isinstance(dt, datetime) else dt
            history_payload.append({"date": iso, "sections": item.get("sections", {})})

        return {"available": bool(history_payload), "entries": history_payload}

    def _build_feedback(self, history: Dict[str, Any], current_scores: Dict[str, float]) -> Dict[str, Any]:
        entries = history.get("entries", [])
        if len(entries) < 2:
            message = "No prior attempts available. Focus on weaker sections highlighted in the report and retake after a week."
            return {
                "summary": message,
                "improved_sections": [],
                "regressed_sections": [],
                "stable_sections": [],
            }

        previous = entries[-2]["sections"]
        improved: List[Dict[str, Any]] = []
        regressed: List[Dict[str, Any]] = []
        stable: List[Dict[str, Any]] = []

        for section in SECTION_ORDER:
            label = SECTION_CONFIG[section]["label"]
            prev_score = float(previous.get(section, 0.0))
            curr_score = float(current_scores.get(label, 0.0))
            delta = round(curr_score - prev_score, 2)

            record = {"section": label, "previous": prev_score, "current": curr_score, "delta": delta}

            if delta > 2:
                improved.append(record)
            elif delta < -2:
                regressed.append(record)
            else:
                stable.append(record)

        parts = []
        if improved:
            parts.append("Improved: " + ", ".join(f"{item['section']} (+{item['delta']}%)" for item in improved))
        if regressed:
            parts.append("Needs attention: " + ", ".join(f"{item['section']} ({item['delta']}%)" for item in regressed))
        if stable:
            parts.append("Stable: " + ", ".join(f"{item['section']}" for item in stable))

        summary = "; ".join(parts) if parts else "Performance comparable to previous attempt."

        return {
            "summary": summary,
            "improved_sections": improved,
            "regressed_sections": regressed,
            "stable_sections": stable,
        }

    def _summarize_study_plan(self, study_plan: Any) -> Dict[str, Any]:
        if isinstance(study_plan, dict):
            return {
                "classification": study_plan.get("classification"),
                "seven_day_focus": study_plan.get("7_day_plan"),
                "thirty_day_roadmap": study_plan.get("30_day_plan"),
                "resources": study_plan.get("topic_resources"),
                "booklist": study_plan.get("booklist"),
                "daily_plan": study_plan.get("daily_plan"),
                "pyq_strategy": study_plan.get("pyq_strategy"),
                "comparison_insights": study_plan.get("comparison_insights"),
                "trend_summary": study_plan.get("trend_summary"),
            }
        if isinstance(study_plan, str):
            return {"raw_text": study_plan}
        return {}

    # ------------------------------------------------------------------
    # Planner generation (LLM + deterministic fallback)
    # ------------------------------------------------------------------
    def generate(
        self,
        performance: Dict[str, float],
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        display_perf = self._normalize_performance(performance)

        previous_doc = self._fetch_previous_report(user_email=user_email, user_id=user_id)
        previous_scores = self._extract_scores_from_report(previous_doc)
        comparison = self._build_comparison_payload(
            current_scores=display_perf,
            previous_scores=previous_scores,
            previous_doc=previous_doc,
        )

        prompt = self._build_prompt(display_perf, comparison)

        if self.api_key:
            try:
                resp = self._call_llm(prompt)
                if resp:
                    if isinstance(resp, dict):
                        if comparison and "comparison_insights" not in resp:
                            resp["comparison_insights"] = comparison
                        resp.setdefault("plan_sections", self._summarize_study_plan(resp))
                        return resp
                    if comparison:
                        return {
                            "text": resp,
                            "comparison_insights": comparison,
                            "plan_sections": self._summarize_study_plan(resp),
                        }
                    return {"text": resp, "plan_sections": self._summarize_study_plan(resp)}
            except Exception:
                pass

        plan = self._deterministic_generate(display_perf, comparison)
        if isinstance(plan, dict):
            plan.setdefault("plan_sections", self._summarize_study_plan(plan))
        return plan

    def _to_display_key(self, key: str) -> str:
        key = key.strip()
        # Already a display label
        for meta in SECTION_CONFIG.values():
            if key == meta["label"]:
                return key
        normalized = self._normalize_section(key)
        return SECTION_CONFIG[normalized]["label"]

    def _normalize_performance(self, raw: Dict[str, float]) -> Dict[str, float]:
        normalized: Dict[str, float] = {}
        for key, value in raw.items():
            label = self._to_display_key(key)
            try:
                normalized[label] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized

    def _build_prompt(
        self,
        performance: Dict[str, float],
        comparison: Optional[Dict[str, Any]] = None,
    ) -> str:
        lines = ["You are a UPSC mentor. Generate a planner based on the performance:"]
        for subj, score in performance.items():
            lines.append(f"{subj}: {score}")
        if comparison and comparison.get("sections"):
            lines.append("Previous attempt snapshot (use this to note improvements/regressions):")
            for entry in comparison["sections"]:
                label = entry["label"]
                prev_val = entry["previous"]
                curr_val = entry["current"]
                delta = entry["delta"]
                status = entry["status"]
                lines.append(
                    f"{label}: previous {prev_val}%, current {curr_val}% (delta {delta:+.2f} pts, {status})."
                )
            lines.append(
                "Highlight what improved, what declined, and prescribe concrete remediation for downgraded sections."
            )
        lines.append("Identify weak vs strong sections, give reasons, 7-day micro plan, 30-day roadmap, resources, daily cadence, and PYQ approach.")
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a UPSC mentor."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 900,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        data = response.json()
        raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            return json.loads(raw)
        except Exception:
            return {"text": raw}

    def _deterministic_generate(
        self,
        perf: Dict[str, float],
        comparison: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        subjects = list(perf.keys())
        if not subjects:
            return {"message": "No performance data provided."}

        classification = {s: classify_score(perf[s]) for s in subjects}

        weak = [s for s in subjects if classification[s] in ("Critical Weak", "Weak")]
        strong = [s for s in subjects if classification[s] in ("Strong", "Excellent")]

        reasons = {
            s: ("Conceptual gaps and low PYQ coverage." if perf[s] < 60 else "Needs more timed practice to boost accuracy.")
            for s in subjects
        }

        focus = weak[:2] if weak else subjects[:2]
        seven_day = [
            {"day": "Day 1", "plan": f"Brush up NCERT notes for {focus[0]} and jot key mind-maps."},
            {"day": "Day 2", "plan": f"Topic drills + PYQs for {focus[0]}."},
            {"day": "Day 3", "plan": f"Concept revisions for {focus[1] if len(focus) > 1 else subjects[0]} plus 30 MCQs."},
            {"day": "Day 4", "plan": "Current Affairs consolidation — monthly magazine + daily quiz."},
            {"day": "Day 5", "plan": "Geography atlas work + map-based MCQs."},
            {"day": "Day 6", "plan": "Full-length mixed mock (100 Qs) under exam conditions."},
            {"day": "Day 7", "plan": "Error log review + revision flashcards."},
        ]

        sorted_by_need = sorted(subjects, key=lambda s: perf[s])
        week_plans = {
            "Week 1": f"{sorted_by_need[0]} deep dive; integrate PYQs",  # weakest
            "Week 2": f"{sorted_by_need[1] if len(sorted_by_need) > 1 else sorted_by_need[0]} + Current Affairs consolidation",
            "Week 3": "Economy & Environment alternating days + answer writing",
            "Week 4": "Comprehensive revision + mixed mocks (2) + error log fixes",
        }

        topic_resources = {
            s: [
                f"NCERT summary for {s}",
                DEFAULT_BOOKLIST.get(s, ["Standard reference book"])[0],
                "Vision/PT365 notes for rapid revision",
            ]
            for s in subjects
        }

        daily_plan = {
            "mcq_per_day": 60,
            "revision_minutes": 90,
            "structure": "Morning: new concepts | Afternoon: MCQs | Evening: revision + PYQ notes",
        }

        pyq_strategy = "Target the last 7 years topic-wise; maintain an error log and reattempt incorrect PYQs fortnightly."

        summary_lines: List[str] = []
        if comparison:
            if comparison.get("improved"):
                summary_lines.append(
                    "Improved: "
                    + ", ".join(f"{item['label']} (+{item['delta']} pts)" for item in comparison["improved"])
                )
            if comparison.get("downgraded"):
                summary_lines.append(
                    "Downgraded: "
                    + ", ".join(f"{item['label']} ({item['delta']} pts)" for item in comparison["downgraded"])
                )
            if comparison.get("stable"):
                summary_lines.append(
                    "Stable: "
                    + ", ".join(item["label"] for item in comparison["stable"])
                )

        result: Dict[str, Any] = {
            "classification": classification,
            "weak_subjects": weak,
            "strong_subjects": strong,
            "reasons": reasons,
            "7_day_plan": seven_day,
            "30_day_plan": week_plans,
            "topic_resources": topic_resources,
            "booklist": {s: DEFAULT_BOOKLIST.get(s, []) for s in subjects},
            "daily_plan": daily_plan,
            "pyq_strategy": pyq_strategy,
        }

        if comparison:
            result["comparison_insights"] = comparison
            if summary_lines:
                result["trend_summary"] = "; ".join(summary_lines)

        return result


if __name__ == "__main__":
    agent = PlannerAgent()
    test = agent.prepare_test(questions_per_section=1)
    print(json.dumps(test, indent=2))

    demo_answers = {}
    for section in test["sections"].values():
        for q in section["questions"]:
            demo_answers[q["question_id"]] = "A"

    try:
        result = agent.evaluate_test(user_id=None, answers=demo_answers)
        print(json.dumps(result, indent=2, default=str))
    except ValueError as exc:
        print(f"Evaluation error: {exc}")
