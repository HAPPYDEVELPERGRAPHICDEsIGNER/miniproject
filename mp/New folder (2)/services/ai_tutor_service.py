"""
AI Personal Learning Assistant Service.
Supports configurable providers (Google Gemini, OpenAI).
Constructs rich pedagogical context using syllabus progress, compiler errors, and quiz results.
"""
import os
import logging
from typing import Dict, Any, Optional, List
import httpx
from config import settings

logger = logging.getLogger("smartedu.ai_tutor")

async def get_ai_tutoring_response(
    student_name: str,
    message: str,
    assistance_type: str = "concept",
    subject_title: Optional[str] = None,
    topic_title: Optional[str] = None,
    code_context: Optional[str] = None,
    error_context: Optional[str] = None,
    weak_topics: Optional[List[str]] = None,
    recent_quiz_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generates intelligent pedagogical tutoring assistance.
    Uses configured LLM (Gemini or OpenAI) or sophisticated educational tutor engine.
    """
    system_prompt = _build_tutor_system_prompt(
        student_name=student_name,
        subject_title=subject_title,
        topic_title=topic_title,
        assistance_type=assistance_type,
        weak_topics=weak_topics,
        recent_quiz_score=recent_quiz_score
    )

    user_prompt = f"Student Question: {message}\n"
    if code_context:
        user_prompt += f"\n--- Student Code ---\n{code_context}\n"
    if error_context:
        user_prompt += f"\n--- Compiler / Runtime Error ---\n{error_context}\n"

    # Route to Gemini
    if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            return await _call_gemini_api(system_prompt, user_prompt, assistance_type)
        except Exception as e:
            logger.warning("Gemini API call failed (%s). Using offline educational tutor fallback.", e)
            return _generate_educational_fallback(student_name, message, assistance_type, topic_title, error_context, warning=f"Gemini API unavailable ({str(e)}). Returned offline tutor response.")

    # Route to OpenAI
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            return await _call_openai_api(system_prompt, user_prompt, assistance_type)
        except Exception as e:
            logger.warning("OpenAI API call failed (%s). Using offline educational tutor fallback.", e)
            return _generate_educational_fallback(student_name, message, assistance_type, topic_title, error_context, warning=f"OpenAI API unavailable ({str(e)}). Returned offline tutor response.")

    # Unconfigured or local mode
    return _generate_educational_fallback(
        student_name, message, assistance_type, topic_title, error_context,
        warning="AI API key not configured in .env. Running in built-in pedagogical tutor mode."
    )

def _build_tutor_system_prompt(
    student_name: str,
    subject_title: Optional[str],
    topic_title: Optional[str],
    assistance_type: str,
    weak_topics: Optional[List[str]],
    recent_quiz_score: Optional[float]
) -> str:
    prompt = (
        f"You are the personalized AI Software Engineering & Computer Science Tutor for student '{student_name}'.\n"
        f"Pedagogical Philosophy:\n"
        f"- Never simply provide the full copy-paste answer or homework solution.\n"
        f"- Guide the student step-by-step through Socratic questioning, conceptual explanations, and hints.\n"
        f"- Break down complex algorithms into simple mental models.\n"
        f"- When reviewing code errors, explain WHY the error happened and what invariant was violated.\n"
    )
    if subject_title:
        prompt += f"- Current Enrolled Subject: {subject_title}\n"
    if topic_title:
        prompt += f"- Current Syllabus Topic: {topic_title}\n"
    if weak_topics:
        prompt += f"- Student's Known Weak Concepts: {', '.join(weak_topics[:3])}\n"
    if recent_quiz_score is not None:
        prompt += f"- Recent Quiz Performance: {recent_quiz_score}%\n"

    prompt += (
        f"- Assistance Mode: {assistance_type.upper()}.\n"
        "Format your answer with clear markdown headings, bullet points, and code snippets where appropriate."
    )
    return prompt

async def _call_gemini_api(system_prompt: str, user_prompt: str, assistance_type: str) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates returned from Gemini.")
    
    reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    return {
        "response": reply,
        "assistance_type": assistance_type,
        "provider": "Google Gemini",
        "model": settings.GEMINI_MODEL
    }

async def _call_openai_api(system_prompt: str, user_prompt: str, assistance_type: str) -> Dict[str, Any]:
    url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    reply = data["choices"][0]["message"]["content"]
    return {
        "response": reply,
        "assistance_type": assistance_type,
        "provider": "OpenAI",
        "model": settings.OPENAI_MODEL
    }

def _generate_educational_fallback(
    student_name: str,
    message: str,
    assistance_type: str,
    topic_title: Optional[str] = None,
    error_context: Optional[str] = None,
    warning: Optional[str] = None
) -> Dict[str, Any]:
    """Smart offline pedagogical tutor for when external LLM credentials are not yet configured."""
    topic_str = topic_title or "Software Engineering"
    
    if assistance_type == "error_debug" or error_context:
        resp = (
            f"### 🔍 Debugging Analysis for {student_name}\n\n"
            f"**Observed Issue:**\n```text\n{error_context or 'Execution error encountered'}\n```\n\n"
            "**Key Troubleshooting Steps:**\n"
            "1. **Check Boundary Conditions:** Ensure arrays, loops, or indices do not step beyond collection bounds (e.g., `IndexError` or segmentation faults).\n"
            "2. **Verify Variable Types:** Check if operations match operand types (e.g. attempting arithmetic on `None` or string).\n"
            "3. **Null / None References:** Guarantee that object handles are initialized before calling methods on them.\n"
            "4. **Trace State:** Insert print statements or step through loop iterations to verify variable transitions.\n\n"
            "*Hint:* Test your code on the smallest possible input (e.g. empty list or 1-element input) first to pinpoint the exact failure point."
        )
    elif assistance_type == "hint":
        resp = (
            f"### 💡 Conceptual Hint on *{topic_str}*\n\n"
            f"Hello {student_name}! To solve this challenge on **{topic_str}** without giving away the direct answer:\n\n"
            "- **Invariance Principle:** What property must remain true after every iteration of your logic?\n"
            "- **Subproblems:** Can this problem be divided into base cases and recursive/iterative steps?\n"
            "- **Time & Space Tradeoff:** Can an auxiliary hash map or two-pointer technique reduce $O(N^2)$ to $O(N)$?\n\n"
            "Try drafting pseudo-code for the base case first before coding the general loop."
        )
    elif assistance_type == "practice":
        resp = (
            f"### 📝 Practice Challenge for *{topic_str}*\n\n"
            f"Here is a targeted problem to reinforce **{topic_str}**:\n\n"
            "**Problem:** Implement a function that processes an incoming collection and detects duplicate elements within a sliding window of size $k$.\n"
            "- **Constraint:** Time complexity must be strictly under $O(N \\log N)$.\n"
            "- **Edge Cases:** Handle $k \\le 1$ and empty arrays gracefully.\n\n"
            "Write your solution in the **Personal Coding Platform** tab and run tests to verify!"
        )
    else:
        resp = (
            f"### 🎓 Concept Breakdown: *{topic_str}*\n\n"
            f"Hello {student_name}! Here is a structured overview addressing your query:\n\n"
            f"**Core Principle:**\n"
            f"In computer science, **{topic_str}** is centered on structuring state and computational operations efficiently to achieve predictable performance and correctness.\n\n"
            "**Key Mental Model:**\n"
            "- **Input / Output Contracts:** Define pre-conditions and post-conditions explicitly.\n"
            "- **Algorithmic Flow:** Trace data transformations from source to sink.\n"
            "- **Common Pitfalls:** Watch out for unhandled edge states, off-by-one indices, and resource leaks.\n\n"
            "Would you like a step-by-step hint on writing code for this or a quick quiz question to check your understanding?"
        )

    if warning:
        resp += f"\n\n> ℹ️ *Note: {warning}*"

    return {
        "response": resp,
        "assistance_type": assistance_type,
        "provider": "SmartEdu Pedagogical Engine (Offline Tutor)",
        "model": "Rule-Based Socratic Guide"
    }
