"""
PLS Evaluation Tool for the Medical Writing API
Evaluates text against Plain Language Summary thresholds and provides feedback.
"""

import json
import os
from typing import Dict, Any, List, Optional
from api.core.base_tool import BaseTool
from api.schemas.base import ToolInfo, ToolResponse
from api.tools.linguistic_analysis_tool import LinguisticAnalysisTool


class PLSEvaluationTool(BaseTool):
    """Tool for evaluating Plain Language Summary compliance"""
    
    def __init__(self):
        """Initialize the PLS evaluation tool"""
        self._linguistic_tool = LinguisticAnalysisTool()
        self._thresholds = None
        
        # Features to evaluate
        self.recommended_features = [
            # CRITICAL FEATURES (Explicitly mentioned)
            'words_per_sentence',        # 20-word rule
            'passive_voice',             # Use active voice
            'active_voice',              # Complement
            'sentences_per_paragraph',   # Keep paragraphs short
            'pronouns',                  # Use we/you
            'nominalization',            # Use verbs, not nouns
            'verbs',
            'nouns',
            'numbers',

            # READABILITY (Reading age of 11 years)
            'flesch_reading_ease',
            'flesch_kincaid_grade',
            'automated_readability_index',
            'coleman_liau_index',
            'gunning_fog_index',
            'lix',
            'rix',
            'smog_index',
            'dale_chall_readability',

            # VOCABULARY COMPLEXITY
            'complex_words_dc',          # Difficult words
            'complex_words',
            'long_words',                # Avoid long words
            'syllables_per_word',        # Simplicity
            'polysyllables',

            # SECONDARY INDICATORS
            'tobeverb',                  # Weak verbs
            'auxverb',                   # Verbal complexity
            'subordinating_conjunctions', # Complex sentences

            # BASIC CONTEXT
            'words',                     # Total words
            'sentences',                 # Total sentences
            'paragraphs'                 # Structure
        ]
    
    @property
    def thresholds(self) -> Dict[str, Any]:
        """Lazy loading of thresholds data"""
        if self._thresholds is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            thresholds_path = os.path.join(current_dir, '../data/pls_evaluation_thresholds_from_data.json')
            
            with open(thresholds_path, 'r') as f:
                self._thresholds = json.load(f)
        
        return self._thresholds
    
    @property
    def info(self) -> ToolInfo:
        """Return tool information"""
        return ToolInfo(
            name="pls_evaluation",
            description="Evaluate text against Plain Language Summary thresholds and provide improvement recommendations",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to evaluate for PLS compliance"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "text"],
                        "description": "Output format: 'json' for structured data or 'text' for human-readable format",
                        "default": "json"
                    }
                },
                "required": ["text"]
            },
            version="1.0.0"
        )
    
    def _evaluate_metric(self, feature: str, value: float, thresholds: Dict[str, float], direction: str) -> Dict[str, Any]:
        """Evaluate a single metric against thresholds"""
        
        if direction == "higher_better":
            # For metrics where higher is better, P75 represents the best 25%
            if value >= thresholds["excellent"]:
                rating = "P75"  # Best 25% of corpus
            elif value >= thresholds["good"]:
                rating = "P50"  # Median
            elif value >= thresholds["acceptable"]:
                rating = "P25"  # 25th percentile
            elif value >= thresholds["poor"]:
                rating = "P10"  # 10th percentile
            else:
                rating = "BELOW_P10"  # Below 10th percentile
        else:  # lower_better
            # For metrics where lower is better, P25 represents the best 25%
            if value <= thresholds["excellent"]:
                rating = "P25"  # Best 25% of corpus
            elif value <= thresholds["good"]:
                rating = "P50"  # Median
            elif value <= thresholds["acceptable"]:
                rating = "P75"  # 75th percentile
            elif value <= thresholds["poor"]:
                rating = "P90"  # 90th percentile
            else:
                rating = "BEYOND_P90"  # Beyond 90th percentile
        
        # Generate feedback for metrics deviating from typical patterns
        feedback = None
        if direction == "higher_better":
            if rating in ["P10", "BELOW_P10"]:
                target = thresholds["good"]
                feedback = f"Deviates from typical PLS patterns. Consider increasing from {value:.1f} to >{target:.1f} (median)"
        else:  # lower_better
            if rating in ["P90", "BEYOND_P90"]:
                target = thresholds["good"]
                feedback = f"Deviates from typical PLS patterns. Consider reducing from {value:.1f} to <{target:.1f} (median)"
        
        return {
            "value": value,
            "rating": rating,
            "direction": direction,
            "feedback": feedback
        }
    
    def _evaluate_word_count(self, word_count: int, limit: int = 850) -> Dict[str, Any]:
        """Evaluate word count against PLS limit"""
        status = "within_limit" if word_count <= limit else "over_limit"
        symbol = "✓" if status == "within_limit" else "✗"
        
        return {
            "word_count": word_count,
            "limit": limit,
            "status": status,
            "message": f"Word count: {word_count} {symbol} {'WITHIN LIMIT' if status == 'within_limit' else 'OVER LIMIT'} (≤{limit} words)"
        }
    
    def _format_text_output(self, evaluation_data: Dict[str, Any]) -> str:
        """Format evaluation as human-readable text"""
        lines = []
        
        # Word count
        word_count_info = evaluation_data["word_count_status"]
        lines.append(word_count_info["message"])
        lines.append(f"Sentences: {evaluation_data['linguistic_evaluation']['sentences']['value']}")
        lines.append("")
        
        # Metric evaluation
        lines.append("METRIC EVALUATION:")
        
        # Group by rating for better readability
        by_rating = {"P25": [], "P50": [], "P75": [], "P90": [], "P10": [], "BEYOND_P90": [], "BELOW_P10": []}
        
        for feature, data in evaluation_data["linguistic_evaluation"].items():
            if feature in ["words", "sentences"]:
                continue
            
            rating = data["rating"]
            direction_symbol = "↑" if data["direction"] == "higher_better" else "↓"
            
            if rating in by_rating:
                by_rating[rating].append(f"{feature:<30} {direction_symbol} = {data['value']:8.2f} → {rating.upper()}")
        
        # Display metrics (order by best to worst, considering both directions)
        # For lower_better metrics: P25, P50, P75, P90, BEYOND_P90
        # For higher_better metrics: P75, P50, P25, P10, BELOW_P10
        for rating in ["P25", "P75", "P50", "P90", "P10", "BEYOND_P90", "BELOW_P10"]:
            if rating in by_rating:
                for line in by_rating[rating]:
                    lines.append(line)
        
        lines.append("")
        
        # Summary
        summary = evaluation_data["summary"]
        lines.append("STATISTICAL CONFORMITY SUMMARY:")
        lines.append("")
        lines.append("Percentile ranges (proportion of corpus):")
        
        # Show P25 and P75 together as they represent best quartile
        best_quartile_total = summary.get('P25_count', 0) + summary.get('P75_count', 0)
        best_quartile_pct = summary.get('P25_percentage', 0) + summary.get('P75_percentage', 0)
        lines.append(f"  Best quartile (P25/P75): {best_quartile_total:3} features ({best_quartile_pct:.1f}%)")
        lines.append(f"  Median (P50):            {summary.get('P50_count', 0):3} features ({summary.get('P50_percentage', 0):.1f}%)")
        
        # Show deviations
        if summary.get('P90_count', 0) > 0:
            lines.append(f"  P90 range:               {summary['P90_count']:3} features ({summary['P90_percentage']:.1f}%)")
        if summary.get('P10_count', 0) > 0:
            lines.append(f"  P10 range:               {summary['P10_count']:3} features ({summary['P10_percentage']:.1f}%)")
        if summary.get('BEYOND_P90_count', 0) > 0:
            lines.append(f"  Beyond P90:              {summary['BEYOND_P90_count']:3} features ({summary['BEYOND_P90_percentage']:.1f}%)")
        if summary.get('BELOW_P10_count', 0) > 0:
            lines.append(f"  Below P10:               {summary['BELOW_P10_count']:3} features ({summary['BELOW_P10_percentage']:.1f}%)")
        
        lines.append("")
        lines.append(f"Overall Pattern Conformity: {summary['overall_assessment']}")
        lines.append(f"Best Quartile Rate: {summary['best_quartile_rate']:.1f}%")
        lines.append("")
        
        # Pattern deviation recommendations
        recommendations = []
        for feature, data in evaluation_data["linguistic_evaluation"].items():
            if data.get("feedback"):
                recommendations.append(f"   {len(recommendations)+1}. {feature}: {data['feedback']}")
        
        if recommendations:
            lines.append("PATTERN DEVIATION ANALYSIS")
            lines.append(f"Features deviating from typical PLS patterns ({len(recommendations)} features):")
            lines.extend(recommendations)
        else:
            lines.append("All metrics conform to typical PLS statistical patterns.")
        
        return "\n".join(lines)
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute PLS evaluation"""
        try:
            text = parameters.get("text")
            output_format = parameters.get("format", "json")
            
            if not text:
                return ToolResponse(
                    tool_name="pls_evaluation",
                    status="error",
                    error="'text' parameter is required"
                )
            
            # Get linguistic analysis
            linguistic_response = await self._linguistic_tool.execute({
                "text": text,
                "include_tokens": False
            })
            
            if linguistic_response.status != "success":
                return ToolResponse(
                    tool_name="pls_evaluation",
                    status="error",
                    error=f"Linguistic analysis failed: {linguistic_response.error}"
                )
            
            features = linguistic_response.result
            
            # Word count evaluation
            word_count = features.get("words", 0)
            sentences_count = features.get("sentences", 0)
            word_count_status = self._evaluate_word_count(word_count)
            
            # Evaluate each metric
            linguistic_evaluation = {}
            
            # Add basic info metrics
            linguistic_evaluation["words"] = {
                "value": word_count,
                "rating": "within_limit" if word_count <= 850 else "over_limit",
                "direction": None,
                "feedback": None
            }
            
            linguistic_evaluation["sentences"] = {
                "value": sentences_count,
                "rating": "info",
                "direction": None,
                "feedback": None
            }
            
            # Evaluate other metrics
            rating_counts = {"P25": 0, "P50": 0, "P75": 0, "P90": 0, "P10": 0, "BEYOND_P90": 0, "BELOW_P10": 0}
            
            for feature in self.recommended_features:
                if feature in ["words", "sentences"]:
                    continue
                    
                if feature not in features:
                    continue
                    
                if feature not in self.thresholds:
                    continue
                
                value = features[feature]
                threshold_data = self.thresholds[feature]
                direction = threshold_data["direction"]
                
                evaluation = self._evaluate_metric(feature, value, threshold_data, direction)
                linguistic_evaluation[feature] = evaluation
                
                # Count ratings (excluding basic info)
                rating_counts[evaluation["rating"]] += 1
            
            # Calculate summary
            total_evaluated = sum(rating_counts.values())
            
            if total_evaluated > 0:
                # Count features in best quartile (P25 for lower_better, P75 for higher_better)
                best_quartile = rating_counts.get("P25", 0) + rating_counts.get("P75", 0)
                median_range = rating_counts.get("P50", 0)
                best_quartile_rate = (best_quartile / total_evaluated) * 100
                
                # Determine overall conformity with typical PLS patterns
                if best_quartile_rate >= 60:
                    overall = "HIGHLY CONFORMS TO TYPICAL PLS PATTERNS"
                elif (best_quartile + median_range) >= total_evaluated * 0.7:
                    overall = "GOOD CONFORMITY WITH PLS PATTERNS"
                elif (best_quartile + median_range) >= total_evaluated * 0.5:
                    overall = "MODERATE CONFORMITY WITH PLS PATTERNS"
                else:
                    overall = "DEVIATES FROM TYPICAL PLS PATTERNS"
            else:
                best_quartile_rate = 0
                overall = "NO EVALUATION POSSIBLE"
            
            summary = {
                "P25_count": rating_counts.get("P25", 0),
                "P50_count": rating_counts.get("P50", 0),
                "P75_count": rating_counts.get("P75", 0),
                "P90_count": rating_counts.get("P90", 0),
                "P10_count": rating_counts.get("P10", 0),
                "BEYOND_P90_count": rating_counts.get("BEYOND_P90", 0),
                "BELOW_P10_count": rating_counts.get("BELOW_P10", 0),
                "total_evaluated": total_evaluated,
                "P25_percentage": (rating_counts.get("P25", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "P50_percentage": (rating_counts.get("P50", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "P75_percentage": (rating_counts.get("P75", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "P90_percentage": (rating_counts.get("P90", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "P10_percentage": (rating_counts.get("P10", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "BEYOND_P90_percentage": (rating_counts.get("BEYOND_P90", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "BELOW_P10_percentage": (rating_counts.get("BELOW_P10", 0) / total_evaluated * 100) if total_evaluated > 0 else 0,
                "best_quartile_rate": best_quartile_rate,
                "overall_assessment": overall
            }
            
            # Prepare result
            evaluation_data = {
                "linguistic_evaluation": linguistic_evaluation,
                "word_count_status": word_count_status,
                "summary": summary
            }
            
            # Format output
            if output_format == "text":
                formatted_result = self._format_text_output(evaluation_data)
                return ToolResponse(
                    tool_name="pls_evaluation",
                    status="success",
                    result=formatted_result
                )
            else:
                return ToolResponse(
                    tool_name="pls_evaluation",
                    status="success",
                    result=evaluation_data
                )
                
        except Exception as e:
            return ToolResponse(
                tool_name="pls_evaluation",
                status="error",
                error=f"PLS evaluation failed: {str(e)}"
            )