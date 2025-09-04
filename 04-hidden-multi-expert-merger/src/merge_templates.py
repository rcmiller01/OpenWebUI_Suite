"""
Deterministic merge templates for Hidden Multi-Expert Merger
Combines draft, helper critiques, and persona into final text
"""

from typing import List
import re


class MergeTemplate:
    """Base class for merge templates"""

    def merge(self, draft: str, critiques: List[str],
              persona: str, tone_policy: List[str]) -> str:
        """Merge draft with critiques using persona and tone policy"""
        raise NotImplementedError


class PersonaPreservingMerger(MergeTemplate):
    """Template that preserves persona while incorporating critiques"""

    def merge(self, draft: str, critiques: List[str],
              persona: str, tone_policy: List[str]) -> str:
        # Clean critiques by removing tool chatter and self-references
        cleaned_critiques = []
        for critique in critiques:
            cleaned = self._clean_critique(critique)
            if cleaned.strip():
                cleaned_critiques.append(cleaned)

        # Apply tone policy filters
        filtered_critiques = self._apply_tone_policy(
            cleaned_critiques, tone_policy)

        # Merge with persona preservation
        merged = self._merge_with_persona(draft, filtered_critiques, persona)

        return merged

    def _clean_critique(self, critique: str) -> str:
        """Remove tool chatter, self-references, and meta-commentary"""
        # Remove common tool chatter patterns
        patterns_to_remove = [
            r'\b(?:I|me|my|mine)\b.*?(?:think|believe|feel|suggest)',  # Self-references
            r'\b(?:As an AI|As a model|As a language model)\b.*?[:.]',  # AI self-identification
            r'\b(?:Let me|I should|I can|I will)\b.*?(?:help|assist|provide)',  # Helper language
            r'\b(?:This is|Here is|The following is)\b.*?(?:my|the|a)\s+(?:analysis|critique|feedback)',  # Meta-introductions
            r'\b(?:Overall|In summary|To conclude)\b.*?:',  # Summary markers
            r'\b(?:Please|You should|Consider)\b.*?(?:using|trying|considering)',  # Directive language
        ]

        cleaned = critique
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        # Remove extra whitespace and empty lines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def _apply_tone_policy(self, critiques: List[str], tone_policy: List[str]) -> List[str]:
        """Filter critiques based on tone policy"""
        if not tone_policy:
            return critiques

        filtered = []
        for critique in critiques:
            # Check if critique violates any tone policies
            violates_policy = False
            for policy in tone_policy:
                if policy.lower() in critique.lower():
                    violates_policy = True
                    break

            if not violates_policy:
                filtered.append(critique)

        return filtered

    def _merge_with_persona(self, draft: str, critiques: List[str], persona: str) -> str:
        """Merge draft with critiques while preserving persona"""
        if not critiques:
            return draft

        # Extract key improvements from critiques
        improvements = []
        for critique in critiques:
            # Look for specific improvement suggestions
            improvement_patterns = [
                r'(?:improve|better|enhance|strengthen).*?(?:by|with|through)\s+(.*?)(?:\n|$|;)',
                r'(?:add|include|incorporate).*?(?:more|additional|further)\s+(.*?)(?:\n|$|;)',
                r'(?:remove|eliminate|avoid).*?(?:the|this|that)\s+(.*?)(?:\n|$|;)',
                r'(?:change|modify|adjust).*?(?:to|into|from)\s+(.*?)(?:\n|$|;)',
            ]

            for pattern in improvement_patterns:
                matches = re.findall(pattern, critique, re.IGNORECASE)
                improvements.extend(matches)

        # Create merged text with persona preservation
        merged_parts = []

        # Start with persona context if present
        if persona and persona.lower() not in draft.lower():
            merged_parts.append(f"[{persona}]")

        # Add original draft
        merged_parts.append(draft)

        # Add improvements as integrated suggestions
        if improvements:
            improvement_text = " ".join(improvements[:3])  # Limit to top 3 improvements
            if improvement_text:
                merged_parts.append(f"\n\n[Improvements: {improvement_text}]")

        return "".join(merged_parts)


class ConciseExecutiveMerger(MergeTemplate):
    """Template for concise executive communication"""

    def merge(self, draft: str, critiques: List[str], persona: str, tone_policy: List[str]) -> str:
        # Clean and filter critiques
        merger = PersonaPreservingMerger()
        cleaned_critiques = [merger._clean_critique(c) for c in critiques]
        filtered_critiques = merger._apply_tone_policy(cleaned_critiques, tone_policy)

        # Extract only the most critical points
        critical_points = []
        for critique in filtered_critiques:
            # Look for high-priority improvements
            priority_patterns = [
                r'(?:critical|important|essential|key).*?(?:to|for|is)\s+(.*?)(?:\n|$|;)',
                r'(?:must|should|need to).*?(?:be|have|include)\s+(.*?)(?:\n|$|;)',
                r'(?:problem|issue|concern).*?(?:with|regarding)\s+(.*?)(?:\n|$|;)',
            ]

            for pattern in priority_patterns:
                matches = re.findall(pattern, critique, re.IGNORECASE)
                critical_points.extend(matches)

        # Create concise merged version
        if critical_points:
            concise_draft = f"{draft}\n\n[Key Points: {'; '.join(critical_points[:2])}]"
        else:
            concise_draft = draft

        # Add persona if not present
        if persona and persona.lower() not in concise_draft.lower():
            return f"[{persona}] {concise_draft}"

        return concise_draft


class CreativeEnhancementMerger(MergeTemplate):
    """Template for creative writing enhancement"""

    def merge(self, draft: str, critiques: List[str], persona: str, tone_policy: List[str]) -> str:
        # Clean critiques
        merger = PersonaPreservingMerger()
        cleaned_critiques = [merger._clean_critique(c) for c in critiques]
        filtered_critiques = merger._apply_tone_policy(cleaned_critiques, tone_policy)

        # Extract creative enhancements
        enhancements = []
        for critique in filtered_critiques:
            creative_patterns = [
                r'(?:add|include|enhance).*?(?:vivid|colorful|engaging|compelling)\s+(.*?)(?:\n|$|;)',
                r'(?:improve|strengthen).*?(?:imagery|metaphor|description|rhythm)\s+(.*?)(?:\n|$|;)',
                r'(?:make|create).*?(?:more|better|stronger)\s+(.*?)(?:\n|$|;)',
            ]

            for pattern in creative_patterns:
                matches = re.findall(pattern, critique, re.IGNORECASE)
                enhancements.extend(matches)

        # Apply creative enhancements
        enhanced_draft = draft

        if enhancements:
            # Add creative elements
            creative_addition = f"\n\n[Creative Enhancement: {'; '.join(enhancements[:2])}]"
            enhanced_draft += creative_addition

        # Preserve persona
        if persona and persona.lower() not in enhanced_draft.lower():
            return f"[{persona}]\n{enhanced_draft}"

        return enhanced_draft


def get_merge_template(template_name: str) -> MergeTemplate:
    """Factory function to get merge template by name"""
    templates = {
        "persona_preserving": PersonaPreservingMerger(),
        "concise_executive": ConciseExecutiveMerger(),
        "creative_enhancement": CreativeEnhancementMerger(),
    }

    return templates.get(template_name, PersonaPreservingMerger())
