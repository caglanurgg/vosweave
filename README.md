
# 🦊 VosWeave

**Personalized reading practice for language learners, built with AI.**

VosWeave is an AI-powered language reading application that generates level-aware reading content and combines it with vocabulary support and active recall. It helps learners practice reading through content tailored to their selected language, proficiency level, interests, and learning goals.

Beyond the learning experience, VosWeave explores practical engineering challenges in AI-powered applications, including text processing, vocabulary matching, learner-state management, usage limits, and response caching.

## 🚀 Live Demo

**[Try VosWeave](https://vosweave.streamlit.app)**

Sign in with Google to access the application.

## ✨ Features

- **AI-Generated Reading Content** — Generate reading passages based on the selected language, CEFR level, topic, tone, and target word count.
- **Vocabulary Highlighting** — Identify vocabulary in reading passages, including supported word variations and inflected forms.
- **Vocabulary Heatmap** — Visualize vocabulary-related learner data and track learning patterns.
- **Active Recall** — Practice recalling information from reading sessions and receive AI-generated feedback.
- **Learner-State Management** — Organize reading and vocabulary-related state by user and language.
- **Shared Daily AI Quota** — Apply a daily limit of 10 operations shared between reading generation and Active Recall evaluation.
- **Response Caching** — Reuse cached responses to reduce unnecessary repeated AI requests.
- **Google Authentication** — Sign in through the application's configured OpenID Connect authentication flow.

## 🛠 Engineering Highlights

### Vocabulary Matching Beyond Exact Words

Vocabulary matching involves more than searching for an exact string. Words can appear with different endings, inflections, or accent variations.

The `highlighter.py` module uses pattern-based matching logic to handle supported word variations, including accent-insensitive matching and suffix-related cases. This helps vocabulary highlighting work across more than just exact word matches.

### Shared AI Usage Quota

Reading generation and Active Recall evaluation share a daily quota of 10 operations. The `quota_manager.py` module centralizes usage-limit handling instead of treating each feature as an independent allowance.

### User- and Language-Aware State

The `storage.py` module organizes learner-related state by user and language. This structure supports separating reading sessions, vocabulary progress, and analytics across different learning contexts.

### AI-Powered Learning Interactions

The `ai_engine.py` module handles AI-powered reading generation and Active Recall evaluation through the OpenAI API. Separating these responsibilities from the interface makes the main application flow easier to maintain.

### Modular Application Design

VosWeave separates interface components, AI interactions, text processing, analytics, quota management, and persistence into dedicated Python modules. This structure makes individual responsibilities easier to understand and evolve.

## 🏗 Architecture

| Module | Responsibility |
|---|---|
| `app.py` | Main Streamlit application flow |
| `ui.py` | User interface components and styling |
| `ai_engine.py` | OpenAI integration, reading generation, and Active Recall evaluation |
| `highlighter.py` | Vocabulary matching and text highlighting |
| `analytics.py` | Learner analytics and learning-related rules |
| `quota_manager.py` | Shared daily operation limits |
| `storage.py` | User- and language-aware state persistence |

## 💻 Tech Stack

- **Language:** Python
- **Application Framework:** Streamlit
- **AI Integration:** OpenAI API
- **Authentication:** Authlib and OpenID Connect
- **Data Persistence:** JSON-based storage
- **Caching and Usage Management:** Application-managed caching and quota logic

## 🏁 Getting Started

### Prerequisites

- Python
- An OpenAI API key
- The authentication configuration required by your environment

### Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/caglanurgg/vosweave.git
cd vosweave
pip install -r requirements.txt
```

### Configuration

Configure the required API credentials and authentication settings using Streamlit secrets or the appropriate local configuration for your environment.

**Never commit API keys, OAuth client secrets, or other credentials to the repository.**

### Run Locally

Start the application with:

```bash
streamlit run app.py
```

Some configuration values may need to be set before all features are available locally.

## 🎯 Project Focus

VosWeave is an ongoing project exploring how AI-generated reading content can be combined with vocabulary interaction, Active Recall, and learner-state tracking.

Development focuses on improving text-matching behavior, managing AI usage, organizing learner data, and maintaining a modular application structure.

## 👤 Author

Developed by [caglanurgg](https://github.com/caglanurgg).

- **Live Application:** [vosweave.streamlit.app](https://vosweave.streamlit.app)
- **Source Code:** [github.com/caglanurgg/vosweave](https://github.com/caglanurgg/vosweave)
