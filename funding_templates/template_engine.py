"""
Template Engine for Funding Application Question Generation
Loads JSON templates and generates smart questions based on user intake data
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class FundingTemplate:
    """Represents a single funding program template with questions and checklist"""
    
    def __init__(self, template_path: str):
        """Load template from JSON file"""
        with open(template_path, 'r') as f:
            self.data = json.load(f)
        
        self.program_id = self.data.get('program_id')
        self.program_name = self.data.get('program_name')
    
    def get_questions(self, user_intake: Dict) -> List[Dict]:
        """
        Get relevant questions based on user intake data
        
        Args:
            user_intake: Dictionary with project details (region, budget, project_types, etc.)
            
        Returns:
            List of question dictionaries, sorted by priority
        """
        relevant_questions = []
        
        for q in self.data.get('questions', []):
            # Check if question is conditional
            if 'conditional' in q:
                if not self._evaluate_condition(q['conditional'], user_intake):
                    continue
            
            # Check if question is triggered by user's project
            if 'triggers' in q:
                user_text = ' '.join(str(v).lower() for v in user_intake.values() if v)
                if not any(trigger.lower() in user_text for trigger in q['triggers']):
                    continue
            
            # Personalize question with user data
            question_text = q['question']
            
            # Replace placeholders with actual values
            if '{project_size}' in question_text:
                project_size = user_intake.get('project_size', user_intake.get('hectares', 'X'))
                question_text = question_text.format(project_size=project_size)
            
            if '{budget}' in question_text:
                budget = user_intake.get('budget_range', user_intake.get('budget', 'X'))
                question_text = question_text.format(budget=budget)
            
            # Create question dict with personalized content
            personalized_q = {
                **q,
                'question': question_text
            }
            
            # Add smart defaults based on region if available
            if 'smart_default' in q and user_intake.get('region'):
                region = user_intake['region'].lower()
                for key, default_text in q['smart_default'].items():
                    if key.lower() in region:
                        personalized_q['hint'] = default_text
                        break
            
            relevant_questions.append(personalized_q)
        
        # Sort by category priority: critical > project_specific > strengthen
        priority_order = {'critical': 0, 'project_specific': 1, 'strengthen': 2}
        relevant_questions.sort(
            key=lambda x: (
                priority_order.get(x.get('category'), 3),
                -x.get('scoring_weight', 0)  # Within category, sort by weight
            )
        )
        
        return relevant_questions
    
    def _evaluate_condition(self, condition: Dict, user_intake: Dict) -> bool:
        """
        Evaluate conditional logic to determine if question should be shown
        
        Args:
            condition: Dict with 'field', 'operator', 'value' keys
            user_intake: User's project data
            
        Returns:
            True if condition is met, False otherwise
        """
        field_value = user_intake.get(condition['field'])
        operator = condition['operator']
        compare_value = condition['value']
        
        # Handle None values
        if field_value is None:
            return False
        
        # Numeric comparisons
        if operator == '<':
            try:
                return float(field_value) < float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == '>':
            try:
                return float(field_value) > float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == '<=':
            try:
                return float(field_value) <= float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == '>=':
            try:
                return float(field_value) >= float(compare_value)
            except (ValueError, TypeError):
                return False
        
        # Equality checks
        elif operator == '==':
            return str(field_value).lower() == str(compare_value).lower()
        elif operator == '!=':
            return str(field_value).lower() != str(compare_value).lower()
        
        # String/list contains
        elif operator == 'contains':
            if isinstance(field_value, list):
                return any(str(compare_value).lower() in str(v).lower() for v in field_value)
            return str(compare_value).lower() in str(field_value).lower()
        elif operator == 'not_contains':
            if isinstance(field_value, list):
                return all(str(compare_value).lower() not in str(v).lower() for v in field_value)
            return str(compare_value).lower() not in str(field_value).lower()
        
        # List operations
        elif operator == 'in':
            return str(field_value).lower() in [str(v).lower() for v in compare_value]
        elif operator == 'not_in':
            return str(field_value).lower() not in [str(v).lower() for v in compare_value]
        
        return True
    
    def get_checklist(self, user_intake: Dict) -> Dict[str, List]:
        """
        Generate smart checklist based on user project
        
        Args:
            user_intake: User's project data
            
        Returns:
            Dictionary with 'critical', 'project_specific', 'strengthen' keys
        """
        checklist = {
            'critical': [],
            'project_specific': [],
            'strengthen': []
        }
        
        checklist_items = self.data.get('checklist_items', {})
        
        # Always include critical items
        checklist['critical'] = checklist_items.get('critical', [])
        
        # Add conditional project-specific items
        for item in checklist_items.get('project_specific', []):
            if 'conditional' in item:
                if self._evaluate_condition(item['conditional'], user_intake):
                    checklist['project_specific'].append(item)
            else:
                checklist['project_specific'].append(item)
        
        # Add strengthen items
        checklist['strengthen'] = checklist_items.get('strengthen', [])
        
        return checklist
    
    def calculate_readiness_score(self, user_responses: Dict) -> float:
        """
        Calculate how ready user is to apply based on their responses
        
        Args:
            user_responses: Dict mapping question IDs to user's answers
            
        Returns:
            Readiness score from 0-100
        """
        total_weight = sum(q.get('scoring_weight', 10) for q in self.data.get('questions', []))
        earned_weight = 0
        
        for q in self.data.get('questions', []):
            q_id = q.get('id')
            if q_id in user_responses:
                response = user_responses[q_id]
                
                # Check if response is substantial (at least 5 words for text responses)
                if isinstance(response, str) and len(response.split()) >= 5:
                    earned_weight += q.get('scoring_weight', 10)
                # For non-text responses (checkboxes, etc), just check if present
                elif response:
                    earned_weight += q.get('scoring_weight', 10)
        
        return (earned_weight / total_weight * 100) if total_weight > 0 else 0
    
    def estimate_time_to_ready(self, checklist: Dict, completed_items: set) -> float:
        """
        Estimate weeks needed to complete remaining checklist items
        
        Args:
            checklist: Dict from get_checklist()
            completed_items: Set of completed item names
            
        Returns:
            Estimated weeks to completion
        """
        remaining_weeks = 0
        
        for category in ['critical', 'project_specific', 'strengthen']:
            for item in checklist.get(category, []):
                item_name = item.get('item', '')
                if item_name not in completed_items:
                    time_estimate = item.get('time_estimate', '1 week')
                    weeks = self._parse_time_estimate(time_estimate)
                    remaining_weeks += weeks
        
        return remaining_weeks
    
    def _parse_time_estimate(self, time_str: str) -> float:
        """Parse time estimate string to weeks"""
        time_str = time_str.lower()
        
        # Handle ranges like "2-4 weeks"
        if '-' in time_str and 'week' in time_str:
            parts = time_str.split('-')
            try:
                low = float(parts[0].strip())
                high = float(parts[1].split()[0].strip())
                return (low + high) / 2
            except (ValueError, IndexError):
                return 1
        
        # Handle single values
        if 'week' in time_str:
            try:
                return float(''.join(c for c in time_str if c.isdigit() or c == '.'))
            except ValueError:
                return 1
        
        if 'day' in time_str:
            try:
                days = float(''.join(c for c in time_str if c.isdigit() or c == '.'))
                return days / 7
            except ValueError:
                return 0.5
        
        if 'month' in time_str:
            try:
                months = float(''.join(c for c in time_str if c.isdigit() or c == '.'))
                return months * 4
            except ValueError:
                return 4
        
        return 1  # Default to 1 week


class TemplateManager:
    """Manages loading and accessing multiple funding program templates"""
    
    def __init__(self, templates_dir: str = "funding_templates/templates"):
        """
        Initialize template manager
        
        Args:
            templates_dir: Path to directory containing template JSON files
        """
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_templates()
    
    def _load_templates(self):
        """Load all JSON templates from directory"""
        if not self.templates_dir.exists():
            return
        
        for template_file in self.templates_dir.glob("*.json"):
            if template_file.name != "template-schema.json":
                try:
                    program_id = template_file.stem
                    self.templates[program_id] = FundingTemplate(str(template_file))
                except Exception as e:
                    print(f"Warning: Could not load template {template_file.name}: {e}")
    
    def get_template(self, program_id: str) -> Optional[FundingTemplate]:
        """
        Get template by program ID
        
        Args:
            program_id: Unique identifier for the program (e.g., 'sfi-climate-smart')
            
        Returns:
            FundingTemplate instance or None if not found
        """
        return self.templates.get(program_id)
    
    def list_available_templates(self) -> List[str]:
        """
        List all available program template IDs
        
        Returns:
            List of program IDs that have templates
        """
        return list(self.templates.keys())
    
    def has_template(self, program_id: str) -> bool:
        """Check if template exists for given program ID"""
        return program_id in self.templates
