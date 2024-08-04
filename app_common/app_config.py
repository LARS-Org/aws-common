"""
Configuration parameters for the whole application.
"""

import os

try:
    email_recipients_parameter = os.environ["LADefaultEmailRecipients"]
    LADefaultEmailRecipients = [
        x.strip() for x in email_recipients_parameter.split(",")
    ]
except KeyError:
    LADefaultEmailRecipients = []

# maximum number of contents to be generated in advance
MAX_CONTENT_BALANCE = 3

# max length of the user message
MAX_USER_MESSAGE_LENGTH = 500

# DDoS prevention parameters --------------------------
# window size in seconds to check the number of requests per user
DDOS_WINDOW_SIZE = 30  # seconds
# max request per window time per user
DDOS_MAX_REQUESTS_PER_WINDOW = 15
# penalty in seconds to block the user considering the last request
DDOS_PENALTY = 900  # seconds
# -------------------------- DDoS prevention parameters


# Languages for content generation
LANGUAGE_GENERIC_ENGLISH = {
    "id": 4,
    "ietf_tag": "en",
    "ietf_name": "English",
    "iso_name": "English",
}
DEFAULT_USER_LANGUAGE_ID = LANGUAGE_GENERIC_ENGLISH["id"]
DEFAULT_USER_LANGUAGE_NAME = (
    LANGUAGE_GENERIC_ENGLISH["ietf_tag"]
    + " ("
    + LANGUAGE_GENERIC_ENGLISH["iso_name"]
    + ")"
)

# Default expire time for the topics (in days)
DEFAULT_TOPIC_EXPIRE_TIME = 90

# Minimum confidence for any AI Service
AI_SERVICE_CONFIDENCE_THRESHOLD = 0.75

# Margin of safety for the MAX_TOKENS parameter
MAX_TOKENS_MARGIN = 1  # increase the number of tokens by 100%

# Weights for the ModelProviderCollection
# consider the range between 0 and 1.0
# the sum of all weights must be 1
RUNTIME_WEIGHT = 0.3
ACCURACY_WEIGHT = 0.6
COST_WEIGHT = 0.1

# Number of registers to be used by the model performance updater
MODEL_PERFORMANCE_UPDATER_ROWS_COUNT = 1000

# General default LRU cache size
DEFAULT_LRU_CACHE_SIZE = 100

# Text length threshold for the short text language detection service
SHORT_TEXT_LANGUAGE_DETECTION_THRESHOLD = 25

# RAG docs content-type mapping
RAG_DOCS_CONTENT_TYPE_MAPPING = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/plain": "txt",
    "text/html": "html",
    "application/rtf": "rtf",
}


# Default values for the size of the embeddings
EMBEDDINGS_DIMENSION_SIZE = 2000

################################################################
# APIs Pricing (always in USD)
################################################################

# AWS Bedrock
# see https://aws.amazon.com/bedrock/pricing/
# pricing updated on 2024-02-10
AWS_BEDROCK_PRICE_PER_1K_INPUT_TOKENS = 0.0015
AWS_BEDROCK_PRICE_PER_1K_OUTPUT_TOKENS = 0.0020

# Maritaca
# see https://chat.maritaca.ai/
# pricing updated on 2024-02-10
MARITACA_PRICE_PER_1M_TOKENS = (
    1  # (Currency is BRL, but we are converting to USD as 5/1 ratio)
)

# NlpCloud
# see https://nlpcloud.com/pricing.html
# pricing updated on 2024-02-10
NLP_CLOUD_ON_CPU_PRICE_PER_REQUEST = 0.003
NLP_CLOUD_ON_GPU_PRICE_PER_REQUEST = 0.005
NLP_CLOUD_LLAMA_PRICE_PER_1K_TOKENS = 0.0018

# OpenAI
# see https://openai.com/pricing/
# pricing updated on 2024-02-10
OPENAI_GPT35_PRICE_PER_1K_INPUT_TOKENS = 0.0005
OPENAI_GPT35_PRICE_PER_1K_OUTPUT_TOKENS = 0.0015
OPENAI_GPT4_PRICE_PER_1K_INPUT_TOKENS = 0.01
OPENAI_GPT4_PRICE_PER_1K_OUTPUT_TOKENS = 0.03
OPENAI_EMBEDDINGS_PRICE_PER_1M_INPUT_TOKENS = 0.13

# Google
# see https://ai.google.dev/pricing
# pricing updated on 2024-02-22
GOOGLE_GEMINI_PRO_PRICE_PER_1K_INPUT_CHARS = 0.000125
GOOGLE_GEMINI_PRO_PRICE_PER_1K_OUTPUT_CHARS = 0.000375
