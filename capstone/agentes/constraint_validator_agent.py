"""
Constraint Validator Subagent
Especialista en validación y negociación de restricciones.
Identifica conflictos, propone ajustes y retorna restricciones refinadas.
"""

import json
from typing import Dict, Tuple
from dataclasses import dataclass
from anthropic import Anthropic

@dataclass
class ValidationResult:
    """Resultado de validación con ajustes propuestos"""
    is_valid: bool
    refined_constraints: Dict
    adjustments_made: list
    explanation: str

class ConstraintValidatorAgent:
    """
    Subagente que:
    1. Recibe constraints (posiblemente conflictivas)
    2. Consulta viabilidad con el catálogo
    3. Propone ajustes si hay conflictos
    4. Retorna constraints refinadas y notas
    """

    def __init__(self):
        self.client = Anthropic()
        self.model = "bedrock-claude-sonnet"
        self.conversation_history = []

    def validate_and_negotiate(
        self,
        constraints: Dict,
        catalog_feedback: Dict
    ) -> ValidationResult:
        """
        Valida restricciones contra feedback del catálogo.
        Si hay conflictos, propone negociación.
        """
        self.conversation_history = []

        prompt = f"""Eres un especialista en validación de restricciones para playlists de DJ.

Has recibido estas restricciones:
{json.dumps(constraints, indent=2)}

Y este feedback del catálogo sobre su viabilidad:
{json.dumps(catalog_feedback, indent=2)}

Tu tarea:
1. Analizar si hay conflictos entre restricciones y disponibilidad
2. Si no son viables, proponer ajustes ESPECÍFICOS y cuantificados
3. Retornar un JSON con:
   - is_valid (bool): ¿Restricciones viables sin cambios?
   - adjustments (list): Qué cambios propones (ej: "aumentar duración a 60 min")
   - refined_constraints (object): Restricciones ajustadas
   - explanation (string): 2-3 líneas justificando la decisión

Mantén el tono profesional pero conversacional, como si negocias con el DJ."""

        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=self.conversation_history
        )

        result_text = response.content[0].text if response.content else ""
        self.conversation_history.append({
            "role": "assistant",
            "content": result_text
        })

        # Parse response (expect JSON)
        try:
            # Extract JSON from response (Claude might wrap it in markdown)
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
            else:
                # Fallback: parse as structured result
                result_json = {
                    "is_valid": True,
                    "adjustments": [],
                    "refined_constraints": constraints,
                    "explanation": result_text
                }
        except json.JSONDecodeError:
            result_json = {
                "is_valid": True,
                "adjustments": [],
                "refined_constraints": constraints,
                "explanation": result_text
            }

        return ValidationResult(
            is_valid=result_json.get("is_valid", True),
            refined_constraints=result_json.get("refined_constraints", constraints),
            adjustments_made=result_json.get("adjustments", []),
            explanation=result_json.get("explanation", result_text)
        )

    def simulate_dj_negotiation(
        self,
        constraints: Dict,
        catalog_feedback: Dict,
        suggested_adjustments: list
    ) -> Dict:
        """
        Simula una negociación con el DJ.
        El agente propone ajustes, "el DJ" responde (simulado).
        """
        self.conversation_history = []

        prompt = f"""Simula una negociación rápida con un DJ.

RESTRICCIONES ORIGINALES:
{json.dumps(constraints, indent=2)}

FEEDBACK DEL CATÁLOGO:
{json.dumps(catalog_feedback, indent=2)}

AJUSTES PROPUESTOS:
{json.dumps(suggested_adjustments, indent=2)}

Tu tarea es simular esta negociación:
1. TÚ (agente): Explica el problema y propone 1-2 ajustes máximo
2. DJ (simulado): "OK, voy con la opción 1" o "déjame pensarlo, ¿hay otra?"
3. RESULTADO FINAL: Devuelve las restricciones finales acordadas

Responde en JSON:
{{
  "negotiation_dialogue": [
    {{"speaker": "agent", "message": "..."}},
    {{"speaker": "dj", "message": "..."}}
  ],
  "final_constraints": {{...}},
  "agreed_adjustments": [...]
}}"""

        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=self.conversation_history
        )

        result_text = response.content[0].text if response.content else ""

        try:
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "negotiation_dialogue": [{"speaker": "agent", "message": result_text}],
                    "final_constraints": constraints,
                    "agreed_adjustments": suggested_adjustments
                }
        except json.JSONDecodeError:
            return {
                "negotiation_dialogue": [{"speaker": "agent", "message": result_text}],
                "final_constraints": constraints,
                "agreed_adjustments": suggested_adjustments
            }
