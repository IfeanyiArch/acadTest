import re
from typing import Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from abc import ABC, abstractmethod


class BaseGradingService(ABC):
    """Abstract base class for grading services"""

    @abstractmethod
    def grade_answer(self, question, answer_text: str) -> Dict:
        """
        Grade a single answer
        Returns: {
            'score': float,
            'feedback': str,
            'is_correct': bool,
            'metadata': dict
        }
        """
        pass


class MockGradingService(BaseGradingService):
    """
    Mock grading service using keyword matching and text similarity
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def grade_answer(self, question, answer_text: str) -> Dict:
        """Grade answer using multiple techniques based on question type"""

        if question.question_type == "MCQ" or question.question_type == "TRUE_FALSE":
            return self._grade_mcq(question, answer_text)
        elif question.question_type == "SHORT":
            return self._grade_short_answer(question, answer_text)
        else:  # LONG or ESSAY
            return self._grade_long_answer(question, answer_text)

    def _grade_mcq(self, question, answer_text: str) -> Dict:
        """Grade multiple choice questions with exact matching"""
        expected = self._normalize_text(question.expected_answer)
        submitted = self._normalize_text(answer_text)

        is_correct = expected == submitted
        score = float(question.marks) if is_correct else 0.0

        feedback = (
            "Correct answer!"
            if is_correct
            else f"Incorrect. Expected: {question.expected_answer}"
        )

        return {
            "score": score,
            "feedback": feedback,
            "is_correct": is_correct,
            "metadata": {
                "grading_method": "exact_match",
                "expected": expected,
                "submitted": submitted,
            },
        }

    def _grade_short_answer(self, question, answer_text: str) -> Dict:
        """Grade short answers using keyword matching and similarity"""

        # Calculate keyword match score
        keyword_score = self._calculate_keyword_score(question, answer_text)

        # Calculate text similarity score
        similarity_score = self._calculate_similarity(
            question.expected_answer, answer_text
        )

        # Weighted combination (60% keywords, 40% similarity)
        combined_score = (0.6 * keyword_score) + (0.4 * similarity_score)

        # Calculate final score - convert question.marks to float
        final_score = float(question.marks) * combined_score

        # Determine if correct (threshold: 70%)
        is_correct = combined_score >= 0.7

        feedback = self._generate_feedback(
            combined_score, keyword_score, similarity_score
        )

        return {
            "score": round(final_score, 2),
            "feedback": feedback,
            "is_correct": is_correct,
            "metadata": {
                "grading_method": "keyword_similarity",
                "keyword_score": round(keyword_score, 2),
                "similarity_score": round(similarity_score, 2),
                "combined_score": round(combined_score, 2),
            },
        }

    def _grade_long_answer(self, question, answer_text: str) -> Dict:
        """Grade long answers and essays"""

        # Length check
        length_score = self._calculate_length_score(answer_text)

        # Keyword density
        keyword_score = self._calculate_keyword_score(question, answer_text)

        # Semantic similarity
        similarity_score = self._calculate_similarity(
            question.expected_answer, answer_text
        )

        # Weighted combination (30% length, 30% keywords, 40% similarity)
        combined_score = (
            (0.3 * length_score) + (0.3 * keyword_score) + (0.4 * similarity_score)
        )

        # Calculate final score - convert question.marks to float
        final_score = float(question.marks) * combined_score
        is_correct = combined_score >= 0.6

        feedback = self._generate_detailed_feedback(
            combined_score, length_score, keyword_score, similarity_score, answer_text
        )

        return {
            "score": round(final_score, 2),
            "feedback": feedback,
            "is_correct": is_correct,
            "metadata": {
                "grading_method": "comprehensive",
                "length_score": round(length_score, 2),
                "keyword_score": round(keyword_score, 2),
                "similarity_score": round(similarity_score, 2),
                "combined_score": round(combined_score, 2),
                "word_count": len(answer_text.split()),
            },
        }

    def _calculate_keyword_score(self, question, answer_text: str) -> float:
        """Calculate score based on keyword matching"""

        # Get keywords from grading criteria or extract from expected answer
        keywords = question.grading_criteria.get("keywords", [])

        if not keywords:
            # Extract keywords from expected answer
            keywords = self._extract_keywords(question.expected_answer)

        if not keywords:
            return 0.5  # Neutral score if no keywords

        # Normalize texts
        answer_lower = answer_text.lower()

        # Count matched keywords
        matched = sum(1 for kw in keywords if kw.lower() in answer_lower)

        return matched / len(keywords) if keywords else 0.5

    def _calculate_similarity(self, expected: str, submitted: str) -> float:
        """Calculate cosine similarity between texts"""

        if not expected.strip() or not submitted.strip():
            return 0.0

        try:
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform([expected, submitted])

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)
        except Exception:
            # Fallback to simple word overlap
            expected_words = set(expected.lower().split())
            submitted_words = set(submitted.lower().split())

            if not expected_words:
                return 0.0

            overlap = len(expected_words.intersection(submitted_words))
            return overlap / len(expected_words)

    def _calculate_length_score(self, text: str) -> float:
        """Calculate score based on answer length"""
        word_count = len(text.split())

        # Scoring based on word count ranges
        if word_count < 50:
            return 0.3
        elif word_count < 100:
            return 0.6
        elif word_count < 200:
            return 0.9
        else:
            return 1.0

    def _extract_keywords(self, text: str, top_n: int = 5) -> list:
        """Extract important keywords from text"""
        # Remove common words and extract nouns/important terms
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

        # Simple frequency-based extraction
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Return top N keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        return text.strip().upper()

    def _generate_feedback(
        self, combined: float, keyword: float, similarity: float
    ) -> str:
        """Generate feedback for short answers"""
        if combined >= 0.9:
            return "Excellent answer! Well done."
        elif combined >= 0.7:
            return "Good answer. You covered the main points."
        elif combined >= 0.5:
            return "Partial credit. Your answer covers some key concepts but could be improved."
        else:
            return "Your answer needs improvement. Please review the key concepts."

    def _generate_detailed_feedback(
        self,
        combined: float,
        length: float,
        keyword: float,
        similarity: float,
        answer: str,
    ) -> str:
        """Generate detailed feedback for long answers"""
        feedback_parts = []

        # Overall assessment
        if combined >= 0.8:
            feedback_parts.append("Excellent comprehensive answer!")
        elif combined >= 0.6:
            feedback_parts.append("Good answer with room for improvement.")
        else:
            feedback_parts.append("Your answer needs significant improvement.")

        # Length feedback
        word_count = len(answer.split())
        if length < 0.6:
            feedback_parts.append(
                f"Consider expanding your answer (current: {word_count} words)."
            )

        # Keyword coverage
        if keyword < 0.5:
            feedback_parts.append("Include more key concepts from the topic.")

        # Similarity feedback
        if similarity < 0.4:
            feedback_parts.append(
                "Your answer could align better with the expected content."
            )

        return " ".join(feedback_parts)


class LLMGradingService(BaseGradingService):
    """
    LLM-based grading service
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def grade_answer(self, question, answer_text: str) -> Dict:
        """
        Grade answer using LLM

        Example implementation with OpenAI:

        import openai

        prompt = f'''
        Question: {question.question_text}
        Expected Answer: {question.expected_answer}
        Student Answer: {answer_text}
        Max Marks: {question.marks}

        Grade the student's answer and provide:
        1. Score (0-{question.marks})
        2. Feedback
        3. Is it correct? (true/false)
        '''

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response and return structured data
        """

        raise NotImplementedError("LLM grading service not implemented")


# Factory function to get grading service
def get_grading_service(service_type: str = "mock") -> BaseGradingService:
    """Factory function to instantiate grading service"""
    if service_type == "mock":
        return MockGradingService()
    elif service_type == "llm":
        return LLMGradingService()
    else:
        return MockGradingService()
